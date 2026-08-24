from django.utils.translation import get_language, gettext as _
from django.views.generic import DetailView, ListView
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.db.models import Q  
from .models import Page, Section, Article
from .forms import SectionForm, PageForm, ArticleForm
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from urllib.parse import quote


class PageDetailView(DetailView):
    model = Page

    def get_template_names(self):
        return [
            f'pages/{self.object.slug}.html',
            'pages/page.html'
        ]

    def get_queryset(self):
        current_language = get_language()
        return Page.objects.filter(slug=self.kwargs['slug'], language=current_language)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        page_obj = self.object

        sections_list = Section.objects.filter(page=page_obj, visible=True).order_by('order')

        query = self.request.GET.get('q', '').strip()
        if query:
            # Varre apenas os campos preenchíveis de texto de SECTION e ARTICLE
            sections_list = sections_list.filter(
                # 1. Busca nos campos de texto da própria SECTION (SectionForm)
                Q(title__icontains=query) |
                Q(header__icontains=query) |
                Q(content__icontains=query) |
                
                # 2. Busca nos campos de texto dos ARTICLES desta seção (ArticleForm)
                Q(articles__title__icontains=query) |
                Q(articles__header__icontains=query) |
                Q(articles__content__icontains=query)
            ).distinct() 
        context['item_count'] = sections_list.count()

        for section in sections_list:
            articles_queryset = section.articles.all().order_by('order', 'id')
            
            if query:
                articles_queryset = articles_queryset.filter(
                    Q(title__icontains=query) |
                    Q(header__icontains=query) |
                    Q(content__icontains=query)
                )
            
            section.top_articles = articles_queryset[:4]

        context['sections'] = sections_list
        context['filters'] = {'q': query}
        
        return context


def section_detail(request, page_slug, section_id):
    current_lang = get_language()
    
    page_mae = get_object_or_404(Page, slug=page_slug, language=current_lang)
    section = get_object_or_404(Section, id=section_id, page=page_mae, visible=True)
    
    articles_list = section.articles.all().order_by('order', 'id')
    
    page_number = request.GET.get('page', 1)
    paginator = Paginator(articles_list, 15)
    
    try:
        articles_paginated = paginator.page(page_number)
    except PageNotAnInteger:
        articles_paginated = paginator.page(1)
    except EmptyPage:
        articles_paginated = paginator.page(paginator.num_pages)
        
    context = {
        'page_mae': page_mae,
        'section': section,
        'articles_paginated': articles_paginated, 
    }
    
    return render(request, 'pages/section.html', context)


def article_detail(request, page_slug, section_id, article_id):
    current_lang = get_language()
    
    page_mae = get_object_or_404(Page, slug=page_slug, language=current_lang)
    section = get_object_or_404(Section, id=section_id, page=page_mae, visible=True)
    article = get_object_or_404(Article, id=article_id, section=section)
    
    context = {
        'page_mae': page_mae,
        'section': section,
        'article': article
    }
    
    return render(request, 'pages/article.html', context)

def render_no_permission(request, message, item_type="", item_title="", perm_needed=""):
    subject = quote(_("Solicitação de Acesso - Painel"))
    
    if item_title:
        body_text = _("Olá, gostaria de solicitar permissão para editar %(item_type)s '%(item_title)s' ou permissão geral de editar %(perm_needed)s.") % {
            'item_type': item_type,
            'item_title': item_title,
            'perm_needed': perm_needed
        }
    else:
        body_text = _("Olá, gostaria de solicitar permissão geral para editar %(perm_needed)s.") % {
            'perm_needed': perm_needed
        }
        
    body = quote(body_text)
    mailto_link = f"mailto:saudesraras@gmail.com?subject={subject}&body={body}"

    return render(request, 'pages/no_permission.html', {
        'exception': message,
        'mailto_link': mailto_link
    }, status=403)


@login_required(login_url='/login')
def edit_page_generic(request, page_slug):
    current_lang = get_language()
    page_obj = get_object_or_404(Page, slug=page_slug, language=current_lang)

    # Checa permissão global OU se tem permissão nesta página específica
    if not (request.user.is_superuser or 
            request.user.has_perm('pages.change_page') or 
            request.user.has_perm('pages.change_page', page_obj)):
        return render_no_permission(
            request, 
            message=_('Você não tem permissão para editar esta página.'),
            item_type=_('a página'),
            item_title=getattr(page_obj, 'title', page_obj.slug),
            perm_needed='pages'
        )
    
    if request.method == 'POST':
        form = PageForm(request.POST, request.FILES, instance=page_obj)
        if form.is_valid():
            form.save()
            return redirect('page_detail', slug=page_slug)
    else:
        form = PageForm(instance=page_obj)
        
    return render(request, 'pages/page_form.html', {'form': form, 'page_obj': page_obj})


