import copy
import csv

from PIL import Image, ImageOps
from authors.models import Author
from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.core.validators import EMPTY_VALUES
from django.db.models import Q
from django.http import HttpResponse, JsonResponse, StreamingHttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _
from eucs_platform import send_email
from eucs_platform.logger import log_message
from rest_framework import status
from utilities.file import save_image_with_path

from .forms import ResourceForm, ResourcePermissionForm
from .models import Resource, Keyword, SavedResources, BookmarkedResources, Theme, Category
from .models import ResourcesGrouped, ResourcePermission

User = get_user_model()


def training_resources(request):
    return resources(request, True)


def resources(request, isTrainingResource=False):
    user = request.user
    if isTrainingResource:
        endPoint = 'training_resources'
    else:
        endPoint = 'resources'

    resources = Resource.objects.all().filter(isTrainingResource=isTrainingResource).order_by('-dateUpdated')
    languagesWithContent = Resource.objects.all().filter(
        isTrainingResource=isTrainingResource).values_list('inLanguage', flat=True).distinct()

    resources = resources.order_by('id')

    themes = Theme.objects.translated_sorted_by_text()
    categories = Category.objects.translated_sorted_by_text()

    filters = {'keywords': '', 'inLanguage': ''}
    resources = applyFilters(request, resources)
    filters = setFilters(request, filters)
    resources = resources.distinct()

    if not user.is_staff:
        resources = resources.filter(approved=True)

    # Ordering
    if request.GET.get('orderby'):
        orderBy = request.GET.get('orderby')
        if "featured" in orderBy:
            resources = resources.filter(featured=True)
            # Qual é a lógica aqui ?
            # resourcesTopIds = list(resourcesTop.values_list('id', flat=True))
            # resources = resources.exclude(id__in=resourcesTopIds)
            # resources = list(resourcesTop) + list(resources)
        elif "name" in orderBy:
            resources = resources.order_by('name')
        else:
            resources = resources.order_by('-dateUpdated')
        filters['orderby'] = request.GET['orderby']
    else:
        resources = resources.order_by('-dateUpdated')

    counter = len(resources)
    paginator = Paginator(resources, 16)
    page = request.GET.get('page')
    resources = paginator.get_page(page)

    return render(request, 'resources.html', {
        'resources': resources,
        'counter': counter,
        'filters': filters,
        'settings': settings,
        'languagesWithContent': languagesWithContent,
        'themes': themes,
        'categories': categories,
        'isTrainingResource': isTrainingResource,
        'endPoint': endPoint,
        'isSearchPage': True})


@login_required(login_url='/login')
def newTrainingResource(request):
    return newResource(request, True)


@login_required(login_url='/login')
def newResource(request, isTrainingResource=False):
    form = ResourceForm()

    return render(
        request, 'resource_form.html',
        {'form': form, 'settings': settings, 'isTrainingResource': isTrainingResource}
    )


def training_resource(request, pk):
    return resource(request, pk)


def resource(request, pk):
    resource = get_object_or_404(Resource, id=pk)
    isTrainingResource = resource.isTrainingResource
    user = request.user

    if isTrainingResource:
        endPoint = '/training_resources'
    else:
        endPoint = '/resources'

    previous_page = request.META.get('HTTP_REFERER')
    if previous_page and 'review' in previous_page:
        # Send email
        to = copy.copy(settings.EMAIL_RECIPIENT_LIST)
        to.append(resource.creator.email)
        if resource.isTrainingResource:
            send_email(
                subject='Seu recurso de formação “%s” recebeu uma avaliação!' % resource.name,
                message=render_to_string('emails/training_resource_review.html', {
                    "domain": settings.HOST,
                    "name": resource.name,
                    "id": pk}),
                to=to)
        else:
            send_email(
                subject='Seu recurso “%s“ recebeu uma avaliação!' % resource.name,
                message=render_to_string('emails/resource_review.html', {
                    "domain": settings.HOST,
                    "name": resource.name,
                    "id": pk}),
                to=to)

    users = getOtherUsers(resource.creator)
    cooperators = getCooperatorsEmail(pk)
    if (not resource.approved or resource.hidden) and \
            (user.is_anonymous or
             (user != resource.creator and not user.is_staff and user.id not in getCooperators(pk))):
        return redirect('../resources', {})
    permissionForm = ResourcePermissionForm(initial={
        'usersCollection': users,
        'selectedUsers': cooperators})
    savedResources = SavedResources.objects.all().filter(user_id=user.id).values_list(
        'resource_id', flat=True)
    bookmarkedResource = BookmarkedResources.objects.all().filter(user_id=user.id, resource_id=pk).exists()

    return render(request, 'resource.html', {
        'resource': resource,
        'savedResources': savedResources,
        'bookmarkedResource': bookmarkedResource,
        'cooperators': getCooperators(pk),
        'permissionForm': permissionForm,
        'isTrainingResource': isTrainingResource,
        'endPoint': endPoint,
        'isSearchPage': True})


