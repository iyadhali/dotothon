# 15. Ferry timetable gaps: Zone 3, Malé links, unscheduled routes, service calendar

Date: 2026-10-24. Output: `data/external/ferry_timetables/supplementary_trips.csv` (597 stop-time rows, 109 trips, 54 MTCC routes). Raw sources in `data/external/ferry_timetables/raw/`.

## Key finding
The MTCC all-atolls timetable PDF (`CTN-Ferry-All-Atolls-16.7.23.pdf`, 54 pages, one page per route 101-607) that returned 403 directly **is retrievable from the Wayback Machine**: `https://web.archive.org/web/2023/https://mtcc.mv/wp-content/uploads/2022/01/CTN-Ferry-All-Atolls-16.7.23.pdf` (HTTP 200, plain curl, no bypass). Text layer is clean; `pdftotext -raw` yields explicit "dep time / from / to / arr time" legs, which were parsed into stop-times (script logic: legs chained into trips when the next leg starts at the previous destination within 100 min).

## Sources
| Source | Status | Use |
|---|---|---|
| Wayback copy of MTCC PDF (effective 29 Apr 2023; Kandoodhoo/Buruni pages 28 May 2023) | OK, saved `raw/mtcc_CTN-Ferry-All-Atolls-16.7.23_wayback.pdf`, `mtcc_all_atolls*.txt` | All CSV rows |
| mtcc.mv direct (ferry-network page, PDF) | 403 (not bypassed) | none |
| archive.org wayback/available API | 429 rate limit; CDX API worked (lists other MTCC PDFs: 2019 route press releases, Route Map 2021 PDF) | discovery only |
| amaldives.com public ferry guide 2026 (`raw/amaldives_guide.html`) | OK | independent check: Malé-Maafushi 309 departs Malé 15:00, arrives Maafushi 16:40, Sat-Thu, none Fri; 306 Sun/Tue/Thu 10:00. Matches the PDF exactly |
| routard forum, Wikipedia Transport in the Maldives | saved, not used (no timetable) | context |
| ferryscanner / 12go | search snippets only, private operator/speedboat listings (Rasdhoo first 10:35, Ukulhas 10:45) | not used (not public ferry) |
| WebSearch for atolltimes/edition/sun/corporatemaldives | one generic query only; no timetable found | not pursued further: PDF supersedes |

## Coverage vs gap list
1. **Zone 3 (K, AA, ADh, V, M)**: covered, routes 301-310 and 401-404. Malé-bound: 303 Thoddoo/Rasdhoo/Ukulhas-Malé (Sun, Wed to Malé; Mon, Thu from Malé), 305 Mahibadhoo-Malé (Male->Mahibadhoo Sat/Mon/Wed, reverse Sun/Tue/Thu, about 4h10), 306 Rakeedhoo-Keyodhoo-Felidhoo-Thinadhoo-Fulidhoo-Maafushi-Malé (to Malé Sat/Mon/Wed 07:00->14:05; from Malé Sun/Tue/Thu 10:00->16:50), 307 Kaashidhoo-Gaafaru-Malé (3.5h), 308 Dhiffushi-Thulusdhoo-Huraa-Himmafushi-Malé (Sat-Thu), 309 Guraidhoo-Maafushi-Gulhi-Malé (Sat-Thu, 2h05). Dhangethi sits on 304 (Fenfushi-Mahibadhoo); Meemu 401-404 (Muli etc.) are Mon/Tue-Wed/Thu/Sat-Sun only and do not reach Malé. Faafu 405, Dhaalu 406-407, Thaa/Laamu 501-505, Gaafu 601-607 are also present (Zones 4/5).
2. **Unscheduled routes (60 usable rows in rtl_unscheduled)**: 38 of 60 have all their stops on a single MTCC trip (island-set match; times are MTCC proxies, not the RTL-coded service). 22 unmatched: old/variant codes (OLD, R3Cx), spelling (Bileyfahi vs Bileffahi, Kumundhoo/Naivaadhoo not in PDF), Z2R5 Manadhoo-Kudafari, Z6 Fuvahmulah-Vaadhoo (no MTCC page; RTL-only/Zone 6), Z5R2 Dhevvadhoo-Villingili. Route codes are not mapped 1:1 between RTL (Z2R3...) and MTCC (101-607): join on island sequence.
3. **Service calendar**: `days_of_week` per trip. Pattern: Zone 2/3 core routes Sat-Thu (no Friday anywhere); Zone 1 and Gaafu routes run 1-3 days a week (e.g. 101 Mon, 102 Thu, 109 Sat/Tue/Thu, 116 Sat, 606 Sun/Tue/Wed).

## Not covered / limits
- Not found: Addu, Hithadhoo-Gan-type intra-atoll or resort/speedboat services; Malé-Villingili/Hulhumalé city ferries (separate MTCC network); Zone 6 Fuvahmulah; fresh 2025-26 timetables (PDF is 2023 vintage, likely revised; RTL snapshot is 2026-10-10).
- 3 stop rows `low` confidence: 102 Ihavandhoo arrival illegible; 502 Kandoodhoo-Buruni sub-timetable days assumed. 114 and 309 each had one leg reconstructed from layout text (noted in `notes`).
- 406/407: PDF lists both day groups together; assumed both days run the timetable.
- Zone labels follow the numeric MTCC series (1xx=Zone 1, 2xx=Zone 2, 301-404=Zone 3, 405-5xx=Zone 4, 6xx=Zone 5), an assumption to confirm against RTL zoning (Faafu may be Zone 3).
- Confidence "medium" for all clean rows: official source, but 2023 dated.
