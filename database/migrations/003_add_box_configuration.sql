-- Run once on an existing database; schema.sql already includes this table for fresh installs.
-- A configuration selects the desired profile; it does not confirm device adoption.
CREATE TABLE box_configuration
(
    box_id     VARCHAR(64) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY,
    profile_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    CONSTRAINT fk_configuration_box FOREIGN KEY (box_id) REFERENCES boxes (box_id),
    CONSTRAINT fk_configuration_profile_box FOREIGN KEY (profile_id, box_id)
        REFERENCES threshold_profiles (profile_id, box_id)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_0900_as_cs;

-- Select automatically only when there is exactly one profile for a box.
-- Boxes with multiple profiles require an explicit operator choice through the API.
INSERT INTO box_configuration (box_id, profile_id)
SELECT box_id, MIN(profile_id)
FROM threshold_profiles
GROUP BY box_id
HAVING COUNT(*) = 1;
