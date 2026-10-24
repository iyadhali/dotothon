"""Four endpoints: one full page and three HTMX fragments.

Each fragment is a plain Django template render — no JSON, no client-side router. HTMX swaps the
HTML in, so the same code path serves the first paint and every interaction after it.
"""
from django.http import Http404
from django.shortcuts import render
from django.views.decorators.http import require_GET

from .data import model


@require_GET
def index(request):
    m = model()
    rows = m.ranked(limit=12)
    return render(request, "access/index.html", {
        "s": m.stats(),
        "islands": m.picker,
        "atolls": m.atolls,
        "rows": rows,
        "default_from": "MV002012",   # Kulhudhuffushi: the demo journey that works
        "default_to": "MLE",
        "default_island": request.GET.get("island", "MV002012"),
        "n_rows": len(m.inhabited),
        "sel_atoll": "",
        "sel_band": "",
    })


@require_GET
def island_card(request, node_id):
    c = model().card(node_id)
    if c is None:
        raise Http404(f"unknown island: {node_id}")
    return render(request, "access/_island_card.html", {"c": c})


@require_GET
def route(request):
    m = model()
    frm = request.GET.get("from", "").strip()
    to = request.GET.get("to", "").strip()
    ctx = {"frm": frm, "to": to}
    if not frm or not to:
        ctx["error"] = "Choose a starting island and a destination."
    elif frm == to:
        ctx["error"] = "Same island on both sides — no sailing needed."
    else:
        legs, total = m.route(frm, to)
        ctx["frm_name"] = m.name_of(frm)
        ctx["to_name"] = m.name_of(to)
        if legs is None:
            ctx["error"] = ("No observed journey within two sailings. "
                            "That is a finding, not a bug: the crossing may exist but was not "
                            "captured in the August 2025 GPS sample.")
        else:
            ctx["legs"] = [{"a": e.a, "b": e.b, "a_name": m.name_of(e.a), "b_name": m.name_of(e.b),
                            "hours": round(e.hours, 2), "kind": e.kind, "trips": e.trips}
                           for e in legs]
            ctx["total"] = total
            ctx["hops"] = len(legs)
            ctx["conn_h"] = max(0, len(legs) - 1) * 1.0
    return render(request, "access/_route.html", ctx)


@require_GET
def ranked(request):
    m = model()
    atoll = request.GET.get("atoll", "").strip()
    band = request.GET.get("band", "").strip()
    rows = m.ranked(atoll=atoll, band=band, limit=60)
    total = len(m.ranked(atoll=atoll, band=band, limit=10_000))
    return render(request, "access/_ranked.html", {
        "rows": rows,
        "n_rows": total,
        "atolls": m.atolls,
        "sel_atoll": atoll,
        "sel_band": band,
    })
