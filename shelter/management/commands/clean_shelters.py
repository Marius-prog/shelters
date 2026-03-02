from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Point, Polygon
from shelter.models import Shelter


class Command(BaseCommand):
    help = 'Remove shelters outside Lithuania boundaries and fix data issues'

    def handle(self, *args, **options):
        # Lithuania's approximate boundaries
        # More precise boundaries based on actual Lithuanian territory
        lithuania_bounds = {
            'min_lat': 53.89,  # Southern boundary
            'max_lat': 56.45,  # Northern boundary
            'min_lon': 20.93,  # Western boundary (excluding Kaliningrad)
            'max_lon': 26.82   # Eastern boundary
        }
        
        # Create a polygon for Lithuania (simplified rectangle)
        lithuania_polygon = Polygon((
            (lithuania_bounds['min_lon'], lithuania_bounds['min_lat']),
            (lithuania_bounds['max_lon'], lithuania_bounds['min_lat']),
            (lithuania_bounds['max_lon'], lithuania_bounds['max_lat']),
            (lithuania_bounds['min_lon'], lithuania_bounds['max_lat']),
            (lithuania_bounds['min_lon'], lithuania_bounds['min_lat'])
        ))
        
        self.stdout.write(f"Total shelters before cleaning: {Shelter.objects.count()}")
        
        # Find shelters outside boundaries
        outside_shelters = []
        invalid_coords = []
        
        for shelter in Shelter.objects.all():
            # Check for invalid coordinates
            if shelter.latitude is None or shelter.longitude is None:
                invalid_coords.append(shelter)
                continue
            
            # Check if coordinates are outside Lithuania
            if (shelter.latitude < lithuania_bounds['min_lat'] or 
                shelter.latitude > lithuania_bounds['max_lat'] or
                shelter.longitude < lithuania_bounds['min_lon'] or 
                shelter.longitude > lithuania_bounds['max_lon']):
                outside_shelters.append(shelter)
                self.stdout.write(
                    f"Outside: {shelter.municipality} - {shelter.address} "
                    f"(Lat: {shelter.latitude}, Lon: {shelter.longitude})"
                )
        
        # Check for shelters with suspicious municipality names
        suspicious_municipalities = [
            'Калининград',  # Kaliningrad in Russian
            'Kaliningrad',  # Kaliningrad in English
            'Калининградская',
            'Kaliningrado'
        ]
        
        for municipality in suspicious_municipalities:
            suspicious = Shelter.objects.filter(municipality__icontains=municipality)
            if suspicious.exists():
                self.stdout.write(f"Found {suspicious.count()} shelters in {municipality}")
                for s in suspicious:
                    if s not in outside_shelters:
                        outside_shelters.append(s)
        
        # Also check for shelters that might be miscoded
        # Western Lithuania cities that are legitimate
        western_cities = ['Mažeikių', 'Klaipėdos', 'Palangos', 'Kretingos', 'Skuodo', 'Šilutės', 'Neringos']
        
        # Check specifically for Kaliningrad area (west of Lithuania, around 54.7 lat, 20.5 lon)
        kaliningrad_area = Shelter.objects.filter(
            latitude__gte=54.5,
            latitude__lte=55.0,
            longitude__gte=20.0,
            longitude__lte=20.93
        )
        
        for shelter in kaliningrad_area:
            # Check if it's not in a legitimate western Lithuanian city
            is_legitimate = any(city in shelter.municipality for city in western_cities)
            if not is_legitimate and shelter not in outside_shelters:
                outside_shelters.append(shelter)
                self.stdout.write(
                    f"Suspicious location: {shelter.municipality} - {shelter.address} "
                    f"(Lat: {shelter.latitude}, Lon: {shelter.longitude})"
                )
        
        # Delete invalid coordinate shelters
        if invalid_coords:
            self.stdout.write(f"\nDeleting {len(invalid_coords)} shelters with invalid coordinates...")
            for shelter in invalid_coords:
                shelter.delete()
        
        # Delete outside shelters
        if outside_shelters:
            self.stdout.write(f"\nDeleting {len(outside_shelters)} shelters outside Lithuania...")
            for shelter in outside_shelters:
                shelter.delete()
        
        self.stdout.write(f"\nTotal shelters after cleaning: {Shelter.objects.count()}")
        self.stdout.write(self.style.SUCCESS('Successfully cleaned shelter data'))
        
        # Show summary of remaining data
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


from django.db import models