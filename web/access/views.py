"""Four endpoints: one full page and three HTMX fragments.

Each fragment is a plain Django template render — no JSON, no client-side router. HTMX swaps the
HTML in, so the same code path serves the first paint and every interaction after it.
"""
import json

import pandas as pd
from django.http import Http404
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_http_methods

from .data import DERIVED, ROOT, model


def _manifest() -> dict | None:
    path = DERIVED / "source_manifest.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return None


SERVICE_LABEL = {
    "hospital": "Hospital",
    "health_centre": "Health centre",
    "school_higher_secondary": "Grade 11–12 school",
    "school_lower_secondary": "Grade 7–10 school",
    "school_primary": "Primary school",
    "college": "University campus",
}


@require_GET
def platform(request):
    """How the thing is built: sources -> ingest -> derived tables -> SQLite -> app."""
    from .data import db_frame
    tables = db_frame("""
        select name, (select count(*) from pragma_table_info(m.name)) as columns
        from sqlite_master m where type = 'table' and name not like 'sqlite_%' order by name""")
    counts = {}
    for t in tables.name:
        try:
            counts[t] = int(db_frame("select count(*) as n from \"%s\"" % t).n.iloc[0])
        except Exception:
            counts[t] = None
    runs = db_frame("select * from ingest_run order by run_id desc limit 1")
    m = model()
    return render(request, "access/platform.html", {
        "run": runs.iloc[0].to_dict() if len(runs) else None,
        "tables": counts,
        "summary": m.summary_rows(),
        "manifest": _manifest(),
        "s": m.stats(),
    })


@require_GET
def simulator(request):
    """Placement simulator: where should the next facility go to connect the most people?"""
    m = model()
    types = m.placement_types()
    # lead with the placement that moves the most people
    default_type = "hospital" if any(t["service_type"] == "hospital" for t in types) else (
        types[0]["service_type"] if types else "hospital")
    stype = request.GET.get("type") or default_type
    if stype not in {t["service_type"] for t in types}:
        stype = types[0]["service_type"] if types else "hospital"
    picks = m.placement(stype).to_dict("records")
    enriched = []
    for t in types:
        st = t["service_type"]
        first = m.placement(st).head(1).to_dict("records")
        now = m.access_now(st)
        enriched.append(dict(t,
                             label=SERVICE_LABEL.get(st, st),
                             first=first,
                             before=now.get("islands_2h", 0),
                             category=t.get("category", ""),
                             metric=f"{t.get('category','')}:{st}"))
    metric = next((e["metric"] for e in enriched if e["service_type"] == stype), "")
    return render(request, "access/simulator.html", {
        "types": enriched,
        "metric": metric,
        "stype": stype,
        "stype_label": SERVICE_LABEL.get(stype, stype),
        "picks": picks,
        "now": m.access_now(stype),
        "islands": m.picker,
        "manifest": _manifest(),
        "s": m.stats(),
    })


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
        "default_to": "MLE",
        "default_island": request.GET.get("island", "MV002012"),
        "n_rows": len(m.inhabited),
        "n_services": len(m.services),
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


def _rebuild_services() -> tuple[bool, str]:
    """Recompute the service access table and the map data after the register changes."""
    import subprocess, sys
    out = []
    for script in ("scripts/build_service_access.py", "web/build_web_data.py"):
        p = subprocess.run([sys.executable, str(ROOT / script)], cwd=ROOT,
                           capture_output=True, text=True, timeout=300)
        out.append(f"{script}: exit {p.returncode}")
        if p.returncode != 0:
            return False, (p.stderr or p.stdout)[-600:]
    return True, "; ".join(out)


@require_http_methods(["GET", "POST"])
def services(request):
    m = model()
    added = error = None
    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()
        node = (request.POST.get("island") or "").strip()
        stype = (request.POST.get("service_type") or "").strip()
        category = dict((t, c) for c, t, _ in SERVICE_TYPES).get(stype, "other")
        notes = (request.POST.get("notes") or "").strip()[:200]
        if not name or not node or not stype:
            error = "A name, an island and a service type are required."
        elif node not in m.by_id.index:
            error = f"Unknown island: {node}"
        elif node not in set(m.inhabited.node_id):
            error = "Pick an inhabited island — services are attributed to island communities."
        else:
            r = m.by_id.loc[node]
            row = {
                "service_id": f"usr-{abs(hash((name, node, stype))) % 10**8:08d}",
                "category": category, "service_type": stype, "name": name[:90],
                "atoll": r.atoll, "island": r["name"],
                "lat": round(float(r.lat), 5), "lon": round(float(r.lon), 5),
                "source": "added in the app", "notes": notes,
                "added_at": __import__("datetime").date.today().isoformat(),
            }
            path = ROOT / "data" / "services.csv"
            df = pd.read_csv(path)
            if ((df.name == row["name"]) & (df.island == row["island"])).any():
                error = f"“{row['name']}” is already on {row['island']}."
            else:
                pd.concat([df, pd.DataFrame([row])], ignore_index=True).to_csv(path, index=False)
                ok, msg = _rebuild_services()
                if ok:
                    added = row["name"]
                else:
                    error = f"Saved, but the rebuild failed — {msg}"
    cat = request.GET.get("cat", "")
    records = m.services if not cat else m.services[m.services.category == cat]
    return render(request, "access/services.html", {
        "services": records.sort_values(["atoll", "island", "service_type"])
                             [["name", "category", "service_type", "atoll", "island", "source"]]
                             .to_dict("records"),
        "summary": m.service_summary.to_dict("records"),
        "types": SERVICE_TYPES,
        "picker": m.picker,
        "n": len(records), "total": len(m.services),
        "cat": cat, "added": added, "error": error,
        "s": m.stats(), "manifest": _manifest(),
    })
