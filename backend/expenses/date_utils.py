import datetime as dt
import zoneinfo

from django.conf import settings


def now() -> dt.datetime:
    return dt.datetime.now(zoneinfo.ZoneInfo(settings.TIME_ZONE))


def today() -> dt.date:
    return now().date()


def year() -> int:
    return today().year


def from_italian_date(italian_date: str) -> dt.date:
    """
    Convert an Italian date string (DD/MM/YYYY) to a Python date object.
    """
    day, month, year = map(int, italian_date.split("/"))
    return dt.date(year, month, day)


def is_italian_date(date_str: str) -> bool:
    """
    Check if the date string is in Italian format (DD/MM/YYYY).
    """
    try:
        day, month, year = map(int, date_str.split("/"))
        dt.date(year, month, day)  # Validate the date
        return True
    except (ValueError, IndexError):
        return False


def all_dates_in_range(start_date: dt.date, end_date: dt.date) -> list[dt.date]:
    """
    Generate a list of all dates between start_date and end_date, inclusive.
    """
    if start_date > end_date:
        raise ValueError("start_date must be less than or equal to end_date")

    return [
        start_date + dt.timedelta(days=i)
        for i in range((end_date - start_date).days + 1)
    ]
