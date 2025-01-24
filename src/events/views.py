import copy

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import ProgrammingError
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.utils import formats
from django.utils.translation import ugettext_lazy as _
from eucs_platform import send_email, set_pages_and_get_object_list
from eucs_platform.logger import log_message
from utilities.models import SearchIndex, SearchIndexType

from .forms import EventForm
from .models import Event


def events(request):
    user = request.user
    page = request.GET.get('page', 1)
    # period key = A means list all events (upcoming, ongoing, past)
    filters = {'keywords': '', 'period': 'A', 'language': ''}
    search_filters = {}

    if request.GET.get('pk'):
        search_filters['pk'] = request.GET.get('pk')
    else:
        if request.GET.get('keywords'):
            search_filters['pk__in'] = SearchIndex.objects.full_text_search_ids(request.GET['keywords'],
                                                                                SearchIndexType.EVENT.value)
            filters['keywords'] = request.GET['keywords']

        if request.GET.get('language'):
            search_filters['language'] = request.GET['language']
            filters['language'] = request.GET['language']

        if request.GET.get('period'):
            filters['period'] = request.GET['period']

    qs = Event.objects.filter(**search_filters)
    upcoming_events = qs.upcoming_events()
    ongoing_events = qs.ongoing_events()
    past_events = qs.past_events()

    if not user.is_staff:
        upcoming_events = upcoming_events.approved_events()
        ongoing_events = ongoing_events.approved_events()
        past_events = past_events.approved_events()

    try:
        counter = len(upcoming_events) + len(ongoing_events) + len(past_events)
    except ProgrammingError:
        counter = 0
        upcoming_events = Event.objects.none()
        ongoing_events = upcoming_events
        past_events = upcoming_events

    paginator_upcoming = Paginator(upcoming_events, 10)
    paginator_ongoing = Paginator(ongoing_events, 10)
    paginator_past = Paginator(past_events, 10)

    page_list = []

    upcoming_events = set_pages_and_get_object_list(paginator_upcoming, page_list, page)
    ongoing_events = set_pages_and_get_object_list(paginator_ongoing, page_list, page)
    past_events = set_pages_and_get_object_list(paginator_past, page_list, page)
    # Return the page object from paginator with max pages, to command pagination
    if page_list:
        if request.GET.get('pk'):
            # Returns page_obj with one item to build meta tags for this item
            page_obj = max(page_list, key=lambda item: item.paginator.count)
        else:
            page_obj = max(page_list, key=lambda item: item.paginator.num_pages)
    else:
        page_obj = None

    return render(
        request, 'events.html', {
            'upcoming_events': upcoming_events,
            'ongoing_events': ongoing_events,
            'past_events': past_events,
            'page_obj': page_obj,
            'user': user,
            'filters': filters,
            'isSearchPage': True,
            'counter': counter,
        }
    )


@login_required(login_url='/login')
def new_event(request):
    user = request.user
    form = EventForm()
    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            pk = form.save(request)
            sendEventEmail(pk, request, form)
            return redirect('/events')
        else:
            messages.error(request, _('Please correct the errors below.'))
    return render(request, 'event_form.html', {'form': form, 'user': user})


@login_required(login_url='/login')
def approve_event(request, pk, status):
    event = get_object_or_404(Event, id=pk)
    if request.user.is_staff:
        event.approved = status == 1
        event.save()
        if event.approved:
            message = _('Event approved')
        else:
            message = _('Event not approved')
        log_message(event, message, request.user)
        messages.success(request, message)
        return redirect('/admin/events/event/')
    else:
        messages.success(request, _('Only staff can approve object'))
        return redirect('../events', {})


def sendEventEmail(event_id, request, form):
    to = copy.copy(settings.EMAIL_RECIPIENT_LIST)
    to.append(request.user.email)
    messages.success(request, _('Event added correctly'))
    context = {
        'domain': settings.DOMAIN, 'submissionName': form.cleaned_data['title'],
        'username': request.user.name, 'eventid': event_id
    }

    send_email(
        subject=_('Your event "%s" has been submitted!') % form.cleaned_data['title'],
        message=render_to_string('emails/new_event.html', context), to=to, reply_to=settings.EMAIL_CIVIS
    )

    send_email(
        subject=_('Notification - New event "%s" submitted') % form.cleaned_data['title'],
        message=render_to_string('emails/notify_event.html', context), reply_to=to, to=settings.EMAIL_CIVIS
    )


@login_required(login_url='/login')
def editEvent(request, pk):
    user = request.user
    event = get_object_or_404(Event, id=pk)

    if user != event.creator and not user.is_staff:
        return redirect('../events', {})

    start_datetime = None
    end_datetime = None
    if event.start_date:
        start_datetime = formats.date_format(event.start_date, 'Y-m-d')
    if event.end_date:
        end_datetime = formats.date_format(event.end_date, 'Y-m-d')
    form = EventForm(initial={
        'title': event.title,
        'description': event.description,
        'place': event.place,
        'start_date': start_datetime,
        'end_date': end_datetime,
        'hour': event.hour,
        'url': event.url})
    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            form.save(request)
            return redirect('/events')
        else:
            messages.error(request, _('Please correct the errors below.'))
    return render(request, 'event_form.html', {'form': form, 'user': user, 'event': event})


def deleteEvent(request, pk):
    obj = get_object_or_404(Event, id=pk)
    if request.user == obj.creator or request.user.is_staff:
        obj.delete()
    return redirect('events')


@staff_member_required()
def setFeaturedEvent(request):
    response = {}
    id = request.POST.get("event_id")
    featured = request.POST.get("featured")
    event = get_object_or_404(Event, id=id)
    event.featured = False if featured == 'false' else True
    event.save()
    return JsonResponse(response, safe=False)
