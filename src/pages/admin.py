from ckeditor.widgets import CKEditorWidget
from django.contrib import admin
from django.db import models

from .models import Page, Section, Article


class BaseInline(admin.StackedInline):
    extra = 0
    fields = (('title', 'order'), ('header', 'content'))
    formfield_overrides = {
        models.TextField: {'widget': CKEditorWidget(config_name='admin')},
    }


class SectionInline(BaseInline):
    model = Section
    show_change_link = True


class ArticleInline(BaseInline):
    model = Article


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'language')
    fields = ('explain', ('title', 'slug', 'language'), ('header', 'content'), 'image')
    search_fields = ['title']
    formfield_overrides = {
        models.TextField: {'widget': CKEditorWidget(config_name='admin')},
    }
    inlines = [SectionInline]


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ('page', 'title', 'order', 'language')
    fields = (('page', 'title', 'order', 'language'), ('header', 'content'))
    list_select_related = ['page']
    search_fields = ['title']
    formfield_overrides = {
        models.TextField: {'widget': CKEditorWidget(config_name='admin')},
    }
    inlines = [ArticleInline]
    autocomplete_fields = ['page']
    ordering = ['page', 'language', 'order']

    def get_readonly_fields(self, request, obj=None):
        if obj is not None and obj.page_id:
            return ['language']

        return super().get_readonly_fields(request, obj)


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('section', 'title', 'order', 'language')
    fields = (('section', 'title', 'order', 'language'), 'header', 'content')
    list_select_related = ['section']
    search_fields = ['title']
    formfield_overrides = {
        models.TextField: {'widget': CKEditorWidget(config_name='admin')},
    }
    autocomplete_fields = ['section']
    ordering = ['section', 'language', 'order']

    def get_readonly_fields(self, request, obj=None):
        if obj is not None and obj.section_id:
            return ['language']

        return super().get_readonly_fields(request, obj)
