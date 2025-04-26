import datetime as dt
import zoneinfo

from django.conf import settings


def now() -> dt.datetime:
    return dt.datetime.now(zoneinfo.ZoneInfo(settings.TIME_ZONE))


def today() -> dt.date:
    return now().date()
