from django.shortcuts import render
from django.db.models import Sum
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.views.decorators.cache import cache_page
from django.conf import settings
import json
import requests
from .models import Shelter

def map_view(request):
    try:
        # Check if database table exists, create it if not
        from django.db import connection
        cursor = connection.cursor()
        
        try:
            # Try to count shelters
            count = Shelter.objects.count()
            if count == 0:
                # Table exists but is empty, populate it
                from django.core.management import call_command
                call_command('setup_and_import')
        except Exception:
            # Table doesn't exist, create and populate it
            from django.core.management import call_command
            call_command('setup_and_import')
        
        # Get all shelters with valid coordinates
        shelters = Shelter.objects.filter(is_valid_coordinates=True)
        
        # Calculate totals from all shelters
        total_shelters = shelters.count()
        total_capacity = shelters.aggregate(
            total=Sum('capacity', default=0)
        )['total'] or 0
        
        # Get unique municipalities (safely handle empty database, only from valid shelters)
        try:
            municipalities = (Shelter.objects
                            .filter(is_valid_coordinates=True)
                            .values_list('municipality', flat=True)
                            .distinct()
                            .exclude(municipality__isnull=True)
                            .exclude(municipality='')
                            .order_by('municipality'))
        except Exception:
            municipalities = []
        
        # Create GeoJSON manually
        features = []
        for shelter in shelters:
            # Skip shelters without coordinates
            if shelter.latitude is None or shelter.longitude is None:
                continue
                
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [shelter.longitude, shelter.latitude]
                },
                "properties": {
                    "address": shelter.address or "",
                    "municipality": shelter.municipality or "",
                    "capacity": shelter.capacity or 0,
                    "purpose": shelter.purpose or "",
                    "condition": shelter.condition or ""
                }
            }
            features.append(feature)
        
        shelters_json = json.dumps({
            "type": "FeatureCollection",
            "features": features
        })
        
        context = {
            'shelters_json': shelters_json,
            'municipalities': municipalities,
            'total_shelters': total_shelters,
            'total_capacity': round(total_capacity)
        }
        
        return render(request, 'shelter/map.html', context)
    except Exception as e:
        import traceback
        error_message = f"Error loading map: {str(e)}\n{traceback.format_exc()}"
        return HttpResponse(f"<h1>Error loading map</h1><pre>{error_message}</pre>", status=500)

def shelter_data(request):
    try:
        # Ensure database is populated
        try:
            count = Shelter.objects.count()
            if count == 0:
                from django.core.management import call_command
                call_command('setup_and_import')
        except Exception:
            from django.core.management import call_command
            call_command('setup_and_import')
        
        municipality = request.GET.get('municipality', '')

        # Filter shelters if municipality is specified, only show valid coordinates
        queryset = Shelter.objects.filter(is_valid_coordinates=True)
        if municipality:
            queryset = queryset.filter(municipality=municipality)
        
        
        # Create GeoJSON manually for filtered data
        features = []
        for shelter in queryset:
            # Skip shelters without coordinates
            if shelter.latitude is None or shelter.longitude is None:
                continue
                
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [shelter.longitude, shelter.latitude]
                },
                "properties": {
                    "address": shelter.address or "",
                    "municipality": shelter.municipality or "",
                    "capacity": shelter.capacity or 0,
                    "purpose": shelter.purpose or "",
                    "condition": shelter.condition or ""
                }
            }
            features.append(feature)
        
        shelters = {
            "type": "FeatureCollection",
            "features": features
        }
        
        # Calculate statistics for filtered data
        stats = {
            'count': queryset.count(),
            'total_capacity': queryset.aggregate(total=Sum('capacity', default=0))['total'] or 0
        }
        
        response_data = {
            'geojson': shelters,
            'stats': stats
        }
        
        return JsonResponse(response_data, safe=False)
    except Exception as e:
        import traceback
        error_message = str(e)
        trace = traceback.format_exc()
        return JsonResponse({
            'error': error_message,
            'trace': trace,
            'geojson': {
                'type': 'FeatureCollection',
                'features': []
            },
            'stats': {
                'count': 0,
                'total_capacity': 0
            }
        }, status=500)



@require_POST
def get_maps_key(request):
    """Securely serve the Maps API key"""
    # Check if request is AJAX by looking at the headers
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    return JsonResponse({
        'key': settings.GOOGLE_MAPS_API_KEY
    })

def robots_txt(request):
    content = """
User-agent: *
Disallow: /admin/
Disallow: /api/
Allow: /$
Allow: /static/

# Block specific bots
User-agent: OAI-SearchBot
Disallow: /

User-agent: Scrapy
Disallow: /

User-agent: GPTBot
Disallow: /

User-agent: ChatGPT-User
Disallow: /

User-agent: Google-Extended
Disallow: /

User-agent: CCBot
Disallow: /

# Crawl-delay
Crawl-delay: 10

# Sitemap
Sitemap: https://www.slepk.lt/sitemap.xml
"""
    return HttpResponse(content, content_type="text/plain")

