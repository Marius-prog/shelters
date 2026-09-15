"""
Custom WhiteNoise middleware to add security headers to static files.
"""
import logging
from django.conf import settings
from whitenoise.middleware import WhiteNoiseMiddleware
from whitenoise.responders import StaticFile

logger = logging.getLogger(__name__)


class SecurityWhiteNoiseMiddleware(WhiteNoiseMiddleware):
    """
    Custom WhiteNoise middleware that adds security headers to static files.
    """

    def serve(self, static_file):
        """
        Override serve() to add custom security headers to the response.
        This method is called by WhiteNoise when serving each static file.
        """
        # Get the response from parent
        response = super().serve(static_file)

        # Only add security headers in production
        if not settings.DEBUG and response:
            logger.info(f"Adding security headers to static file")

            # Add security headers
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
            response.headers['X-XSS-Protection'] = '1; mode=block'

            # Remove CORS header if present
            if 'Access-Control-Allow-Origin' in response.headers:
                logger.info(f"Removing Access-Control-Allow-Origin")
                del response.headers['Access-Control-Allow-Origin']

            # Add CSP for JS files
            if hasattr(static_file, 'path') and static_file.path.endswith('.js'):
                logger.info(f"Adding CSP to JS file")
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
                    response.headers['Content-Security-Policy'] = '; '.join(csp_parts)

            logger.info(f"Security headers applied")

        return response
