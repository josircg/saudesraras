from utilities.managers import TranslationBaseQuerySet


class GeographicExtendQuerySet(TranslationBaseQuerySet):
    default_field = 'description'