def sitemap_xml(request):
    content = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>https://www.slepk.lt/</loc>
        <lastmod>2025-01-26</lastmod>
        <changefreq>daily</changefreq>
        <priority>1.0</priority>
    </url>
</urlset>
"""
    return HttpResponse(content, content_type="application/xml")

# ponytail: per-worker LocMemCache, only 200s are cached; use shared cache if workers scale out
@cache_page(10)
def aircraft_data(request):
    """Fetch real-time aircraft data over Lithuania and surrounding areas from adsb.lol API"""
    try:
        # Lithuania center coordinates and radius
        # Center: approximately Vilnius area
        lat = 55.17
        lon = 23.88
        radius_nm = 108  # ~200km to cover Lithuania and neighboring airspace

        # Fetch data from adsb.lol API (airplanes.live now requires registration)
        api_url = f"https://api.adsb.lol/v2/point/{lat}/{lon}/{radius_nm}"
        response = requests.get(api_url, timeout=5)

        if response.status_code == 200:
            data = response.json()
            aircraft_list = data.get('ac', [])

            # Transform to GeoJSON format for Leaflet
            features = []
            for aircraft in aircraft_list:
                # Skip aircraft without position data
                if 'lat' not in aircraft or 'lon' not in aircraft:
                    continue

                # Photo fetching temporarily disabled - causes 5+ second delays
                # TODO: Re-enable with caching or client-side fetching
                registration = aircraft.get('r', '').strip()
                photo_url = None

                # Route information - disabled for now (causes slowdowns)
                # TODO: Re-enable when we have a proper flight route API
                flight_number = aircraft.get('flight', '').strip()
                origin = None
                destination = None

                feature = {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [aircraft['lon'], aircraft['lat']]
                    },
                    "properties": {
                        # Basic identification
                        "flight": flight_number if flight_number else 'N/A',
                        "registration": registration if registration else 'N/A',
                        "type": aircraft.get('t', 'N/A'),
                        "description": aircraft.get('desc', 'Unknown'),
                        "category": aircraft.get('category', 'N/A'),
                        "hex": aircraft.get('hex', ''),
                        "squawk": aircraft.get('squawk', 'N/A'),

                        # Altitude data
                        "altitude": aircraft.get('alt_baro', 0),
                        "alt_geom": aircraft.get('alt_geom'),
                        "baro_rate": aircraft.get('baro_rate', 0),
                        "geom_rate": aircraft.get('geom_rate'),

                        # Speed data
                        "speed": aircraft.get('gs', 0),
                        "ias": aircraft.get('ias'),
                        "tas": aircraft.get('tas'),
                        "mach": aircraft.get('mach'),

                        # Heading and navigation
                        "heading": aircraft.get('track', 0),
                        "true_heading": aircraft.get('true_heading'),
                        "mag_heading": aircraft.get('mag_heading'),
                        "roll": aircraft.get('roll'),
                        "track_rate": aircraft.get('track_rate'),

                        # Navigation systems
                        "nav_altitude_mcp": aircraft.get('nav_altitude_mcp'),
                        "nav_altitude_fms": aircraft.get('nav_altitude_fms'),
                        "nav_heading": aircraft.get('nav_heading'),
                        "nav_modes": aircraft.get('nav_modes', []),
                        "nav_qnh": aircraft.get('nav_qnh'),

                        # Wind and temperature
                        "wind_dir": aircraft.get('wd'),
                        "wind_speed": aircraft.get('ws'),
                        "oat": aircraft.get('oat'),
                        "tat": aircraft.get('tat'),

                        # Signal quality
                        "rssi": aircraft.get('rssi'),
                        "seen": aircraft.get('seen'),
                        "messages": aircraft.get('messages'),

                        # Database/accuracy flags
                        "nic": aircraft.get('nic'),
                        "nac_p": aircraft.get('nac_p'),
                        "nac_v": aircraft.get('nac_v'),
                        "sil": aircraft.get('sil'),
                        "sil_type": aircraft.get('sil_type'),
                        "gva": aircraft.get('gva'),
                        "sda": aircraft.get('sda'),
                        "nic_baro": aircraft.get('nic_baro'),
                        "rc": aircraft.get('rc'),
                        "mlat": aircraft.get('mlat', []),

                        # Emergency and alerts
                        "emergency": aircraft.get('emergency'),
                        "alert": aircraft.get('alert'),
                        "spi": aircraft.get('spi'),

                        # Route (for future use)
                        "photo_url": photo_url,
                        "origin": origin,
                        "destination": destination
                    }
                }
                features.append(feature)

            return JsonResponse({
                "type": "FeatureCollection",
                "features": features,
                "count": len(features)
            })
        else:
            return JsonResponse({
                "error": f"API returned status {response.status_code}",
                "type": "FeatureCollection",
                "features": [],
                "count": 0
            }, status=response.status_code)

    except requests.exceptions.Timeout:
        return JsonResponse({
            "error": "Request to adsb.lol API timed out",
            "type": "FeatureCollection",
            "features": [],
            "count": 0
        }, status=504)
    except Exception as e:
        return JsonResponse({
            "error": str(e),
            "type": "FeatureCollection",
            "features": [],
            "count": 0
        }, status=500)
