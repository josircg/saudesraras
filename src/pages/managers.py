from django.db import models


class SectionQuerySet(models.QuerySet):

    def sections_by_order(self):
        return self.order_by('order')


class ArticleQuerySet(models.QuerySet):

    def articles_by_order(self):
        return self.order_by('order')
