-- Run after 001_add_prototype_box.sql, with the project's database selected.
-- Agreed prototype rules for valid samples:
-- Alert: T <= 0 or T > 25; Warning: 24 <= T <= 25; Normal: 0 < T < 24.
-- Keep this profile unchanged; future threshold changes need a new profile ID.
INSERT INTO threshold_profiles
    (profile_id, box_id, lower_c, warning_c, upper_c, source_note, is_demo)
SELECT 'e93a4368-e11a-4f27-8b31-d55d61392548',
       'TS-01',
       0.00,
       24.00,
       25.00,
       'Agreed prototype settings: Alert at or below 0 C or above 25 C; Warning from 24 C through 25 C. See docs/research/temperature-research-sources.md and docs/research/sensor-research.md. Not a universal medicine storage range.',
       TRUE
WHERE NOT EXISTS (SELECT 1
                  FROM threshold_profiles
                  WHERE profile_id = 'e93a4368-e11a-4f27-8b31-d55d61392548');
