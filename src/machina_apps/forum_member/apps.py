from machina.apps.forum_member.apps import ForumMemberAppConfig as BaseForumMemberAppConfig


class ForumMemberAppConfig(BaseForumMemberAppConfig):
    name = 'machina_apps.forum_member'
    default = True
