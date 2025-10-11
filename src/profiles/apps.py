from django.apps import AppConfig
from django.conf import settings
from django.db.models.signals import post_save, post_delete

from .signals import add_search_index, delete_search_index, create_profile_handler


class ProfileConfig(AppConfig):
    name = "profiles"
    verbose_name = "User Profiles"

    def ready(self):
        post_save.connect(create_profile_handler, sender=settings.AUTH_USER_MODEL)
        post_save.connect(add_search_index, 'profiles.Profile', dispatch_uid='profile_add_searchindex')
        post_delete.connect(delete_search_index, 'profiles.Profile', dispatch_uid='profile_delete_searchindex')
