-- Run after schema.sql, with the project's database selected.
-- Add the single prototype box without changing an existing record.
INSERT INTO boxes (box_id, name, last_seen_at)
SELECT 'TS-01', 'Prototype box TS-01', NULL
WHERE NOT EXISTS (SELECT 1
                  FROM boxes
                  WHERE box_id = 'TS-01');
