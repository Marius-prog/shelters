# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Server Management
- **Run server (local)**: `./start_local.sh` or `DEBUG=True python run_local.py runserver 8008` (DEBUG=True required to disable SSL redirect)
- **Run server (production)**: `python manage.py runserver`
- **Docker development**: `docker-compose up --build`
- **Docker production**: `docker-compose -f docker-compose.prod.yml up --build`
- **Docker exec commands**: `docker-compose exec web python manage.py <command>`

### Testing
- **Run all tests**: `python manage.py test`
- **Run single test**: `python manage.py test shelter.tests.TestClassName.test_method_name`
- **Run app tests**: `python manage.py test shelter`

### Database Management
- **Check database**: `python manage.py check_db`
- **Fix database structure**: `python manage.py fix_db`
- **Test database connection**: `python manage.py test_db`
- **Run migrations**: `python manage.py migrate`

### Data Import & Cleaning
- **Import shelters**: `python manage.py import_shelters`
- **Advanced import**: `python manage.py fix_coordinates`
- **Setup and import**: `python manage.py setup_and_import` (runs migrations + import)
- **Clean shelters (basic)**: `python manage.py clean_shelters`
- **Clean shelters (advanced)**: `python manage.py clean_shelters_advanced`
- **Verify boundaries**: `python manage.py verify_boundaries`
- **Validate coordinates**: `python manage.py validate_coordinates`

### Deployment
- **Heroku container**: `heroku container:push web && heroku container:release web`
- **Collect static files**: `python manage.py collectstatic --noinput`
- **Deploy script**: `./deploy-heroku.sh` (automated Heroku deployment)

## Architecture

This is a GeoDjango application for mapping Lithuanian civil defense shelters:

### Core Components
- **Core Model**: `Shelter` model (`shelter/models.py`) with PostGIS `PointField` for geographic data
- **GIS Stack**: Django + PostGIS/SpatiaLite + Leaflet for interactive mapping
- **Database**: PostgreSQL with PostGIS (production), SpatiaLite (SQLite) for local development
- **Static Files**: WhiteNoise for production static file serving with compression
- **Frontend**: Vanilla JavaScript with Leaflet maps, AJAX filtering, and marker clustering
- **Deployment**: Configured for Heroku (container), Render.com, and Docker with automatic SSL

### Database Configuration
- **Production**: PostgreSQL with PostGIS via `DATABASE_URL` environment variable
  - Auto-converts postgres:// to postgis:// engine in `settings.py`
  - Connection pooling: `conn_max_age=600`, `conn_health_checks=True`
- **Local Development**:
  - SpatiaLite (SQLite with spatial extensions) via `run_local.py`
  - PostgreSQL/PostGIS via Docker Compose (`docker-compose.yml`)
- **Auto-detection**: GIS libraries auto-configured for macOS (Homebrew), Windows, and Linux
- **Database bootstrapping**: Views auto-run `setup_and_import` if database is empty (`views.py:21-25`)

### Settings Architecture
- **Main settings**: `geodjango/settings.py` - unified settings for all environments
- **Local runner**: `run_local.py` - uses `geodjango.settings` (same as production)
- **Environment detection**: `ENVIRONMENT` and `DEBUG` env vars control production vs development mode
- **Security**: Auto-enables HTTPS, HSTS, secure cookies when `DEBUG=False`

### Data Flow & Import Architecture
- **Data source**: Lithuanian government open data API at `https://get.data.gov.lt/datasets/gov/pagd/priedangos/Priedanga/:format/json`
- **Import command**: `import_shelters.py` fetches JSON, parses POINT(lat lon) format, creates Shelter objects
- **Coordinate parsing**: Handles multiple formats (POINT geometry, comma-separated, space-separated)
- **Dual coordinate storage**: Both `location` PointField (spatial) and separate `latitude`/`longitude` fields
- **Auto-bootstrapping**: Views (`map_view`, `shelter_data`) automatically run `setup_and_import` if database is empty - ensures zero-config deployment

### Frontend Features
- **Map**: Leaflet.js centered on Lithuania with OpenStreetMap tiles (`static/shelter/js/map.js`)
- **Filtering**: AJAX-based municipality filtering via `/shelter/data/` endpoint
- **Real-time Aircraft**: Live airplane tracking over Lithuania and surrounding airspace (Latvia, Belarus, Poland, Kaliningrad)
  - Updates every 10 seconds via `/api/aircraft/` endpoint
  - Altitude-based color coding (green/orange/blue/magenta for low/medium/high/very-high)
  - Rotating SVG plane icons based on heading
  - Comprehensive popup info: altitude, speed, navigation, weather, DB flags
  - Client-side photo loading from PlaneSpotters.net (cached, lazy-loaded on popup open)
  - Country detection from registration prefix (40+ countries)
  - Military aircraft detection (German, Turkish, Italian, UK, French, Russian patterns)
  - Popup persistence during auto-refresh (stays open, photo cached)
