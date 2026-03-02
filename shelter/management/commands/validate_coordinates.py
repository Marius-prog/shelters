from django.core.management.base import BaseCommand
from shelter.models import Shelter
import requests

class Command(BaseCommand):
    help = 'Validate coordinate correctness by checking against API data'

    def handle(self, *args, **options):
        try:
            # Get some sample data from API to check coordinate format
            url = "https://get.data.gov.lt/datasets/gov/pagd/priedangos/Priedanga/:format/json"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            # Check first few records
            for i, item in enumerate(data['_data'][:5]):
                if i >= 5:
                    break
                    
                wgs_str = item.get('taskas_wgs', '')
                lat_field = item.get('wgs_lat_platuma')
                lon_field = item.get('wgs_lon_ilguma')
                
                self.stdout.write(f"\n--- Record {i+1} ---")
                self.stdout.write(f"taskas_wgs: {wgs_str}")
                self.stdout.write(f"wgs_lat_platuma: {lat_field}")
                self.stdout.write(f"wgs_lon_ilguma: {lon_field}")
                
                # Parse POINT format
                if 'POINT' in wgs_str:
                    coords_str = wgs_str.replace('POINT (', '').replace('POINT(', '').replace(')', '').strip()
                    coord_parts = coords_str.split()
                    if len(coord_parts) >= 2:
                        first, second = map(float, coord_parts[:2])
                        self.stdout.write(f"POINT parsed: first={first}, second={second}")
                        
                        # Check which coordinate matches latitude
                        if abs(first - lat_field) < 0.001:
                            self.stdout.write("✓ First coordinate is LATITUDE (correct)")
                        elif abs(second - lat_field) < 0.001:
                            self.stdout.write("✗ Second coordinate is LATITUDE (SWAPPED!)")
                        else:
                            self.stdout.write("? Neither coordinate matches lat field exactly")
                            
                        # Check which coordinate matches longitude  
                        if abs(first - lon_field) < 0.001:
                            self.stdout.write("✗ First coordinate is LONGITUDE (SWAPPED!)")
                        elif abs(second - lon_field) < 0.001:
                            self.stdout.write("✓ Second coordinate is LONGITUDE (correct)")
                        else:
                            self.stdout.write("? Neither coordinate matches lon field exactly")
                            
            # Check our database
            self.stdout.write(f"\n--- Database Check ---")
            total = Shelter.objects.count()
            with_coords = Shelter.objects.filter(
                latitude__isnull=False, 
                longitude__isnull=False
            ).count()
            
            # Check if coordinates are in Lithuania range
            in_lithuania = Shelter.objects.filter(
                latitude__gte=53.8, latitude__lte=56.5,  # Lithuania lat range
                longitude__gte=20.5, longitude__lte=26.9,  # Lithuania lon range
                latitude__isnull=False, longitude__isnull=False
            ).count()
            
            self.stdout.write(f"Total shelters: {total}")
            self.stdout.write(f"With coordinates: {with_coords}")
            self.stdout.write(f"In Lithuania coordinate range: {in_lithuania}")
            
            if in_lithuania < with_coords * 0.9:  # If less than 90% are in Lithuania
                self.stdout.write("⚠️  WARNING: Many coordinates seem to be outside Lithuania!")
                self.stdout.write("This suggests coordinates might be swapped.")
                
            # Show some examples from database
            examples = Shelter.objects.filter(
                latitude__isnull=False, 
                longitude__isnull=False
            ).order_by('?')[:3]  # Random 3 examples
            
            self.stdout.write(f"\n--- Database Examples ---")
            for shelter in examples:
                self.stdout.write(f"{shelter.address[:30]}... lat:{shelter.latitude:.6f}, lon:{shelter.longitude:.6f}")
                
                # Check if this looks like Lithuania
                if 53.8 <= shelter.latitude <= 56.5 and 20.5 <= shelter.longitude <= 26.9:
                    self.stdout.write("  ✓ Coordinates look like Lithuania")
                else:
                    self.stdout.write("  ✗ Coordinates don't look like Lithuania")
                        
        except Exception as e:
            self.stdout.write(f"Error: {e}")
            import traceback
            self.stdout.write(traceback.format_exc())