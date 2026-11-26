-- Existing selections remain unconfirmed until the device reports adoption.
ALTER TABLE box_configuration
    ADD COLUMN applied_profile_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin DEFAULT NULL,
    ADD CONSTRAINT fk_configuration_applied FOREIGN KEY (applied_profile_id, box_id)
        REFERENCES threshold_profiles (profile_id, box_id);
