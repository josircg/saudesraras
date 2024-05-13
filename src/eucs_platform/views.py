from itertools import chain

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.admin.views.main import SEARCH_VAR
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.utils import translation
from django.utils.safestring import mark_safe
from django.utils.translation import get_language
from django_countries import countries
from django_countries.templatetags.countries import get_country
from eucs_platform.models import Post
from events.models import Event
from machina.apps.forum.models import Forum
from machina.apps.forum_conversation.models import Topic
from machina.apps.forum_tracking.handler import TrackingHandler
from organisations.models import Organisation
from organisations.views import getOrganisationAutocomplete
from platforms.models import Platform
from platforms.views import getPlatformsAutocomplete
from profiles.models import Profile
from profiles.views import getProfilesAutocomplete
from projects.models import Project, Topic as PTopic
from projects.views import getProjectsAutocomplete
from resources.models import Resource, ResourceGroup, ResourcesGrouped
from resources.views import getResourcesAutocomplete


def home(request):
    # TODO: Clean this, we dont need lot of things
    user = request.user
    filters = {'keywords': ''}
    items_per_page = 4
    page = request.GET.get('page')

    # Projects
    projects = Project.objects.filter(approved=True, hidden=False).order_by('-dateCreated')
    paginatorprojects = Paginator(projects, items_per_page)
    projects = paginatorprojects.get_page(page)
    counterprojects = paginatorprojects.count

    # Resources
    resources = Resource.objects.approved_resources().order_by('-dateUpdated')
    paginatorresources = Paginator(resources, items_per_page)
    resources = paginatorresources.get_page(page)
    counterresources = paginatorresources.count

    # Training Resources
    training_resources = Resource.objects.approved_training_resources().order_by('-dateUpdated')
    paginator_training_resources = Paginator(training_resources, items_per_page)
    training_resources = paginator_training_resources.get_page(page)
    countertresources = paginator_training_resources.count

    # Organisations
    # TODO: Put -dateCreated
    organisations = Organisation.objects.all().order_by('id')
    if request.GET.get('keywords'):
        organisations = organisations.filter(Q(name__icontains=request.GET['keywords'])).distinct()
    paginatororganisation = Paginator(organisations, items_per_page)
    organisations = paginatororganisation.get_page(page)
    counterorganisations = paginatororganisation.count

    # Platforms
    platforms = Platform.objects.filter(active=True).order_by('-dateCreated')
    paginator_platform = Paginator(platforms, items_per_page)
    platforms = paginator_platform.get_page(page)
    counter_platforms = paginator_platform.count

    if settings.VISAO_USERNAME:
        base_endpoint = f'{settings.VISAO_URL}/visao2/viewGroupCategory/{settings.VISAO_GROUP}?'
        compare_topics_endpoint = mark_safe(
            f'{settings.VISAO_URL}/app/#/visao?chart=1&grupCategory={settings.VISAO_GROUP}'
        )

        visao_endpoint = mark_safe(
            f'{base_endpoint}l={settings.VISAO_LAYER}&amp&ui=f&amp&header=f&amp&hideIndicator=t'
        )
        project_topics = [
            (str(ptopic), f'{base_endpoint}{ptopic.external_url}')
            for ptopic in PTopic.objects.topics_with_external_url().translated().order_by('translated_text')
        ]
    else:
        compare_topics_endpoint = None
        visao_endpoint = None
        project_topics = []

    # Events
    ongoing_events = Event.objects.approved_events().ongoing_events()
    upcoming_events = Event.objects.approved_events().upcoming_events()
    # Join ongoing and upcoming events in one paginator
    paginator_event = \
        Paginator(ongoing_events.union(upcoming_events, all=True).order_by('-featured', 'start_date', 'end_date'),
                  items_per_page)
    events = paginator_event.get_page(page)

    # Users
    counter_users = Profile.objects.count()

    total = countertresources + counterprojects + countertresources + counterorganisations

    return render(request, 'home.html', {
        'user': user,
        'projects': projects,
        'counterprojects': counterprojects,
        'resources': resources,
        'counterresources': counterresources,
        'filters': filters,
        'trainingResources': training_resources,
        'countertresources': countertresources,
        'organisations': organisations,
        'counterorganisations': counterorganisations,
        'platforms': platforms,
        'events': events,
        'counterPlatforms': counter_platforms,
        'counterUsers': counter_users,
        'total': total,
        'visao_endpoint': visao_endpoint,
        'compare_topics_endpoint': compare_topics_endpoint,
        'project_topics': project_topics,
        'isSearchPage': True,
    })


def all(request):
    return home(request)

def noticias(request):
    posts = Post.objects.filter(status=1).order_by('-created_on')
    return render(request, 'pages/{}/noticias.html'.format(get_language()), {'posts': posts})

def doencas(request):
    return render(request, 'pages/%s/doencas.html' % get_language())

def diagnostico(request):
    return render(request, 'pages/%s/diagnostico.html' % get_language())

