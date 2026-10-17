"""
Signals for Blood Requests
- Clear cache when data changes
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import BloodRequest

@receiver(post_save, sender=BloodRequest)
def clear_cache_on_request_save(sender, instance, **kwargs):
    """Clear home page cache when blood request is created/updated"""
    cache.delete('home_stats')

@receiver(post_delete, sender=BloodRequest)
def clear_cache_on_request_delete(sender, instance, **kwargs):
    """Clear home page cache when blood request is deleted"""
    cache.delete('home_stats')
