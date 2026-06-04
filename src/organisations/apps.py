from django.apps import AppConfig
from django.db.models.signals import pre_save, post_save, post_delete
from django.utils.translation import ugettext_lazy as _

from .signals import notify_approved_organisation, add_search_index, delete_search_index


class OrganisationsConfig(AppConfig):
    name = 'organisations'
    verbose_name = _('Organisations')

    def ready(self):
        super().ready()
        pre_save.connect(notify_approved_organisation, 'organisations.Organisation',
                         dispatch_uid='notify_approved_organisation')
        post_save.connect(add_search_index, 'organisations.Organisation', dispatch_uid='organisation_add_searchindex')
        post_delete.connect(delete_search_index, 'organisations.Organisation',
                            dispatch_uid='organisation_delete_searchindex')
