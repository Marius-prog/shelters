from django.core.management.base import BaseCommand
from django.db import connection
from django.contrib.gis.geos import Point
from shelter.models import Shelter
import requests

class Command(BaseCommand):
    help = 'Fix coordinates by using separate lat/lon fields from API'

    def handle(self, *args, **options):
        cursor = connection.cursor()
        
        # First create the table
        try:
            cursor.execute("DROP TABLE IF EXISTS shelter_shelter;")
            cursor.execute("""
                CREATE TABLE shelter_shelter (
                    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                    object_id VARCHAR(100) NOT NULL UNIQUE,
                    address VARCHAR(255) NOT NULL,
                    municipality VARCHAR(100) NOT NULL,
                    capacity INTEGER NULL,
                    purpose VARCHAR(255) NOT NULL,
                    "condition" VARCHAR(100) NOT NULL,
                    latitude REAL NULL,
                    longitude REAL NULL
                );
            """)
            self.stdout.write("Created shelter table")
        except Exception as e:
            self.stdout.write(f"Error creating table: {e}")
            return
        
        # Import data using separate lat/lon fields for accuracy
        url = "https://get.data.gov.lt/datasets/gov/pagd/priedangos/Priedanga/:format/json"
        
        try:
            self.stdout.write("Fetching data from API...")
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            shelters_data = data.get('_data', [])
            total_shelters = len(shelters_data)
            self.stdout.write(f"Found {total_shelters} shelters in API response")
            
            success_count = 0
            error_count = 0
            coordinate_method_stats = {
                'separate_fields': 0,
                'point_format': 0,
                'no_coordinates': 0
            }
            
            for item in shelters_data:
                try:
                    # Method 1: Use separate lat/lon fields (most reliable)
                    lat = item.get('wgs_lat_platuma')
                    lon = item.get('wgs_lon_ilguma')
                    
                    if lat is not None and lon is not None:
                        lat = float(lat)
                        lon = float(lon)
                        coordinate_method_stats['separate_fields'] += 1
                    else:
                        # Method 2: Parse POINT format as fallback
                        wgs_str = item.get('taskas_wgs', '')
                        if not wgs_str or 'POINT' not in wgs_str:
                            coordinate_method_stats['no_coordinates'] += 1
                            continue
                        
                        coords_str = wgs_str.replace('POINT (', '').replace('POINT(', '').replace(')', '').strip()
                        coord_parts = coords_str.split()
                        if len(coord_parts) >= 2:
                            # Try both orders and see which makes sense for Lithuania
                            first, second = map(float, coord_parts[:2])
                            
                            # Lithuania latitude range: ~53.8-56.5, longitude range: ~20.5-26.9
                            if 53.5 <= first <= 57.0 and 20.0 <= second <= 27.0:
                                lat, lon = first, second  # first is lat
                            elif 53.5 <= second <= 57.0 and 20.0 <= first <= 27.0:
                                lat, lon = second, first  # second is lat, first is lon
                            else:
                                # Neither order makes sense for Lithuania, skip
                                continue
                            coordinate_method_stats['point_format'] += 1
                        else:
                            coordinate_method_stats['no_coordinates'] += 1
                            continue
                    
                    # Validate coordinates are in Lithuania
                    if not (53.5 <= lat <= 57.0 and 20.0 <= lon <= 27.0):
                        continue
                    
                    capacity = 0
                    try:
                        capacity = int(item.get('gyventoju_skaicius', 0) or item.get('vietų_skaičius', 0) or 0)
                    except (ValueError, TypeError):
                        pass
                        
                    # Create Point object for spatial field
                    point = Point(lon, lat, srid=4326)
                    
                    shelter = Shelter.objects.create(
                        object_id=item.get('_id', ''),
                        address=f"{item.get('gatve', '')} {item.get('namo_numeris', '')}".strip(),
                        municipality=item.get('savivaldybe', ''),
                        capacity=capacity,
                        purpose=item.get('pavadinimas', '') or 'Shelter',
                        condition=item.get('būklė', '') or 'Unknown',
                        longitude=lon,
                        latitude=lat,
                        location=point
                    )
                    success_count += 1
                    
                    if success_count % 500 == 0:
                        self.stdout.write(f"Processed {success_count}/{total_shelters} shelters")
                        
                except Exception as e:
                    error_count += 1
                    if error_count < 5:  # Only show first 5 errors
                        self.stdout.write(f"Error: {str(e)}")
            
            self.stdout.write(self.style.SUCCESS(
                f"Import completed:\n"
                f"- Successfully imported: {success_count}\n"
                f"- Errors: {error_count}\n"
                f"- Used separate lat/lon fields: {coordinate_method_stats['separate_fields']}\n"
                f"- Used POINT format: {coordinate_method_stats['point_format']}\n"
                f"- No coordinates: {coordinate_method_stats['no_coordinates']}\n"
                f"- Total in database: {Shelter.objects.count()}"
            ))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to import shelters: {str(e)}"))