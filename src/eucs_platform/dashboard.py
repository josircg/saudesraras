"""
This file was generated with the customdashboard management command, it
contains the two classes for the main dashboard and app index dashboard.
You can customize these classes as you want.

To activate your index dashboard add the following to your settings.py::
    ADMIN_TOOLS_INDEX_DASHBOARD = 'eucs_platform.CustomIndexDashboard'

And to activate the app index dashboard::
    ADMIN_TOOLS_APP_INDEX_DASHBOARD = 'eucs_platform.CustomAppIndexDashboard'
"""

from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from admin_tools.dashboard import modules, Dashboard, AppIndexDashboard
from admin_tools.utils import get_admin_site_name


class CustomIndexDashboard(Dashboard):
    """
    Custom index dashboard for src.
    """

    def init_with_context(self, context):
        site_name = get_admin_site_name(context)

        self.children += [
            modules.ModelList(
                _('Projects'),
                models=('projects.models.Project',
                        'projects.models.FundingBody',
                        'projects.models.Keyword',
                        'projects.models.Status',
                        'projects.models.Topic',
                        'projects.models.ParticipationTask')
            ),
        ]

        self.children += [
            modules.ModelList(
                _('Platforms'),
                models=('platforms.models.Platform',
                        'platforms.models.GeographicExtend',
                        'platforms.models.Keyword')
            ),
        ]

        self.children += [
            modules.ModelList(_('Resources'),
                              models=('resources.models.Resource',
                                      'resources.models.TrainingResource',
                                      'resources.models.ResourceGroup',
                                      'resources.models.Keyword',
                                      'resources.models.Audience',
                                      'resources.models.Category',
                                      'resources.models.Theme',
                                      )),
        ]

        self.children += [
            modules.ModelList(_('Events'), models=('events.models.*',)),
        ]

        self.children += [
            modules.ModelList(_('Organisations'), models=('organisations.models.*',)),
        ]

        self.children.append(modules.AppList(
            _('Communications'),
            models=('contact.*', 'blog.*', 'digest.*',)
        ))

        self.children += [
            modules.ModelList(
                _('Authentication'),
                models=('authtools.models.User',
                        'django.contrib.auth.models.Group',
                        'django.contrib.admin.models.LogEntry',
                        'profiles.models.InterestArea',
                        )),
        ]

        self.children.append(modules.ModelList(
            _('Forum'),
            models=('machina.*', 'machina_apps.*')
        ))

        self.children.append(modules.ModelList(
            title=_('Administration'),
            models=('django_cron.*', 'django_summernote.*', 'oauth2_provider.*', 'oidc_provider.*'),
            extra=[
                    {'title': _('Countries'), 'change_url': reverse('country_list')},
            ]
        ))
        # append a link list module for "quick links"
        self.children.append(modules.LinkList(
            _('Quick links'),
            layout='inline',
            draggable=False,
            deletable=False,
            collapsible=False,
            children=[
                [_('Return to site'), '/'],
                [_('Change password'),
                 reverse('%s:password_change' % site_name)],
                [_('Log out'), reverse('%s:logout' % site_name)],
            ]
        ))


class CustomAppIndexDashboard(AppIndexDashboard):
    """
    Custom app index dashboard for src.
    """

    # we disable title because its redundant with the model list module
    title = ''

    def __init__(self, *args, **kwargs):
        AppIndexDashboard.__init__(self, *args, **kwargs)

        # append a model list module and a recent actions module
        self.children += [
            modules.ModelList(self.app_title, self.models),
            modules.RecentActions(
                _('Recent Actions'),
                include_list=self.get_app_content_types(),
                limit=5
            )
        ]

    def init_with_context(self, context):
        """
        Use this method if you need to access the request context.
        """
        return super(CustomAppIndexDashboard, self).init_with_context(context)
