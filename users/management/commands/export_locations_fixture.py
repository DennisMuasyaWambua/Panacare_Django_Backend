import json
import requests
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Export Kenyan location data to fixtures'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            default='users/fixtures/locations.json',
            help='Output fixture file path',
        )

    def handle(self, *args, **options):
        output_path = options['output']
        
        self.stdout.write('Fetching location data from API...')
        
        try:
            api_url = "https://kenyaareadata.vercel.app/api/areas?apiKey=keyPub1569gsvndc123kg9sjhg"
            response = requests.get(api_url, timeout=30)
            
            if response.status_code != 200:
                self.stdout.write(
                    self.style.ERROR(f'API request failed: {response.status_code}')
                )
                return
            
            data = response.json()
            fixtures = []
            pk_counter = 1
            
            self.stdout.write('Processing location data...')
            
            for county_name, subcounties in data.items():
                county_pk = pk_counter
                pk_counter += 1
                
                fixtures.append({
                    "model": "users.location",
                    "pk": county_pk,
                    "fields": {
                        "name": county_name,
                        "level": "county",
                        "parent": None
                    }
                })
                
                for subcounty_name, wards in subcounties.items():
                    subcounty_pk = pk_counter
                    pk_counter += 1
                    
                    fixtures.append({
                        "model": "users.location",
                        "pk": subcounty_pk,
                        "fields": {
                            "name": subcounty_name,
                            "level": "sub_county",
                            "parent": county_pk
                        }
                    })
                    
                    for ward_name in wards:
                        ward_pk = pk_counter
                        pk_counter += 1
                        
                        fixtures.append({
                            "model": "users.location",
                            "pk": ward_pk,
                            "fields": {
                                "name": ward_name,
                                "level": "ward",
                                "parent": subcounty_pk
                            }
                        })
            
            with open(output_path, 'w') as f:
                json.dump(fixtures, f, indent=2)
            
            counties = len([f for f in fixtures if f['fields']['level'] == 'county'])
            subcounties = len([f for f in fixtures if f['fields']['level'] == 'sub_county'])
            wards = len([f for f in fixtures if f['fields']['level'] == 'ward'])
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully created fixture with:\n'
                    f'  - {counties} counties\n'
                    f'  - {subcounties} sub-counties\n' 
                    f'  - {wards} wards\n'
                    f'  - Saved to: {output_path}'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating fixture: {str(e)}')
            )
            raise