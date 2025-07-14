import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panacare.settings')
import django
django.setup()

from django.urls import get_resolver
urlconf = get_resolver()

def list_urls(urlpatterns, prefix=''):
    for pattern in urlpatterns:
        if hasattr(pattern, 'url_patterns'):
            list_urls(pattern.url_patterns, prefix + pattern.pattern.regex.pattern)
        else:
            print(f"{prefix}{pattern.pattern} - {pattern.callback.__name__} - {pattern.name}")

# Print all URLs
print("All URLs in the project:")
list_urls(urlconf.url_patterns)