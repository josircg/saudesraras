from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def param_replace(context, **kwargs):
    """
    Mantém todos os parâmetros atuais da URL e substitui apenas os
    informados (ex.: page, q_symptom, letter, etc.).
    """
    query = context["request"].GET.copy()

    for key, value in kwargs.items():
        query[key] = value

    for key in list(query.keys()):
        if query[key] == "":
            del query[key]

    return query.urlencode()