from itertools import chain

from django.db.models import QuerySet
from utilities.managers import TranslationBaseQuerySet


class ProjectPermissionQuerySet(QuerySet):

    def all_cooperators(self, project_id):
        return self.filter(project__pk=project_id)

    def cooperators(self, project_id=None):
        kwargs = {'accepted': True}

        if project_id is not None:
            kwargs['project__pk'] = project_id

        return self.filter(**kwargs)

    def cooperators_as_list(self, project_id):
        return self.cooperators(project_id).values_list('user', flat=True)

    def cooperators_emails(self, project_id):
        qs = self.cooperators(project_id).values_list('user__email', flat=True)
        return ', '.join(qs)

    def invite_accepted(self, project_id, user):
        return self.filter(project__pk=project_id, user=user, accepted=True).exists()

    def project_permissions_by_user(self, user):
        return self.filter(user=user).select_related('project')


class ProjectQuerySet(QuerySet):

    def countries_with_content(self, **kwargs):
        """
        Returns a set of countries from projects.
        It should be a model function, but we also need as a manager function to return a set from all projects.
        """
        main_organization_country = self.filter(**kwargs).values_list('mainOrganisation__country', flat=True).distinct()
        organization_country = self.filter(**kwargs).values_list('organisation__country', flat=True).distinct()
        project_country = self.filter(**kwargs).values_list('country', flat=True).distinct()

        return set(chain(main_organization_country, organization_country, project_country))


class TopicQuerySet(TranslationBaseQuerySet):
    default_field = 'topic'

    def topics_with_external_url(self):
        return self.filter(external_url__isnull=False).order_by('topic')


class StatusQuerySet(TranslationBaseQuerySet):
    default_field = 'status'


class ParticipationTaskQuerySet(TranslationBaseQuerySet):
    default_field = 'participationTask'