@login_required(login_url='/login')
def new_section_generic(request, page_slug):
    user = request.user
    current_lang = get_language()
    page_mae = get_object_or_404(Page, slug=page_slug, language=current_lang)

    # Pode criar seção se tiver acesso global OU se tiver acesso a esta página mãe
    if not (user.is_superuser or 
            user.has_perm('pages.change_page') or 
            user.has_perm('pages.change_section') or 
            user.has_perm('pages.change_page', page_mae)):
        return render_no_permission(
            request, 
            message=_('Você não tem permissão para criar seções.'),
            item_type=_('a página'),
            item_title=getattr(page_mae, 'title', page_mae.slug),
            perm_needed='sections'
        )

    if request.method == 'POST':
        form = SectionForm(request.POST)
        if form.is_valid():
            section = form.save(commit=False)
            section.page = page_mae
            section.save()
            return redirect('page_detail', slug=page_slug)
    else:
        form = SectionForm()

    return render(request, 'pages/section_form.html', {
        'form': form,
        'user': user,
        'page_mae': page_mae,
        'page_slug': page_slug
    })


@login_required(login_url='/login')
def edit_section_generic(request, page_slug, section_id):
    current_lang = get_language()
    page_mae = get_object_or_404(Page, slug=page_slug, language=current_lang)
    section = get_object_or_404(Section, id=section_id, page=page_mae)

    # Pode editar seção se tiver permissão global OU na página mãe OU na seção específica
    if not (request.user.is_superuser or 
            request.user.has_perm('pages.change_page') or 
            request.user.has_perm('pages.change_section') or 
            request.user.has_perm('pages.change_page', page_mae) or 
            request.user.has_perm('pages.change_section', section)):
        return render_no_permission(
            request, 
            message=_('Você não tem permissão para editar seções.'),
            item_type=_('a seção'),
            item_title=getattr(section, 'title', f'ID {section.id}'),
            perm_needed='sections'
        )
        
    if request.method == 'POST':
        form = SectionForm(request.POST, instance=section)
        if form.is_valid():
            updated_section = form.save(commit=False)
            updated_section.page = page_mae
            updated_section.save()
            return redirect('section_detail', page_slug=page_slug, section_id=section_id)
    else:
        form = SectionForm(instance=section)
        
    return render(request, 'pages/section_form.html', {
        'form': form, 
        'page_mae': page_mae, 
        'page_slug': page_slug
    })


@login_required(login_url='/login')
def new_article_generic(request, page_slug, section_id):
    user = request.user
    current_lang = get_language()
    page_mae = get_object_or_404(Page, slug=page_slug, language=current_lang)
    section = get_object_or_404(Section, id=section_id, page=page_mae)

    # Pode criar artigo se tiver acesso global OU na página mãe OU na seção pai
    if not (user.is_superuser or 
            user.has_perm('pages.change_page') or 
            user.has_perm('pages.change_section') or 
            user.has_perm('pages.change_article') or 
            user.has_perm('pages.change_page', page_mae) or 
            user.has_perm('pages.change_section', section)):
        return render_no_permission(
            request, 
            message=_('Você não tem permissão para criar artigos.'),
            item_type=_('a seção'),
            item_title=getattr(section, 'title', f'ID {section.id}'),
            perm_needed='articles'
        )

    if request.method == 'POST':
        form = ArticleForm(request.POST)
        if form.is_valid():
            article = form.save(commit=False)
            article.section = section  
            article.save()
            return redirect('section_detail', page_slug=page_slug, section_id=section_id)
    else:
        form = ArticleForm()

    return render(request, 'pages/article_form.html', {
        'form': form,
        'user': user,
        'page_slug': page_slug,
        'section_id': section_id,
        'section': section
    })


@login_required(login_url='/login')
def edit_article_generic(request, page_slug, section_id, article_id):
    current_lang = get_language()
    page_mae = get_object_or_404(Page, slug=page_slug, language=current_lang)
    section = get_object_or_404(Section, id=section_id, page=page_mae)
    article = get_object_or_404(Article, id=article_id, section=section)

    # Cascata completa: Permissão Global OU na Page Mãe OU na Section Pai OU no Article Específico
    if not (request.user.is_superuser or 
            request.user.has_perm('pages.change_page') or 
            request.user.has_perm('pages.change_section') or 
            request.user.has_perm('pages.change_article') or 
            request.user.has_perm('pages.change_page', page_mae) or 
            request.user.has_perm('pages.change_section', section) or 
            request.user.has_perm('pages.change_article', article)):
        return render_no_permission(
            request, 
            message=_('Você não tem permissão para editar artigos.'),
            item_type=_('o artigo'),
            item_title=getattr(article, 'title', f'ID {article.id}'),
            perm_needed='articles'
        )
        
    if request.method == 'POST':
        form = ArticleForm(request.POST, instance=article)
        if form.is_valid():
            updated_article = form.save(commit=False)
            updated_article.section = section
            updated_article.save()
            return redirect('section_detail', page_slug=page_slug, section_id=section_id)
    else:
        form = ArticleForm(instance=article)
        
    return render(request, 'pages/article_form.html', {
        'form': form, 
        'page_slug': page_slug,
        'section_id': section_id,
        'article': article
    })

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
