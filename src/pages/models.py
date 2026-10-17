import re

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from .managers import SectionQuerySet, ArticleQuerySet

img_finder = re.compile(r'<img[^>]*?src="([^"]+)"[^>]*?>')

class Page(models.Model):
    slug = models.SlugField()
    title = models.CharField(verbose_name=_('Title'), max_length=200)
    header = models.TextField(verbose_name=_('Header'), null=True, blank=True)
    content = models.TextField(verbose_name=_('Content'), null=True, blank=True)
    language = models.CharField(verbose_name=_('Language'), max_length=5, choices=settings.TRANSLATED_LANGUAGES)
    explain = models.TextField(verbose_name=_('Documentation'), null=True, blank=True)
    image = models.ImageField(verbose_name=_('Image'), null=True, blank=True)

    class Meta:
        verbose_name = _('Page')
        verbose_name_plural = _('Pages')
        constraints = [
            models.UniqueConstraint(fields=['slug', 'language'], name='unique_page_slug_language'),
        ]

    def __str__(self):
        return self.title

    def first_image(self):
        images = self.get_images()
        if len(images) > 0:
            return images[0]
        else:
            return self.image.url

    def get_images(self):
        images = []
        if self.image:
            images.append(self.image.url)
        if self.header:
            for img_rex in img_finder.findall(self.header):
                images.append(img_rex)
        if self.content:
            for img_rex in img_finder.findall(self.content):
                images.append(img_rex)
        return images

class Section(models.Model):
    page = models.ForeignKey(Page, verbose_name=_('Page'), on_delete=models.PROTECT, related_name='sections', null=True,
                             blank=True)
    order = models.PositiveIntegerField(verbose_name=_('Order'))
    title = models.CharField(verbose_name=_('Title'), max_length=200)
    header = models.TextField(verbose_name=_('Header'), null=True, blank=True)
    content = models.TextField(verbose_name=_('Content'), null=True, blank=True)
    language = models.CharField(verbose_name=_('Language'), max_length=5, choices=settings.TRANSLATED_LANGUAGES)
    visible = models.BooleanField(verbose_name=_('Visible'), default=True)

    objects = SectionQuerySet.as_manager()

    class Meta:
        verbose_name = _('Section')
        verbose_name_plural = _('Sections')

    def __str__(self):
        return self.title

    def get_images(self):
        images = []
        if self.header:
            for img_rex in img_finder.findall(self.header):
                images.append(img_rex)
        if self.content:
            for img_rex in img_finder.findall(self.content):
                images.append(img_rex)
        for article in self.articles.all():
            for img_rex in img_finder.findall(article.content):
                images.append(img_rex)
        return images

    def first_image(self):
        images = self.get_images()
        if len(images) > 0:
            return images[0]
        else:
            if self.page.image:
                return self.page.image.url
            else:
                return None

    def save(self, *args, **kwargs):
        if self.page_id:
            self.language = self.page.language

        super().save(*args, **kwargs)


class Article(models.Model):
    section = models.ForeignKey(Section, verbose_name=_('Section'), on_delete=models.PROTECT, related_name='articles',
                                null=True, blank=True)
    order = models.PositiveIntegerField(verbose_name=_('Order'))
    title = models.CharField(verbose_name=_('Title'), max_length=200)
    header = models.TextField(verbose_name=_('Header'), null=True, blank=True)
    content = models.TextField(verbose_name=_('Content'))
    language = models.CharField(verbose_name=_('Language'), max_length=5, choices=settings.TRANSLATED_LANGUAGES)

    objects = ArticleQuerySet.as_manager()

    class Meta:
        verbose_name = _('Article')
        verbose_name_plural = _('Articles')

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.section_id:
            self.language = self.section.language

        super().save(*args, **kwargs)
