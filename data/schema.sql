-- Schema for the compliance violations store.
-- Matches the SELECT in src/tools.py::query_violations.
CREATE TABLE IF NOT EXISTS violations (
    id          INTEGER PRIMARY KEY,
    driver_id   TEXT    NOT NULL,
    type        TEXT    NOT NULL,
    severity    TEXT    NOT NULL,
    occurred_at TEXT    NOT NULL
);

-- Tiny synthetic seed so the agent can run end-to-end locally.
INSERT INTO violations (id, driver_id, type, severity, occurred_at) VALUES
    (1, 'D-1042', 'speeding',          'minor',    '2024-04-10'),
    (2, 'D-1042', 'speeding',          'minor',    '2024-09-02'),
    (3, 'D-1043', 'failure_to_signal', 'minor',    '2023-11-15'),
    (4, 'D-1044', 'dui',               'major',    '2024-12-22'),
    (5, 'D-1044', 'reckless_driving',  'major',    '2025-01-30'),
    (6, 'D-1046', 'license_suspended', 'critical', '2022-07-15');
