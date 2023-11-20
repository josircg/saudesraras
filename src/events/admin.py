from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from .models import Event


class EventAdmin(admin.ModelAdmin):
    list_filter = ('approved',)
    search_fields = ('title',)
    list_display = ('title', 'start_date', 'hour', 'creator', 'approved', 'safe_url')
    ordering = ('-start_date',)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['approved'].widget.choices[0] = ('unknown', _('Not moderated'))
        return form


admin.site.register(Event, EventAdmin)
