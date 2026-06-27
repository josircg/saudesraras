import re
from django.utils import timezone
from collections import OrderedDict
from itertools import chain
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.admin.views.main import SEARCH_VAR
from django.core.paginator import Paginator
from django.db.models import Q, Prefetch
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.shortcuts import render
from django.utils import translation
from django.utils.safestring import mark_safe
from django.utils.translation import get_language
from django_countries import countries
from django_countries.templatetags.countries import get_country
from blog.models import Post
from events.models import Event
from organisations.models import Organisation
from organisations.views import getOrganisationAutocomplete
from platforms.models import Platform
from platforms.views import getPlatformsAutocomplete
from profiles.models import Profile, InterestArea
from profiles.views import getProfilesAutocomplete
from projects.models import Project, Topic as PTopic
from projects.views import getProjectsAutocomplete
from resources.models import Resource, ResourceGroup, ResourcesGrouped
from resources.views import getResourcesAutocomplete
from pages.models import Page, Section

def home(request):
    user = request.user
    filters = {'keywords': ''}
    page = request.GET.get('page')

    # Blog
    items_per_page = 4
    posts = Post.objects.all().order_by('-sticky', '-created_on')[:4]
    paginatorposts = Paginator(posts, items_per_page)
    posts = paginatorposts.get_page(page)

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

    # Depoimentos
    depoimentos = Section.objects.filter(page__slug='depoimentos').order_by('order')[:3]

    # FAQ
    perguntas_frequentes = Section.objects.filter(page__slug='depoimentos').order_by('order')[:10]

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
        'posts': posts,
        'events': events,
        'depoimentos': depoimentos,
        'faq': perguntas_frequentes,
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

def riofarmes(request):
    return render(request, 'pages/%s/riofarmes.html' % get_language())

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

def projeto(request):
    return render(request, 'pages/%s/projeto.html' % get_language())

def pag_em_construcao(request):
    return render(request, 'pag_em_construcao.html')

def parceiro(request):
    return render(request, 'pages/%s/parceiro.html' % get_language())

def about(request):
    prefetch_funcoes = Prefetch(
        'interestAreas',
        queryset=InterestArea.objects.exclude(interestArea__iexact='Equipe')
    )

    equipe = Profile.objects.filter(
        team__lt=99
    ).prefetch_related(prefetch_funcoes).order_by(
        'team',
        'user__name'
    )

    todos_colaboradores = Profile.objects.filter(title__isnull=False).prefetch_related(prefetch_funcoes)
    
    periodos_dict = {}
    padrao_periodo = re.compile(r'\b(\d{4})[./]([12])\b')

    for perfil in todos_colaboradores:
        if perfil.title:
            matches = padrao_periodo.findall(perfil.title)
            periodos_unicos = set(f"{ano}.{semestre}" for ano, semestre in matches)
            
            for periodo_formatado in periodos_unicos:
                if periodo_formatado not in periodos_dict:
                    periodos_dict[periodo_formatado] = []
                
                if perfil not in periodos_dict[periodo_formatado]:
                    periodos_dict[periodo_formatado].append(perfil)

    periodos_ordenados = OrderedDict()
    for per in sorted(periodos_dict.keys(), reverse=True):
        periodos_ordenados[per] = sorted(
            periodos_dict[per], 
            key=lambda p: p.user.name.lower()
        )

    return render(
        request,
        'pages/%s/about.html' % get_language(),
        {
            'equipe': equipe,
            'equipe_por_periodo': periodos_ordenados
        }
    )

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


def development(request):
    return render(request, 'development.html')


def moderation(request):
    return render(request, 'moderation.html')


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
