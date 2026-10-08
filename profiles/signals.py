from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import SupervisorProfile


@receiver(post_save, sender=settings.AUTH_USER_MODEL, dispatch_uid='profiles.create_supervisor_profile')
def create_supervisor_profile(sender, instance, created, **kwargs):
    if instance.role == 'supervisor':
        SupervisorProfile.objects.get_or_create(user=instance)