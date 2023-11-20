from authors.models import Author
from django.conf import settings
from django.core.files.storage import default_storage
from django.db import models
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from organisations.models import Organisation
from projects.models import Project
from utilities.models import AbstractTranslatedModel

from .managers import ResourceQuerySet, ThemeQuerySet, CategoryQuerySet, AudienceQuerySet


class Keyword(models.Model):
    keyword = models.TextField()

    def __str__(self):
        return f'{self.keyword}'

    class Meta:
        verbose_name = _('Resource Keyword')
        verbose_name_plural = _('Resource Keywords')
        ordering = ['keyword']


class Theme(AbstractTranslatedModel):
    theme = models.TextField()

    str_field = 'theme'

    objects = ThemeQuerySet.as_manager()

    class Meta:
        verbose_name = _('Theme')
        ordering = ['theme']


class Audience(AbstractTranslatedModel):
    audience = models.TextField()

    str_field = 'audience'

    objects = AudienceQuerySet.as_manager()

    class Meta:
        verbose_name = _('Audience')
        verbose_name_plural = _('Audiences')
        ordering = ['audience']


class Category(AbstractTranslatedModel):
    text = models.TextField()
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE)

    str_field = 'text'

    objects = CategoryQuerySet.as_manager()

    class Meta:
        verbose_name = _('Resource category')
        verbose_name_plural = _('Resource categories')


class Resource(models.Model):
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE)

    # Main information, mandatory
    name = models.CharField(max_length=200)
    url = models.URLField(max_length=200)
    keywords = models.ManyToManyField(Keyword)
    abstract = models.CharField(max_length=3000)
    description_citizen_science_aspects = models.CharField(max_length=2000)
    category = models.ForeignKey(Category, null=True, on_delete=models.CASCADE)
    theme = models.ManyToManyField(Theme)

    # Publish information
    # TODO: Convert datePublished to Year
    authors = models.ManyToManyField(Author, blank=True)
    publisher = models.CharField(max_length=100, blank=True, null=True)
    datePublished = models.IntegerField(_('Year published'), null=True, blank=True)
    resourceDOI = models.CharField(max_length=100, null=True, blank=True)
    inLanguage = models.CharField(max_length=100, null=True, blank=True)
    license = models.CharField(max_length=300, null=True, blank=True)

    # Links
    organisation = models.ManyToManyField(Organisation, blank=True)
    project = models.ManyToManyField(Project, blank=True)

    # Pictures
    image1 = models.ImageField(upload_to='images/', max_length=300, null=True, blank=True)
    imageCredit1 = models.CharField(max_length=300, null=True, blank=True)
    image2 = models.ImageField(upload_to='images/', max_length=300, null=True, blank=True)
    imageCredit2 = models.CharField(max_length=300, null=True, blank=True)

    # Training resources fields
    isTrainingResource = models.BooleanField(_('Is Training Resource'), null=True, blank=True, default=False)

    # Time
    # Legacy TODO: delete dateUploaded
    dateUploaded = models.DateTimeField('Date Uploaded')
    dateCreated = models.DateTimeField('Created date', auto_now_add=True)
    dateUpdated = models.DateTimeField('Updated date', auto_now=True)

    # Moderation
    approved = models.BooleanField(_('Approved'), null=True)

    # Other
    hidden = models.BooleanField(null=True, blank=True)
    featured = models.BooleanField(default=False)
    own = models.BooleanField(null=True, blank=True)

    objects = ResourceQuerySet.as_manager()

    class Meta:
        verbose_name = _('Resource')

    def __str__(self):
        return self.name

    @property
    def safe_image(self):
        if self.image1 and default_storage.exists(self.image1.path):
            return self.image1
        else:
            return 'void_600.png'

    def full_url(self):
        return f'{settings.DOMAIN}/resource/{self.id}'

    def safe_url(self):
        if self.isTrainingResource:
            return mark_safe(f'<a href="/editTrainingResource/{self.id}" target="_blank">URL</a>')
        else:
            return mark_safe(f'<a href="/editResource/{self.id}" target="_blank">URL</a>')

    safe_url.allow_tags = True
    safe_url.short_description = 'Site URL'

    def save(self, *args, **kwargs):
        # approved can be null (not moderated), so we can't put self.approved = ... in one line
        if not self.pk and self.creator.is_staff:
            self.approved = True

        super().save(*args, **kwargs)


class TrainingResource(Resource):
    class Meta:
        proxy = True
        verbose_name = _('Training Resource')
        verbose_name_plural = _('Training Resources')

    def save(self, *args, **kwargs):
        if not self.pk:
            self.isTrainingResource = True

        super().save(*args, **kwargs)


class ResourceGroup(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=200)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Resource Group')
        verbose_name_plural = _('Resource Groups')
        ordering = ['name']


class ResourcesGrouped(models.Model):
    group = models.ForeignKey(ResourceGroup, on_delete=models.CASCADE)
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE)

    class Meta:
        verbose_name = _('Resources Grouped')
        unique_together = (("group", "resource"),)

    def __str__(self):
        return str(self.group) + ' - ' + str(self.resource)


# TODO: Important! copy SavedResources table to Bookmarked resources
class BookmarkedResources(models.Model):
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        unique_together = (('user', 'resource'),)

    def __str__(self):
        return f'{self.resource} - {self.user.name}'


class SavedResources(models.Model):
    class Meta:
        unique_together = (('user', 'resource'),)

    resource = models.ForeignKey(Resource, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.resource} - {self.user.name}'


class ResourcePermission(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE)
