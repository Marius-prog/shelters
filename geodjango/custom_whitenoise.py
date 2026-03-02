"""
Custom WhiteNoise middleware to add security headers to static files.
"""
import logging
from django.conf import settings
from whitenoise.middleware import WhiteNoiseMiddleware

logger = logging.getLogger(__name__)


class SecurityWhiteNoiseMiddleware(WhiteNoiseMiddleware):
    """
    Custom WhiteNoise middleware that adds security headers to static files.
    """

    def add_headers(self, static_file, url):
        """
        Add security headers to static files served by WhiteNoise.
        This method is called by WhiteNoise for each static file at WSGI level.
        """
        # Call parent method to get default headers
        headers = super().add_headers(static_file, url)

        # Only add security headers in production
        if not settings.DEBUG:
            logger.info(f"Adding security headers to static file: {url}")

            # Add security headers
            headers['X-Frame-Options'] = 'DENY'
            headers['X-Content-Type-Options'] = 'nosniff'
            headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
            headers['X-XSS-Protection'] = '1; mode=block'

            # Remove CORS header if present - WhiteNoise adds this by default
            if 'Access-Control-Allow-Origin' in headers:
                logger.info(f"Removing Access-Control-Allow-Origin from {url}")
                del headers['Access-Control-Allow-Origin']

            # Add CSP for JS files
            if url.endswith('.js'):
                logger.info(f"Adding CSP to JS file: {url}")
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

            logger.info(f"Security headers applied to {url}")

        return headers
