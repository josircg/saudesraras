import copy
import os
import random
from datetime import datetime

from PIL import Image, ImageOps
from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.db import ProgrammingError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils import formats
from django.utils.translation import ugettext_lazy as _
from eucs_platform import send_email
from rest_framework import status
from utilities.models import SearchIndex, SearchIndexType

from .forms import PlatformForm
from .models import Platform, GeographicExtend


@staff_member_required(login_url='/login')
def newPlatform(request):
    user = request.user
    platformForm = PlatformForm()
    return render(request, 'platform_form.html', {'form': platformForm, 'user': user})


@staff_member_required(login_url='/login')
def editPlatform(request, pk):
    user = request.user
    platform = get_object_or_404(Platform, id=pk)

    if user != platform.creator and not user.is_staff:
        return redirect('../platforms', {})

    platformForm = PlatformForm(initial={
        'name': platform.name,
        'url': platform.url,
        'description': platform.description,
        'geoExtend': platform.geoExtend,
        'countries': platform.countries,
        'contactPoint': platform.contactPoint,
        'contactPointEmail': platform.contactPointEmail,
        'organisation': platform.organisation.all,
        'logo': platform.logo,
        'logoCredit': platform.logoCredit,
        'profileImage': platform.profileImage,
        'profileImageCredit': platform.profileImageCredit
    })
    return render(request, 'platform_form.html', {'form': platformForm, 'user': user, 'id': platform.id})


@staff_member_required(login_url='/login')
def deletePlatformAjax(request, pk):
    platform = get_object_or_404(Platform, id=pk)
    if request.user == platform.creator or request.user.is_staff:
        platform.delete()
        return JsonResponse({'Platform deleted': 'OK', 'Id': pk}, status=status.HTTP_200_OK)
    else:
        return JsonResponse({}, status=status.HTTP_403.FORBIDDEN)


@staff_member_required(login_url='/login')
def savePlatformAjax(request):
    form = PlatformForm(request.POST, request.FILES)
    if form.is_valid():
        images = setImages(request, form)
        pk = form.save(request, images)
        if request.POST.get('Id').isnumeric():
            return JsonResponse({'Platform updated': 'OK', 'Id': pk}, status=status.HTTP_200_OK)
        else:
            sendPlatformEmail(pk, request, form)
            return JsonResponse({'Platform created': 'OK', 'Id': pk}, status=status.HTTP_200_OK)
    else:
        return JsonResponse(form.errors, status=status.HTTP_406_NOT_ACCEPTABLE)


def sendPlatformEmail(id, request, form):
    to = copy.copy(settings.EMAIL_RECIPIENT_LIST)
    to.append(request.user.email)
    messages.success(request, _('Platform added correctly'))
    send_email(
        subject='Sua plataforma "%s" foi submetida!' % form.cleaned_data['name'],
        message=render_to_string('emails/new_platform.html',
                                 {"domain": settings.DOMAIN, 'submissionName': form.cleaned_data['name'],
                                  'username': request.user.name}),
        reply_to=settings.EMAIL_CIVIS, to=to
    )

    # NOTIFICAÇÃO
    send_email(
        subject='Notificação - Uma nova Plataforma "%s" foi submetida' % form.cleaned_data['name'],
        message=render_to_string('emails/notify_platform.html', {"platformid": id, "domain": settings.DOMAIN,
                                                                 'submissionName': form.cleaned_data['name'],
                                                                 'username': request.user.name}),
        reply_to=to, to=settings.EMAIL_CIVIS
    )


def platform(request, pk):
    platform = get_object_or_404(Platform.objects.select_related('geoExtend'), id=pk)
    return render(request, 'platform.html', {'platform': platform})


def platforms(request):
    platforms = Platform.objects.select_related('geoExtend').filter(active=True)
    countries = Platform.objects.all().values_list('countries', flat=True).distinct()
    geographicExtend = GeographicExtend.objects.translated_sorted_by_text()

    # I think this is not needded
    filters = {'keywords': '', 'geographicExtend': '', 'country': ''}

    platforms = applyFilters(request, platforms)
    platforms = platforms.distinct()
    filters = setFilters(request, filters)
    # Distinct list of countries
    countriesWithContent = [country for gcountry in countries for country in gcountry.split(',')]
    countriesWithContent = list(set(countriesWithContent))

    # Ordering
    if request.GET.get('orderby'):
        orderBy = request.GET.get('orderby')
        if "name" in orderBy:
            platforms = platforms.order_by('name')
    else:
        platforms = platforms.order_by('-dateUpdated')

    try:
        counter = len(platforms)
    except ProgrammingError:
        counter = 0
        platforms = Platform.objects.none()

    paginator = Paginator(platforms, 16)
    page = request.GET.get('page')
    platforms = paginator.get_page(page)

    return render(request, 'platforms.html', {
        'platforms': platforms,
        'filters': filters,
        'countriesWithContent': countriesWithContent,
        'counter': counter,
        'geographicExtend': geographicExtend,
        'isSearchPage': True})


def applyFilters(request, platforms):
    if request.GET.get('keywords'):
        platforms = platforms.filter(
            pk__in=SearchIndex.objects.full_text_search_ids(request.GET['keywords'], SearchIndexType.PLATFORM.value)
        )

    if request.GET.get('country'):
        platforms = platforms.filter(countries__contains=request.GET['country'])

    if request.GET.get('geographicExtend'):
        geoextend_qs = GeographicExtend.objects.translated().filter(translated_text=request.GET['geographicExtend'])
        platforms = platforms.filter(geoExtend__pk__in=geoextend_qs.values_list('pk'))

    return platforms


def setFilters(request, filters):
    if request.GET.get('keywords'):
        filters['keywords'] = request.GET['keywords']
    if request.GET.get('orderby'):
        filters['orderby'] = request.GET['orderby']
    if request.GET.get('country'):
        filters['country'] = request.GET['country']
    if request.GET.get('geographicExtend'):
        filters['geographicExtend'] = request.GET['geographicExtend']
    return filters


def setImages(request, form):
    images = {}
    for key, value in request.FILES.items():
        x = form.cleaned_data.get('x' + key)
        y = form.cleaned_data.get('y' + key)
        w = form.cleaned_data.get('width' + key)
        h = form.cleaned_data.get('height' + key)
        image = Image.open(value)
        # Fix image orientation based on EXIF information
        image = ImageOps.exif_transpose(image)
        image = image.crop((x, y, w + x, h + y))
        if key == 'profileImage':
            finalsize = (1100, 400)
        else:
            finalsize = (600, 400)
        image = image.resize(finalsize, Image.LANCZOS)
        imagePath = getImagePath(value.name)
        image.save(os.path.join(settings.MEDIA_ROOT, imagePath))
        images[key] = imagePath
    return images


def getImagePath(imageName):
    _datetime = formats.date_format(datetime.now(), 'Y-m-d_hhmmss')
    random_num = random.randint(0, 1000)
    return "images/" + _datetime + '_' + str(random_num) + '_' + imageName
