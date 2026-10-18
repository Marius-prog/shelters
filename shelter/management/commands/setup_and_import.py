from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Run migrations, then import shelters from data.gov.lt (safe to re-run)'

    def handle(self, *args, **options):
        # Schema comes from migrations, never from hand-written DDL: the old
        # DROP TABLE / CREATE TABLE here used SQLite syntax, lacked the
        # `location` and `is_valid_coordinates` columns, and wiped production
        # data every time a request found the table empty.
        call_command('migrate', interactive=False, verbosity=1)
        call_command('import_shelters')
