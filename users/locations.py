import requests
import json
from django.core.cache import cache
from django.conf import settings
from .models import Location


class LocationService:
    """
    Service class for managing hierarchical location data
    """
    BASE_URL = "https://kenyaareadata.vercel.app/api/areas?apiKey=keyPub1569gsvndc123kg9sjhg"
    CACHE_TIMEOUT = 3600 * 24  # 24 hours
    
    @classmethod
    def fetch_external_locations(cls):
        """
        Fetch location data from external API
        """
        try:
            response = requests.get(cls.BASE_URL, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error fetching data: {response.status_code}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            return None
    
    @classmethod
    def sync_locations_from_api(cls):
        """
        Sync location data from external API to database
        """
        external_data = cls.fetch_external_locations()
        if not external_data:
            return False
            
        try:
            for county_data in external_data:
                county, created = Location.objects.get_or_create(
                    name=county_data['name'],
                    level='county',
                    parent=None,
                    defaults={'name': county_data['name']}
                )
                
                for subcounty_data in county_data.get('subcounties', []):
                    subcounty, created = Location.objects.get_or_create(
                        name=subcounty_data['name'],
                        level='sub_county',
                        parent=county,
                        defaults={'name': subcounty_data['name']}
                    )
                    
                    for ward_data in subcounty_data.get('wards', []):
                        ward, created = Location.objects.get_or_create(
                            name=ward_data['name'],
                            level='ward',
                            parent=subcounty,
                            defaults={'name': ward_data['name']}
                        )
                        
                        for village_name in ward_data.get('villages', []):
                            village, created = Location.objects.get_or_create(
                                name=village_name,
                                level='village',
                                parent=ward,
                                defaults={'name': village_name}
                            )
            
            cache.set('locations_synced', True, cls.CACHE_TIMEOUT)
            return True
            
        except Exception as e:
            print(f"Error syncing locations: {e}")
            return False
    
    @classmethod
    def get_counties(cls):
        """
        Get all counties from database
        """
        cache_key = 'counties_list'
        counties = cache.get(cache_key)
        
        if counties is None:
            counties = list(Location.objects.filter(
                level='county'
            ).values('id', 'name').order_by('name'))
            cache.set(cache_key, counties, cls.CACHE_TIMEOUT)
        
        return counties
    
    @classmethod
    def get_subcounties(cls, county_id=None):
        """
        Get subcounties, optionally filtered by county
        """
        cache_key = f'subcounties_list_{county_id}' if county_id else 'subcounties_list_all'
        subcounties = cache.get(cache_key)
        
        if subcounties is None:
            query = Location.objects.filter(level='sub_county')
            if county_id:
                query = query.filter(parent_id=county_id)
            
            subcounties = list(query.values(
                'id', 'name', 'parent_id'
            ).order_by('name'))
            cache.set(cache_key, subcounties, cls.CACHE_TIMEOUT)
        
        return subcounties
    
    @classmethod
    def get_wards(cls, subcounty_id=None):
        """
        Get wards, optionally filtered by subcounty
        """
        cache_key = f'wards_list_{subcounty_id}' if subcounty_id else 'wards_list_all'
        wards = cache.get(cache_key)
        
        if wards is None:
            query = Location.objects.filter(level='ward')
            if subcounty_id:
                query = query.filter(parent_id=subcounty_id)
            
            wards = list(query.values(
                'id', 'name', 'parent_id'
            ).order_by('name'))
            cache.set(cache_key, wards, cls.CACHE_TIMEOUT)
        
        return wards
    
    @classmethod
    def get_villages(cls, ward_id=None):
        """
        Get villages, optionally filtered by ward
        """
        cache_key = f'villages_list_{ward_id}' if ward_id else 'villages_list_all'
        villages = cache.get(cache_key)
        
        if villages is None:
            query = Location.objects.filter(level='village')
            if ward_id:
                query = query.filter(parent_id=ward_id)
            
            villages = list(query.values(
                'id', 'name', 'parent_id'
            ).order_by('name'))
            cache.set(cache_key, villages, cls.CACHE_TIMEOUT)
        
        return villages
    
    @classmethod
    def get_location_hierarchy(cls, location_id):
        """
        Get the full hierarchy for a given location
        """
        try:
            location = Location.objects.get(id=location_id)
            hierarchy = []
            
            current = location
            while current:
                hierarchy.insert(0, {
                    'id': str(current.id),
                    'name': current.name,
                    'level': current.level
                })
                current = current.parent
            
            return hierarchy
            
        except Location.DoesNotExist:
            return []
    
    @classmethod
    def ensure_locations_exist(cls):
        """
        Ensure locations are available in database, sync if needed
        """
        if not cache.get('locations_synced') and not Location.objects.exists():
            return cls.sync_locations_from_api()
        return True


def get_locations():
    """
    Legacy function for backward compatibility
    """
    return LocationService.fetch_external_locations()