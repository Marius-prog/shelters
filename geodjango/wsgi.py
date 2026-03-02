import os
import sys
from django.core.wsgi import get_wsgi_application
from whitenoise import WhiteNoise

# Add the project directory to the Python path
path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if path not in sys.path:
    sys.path.append(path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'geodjango.settings')

application = get_wsgi_application()
application = WhiteNoise(application)
application.add_files(os.path.join(os.path.dirname(__file__), '..', 'staticfiles'), prefix='static/')