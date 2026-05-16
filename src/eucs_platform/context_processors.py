from django.conf import settings
from organisations.models import OrganisationType

def global_settings(request):
    org_types = OrganisationType.objects.values('type').distinct().order_by('type')
    return {
        'TRANSLATED_LANGUAGES': settings.TRANSLATED_LANGUAGES,
        'FEATURED_MGT': settings.FEATURED_MGT,
        'FORUM_ENABLED': settings.FORUM_ENABLED,
        'all_organisation_types': org_types
    }
