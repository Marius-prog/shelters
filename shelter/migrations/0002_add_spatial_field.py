# Generated manually for GeoDjango spatial field

from django.db import migrations
from django.contrib.gis.db import models
import django.contrib.gis.db.models.fields


class Migration(migrations.Migration):
    dependencies = [
        ('shelter', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='shelter',
            name='location',
            field=django.contrib.gis.db.models.fields.PointField(blank=True, null=True, srid=4326),
        ),
    ]