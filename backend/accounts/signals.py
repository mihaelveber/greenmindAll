from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

User = get_user_model()


@receiver(post_save, sender=User)
def set_default_standards(sender, instance, created, **kwargs):
    """Set ESRS as default standard for new users"""
    if created and not instance.allowed_standards:
        # Set ESRS as default
        instance.allowed_standards = ['ESRS']
        instance.save(update_fields=['allowed_standards'])
