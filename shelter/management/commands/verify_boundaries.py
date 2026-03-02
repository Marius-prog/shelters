from django.core.management.base import BaseCommand
from django.db import models
from shelter.models import Shelter
import json


class Command(BaseCommand):
    help = 'Verify all shelters are within Lithuania and export problematic ones'

    def handle(self, *args, **options):
        # Strict Lithuania boundaries based on actual borders
        # These exclude any possibility of Kaliningrad points
        strict_bounds = {
            'min_lat': 53.89,   # Southern border
            'max_lat': 56.46,   # Northern border  
            'min_lon': 20.93,   # Western border (east of Kaliningrad)
            'max_lon': 26.84    # Eastern border
        }
        
        # Known Kaliningrad area (to specifically exclude)
        kaliningrad_region = {
            'min_lat': 54.4,
            'max_lat': 55.0,
            'min_lon': 19.8,
            'max_lon': 20.93
        }
        
        total = Shelter.objects.count()
        self.stdout.write(f"Total shelters: {total}")
        
        # Find any shelters that might appear in Kaliningrad
        problematic = []
        
        for shelter in Shelter.objects.all():
            if not shelter.latitude or not shelter.longitude:
                problematic.append({
                    'id': shelter.id,
                    'municipality': shelter.municipality,
                    'address': shelter.address,
                    'issue': 'Missing coordinates'
                })
                continue
            
            # Check if in Kaliningrad region
            if (kaliningrad_region['min_lat'] <= shelter.latitude <= kaliningrad_region['max_lat'] and
                kaliningrad_region['min_lon'] <= shelter.longitude <= kaliningrad_region['max_lon']):
                # Double check it's not a legitimate Lithuanian coastal location
                if shelter.longitude < 20.93:  # Definitely west of Lithuania
                    problematic.append({
                        'id': shelter.id,
                        'municipality': shelter.municipality,
                        'address': shelter.address,
                        'latitude': shelter.latitude,
                        'longitude': shelter.longitude,
                        'issue': 'In Kaliningrad region'
                    })
            
            # Check if outside Lithuania bounds
            elif (shelter.latitude < strict_bounds['min_lat'] or 
                  shelter.latitude > strict_bounds['max_lat'] or
                  shelter.longitude < strict_bounds['min_lon'] or 
                  shelter.longitude > strict_bounds['max_lon']):
                problematic.append({
                    'id': shelter.id,
                    'municipality': shelter.municipality,
                    'address': shelter.address,
                    'latitude': shelter.latitude,
                    'longitude': shelter.longitude,
                    'issue': 'Outside Lithuania boundaries'
                })
        
        if problematic:
            self.stdout.write(f"\nFound {len(problematic)} problematic shelters:")
            for p in problematic:
                self.stdout.write(f"ID {p['id']}: {p['municipality']} - {p['address']}")
                if 'latitude' in p:
                    self.stdout.write(f"  Coordinates: {p['latitude']}, {p['longitude']}")
                self.stdout.write(f"  Issue: {p['issue']}")
            
            # Export to JSON for review
            with open('/tmp/problematic_shelters.json', 'w') as f:
                json.dump(problematic, f, indent=2, ensure_ascii=False)
            self.stdout.write("\nExported to /tmp/problematic_shelters.json")
            
            # Option to delete
            if input("\nDelete these shelters? (yes/no): ").lower() == 'yes':
                ids_to_delete = [p['id'] for p in problematic]
                deleted = Shelter.objects.filter(id__in=ids_to_delete).delete()
                self.stdout.write(f"Deleted {deleted[0]} shelters")
        else:
            self.stdout.write("\nNo problematic shelters found!")
        
        # Check western edge shelters
        self.stdout.write("\n" + "="*50)
        self.stdout.write("WESTERN EDGE ANALYSIS:")
        western = Shelter.objects.filter(longitude__lt=21.1).order_by('longitude')
        self.stdout.write(f"Shelters with longitude < 21.1: {western.count()}")
        
        if western.exists():
            self.stdout.write("\nWesternmost 5 shelters:")
            for s in western[:5]:
                self.stdout.write(f"{s.municipality} - {s.address}")
                self.stdout.write(f"  Lat: {s.latitude}, Lon: {s.longitude}")
        
        # Summary statistics
        self.stdout.write("\n" + "="*50)
        self.stdout.write("FINAL STATISTICS:")
        if Shelter.objects.exists():
            stats = Shelter.objects.aggregate(
                min_lat=models.Min('latitude'),
                max_lat=models.Max('latitude'),
                min_lon=models.Min('longitude'),
                max_lon=models.Max('longitude'),
                avg_lat=models.Avg('latitude'),
                avg_lon=models.Avg('longitude')
            )
            self.stdout.write(f"Latitude range: {stats['min_lat']:.4f} to {stats['max_lat']:.4f}")
            self.stdout.write(f"Longitude range: {stats['min_lon']:.4f} to {stats['max_lon']:.4f}")
            self.stdout.write(f"Center point: {stats['avg_lat']:.4f}, {stats['avg_lon']:.4f}")
            
            # Municipality summary
            mun_counts = Shelter.objects.values('municipality').annotate(
                count=models.Count('id')
            ).order_by('-count')[:5]
            self.stdout.write("\nTop 5 municipalities:")
            for m in mun_counts:
                self.stdout.write(f"  {m['municipality']}: {m['count']} shelters")