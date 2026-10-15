import os
import re
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.files.storage import FileSystemStorage
from django.utils.translation import get_language
from django.views.generic import DetailView, ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404

from .models import Page, Section, img_finder, iframe_finder
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
        
        try:
            page = Page.objects.get(slug='depoimentos', language=current_language)
        except Page.DoesNotExist:
            page = Page.objects.filter(slug='depoimentos').first()

        form.instance.page = page
        form.instance.language = page.language if page else current_language
        form.instance.visible = True
        if not form.instance.order:
            form.instance.order = 1

        fs = FileSystemStorage()

        # 1. Avatar / Foto de Perfil
        profile_image = form.cleaned_data.get('profile_image')
        avatar_html = ""
        if profile_image:
            filename = fs.save(f'depoimentos/{profile_image.name}', profile_image)
            avatar_url = fs.url(filename)
            avatar_html = f'<p><img src="{avatar_url}" alt="{form.instance.title}" width="120" /></p>\n'

        # 2. Vídeo do Google Drive (Inserido no HEADER para aparecer no Admin)
        video_url = form.cleaned_data.get('video_url')
        video_html = ""
        if video_url:
            embed_url = self.get_embed_url(video_url)
            if embed_url:
                video_html = (
                    f'<div class="ratio ratio-16x9 my-3">'
                    f'<iframe src="{embed_url}" title="Vídeo do depoimento" allow="autoplay" allowfullscreen style="border:0;"></iframe>'
                    f'</div>\n'
                )

        # 3. Imagens Extras (1 a 5)
        extra_images_html = ""
        for i in range(1, 6):
            img_file = form.cleaned_data.get(f'image_{i}')
            if img_file:
                filename = fs.save(f'depoimentos/{img_file.name}', img_file)
                img_url = fs.url(filename)
                extra_images_html += f'<p><img src="{img_url}" class="img-fluid rounded my-2" alt="Imagem {i}" /></p>\n'

        # Monta o header com: Avatar -> Vídeo do Drive -> Texto escrito -> Fotos extras
        current_header = form.instance.header or ''
        form.instance.header = f'{avatar_html}{video_html}{current_header}\n{extra_images_html}'

        return super().form_valid(form)

    def get_embed_url(self, url):
        if not url:
            return ""
        
        # Suporte exclusivo para Google Drive (converte /view, /edit, etc. para /preview)
        if 'drive.google.com' in url:
            drive_match = re.search(r'/d/([a-zA-Z0-9_-]+)', url)
            if drive_match:
                file_id = drive_match.group(1)
                return f"https://drive.google.com/file/d/{file_id}/preview"

        return ""





class DepoimentoUpdateView(UpdateView):
    model = Section
    form_class = DepoimentoForm
    template_name = 'pages/novo_depoimento.html'
    success_url = reverse_lazy('depoimentos')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_editing'] = True
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        self.original_header = kwargs['instance'].header or ''
        return kwargs

    def form_valid(self, form):
        fs = FileSystemStorage()
        original_header = self.original_header

        existing_images = img_finder.findall(original_header)
        existing_videos = iframe_finder.findall(original_header)

        old_avatar = existing_images[0] if existing_images else None
        old_gallery = existing_images[1:] if existing_images else []

        # 1. Avatar: excluir, substituir ou manter.
        profile_image = form.cleaned_data.get('profile_image')
        remove_avatar = form.cleaned_data.get('remove_profile_image')

        if remove_avatar:
            avatar_url = None
        elif profile_image:
            filename = fs.save(
                f'depoimentos/{profile_image.name}',
                profile_image
            )
            avatar_url = fs.url(filename)
        else:
            avatar_url = old_avatar

        avatar_html = ''
        if avatar_url:
            avatar_html = (
                f'<p><img src="{avatar_url}" '
                f'alt="{form.instance.title}" width="120"></p>\n'
            )

        # 2. Vídeo: mantém o existente se não houver novo link.
        video_url = form.cleaned_data.get('video_url')

        if video_url:
            embed_url = self.get_embed_url(video_url)
        else:
            embed_url = existing_videos[0] if existing_videos else ''

        video_html = ''
        if embed_url:
            video_html = (
                '<div class="ratio ratio-16x9 my-3">'
                f'<iframe src="{embed_url}" '
                'title="Vídeo do depoimento" '
                'allow="autoplay" allowfullscreen '
                'style="border:0;"></iframe></div>\n'
            )

        # 3. Fotos extras: excluir, substituir ou manter.
        gallery = list(old_gallery)

        for i in range(1, 6):
            position = i - 1

            remove_image = form.cleaned_data.get(f'remove_image_{i}')
            img_file = form.cleaned_data.get(f'image_{i}')

            # Excluir tem prioridade sobre substituir.
            if remove_image:
                if position < len(gallery):
                    gallery[position] = None
                continue

            if img_file:
                filename = fs.save(
                    f'depoimentos/{img_file.name}',
                    img_file
                )
                img_url = fs.url(filename)

                if position < len(gallery):
                    gallery[position] = img_url
                else:
                    gallery.append(img_url)

        # Retira as posições excluídas sem alterar a ordem restante.
        gallery = [url for url in gallery if url]

        # 4. Remonta o HTML da galeria.
        extra_images_html = ''

        for i, image_url in enumerate(gallery, start=1):
            extra_images_html += (
                f'<p><img src="{image_url}" '
                'class="img-fluid rounded my-2" '
                f'alt="Imagem {i}"></p>\n'
            )

        # 5. Salva o texto editável junto das mídias atualizadas.
        text_header = form.cleaned_data.get('header') or ''

        form.instance.header = (
            f'{avatar_html}{video_html}'
            f'{text_header}\n{extra_images_html}'
        )

        return super().form_valid(form)

    def get_embed_url(self, url):
        if not url:
            return ''

        if 'drive.google.com' in url:
            drive_match = re.search(r'/d/([a-zA-Z0-9_-]+)', url)

            if drive_match:
                file_id = drive_match.group(1)
                return (
                    f'https://drive.google.com/file/d/'
                    f'{file_id}/preview'
                )

        return ''
