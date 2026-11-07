ALTER TABLE boxes
    ADD COLUMN heartbeat_interval_seconds SMALLINT UNSIGNED NOT NULL DEFAULT 60,
    ADD CONSTRAINT ck_box_heartbeat_interval CHECK (heartbeat_interval_seconds >= 1);