@login_required(login_url='/login')
def editTrainingResource(request, pk):
    return editResource(request, pk)


@login_required(login_url='/login')
def editResource(request, pk):
    resource = get_object_or_404(Resource, id=pk)
    isTrainingResource = resource.isTrainingResource
    user = request.user
    cooperators = getCooperators(pk)
    if user != resource.creator and not user.is_staff and user.id not in cooperators:
        if isTrainingResource:
            return redirect('/training_resources')
        return redirect('../resources', {})

    curatedGroups = list(ResourcesGrouped.objects.all().filter(resource_id=pk).values_list('group_id', flat=True))

    # TODO: is needed with image?
    form = ResourceForm(initial={
        # Main information, mandatory
        'name': resource.name,
        'url': resource.url,
        'keywords': resource.keywords.all,
        'abstract': resource.abstract,
        'description_citizen_science_aspects': resource.description_citizen_science_aspects,
        'category': getCategory(resource.category),
        'categorySelected': resource.category.id,
        'theme': resource.theme.all,
        # Publish information
        'authors': resource.authors.all,
        'publisher': resource.publisher,
        'year_of_publication': resource.datePublished,
        'resource_DOI': resource.resourceDOI,
        'license': resource.license,
        # Training related fields
        # Links
        'project': resource.project.all,
        'organisation': resource.organisation.all,
        # Images
        'image_credit1': resource.imageCredit1,
        'image_credit2': resource.imageCredit2,
        'image1': resource.image1,
        'image2': resource.image2,
        'withImage1': (True, False)[resource.image1 == ""],
        'withImage2': (True, False)[resource.image2 == ""],
    })

    if request.method == 'POST':
        form = ResourceForm(request.POST, request.FILES)
        if form.is_valid():
            images = []
            image1_path = saveImage(request, form, 'image1', '1')
            image2_path = saveImage(request, form, 'image2', '2')
            images.append(image1_path)
            images.append(image2_path)
            form.save(request, images)
            if isTrainingResource:
                return redirect('/training_resource/' + str(pk))
            return redirect('/resource/' + str(pk))

    return render(request, 'resource_form.html', {
        'form': form,
        'resource': resource,
        'curatedGroups': curatedGroups,
        'user': user,
        'settings': settings,
        'isTrainingResource': isTrainingResource})


# TODO: Verificar se ainda está sendo utilizado
def saveResourceAjax(request):
    request.POST = request.POST.copy()
    request.POST = updateKeywords(request.POST)
    request.POST = updateAuthors(request.POST)
    form = ResourceForm(request.POST, request.FILES)

    isTrainingResource = request.POST.get('isTrainingResource') == 'True'

    if form.is_valid():
        images = setImages(request, form)
        pk = form.save(request, images)

        if pk and not request.POST.get('resourceID').isnumeric():
            sendResourceEmail(pk, request, isTrainingResource, form)

        if isTrainingResource:
            redirect_to = f'/training_resource/{pk}'
        else:
            redirect_to = f'/resource/{pk}'

        return JsonResponse(
            {'ResourceCreated': 'OK', 'Resource': pk, 'redirect_to': redirect_to}, status=status.HTTP_200_OK
        )
    else:
        return JsonResponse(form.errors, status=status.HTTP_406_NOT_ACCEPTABLE)


