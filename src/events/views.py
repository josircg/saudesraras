import copy

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.utils import formats
from django.utils.translation import ugettext_lazy as _
from eucs_platform import send_email
from eucs_platform.logger import log_message
from django.db.models import Q
from django.utils import timezone

from .forms import EventForm
from .models import Event


def set_pages_and_get_object_list(paginator, pages, page_num):
    """Append a page object into page list and return object_list from actual page"""
    try:
        p_obj = paginator.page(page_num)
        object_list = p_obj.object_list
        pages.append(p_obj)
    except EmptyPage:
        object_list = []
    return object_list


def events(request):
    user = request.user
    page = request.GET.get('page', 1)
    keywords = request.GET.get('keywords', '').strip()
    orderby = request.GET.get('orderby', '-start_date')
    status = request.GET.get('status', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')

    upcoming_events = Event.objects.upcoming_events()
    ongoing_events = Event.objects.ongoing_events()
    past_events = Event.objects.past_events()

    if not user.is_staff:
        upcoming_events = upcoming_events.approved_events()
        ongoing_events = ongoing_events.approved_events()
        past_events = past_events.approved_events()

    if keywords:
        kw_filter = Q(title__icontains=keywords) | Q(description__icontains=keywords)
        upcoming_events = upcoming_events.filter(kw_filter)
        ongoing_events = ongoing_events.filter(kw_filter)
        past_events = past_events.filter(kw_filter)

    if start_date:
        upcoming_events = upcoming_events.filter(start_date__gte=start_date)
        ongoing_events = ongoing_events.filter(start_date__gte=start_date)
        past_events = past_events.filter(start_date__gte=start_date)

    if end_date:
        upcoming_events = upcoming_events.filter(start_date__lte=end_date)
        ongoing_events = ongoing_events.filter(start_date__lte=end_date)
        past_events = past_events.filter(start_date__lte=end_date)

    if status == 'ongoing':
        upcoming_events = Event.objects.none()
        past_events = Event.objects.none()
    elif status == 'upcoming':
        ongoing_events = Event.objects.none()
        past_events = Event.objects.none()
    elif status == 'past':
        upcoming_events = Event.objects.none()
        ongoing_events = Event.objects.none()

    if orderby == 'title':
        ordering_field = 'title'
    elif orderby == 'start_date':       
        ordering_field = 'start_date'
    elif orderby == '-start_date':      
        ordering_field = '-start_date'
    else:                               
        ordering_field = 'start_date'

    upcoming_events = upcoming_events.order_by(ordering_field)
    ongoing_events = ongoing_events.order_by(ordering_field)
    past_events = past_events.order_by(ordering_field)

    
    counter = upcoming_events.count() + ongoing_events.count() + past_events.count()

    
    paginator_upcoming = Paginator(upcoming_events, 10)
    paginator_ongoing = Paginator(ongoing_events, 10)
    paginator_past = Paginator(past_events, 10)

    page_list = []
    upcoming_events = set_pages_and_get_object_list(paginator_upcoming, page_list, page)
    ongoing_events = set_pages_and_get_object_list(paginator_ongoing, page_list, page)
    past_events = set_pages_and_get_object_list(paginator_past, page_list, page)

    page_obj = max(page_list, key=lambda item: item.paginator.num_pages) if page_list else None

    filters = {
        'keywords': keywords,
        'orderby': orderby,
        'status': status,
        'start_date': start_date,
        'end_date': end_date,
    }

    return render(request, 'events.html', {
        'isSearchPage': True,
        'upcoming_events': upcoming_events,
        'ongoing_events': ongoing_events,
        'past_events': past_events,
        'page_obj': page_obj,
        'counter': counter,
        'filters': filters,
        'user': user
    })
    
@login_required(login_url='/login')
def new_event(request):
    user = request.user
    form = EventForm()
    if request.method == 'POST':
        form = EventForm(request.POST)
        if request.FILES.get('logo'):
            logo_path = request.FILES.get('logo')
        if form.is_valid():
            pk = form.save(request, logo_path)
            sendEventEmail(pk, request, form)
            return redirect('/events')
        else:
            print(form.errors)
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
        'logo': event.logo,
        'url': event.url})
    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            logo_path = request.FILES.get('logo')
            form.save(request, logo_path)
            return redirect('/events')
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
