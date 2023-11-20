import csv
import re
from io import TextIOWrapper
from urllib.parse import urlencode

from PIL import Image
from contact.models import Subscriber, Newsletter
from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import BadHeaderError
from django.core.validators import validate_email
from django.db.models import F
from django.http import HttpResponse, FileResponse
from django.shortcuts import redirect
from django.shortcuts import render, get_object_or_404
from django.template import Template, Context
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import translation
from django.utils.translation import ugettext_lazy as _
from django.views import generic
from django.views.generic import CreateView
from eucs_platform import send_email
from eucs_platform.logger import log_message
from events.models import Event
from projects.models import Project
from resources.models import Resource

from .forms import ContactForm, SubmitterContactForm, SubscribeForm, ImportForm, ForumProposalForm


def contactView(request):
    if request.method == 'GET':
        form = ContactForm()
    else:
        form = ContactForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            surname = form.cleaned_data['surname']
            from_email = form.cleaned_data['from_email']
            newsletter = form.cleaned_data['newsletter']

            if newsletter:
                Subscriber.objects.subscribe(name, from_email)

            message = render_to_string('emails/%s/contact_notify.html' % settings.LANGUAGE_CODE, {
                'nome': name,
                'sobrenome': surname,
                'email': from_email,
                'mensagem': form.cleaned_data['message']})

            send_email(
                subject=_('Contact Form'),
                message=message,
                to=settings.EMAIL_CIVIS,
                reply_to=[from_email]
            )
            return render(request, 'success.html',
                          {'title': _('Success!'),
                           'message': _('Thanks for you contact')})
    return render(request, "contact.html", {'form': form})


def subscribeView(request):
    if request.method == 'GET':
        if settings.NEWSLETTER_TYPE == 'Mailchimp':
            return render(request, 'subscribe_mailchimp.html')
        else:
            form = SubscribeForm()
    else:
        form = SubscribeForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            organisation = form.cleaned_data['organisation']
            subscriber, created = Subscriber.objects.get_or_create(email=email,
                                                                   defaults={'name': name})
            if subscriber.name == subscriber.email:
                subscriber.name = name
            if not subscriber.organisation:
                subscriber.organisation = organisation
            subscriber.save()
            if created:
                log_message(Subscriber, _('Subscription created from site'))
            else:
                log_message(Subscriber, _('Subscription updated from site'))

            if subscriber.valid:
                return render(request, 'success.html',
                              {'title': _('Subscription done'),
                               'message': _('Thank you for your interest in subscribing to our newsletter.')})
            else:
                domain = settings.DOMAIN
                template = 'emails/%s/confirm_email.html' % settings.LANGUAGE_CODE
                message = render_to_string(template, {
                    'nome': name,
                    'email': email,
                    'link': f'{domain}/confirm_email/{subscriber.secret()}/{subscriber.id}'})

                send_email(
                    subject=_('Confirm your Email'),
                    message=message,
                    to=[email],
                )
                return render(request, 'success.html', {
                    'title': _("Thank you for subscribing to our newsletter"),
                    'message': _("Please check your mailbox."
                                 "You are going to receive an email to certify that your email is valid.")
                })

    return render(request, "subscribe.html", {'form': form})


def confirm_email(request, token, id):
    try:
        subscriber = Subscriber.objects.get(pk=id)
        if subscriber.secret() == token:
            subscriber.valid = True
            subscriber.save()
            log_message(subscriber, _('Email confirmed'))
            return render(request, 'success.html',
                          {'title': _('Confirmation Done!'), 'message': _('Thanks for confirming your email')})
    except (TypeError, ValueError, OverflowError, Subscriber.DoesNotExist):
        subscriber = None

    return render(request, 'accounts/confirm-error.html', {})


def unsubscribe(request, token, id):
    try:
        subscriber = Subscriber.objects.get(pk=id)
        if subscriber.secret() == token:
            subscriber.opt_out = True
            subscriber.save()
            log_message(subscriber, 'Opt-out')
            return render(request, 'success.html',
                          {'title': _('Email %s has been unsubscribed' % subscriber.email),
                           'message': _('We hope you come back soon.')})
    except Subscriber.DoesNotExist:
        subscriber = None

    return render(request, 'accounts/confirm-error.html', {})


@login_required
def test_newsletter(request, pk):
    subscriber = get_object_or_404(Subscriber, id=pk)
    # Get last newsletter
    newsletter = Newsletter.objects.all().last()
    if newsletter:
        newsletter.send(subscriber)
        messages.success(request, _('Newsletter %s successfully sent') % newsletter.title)
    else:
        messages.error(request, _('No Newsletter found'))
    return redirect(f'/admin/contact/subscriber/{pk}/change')


@staff_member_required
def render_newsletter(request, pk):
    newsletter = get_object_or_404(Newsletter, id=pk)
    newsletter.render()
    return redirect(f'/admin/contact/newsletter/{pk}/change')


def newsletter(request, pk):
    obj = get_object_or_404(Newsletter, id=pk)
    context = Context({'invisible': 'style = "display: none;"'})
    t = Template(obj.html)
    texto = t.render(context)
    return HttpResponse(texto)


