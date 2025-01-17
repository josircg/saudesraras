from django.conf import settings
from django.db import models
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django.core.files.storage import default_storage

from .managers import EventQuerySet


class Event(models.Model):
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True)
    title = models.CharField(max_length=200)
    description = models.CharField(max_length=3000)
    place = models.CharField(max_length=200, blank=True)
    start_date = models.DateTimeField('Start date')
    end_date = models.DateTimeField('End date')
    hour = models.TimeField(null=True, blank=True)
    url = models.URLField(null=True, blank=True)
    image = models.ImageField(upload_to='images/', null=True, blank=True)

    featured = models.BooleanField(null=True, default=False)
    approved = models.BooleanField(_('Approved'), null=True)

    objects = EventQuerySet.as_manager()

    class Meta:
        ordering = ['start_date']
        verbose_name = _('Event')

    def __str__(self):
        return self.title

    def safe_url(self):
        return mark_safe(f'<a href="/editEvent/{self.id}" target="_blank">URL</a>')
    safe_url.allow_tags = True
    safe_url.short_description = 'Site URL'

    @property
    def safe_image(self):
        if self.logo and default_storage.exists(self.logo.path):
            return self.logo
        else:
            return 'void_600.png'

    def save(self, *args, **kwargs):
        # approved can be null (not moderated), so we can't put self.approved = ... in one line
        if not self.pk and self.creator.is_staff:
            self.approved = True

        super().save(*args, **kwargs)
