from django.core.management.base import BaseCommand
from django.db import connection
from shelter.models import Shelter
import requests

class Command(BaseCommand):
    help = 'Setup database and import shelters'

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
        
        # Now import data
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
            
            for item in shelters_data:
                try:
                    wgs_str = item.get('taskas_wgs', '')
                    if not wgs_str:
                        continue
                    
                    # Handle different POINT formats
                    if 'POINT' in wgs_str:
                        coords_str = wgs_str.replace('POINT (', '').replace('POINT(', '').replace(')', '').strip()
                        coord_parts = coords_str.split()
                        if len(coord_parts) >= 2:
                            # API returns lat, lon format
                            lat, lon = map(float, coord_parts[:2])
                        else:
                            continue
                    else:
                        try:
                            if ',' in wgs_str:
                                lat, lon = map(float, wgs_str.split(','))
                            else:
                                lat, lon = map(float, wgs_str.split()[:2])
                        except (ValueError, IndexError):
                            continue
                    
                    capacity = 0
                    try:
                        capacity = int(item.get('gyventoju_skaicius', 0) or item.get('vietų_skaičius', 0) or 0)
                    except (ValueError, TypeError):
                        pass
                        
                    shelter = Shelter.objects.create(
                        object_id=item.get('_id', ''),
                        address=f"{item.get('gatve', '')} {item.get('namo_numeris', '')}".strip(),
                        municipality=item.get('savivaldybe', ''),
                        capacity=capacity,
                        purpose=item.get('pavadinimas', ''),
                        condition=item.get('būklė', ''),
                        longitude=lon,
                        latitude=lat
                    )
                    success_count += 1
                    
                    if success_count % 100 == 0:
                        self.stdout.write(f"Processed {success_count}/{total_shelters} shelters")
                        
                except Exception as e:
                    error_count += 1
                    if error_count < 5:  # Only show first 5 errors
                        self.stdout.write(f"Error: {str(e)}")
            
            self.stdout.write(self.style.SUCCESS(
                f"Import completed:\n"
                f"- Successfully imported: {success_count}\n"
                f"- Errors: {error_count}\n"
                f"- Total in database: {Shelter.objects.count()}"
            ))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to import shelters: {str(e)}"))