- **Languages**: Multi-language support (LT, EN, RU, PL)
- **Themes**: Dark/light mode toggle
- **Mobile**: QR code generation and responsive design
- **Integration**: Google Street View for shelter locations (API key via secure POST endpoint)

### Performance Optimizations
- Initial map load limited to 1000 shelters
- Marker clustering for dense areas (Leaflet.markercluster)
- AJAX endpoints for filtered data (`/shelter/data/?municipality=X`)
- Compressed static files with WhiteNoise (gzip + Brotli)
- Database connection pooling with health checks

### Data Boundaries & Validation
- **Lithuania bounds**: Latitude 53.89-56.45, Longitude 20.93-26.82
- **Coordinate format**: Point(longitude, latitude, srid=4326) - note lon/lat order for PostGIS
- **Validation commands**: `validate_coordinates`, `verify_boundaries`, `check_coordinates`

## Code Style
- **Imports**: Group by Django, third-party, then local modules
- **Formatting**: 4 spaces for indentation
- **Types**: Use appropriate Django model fields (PointField for geo data)
- **Naming**: snake_case for variables/functions, PascalCase for classes
- **Error Handling**: Use try/except with detailed logging
- **GIS**: Geographic coordinates as Point(lon, lat, srid=4326) - longitude first!
- **Testing**: Follow Django's TestCase pattern with clear docstrings

## Key Files & Locations
- **Main app**: `shelter/` - models, views, templates, management commands
- **Settings**: `geodjango/settings.py` - single settings file for all environments
- **Map template**: `shelter/templates/shelter/map.html`
- **Map JavaScript**:
  - `static/shelter/js/map.js` - Main Leaflet map, shelters, filtering, theme toggle, reset functionality
  - `static/shelter/js/aircraft.js` - Aircraft tracking module (IIFE pattern, 10s refresh, photo cache, popup persistence)
- **Management commands**: `shelter/management/commands/` - 9 custom commands for data import and validation
- **Docker configs**: `Dockerfile`, `Dockerfile.heroku`, `docker-compose.yml`, `docker-compose.prod.yml`

## Frontend Development & Deployment

**CRITICAL**: WhiteNoise compresses static files (`.js`, `.css`) creating `.gz` versions that must be manually deleted when updating:

```bash
# Standard deployment workflow for JS/CSS changes:
/bin/rm -f staticfiles/shelter/js/aircraft.js.gz
/bin/cp -f static/shelter/js/aircraft.js staticfiles/shelter/js/aircraft.js
touch shelter/views.py  # Trigger Django reload
```

**Why this matters**:
- WhiteNoise serves compressed `.gz` files if they exist (even if stale)
- Browser caching requires hard refresh (Cmd+Shift+R) after deployment
- The `aircraft.js` module is updated frequently for real-time tracking features
- Template version numbers were removed to rely on server-side cache busting

## API Endpoints
- `/shelter/data/` - Get shelter GeoJSON data (accepts `?municipality=` query parameter for filtering)
- `/api/aircraft/` - Get real-time aircraft positions over Lithuania and surrounding areas
  - Proxies adsb.lol API: `https://api.adsb.lol/v2/point/{lat}/{lon}/{radius_nm}` (cached 10s)
  - Center: 55.17°N, 23.88°E (Vilnius area)
  - Radius: 108 nautical miles (~200km) - covers Lithuania + neighboring airspace
  - Returns GeoJSON with 38+ aircraft properties (position, altitude, speed, navigation, weather, DB flags)
- `/api/maps-key/` - Securely serve Google Maps API key (POST only, requires X-Requested-With: XMLHttpRequest header)

## Environment Variables
- `SECRET_KEY` or `DJANGO_SECRET_KEY`: Django secret key (auto-generated if missing)
- `DATABASE_URL`: Database connection string (auto-detects PostGIS)
- `GOOGLE_MAPS_API_KEY`: For Street View integration
- `ALLOWED_HOSTS`: Comma-separated list of allowed hosts (defaults to `*`)
- `CUSTOM_DOMAINS`: Comma-separated domains for CSRF_TRUSTED_ORIGINS
- `DEBUG`: Set to `False` in production (enables security features)
- `ENVIRONMENT`: `production` or `development` (affects logging, monitoring)
- `SENTRY_DSN`: Error tracking with Sentry (optional)
- `HEROKU_RELEASE_VERSION`: Auto-set by Heroku for release tracking

## Production Features
- **Health checks**: `/health/` endpoint when `IS_PRODUCTION=True` (requires health_check app)
- **Error tracking**: Sentry integration with 10% trace sampling in production
- **Security headers**: HSTS, XSS filter, content type nosniff, SSL redirect
- **CSRF protection**: Trusted origins for Heroku, Render, and custom domains
- **Static files**: WhiteNoise with compressed manifest storage
- **Logging**: Structured logging with verbose formatting to console