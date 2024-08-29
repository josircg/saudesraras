"""
Django settings for eucs_platform project.

For more information on this file, see
https://docs.djangoproject.com/en/dev/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/dev/ref/settings/
"""
import os
from pathlib import Path

# Use 12factor inspired environment variables or from a file
import environ
# For Bootstrap 3, change error alert to 'danger'
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from machina import MACHINA_MAIN_TEMPLATE_DIR, MACHINA_MAIN_STATIC_DIR

# instalando o GDAL windows
if os.name == 'nt':
    import platform

    OSGEO4W = r"C:\OSGeo4W"
    if '64' in platform.architecture()[0]:
        OSGEO4W += "64"
    assert os.path.isdir(OSGEO4W), "Directory does not exist: " + OSGEO4W
    os.environ['OSGEO4W_ROOT'] = OSGEO4W
    os.environ['GDAL_DATA'] = OSGEO4W + r"\share\gdal"
    os.environ['PROJ_LIB'] = OSGEO4W + r"\share\proj"
    os.environ['PATH'] = OSGEO4W + r"\bin;" + os.environ['PATH']

# Build paths inside the project like this: BASE_DIR / "directory"
BASE_DIR = Path(__file__).resolve().parent.parent.parent
STATICFILES_DIRS = [str(BASE_DIR / "static"), MACHINA_MAIN_STATIC_DIR]
MEDIA_ROOT = str(BASE_DIR / "media")
MEDIA_URL = "/media/"
STATIC_ROOT = str(BASE_DIR.parent / "static")
THUMBNAIL_DEBUG = True

LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'locale'),
]

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    },
    'machina_attachments': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': '/tmp',
    },
    # … default cache config and others
    "select2": {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'select2-cache',
        'TIMEOUT': 7200,
        #   "BACKEND": "django_redis.cache.RedisCache",
        #   "LOCATION": "redis://127.0.0.1:6379/2",
        #   "OPTIONS": {
        #       "CLIENT_CLASS": "django_redis.client.DefaultClient",
        #   }
    }
}

# Tell select2 which cache configuration to use:
SELECT2_CACHE_BACKEND = "select2"

# Use Django templates using the new Django 1.8 TEMPLATES settings
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            str(BASE_DIR / "templates"),
            MACHINA_MAIN_TEMPLATE_DIR
            # insert more TEMPLATE_DIRS here
        ],
        "APP_DIRS": False,
        "OPTIONS": {
            "context_processors": [
                # Insert your TEMPLATE_CONTEXT_PROCESSORS here or use this
                # list if you haven't customized them:
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.debug",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.contrib.messages.context_processors.messages",
                'django.template.context_processors.request',
                # Machina
                'machina.core.context_processors.metadata',
                # Wwn
                'eucs_platform.context_processors.global_settings',

            ],
            'loaders': [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
                'admin_tools.template_loaders.Loader',
            ],
        },
    }
]

env = environ.Env(
    FEATURED_MGT=(bool, True),
    ADMIN_EMAIL=(str, ''),
    DEBUG=(bool, False),
    FORUM_ENABLED=(bool, False)
)

# Create a local.env file in the settings directory
# But ideally this env file should be outside the git repo
env_file = Path(__file__).resolve().parent / "local.env"
if env_file.exists():
    environ.Env.read_env(str(env_file))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/dev/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
# Raises ImproperlyConfigured exception if SECRET_KEY not in os.environ
SECRET_KEY = env("SECRET_KEY")

ALLOWED_HOSTS = []

ADMIN_EMAIL = env("ADMIN_EMAIL")

if ADMIN_EMAIL:
    ADMINS = [(email.split('@')[0], email) for email in ADMIN_EMAIL.split(',')]
    MANAGERS = ADMINS
# Application definition
INSTALLED_APPS = (
    "admin_tools",
    "admin_tools.dashboard",

    "django.contrib.auth",
    "django.contrib.admin",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    "authtools",
    "crispy_forms",
    "crispy_bootstrap3",
    "easy_thumbnails",
    "profiles",
    "accounts",
    "projects",
    "resources",
    "digest",
    "platforms",
    "django_select2",
    "blog",
    "django_summernote",
    "leaflet",
    "django_countries",
    "authors",
    "contact",
    "reviews",
    'django.contrib.sites',
    'cookielaw',
    'events',
    'rest_framework',
    'rest_framework.authtoken',
    'djoser',
    'rest_framework_swagger',
    'oidc_provider',
    'drf_yasg',
    'captcha',
    'active_link',
    'oauth2_provider',
    'django.contrib.gis',

    # Machina dependencies:
    'mptt',
    'haystack',
    'widget_tweaks',

    # Machina apps:
    'machina',
    'machina.apps.forum',
    'machina.apps.forum_conversation',
    'machina.apps.forum_conversation.forum_attachments',
    'machina.apps.forum_conversation.forum_polls',
    'machina.apps.forum_feeds',
    'machina.apps.forum_moderation',
    'machina.apps.forum_search',
    'machina.apps.forum_tracking',
    # 'machina.apps.forum_member',
    'machina.apps.forum_permission',
    # Machina overriden apps
    'machina_apps.forum_member',

    'organisations',
    "django_cron",
    'django_crontab',
    'ckeditor',
    'ckeditor_uploader',

    'django_cleanup.apps.CleanupConfig',

    'utilities',
)

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Machina
    'machina.apps.forum_permission.middleware.ForumPermissionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
]

