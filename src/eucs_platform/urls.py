import accounts.urls
import contact.urls
import digest.urls
import events.urls
import organisations.urls
import platforms.urls
import profiles.urls
import projects.urls
import resources.urls
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path, re_path
from django.views.defaults import server_error
from django.views.generic import TemplateView
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from machina import urls as machina_urls
from rest_framework import permissions

from . import sitemaps
from . import views

schema_view = get_schema_view(
    openapi.Info(
        title="CIVIS API",
        default_version='v1',
        description="CIVIS API",
    ),
    public=False,
    permission_classes=(permissions.IsAuthenticated,),
)

# Personalized admin site settings like title and header
admin.site.site_title = "Civis Administração"
admin.site.site_header = "Civis Administração"

urlpatterns = [
    path("", views.home, name="home"),
    path("country_list/", views.country_list, name="country_list"),
    path("all/", views.all, name="all"),
    path("curated/", views.curated, name="curated"),
    path("imprint/", views.imprint, name="imprint"),
    path("terms/", views.terms, name="terms"),
    path("privacy/", views.privacy, name="privacy"),
    path("guide/", views.guide, name="guide"),
    path("faq/", views.faq, name="faq"),
    path("moderation/", views.moderation, name="moderation"),
    path("criteria/", views.criteria, name="criteria"),
    path("moderation_quality_criteria", views.moderation_quality_criteria, name="moderation_quality_criteria"),
    path("translations/", views.translations, name="translations"),
    path("home_autocomplete/", views.home_autocomplete, name="home_autocomplete"),
    path("development/", views.development, name="development"),
    path("about/", views.about, name="about"),
    path("noticias/", views.noticias, name="noticias"),
    path("users/", include(profiles.urls)),
    path("admin/", admin.site.urls),
    path("admin_tools/", include('admin_tools.urls')),
    path("select2/", include("django_select2.urls")),
    path('captcha/', include('captcha.urls')),
    path("", include(contact.urls)),
    path("", include(accounts.urls)),
    path("", include(organisations.urls)),
    path("", include(projects.urls)),
    path("", include(resources.urls)),
    path('', include('blog.urls')),
    path("", include(events.urls)),
    path("", include(digest.urls)),
    path("", include(platforms.urls)),
    path('summernote/', include('django_summernote.urls')),
    path('forum/', include(machina_urls)),
    path('getTopicsResponded', views.getTopicsResponded, name='getTopicsResponded'),
    path('getForumResponsesNumber', views.getForumResponsesNumber, name='getForumResponsesNumber'),
    re_path(r'^i18n/', include('django.conf.urls.i18n')),
    re_path(r'^reviews/', include('reviews.urls')),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    re_path(r'^api/auth/', include('djoser.urls')),
    re_path(r'^api/auth/', include('djoser.urls.authtoken')),
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    re_path(r'^swagger/$', login_required(schema_view.with_ui('swagger', cache_timeout=0), login_url='/login'),
            name='schema-swagger-ui'),
    re_path(r'^redoc/$', login_required(schema_view.with_ui('redoc', cache_timeout=0), login_url='/login'),
            name='schema-redoc'),
    re_path(r'^openid/', include('oidc_provider.urls', namespace='oidc_provider')),
    path('ckeditor/', include('ckeditor_uploader.urls')),
    path('o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    path('500/', server_error),
    path('403/', TemplateView.as_view(template_name='403.html')),
    path('coming_soon/', TemplateView.as_view(template_name='coming_soon.html'), name='coming_soon'),
    # add the robots.txt file
    path("robots.txt", TemplateView.as_view(template_name="robots.txt", content_type="text/plain")),
    # sitemaps
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps.sitemaps}, name='django.contrib.sitemaps.views.sitemap')
]

# User-uploaded files like profile pics need to be served in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Include django debug toolbar if DEBUG is on
if settings.DEBUG:
    import debug_toolbar

    urlpatterns += [
        path("__debug__/", include(debug_toolbar.urls)),
    ]
