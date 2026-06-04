import re
from itertools import groupby
from urllib.parse import quote

from django.apps import apps as django_apps
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.search import SearchQuery
from django.db import ProgrammingError
from django.db.models import QuerySet, Subquery, OuterRef, F, CharField, IntegerField, UUIDField
from django.db.models.functions import Coalesce, Cast
from django.utils.translation import get_language
from django.utils.translation import ugettext_lazy as _
from unidecode import unidecode


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


class SearchIndexQuerySet(QuerySet):

    def full_text_search(self, text, index_type=None):
        normalized_text = unidecode(text).strip()
        # Execute search only if text not ends with | or & or text is not empty
        if not normalized_text or (normalized_text and normalized_text[-1] in ['|', '&']):
            qs = self.none()
        else:
            if index_type is None:
                kwargs = {}
            else:
                kwargs = {'type__type': index_type}
            # Pattern to retrieve all words between quotes
            pattern = r'"([^"]*)"'

            if '|' not in normalized_text and '&' not in normalized_text:
                # Basic search:
                # Replaces empty espaces by & and & by <-> (followed by) in quoted words and remove quotes
                normalized_text = ' & '.join(s for s in normalized_text.split(' ') if s.strip())

                ends_with_quotes = normalized_text.endswith('"')
                # Retrieve all words between quotes
                match = re.findall(pattern, normalized_text)
                # Replace & by <-> in all matches
                for s in match:
                    normalized_text = normalized_text.replace(f'"{s}"', s.replace('&', '<->'))

                if not ends_with_quotes:
                    normalized_text += ':*'
            else:
                # Advanced search:
                # User will input & or I, so only replaces espaces by <-> in quoted words
                match = re.findall(pattern, normalized_text)

                for s in match:
                    sr = ' <-> '.join(i for i in s.split(' ') if i.strip())
                    normalized_text = normalized_text.replace(f'"{s}"', sr)

            qs = self.filter(text__search=SearchQuery(normalized_text, config='english', search_type='raw'), **kwargs)

        return qs

    def full_text_search_as_json(self, text, index_type=None, only_public=True):
        """
        Returns a data structure with SearchIndex items and a total by type.
        [
            {"type": "projectKeyWord", "text": "Projects", "numberElements": 2, "keyword": "search term"},
            {"type": "project", "id": "1", "text": "Project1"},
            {"type": "project", "id": "2", "text": "Project2"},
            {"type": "resourceKeyWord", "text": "Resources", "numberElements": 3, "keyword": "search term"}
            {"type": "resource", "id": "1", "text": "Resource1"},
            {"type": "resource", "id": "2", "text": "Resource2"},
            {"type": "resource", "id": "3", "text": "Resource3"},
        ]
        """
        from .models import SearchIndexType

        if only_public:
            kwargs = {'is_public': True}
        else:
            kwargs = {}

        qs = (self.filter(**kwargs).full_text_search(text, index_type).values('object_id', 'object_repr', 'type__type').
              order_by('type__order'))
        try:
            groups = groupby(qs, key=lambda k: k['type__type'])

            for group_index, group in groups:
                group_items = list(group)

                yield {
                    "type": f"{group_index}Keyword", "text": SearchIndexType[group_index.upper()].label,
                    "numberElements": len(group_items), "keyword": quote(text)
                }

                for item in group_items:
                    yield {"type": group_index, "id": item['object_id'], "text": item['object_repr']}
        except ProgrammingError:
            yield {'type': 'error', 'id': None, 'text': _('Invalid search term')}

    def full_text_search_ids(self, text, index_type, cast_as='int'):
        """Returns full text search ids for a given index type"""

        # PostgreSQL is strongly typed. We must cast object_id to match Model search_id.
        if cast_as == 'int':
            qs = (
                self.annotate(int_object_id=Cast('object_id', output_field=IntegerField())).
                full_text_search(text, index_type).values_list('int_object_id')
            )
        elif cast_as == 'uuid':
            qs = (
                self.annotate(uuid_object_id=Cast('object_id', output_field=UUIDField())).
                full_text_search(text, index_type).values_list('uuid_object_id')
            )
        else:
            qs = (
                self.annotate(chr_object_id=Cast('object_id', output_field=CharField())).
                full_text_search(text, index_type).values_list('chr_object_id')
            )

        return qs
