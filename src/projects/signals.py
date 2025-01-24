import copy

from django.conf import settings
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils import translation
from django.utils.translation import ugettext as _
from eucs_platform import send_email


def notify_approved_project(sender, instance, **kwargs):
    """Notify approved and not approved projects"""
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


def add_search_index(sender, instance, created, **kwargs):
    from utilities.models import add_searchindex_text, SearchIndexType

    if instance.approved and not instance.hidden:
        text = f'{instance.name} {instance.description}'

        for translated_project in instance.translatedProject.values_list('translatedDescription', flat=True):
            text += f' {translated_project}'

        for keyword in instance.keywords.values_list('keyword', flat=True):
            text += f' {keyword}'

        for topic in instance.topic.prefetch_related('translations').all():
            text += f' {topic}'
            for t in topic.translations.values_list('text', flat=True):
                text += f' {t}'

        add_searchindex_text(SearchIndexType.PROJECT.value, instance.pk, instance.name, text)
    else:
        delete_search_index(None, instance)


def delete_search_index(sender, instance, **kwargs):
    from utilities.models import delete_searchindex, SearchIndexType
    delete_searchindex(SearchIndexType.PROJECT.value, instance.pk)


def notify_new_translation(sender, instance, action, reverse, model, pk_set, using, **kwargs):
    if action == 'post_add':
        try:
            for translation_id in pk_set:
                t = instance.translatedProject.get(pk=translation_id)

                with translation.override(settings.LANGUAGE_CODE):
                    subject = _('Notification - New translation for project "%s" submitted') % instance
                    inlanguage = t.get_inLanguage_display()

                template = 'emails/%s/notify_translation.html' % settings.LANGUAGE_CODE
                project_url = reverse_lazy('project', kwargs={'pk': instance.pk})
                message = render_to_string(template, {
                    'project_name': instance.name, 'project_url': f'{settings.DOMAIN}{project_url}',
                    'language': inlanguage
                })
                send_email(subject=subject, message=message, to=settings.EMAIL_CIVIS)
        except Exception as e:
            from eucs_platform.logger import log_message
            log_message(instance, f'Notify new translation error: {e}')
