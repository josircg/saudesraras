from django.conf import settings
from django.core.files.storage import default_storage
from django.template import Library
from django.template.defaultfilters import stringfilter, truncatewords
from django.utils.html import strip_tags

register = Library()


@register.filter(is_safe=True)
@stringfilter
def truncate_summary(value, arg):
    """Remove all tags/whitespaces and return a truncated text"""
    if isinstance(value, str):
        value = strip_tags(value).replace('&nbsp;', '')
        value = ' '.join([s for s in value.splitlines() if s])

    return truncatewords(value, arg)


@register.filter
def safe_image(img_field, default=None):
    if default is None:
        default = 'void_600.png'

    if img_field and hasattr(img_field, 'url'):
        if default_storage.exists(img_field.path):
            return img_field

    return default


@register.filter
def safe_image_url(img_field, default=None):
    if default is None:
        default = f'{settings.MEDIA_URL}/void_600.png'

    if img_field and hasattr(img_field, 'url'):
        if default_storage.exists(img_field.path):
            return img_field.url

    return default
