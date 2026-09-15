# GeoDjango Shelter Map - Deployment Guide

This guide covers deployment options for the GeoDjango Lithuanian Shelter Map application using Docker containers.

## Quick Start

### Development
```bash
git clone https://github.com/your-username/geodjango-shelter-map.git
cd geodjango-shelter-map
docker-compose up --build
```
Access: http://localhost:8000

### Production
```bash
git clone https://github.com/your-username/geodjango-shelter-map.git
cd geodjango-shelter-map
cp .env.example .env
# Edit .env with your production values
docker-compose -f docker-compose.prod.yml up --build -d
```
Access: http://localhost (or your domain)

## Available Docker Configurations

### 1. Development (`docker-compose.yml`)
- **Purpose**: Local development with hot reload
- **Database**: PostGIS with spatial features
- **Command**: `docker-compose up --build`
- **Features**:
  - Live code reloading
  - Debug mode enabled
  - Development server
  - Volume mounts for real-time changes

### 2. Production (`docker-compose.prod.yml`)
- **Purpose**: Production deployment with Nginx
- **Database**: PostGIS with spatial features
- **Command**: `docker-compose -f docker-compose.prod.yml up --build -d`
- **Features**:
  - Gunicorn WSGI server
  - Nginx reverse proxy
  - Static file serving
  - Environment variable configuration

### 3. Heroku (`Dockerfile.heroku` + `heroku.yml`)
- **Purpose**: Heroku container deployment
- **Database**: Regular PostgreSQL (no PostGIS)
- **Features**:
  - Optimized for Heroku constraints
  - Automatic fallback to non-spatial fields
  - Container registry deployment

## Environment Configuration

### Required Environment Variables

Create a `.env` file based on `.env.example`:

```bash
# Required
SECRET_KEY=your-very-secure-secret-key-here
DEBUG=False
DATABASE_URL=postgis://user:password@localhost:5432/geodjango

# Optional
GOOGLE_MAPS_API_KEY=your-google-maps-api-key
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com
```

### Environment-Specific Settings

The application automatically detects the environment:
- **Local Development**: Uses SpatiaLite for spatial features
- **Docker with PostGIS**: Uses PostGIS for full spatial features
- **Heroku**: Uses regular PostgreSQL without spatial extensions

## Deployment Options

### Option 1: VPS/Cloud Server with Docker Compose

1. **Setup server** (Ubuntu/Debian):
```bash
# Install Docker and Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
sudo usermod -aG docker $USER
```

2. **Deploy application**:
```bash
git clone https://github.com/your-username/geodjango-shelter-map.git
cd geodjango-shelter-map
cp .env.example .env
nano .env  # Configure your environment
docker-compose -f docker-compose.prod.yml up --build -d
```

3. **Setup reverse proxy** (optional, if not using included Nginx):
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Option 2: Docker Registry Deployment

1. **Build and tag**:
```bash
docker build -t yourusername/geodjango-shelter-map:latest .
docker push yourusername/geodjango-shelter-map:latest
```

2. **Deploy on target server**:
```bash
docker pull yourusername/geodjango-shelter-map:latest
docker run -d \
  --name geodjango-app \
  -p 8000:8000 \
  -e SECRET_KEY=your-secret-key \
  -e DATABASE_URL=your-database-url \
  yourusername/geodjango-shelter-map:latest
```

### Option 3: Container Orchestration (Kubernetes)

Example `deployment.yaml`:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: geodjango-shelter-map
spec:
  replicas: 3
  selector:
    matchLabels:
      app: geodjango-shelter-map
  template:
    metadata:
      labels:
        app: geodjango-shelter-map
    spec:
      containers:
      - name: web
        image: yourusername/geodjango-shelter-map:latest
        ports:
        - containerPort: 8000
        env:
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: geodjango-secrets
              key: secret-key
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: geodjango-secrets
              key: database-url
```

## Database Considerations

### PostGIS Features (Full Spatial Support)
- Available in: Docker Compose deployments
- Features: Full GeoDjango spatial operations, point fields, geographic queries
- Database: PostgreSQL with PostGIS extension

### Regular PostgreSQL (Limited Spatial)
- Available in: Heroku, some cloud providers
- Features: Coordinates stored as separate lat/lng float fields
- Database: Standard PostgreSQL

### SpatiaLite (Development)
- Available in: Local development without Docker
- Features: SQLite with spatial extensions
- Database: File-based SQLite with SpatiaLite

## Production Checklist

- [ ] Set `DEBUG=False`
- [ ] Configure strong `SECRET_KEY`
- [ ] Set up proper `ALLOWED_HOSTS`
- [ ] Configure database with connection pooling
- [ ] Set up SSL/TLS certificates
- [ ] Configure static file serving
- [ ] Set up monitoring and logging
- [ ] Configure backup strategy
- [ ] Set up health checks
- [ ] Configure firewall rules

## Monitoring and Maintenance

### Health Checks
```bash
# Check application health
curl http://localhost:8000/

# Check database connectivity
docker-compose exec db pg_isready -U geodjango

# View logs
docker-compose logs -f web
docker-compose logs -f db
```

### Updates
```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose -f docker-compose.prod.yml up --build -d

# Run migrations if needed
docker-compose exec web python manage.py migrate
```

### Backup
```bash
# Database backup
docker-compose exec db pg_dump -U geodjango geodjango > backup.sql

# Volume backup
docker run --rm -v geodjango_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz /data
```

## Troubleshooting

### Common Issues

1. **Database connection errors**:
   - Check DATABASE_URL format
   - Verify database container is running
   - Check network connectivity

2. **Static files not loading**:
   - Run `docker-compose exec web python manage.py collectstatic`
   - Check volume mounts
   - Verify Nginx configuration

3. **Memory issues**:
   - Increase Docker memory limits
   - Reduce Gunicorn worker count
   - Optimize database queries

### Useful Commands
```bash
# Shell access
docker-compose exec web bash
docker-compose exec db psql -U geodjango

# Import shelter data
docker-compose exec web python manage.py import_shelters

# Create admin user
docker-compose exec web python manage.py createsuperuser

# Check logs
docker-compose logs --tail=100 -f
```