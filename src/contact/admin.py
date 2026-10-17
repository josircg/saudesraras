import copy
import mimetypes
import os
from io import BytesIO

from PIL import Image
from ckeditor.widgets import CKEditorWidget
from django.conf import settings
from django.contrib import admin
from django.contrib.admin.models import ADDITION
from django.contrib.auth.models import AnonymousUser
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import translation
from django.utils.translation import gettext as _
from eucs_platform import send_email
from eucs_platform.logger import log_message

from .models import Subscriber, Newsletter


class SubscriberAdmin(admin.ModelAdmin):
    list_filter = ('valid', 'opt_out')
    search_fields = ('name', 'email', 'organisation')
    list_display = ('name', 'email', 'valid', 'opt_out', 'organisation', 'dateCreated',)
    exclude = ('last_newsletter',)


class NewsletterAdmin(admin.ModelAdmin):
    list_display = ('title', 'dateCreated', 'status',)

    def get_view_on_site_url(self, obj=None):
        self.view_on_site = obj and obj.html
        return super().get_view_on_site_url(obj)


admin.site.register(Subscriber, SubscriberAdmin)
admin.site.register(Newsletter, NewsletterAdmin)
