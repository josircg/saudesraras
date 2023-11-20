from django.contrib import admin, messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import path
from django.utils.translation import ugettext as _
from utilities.admin import TranslationInline

from .models import ResourcesGrouped, TrainingResource, Resource, Theme, Audience, Keyword, Category, ResourceGroup


class ResourceGroupInline(admin.TabularInline):
    model = ResourcesGrouped


class ResourceGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    inlines = [ResourceGroupInline, ]


class CategoryAdmin(admin.ModelAdmin):
    list_filter = ('text', 'parent',)
    ordering = ('text',)
    inlines = (TranslationInline,)


class ResourceAdminBase(admin.ModelAdmin):
    search_fields = ('name',)
    list_display = ('name', 'category', 'dateCreated', 'dateUpdated', 'approved', 'safe_url')
    list_filter = ('approved',)
    exclude = ('isTrainingResource',)
    readonly_fields = ('image1', 'image2')
    migrate_to_cls = None

    def migrate_resource(self, request, object_id):
        """Change Resource to Training Resource and Training Resource to Resource"""
        # Use self.migrate_to_cls to log change in the right admin class
        obj = get_object_or_404(self.migrate_to_cls, pk=object_id)
        obj.isTrainingResource = not obj.isTrainingResource
        obj.save()
        # Save log on migrated model
        self.log_change(request, obj, _('Field isTrainingResource changed'))

        self.message_user(request, _(f'"{obj}" was changed successfully'), messages.SUCCESS)

        if obj.isTrainingResource:
            redirect_to = 'admin:resources_trainingresource_change'
        else:
            redirect_to = 'admin:resources_resource_change'

        return redirect(redirect_to, object_id)

    def get_urls(self):
        urls = super().get_urls()

        info = self.model._meta.app_label, self.model._meta.model_name

        my_urls = [
            path('migrate_resource/<int:object_id>', self.admin_site.admin_view(self.migrate_resource),
                 name='{0}_{1}_migrate_resource'.format(*info)),
        ]
        return my_urls + urls

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['approved'].widget.choices[0] = ('unknown', _('Not moderated'))
        return form


class ResourceAdmin(ResourceAdminBase):
    migrate_to_cls = TrainingResource

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.resources()


class TrainingResourceAdmin(ResourceAdminBase):
    migrate_to_cls = Resource

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.training_resources()


@admin.register(Theme)
class ThemeAdmin(admin.ModelAdmin):
    inlines = (TranslationInline,)


@admin.register(Audience)
class AudienceAdmin(admin.ModelAdmin):
    inlines = (TranslationInline,)


admin.site.register(Keyword)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Resource, ResourceAdmin)
admin.site.register(TrainingResource, TrainingResourceAdmin)
admin.site.register(ResourceGroup, ResourceGroupAdmin)
