from django.apps import AppConfig
from django.db.models.signals import post_save, post_delete
from django.utils.translation import ugettext_lazy as _

from .signals import add_search_index, delete_search_index


class PlatformsConfig(AppConfig):
    name = 'platforms'
    verbose_name = _('Platforms')

    def ready(self):
        super().ready()
        post_save.connect(add_search_index, 'platforms.Platform', dispatch_uid='platform_add_searchindex')
        post_delete.connect(delete_search_index, 'platforms.Platform', dispatch_uid='platform_delete_searchindex')
