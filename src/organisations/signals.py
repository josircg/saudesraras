import copy

from django.conf import settings
from django.template.loader import render_to_string
from django.urls import reverse_lazy as rl
from django.utils.translation import ugettext as _, get_language
from eucs_platform import send_email


def notify_approved_organisation(sender, instance, **kwargs):
    if instance.pk:
        old_instance = sender.objects.get(pk=instance.pk)
        if instance.approved and old_instance.approved != instance.approved:
            to = copy.copy(settings.EMAIL_RECIPIENT_LIST)
            to.append(instance.creator.email)
            # TODO: Send e-mail based on creator's profile language
            language = get_language()
            send_email(
                subject=_('Your organisation "%s" has been approved!') % instance.name,
                message=render_to_string(
                    'emails/%s/approved_organisation.html' % language,
                    {"domain": settings.DOMAIN, "name": instance.name,
                     'organisation_url': rl('organisation', kwargs={'pk': instance.pk}),
                     'my_profile_url': rl('profiles:show_self')}
                ),
                to=to
            )
