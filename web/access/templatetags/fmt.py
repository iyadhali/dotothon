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


@register.filter
def filesize(value) -> str:
    """Bytes -> '1.9 GB' / '164 kB'. Used for the data-provenance line."""
    try:
        n = float(value)
    except (TypeError, ValueError):
        return "—"
    for unit, scale in (("GB", 1e9), ("MB", 1e6), ("kB", 1e3)):
        if n >= scale:
            return f"{n / scale:,.1f} {unit}".replace(".0 ", " ")
    return f"{n:,.0f} B"
