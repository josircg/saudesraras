import copy

from django.conf import settings
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _
from eucs_platform import send_email


def notify_approved_project(sender, instance, **kwargs):
    if instance.pk:
        old_instance = sender.objects.get(pk=instance.pk)
        if instance.approved and old_instance.approved != instance.approved:
            to = copy.copy(settings.EMAIL_RECIPIENT_LIST)
            to.append(instance.creator.email)
            send_email(
                subject=_('Your project "%s" has been approved!') % instance.name,
                message=render_to_string(
                    'emails/approved_project.html',
                    {"domain": settings.DOMAIN, "name": instance.name, "id": instance.pk}
                ),
                to=to
            )


def notify_removed_from_project(sender, instance, using, **kwargs):
    project_id = instance.project_id
    email = instance.user.email
    project_name = instance.project.name

    send_email(
        _('You were removed from project %s') % project_name,
        render_to_string('emails/removed_from_project.html',
                         {'domain': settings.DOMAIN, 'project_id': project_id, 'project': project_name}),
        [email]
    )