class NewsletterList(generic.ListView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query_params = self.request.GET.copy()
        query_params.pop('page', None)
        context['query_params'] = urlencode(query_params)
        return context

    queryset = Newsletter.objects. \
        filter(status__in=(Newsletter.QUEUED, Newsletter.SENT)).order_by('-dateCreated')
    template_name = 'newsletters.html'
    paginate_by = '12'


def countView(request, pk):
    obj = Newsletter.objects.get(id=pk)
    obj.read_count += 1
    obj.save()
    return FileResponse('/static/site/newsletter/Logo_Civis.png')


def submitterContactView(request, group, pk):
    referenceURL = settings.DOMAIN + '/' + group + '/' + str(pk)
    if request.method == 'GET':
        form = SubmitterContactForm()
    else:
        form = SubmitterContactForm(request.POST)
        if form.is_valid():
            subject = form.cleaned_data['subject']
            if group == "project":
                project = get_object_or_404(Project, id=pk)
                to_email = project.creator.email
            elif group == "resource":
                resource = get_object_or_404(Resource, id=pk)
                to_email = resource.creator.email
            else:
                event = get_object_or_404(Event, id=pk)
                to_email = event.creator.email
            message = form.cleaned_data['message']
            try:
                send_email(subject, message, [to_email])
            except BadHeaderError:
                return HttpResponse('Invalid header found.')
            return redirect('success')
    return render(request, "submitter_contact.html", {'form': form, 'referenceURL': referenceURL})


@staff_member_required(login_url='/login')
def import_csv(request):
    if request.method == 'GET':
        form = ImportForm()
    else:
        form = ImportForm(request.POST, request.FILES)
        if form.is_valid():
            texto = form.cleaned_data['file']
            source_name = form.cleaned_data['source']
            arquivo = TextIOWrapper(texto, encoding='utf-8')
            counter = 0
            errors = 0
            line_no = 1
            error_list = []
            # Recognizes just email as required. Name and Organisation are optional
            for csv_record in csv.reader(arquivo, delimiter=','):
                try:
                    email = csv_record[0].split(';')[0].strip()
                    validate_email(email)

                    if len(csv_record) > 1:
                        name = csv_record[1].strip()
                    else:
                        name = email

                    subscriber, created = Subscriber.objects.get_or_create(
                        email=email,
                        defaults={'name': name, 'valid': True})
                    if subscriber.email == subscriber.name and len(csv_record) > 1:
                        subscriber.name = csv_record[1]
                    if len(csv_record) > 2:
                        subscriber.organisation = csv_record[2].strip()
                    subscriber.save()
                    if created:
                        counter += 1
                        log_message(subscriber, _('Added by CSV named %s') % source_name, request.user)
                    line_no += 1
                except Exception as e:
                    errors += 1
                    error_list.append('Line %d: %s' % (line_no, e))
                    if errors > 10:
                        break

            if errors > 0:
                return render(request, 'contact/error_log.html',
                              {'title': _('Errors during import'),
                               'error_list': error_list})

            if counter > 0:
                messages.info(request, _('%d lines read') % line_no)
                messages.info(request, _('%d subscribers added') % counter)
                return redirect('/admin/contact/subscriber/')

    return render(request, "import_csv.html", {'form': form})


def load_image(request, image_name):
    """Saves newsletter's statistics. image_name should be in pattern pixel-newsletter_id-subscriber_id.png"""
    pattern = r'pixel-(\d+)-(\d+)\.png'

    match = re.search(pattern, image_name)

    if match:
        newsletter_id = match.group(1)
        subscriber_id = match.group(2)

        newsletter_obj = Newsletter.objects.only('title', 'read_count').get(pk=newsletter_id)
        subscriber = Subscriber.objects.only('pk', 'name').get(pk=subscriber_id)

        newsletter_obj.read_count = F('read_count') + 1
        newsletter_obj.save()

        log_message(subscriber, _('Opened newsletter %s email') % newsletter_obj)

    image = Image.new('RGB', (1, 1))
    response = HttpResponse(content_type="image/png")
    image.save(response, "PNG")

    return response


class NewForumProposal(CreateView, LoginRequiredMixin):
    form_class = ForumProposalForm
    template_name = 'forum_proposal.html'

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.creator = self.request.user
        self.object.save()
        # Save forum proposal and send notification
        messages.success(self.request, _('Forum Proposal added correctly'))
        # Subject and notification message must be sent based on settings.LANGUAGE_CODE
        with translation.override(settings.LANGUAGE_CODE):
            subject = _('Notification - New Forum Proposal "%s" submitted') % self.object.name
        # Templates must be a list, to raise exception if template for LANGUAGE_CODE does not exist.
        templates = ['emails/%s/notify_forumproposal.html' % settings.LANGUAGE_CODE]
        change_url = reverse('admin:contact_forumproposal_change', args=(self.object.pk,))
        message = render_to_string(templates, {
            'forumproposal': self.object.name,
            'forumproposal_url': f'{settings.DOMAIN}{change_url}'
        })

        send_email(subject=subject, message=message, reply_to=[self.request.user.email], to=settings.EMAIL_CIVIS)

        return redirect('forum:index')
