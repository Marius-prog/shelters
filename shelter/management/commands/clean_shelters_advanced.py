from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Point
from django.db import models
from shelter.models import Shelter
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Remove shelters outside Lithuania using advanced boundary checking'

    def handle(self, *args, **options):
        # List of all legitimate Lithuanian municipalities
        lithuanian_municipalities = [
            # Cities
            'Vilniaus m. sav.', 'Kauno m. sav.', 'Klaipėdos m. sav.', 'Šiaulių m. sav.',
            'Panevėžio m. sav.', 'Alytaus m. sav.', 'Marijampolės sav.', 'Mažeikių r. sav.',
            'Utenos r. sav.', 'Telšių r. sav.', 'Tauragės r. sav.', 'Visagino sav.',
            'Palangos m. sav.', 'Neringos sav.', 'Birštono sav.', 'Druskininkų sav.',
            'Elektrėnų sav.', 'Kalvarijos sav.', 'Kazlų Rūdos sav.', 'Pagėgių sav.',
            'Rietavo sav.',
            
            # Districts (rajonai)
            'Akmenės r. sav.', 'Alytaus r. sav.', 'Anykščių r. sav.', 'Biržų r. sav.',
            'Ignalinos r. sav.', 'Jonavos r. sav.', 'Joniškio r. sav.', 'Jurbarko r. sav.',
            'Kaišiadorių r. sav.', 'Kauno r. sav.', 'Kėdainių r. sav.', 'Kelmės r. sav.',
            'Klaipėdos r. sav.', 'Kretingos r. sav.', 'Kupiškio r. sav.', 'Lazdijų r. sav.',
            'Marijampolės r. sav.', 'Molėtų r. sav.', 'Pakruojo r. sav.', 'Panevėžio r. sav.',
            'Pasvalio r. sav.', 'Plungės r. sav.', 'Prienų r. sav.', 'Radviliškio r. sav.',
            'Raseinių r. sav.', 'Rokiškio r. sav.', 'Skuodo r. sav.', 'Šakių r. sav.',
            'Šalčininkų r. sav.', 'Šiaulių r. sav.', 'Šilalės r. sav.', 'Šilutės r. sav.',
            'Širvintų r. sav.', 'Švenčionių r. sav.', 'Tauragės r. sav.', 'Telšių r. sav.',
            'Trakų r. sav.', 'Ukmergės r. sav.', 'Utenos r. sav.', 'Varėnos r. sav.',
            'Vilkaviškio r. sav.', 'Vilniaus r. sav.', 'Zarasų r. sav.'
        ]
        
        # More precise Lithuania boundaries
        # These are the actual extreme points of Lithuania
        lithuania_bounds = {
            'min_lat': 53.8968,  # Southernmost point near Lazdijai
            'max_lat': 56.4504,  # Northernmost point near Biržai
            'min_lon': 20.9310,  # Westernmost point in Neringa
            'max_lon': 26.8355   # Easternmost point near Ignalina
        }
        
        self.stdout.write(f"Total shelters before cleaning: {Shelter.objects.count()}")
        
        # Track different types of issues
        outside_bounds = []
        invalid_municipality = []
        invalid_coords = []
        suspicious_locations = []
        
        for shelter in Shelter.objects.all():
            # Check for invalid coordinates
            if shelter.latitude is None or shelter.longitude is None:
                invalid_coords.append(shelter)
                continue
            
            # Check municipality
            if shelter.municipality and shelter.municipality not in lithuanian_municipalities:
                # Check for variations or typos
                municipality_found = False
                for valid_mun in lithuanian_municipalities:
                    if (shelter.municipality in valid_mun or 
                        valid_mun.replace(' sav.', '') in shelter.municipality or
                        valid_mun.replace(' r.', '') in shelter.municipality):
                        municipality_found = True
                        break
                
                if not municipality_found:
                    invalid_municipality.append(shelter)
                    self.stdout.write(
                        f"Invalid municipality: {shelter.municipality} - {shelter.address} "
                        f"(Lat: {shelter.latitude}, Lon: {shelter.longitude})"
                    )
            
            # Check if coordinates are outside Lithuania
            if (shelter.latitude < lithuania_bounds['min_lat'] or 
                shelter.latitude > lithuania_bounds['max_lat'] or
                shelter.longitude < lithuania_bounds['min_lon'] or 
                shelter.longitude > lithuania_bounds['max_lon']):
                outside_bounds.append(shelter)
                self.stdout.write(
                    f"Outside bounds: {shelter.municipality} - {shelter.address} "
                    f"(Lat: {shelter.latitude}, Lon: {shelter.longitude})"
                )
            
            # Special check for Kaliningrad area
            # Kaliningrad is approximately at 54.7104° N, 20.4522° E
            if (54.5 <= shelter.latitude <= 55.0 and 
                20.0 <= shelter.longitude <= 20.93):
                # This is in the Kaliningrad latitude range and west of Lithuania
                # Check if it's a legitimate Lithuanian coastal location
                coastal_municipalities = ['Neringos sav.', 'Klaipėdos r. sav.', 'Palangos m. sav.']
                if shelter.municipality not in coastal_municipalities:
                    suspicious_locations.append(shelter)
                    self.stdout.write(
                        f"Suspicious (possible Kaliningrad): {shelter.municipality} - {shelter.address} "
                        f"(Lat: {shelter.latitude}, Lon: {shelter.longitude})"
                    )
        
        # Summary
        self.stdout.write("\n" + "="*50)
        self.stdout.write("SUMMARY OF ISSUES FOUND:")
        self.stdout.write(f"Invalid coordinates: {len(invalid_coords)}")
        self.stdout.write(f"Invalid municipality: {len(invalid_municipality)}")
        self.stdout.write(f"Outside bounds: {len(outside_bounds)}")
        self.stdout.write(f"Suspicious locations: {len(suspicious_locations)}")
        self.stdout.write("="*50 + "\n")
        
        # Combine all problematic shelters (avoiding duplicates)
        all_problematic = set()
        all_problematic.update(invalid_coords)
        all_problematic.update(invalid_municipality)
        all_problematic.update(outside_bounds)
        all_problematic.update(suspicious_locations)
        
        if all_problematic:
            self.stdout.write(f"\nTotal problematic shelters to remove: {len(all_problematic)}")
            
            if input("\nDo you want to delete these shelters? (yes/no): ").lower() == 'yes':
                deleted_count = 0
                for shelter in all_problematic:
                    try:
                        shelter.delete()
                        deleted_count += 1
                    except Exception as e:
                        self.stdout.write(f"Error deleting shelter {shelter.id}: {e}")
                
                self.stdout.write(f"\nDeleted {deleted_count} shelters")
        else:
            self.stdout.write("\nNo problematic shelters found!")
        
        self.stdout.write(f"\nTotal shelters after cleaning: {Shelter.objects.count()}")
        
        # Show final boundaries
        remaining = Shelter.objects.all()
        if remaining.exists():
            bounds = remaining.aggregate(
                min_lat=models.Min('latitude'),
                max_lat=models.Max('latitude'),
                min_lon=models.Min('longitude'),
                max_lon=models.Max('longitude')
            )
            self.stdout.write(f"\nRemaining data boundaries:")
            self.stdout.write(f"Latitude: {bounds['min_lat']} to {bounds['max_lat']}")
            self.stdout.write(f"Longitude: {bounds['min_lon']} to {bounds['max_lon']}")
            
            # Show westernmost shelters
            western = remaining.order_by('longitude')[:5]
            self.stdout.write("\nWesternmost remaining shelters:")
            for s in western:
                self.stdout.write(f"{s.municipality} - Lat: {s.latitude}, Lon: {s.longitude}")