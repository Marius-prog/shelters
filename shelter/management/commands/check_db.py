from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Check database tables'

    def handle(self, *args, **options):
        cursor = connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        self.stdout.write(f"Existing tables: {tables}")
        
        # Try to create the table manually if it doesn't exist
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS shelter_shelter (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    object_id VARCHAR(100) UNIQUE,
                    address VARCHAR(255),
                    municipality VARCHAR(100),
                    capacity INTEGER,
                    purpose VARCHAR(255),
                    condition VARCHAR(100),
                    latitude REAL,
                    longitude REAL
                );
            """)
            self.stdout.write("Table created successfully")
        except Exception as e:
            self.stdout.write(f"Error creating table: {e}")