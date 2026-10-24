"""Four endpoints: one full page and three HTMX fragments.

Each fragment is a plain Django template render — no JSON, no client-side router. HTMX swaps the
HTML in, so the same code path serves the first paint and every interaction after it.
"""
import json

import pandas as pd
from django.http import Http404
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_http_methods

from .data import DERIVED, ROOT, coverage_by_atoll, model, service_gap_by_atoll


def _manifest() -> dict | None:
    path = DERIVED / "source_manifest.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return None


def source_rows(manifest: dict | None) -> list[dict]:
    """Manifest sources flattened for the table on the data page."""
    if not manifest:
        return []
    rows = []
    for key, info in manifest.get("sources", {}).items():
        label, publisher, detail = SOURCE_INFO.get(key, (key.title(), "—", ""))
        rows.append({"key": key, "label": label, "publisher": publisher, "detail": detail,
                     "files": info.get("files"), "bytes": info.get("bytes"),
                     "latest": (info.get("latest_mtime") or "")[:10]})
    return sorted(rows, key=lambda r: r["label"])


def funnel_rows(m) -> list[dict]:
    """The coverage ladder for grade 11-12, from all islands down to the ones with no route."""
    from .data import db_frame
    st = m.stats()
    ls = int(db_frame("select count(*) as n from island_access where has_own_lower_secondary = 1").n.iloc[0])
    return [
        {"label": "Inhabited islands", "value": st["islands"], "of": st["islands"], "note": "2022 census"},
        {"label": "Teach grade 7-10", "value": ls,
         "of": st["islands"], "note": "lower secondary on the island"},
        {"label": "Teach grade 11-12", "value": st["hs_islands"], "of": st["islands"], "note": "higher secondary on the island"},
        {"label": "Reach grade 11-12 in 2 h", "value": st["within2_islands"], "of": st["islands"], "note": "on the observed network"},
        {"label": "No observed route", "value": st["no_service"], "of": st["islands"], "note": "no sailing in the month of GPS"},
    ]


# what each source is, in the words the page uses; the file counts come from the manifest
SERVICE_LABEL = {
    "hospital": "Hospital",
    "health_centre": "Health centre",
    "school_higher_secondary": "Grade 11–12 school",
    "school_lower_secondary": "Grade 7–10 school",
    "school_primary": "Primary school",
    "college": "University campus",
}


@require_GET
def index(request):
    m = model()
    rows = m.ranked(limit=12)
    return render(request, "access/index.html", {
        "s": m.stats(),
        "islands": m.picker,
        "atolls": m.atolls,
        "rows": rows,
        "gaps": m.gaps,
        "manifest": _manifest(),
        "default_from": "MV002012",   # Kulhudhuffushi: the demo journey that works
        "default_to": "",
        "default_from_name": "Kulhudhuffushi",
        "default_to_name": "",
        "default_island": request.GET.get("island", "MV002012"),
        "n_rows": len(m.inhabited),
        "n_services": len(m.services),
        "atoll_rows": coverage_by_atoll(),
        "n_beyond": m.stats()["islands"] - m.stats()["within2_islands"],
        "gap_people": sum(int(g.get("population", 0)) for g in m.gaps),
        "gap_children": sum(int(g.get("child_0_17", 0) or 0) for g in m.gaps),
        "funnel": funnel_rows(m),
        "bands": m.band_population(),
        "beyond2_pct": round(sum(b["share"] for b in m.band_population()
                                  if b["band"] in ("under4", "under8", "over8", "unknown")), 1),
        "median_h": "%d min" % round(60 * float(m.inhabited.hours_to_hs.median())),
        "worst_h": "%.1f h" % float(m.inhabited.hours_to_hs.max()),
        "sel_atoll": "",
        "sel_band": "",
    })


@require_GET
def island_card(request, node_id):
    c = model().card(node_id)
    if c is None:
        raise Http404(f"unknown island: {node_id}")
    return render(request, "access/_island_card.html", {"c": c})


TYPE_LABEL = {
    "school_primary": "Primary school",
    "school_lower_secondary": "Grades 7–10",
    "school_higher_secondary": "Grades 11–12",
    "college": "University campus",
    "health_centre": "Health centre",
    "hospital": "Hospital",
}


@require_GET
def connect(request):
    """Island to service: every service type, where the nearest one is, and how you get there."""
    m = model()
    node = request.GET.get("island", "").strip()
    if not node:
        node = m.inhabited.sort_values("population", ascending=False).iloc[0].node_id
    card = m.card(node)
    if card is None:
        raise Http404(f"unknown island: {node}")
    category = request.GET.get("category", "").strip()

    rows, paths = [], []
    for svc_type, a in card["access"].items():
        if category and a["category"] != category:
            continue
        row = {"type": svc_type, "label": TYPE_LABEL.get(svc_type, svc_type),
               "category": a["category"], "local": a["local"], "hours": a["hours"],
               "place": a["place"], "hops": None, "path": None}
        pid = a.get("provider_id")
        if not a["local"] and pid:
            legs, total = m.route(node, pid)
            if legs:
                row["hops"] = len(legs)
                row["hours"] = round(total, 2)
                seq = [legs[0].a] + [e.b for e in legs]
                pts = [[round(float(m.by_id.loc[n, "lat"]), 5), round(float(m.by_id.loc[n, "lon"]), 5)]
                       for n in seq]
                row["path"] = pts
                paths.append(pts)
        if row["local"]:
            row["pct"], row["band"] = 100, "own"
        elif row["hours"] is None:
            row["pct"], row["band"] = 0, "unknown"
        else:
            row["pct"] = max(6, min(100, round(100 * row["hours"] / 8)))
            row["band"] = ("under2" if row["hours"] <= 2 else "under4" if row["hours"] <= 4
                           else "under8" if row["hours"] <= 8 else "over8")
        rows.append(row)

    rows.sort(key=lambda r: (0 if r["local"] else 1, r["hours"] if r["hours"] is not None else 999))
    local_n = sum(1 for r in rows if r["local"])
    within2 = sum(1 for r in rows if r["hours"] is not None and r["hours"] <= 2)
    far = [r for r in rows if r["hours"] is not None]
    worst = max(far, key=lambda r: r["hours"]) if far else None

    return render(request, "access/_connect.html", {
        "c": card, "rows": rows, "category": category,
        "paths": json.dumps(paths),
        "local_n": local_n, "within2": within2, "total_n": len(rows),
        "worst": worst, "categories": ["education", "health"],
        "cat_label": {"education": "Education", "health": "Health"},
    })


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
            # sailing time vs time spent waiting for a connection, for the little bar
            sailing = sum(e.hours for e in legs)
            ctx["sailing"] = round(sailing, 2)
            ctx["sailing_pct"] = round(100 * sailing / total) if total else 0
            ctx["wait_pct"] = 100 - ctx["sailing_pct"]
            # coordinates for the map polyline: the start island then every leg's destination
            seq = [legs[0].a] + [e.b for e in legs]
            ctx["path"] = json.dumps([
                [round(float(m.by_id.loc[n, "lat"]), 5), round(float(m.by_id.loc[n, "lon"]), 5)]
                for n in seq
            ])
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


SERVICE_TYPES = [
    ("education", "school_primary", "Primary school (Gr 1–6)"),
    ("education", "school_lower_secondary", "Lower secondary (Gr 7–10)"),
    ("education", "school_higher_secondary", "Higher secondary (Gr 11–12)"),
    ("education", "college", "College / university campus"),
    ("health", "health_centre", "Health centre"),
    ("health", "hospital", "Hospital"),
    ("other", "other", "Other (describe in the name)"),
]


