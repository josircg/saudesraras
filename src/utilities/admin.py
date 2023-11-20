from django.contrib.contenttypes.admin import GenericTabularInline

from .models import Translation


class TranslationInline(GenericTabularInline):
    model = Translation
    extra = 0
