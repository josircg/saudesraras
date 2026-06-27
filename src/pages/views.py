from django.utils.translation import get_language
from django.views.generic import DetailView

from .models import Page


class PageDetailView(DetailView):

    def get_template_names(self):
        templates = [
            f'pages/{self.object.slug}.html',
        ]
        return templates

    def get_queryset(self):
        current_language = get_language()
        return Page.objects.filter(slug=self.kwargs['slug'], language=current_language)


