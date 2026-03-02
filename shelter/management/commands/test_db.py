from django.core.management.base import BaseCommand
from shelter.models import Shelter

class Command(BaseCommand):
    help = 'Test database access'

    def handle(self, *args, **options):
        try:
            count = Shelter.objects.count()
            self.stdout.write(f"Shelter count: {count}")
            
            # Try to query for a specific shelter
            if count > 0:
                first_shelter = Shelter.objects.first()
                self.stdout.write(f"First shelter: {first_shelter.address}")
            
            self.stdout.write("Database access successful")
        except Exception as e:
            self.stdout.write(f"Database error: {e}")
            import traceback
            self.stdout.write(traceback.format_exc())