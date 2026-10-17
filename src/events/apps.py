from django.apps import AppConfig
from django.db.models.signals import pre_save
from django.utils.translation import ugettext_lazy as _

from .signals import notify_approved_event


class EventsConfig(AppConfig):
    name = 'events'
    verbose_name = _('Events')

    def ready(self):
        super().ready()
        pre_save.connect(notify_approved_event, 'events.Event', dispatch_uid='notify_approved_event')
