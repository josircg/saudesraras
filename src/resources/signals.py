import copy

from django.conf import settings
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _
from eucs_platform import send_email


def notify_approved_resource(sender, instance, **kwargs):
    if instance.pk:
        old_instance = sender.objects.get(pk=instance.pk)
        if instance.approved and old_instance.approved != instance.approved:
            if instance.isTrainingResource:
                resource_url = 'training_resource'
            else:
                resource_url = 'resource'

            to = copy.copy(settings.EMAIL_RECIPIENT_LIST)
            to.append(instance.creator.email)

            send_email(
                subject=_('Your resource "%s" has been approved!') % instance.name,
                message=render_to_string(
                    'emails/approved_resource.html',
                    {"domain": settings.DOMAIN, "name": instance.name, "id": instance.pk, 'resource_url': resource_url}
                ),
                to=to
            )
