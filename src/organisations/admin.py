from django import forms
from django.contrib import admin
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from ckeditor.widgets import CKEditorWidget

from .models import Organisation, OrganisationType

from utilities.admin import TranslationInline


class OrgAdminForm(forms.ModelForm):
    description = forms.CharField(
        help_text=_('Please briefly describe the organisation (max 500 words).'),
        widget=CKEditorWidget(config_name='frontpage'),
        label=_('Description'),
        max_length=3000)

    class Meta:
        model = Organisation
        fields = '__all__' # Inclui todos os campos do modelo no formulário

    # Injetamos o CSS diretamente através da classe Media do Formulário
    class Media:
        js = (
            # Criamos um "truque" injetando o CSS via JavaScript para garantir
            # que ele seja o ÚLTIMO a carregar na página, vencendo o Select2.
            mark_safe(
                'data:text/javascript,'
                'const style = document.createElement("style");'
                'style.innerHTML = `'
                '  .related-widget-wrapper .select2-container--admin-autocomplete { '
                '     width: 100% !important; '
                '     max-width: 100% !important; '
                '  }'
                '  .select2-container--admin-autocomplete .select2-selection--multiple { '
                '     min-height: 100px !important; '
                '  }'
                '`;'
                'document.head.appendChild(style);'
            ),
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['orgType'].queryset = OrganisationType.objects.translated_sorted_by_text()


@admin.register(Organisation)
class OrganisationAdmin(admin.ModelAdmin):
    list_display = ('name', 'orgType', 'approved', 'dateCreated', 'safe_url')
    list_filter = ('orgType', 'approved')
    ordering = ('-name',)
    exclude = ('location',)
    readonly_fields = ('dateCreated', 'dateUpdated', 'logo')
    autocomplete_fields = ('diseases',)
    search_fields = ('name',)
    form = OrgAdminForm

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['approved'].widget.choices[0] = ('unknown', _('Not moderated'))
        return form


@admin.register(OrganisationType)
class OrganisationTypeAdmin(admin.ModelAdmin):
    inlines = (TranslationInline,)
