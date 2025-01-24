from django import forms
from django.conf import settings
from django.contrib import admin
from django.contrib.admin.views.main import ChangeList
from django.contrib.contenttypes.admin import GenericTabularInline
from django.contrib.contenttypes.forms import BaseGenericInlineFormSet
from django.utils.translation import gettext as _

from .actions import export_as_csv_action
from .models import Translation


class TranslationInlineFormset(BaseGenericInlineFormSet):

    def validate_unique(self):
        """Validates unique language. Form does not have content_type and object_id to do builtin unique validation."""
        forms_to_delete = self.deleted_forms
        valid_forms = [form for form in self.forms if form.is_valid() and form not in forms_to_delete]
        unique = []
        errors = []
        dct = dict(settings.TRANSLATED_LANGUAGES)

        for form in valid_forms:
            unique_data = form.cleaned_data.get('language', '')

            if unique_data:
                if unique_data in unique:
                    errors.append(
                        _('A translation for %s already exists for this object.') % dct.get(unique_data, '')
                    )
                else:
                    unique.append(unique_data)

        if errors:
            raise forms.ValidationError(errors)

        super().validate_unique()


class TranslationInline(GenericTabularInline):
    model = Translation
    extra = 0
    formset = TranslationInlineFormset


class EUCSChangeList(ChangeList):
    """ChangeList to compute results to add a table footer"""

    def get_results(self, request):
        super().get_results(request)
        # Compute total of each field listed on EUCSAdmin.list_totals
        # Only sum is available on this version
        totals = {v: 0 for v in self.model_admin.list_totals}

        for obj in self.result_list:
            for f in self.model_admin.list_totals:
                totals[f] += getattr(obj, f)

        self.footer_result = totals


class EUCSAdmin(admin.ModelAdmin):
    """ModelAdmin with export to csv action and list_totals change_list on table footer"""
    list_totals = []

    def get_actions(self, request):
        actions = super().get_actions(request)
        export_as_csv = export_as_csv_action(fields=self.get_list_display(request))
        actions['export_as_csv'] = (export_as_csv, 'export_as_csv', export_as_csv.short_description)

        return actions

    def get_changelist(self, request, **kwargs):
        return EUCSChangeList
