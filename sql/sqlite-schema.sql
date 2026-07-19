-- SQLite version , for local dev/testing.
-- Run with: sqlite3 endpoint_security.db < sql/schema_sqlite.sql
--
-- hostname is the natural
-- key everywhere, and there's no FK from av_controls/edr_controls to
-- assets on purpose — evidence for a hostname not yet in the inventory
-- is a real finding, not an import error.

DROP TABLE IF EXISTS edr_controls;
DROP TABLE IF EXISTS av_controls;
DROP TABLE IF EXISTS assets;

CREATE TABLE assets (
    hostname            TEXT NOT NULL PRIMARY KEY,
    ip_address          TEXT NOT NULL UNIQUE,
    operating_system    TEXT NOT NULL,
    business_owner      TEXT NOT NULL,
    loaded_at           TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE av_controls (
    hostname              TEXT NOT NULL PRIMARY KEY,
    installed              INTEGER NOT NULL,   -- 0/1
    version                TEXT,
    engine_version         TEXT,
    signature_version      TEXT,
    last_update            TEXT,               -- ISO datetime string
    realtime_protection    INTEGER NOT NULL,
    tamper_protection      INTEGER NOT NULL,
    policy                 TEXT,
    last_heartbeat         TEXT,
    loaded_at              TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE edr_controls (
    hostname              TEXT NOT NULL PRIMARY KEY,
    sensor_installed       INTEGER NOT NULL,
    sensor_version         TEXT,
    last_checkin           TEXT,
    protection_status      TEXT NOT NULL,      -- 'Healthy' | 'Unhealthy'
    isolation_status        TEXT NOT NULL,      -- 'Isolated' | 'Not Isolated'
    policy                 TEXT,
    detection_count         INTEGER NOT NULL DEFAULT 0,
    loaded_at              TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE VIEW vw_inventory_drift AS
SELECT hostname, 'evidence_without_inventory' AS drift_type, 'av_controls' AS source
FROM av_controls WHERE hostname NOT IN (SELECT hostname FROM assets)
UNION
SELECT hostname, 'evidence_without_inventory', 'edr_controls'
FROM edr_controls WHERE hostname NOT IN (SELECT hostname FROM assets)
UNION
SELECT hostname, 'inventory_without_av_evidence', NULL
FROM assets WHERE hostname NOT IN (SELECT hostname FROM av_controls)
UNION
SELECT hostname, 'inventory_without_edr_evidence', NULL
FROM assets WHERE hostname NOT IN (SELECT hostname FROM edr_controls);
