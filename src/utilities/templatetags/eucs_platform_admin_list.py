from django.conf import settings
from django.contrib.admin.templatetags.admin_list import result_list as rl
from django.contrib.admin.templatetags.base import InclusionAdminNode
from django.template import Library
from django.utils.formats import localize
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

register = Library()


def result_footer(cl):
    footer_result = getattr(cl, 'footer_result', {})

    if footer_result:
        for index, f in enumerate(cl.list_display):
            value = cl.footer_result.get(f, '')

            if index == 0 and value == '':
                value = _('TOTALS')
            else:
                if value is None:
                    value = cl.model_admin.get_empty_value_display()
                else:
                    value = localize(value, settings.USE_L10N)

            yield format_html('<th scope="row">{}</th>', value)


def result_list(cl):
    """Calls default result_list function and adds footer result"""
    context = rl(cl)

    context['footer_result'] = result_footer(cl)

    return context


@register.tag(name='eucs_result_list')
def result_list_tag(parser, token):
    return InclusionAdminNode(
        parser, token,
        func=result_list,
        template_name='change_list_results.html',
        takes_context=False,
    )
