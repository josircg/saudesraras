from django.db import models
from django.utils.translation import ugettext_lazy as _


class Symptom(models.Model):
    description = models.TextField(_('Description'))

    def __str__(self):
        return f'{self.description}'

    class Meta:
        verbose_name = _('Symptom')
        verbose_name_plural = _('Symptoms')
        ordering = ['description']


class Disease(models.Model):
    name = models.TextField(_('Name'))
    ICD = models.CharField(_('ICD'), max_length=5, blank=True, null=True)
    other_names = models.TextField(_('Other names'), blank=True, null=True)
    description = models.TextField(_('Description'), blank=True, null=True)
    symptoms = models.ManyToManyField(Symptom, blank=True, verbose_name=_('Symptoms'))

    def __str__(self):
        return f'{self.name}'

    class Meta:
        verbose_name = _('Disease')
        verbose_name_plural = _('Diseases')
        ordering = ['name']