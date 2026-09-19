from django import forms
from django.contrib import admin
from django.contrib.admin.models import LogEntry  # <--- Importação que faltava aqui!

from authtools.models import User
from authtools.admin import UserAdmin as AuthtoolsUserAdmin
from guardian.shortcuts import assign_perm, remove_perm, get_objects_for_user
from guardian.admin import GuardedModelAdminMixin

from profiles.models import Profile
from pages.models import Page, Section, Article

from .models import ActivationTask

# 1. Inline do Profile
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False


# 2. Form customizado para o UserAdmin com Pages, Sections e Articles
class CustomUserChangeForm(forms.ModelForm):
    allowed_pages = forms.ModelMultipleChoiceField(
        queryset=Page.objects.all(),
        required=False,
        widget=admin.widgets.FilteredSelectMultiple("Páginas Permitidas", is_stacked=False),
        label="Permissões em Páginas"
    )
    allowed_sections = forms.ModelMultipleChoiceField(
        queryset=Section.objects.select_related('page').all(),
        required=False,
        widget=admin.widgets.FilteredSelectMultiple("Seções Permitidas", is_stacked=False),
        label="Permissões em Seções"
    )
    allowed_articles = forms.ModelMultipleChoiceField(
        queryset=Article.objects.select_related('section').all(),
        required=False,
        widget=admin.widgets.FilteredSelectMultiple("Artigos Permitidos", is_stacked=False),
        label="Permissões em Artigos"
    )

    class Meta:
        model = User
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # Carrega o que o usuário já tem de permissão
            self.fields['allowed_pages'].initial = get_objects_for_user(
                self.instance, 'pages.change_page', klass=Page
            )
            self.fields['allowed_sections'].initial = get_objects_for_user(
                self.instance, 'pages.change_section', klass=Section
            )
            self.fields['allowed_articles'].initial = get_objects_for_user(
                self.instance, 'pages.change_article', klass=Article
            )

    def save(self, commit=True):
        user = super().save(commit=commit)
        if user.pk:
            # Mapeamento para sincronizar permissões de cada model
            permissions_map = [
                ('allowed_pages', 'change_page', Page),
                ('allowed_sections', 'change_section', Section),
                ('allowed_articles', 'change_article', Article),
            ]

            for field_name, perm_name, model_cls in permissions_map:
                if field_name in self.cleaned_data:
                    selected_objs = set(self.cleaned_data[field_name])
                    current_objs = set(get_objects_for_user(user, f'pages.{perm_name}', klass=model_cls))

                    # Atribui novas permissões
                    for obj in selected_objs - current_objs:
                        assign_perm(perm_name, user, obj)

                    # Remove permissões desmarcadas
                    for obj in current_objs - selected_objs:
                        remove_perm(perm_name, user, obj)

        return user


# 3. Desregistra e Re-registra o User
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass


@admin.register(User)
class CustomUserAdmin(GuardedModelAdminMixin, AuthtoolsUserAdmin):
    form = CustomUserChangeForm
    inlines = [ProfileInline]

    # Organiza os seletores na tela do Admin em uma seção dedicada
    fieldsets = AuthtoolsUserAdmin.fieldsets + (
        ('Permissões de Objeto (Páginas, Seções e Artigos)', {
            'fields': ('allowed_pages', 'allowed_sections', 'allowed_articles'),
        }),
    )


# 4. Seus outros Admins intactos
@admin.register(ActivationTask)
class ActivationTaskAdmin(admin.ModelAdmin):
    list_filter = ('task_description', 'task_name', 'email')
    list_display = ('email', 'task_description')
    fields = ('email', 'task_description', 'task_module', 'task_name', 'task_kwargs')

    def get_readonly_fields(self, request, obj=None):
        return self.fields

    def has_add_permission(self, request):
        return False


@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    """List of LogEntry (only permission to view)"""
    list_filter = ('action_time', 'content_type', 'action_flag')
    list_display = ('action_time', 'user', 'content_type', 'action_flag', 'object_repr', '__str__')
    fields = ('action_time', 'user', 'content_type', 'object_id', 'object_repr', 'action_flag', '__str__')
    readonly_fields = ('action_time', 'user', 'content_type', 'object_id', 'object_repr', 'action_flag', '__str__')
    search_fields = ('object_repr', 'change_message', 'user__name')
    list_select_related = ('user', 'content_type')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False