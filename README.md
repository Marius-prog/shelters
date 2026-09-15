# GeoDjango Shelter Map

A web application that displays shelters on a map using GeoDjango and Leaflet.

## Prerequisites

- Python 3.8 or higher
- SpatiaLite for spatial database support
- GDAL/OGR libraries

### Installing SpatiaLite

#### macOS
```bash
brew install spatialite-tools libspatialite gdal
```

#### Ubuntu/Debian
```bash
sudo apt-get install spatialite-bin libspatialite-dev python3-gdal
```

#### Windows
Download and install from http://www.gaia-gis.it/gaia-sins/

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd geodjango_live
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Initialize the SpatiaLite database:
```bash
python init_spatialite.py
```

5. Run migrations:
```bash
python manage.py migrate
```

6. Import shelters data:
```bash
python manage.py import_shelters
```

7. Run the development server:
```bash
python manage.py runserver
```

8. Open your browser and navigate to http://127.0.0.1:8000/

## Docker Setup

### Prerequisites
- Docker and Docker Compose installed

### Quick Start with Docker

1. Clone the repository:
```bash
git clone <repository-url>
cd geodjango_live
```

2. Build and run with Docker Compose:
```bash
docker-compose up --build
```

3. The application will be available at http://localhost:8000

### Docker Commands

```bash
# Build and start containers
docker-compose up --build

# Run in background
docker-compose up -d

# Stop containers
docker-compose down

# View logs
docker-compose logs -f

# Run management commands
docker-compose exec web python manage.py <command>

# Import shelter data
docker-compose exec web python manage.py import_shelters

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Production deployment
docker-compose -f docker-compose.prod.yml up --build
```

### Docker Configuration

The Docker setup includes:
- **web**: Django application with Gunicorn
- **db**: PostGIS database (PostgreSQL with spatial extensions)
- **nginx**: Reverse proxy and static file server (production only)

## Features

- Interactive map showing shelters across Lithuania
- Filtering by municipality
- Detailed information about each shelter
- Street view integration
- Mobile-responsive design
- Dark/light theme toggle
- Multi-language support (Lithuanian, English, Russian, Polish)

## Data Source

The shelter data is imported from the Lithuanian government's open data portal:
https://get.data.gov.lt/datasets/gov/pagd/priedangos/Priedanga/ 