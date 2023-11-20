from django.core.mail import EmailMessage
from django.conf import settings as django_settings
from django.core.paginator import EmptyPage


def send_email(subject, message, to, reply_to=None, bcc=None, headers=None):
    tag = getattr(django_settings, 'EMAIL_TAG', 'XXX')
    if tag != 'DEV':
        email = EmailMessage('[%s] %s' % (tag, subject), message, to=to, reply_to=reply_to, bcc=bcc, headers=headers)
        email.content_subtype = "html"
        email.send()


def set_pages_and_get_object_list(paginator, pages, page_num):
    """Append a page object into page list and return object_list from actual page"""
    try:
        p_obj = paginator.page(page_num)
        object_list = p_obj.object_list
        pages.append(p_obj)
    except EmptyPage:
        object_list = []
    return object_list


def get_main_page(page_list):
    """Get page object with max pages to control pagination (multiple pagination)"""
    if page_list:
        page_obj = max(page_list, key=lambda item: item.paginator.num_pages)
    else:
        page_obj = None

    return page_obj
