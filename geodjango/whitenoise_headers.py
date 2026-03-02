"""
WhiteNoise custom headers function for adding security headers to static files.
"""
from django.conf import settings


def add_security_headers(headers, path, url):
    """
    Add security headers to static files served by WhiteNoise.
    This function is called by WhiteNoise for each static file response.
    """
    # Add X-Frame-Options
    headers['X-Frame-Options'] = 'DENY'

    # Add X-Content-Type-Options
    headers['X-Content-Type-Options'] = 'nosniff'

    # Add Strict-Transport-Security (HSTS)
    headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'

    # Add X-XSS-Protection
    headers['X-XSS-Protection'] = '1; mode=block'

    # Remove permissive CORS header - WhiteNoise adds this by default
    # We don't need CORS for same-origin static files
    if 'Access-Control-Allow-Origin' in headers:
        del headers['Access-Control-Allow-Origin']

    # Add Content-Security-Policy for JS files
    if path.endswith('.js'):
        csp_parts = []
        if hasattr(settings, 'CSP_DEFAULT_SRC'):
            csp_parts.append(f"default-src {' '.join(settings.CSP_DEFAULT_SRC)}")
        if hasattr(settings, 'CSP_SCRIPT_SRC'):
            csp_parts.append(f"script-src {' '.join(settings.CSP_SCRIPT_SRC)}")
        if hasattr(settings, 'CSP_STYLE_SRC'):
            csp_parts.append(f"style-src {' '.join(settings.CSP_STYLE_SRC)}")
        if hasattr(settings, 'CSP_IMG_SRC'):
            csp_parts.append(f"img-src {' '.join(settings.CSP_IMG_SRC)}")
        if hasattr(settings, 'CSP_FONT_SRC'):
            csp_parts.append(f"font-src {' '.join(settings.CSP_FONT_SRC)}")
        if hasattr(settings, 'CSP_CONNECT_SRC'):
            csp_parts.append(f"connect-src {' '.join(settings.CSP_CONNECT_SRC)}")
        if hasattr(settings, 'CSP_FRAME_SRC'):
            csp_parts.append(f"frame-src {' '.join(settings.CSP_FRAME_SRC)}")

        if csp_parts:
            headers['Content-Security-Policy'] = '; '.join(csp_parts)

    return headers
