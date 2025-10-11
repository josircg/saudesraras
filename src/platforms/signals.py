def add_search_index(sender, instance, created, **kwargs):
    from utilities.models import add_searchindex_text, SearchIndexType

    if instance.active:
        text = f'{instance.name} {instance.description}'

        for keyword in instance.keywords.values_list('keyword', flat=True):
            text += f' {keyword}'

        add_searchindex_text(SearchIndexType.PLATFORM.value, instance.pk, instance.name, text)
    else:
        delete_search_index(None, instance)


def delete_search_index(sender, instance, **kwargs):
    from utilities.models import delete_searchindex, SearchIndexType

    delete_searchindex(SearchIndexType.PLATFORM.value, instance.pk)