ROOT_URLCONF = "eucs_platform.urls"

WSGI_APPLICATION = "eucs_platform.wsgi.application"

# Database
# https://docs.djangoproject.com/en/dev/ref/settings/#databases

DATABASES = {
    'default': {
        # 'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': env("DATABASE_NAME"),
        'USER': env("DATABASE_USER"),
        'PASSWORD': env("DATABASE_PASSWORD"),
        'HOST': env('DATABASE_HOST'),
        'PORT': '5432',
    }
}

# Internationalization
# https://docs.djangoproject.com/en/dev/topics/i18n/

LANGUAGE_CODE = "pt-br"

TRANSLATED_LANGUAGES = (
    ('pt-br', _('Brazilian Portuguese')),
    ('es', _('Spanish')),
    ('en', _('English')),
)

LANGUAGE_CODES = [
    'pt-br',
    'es',
    'en'
]

LANGUAGES = [
    ('pt-br', _('Brazilian Portuguese')),
    ('es', _('Spanish')),
    ('en', _('English')),
]

TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_L10N = True
USE_TZ = True
FORMAT_MODULE_PATH = 'formats'

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/dev/howto/static-files/

STATIC_URL = "/static/"

ALLOWED_HOSTS = ["*"]

# Crispy Form Theme - Bootstrap 3
CRISPY_TEMPLATE_PACK = "bootstrap3"

MESSAGE_TAGS = {
    messages.DEBUG: 'alert-secondary',
    messages.INFO: 'alert-info',
    messages.SUCCESS: 'alert-success',
    messages.WARNING: 'alert-warning',
    messages.ERROR: 'alert-danger',
}
# Authentication Settings
AUTH_USER_MODEL = "authtools.User"
LOGIN_REDIRECT_URL = reverse_lazy("home")
LOGIN_URL = reverse_lazy("accounts:login")

THUMBNAIL_EXTENSION = "png"  # Or any extn for your thumbnails

LEAFLET_CONFIG = {
    'DEFAULT_CENTER': (-15.125159, -57.636719),
    'DEFAULT_ZOOM': 3,
    'MIN_ZOOM': 2,
    'RESET_VIEW': False,
    'MAX_ZOOM': 18,
}

SUMMERNOTE_THEME = 'bs4'

SUMMERNOTE_CONFIG = {
    'iframe': True,
    'summernote': {
        'airMode': False,
        'width': '100%',
        'height': '300',
        'toolbar': ['bold', 'italic', 'underline'],
    },
}

# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env("HOST_EMAIL")
EMAIL_HOST_USER = env("FROM_EMAIL")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
EMAIL_PORT = '587'
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = env("FROM_EMAIL")
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# These are optional -- if they're set as environment variables they won't need to be set here as well
# AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID')
# AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY')
# Additionally, if you are not using the default AWS region of us-east-1,
# you need to specify a region, like so:
# EMAIL_BACKEND = 'django_ses.SESBackend'
# AWS_SES_REGION_NAME = env('AWS_SES_REGION_NAME')
# AWS_SES_REGION_ENDPOINT = env('AWS_SES_REGION_ENDPOINT')

SITE_NAME = 'Saúdes Raras'
EMAIL_RECIPIENT_LIST = ["josircg@gmail.com"]
EMAIL_CONTACT_RECIPIENT_LIST = ["josircg@gmail.com"]
EMAIL_CIVIS = ["laccops.gco.ega@id.uff.br"]
EMAIL_TAG = env("EMAIL_TAG")
HOST = env("HOST")
DOMAIN = env("DOMAIN")
USE_GUIDE = env("USE_GUIDE")

VISAO_USERNAME = env('VISAO_USERNAME')
VISAO_PASSWORD = env('VISAO_PASSWORD')
VISAO_GROUP = env('VISAO_GROUP')
VISAO_LAYER = env('VISAO_LAYER')
VISAO_URL = env('VISAO_URL')

# Debug Options
DEBUG = env('DEBUG')
ADMIN_EMAIL = env('ADMIN_EMAIL')
TEMPLATES[0]["OPTIONS"].update({"debug": DEBUG})

SITE_ID = 1
REVIEW_PUBLISH_UNMODERATED = True
NEWSLETTER_TYPE = 'Local'  # Accepts Local or Mailchimp

REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.coreapi.AutoSchema',
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication'
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'utilities.renderers.CSVRenderer',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    )
}

SWAGGER_SETTINGS = {
    'DEFAULT_AUTO_SCHEMA_CLASS': 'utilities.inspectors.SwaggerAutoSchema',
}

PASSWORD_RESET_CONFIRM_URL = '/password-reset/'
ACTIVATION_URL = '/activate/'
DJOSER = {
    'PASSWORD_RESET_CONFIRM_URL': '/password-reset/',
    'EMAIL': {
        'activation': 'accounts.views.ActivationEmail',
        'confirmation': 'accounts.views.ConfirmationEmail',
        'password_reset': 'accounts.views.PasswordResetEmail',
    },
    'SEND_ACTIVATION_EMAIL': True,
}

