from django.contrib.gis.db import models

class Shelter(models.Model):
    object_id = models.CharField(max_length=100, unique=True)
    address = models.CharField(max_length=255)
    municipality = models.CharField(max_length=100)
    capacity = models.IntegerField(null=True, blank=True)
    purpose = models.CharField(max_length=255, blank=True)
    condition = models.CharField(max_length=100, blank=True)
    
    # GeoDjango PointField for spatial data
    location = models.PointField(null=True, blank=True, srid=4326)
    
    # Keep separate lat/lon fields for backward compatibility and non-spatial views
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    # Flag to mark shelters with valid coordinates (within Lithuania bounds)
    is_valid_coordinates = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.address} ({self.municipality})"
    
    class Meta:
        ordering = ['municipality', 'address']