from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from projects.models import Project


class StaticViewSitemap(Sitemap):
    priority = 0.5
    changefreq = 'daily'

    def items(self):
        return ['home', 'about']

    def location(self, item):
        return reverse(item)


class ProjectSitemap(Sitemap):
    priority = 0.5
    changefreq = "daily"

    def location(self, obj):
        return obj.get_absolute_url()

    def lastmod(self, obj):
        return obj.dateUpdated

    def items(self):
        return Project.objects.filter(approved=True)


sitemaps = {
    'static': StaticViewSitemap,
    'projects': ProjectSitemap
}