def sendResourceEmail(id, request, isTrainingResource, form):
    if isTrainingResource:
        msg = _('Training Resource added correctly!')
        resource_url = 'training_resource'
        resource_edit_url = 'editTrainingResource'
    else:
        msg = _('Resource added correctly!')
        resource_url = 'resource'
        resource_edit_url = 'editResource'

    messages.success(request, msg)

    to = [request.user.email]

    context = {
        'domain': settings.DOMAIN, 'submissionName': form.cleaned_data['name'], 'resource_url': resource_url,
        'resourceid': id, 'resource_edit_url': resource_edit_url
    }

    send_email(
        subject=_('Your resource "%s" has been submitted!') % form.cleaned_data['name'],
        message=render_to_string('emails/new_resource.html', context), to=to, reply_to=settings.EMAIL_CIVIS
    )

    send_email(
        subject=_('Notification - New resource "%s" submitted') % form.cleaned_data['name'],
        message=render_to_string('emails/notify_resource.html', context), to=settings.EMAIL_CIVIS, reply_to=to
    )


def updateKeywords(dictio):
    keywords = dictio.pop('keywords', None)
    if (keywords):
        for k in keywords:
            if not k.isdecimal():
                # This is a new keyword
                Keyword.objects.get_or_create(keyword=k)
                keyword_id = Keyword.objects.get(keyword=k).id
                dictio.update({'keywords': keyword_id})
            else:
                # This keyword is already in the database
                dictio.update({'keywords': k})
    return dictio


def updateAuthors(dictio):
    authors = dictio.pop('authors', None)
    if (authors):
        for a in authors:
            if not a.isdecimal():
                # This is a new author
                Author.objects.get_or_create(author=a)
                author_id = Author.objects.get(author=a).id
                dictio.update({'authors': author_id})
            else:
                # This author is already in the database
                dictio.update({'author': a})
    return dictio


def setImages(request, form):
    images = []
    image1_path = saveImage(request, form, 'image1', '1')
    image2_path = saveImage(request, form, 'image2', '2')
    images.append(image1_path)
    images.append(image2_path)
    return images


def deleteResource(request, pk, isTrainingResource):
    obj = get_object_or_404(Resource, id=pk)
    if request.user == obj.creator or request.user.is_staff or request.user.id in getCooperators(pk):
        obj.delete()
        reviews = Review.objects.filter(content_type=ContentType.objects.get(model="resource"), object_pk=pk)
        for r in reviews:
            r.delete()
    if isTrainingResource:
        return redirect('training_resources')
    else:
        return redirect('resources')


def trainingsAutocompleteSearch(request):
    return resourcesAutocompleteSearch(request, True)


def resourcesAutocompleteSearch(request, isTrainingResource=False):
    if request.GET.get('q'):
        text = request.GET['q']
        resources = getResourcesAutocomplete(text, isTrainingResource)
        resources = list(resources)
        return JsonResponse(resources, safe=False)
    else:
        return HttpResponse("No cookies")


def getResourcesAutocomplete(text, isTrainingResource=False):
    resources = Resource.objects.filter(approved=True).filter(name__icontains=text)
    if isTrainingResource:
        resources = resources.filter(isTrainingResource=True)
    else:
        resources = resources.filter(isTrainingResource=False)
    resources = resources.values_list('id', 'name').distinct()
    keywords = Keyword.objects.filter(
        keyword__icontains=text).values_list('keyword', flat=True).distinct()
    report = []
    for resource in resources:
        if isTrainingResource:
            report.append({"type": "training", "id": resource[0], "text": resource[1]})
        else:
            report.append({"type": "resource", "id": resource[0], "text": resource[1]})
    for keyword in keywords:
        if isTrainingResource:
            numberElements = Resource.objects.filter(
                Q(keywords__keyword__icontains=keyword)).filter(
                isTrainingResource=True).count()
            report.append({"type": "trainingKeyword", "text": keyword, "numberElements": numberElements})
        else:
            numberElements = Resource.objects.filter(
                Q(keywords__keyword__icontains=keyword)).filter(
                ~Q(isTrainingResource=True)).count()
            report.append({"type": "resourceKeyword", "text": keyword, "numberElements": numberElements})
    return report


