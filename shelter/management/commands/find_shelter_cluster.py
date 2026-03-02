from django.core.management.base import BaseCommand
from shelter.models import Shelter
from django.db.models import Count, Q

class Command(BaseCommand):
    help = 'Find clusters of shelters that might be misplaced'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=22,
            help='Number of shelters in the cluster to search for',
        )

    def handle(self, *args, **options):
        target_count = options['count']

        self.stdout.write(f"\nSearching for clusters of {target_count} shelters...")

        # Check municipalities with exactly this count
        municipalities = (Shelter.objects
                         .values('municipality')
                         .annotate(count=Count('id'))
                         .filter(count=target_count))

        if municipalities:
            self.stdout.write(f"\n--- Municipalities with exactly {target_count} shelters (valid + invalid) ---")
            for mun in municipalities:
                mun_name = mun['municipality']
                valid_count = Shelter.objects.filter(
                    municipality=mun_name,
                    is_valid_coordinates=True
                ).count()
                invalid_count = Shelter.objects.filter(
                    municipality=mun_name,
                    is_valid_coordinates=False
                ).count()

                self.stdout.write(
                    f"\n{mun_name}: {valid_count} valid, {invalid_count} invalid"
                )

                # Show first 5 shelters from this municipality
                shelters = Shelter.objects.filter(municipality=mun_name)[:5]
                for s in shelters:
                    status = "✓ valid" if s.is_valid_coordinates else "✗ invalid"
                    self.stdout.write(
                        f"  ID:{s.id} - {s.address} - "
                        f"lat:{s.latitude:.6f}, lon:{s.longitude:.6f} [{status}]"
                    )

        # Check for clusters by proximity
        self.stdout.write(f"\n--- Checking for invalid shelter clusters ---")
        invalid_shelters = Shelter.objects.filter(is_valid_coordinates=False)

        if invalid_shelters.count() == 0:
            self.stdout.write("No invalid shelters found")
        else:
            self.stdout.write(f"Found {invalid_shelters.count()} invalid shelters:")
            for shelter in invalid_shelters:
                self.stdout.write(
                    f"  ID:{shelter.id} - {shelter.address} ({shelter.municipality}) - "
                    f"lat:{shelter.latitude:.6f}, lon:{shelter.longitude:.6f}"
                )
