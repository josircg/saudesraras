from django.conf import settings
from django.core.files.storage import default_storage
from django.db import models
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

STATUS = (
    (0, _("Draft")),
    (1, _("Published"))
)
STICKY = (
    (0, _("No")),
    (1, _("Yes"))
)


class Post(models.Model):
    title = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True)
    author = models.ForeignKey(
            settings.AUTH_USER_MODEL,
            on_delete=models.CASCADE,
            related_name='blog_posts')
    updated_on = models.DateTimeField(auto_now=True)
    content = models.TextField()
    excerpt = models.TextField(max_length=1000, default="")
    image = models.ImageField(max_length=200)
    created_on = models.DateTimeField()
    sticky = models.IntegerField(choices=STICKY, default=0)
    status = models.IntegerField(choices=STATUS, default=0)

    class Meta:
        ordering = ['-created_on']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse(
                'post_detail', args=[
                    self.created_on.year,
                    self.created_on.strftime('%m'),
                    self.created_on.strftime('%d'),
                    self.slug])

    @property
    def safe_image(self):
        if self.image and default_storage.exists(self.image.path):
            return self.image
        else:
            return 'void_600.png'