def getOtherUsers(creator):
    users = list(User.objects.all().exclude(is_superuser=True).exclude(id=creator.id).values_list('name', 'email'))
    return users


def getCooperators(resourceID):
    users = list(ResourcePermission.objects.all().filter(resource_id=resourceID).values_list('user', flat=True))
    return users


def getCooperatorsEmail(resourceID):
    users = getCooperators(resourceID)
    cooperators = ""
    for user in users:
        userObj = get_object_or_404(User, id=user)
        cooperators += userObj.email + ", "
    return cooperators


def clearFilters(request):
    return redirect('resources')


def saveImage(request, form, element, ref):
    image_path = ''
    filepath = request.FILES.get(element, False)
    withImage = form.cleaned_data.get('withImage' + ref)
    if filepath:
        x = form.cleaned_data.get('x' + ref)
        y = form.cleaned_data.get('y' + ref)
        w = form.cleaned_data.get('width' + ref)
        h = form.cleaned_data.get('height' + ref)
        photo = request.FILES[element]
        image = Image.open(photo)
        # Fix image orientation based on EXIF information
        fixed_image = ImageOps.exif_transpose(image)
        cropped_image = fixed_image.crop((x, y, w + x, h + y))
        if ref == '2':
            finalSize = (1100, 400)
        else:
            finalSize = (600, 400)
        resized_image = cropped_image.resize(finalSize, Image.LANCZOS)

        if cropped_image.width > fixed_image.width:
            size = (
                abs(int((finalSize[0] - (finalSize[0] / cropped_image.width * fixed_image.width)) / 2)), finalSize[1]
            )
            whitebackground = Image.new(mode='RGBA', size=size, color=(255, 255, 255, 0))
            position = ((finalSize[0] - whitebackground.width), 0)
            resized_image.paste(whitebackground, position)
            position = (0, 0)
            resized_image.paste(whitebackground, position)
        if cropped_image.height > fixed_image.height:
            size = (
                finalSize[0], abs(int((finalSize[1] - (finalSize[1] / cropped_image.height * fixed_image.height)) / 2))
            )
            whitebackground = Image.new(mode='RGBA', size=size, color=(255, 255, 255, 0))
            position = (0, (finalSize[1] - whitebackground.height))
            resized_image.paste(whitebackground, position)
            position = (0, 0)
            resized_image.paste(whitebackground, position)

        image_path = save_image_with_path(resized_image, photo.name)
    elif withImage:
        image_path = '/'
    else:
        image_path = ''
    return image_path


def preFilteredResources(request):
    resources = Resource.objects.all().order_by('id')
    return applyFilters(request, resources)


def applyFilters(request, resources):
    if request.GET.get('keywords'):
        resources = resources.filter(
            Q(name__icontains=request.GET['keywords']) |
            Q(keywords__keyword__icontains=request.GET['keywords'])).distinct()
    if request.GET.get('inLanguage'):
        resources = resources.filter(inLanguage=request.GET['inLanguage'])
    if request.GET.get('license'):
        resources = resources.filter(license__icontains=request.GET['license'])
    if request.GET.get('theme'):
        theme_qs = Theme.objects.translated().filter(translated_text=request.GET['theme']).values_list('pk')
        resources = resources.filter(theme__pk__in=theme_qs)
    if request.GET.get('category'):
        category_qs = Category.objects.translated().filter(translated_text=request.GET['category']).values_list('pk')
        resources = resources.filter(category__pk__in=category_qs)
    if request.GET.get('approved'):
        if request.GET['approved'] == 'approved':
            resources = resources.filter(approved=True)
        if request.GET['approved'] == 'notApproved':
            resources = resources.filter(approved=False)
        if request.GET['approved'] == 'notYetModerated':
            resources = resources.filter(approved__isnull=True)
    else:
        resources = resources.filter(approved=True)

    return resources


