from django.conf import settings
import hashlib
import time

def google_maps_api_key(request):
    """
    Generates a temporary, hashed version of the API key for the template
    """
    if not hasattr(settings, 'GOOGLE_MAPS_API_KEY'):
        return {'GOOGLE_MAPS_API_KEY': ''}
    
    # Create a temporary token that changes every hour
    timestamp = int(time.time() / 3600)  # Changes every hour
    token = f"{settings.SECRET_KEY}:{timestamp}"
    hashed = hashlib.sha256(token.encode()).hexdigest()[:12]
    
    return {'GOOGLE_MAPS_API_KEY': hashed}