import hashlib
import os
import uuid

from blog.models import Post
from django.conf import settings
from django.db import models
from django.template import Template, Context
from django.template.loader import render_to_string
from django.utils.formats import date_format
from django.utils.translation import ugettext_lazy as _
from eucs_platform import send_email
from events.models import Event
from machina.conf import settings as machina_settings
from machina.models.fields import ExtendedImageField
from projects.models import Project
from resources.models import Resource

from .managers import SubscriberQuerySet


class Subscriber(models.Model):
    name = models.CharField(_('Name'), max_length=100)
    email = models.EmailField(_('Email'), unique=True)
    organisation = models.CharField(_('Organisation'), max_length=200, blank=True, null=True)
    valid = models.BooleanField(_('Valid Email'), default=False)
    opt_out = models.BooleanField(default=False)
    last_newsletter = models.ForeignKey('Newsletter', null=True, blank=True, on_delete=models.SET_NULL)
    dateCreated = models.DateField(_('Date Created'), auto_now_add=True)

    objects = SubscriberQuerySet.as_manager()

    class Meta:
        verbose_name = _('Subscriber')
        verbose_name_plural = _('Subscribers')
        ordering = ('-id',)

    def __str__(self):
        return self.name

    def secret(self):
        # hash to be used to verify email authenticity - does not expire
        return hashlib.md5((settings.SECRET_KEY + str(self.id)).encode()).hexdigest()


class Newsletter(models.Model):
    DRAFT = 'D'
    READY = 'R'
    QUEUED = 'Q'
    SENT = 'S'
    ERROR = 'E'
    STATUS = (
        (DRAFT, _('Draft')),
        (READY, _('Ready')),
        (QUEUED, _('Queued')),
        (SENT, _('Sent')),
        (ERROR, _('Error'))
    )
    title = models.CharField(_('Title'), max_length=200)
    headline = models.TextField(_('Headline'))
    featured_title = models.CharField(_('Featured Title'), max_length=200, blank=True, null=True)
    featured_text = models.TextField(_('Featured Text'), blank=True, null=True)
    blog = models.ForeignKey(Post, blank=True, null=True, on_delete=models.SET_NULL)
    featured_resource = models.ForeignKey(Resource, blank=True, null=True,
                                          on_delete=models.SET_NULL, verbose_name=_('Feature Resource'))
    html = models.TextField(_('Source HTML'), blank=True, null=True)
    status = models.CharField(_('Status'), max_length=1, choices=STATUS, default=DRAFT)
    dateCreated = models.DateField(_('Date Created'), auto_now_add=True)
    sent_count = models.BigIntegerField(_('Sent Count'), default=0)
    read_count = models.BigIntegerField(_('Read Count'), default=0)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return f'{settings.DOMAIN}/newsletter/{self.id}'

    def image(self):
        if self.blog:
            return self.blog.image
        else:
            return None

    def render(self):
        acontece = []
        for event in Event.objects.ongoing_events():
            acontece.append(
                {'period': date_format(event.start_date, 'd/M') + ' a ' + date_format(event.end_date, 'd/M'),
                 'title': event.title,
                 'url': event.url
                 }
            )
        for event in Event.objects.upcoming_events():
            acontece.append(
                {'period': date_format(event.start_date, 'd/M') + ' a ' + date_format(event.end_date, 'd/M'),
                 'title': event.title,
                 'url': event.url
                 }
            )

        projects = []
        for project in Project.objects.filter(approved=True).order_by('-dateUpdated')[:3]:
            projects.append(
                {'title': project.name,
                 'id': project.id,
                 'description': project.description.replace('<p>', '<p class="m-0">'),
                 'image': project.safe_image})

        context = {'news': self, 'domain': settings.DOMAIN,
                   'acontece': acontece,
                   'projects': projects,
                   'invisible': '{{invisible | safe}}',
                   'unsubscribe': '{{unsubscribe}}',
                   'tracking_url': '{{tracking_url}}'}
        self.html = render_to_string("contact/newsletter.html", context)
        self.save()

    def send(self, subscriber):
        unsubscribe_url = '%s/unsubscribe/%s/%d' % (settings.DOMAIN, subscriber.secret(), subscriber.id)
        tracking_url = f'{settings.DOMAIN}/load_image/pixel-{self.pk}-{subscriber.pk}.png'

        headers = {
            'List-Unsubscribe': '<%s>' % unsubscribe_url,
            'Campaign-Id': '%s' % self.pk,
        }
        context = Context({'unsubscribe': unsubscribe_url, 'id': self.id, 'tracking_url': tracking_url})
        t = Template(self.html)
        message = t.render(context)
        send_email(
            subject=self.headline,
            message=message, to=[subscriber.email], reply_to=settings.EMAIL_CIVIS,
            headers=headers,
        )


def forum_proposal_upload_to(instance, filename):
    dummy, ext = os.path.splitext(filename)
    file_id = str(uuid.uuid4()).replace('-', '')
    return os.path.join('images', f'{file_id}{ext}')


class ForumProposal(models.Model):
    name = models.CharField(max_length=100, verbose_name=_('Name'))
    description = models.TextField(verbose_name=_('Description'), null=True, blank=True)
    image = ExtendedImageField(
        null=True, blank=True, upload_to=forum_proposal_upload_to,
        verbose_name=_('Forum image'), **machina_settings.DEFAULT_FORUM_IMAGE_SETTINGS
    )
    approved = models.BooleanField(verbose_name=_('Approved'), null=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                related_name='forumproposal_creator')

    class Meta:
        verbose_name = _('Forum Proposal')
        verbose_name_plural = _('Forum Proposals')

    def __str__(self):
        return self.name
