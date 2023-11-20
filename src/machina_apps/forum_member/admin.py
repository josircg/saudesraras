from django.contrib.auth import get_user_model
from machina.apps.forum_member.admin import ForumProfileAdmin as BaseForumProfileAdmin, admin

from .models import ForumProfile

USERNAME_FIELD = get_user_model().USERNAME_FIELD

admin.site.unregister(ForumProfile)


@admin.register(ForumProfile)
class ForumProfileAdmin(BaseForumProfileAdmin):
    search_fields = (f'user__{USERNAME_FIELD}',)