# OPENID
# LOGIN_URL = '/accounts/login/'
OIDC_SESSION_MANAGEMENT_ENABLE = True
OIDC_USERINFO = 'eucs_platform.oidc_provider_settings.userinfo'

# Swagger
LOGOUT_URL = 'rest_framework:logout'

RECAPTCHA_PUBLIC_KEY = env("RECAPTCHA_PUBLIC_KEY")
RECAPTCHA_PRIVATE_KEY = env("RECAPTCHA_PRIVATE_KEY")

# Machina - search for forum conversations
HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.whoosh_backend.WhooshEngine',
        'PATH': str(Path(__file__).parents[2] / 'whoosh_index'),
    },
}

HAYSTACK_SIGNAL_PROCESSOR = 'haystack.signals.RealtimeSignalProcessor'

MACHINA_BASE_TEMPLATE_NAME = 'base_forum_new.html'
MACHINA_FORUM_NAME = 'Community Forums'
MACHINA_USER_DISPLAY_NAME_METHOD = 'get_full_name'

MACHINA_DEFAULT_AUTHENTICATED_USER_FORUM_PERMISSIONS = [
    'can_see_forum',
    'can_read_forum',
    'can_start_new_topics',
    'can_reply_to_topics',
    'can_edit_own_posts',
    'can_post_without_approval',
    'can_create_polls',
    'can_vote_in_polls',
    'can_download_file',
]

MACHINA_MARKUP_LANGUAGE = None
MACHINA_MARKUP_WIDGET = 'ckeditor_uploader.widgets.CKEditorUploadingWidget'
MACHINA_PROFILE_AVATARS_ENABLED = False
ATTACHMENT_FILE_UPLOAD_TO = 'forum/atch'
MACHINA_FORUM_IMAGE_UPLOAD_TO = 'forum/img'
MACHINA_PROFILE_AVATAR_UPLOAD_TO = 'forum/avatar'

CKEDITOR_UPLOAD_PATH = "uploads/"
CKEDITOR_BASEPATH = "/static/ckeditor/ckeditor/"
CKEDITOR_REQUIRE_STAFF = False

CKEDITOR_CONFIGS = {
    'default': {
        'removePlugins': 'exportpdf',
        'toolbar': 'default_custom',
        'toolbar_default_custom': [
            {'name': 'basicstyles',
             'items': ['Bold', 'Italic', 'Underline', 'Strike', 'Subscript', 'Superscript', '-', 'RemoveFormat']},
            {'name': 'paragraph',
             'items': ['NumberedList', 'BulletedList', '-', 'Outdent', 'Indent', '-', 'Blockquote', 'CreateDiv', '-',
                       'JustifyLeft', 'JustifyCenter', 'JustifyRight', 'JustifyBlock', '-', 'BidiLtr', 'BidiRtl',
                       'Language']},
            {'name': 'links', 'items': ['Link', 'Unlink', 'Anchor']},
            {'name': 'insert', 'items': ['Image']},
            '/',
            {'name': 'styles', 'items': ['Styles', 'Format', 'FontSize']},
            {'name': 'colors', 'items': ['TextColor', 'BGColor']},
        ],
    },
    'frontpage': {
        'toolbar': 'Custom',
        'toolbar_Custom': [
            ['Bold', 'Italic', 'Underline'],
            ['NumberedList', 'BulletedList', '-', 'Outdent', 'Indent',
             '-', 'JustifyLeft', 'JustifyCenter', 'JustifyRight', 'JustifyBlock'],
            ['Link', 'Unlink'],
            ['RemoveFormat']
        ]
    },
}

CRON_CLASSES = [
    "eucs_platform.cron.ExpiredUsersCronJob",
    "eucs_platform.cron.NewForumResponseCronJob",
    "eucs_platform.cron.CleanExpiredCaptchaCronJob",
]

CRONJOBS = [
    ('0 1 * * *', 'eucs_platform.cron.ExpiredUsersCronJob'),
    ('0 * * * *', 'eucs_platform.cron.NewForumResponseCronJob'),
    ('30 0 * * *', 'eucs_platform.cron.CleanExpiredCaptchaCronJob')
]

FEATURED_MGT = env('FEATURED_MGT')
FORUM_ENABLED = env('FORUM_ENABLED')

# django-countries override. Diplomatic solition.
COUNTRIES_OVERRIDE = {
    "FK": _("Falkland Islands (Malvinas)"),
}

ADMIN_TOOLS_INDEX_DASHBOARD = 'eucs_platform.dashboard.CustomIndexDashboard'
ADMIN_TOOLS_APP_INDEX_DASHBOARD = 'eucs_platform.dashboard.CustomAppIndexDashboard'

# Machina migrations for overriden apps
MIGRATION_MODULES = {
    'forum_member': 'machina.apps.forum_member.migrations',
}

# geopy Nominatim user agent
USER_AGENT = env('USER_AGENT')

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"
