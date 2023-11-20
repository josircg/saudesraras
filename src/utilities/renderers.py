import csv
import html

from django.utils.html import strip_tags
from rest_framework_csv.renderers import CSVRenderer as CSVR


class CSVRenderer(CSVR):
    writer_opts = {'quoting': csv.QUOTE_ALL}

    def flatten_data(self, data):
        flattened_data = super().flatten_data(data)

        for item in flattened_data:
            for key, value in item.items():
                if isinstance(value, str):
                    item[key] = strip_tags(html.unescape(value))

            yield item
