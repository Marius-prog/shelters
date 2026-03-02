from django.core.management.base import BaseCommand
from shelter.models import Shelter

class Command(BaseCommand):
    help = 'Mark shelters with coordinates outside Lithuania bounds as invalid'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be marked without making changes',
        )

    def handle(self, *args, **options):
        # Lithuania coordinate bounds from CLAUDE.md
        MIN_LAT = 53.89
        MAX_LAT = 56.45
        MIN_LON = 20.93
        MAX_LON = 26.82

        dry_run = options['dry_run']

        # Find all shelters with coordinates
        all_shelters = Shelter.objects.filter(
            latitude__isnull=False,
            longitude__isnull=False
        )

        total_count = all_shelters.count()
        self.stdout.write(f"\nTotal shelters with coordinates: {total_count}")

        # Find shelters outside Lithuania bounds
        invalid_shelters = all_shelters.exclude(
            latitude__gte=MIN_LAT,
            latitude__lte=MAX_LAT,
            longitude__gte=MIN_LON,
            longitude__lte=MAX_LON
        )

        invalid_count = invalid_shelters.count()
        valid_count = total_count - invalid_count

        self.stdout.write(f"Shelters within Lithuania bounds: {valid_count}")
        self.stdout.write(f"Shelters outside Lithuania bounds: {invalid_count}")

        if invalid_count > 0:
            self.stdout.write("\n--- Shelters to be marked as invalid ---")

            for shelter in invalid_shelters:
                self.stdout.write(
                    f"  • {shelter.address} ({shelter.municipality}) - "
                    f"lat: {shelter.latitude:.6f}, lon: {shelter.longitude:.6f}"
                )

            if dry_run:
                self.stdout.write(
                    self.style.WARNING('\n[DRY RUN] Would mark these shelters as invalid. '
                                      'Run without --dry-run to apply changes.')
                )
            else:
                # Mark shelters as invalid
                updated = invalid_shelters.update(is_valid_coordinates=False)
                self.stdout.write(
                    self.style.SUCCESS(f'\n✓ Marked {updated} shelters as invalid')
                )

                # Also ensure all valid shelters are marked as valid
                valid_updated = all_shelters.filter(
                    latitude__gte=MIN_LAT,
                    latitude__lte=MAX_LAT,
                    longitude__gte=MIN_LON,
                    longitude__lte=MAX_LON
                ).update(is_valid_coordinates=True)

                self.stdout.write(
                    self.style.SUCCESS(f'✓ Confirmed {valid_updated} shelters as valid')
                )
        else:
            self.stdout.write(
                self.style.SUCCESS('\n✓ All shelters have valid coordinates within Lithuania bounds!')
            )

        # Show statistics
        self.stdout.write(f"\n--- Summary ---")
        self.stdout.write(f"Lithuania bounds:")
        self.stdout.write(f"  Latitude: {MIN_LAT} to {MAX_LAT}")
        self.stdout.write(f"  Longitude: {MIN_LON} to {MAX_LON}")

        if not dry_run and invalid_count > 0:
            self.stdout.write(f"\nThese shelters will not appear on the map but remain in the database.")
