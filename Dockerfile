# Heroku-optimized production Dockerfile
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PORT=8000

# Set work directory
WORKDIR /app

# Install system dependencies for GeoDjango and PostGIS
RUN apt-get update && apt-get install -y \
    # Essential build tools
    build-essential \
    # PostgreSQL client for database connections
    postgresql-client \
    # GDAL dependencies for GeoDjango
    gdal-bin \
    libgdal-dev \
    # GEOS library for geometric operations
    libgeos-dev \
    # PROJ library for coordinate transformations
    libproj-dev \
    # Additional tools for debugging
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set GDAL library paths for GeoDjango
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal \
    C_INCLUDE_PATH=/usr/include/gdal \
    GDAL_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu/libgdal.so

# Copy requirements first for better Docker layer caching
COPY requirements.txt requirements-base.txt ./

# Install Python dependencies with optimizations
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create necessary directories with proper permissions
RUN mkdir -p staticfiles media logs && \
    chmod 755 staticfiles media logs

# Collect static files for production
RUN python manage.py collectstatic --noinput --clear

# Create a non-root user for security
RUN groupadd -r appgroup && useradd -r -g appgroup appuser && \
    chown -R appuser:appgroup /app
USER appuser

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:$PORT/health/ || exit 1

# Expose the port that Heroku provides
EXPOSE $PORT

# Production-ready gunicorn command with optimized settings
CMD gunicorn geodjango.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 3 \
    --worker-class gthread \
    --threads 2 \
    --worker-connections 1000 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --timeout 30 \
    --keep-alive 2 \
    --preload \
    --access-logfile - \
    --error-logfile - \
    --log-level info