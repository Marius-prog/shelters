from django.core.management.base import BaseCommand
from shelter.models import Shelter
import requests

class Command(BaseCommand):
    help = 'Import shelters from API'

    def handle(self, *args, **options):
        # First, clear existing data if table exists
        try:
            Shelter.objects.all().delete()
            self.stdout.write("Cleared existing shelters from database")
        except Exception as e:
            self.stdout.write(f"No existing data to clear: {e}")

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
                    
                    # Handle different POINT formats that may come from the API
                    if 'POINT' in wgs_str:
                        # Remove 'POINT (', ')', and any extra whitespace
                        coords_str = wgs_str.replace('POINT (', '').replace('POINT(', '').replace(')', '').strip()
                        # Handle different coordinate orders
                        coord_parts = coords_str.split()
                        if len(coord_parts) >= 2:
                            # API returns lat, lon format
                            lat, lon = map(float, coord_parts[:2])
                        else:
                            self.stdout.write(self.style.WARNING(
                                f"Invalid coordinate format: {wgs_str}"
                            ))
                            continue
                    else:
                        # Try to parse as simple comma or space-separated coordinates
                        try:
                            if ',' in wgs_str:
                                lat, lon = map(float, wgs_str.split(','))
                            else:
                                lat, lon = map(float, wgs_str.split()[:2])
                        except (ValueError, IndexError):
                            self.stdout.write(self.style.WARNING(
                                f"Could not parse coordinates: {wgs_str}"
                            ))
                            continue
                    
                    capacity = 0
                    try:
                        # Try both possible field names for capacity
                        capacity = int(item.get('gyventoju_skaicius', 0) or item.get('vietų_skaičius', 0) or 0)
                    except (ValueError, TypeError):
                        pass
                        
                    # Create shelter data
                    shelter_data = {
                        'object_id': item.get('_id', ''),
                        'address': f"{item.get('gatve', '')} {item.get('namo_numeris', '')}",
                        'municipality': item.get('savivaldybe', ''),
                        'capacity': capacity,
                        'purpose': item.get('priedangos_pavadinimas', ''),
                        'condition': item.get('būklė', ''),
                        'longitude': lon,
                        'latitude': lat
                    }
                    
                    # Add spatial field if available
                    try:
                        from django.contrib.gis.geos import Point
                        shelter_data['location'] = Point(lon, lat, srid=4326)
                    except ImportError:
                        # GeoDjango not available, skip spatial field
                        pass
                    
                    shelter = Shelter.objects.create(**shelter_data)
                    success_count += 1
                    
                    if success_count % 10 == 0:  # Print progress every 10 shelters
                        self.stdout.write(f"Processed {success_count}/{total_shelters} shelters")
                        
                except Exception as e:
                    error_count += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f"Error processing shelter: {str(e)}\n"
                            f"Data: {str(item)}"
                        )
                    )
            
            self.stdout.write(self.style.SUCCESS(
                f"\nImport completed:\n"
                f"- Total shelters in API: {total_shelters}\n"
                f"- Successfully imported: {success_count}\n"
                f"- Errors: {error_count}\n"
                f"- Total in database: {Shelter.objects.count()}"
            ))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to import shelters: {str(e)}"))