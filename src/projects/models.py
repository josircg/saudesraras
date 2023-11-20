from django.conf import settings
from django.contrib.gis.db import models
from django.core.files.storage import default_storage
from django.urls import reverse_lazy
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django_countries.fields import CountryField
from eucs_platform import visao
from eucs_platform.logger import log_message
from organisations.models import Organisation
from utilities.models import AbstractTranslatedModel

from .managers import ProjectPermissionQuerySet, ProjectQuerySet, TopicQuerySet, StatusQuerySet, \
    ParticipationTaskQuerySet


class Status(AbstractTranslatedModel):
    status = models.TextField(_('Project Status'))

    str_field = 'status'

    objects = StatusQuerySet.as_manager()

    class Meta:
        verbose_name = _('Project Status')
        verbose_name_plural = _('Project Status')
        ordering = ('status',)


class Topic(AbstractTranslatedModel):
    topic = models.TextField(_('Topic'))
    external_url = models.CharField(max_length=100, null=True, blank=True)

    str_field = 'topic'

    objects = TopicQuerySet.as_manager()

    class Meta:
        verbose_name = _('Topic')
        ordering = ['topic']


class ParticipationTask(AbstractTranslatedModel):
    participationTask = models.TextField()

    str_field = 'participationTask'

    objects = ParticipationTaskQuerySet.as_manager()

    class Meta:
        verbose_name = _('Participation Task')
        verbose_name_plural = _('Participation Task')
        ordering = ['participationTask']


class Keyword(models.Model):
    keyword = models.TextField()

    class Meta:
        verbose_name = _('Keyword')
        verbose_name_plural = _('Keywords')
        ordering = ['keyword']

    def __str__(self):
        return f'{self.keyword}'


class FundingBody(models.Model):
    body = models.TextField()

    def __str__(self):
        return f'{self.body}'

    class Meta:
        verbose_name = _('Funding Body')
        verbose_name_plural = _('Funding Body')
        ordering = ['body']


class OriginDatabase(models.Model):
    originDatabase = models.TextField()

    def __str__(self):
        return f'{self.originDatabase}'


class CustomField(models.Model):
    title = models.TextField()
    paragraph = models.TextField()


# For translation

class TranslatedProject(models.Model):
    translatedDescription = models.CharField(max_length=10000)
    translatedHowToParticipate = models.CharField(max_length=10000)
    translatedEquipment = models.CharField(max_length=10000)
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE)
    inLanguage = models.TextField(max_length=5)
    dateCreated = models.DateTimeField('Created date', auto_now=True)
    needsUpdate = models.BooleanField(default=False)

    class Meta:
        verbose_name = _('Translated Project')
        ordering = ['translatedDescription']


