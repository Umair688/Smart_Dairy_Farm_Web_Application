import datetime as dt

from django import template

from core.utils import format_money

register = template.Library()


@register.simple_tag(takes_context=True)
def money(context, value):
    """{% money value %} -> 'Rs 1,250.00' using the farm's currency."""
    return format_money(context.get("currency", "Rs"), value)


@register.simple_tag(takes_context=True)
def cell(context, obj, attr, kind=""):
    """Render one table cell for a generic list page."""
    display = getattr(obj, f"get_{attr}_display", None)
    value = display() if display else getattr(obj, attr, "")
    if callable(value):
        value = value()
    if value is None or value == "":
        return "—"
    if kind == "money":
        return format_money(context.get("currency", "Rs"), value)
    if kind == "liters":
        return f"{value:,.2f} L"
    if kind == "date" or isinstance(value, dt.date):
        return value.strftime("%d %b %Y")
    if isinstance(value, bool):
        return "Yes" if value else "No"
    return value


@register.filter
def bs(field):
    """Render a form field with the right Bootstrap 5 class."""
    kind = field.widget_type
    if kind == "checkbox":
        css = "form-check-input"
    elif kind in ("select", "selectmultiple"):
        css = "form-select"
    else:
        css = "form-control"
    if field.errors:
        css += " is-invalid"
    return field.as_widget(attrs={"class": css})
