from django import template
from django.utils.translation import get_language

from utilities.models import Translation

register = template.Library()


@register.filter
def translate_instance(instance):
    """
    Translate support tables text.
    :param instance: instance of models.Model or models.ForeignKey. Must have a GenericRelation called translations.
    """
    if isinstance(instance, str):
        return instance

    if not hasattr(instance, 'translations'):
        raise NotImplementedError(f'GenericRelation "translations" not defined in {instance.__class__}')

    try:
        language = get_language()
        translated_instance = instance.translations.get(language=language)
        result = str(translated_instance)
    except Translation.DoesNotExist:
        result = str(instance)

    return result
