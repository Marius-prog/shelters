from django.test import TestCase
from django.contrib.gis.geos import Point
from shelter.models import Shelter

class ShelterModelTest(TestCase):
    def setUp(self):
        # Create a test shelter
        self.shelter = Shelter.objects.create(
            object_id="test123",
            address="Test Street 123",
            municipality="Test City",
            capacity=100,
            purpose="Test Shelter",
            condition="Good",
            location=Point(24.0, 54.0, srid=4326)  # Example point in Lithuania
        )
    
    def test_shelter_creation(self):
        """Test that a shelter can be created with the correct attributes"""
        self.assertEqual(self.shelter.object_id, "test123")
        self.assertEqual(self.shelter.address, "Test Street 123")
        self.assertEqual(self.shelter.municipality, "Test City")
        self.assertEqual(self.shelter.capacity, 100)
        self.assertEqual(self.shelter.purpose, "Test Shelter")
        self.assertEqual(self.shelter.condition, "Good")
        
        # Test the Point location
        self.assertEqual(self.shelter.location.x, 24.0)  # Longitude
        self.assertEqual(self.shelter.location.y, 54.0)  # Latitude
        self.assertEqual(self.shelter.location.srid, 4326)
    
    def test_shelter_string_representation(self):
        """Test the string representation of a shelter"""
        self.assertEqual(str(self.shelter), "Test Street 123 (Test City)")
