from django.conf import settings


def global_settings(request):
    return {
        'TRANSLATED_LANGUAGES': settings.TRANSLATED_LANGUAGES,
        'FEATURED_MGT': settings.FEATURED_MGT,
        'FORUM_ENABLED': settings.FORUM_ENABLED
    }
