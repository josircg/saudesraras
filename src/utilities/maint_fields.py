from urllib.parse import urlsplit, urlunsplit

from django.core.validators import EMPTY_VALUES
from events.models import Event
from organisations.models import Organisation
from platforms.models import Platform
from projects.models import Project
from resources.models import Resource

"""
  Usage:
  >>> python manage.py shell
  >>> from eucs_platform.update_url_fields import update_models
  >>> update_models()
"""


def split_url(url):
    try:
        return list(urlsplit(url))
    except ValueError:
        raise Exception(f'Url split error on string {url}')


def update_url_value(url):
    url_fields = split_url(url)

    if not url_fields[0]:
        # If no URL scheme given, assume http://
        url_fields[0] = 'http'
    if not url_fields[1]:
        # Assume that if no domain is provided, that the path segment
        # contains the domain.
        url_fields[1] = url_fields[2]
        url_fields[2] = ''
        # Rebuild the url_fields list, since the domain segment may now
        # contain the path too.
        url_fields = split_url(urlunsplit(url_fields))

    return urlunsplit(url_fields)


def update_object_url_fields(model, fields):
    for obj in model.objects.all():
        values = {}

        for field in fields:
            value = getattr(obj, field)

            if value not in EMPTY_VALUES:
                new_value = update_url_value(value)
                values[field] = new_value
                print(f'{obj} - {field}: {value} > {new_value}')
        # Force update without execute object save method
        if values:
            model.objects.filter(pk=obj.pk).update(**values)


def update_models():
    update_object_url_fields(Event, ['url'])
    update_object_url_fields(Organisation, ['url'])
    update_object_url_fields(Platform, ['url'])
    update_object_url_fields(Project, ['url', 'originURL'])
    update_object_url_fields(Resource, ['url'])
    print('Process complete')


# After changing the locale language from pt to pt-br, we have to change the resources too
def update_resources_language():
    from resources.models import Resource
    Resource.objects.filter(inLanguage='pt').update(inLanguage='pt-br')


def save_user_csv():
    from django.contrib.auth import get_user_model
    User = get_user_model()

    with open('users.csv', 'w', encoding='utf-8') as user_csv:
        for user in User.objects.filter(is_active=True):
            if user.email:
                user_csv.write(f'{user.email},{user.name}\n')
