from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.db import models
from django.utils.translation import ugettext_lazy as _


class Translation(models.Model):
    language = models.CharField(max_length=5, choices=settings.TRANSLATED_LANGUAGES, verbose_name=_('Language'))
    text = models.TextField(verbose_name=_('Translated Text'))
    content_type = models.ForeignKey('contenttypes.ContentType', on_delete=models.PROTECT)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey()

    class Meta:
        indexes = [
            models.Index(fields=['object_id', 'content_type'])
        ]
        unique_together = ('language', 'content_type', 'object_id')
        db_table = 'translation'
        verbose_name = _('Translation')
        verbose_name_plural = _('Translations')

    def __str__(self):
        return self.text


class AbstractTranslatedModel(models.Model):
    """Base model with translated representation. str_field must be the field used in __str__ method."""
    str_field = None
    translations = GenericRelation('utilities.Translation')

    class Meta:
        abstract = True

    def __str__(self):
        if hasattr(self, 'translated_text'):
            return self.translated_text
        else:
            return str(getattr(self, self.str_field))
