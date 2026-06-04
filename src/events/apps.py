from django.apps import AppConfig
from django.db.models.signals import pre_save, post_save, post_delete
from django.utils.translation import ugettext_lazy as _

from .signals import notify_approved_event, add_search_index, delete_search_index


class EventsConfig(AppConfig):
    name = 'events'
    verbose_name = _('Events')

    def ready(self):
        super().ready()
        pre_save.connect(notify_approved_event, 'events.Event', dispatch_uid='notify_approved_event')
        post_save.connect(add_search_index, 'events.Event', dispatch_uid='event_add_searchindex')
        post_delete.connect(delete_search_index, 'events.Event', dispatch_uid='event_delete_searchindex')
