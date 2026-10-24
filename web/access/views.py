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


TABLE_NOTES = {
    "dataset": "one row per source file, with its fingerprint",
    "ingest_run": "one row per pipeline run",
    "ingest_stage": "each stage of each run, with seconds",
    "island": "every node in the network, inhabited or not",
    "sea_edge": "observed crossings between islands",
    "land_edge": "causeway links the boat data cannot see",
    "service": "the facility register",
    "service_access": "time from every island to each service type",
    "service_summary": "national line per service type",
    "priority_gaps": "islands beyond two hours, ranked",
    "placement": "the greedy placement ranking",
    "meta": "build metadata",
}

# what each source is, in the words the page uses; the file counts come from the manifest
SOURCE_INFO = {
    "followme":  ("FollowMe GPS pings", "Organiser", "Anonymised device movement, August 2025"),
    "mtcc":      ("MTCC bus and ferry ridership", "Organiser", "Monthly and daily passenger counts"),
    "macl":      ("MACL airport traffic", "Organiser", "Scheduled and charter records, 2012–2026"),
    "avas":      ("Avas Ride trips", "Organiser", "Completed, expired and cancelled rides, 2026"),
    "census":    ("Census 2022 population", "Maldives Bureau of Statistics", "Island and atoll indicator sheets"),
    "boundaries":("Administrative boundaries", "OCHA COD-AB (CC BY)", "21 atolls, 1,556 islands"),
    "moe":       ("School statistics 2024", "Ministry of Education", "Enrolment and grade range, island by island"),
    "moh":       ("Health facility list", "Ministry of Health", "Health centres and hospitals by island"),
    "services":  ("Service register", "This project", "Additions made in the app, kept in data/services.csv"),
}

SERVICE_LABEL = {
    "hospital": "Hospital",
    "health_centre": "Health centre",
    "school_higher_secondary": "Grade 11–12 school",
    "school_lower_secondary": "Grade 7–10 school",
    "school_primary": "Primary school",
    "college": "University campus",
}


@require_GET
def data_room(request):
    """Where the numbers come from: sources, refresh state, tables, method."""
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
    summary = m.summary_rows()
    for row in summary:
        row["label"] = SERVICE_LABEL.get(row.get("service_type", ""), row.get("service_type", ""))
    return render(request, "access/data.html", {
        "run": runs.iloc[0].to_dict() if len(runs) else None,
        "tables": counts,
        "summary": summary,
        "manifest": _manifest(),
        "s": m.stats(),
        "stage_count": len((runs.iloc[0]["stages"] or "").split(",")) if len(runs) else 0,
        "sources": source_rows(_manifest()),
        "total_services": len(m.services),
        "table_notes": TABLE_NOTES,
    })


@require_GET
def placement(request):
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
    return render(request, "access/placement.html", {
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
        "atoll_rows": coverage_by_atoll(),
        "n_beyond": m.stats()["islands"] - m.stats()["within2_islands"],
        "gap_people": sum(int(g.get("population", 0)) for g in m.gaps),
        "gap_children": sum(int(g.get("child_0_17", 0) or 0) for g in m.gaps),
        "funnel": funnel_rows(m),
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
    rows = records.sort_values(["atoll", "island", "service_type"]).copy()
    rows["type_label"] = rows.service_type.map(SERVICE_LABEL).fillna(rows.service_type)
    summary = m.service_summary.copy()
    summary["label"] = summary.service_type.map(SERVICE_LABEL).fillna(summary.service_type)
    summary = summary.sort_values("islands_within_2h")
    return render(request, "access/services.html", {
        "services": rows[["name", "category", "service_type", "type_label", "atoll", "island", "source"]]
                          .to_dict("records"),
        "summary": summary.to_dict("records"),
        "hospital": m.access_now("hospital"),
        "categories": sorted(m.services.category.unique()),
        "types": SERVICE_TYPES,
        "picker": m.picker,
        "n": len(records), "total": len(m.services),
        "cat": cat, "added": added, "error": error,
        "gap_rows": service_gap_by_atoll("hospital"),
        "s": m.stats(), "manifest": _manifest(),
    })
