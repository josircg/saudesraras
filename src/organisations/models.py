from django.conf import settings
from django.contrib.gis.db import models
from django.core.files.storage import default_storage
from django.urls import reverse_lazy as rl
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django_countries.fields import CountryField
from utilities.models import AbstractTranslatedModel

from .managers import OrganisationTypeQuerySet


class OrganisationType(AbstractTranslatedModel):
    type = models.TextField()

    str_field = 'type'

    objects = OrganisationTypeQuerySet.as_manager()

    class Meta:
        verbose_name = _('Organization Type')
        verbose_name_plural = _('Organization Types')
        ordering = ['type']


class Organisation(models.Model):
    name = models.CharField(_('Name'), max_length=200)
    url = models.URLField(max_length=200)
    description = models.CharField(max_length=3000)
    orgType = models.ForeignKey(OrganisationType, on_delete=models.CASCADE, verbose_name=_('Organization Type'))
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                related_name='creator', verbose_name=_('Creator'))
    dateCreated = models.DateTimeField('Created date', auto_now=True)
    dateUpdated = models.DateTimeField('Updated date', auto_now=True)
    logo = models.ImageField(upload_to='images/', max_length=300, null=True, blank=True)
    contactPoint = models.CharField(max_length=100, null=True, blank=True)
    contactPointEmail = models.EmailField(max_length=100, null=True, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    location = models.PointField(blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    country = CountryField(null=True, blank=True)
    approved = models.BooleanField(_('Approved'), null=True)

    class Meta:
        verbose_name = _('Organisation')
        verbose_name_plural = _('Organisations')

    def __str__(self):
        return f'{self.name}'

    @property
    def safe_image(self):
        if self.logo and default_storage.exists(self.logo.path):
            return self.logo
        else:
            return 'void_600.png'

    def safe_url(self):
        href = rl('edit_organisation', kwargs={'pk': self.pk})
        return mark_safe(f'<a href="{href}" target="_blank">URL</a>')

    safe_url.allow_tags = True
    safe_url.short_description = 'Site URL'

    def save(self, *args, **kwargs):
        # approved can be null (not moderated), so we can't put self.approved = ... in one line
        if not self.pk and self.creator.is_staff:
            self.approved = True

        super().save(*args, **kwargs)


class OrganisationPermission(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE)