class Project(models.Model):
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE)
    dateCreated = models.DateTimeField('Created date', auto_now_add=True)
    dateUpdated = models.DateTimeField('Updated date', auto_now=True)

    # Main information
    name = models.CharField(max_length=200)
    url = models.URLField(null=True)
    description = models.CharField(max_length=3000)
    description_citizen_science_aspects = models.CharField(max_length=2000)
    status = models.ForeignKey(Status, on_delete=models.CASCADE)
    keywords = models.ManyToManyField(Keyword, blank=True)

    # Useful information to classificate the project
    topic = models.ManyToManyField(Topic, verbose_name=_('Topic'), blank=True)
    start_date = models.DateTimeField('Start date', null=True, blank=True)
    end_date = models.DateTimeField('End date', null=True, blank=True)

    # Participation information
    participationTask = models.ManyToManyField(ParticipationTask, blank=True)
    howToParticipate = models.CharField(max_length=2000, null=True, blank=True)
    equipment = models.CharField(max_length=2000, null=True, blank=True)

    # Project Location
    projectGeographicLocation = models.MultiPolygonField(blank=True, null=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    # Legacy
    country = CountryField(null=True, blank=True)

    # Contact and host details
    author = models.CharField(max_length=100, null=True, blank=True)
    author_email = models.CharField(max_length=100, null=True, blank=True)
    mainOrganisation = models.ForeignKey(
        Organisation,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='main_organisation')
    organisation = models.ManyToManyField(Organisation, blank=True)

    # Funding information
    fundingBody = models.ManyToManyField(FundingBody, blank=True)
    fundingProgram = models.CharField(max_length=500, null=True, blank=True)

    # Images
    image1 = models.ImageField(upload_to='images/', max_length=300, null=True, blank=True)
    imageCredit1 = models.CharField(max_length=300, null=True, blank=True)
    image2 = models.ImageField(upload_to='images/', max_length=300, null=True, blank=True)
    imageCredit2 = models.CharField(max_length=300, null=True, blank=True)
    image3 = models.ImageField(upload_to='images/', max_length=300, null=True, blank=True)
    imageCredit3 = models.CharField(max_length=300, null=True, blank=True)

    # Database information
    origin = models.CharField(max_length=100, null=True, blank=True)
    originDatabase = models.ForeignKey(OriginDatabase, on_delete=models.CASCADE, null=True, blank=True)
    originURL = models.URLField(null=True, blank=True)
    originUID = models.CharField(max_length=200, null=True, blank=True)

    # For moderation
    approved = models.BooleanField(_('Approved'), null=True)
    hidden = models.BooleanField(blank=True, default=False)

    # Others (some of them not used)
    featured = models.BooleanField(default=False)
    host = models.CharField(max_length=200, null=True, blank=True)
    doingAtHome = models.BooleanField(null=True, default=False)
    participatingInaContest = models.BooleanField(null=True, default=False)
    customField = models.ManyToManyField(CustomField, blank=True)

    # For translation
    translatedProject = models.ManyToManyField(TranslatedProject)

    # For editPermission
    editors = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='project_editors')

    objects = ProjectQuerySet.as_manager()

    class Meta:
        verbose_name = _('Project')

    def __str__(self):
        return f'{self.name}'

    @property
    def safe_image(self):
        if self.image1 and default_storage.exists(self.image1.path):
            return self.image1
        else:
            return 'void_600.png'

    def safe_image_url(self):
        if self.image1 and default_storage.exists(self.image1.path):
            return self.image1.url
        else:
            return '/media/void_600.png'

    def safe_url(self):
        return mark_safe(f'<a href="/editProject/{self.id}" target="_blank">URL</a>')

    safe_url.allow_tags = True
    safe_url.short_description = 'Site URL'

    def save(self, *args, **kwargs):
        if not self.pk and self.creator.is_staff:
            # Can't use self.approved = self.creator.is_staff. Approved accepts None.
            self.approved = True

        super(Project, self).save(*args, **kwargs)
        if self.approved and self.latitude and self.longitude and settings.VISAO_USERNAME:
            try:
                auth_header = visao.authenticate()
                visao.save_project(self, auth_header)
            except Exception as e:
                log_message(self, e)

    def delete(self, *args, **kwargs):
        if settings.VISAO_USERNAME:
            try:
                auth_header = visao.authenticate()
                visao.delete_project(self, auth_header)
            except Exception as e:
                log_message(self, e)

    def cooperators_as_list(self):
        return self.projectpermission_set.cooperators_as_list(None)

    def get_approved_display(self):
        if self.approved is None:
            message = _('Project not moderated')
        elif self.approved:
            message = _('Project approved')
        else:
            message = _('Project not approved')

        return message

    def get_absolute_url(self):
        return reverse_lazy('project', kwargs={'pk': self.pk})


class FollowedProjects(models.Model):
    class Meta:
        unique_together = (('user', 'project'),)

    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.project.id}'


class ProjectPermission(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name=_('Editor'))
    project = models.ForeignKey(Project, on_delete=models.CASCADE, verbose_name=_('Project'))
    accepted = models.BooleanField(default=False, verbose_name=_('Invite accepted'))

    objects = ProjectPermissionQuerySet.as_manager()

    class Meta:
        verbose_name = _('Project Permission')
        verbose_name_plural = _('Project Permissions')

    def __str__(self):
        return f'{self.user} - {self.project}'
