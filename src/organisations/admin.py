from django.contrib import admin
from .models import Organisation, OrganisationType
from django.utils.translation import ugettext_lazy as _

from utilities.admin import TranslationInline


@admin.register(Organisation)
class OrganisationAdmin(admin.ModelAdmin):
    list_display = ('name', 'orgType', 'approved', 'country', 'dateCreated', 'dateUpdated', 'safe_url')
    list_filter = ('orgType', 'approved')
    ordering = ('-name',)
    exclude = ('location',)
    readonly_fields = ('dateCreated', 'dateUpdated', 'logo')
    search_fields = ('name',)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['approved'].widget.choices[0] = ('unknown', _('Not moderated'))
        return form


@admin.register(OrganisationType)
class OrganisationTypeAdmin(admin.ModelAdmin):
    inlines = (TranslationInline,)
