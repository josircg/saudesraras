from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class DiseasesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'diseases'
    verbose_name = _('Diseases')