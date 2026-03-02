from django.core.management.base import BaseCommand
from shelter.models import Shelter

class Command(BaseCommand):
    help = 'Manually mark or unmark a shelter as having invalid coordinates'

    def add_arguments(self, parser):
        parser.add_argument(
            '--address',
            type=str,
            help='Address of the shelter to toggle (partial match)',
        )
        parser.add_argument(
            '--id',
            type=int,
            help='ID of the shelter to toggle',
        )
        parser.add_argument(
            '--mark-invalid',
            action='store_true',
            help='Mark the shelter as invalid (default)',
        )
        parser.add_argument(
            '--mark-valid',
            action='store_true',
            help='Mark the shelter as valid',
        )
        parser.add_argument(
            '--list',
            action='store_true',
            help='List all shelters with invalid coordinates',
        )

    def handle(self, *args, **options):
        if options['list']:
            invalid_shelters = Shelter.objects.filter(is_valid_coordinates=False)
            count = invalid_shelters.count()

            if count == 0:
                self.stdout.write(self.style.SUCCESS('No shelters marked as invalid'))
            else:
                self.stdout.write(f"\n{count} shelter(s) marked as invalid:")
                for shelter in invalid_shelters:
                    self.stdout.write(
                        f"  ID: {shelter.id} - {shelter.address} ({shelter.municipality}) - "
                        f"lat: {shelter.latitude}, lon: {shelter.longitude}"
                    )
            return

        # Get the shelter to toggle
        shelter = None
        if options['id']:
            try:
                shelter = Shelter.objects.get(id=options['id'])
            except Shelter.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Shelter with ID {options['id']} not found"))
                return
        elif options['address']:
            shelters = Shelter.objects.filter(address__icontains=options['address'])
            count = shelters.count()

            if count == 0:
                self.stdout.write(self.style.ERROR(f"No shelters found matching '{options['address']}'"))
                return
            elif count > 1:
                self.stdout.write(self.style.WARNING(f"Multiple shelters found matching '{options['address']}':"))
                for s in shelters[:10]:  # Show max 10
                    self.stdout.write(f"  ID: {s.id} - {s.address} ({s.municipality})")
                self.stdout.write("\nPlease use --id to specify which one to toggle")
                return
            else:
                shelter = shelters.first()
        else:
            self.stdout.write(self.style.ERROR('Please provide either --address or --id'))
            return

        # Toggle the validity
        if options['mark_valid']:
            new_value = True
            action = "valid"
        else:
            new_value = False
            action = "invalid"

        old_value = shelter.is_valid_coordinates
        shelter.is_valid_coordinates = new_value
        shelter.save()

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✓ Marked shelter as {action}:\n"
                f"  ID: {shelter.id}\n"
                f"  Address: {shelter.address}\n"
                f"  Municipality: {shelter.municipality}\n"
                f"  Coordinates: lat {shelter.latitude}, lon {shelter.longitude}\n"
                f"  Previous state: {'valid' if old_value else 'invalid'}\n"
                f"  New state: {'valid' if new_value else 'invalid'}"
            )
        )

        if not new_value:
            self.stdout.write("\nThis shelter will no longer appear on the map.")
        else:
            self.stdout.write("\nThis shelter will now appear on the map.")
