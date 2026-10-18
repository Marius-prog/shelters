"""
Non-blocking database bootstrap for zero-config deployments.

Previously `map_view` / `shelter_data` ran `setup_and_import` synchronously
inside the request whenever the shelter table was missing or empty. That
command dropped the table, fetched the full data.gov.lt dataset with no
timeout and inserted rows one by one. Under gunicorn's 30 s worker timeout
the import never finished: the worker was killed, the next request started
the whole thing over, and the site hung on every request.

The import now runs at most once per process, in a daemon thread, and is
retried no more often than RETRY_SECONDS. Requests never wait for it; they
render whatever is in the database right now.
"""
import logging
import threading
import time

from django.core.management import call_command
from django.db import close_old_connections, connection
from django.db.utils import DatabaseError

from .models import Shelter

logger = logging.getLogger(__name__)

RETRY_SECONDS = 600

_lock = threading.Lock()
_running = False
_last_attempt = 0.0


def needs_bootstrap():
    """True when the shelter table is missing or has no rows."""
    try:
        return Shelter.objects.count() == 0
    except DatabaseError:
        return True


def _run():
    global _running
    try:
        close_old_connections()
        if Shelter._meta.db_table not in connection.introspection.table_names():
            logger.info("Shelter table missing - running migrations")
            call_command('migrate', interactive=False, verbosity=0)
        if Shelter.objects.count() == 0:
            logger.info("Shelter table empty - importing from data.gov.lt")
            call_command('import_shelters')
        logger.info("Shelter bootstrap finished: %d rows", Shelter.objects.count())
    except Exception:
        logger.exception("Shelter bootstrap failed; will retry in %ds", RETRY_SECONDS)
    finally:
        close_old_connections()
        with _lock:
            _running = False


def ensure_data():
    """
    Kick off a background bootstrap if the database has no shelter data.

    Returns True when data is still missing (a bootstrap is running or was
    attempted recently), False when the database is populated. Never blocks.
    """
    global _running, _last_attempt
    if not needs_bootstrap():
        return False
    with _lock:
        if _running or time.monotonic() - _last_attempt < RETRY_SECONDS:
            return True
        _running = True
        _last_attempt = time.monotonic()
    threading.Thread(target=_run, name="shelter-bootstrap", daemon=True).start()
    return True
