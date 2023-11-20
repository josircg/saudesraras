from django.apps import AppConfig
from django_cleanup.signals import cleanup_pre_delete

from .signals import easy_thumbnail_delete


class UtilitiesConfig(AppConfig):
    name = 'utilities'

    def ready(self):
        super().ready()
        cleanup_pre_delete.connect(easy_thumbnail_delete)
