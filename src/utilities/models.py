from html import unescape

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.db import models
from django.utils.html import strip_tags
from django.utils.translation import ugettext_lazy as _

from .managers import SearchIndexQuerySet


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


class SearchIndexType(models.TextChoices):
    """Choices for IndexType.type"""
    PROJECT = 'project', _('Projects')
    RESOURCE = 'resource', _('Resources')
    TRAINING = 'training', _('Training Resources')
    ORGANISATION = 'organisation', _('Organisations')
    PLATFORM = 'platform', _('Platforms')
    PROFILE = 'profile', _('Users')
    EVENT = 'event', _('Events')


class IndexType(models.Model):
    """Helper class to handle type sorting"""
    type = models.CharField(choices=SearchIndexType.choices, max_length=20, unique=True)
    order = models.PositiveIntegerField()

    class Meta:
        verbose_name = _('Search Index Type')
        verbose_name_plural = _('Search Index Types')

    def __str__(self):
        return self.get_type_display()


class SearchIndex(models.Model):
    """
    Class used to perform full-text search.
    Does not use content_type as there may be types that do not correspond to classes implemented in Django.
    """
    type = models.ForeignKey(IndexType, max_length=20, on_delete=models.PROTECT)
    object_id = models.CharField(max_length=40)
    object_repr = models.CharField(max_length=255)
    language = models.CharField(max_length=5, choices=settings.TRANSLATED_LANGUAGES, verbose_name=_('Language'),
                                default=settings.LANGUAGE_CODE)
    text = models.TextField()
    # Admin has full access and non admin has access only to items marked as public
    is_public = models.BooleanField(default=True)

    objects = SearchIndexQuerySet.as_manager()

    class Meta:
        unique_together = ('type', 'object_id', 'language')
        db_table = 'search'
        verbose_name = _('Search Index')
        verbose_name_plural = _('Search Indexes')

    def __str__(self):
        return f'{self.type} {self.object_id}'


def add_searchindex_text(searchindex_type, object_id, object_repr, text, **extra_fields):
    """Create or update SearchIndex for a given type and object_id"""
    from unidecode import unidecode
    # Text without html tags and special characters
    normalized_text = unidecode(unescape(strip_tags(text).replace('&nbsp;', ' ')))

    defaults = {'object_repr': object_repr, 'text': normalized_text}
    defaults.update(extra_fields)

    type = IndexType.objects.get(type=searchindex_type)

    return SearchIndex.objects.update_or_create(type=type, object_id=object_id, defaults=defaults)


def delete_searchindex(searchindex_type, object_id):
    return SearchIndex.objects.filter(type__type=searchindex_type, object_id=object_id).delete()