def justica(request):
    return render(request, 'pages/%s/justica.html' % get_language())

def medicos(request):
    return render(request, 'pages/%s/medicos.html' % get_language())

def ajuda(request):
    return render(request, 'pages/%s/ajuda.html' % get_language())

def eventos(request):
    return render(request, 'pages/%s/eventos.html' % get_language())

def projeto(request):
    return render(request, 'pages/%s/projeto.html' % get_language())

def parceiro(request):
    return render(request, 'pages/%s/parceiro.html' % get_language())

def about(request):
    return render(request, 'pages/%s/about.html' % get_language())


def terms(request):
    return render(request, 'pages/%s/terms.html' % get_language())


def faq(request):
    return render(request, 'pages/%s/faq.html' % get_language())


def privacy(request):
    return render(request, 'pages/%s/privacy.html' % get_language())


def curated(request):
    groups = ResourceGroup.objects.get_queryset().order_by('id')
    resourcesgrouped = ResourcesGrouped.objects.get_queryset().order_by('group')
    return render(request, 'curated.html', {
        'groups': groups,
        'resourcesgrouped': resourcesgrouped,
        'isSearchPage': False})


def imprint(request):
    return render(request, 'imprint.html')


def contact(request):
    return render(request, 'contact.html')


def development(request):
    return render(request, 'development.html')


def moderation(request):
    return render(request, 'moderation.html')


def criteria(request):
    return render(request, 'criteria.html')


def moderation_quality_criteria(request):
    return render(request, 'moderation_quality_criteria.html')


def translations(request):
    return render(request, 'translations.html')


def guide(request):
    if settings.USE_GUIDE:
        return HttpResponseRedirect("/static/site/files/%s/%s" % (get_language(), settings.USE_GUIDE))
    else:
        return render(request, 'guide.html')


def home_autocomplete(request):
    if request.GET.get('q'):
        text = request.GET['q']
        is_admin = request.user and request.user.is_staff
        projects = getProjectsAutocomplete(text)
        resources = getResourcesAutocomplete(text, False)
        training = getResourcesAutocomplete(text, True)
        organisations = getOrganisationAutocomplete(text, is_admin)
        platforms = getPlatformsAutocomplete(text)
        profiles = getProfilesAutocomplete(text)
        report = chain(resources, projects, training, organisations, platforms, profiles)
        response = list(report)
        return JsonResponse(response, safe=False)
    else:
        return HttpResponse("No cookies")


def getTopicsResponded(request):
    response = {}
    topics = {}
    if not request.user.is_anonymous and not request.user.is_staff:
        own_topics = Topic.objects.get_queryset().filter(status=0, poster_id=request.user, posts_count__gt=1)
        suscribed_topics = request.user.topic_subscriptions.all()
        result = own_topics | suscribed_topics
        result = result.distinct()
        topics = TrackingHandler.get_unread_topics(request, result, request.user)

    topicshtml = "</br>"

    for topic in topics:
        slug = '' + topic.slug + '-' + str(topic.id)
        forum = get_object_or_404(Forum, id=topic.forum_id)
        forum_slug = forum.slug + '-' + str(forum.id)
        topicshtml += (
                '<p class="alert alert-info" role="alert">There is a response in a topic that you follow'
                ' <a href="' + settings.HOST + '/forum/forum/' + forum_slug + '/topic/' + slug + '">%s</a></p>' %
                topic.subject
        )

    response['topics'] = topicshtml
    return JsonResponse(response)


def getForumResponsesNumber(request):
    response = {}
    forumresponses = 0
    if not request.user.is_anonymous and not request.user.is_staff:
        own_topics = Topic.objects.get_queryset().filter(status=0, poster_id=request.user, posts_count__gt=1)
        suscribed_topics = request.user.topic_subscriptions.all()
        result = own_topics | suscribed_topics
        result = result.distinct()
        result = TrackingHandler.get_unread_topics(request, result, request.user)
        forumresponses = len(result)

    response['forumresponses'] = forumresponses
    return JsonResponse(response)


@staff_member_required(login_url='/login')
def country_list(request):
    """Page with admin style to list countries from django-countries"""
    if SEARCH_VAR in request.GET:
        text = request.GET.get(SEARCH_VAR)
        result = filter(lambda c: text.lower() in c.name.lower(), countries)
    else:
        result = countries
    # Return country name translations
    result = country_translation(result)

    return render(request, 'country_list.html', {'countries': result})


def country_translation(country_iterator):
    """Rebuild country list to return translations"""
    for country in country_iterator:
        country_object = get_country(country.code)
        yield {
            'code': country_object.code,
            'name_english': get_country_translated_name('en', country_object),
            'name_portuguese': get_country_translated_name('pt-br', country_object),
            'name_spanish': get_country_translated_name('es', country_object),
        }


def get_country_translated_name(language, country):
    with translation.override(language):
        return translation.gettext(country.countries.name(country.code))
