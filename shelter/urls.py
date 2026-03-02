from django.urls import path
from . import views

urlpatterns = [
    path('', views.map_view, name='map'),
    path('api/shelters/', views.shelter_data, name='shelter_data'),
    path('api/maps-key/', views.get_maps_key, name='get_maps_key'),
    path('api/aircraft/', views.aircraft_data, name='aircraft_data'),
]