from utilities.managers import TranslationBaseQuerySet


class OrganisationTypeQuerySet(TranslationBaseQuerySet):
    default_field = 'type'
