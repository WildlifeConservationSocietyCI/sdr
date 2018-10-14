from django.contrib.gis.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist


class Organization(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class UserProfile(models.Model):
    user = models.OneToOneField(User)
    organization = models.ForeignKey(Organization, null=True, blank=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.get_full_name()


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    try:
        instance.userprofile.save()
    except ObjectDoesNotExist:
        pass


class Period(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Reference(models.Model):
    zotero = models.CharField(max_length=8, verbose_name='zotero ID')
    name = models.CharField(max_length=255, verbose_name='reference')
    name_short = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    last_modified = models.DateTimeField(auto_now=True, verbose_name='last modified')

    def __str__(self):
        return self.name_short

    class Meta:
        ordering = ['name']
