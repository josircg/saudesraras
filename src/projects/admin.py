from django import forms
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from organisations.models import Organisation
from utilities.admin import TranslationInline

from .models import Project, Topic, Status, ParticipationTask, ProjectPermission, Keyword, FundingBody


class ProjectFormA(forms.ModelForm):
    class Meta:
        widgets = {
            'description': forms.Textarea(attrs={'rows': 10, 'cols': 100}),
            'description_citizen_science_aspects': forms.Textarea(attrs={'rows': 10, 'cols': 100}),
        }


class ProjectPermissionInLine(admin.TabularInline):
    model = ProjectPermission
    max_num = 0
    fields = ('user', 'project', 'accepted')
    readonly_fields = ('user', 'project', 'accepted')


class OrganisationInline(admin.TabularInline):
    model = Organisation.project_set.through
    extra = 0
    raw_id_fields = ('organisation',)


@admin.register(Project)
class ProjectA(admin.ModelAdmin):
    list_filter = ('status', 'approved')
    search_fields = ('creator__name', 'name',)
    list_display = ('name', 'creator', 'status', 'dateCreated', 'dateUpdated', 'approved', 'safe_url')
    fields = (
        'name', 'url', 'description', 'description_citizen_science_aspects', 'status', 'keywords',
        'topic', ('start_date', 'end_date'), 'participationTask', 'howToParticipate', 'equipment',
        ('latitude', 'longitude'), 'country', ('author', 'author_email', 'mainOrganisation'),
        ('fundingBody', 'fundingProgram'), ('image1', 'imageCredit1'), ('image2', 'imageCredit2'),
        ('image3', 'imageCredit3'), ('originDatabase', 'originURL', 'originUID'),
        'featured', 'host', 'doingAtHome', 'participatingInaContest',
        ('approved', 'creator', 'dateCreated', 'dateUpdated'),
    )
    form = ProjectFormA
    inlines = [OrganisationInline, ProjectPermissionInLine]
    list_select_related = ('creator',)
    raw_id_fields = ('creator',)
    autocomplete_fields = ('topic', 'keywords', 'participationTask', 'fundingBody')
    readonly_fields = ('dateCreated', 'dateUpdated', 'image1', 'image2', 'image3')

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['approved'].widget.choices[0] = ('unknown', _('Not moderated'))
        return form

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        if change and 'approved' in form.changed_data:
            self.log_change(request, obj, obj.get_approved_display())

    def has_delete_permission(self, request, obj=None):
        delete_permission = super().has_delete_permission(request, obj)

        if delete_permission:
            delete_permission = request.user.is_superuser

        return delete_permission


class ProjectInline(admin.TabularInline):
    """Inline class. Users can't add or delete (can_delete, extra and max_num configured)."""
    model = Project.topic.through
    fields = ('project_name',)
    readonly_fields = ('project_name',)
    extra = 0
    max_num = 0
    can_delete = False

    def project_name(self, instance):
        return instance.project.name

    project_name.short_description = _('Project')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('project')


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    search_fields = ('topic',)
    inlines = (ProjectInline, TranslationInline)


@admin.register(ParticipationTask)
class ParticipationTaskAdmin(admin.ModelAdmin):
    search_fields = ('participationTask',)
    inlines = (TranslationInline,)


@admin.register(Keyword)
class KeywordAdmin(admin.ModelAdmin):
    search_fields = ('keyword',)


@admin.register(FundingBody)
class FundingBodyAdmin(admin.ModelAdmin):
    search_fields = ('body',)


@admin.register(Status)
class StatusAdmin(admin.ModelAdmin):
    inlines = (TranslationInline,)
