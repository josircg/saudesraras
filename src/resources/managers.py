from django.db.models import QuerySet, Q

from utilities.managers import TranslationBaseQuerySet


class ResourceQuerySet(QuerySet):

    def resources(self):
        return self.filter(~Q(isTrainingResource=True))

    def training_resources(self):
        return self.filter(isTrainingResource=True)

    def approved_resources(self):
        return self.resources().filter(approved=True)

    def approved_training_resources(self):
        return self.training_resources().filter(approved=True)


class ThemeQuerySet(TranslationBaseQuerySet):
    default_field = 'theme'


class CategoryQuerySet(TranslationBaseQuerySet):
    default_field = 'text'


class AudienceQuerySet(TranslationBaseQuerySet):
    default_field = 'text'
