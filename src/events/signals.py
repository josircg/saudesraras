import copy

from django.conf import settings
from django.template.loader import render_to_string
from django.urls import reverse_lazy as rl
from django.utils.translation import ugettext as _
from eucs_platform import send_email


def notify_approved_event(sender, instance, **kwargs):
    if instance.pk:
        old_instance = sender.objects.get(pk=instance.pk)
        if instance.approved and old_instance.approved != instance.approved:
            to = copy.copy(settings.EMAIL_RECIPIENT_LIST)
            to.append(instance.creator.email)
            send_email(
                subject=_('Your event "%s" has been approved!') % instance.title,
                message=render_to_string(
                    'emails/approved_event.html',
                    {"domain": settings.DOMAIN, "title": instance.title,
                     'event_url': rl('events')}
                ),
                to=to
            )
