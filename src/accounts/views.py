import six
from braces import views as bracesviews
from contact.models import Subscriber
from django.conf import settings
from django.contrib import auth
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth import views as authviews
from django.contrib.auth.tokens import default_token_generator
from django.shortcuts import redirect, get_object_or_404, resolve_url
from django.shortcuts import render
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.encoding import force_bytes, force_text
from django.utils.functional import lazy
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.translation import ugettext_lazy as _
from django.views import generic
from djoser import utils
from eucs_platform import send_email
from profiles.models import Profile
from templated_mail.mail import BaseEmailMessage

from . import forms
from .models import ActivationTask
from .tokens import account_activation_token

User = get_user_model()


def _safe_resolve_url(url):
    """
    Previously, resolve_url_lazy would fail if the url was a unicode object.
    See <https://github.com/fusionbox/django-authtools/issues/13> for more
    information.

    Thanks to GitHub user alanwj for pointing out the problem and providing
    this solution.
    """
    return six.text_type(resolve_url(url))


resolve_url_lazy = lazy(_safe_resolve_url, six.text_type)


class LoginView(bracesviews.AnonymousRequiredMixin, authviews.LoginView):
    template_name = "accounts/login.html"
    form_class = forms.LoginForm

    def form_valid(self, form):
        redirect = super().form_valid(form)
        remember_me = form.cleaned_data.get("remember_me")
        if remember_me is True:
            ONE_MONTH = 30 * 24 * 60 * 60
            expiry = getattr(settings, "KEEP_LOGGED_DURATION", ONE_MONTH)
            self.request.session.set_expiry(expiry)
        return redirect


class LogoutView(authviews.LogoutView):
    next_page = reverse_lazy("home")


class SignUpView(
    bracesviews.AnonymousRequiredMixin,
    bracesviews.FormValidMessageMixin,
    generic.CreateView,
):
    form_class = forms.SignupForm
    model = User
    template_name = "accounts/signup.html"
    success_url = reverse_lazy("home")
    form_valid_message = "Você foi cadastrado(a)!"

    def form_valid(self, form):
        super().form_valid(form)
        user = form.save(commit=False)
        user.is_active = False
        user.save()
        orcid = form.cleaned_data.get('orcid')
        newsletter = form.cleaned_data.get('newsletter')
        profile = get_object_or_404(Profile, user_id=user.id)
        profile.orcid = orcid
        profile.save()

        if newsletter:
            Subscriber.objects.subscribe(form.cleaned_data['name'], form.cleaned_data['email'], valid=True)

        html_message = render_to_string('accounts/acc_active_email.html', {
            'user': user,
            'domain': settings.DOMAIN,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': account_activation_token.make_token(user),
        })

        notify_message = render_to_string('accounts/emails/notify_new_user.html', {
            'user': user,
            'domain': settings.DOMAIN,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': account_activation_token.make_token(user),
        })

        to_email = form.cleaned_data.get('email')
        send_email(subject='Ative sua conta!', to=[to_email],
                   message=html_message)

        send_email(subject='Cadastro de novo usuário', to=['civis@apps.ibict.br'],
                   message=notify_message)

        return render(self.request, 'accounts/confirm-email.html', {})


class PasswordChangeView(authviews.PasswordChangeView):
    form_class = forms.PasswordChangeForm
    template_name = "accounts/password-change.html"
    success_url = reverse_lazy("accounts:logout")

    def form_valid(self, form):
        form.save()
        messages.success(
            self.request,
            "Sua senha foi alterada, portanto, você foi desconectado(a). Por favor, faça login novamente.",
        )

        return super().form_valid(form)


class PasswordResetView(authviews.PasswordResetView):
    form_class = forms.PasswordResetForm
    template_name = "accounts/password-reset.html"
    success_url = reverse_lazy("accounts:password-reset-done")
    subject_template_name = "accounts/emails/password-reset-subject.txt"
    email_template_name = "accounts/emails/password-reset-email.html"
    tag = getattr(settings, 'EMAIL_TAG', 'XXX')
    extra_email_context = {'PASSWORD_RESET_TIMEOUT_HOURS': settings.PASSWORD_RESET_TIMEOUT_DAYS * 24,
                           'domain': settings.DOMAIN,
                           'tag': tag}


class PasswordResetDoneView(authviews.PasswordResetDoneView):
    template_name = "accounts/password-reset-done.html"


class PasswordResetConfirmAndLoginView(authviews.PasswordResetConfirmView):
    """View removed from django-authtools"""
    success_url = resolve_url_lazy(settings.LOGIN_REDIRECT_URL)

    def save_form(self, form):
        ret = super(PasswordResetConfirmAndLoginView, self).save_form(form)
        user = auth.authenticate(username=self.user.get_username(),
                                 password=form.cleaned_data['new_password1'])
        auth.login(self.request, user)
        return ret


class PasswordResetConfirmView(PasswordResetConfirmAndLoginView):
    template_name = "accounts/password-reset-confirm.html"
    form_class = forms.SetPasswordForm


def delete_user(request):
    try:
        u = User.objects.get(id=request.user.id)
        u.delete()
        messages.success(request, "The user has been deleted.")
    except User.DoesNotExist:
        messages.error = 'User does not exist.'
    except Exception:
        messages.error = 'There was a problem trying delete an user'

    return redirect('home')


def activate(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        send_email(
            subject=_('Welcome!'),
            message=render_to_string('accounts/welcome_email.html',
                                     {'user': user, "domain": settings.DOMAIN, }),
            to=[user.email])
        auth.login(request, user)

        try:
            # Execute a task after user activation
            task = ActivationTask.objects.get(email=user.email)
            # Task must be a function with request param
            response = task.execute_task(request=request)

            task.delete()

            if response is not None:
                return response
        except ActivationTask.DoesNotExist:
            pass

        return render(request, 'accounts/confirmation-account.html', {})
    else:
        return render(request, 'accounts/confirm-error.html', {})


class PasswordResetEmail(BaseEmailMessage):
    template_name = "accounts/emails/password-reset-email.html"

    def get_context_data(self):
        context = super().get_context_data()
        user = context.get("user")
        context["uid"] = utils.encode_uid(user.pk)
        context["token"] = default_token_generator.make_token(user)
        context["domain"] = settings.DOMAIN
        context["url"] = settings.PASSWORD_RESET_CONFIRM_URL.format(**context)
        return context


class ActivationEmail(BaseEmailMessage):
    template_name = "accounts/acc_active_email.html"

    def get_context_data(self):
        context = super().get_context_data()
        user = context.get("user")
        context["uid"] = utils.encode_uid(user.pk)
        context["token"] = account_activation_token.make_token(user)
        context["url"] = settings.ACTIVATION_URL.format(**context)
        context["domain"] = settings.DOMAIN
        return context


class ConfirmationEmail(BaseEmailMessage):
    template_name = "accounts/welcome_email.html"
