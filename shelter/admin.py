from django.contrib import admin
from .models import Shelter

@admin.register(Shelter)
class ShelterAdmin(admin.ModelAdmin):
    list_display = ('address', 'municipality', 'capacity', 'condition', 'latitude', 'longitude')
    list_filter = ('municipality', 'condition')
    search_fields = ['address', 'municipality']