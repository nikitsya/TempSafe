-- Back up the database and apply once before deploying the dual-sensor backend.
-- Existing readings belong to the inside sensor; numbering remains box-wide.
ALTER TABLE temperature_samples
    ADD COLUMN sensor_location ENUM ('inside','outside') NOT NULL DEFAULT 'inside'
        AFTER sequence_no,
    ADD KEY ix_box_sensor_sequence (box_id, sensor_location, sequence_no),
    ADD KEY ix_box_sensor_time (box_id, sensor_location, observed_at);
