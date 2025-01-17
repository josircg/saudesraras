import csv

from django.conf import settings
from django.contrib.admin.utils import label_for_field, lookup_field, display_for_value, display_for_field
from django.db import models
from django.db.models.constants import LOOKUP_SEP
from django.http import HttpResponse
from django.utils.datetime_safe import datetime
from django.utils.formats import localize
from django.utils.html import strip_tags
from django.utils.translation import gettext_lazy as _


def get_field_value(field_name, obj, model_admin):
    attr = None
    f = None
    value = model_admin.get_empty_value_display()
    try:
        if LOOKUP_SEP in field_name:
            fields = field_name.split(LOOKUP_SEP)
            value = obj
            for field in fields:
                value = getattr(value, field)
                attr = field
        else:
            f, attr, value = lookup_field(field_name, obj, model_admin)
            if isinstance(value, (datetime.datetime, datetime.date)):
                # Format a date based on settings.DATE_FORMAT/settings.DATE_TIME_FORMAT
                value = localize(value, settings.USE_L10N)

    except AttributeError:
        pass

    return f, attr, value


def export_as_csv_action(description=_('Export as CSV'), fields=None, header=True):
    def export_as_csv(model_admin, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=%s.csv' % model_admin.opts.db_table

        writer = csv.writer(response)
        if header:
            fields_header = []
            for field_name in fields:
                try:
                    text, attr = label_for_field(
                        field_name, model_admin.model,
                        model_admin=model_admin,
                        return_attr=True
                    )
                except Exception:
                    if LOOKUP_SEP in field_name:
                        text = field_name.split(LOOKUP_SEP)[1]
                    else:
                        text = field_name

                fields_header.append(text.capitalize())
            writer.writerow(fields_header)

        for obj in queryset:
            line = []
            for field_name in fields:
                f, attr, value = get_field_value(field_name, obj, model_admin)
                if f is None or f.auto_created:
                    boolean = getattr(attr, 'boolean', False)
                    result_repr = display_for_value(value, boolean)
                else:
                    if hasattr(f, 'rel') and isinstance(f.rel, models.ManyToOneRel):
                        field_val = getattr(obj, f.name)
                        if field_val is None:
                            result_repr = model_admin.get_empty_value_display()
                        else:
                            result_repr = field_val
                    else:
                        result_repr = display_for_field(value, f, model_admin.get_empty_value_display())
                line.append(strip_tags('%s' % result_repr))
            writer.writerow(line)
        return response

    export_as_csv.short_description = description
    return export_as_csv
