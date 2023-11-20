from django.db.models import QuerySet
from datetime import datetime
import pytz


def day_start():
    today = datetime.today()
    today = datetime(today.year, today.month, today.day, 0, 0, 0, tzinfo=pytz.UTC)
    return today


class EventQuerySet(QuerySet):

    def approved_events(self):
        return self.filter(approved=True)

    def unapproved_events(self):
        return self.filter(approved=False)

    def upcoming_events(self):
        return self.filter(start_date__gt=day_start()).\
            order_by('-featured', 'start_date', 'end_date')

    def ongoing_events(self):
        return self.filter(start_date__lte=day_start(), end_date__gte=day_start()).\
            order_by('-featured', 'start_date', 'end_date')

    def past_events(self):
        return self.filter(end_date__lte=day_start()).\
            order_by('-featured', '-start_date', '-end_date')
