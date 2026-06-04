import logging

from django.apps import apps as django_apps

logger = logging.getLogger("project")


def create_profile_handler(sender, instance, created, **kwargs):
    if not created:
        return
    # Create the profile object, only if it is newly created
    profile_cls = django_apps.get_model("profiles", "Profile")
    profile = profile_cls(user=instance)
    profile.save()
    logger.info("New user profile for {} created".format(instance))


def add_search_index(sender, instance, created, **kwargs):
    from utilities.models import add_searchindex_text, SearchIndexType

    if instance.profileVisible and instance.user.is_active:
        text = f'{instance.user.name} {instance.bio} {instance.title}'

        for interest_area in instance.interestAreas.values_list('interestArea', flat=True):
            text += f' {interest_area}'

        add_searchindex_text(SearchIndexType.PROFILE.value, instance.slug, instance.user.name, text)
    else:
        delete_search_index(None, instance)


def delete_search_index(sender, instance, **kwargs):
    from utilities.models import delete_searchindex, SearchIndexType
    delete_searchindex(SearchIndexType.PROFILE.value, instance.slug)
