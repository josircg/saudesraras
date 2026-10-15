import os
from django.core.files.storage import FileSystemStorage
from django.utils.translation import get_language
from django.views.generic import DetailView, ListView, CreateView
from django.urls import reverse_lazy

from .models import Page, Section
from .forms_depoimentos import DepoimentoForm


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
        current_language = get_language()
        return Section.objects.filter(
            page__slug='depoimentos',
            language=current_language
        ).order_by('order')
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_language = get_language()
        
        try:
            context['page'] = Page.objects.get(slug='depoimentos', language=current_language)
        except Page.DoesNotExist:
            context['page'] = None
            
        return context

class DepoimentoCreateView(CreateView):
    model = Section
    form_class = DepoimentoForm
    template_name = 'pages/novo_depoimento.html'
    success_url = reverse_lazy('depoimentos')

    def form_valid(self, form):
        current_language = get_language()
        
        # 1. Procura a Page 'depoimentos'
        try:
            page = Page.objects.get(slug='depoimentos', language=current_language)
        except Page.DoesNotExist:
            page = Page.objects.filter(slug='depoimentos').first()

        # 2. Preenche os campos obrigatórios da Section
        form.instance.page = page
        form.instance.language = page.language if page else current_language
        form.instance.visible = True

        if not form.instance.order:
            form.instance.order = 1

        # 3. Processa a foto de perfil se tiver sido enviada
        profile_image = form.cleaned_data.get('profile_image')
        if profile_image:
            fs = FileSystemStorage()
            filename = fs.save(f'depoimentos/{profile_image.name}', profile_image)
            image_url = fs.url(filename)

            # Injeta a tag <img ...> visível com uma largura limite para o editor
            img_tag = f'<p><img src="{image_url}" alt="{form.instance.title}" width="120" /></p>'
            
            current_header = form.instance.header or ''
            form.instance.header = f'{img_tag}\n{current_header}'

        return super().form_valid(form)

    def form_invalid(self, form):
        # Imprime os erros no terminal para depuração rápida
        print("ERROS DO FORMULÁRIO DEPOIMENTOS:", form.errors)
        return super().form_invalid(form)