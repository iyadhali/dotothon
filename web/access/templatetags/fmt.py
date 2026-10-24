"""Small display filters. Django's templates cannot call str.format, so grouping lives here."""
from django import template

register = template.Library()


@register.filter
def num(value) -> str:
    """187 -> '187', 448819 -> '448,819'. Blank for None."""
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return "—"


@register.filter
def hours(value) -> str:
    """Seconds-free hour display: 2.6325 -> '2.6 h'."""
    if value is None or value == "":
        return "—"
    try:
        return f"{float(value):.1f} h"
    except (TypeError, ValueError):
        return "—"
