# Custom models should be declared before importing
# django-machina models
from machina.apps.forum_member.abstract_models import AbstractForumProfile


class ForumProfile(AbstractForumProfile):

    def __str__(self):
        return self.user.get_username()


from machina.apps.forum_conversation.models import *  # noqa
