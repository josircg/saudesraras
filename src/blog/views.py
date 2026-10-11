from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from django.views import generic

from .models import Post

User = get_user_model()


class PostList(generic.ListView):
    template_name = 'blog.html'
    paginate_by = 12

    def get_queryset(self):
        queryset = Post.objects.filter(status=1)

        keywords = self.request.GET.get('keywords', '').strip()
        author_id = self.request.GET.get('author', '').strip()
        start_date = self.request.GET.get('start_date', '').strip()
        end_date = self.request.GET.get('end_date', '').strip()
        orderby = self.request.GET.get('orderby', '-created_on').strip()

        if keywords:
            queryset = queryset.filter(
                Q(title__icontains=keywords) |
                Q(excerpt__icontains=keywords) |
                Q(slug__icontains=keywords) |
                Q(content__icontains=keywords)
            )

        if author_id:
            queryset = queryset.filter(author_id=author_id)

        if start_date:
            queryset = queryset.filter(created_on__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_on__date__lte=end_date)

        ordering_map = {
            'title': ('-sticky', 'title'),
            '-title': ('-sticky', '-title'),
            'created_on': ('-sticky', 'created_on'),
            '-created_on': ('-sticky', '-created_on'),
        }
        ordering = ordering_map.get(orderby, ('-sticky', '-created_on'))

        return queryset.order_by(*ordering).select_related('author')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        query_params = self.request.GET.copy()
        query_params.pop('page', None)

        selected_author_id = self.request.GET.get('author', '').strip()
        author_name = ''
        if selected_author_id:
            author_obj = User.objects.filter(id=selected_author_id).first()
            if author_obj:
                author_name = getattr(author_obj, 'name', str(author_obj))

        all_authors = User.objects.filter(blog_posts__status=1).distinct().order_by('name')

        context['query_params'] = urlencode(query_params)
        context['site_name'] = settings.SITE_NAME
        context['all_authors'] = all_authors
        context['isSearchPage'] = True
        context['filters'] = {
            'isSearchPage': True,
            'keywords': self.request.GET.get('keywords', '').strip(),
            'author': selected_author_id,
            'author_name': author_name,
            'start_date': self.request.GET.get('start_date', '').strip(),
            'end_date': self.request.GET.get('end_date', '').strip(),
            'orderby': self.request.GET.get('orderby', '-created_on').strip(),
        }

        return context


def post_detail(request, year, month, day, slug):
    post = get_object_or_404(Post, slug=slug, status=1)
    return render(request, 'post_detail.html', {'post': post, 'domain': settings.HOST})