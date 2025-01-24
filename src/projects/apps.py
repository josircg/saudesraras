from django.apps import AppConfig
from django.db.models.signals import pre_save, post_save, post_delete, m2m_changed
from django.utils.translation import ugettext_lazy as _

from .signals import notify_approved_project, add_search_index, delete_search_index, notify_new_translation


class ProjectsConfig(AppConfig):
    name = 'projects'
    verbose_name = _('Projects')

    def ready(self):
        super().ready()
        project_cls = self.get_model('Project')
        pre_save.connect(notify_approved_project, 'projects.Project', dispatch_uid='notify_approved_project')
        post_save.connect(add_search_index, 'projects.Project', dispatch_uid='project_add_searchindex')
        post_delete.connect(delete_search_index, 'projects.Project', dispatch_uid='project_delete_searchindex')
        m2m_changed.connect(notify_new_translation, sender=project_cls.translatedProject.through,
                            dispatch_uid='project_notify_new_translation')
