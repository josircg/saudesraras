from django.utils.translation import get_language
from django.views.generic import DetailView
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.db.models import Q  
from .models import Page, Section, Article

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

@login_required(login_url='/login')
def edit_page_generic(request, page_slug):
    if not (request.user.has_perm('pages.change_page') or request.user.is_superuser):
        return HttpResponseForbidden()
        
    current_lang = get_language()
    page_obj = get_object_or_404(Page, slug=page_slug, language=current_lang)
    
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
    if not (request.user.has_perm('pages.change_page') or request.user.is_superuser):
        return HttpResponseForbidden()
        
    current_lang = get_language()
    page_mae = get_object_or_404(Page, slug=page_slug, language=current_lang)
    section = get_object_or_404(Section, id=section_id, page=page_mae)
    
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
    if not (request.user.has_perm('pages.change_page') or request.user.is_superuser):
        return HttpResponseForbidden()
        
    current_lang = get_language()
    page_mae = get_object_or_404(Page, slug=page_slug, language=current_lang)
    section = get_object_or_404(Section, id=section_id, page=page_mae)
    article = get_object_or_404(Article, id=article_id, section=section)
    
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