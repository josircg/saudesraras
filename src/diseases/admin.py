from django.contrib import admin

from django.utils.translation import ugettext_lazy as _

from .models import Disease, Symptom


@admin.register(Symptom)
class SymptomAdmin(admin.ModelAdmin):
    search_fields = ['description',]
    list_display = ['description',]


@admin.register(Disease)
class DiseaseAdmin(admin.ModelAdmin):
    list_display = ('name', 'ICD', 'other_names')
    search_fields = ('name','ICD','other_names')
    autocomplete_fields = ('symptoms',)

# A propriedade Media injeta arquivos CSS ou JavaScript no Django Admin
    class Media:
        css = {
            # 'all' significa que o CSS será aplicado a todos os tipos de media (telas, impressões, etc.)
            'all': ('css/autocomplete.css',)
        }