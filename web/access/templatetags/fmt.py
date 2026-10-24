"""Small display filters. Django's templates cannot call str.format, so grouping lives here."""
from django import template

register = template.Library()


SVC_LABEL = {
    "school_primary": "primary school",
    "school_lower_secondary": "grades 7–10",
    "school_higher_secondary": "grades 11–12",
    "college": "university campus",
    "health_centre": "health centre",
    "hospital": "hospital",
}


@register.filter
def svclabel(v):
    return SVC_LABEL.get(str(v), str(v).replace("_", " "))


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


@register.filter
def get_item(mapping, key):
    """dict lookup by variable key, which Django templates cannot do natively."""
    try:
        return mapping.get(key, "")
    except AttributeError:
        return ""
