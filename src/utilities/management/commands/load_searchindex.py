from django.apps import apps as django_apps
from django.core.management import BaseCommand


class Command(BaseCommand):
    label = 'Load SearchIndex table'

    def handle(self, *args, **options):
        self._load_class_into_search_index('projects.Project', update_fields=['dateUpdated', 'approved'])
        self._load_class_into_search_index('resources.Resource', update_fields=['dateUpdated', 'approved'])
        self._load_class_into_search_index('organisations.Organisation', update_fields=['dateUpdated', 'approved'])
        self._load_class_into_search_index('platforms.Platform', update_fields=['dateUpdated', 'active'])
        self._load_class_into_search_index('profiles.Profile')
        self._load_class_into_search_index('events.Event', update_fields=['approved'])

        print('Proccess Completed')

    def _load_class_into_search_index(self, class_name, update_fields=None):
        print(f'Loading {class_name}')
        cls = django_apps.get_model(class_name)
        # Call instance.save to trigger post_save and add_searchindex_text
        for obj in cls.objects.all():
            kwargs = {}

            if update_fields:
                # Stores the fields that should not be replaced when calling save.
                # Ex.: Date fields with auto_now option.
                for field in update_fields:
                    kwargs[field] = getattr(obj, field)
            obj.save()
            # Calls update to restore values
            cls.objects.filter(pk=obj.pk).update(**kwargs)