def setFilters(request, filters):
    if request.GET.get('keywords'):
        filters['keywords'] = request.GET['keywords']
    if request.GET.get('inLanguage'):
        filters['inLanguage'] = request.GET['inLanguage']
    if request.GET.get('license'):
        filters['license'] = request.GET['license']
    if request.GET.get('theme'):
        filters['theme'] = request.GET['theme']
    if request.GET.get('category'):
        filters['category'] = request.GET['category']
    if request.GET.get('approved'):
        filters['approved'] = request.GET['approved']

    filters['has_active_filters'] = any([v not in EMPTY_VALUES for k, v in filters.items() if k != 'orderby'])

    return filters


def get_sub_category(request):
    category = request.GET.get("category")
    options = '<select id="id_subcategory" class="select form-control">'
    response = {}

    if category:
        sub_categories = Category.objects.filter(parent=category)
        sub_categories = sub_categories.values_list("id", "text")
        tupla_sub_categories = tuple(sub_categories)
        if tupla_sub_categories:
            for sub_category in tupla_sub_categories:
                options += '<option value = "%s">%s</option>' % (
                    sub_category[0],
                    sub_category[1]
                )
            options += '</select>'
            response['sub_categories'] = options
        else:
            response['sub_categories'] = '<select id="id_subcategory" class="select form-control" disabled></select>'
    else:
        response['sub_categories'] = '<select id="id_subcategory" class="select form-control" disabled></select>'
    return JsonResponse(response)


def getCategory(category):
    if category.parent:
        return category.parent
    else:
        return category


def bookmarkResource(request):
    resourceId = request.POST.get("resourceId")
    fResource = get_object_or_404(Resource, id=resourceId)
    user = request.user
    bookmark = False if request.POST.get("bookmark") in ['false'] else True
    if bookmark:
        BookmarkedResources.objects.get_or_create(resource=fResource, user=user)
        if fResource.isTrainingResource:
            resource_url = 'training_resource'
        else:
            resource_url = 'resource'

        to = copy.copy(settings.EMAIL_RECIPIENT_LIST)
        to.append(fResource.creator.email)

        send_email(
            subject=_("Your resource \"%s\" has been bookmarked!") % fResource.name,
            message=render_to_string('emails/library_resource.html', {
                'domain': settings.DOMAIN,
                'name': fResource.name,
                'id': fResource.pk,
                'resource_url': resource_url}),
            to=to)

        response = {"created": "OK", "resource": fResource.name}
    else:
        try:
            obj = BookmarkedResources.objects.get(resource_id=resourceId, user_id=user.id)
            obj.delete()
            response = {"success": "Bookmark deleted"}
        except BookmarkedResources.DoesNotExist:
            response = {"error": "Do not exits"}

    return JsonResponse(response, safe=False)


@login_required(login_url='/login')
def approve_resource(request, pk, status):
    resource = get_object_or_404(Resource, id=pk)
    if request.user.is_staff:
        resource.approved = status == 1
        resource.save()
        if resource.isTrainingResource:
            title = _('Training Resource')
            endpoint = 'trainingresource'
        else:
            title = _('Resource')
            endpoint = 'resource'

        if resource.approved:
            message = '%s %s' % (title, _('approved'))
        else:
            message = '%s %s' % (title, _('not approved'))

        log_message(resource, message, request.user)
        messages.success(request, message)
        return redirect(f'/admin/resources/{endpoint}/')
    else:
        messages.success(request, _('Only staff can approve object'))
        return redirect('../resources', {})


