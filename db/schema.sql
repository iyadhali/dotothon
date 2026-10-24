-- Maldives Accessibility Platform — SQLite schema
--
-- The pipeline writes typed CSV artifacts (reproducible, diffable, one per stage); this database
-- is the queryable system of record the web app reads. Every table is rebuilt from those
-- artifacts, so the database is never hand-edited — it is a projection of the pipeline.
--
--   data/derived/*.csv  --(scripts/build_database.py)-->  data/platform.sqlite

PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS dataset;
DROP TABLE IF EXISTS ingest_run;
DROP TABLE IF EXISTS ingest_stage;
DROP TABLE IF EXISTS island;
DROP TABLE IF EXISTS sea_edge;
DROP TABLE IF EXISTS land_edge;
DROP TABLE IF EXISTS service;
DROP TABLE IF EXISTS service_access;
DROP TABLE IF EXISTS service_summary;
DROP TABLE IF EXISTS placement;
DROP TABLE IF EXISTS priority_gaps;
DROP TABLE IF EXISTS meta;

-- ---------------------------------------------------------------- provenance ----------------
CREATE TABLE dataset (
    id           TEXT PRIMARY KEY,      -- macl | avas | followme | mtcc | census | boundaries | moe | moh | services
    files        INTEGER NOT NULL,
    bytes        INTEGER NOT NULL,
    fingerprint  TEXT,                  -- sha256 over (path, size, mtime), truncated
    latest_mtime TEXT,
    first_seen   TEXT,
    last_seen    TEXT
);

CREATE TABLE ingest_run (
    run_id     INTEGER PRIMARY KEY,
    started    TEXT,
    finished   TEXT,
    seconds    REAL,
    trigger    TEXT,                    -- cli | watch | app
    stages     TEXT
);

CREATE TABLE ingest_stage (
    run_id  INTEGER REFERENCES ingest_run(run_id),
    stage   TEXT,
    status  TEXT,                       -- ok | skipped | failed
    seconds REAL,
    detail  TEXT
);

-- ---------------------------------------------------------------- the network ---------------
CREATE TABLE island (
    node_id                TEXT PRIMARY KEY,
    name                   TEXT NOT NULL,
    atoll                  TEXT,
    type                   TEXT,        -- inhabited | resort | airport | industrial | ...
    lat                    REAL,
    lon                    REAL,
    population             INTEGER DEFAULT 0,
    child_0_17             INTEGER DEFAULT 0,
    area_km2               REAL,
    has_higher_secondary   INTEGER DEFAULT 0,
    has_lower_secondary    INTEGER DEFAULT 0,
    hours_to_hs            REAL,        -- NULL = no observed route
    hours_to_lower_sec     REAL,
    hours_to_campus        REAL,
    islands_reachable      INTEGER,
    sea_neighbours         INTEGER
);

CREATE TABLE sea_edge (
    from_id    TEXT REFERENCES island(node_id),
    to_id      TEXT REFERENCES island(node_id),
    trips      INTEGER,
    devices    INTEGER,
    med_hours  REAL,
    p10_hours  REAL,
    p90_hours  REAL,
    med_km     REAL,
    med_knots  REAL,
    am_share   REAL,
    pm_share   REAL,
    PRIMARY KEY (from_id, to_id)
);

CREATE TABLE land_edge (
    a      TEXT REFERENCES island(node_id),
    b      TEXT REFERENCES island(node_id),
    hours  REAL,
    note   TEXT,
    PRIMARY KEY (a, b)
);

-- ---------------------------------------------------------------- services ------------------
CREATE TABLE service (
    service_id   TEXT PRIMARY KEY,
    category     TEXT NOT NULL,         -- education | health
    service_type TEXT NOT NULL,         -- school_primary | school_lower_secondary | ... | hospital
    name         TEXT NOT NULL,
    atoll        TEXT,
    island       TEXT,
    node_id      TEXT REFERENCES island(node_id),
    lat          REAL,
    lon          REAL,
    source       TEXT,
    notes        TEXT,
    added_at     TEXT
);

CREATE TABLE service_access (
    node_id         TEXT REFERENCES island(node_id),
    island          TEXT,
    atoll           TEXT,
    category        TEXT,
    service_type    TEXT,
    n_providers     INTEGER,
    has_local       INTEGER,
    hours           REAL,               -- NULL = unreachable
    provider_node   TEXT,               -- the island that provides it
    provider_island TEXT,
    provider_name   TEXT,
    population      INTEGER,
    child_0_17      INTEGER,
    PRIMARY KEY (node_id, service_type)
);

CREATE TABLE service_summary (
    category            TEXT,
    service_type        TEXT,
    n_facilities        INTEGER,
    islands_with_local  INTEGER,
    islands_within_2h   INTEGER,
    islands_unreachable INTEGER,
    population_within_2h INTEGER,
    children_within_2h  INTEGER,
    median_hours        REAL,
    PRIMARY KEY (category, service_type)
);

-- ---------------------------------------------------------------- simulator -----------------
-- Greedy placement: for each service type, the best k-th facility to add, with the impact of
-- adding it to the network that already contains the previous k-1 picks.
CREATE TABLE placement (
    service_type       TEXT,
    k                  INTEGER,         -- 1 = first facility added, 2 = second, ...
    node_id            TEXT REFERENCES island(node_id),
    island             TEXT,
    atoll              TEXT,
    newly_within_2h    INTEGER,         -- additional people inside 2 h
    children_newly     INTEGER,
    islands_newly      INTEGER,
    pop_weighted_gain  REAL,            -- hours saved, weighted by residents
    median_gain        REAL,
    coverage_after     INTEGER,         -- islands within 2 h after this placement
    population_after   INTEGER,
    PRIMARY KEY (service_type, k)
);

CREATE TABLE priority_gaps (
    node_id        TEXT REFERENCES island(node_id),
    island         TEXT,
    atoll          TEXT,
    population     INTEGER,
    child_0_17     INTEGER,
    hours_now      REAL,
    nearest_hs_id  TEXT,
    nearest_hs     TEXT,
    distance_km    REAL,
    hours_if_direct REAL,
    hours_saved    REAL
);

CREATE TABLE meta (
    key   TEXT PRIMARY KEY,
    value TEXT
);

CREATE INDEX idx_island_pop      ON island(population DESC);
CREATE INDEX idx_access_type     ON service_access(service_type, hours);
CREATE INDEX idx_service_node    ON service(node_id);
CREATE INDEX idx_edge_from       ON sea_edge(from_id);
CREATE INDEX idx_placement_k     ON placement(service_type, k);

-- ---------------------------------------------------------------- views ----------------------
-- The web app reads these names, which is also what the pipeline stages are called, so a
-- reader can trace any number in the UI back to the stage that produced it.
CREATE VIEW IF NOT EXISTS sea_nodes AS
    SELECT node_id, name, atoll, type, population, child_0_17, lat, lon FROM island;

CREATE VIEW IF NOT EXISTS sea_edges AS
    SELECT from_id, to_id, trips, devices, med_hours, p10_hours, p90_hours, med_km, med_knots,
           am_share, pm_share FROM sea_edge;

CREATE VIEW IF NOT EXISTS services_placed AS
    SELECT service_id, category, service_type, name, atoll, island, lat, lon, source, added_at,
           notes, node_id FROM service;

CREATE VIEW IF NOT EXISTS island_access AS
    SELECT node_id, name AS island, atoll, population, child_0_17, lat, lon,
           has_higher_secondary AS has_own_higher_secondary,
           has_lower_secondary  AS has_own_lower_secondary,
           hours_to_hs, hours_to_lower_sec, hours_to_campus,
           islands_reachable, sea_neighbours
    FROM island WHERE type = 'inhabited';
