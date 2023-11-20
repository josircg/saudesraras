from django.apps import AppConfig
from django.db.models.signals import pre_save
from django.utils.translation import ugettext_lazy as _

from .signals import notify_approved_resource


class ResourcesConfig(AppConfig):
    name = 'resources'
    verbose_name = _('Resources')

    def ready(self):
        super().ready()
        pre_save.connect(notify_approved_resource, 'resources.Resource', dispatch_uid='notify_approved_resource')
        pre_save.connect(notify_approved_resource, 'resources.TrainingResource',
                         dispatch_uid='notify_approved_training_resource')
