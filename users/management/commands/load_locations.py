from django.core.management.base import BaseCommand
from django.db import transaction
from users.models import Location
from users.locations import LocationService


class Command(BaseCommand):
    help = 'Load Kenyan counties, subcounties, wards and villages into the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force reload even if data already exists',
        )

    def handle(self, *args, **options):
        force = options['force']
        
        if not force and Location.objects.exists():
            self.stdout.write(
                self.style.WARNING(
                    'Location data already exists. Use --force to reload.'
                )
            )
            return

        if force:
            self.stdout.write('Clearing existing location data...')
            Location.objects.all().delete()

        self.stdout.write('Loading Kenyan administrative divisions...')
        
        try:
            with transaction.atomic():
                location_service = LocationService()
                location_service.sync_locations_from_api()
                
                counties_count = Location.objects.filter(level='county').count()
                subcounties_count = Location.objects.filter(level='sub_county').count()
                wards_count = Location.objects.filter(level='ward').count()
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully loaded:\n'
                        f'  - {counties_count} counties\n'
                        f'  - {subcounties_count} sub-counties\n'
                        f'  - {wards_count} wards'
                    )
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error loading locations: {str(e)}')
            )
            raise