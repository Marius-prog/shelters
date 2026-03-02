from django.core.management.base import BaseCommand
from django.db import connection
from shelter.models import Shelter

class Command(BaseCommand):
    help = 'Fix database structure'

    def handle(self, *args, **options):
        cursor = connection.cursor()
        
        # Check current tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        self.stdout.write(f"Existing tables: {tables}")
        
        # Drop and recreate the shelter table with correct structure
        try:
            cursor.execute("DROP TABLE IF EXISTS shelter_shelter;")
            self.stdout.write("Dropped existing shelter table")
        except Exception as e:
            self.stdout.write(f"Error dropping table: {e}")
        
        # Create table with exact Django structure
        try:
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
            self.stdout.write("Created shelter table with correct structure")
            
            # Test that Django can access it
            count = Shelter.objects.count()
            self.stdout.write(f"Django can access table. Current count: {count}")
            
        except Exception as e:
            self.stdout.write(f"Error creating table: {e}")
            
        # Show final structure
        try:
            cursor.execute("PRAGMA table_info(shelter_shelter);")
            columns = cursor.fetchall()
            self.stdout.write(f"Table structure: {columns}")
        except Exception as e:
            self.stdout.write(f"Error checking structure: {e}")