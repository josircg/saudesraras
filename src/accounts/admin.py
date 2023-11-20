from django.contrib import admin
from django.contrib.admin.models import LogEntry

from .models import ActivationTask


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