@staff_member_required()
def setFeaturedResource(request):
    resourceId = request.POST.get("resourceId")
    resource = get_object_or_404(Resource, id=resourceId)
    if request.POST.get("featured") in ['true']:
        resource.featured = True
    else:
        resource.featured = False
    resource.save()

    return JsonResponse({"success": "Updated featured resource"}, safe=False)


@staff_member_required()
def setTrainingResource(request):
    resourceId = request.POST.get("resourceId")
    resource = get_object_or_404(Resource, id=resourceId)
    if request.POST.get("isTraining") in ['true']:
        resource.isTrainingResource = True
    else:
        resource.isTrainingResource = False
    resource.save()

    return JsonResponse({"success": "Updated training resource"}, safe=False)


@staff_member_required()
def setHiddenResource(request):
    response = {}
    id = request.POST.get("resource_id")
    hidden = request.POST.get("hidden")
    setResourceHidden(id, hidden)
    return JsonResponse(response, safe=False)


def setResourceHidden(id, hidden):
    resource = get_object_or_404(Resource, id=id)
    resource.hidden = False if hidden in ['False', 'false', '0'] else True
    resource.save()


@staff_member_required()
def setTraining(request):
    response = {}
    id = request.POST.get("resource_id")
    status = request.POST.get("status")
    resource = get_object_or_404(Resource, id=id)
    resource.isTrainingResource = status
    resource.save()
    return JsonResponse(response, safe=False)


@staff_member_required()
def setOwnTraining(request):
    response = {}
    id = request.POST.get("resource_id")
    status = request.POST.get("status")
    resource = get_object_or_404(Resource, id=id)
    resource.own = status
    resource.save()
    return JsonResponse(response, safe=False)


def allowUserResource(request):
    response = {}
    resourceId = request.POST.get("resource_id")
    users = request.POST.get("users")
    resource = get_object_or_404(Resource, id=resourceId)

    if request.user != resource.creator and not request.user.is_staff:
        # TODO return JsonResponse with error code
        return redirect('../resources', {})

    # Delete all
    objs = ResourcePermission.objects.all().filter(resource_id=resourceId)
    if (objs):
        for obj in objs:
            obj.delete()

    # Insert all
    users = users.split(',')
    for user in users:
        fUser = User.objects.filter(email=user)[:1].get()
        resourcePermission = ResourcePermission(resource=resource, user=fUser)
        resourcePermission.save()

    return JsonResponse(response, safe=False)


def resource_review(request, pk):
    return render(request, 'resource_review.html', {'resourceID': pk})


# Download all resources in a CSV file
def downloadResources(request):
    resources = Resource.objects.get_queryset()

    response = StreamingHttpResponse(
        streaming_content=(iter_items(resources, Buffer())),
        content_type='text/csv',
    )
    response['Content-Disposition'] = 'attachment; filename="resources.csv"'
    return response


def get_headers():
    return [
        'id', 'name', 'abstract', 'keywords', 'inLanguage', 'category', 'url', 'license', 'authors', 'publisher',
        'datePublished', 'theme', 'resourceDOI'
    ]


def get_data(item):
    keywordsList = list(item.keywords.all().values_list('keyword', flat=True))
    authorsList = list(item.authors.all().values_list('author', flat=True))
    themeList = list(item.theme.all().values_list('theme', flat=True))

    return {
        'id': item.id,
        'name': item.name,
        'abstract': item.abstract,
        'keywords': keywordsList,
        'inLanguage': item.inLanguage,
        'category': item.category,
        'url': item.url,
        'license': item.license,
        'authors': authorsList,
        'publisher': item.publisher,
        'datePublished': item.datePublished,
        'theme': themeList,
        'resourceDOI': item.resourceDOI,
    }


class Buffer(object):
    def write(self, value):
        return value


def iter_items(items, pseudo_buffer):
    writer = csv.DictWriter(pseudo_buffer, fieldnames=get_headers())
    yield ','.join(get_headers()) + '\r\n'

    for item in items:
        yield writer.writerow(get_data(item))
