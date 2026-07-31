from django.utils.translation import get_language
from django.views.generic import DetailView, ListView
from django.core.paginator import Paginator

from .models import Page, Section


class PageDetailView(DetailView):

    def get_template_names(self):
        templates = [
            f'pages/{self.object.slug}.html',
        ]
        return templates

    def get_queryset(self):
        current_language = get_language()
        return Page.objects.filter(slug=self.kwargs['slug'], language=current_language)


class DepoimentosListView(ListView):
    model = Section
    template_name = 'pages/depoimentos.html'
    context_object_name = 'page_obj'
    paginate_by = 6 

    def get_queryset(self):
        return Section.objects.filter(page__slug='depoimentos').order_by('order')
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_language = get_language()
        
        try:
            context['page'] = Page.objects.get(slug='depoimentos', language=current_language)
        except Page.DoesNotExist:
            context['page'] = None
            
        return context
