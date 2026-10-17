from django.apps import apps as django_apps
from django.contrib.contenttypes.models import ContentType
from django.db.models import QuerySet, Subquery, OuterRef, F, CharField
from django.db.models.functions import Coalesce
from django.utils.translation import get_language


class TranslationBaseQuerySet(QuerySet):
    """
    Handles translation from support tables. default_field is the name of the field used to display in __str__ method.
    """
    default_field = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.default_field is None:
            raise NotImplementedError('default_field not defined')

    def translated(self):
        """Returns a queryset annotated with translated text from Translation class or instance original text"""
        translation_cls = django_apps.get_model('utilities', 'Translation')
        ctype = ContentType.objects.get_for_model(self.model)
        language = get_language()
        translation = translation_cls.objects.filter(content_type=ctype, object_id=OuterRef('pk'), language=language)
        return self.annotate(
            translated_text=Coalesce(
                Subquery(translation.values('text')), F(self.default_field), output_field=CharField()),
        )

    def translated_sorted_by_text(self):
        """Returns a queryset sorted by translated_text"""
        return self.translated().order_by('translated_text')
