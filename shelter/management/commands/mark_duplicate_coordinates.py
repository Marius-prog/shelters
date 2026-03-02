from django.core.management.base import BaseCommand
from shelter.models import Shelter
from django.db.models import Count

class Command(BaseCommand):
    help = 'Find and mark shelters with duplicate coordinates (same lat/lon) as invalid'

    def add_arguments(self, parser):
        parser.add_argument(
            '--min-duplicates',
            type=int,
            default=2,
            help='Minimum number of shelters at the same coordinates to mark as invalid (default: 2)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be marked without making changes',
        )

    def handle(self, *args, **options):
        min_duplicates = options['min_duplicates']
        dry_run = options['dry_run']

        self.stdout.write(f"\nSearching for coordinates with {min_duplicates}+ shelters...")

        # Find coordinates with multiple shelters
        duplicate_coords = (Shelter.objects
                          .values('latitude', 'longitude')
                          .annotate(count=Count('id'))
                          .filter(count__gte=min_duplicates,
                                 latitude__isnull=False,
                                 longitude__isnull=False))

        if not duplicate_coords:
            self.stdout.write(self.style.SUCCESS('\n✓ No duplicate coordinates found!'))
            return

        total_to_mark = 0
        for coords in duplicate_coords:
            lat = coords['latitude']
            lon = coords['longitude']
            count = coords['count']

            shelters = Shelter.objects.filter(
                latitude=lat,
                longitude=lon
            )

            self.stdout.write(f"\n--- {count} shelters at lat: {lat:.6f}, lon: {lon:.6f} ---")

            for shelter in shelters:
                status = "✓ valid" if shelter.is_valid_coordinates else "✗ invalid"
                self.stdout.write(
                    f"  ID: {shelter.id} - {shelter.address or 'N/A'} "
                    f"({shelter.municipality}) [{status}]"
                )

            # Count how many would be marked
            valid_count = shelters.filter(is_valid_coordinates=True).count()
            total_to_mark += valid_count

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'\n[DRY RUN] Would mark {total_to_mark} shelters as invalid. '
                    'Run without --dry-run to apply changes.'
                )
            )
        else:
            # Mark all shelters with duplicate coordinates as invalid
            marked_count = 0
            for coords in duplicate_coords:
                updated = Shelter.objects.filter(
                    latitude=coords['latitude'],
                    longitude=coords['longitude'],
                    is_valid_coordinates=True
                ).update(is_valid_coordinates=False)
                marked_count += updated

            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✓ Marked {marked_count} shelters with duplicate coordinates as invalid'
                )
            )

        self.stdout.write(
            f"\nReason: Multiple different shelters cannot have identical coordinates. "
            f"These are likely default/fallback coordinates from bad data."
        )
