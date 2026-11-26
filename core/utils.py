import calendar
import datetime as dt
from decimal import Decimal

from django.utils import timezone


def today():
    return timezone.localdate()


def parse_month(value, default=None):
    """Parse 'YYYY-MM' into (year, month); fall back to the current month."""
    default = default or today()
    try:
        year_s, month_s = value.split("-")
        year, month = int(year_s), int(month_s)
        if 1 <= month <= 12 and 1900 <= year <= 2200:
            return year, month
    except (AttributeError, ValueError):
        pass
    return default.year, default.month


def month_bounds(year, month):
    last_day = calendar.monthrange(year, month)[1]
    return dt.date(year, month, 1), dt.date(year, month, last_day)


def shift_month(year, month, delta):
    index = year * 12 + (month - 1) + delta
    return index // 12, index % 12 + 1


def month_label(year, month):
    return dt.date(year, month, 1).strftime("%B %Y")


def month_value(year, month):
    return f"{year:04d}-{month:02d}"


def format_money(currency, value):
    if value is None:
        return "—"
    value = Decimal(value)
    sign = "-" if value < 0 else ""
    return f"{sign}{currency} {abs(value):,.2f}"
