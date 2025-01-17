from django.contrib import admin
from django.contrib.admin.views.main import ChangeList
from django.contrib.contenttypes.admin import GenericTabularInline

from .actions import export_as_csv_action
from .models import Translation


class TranslationInline(GenericTabularInline):
    model = Translation
    extra = 0


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
