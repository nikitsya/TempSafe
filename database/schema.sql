-- TEMSAFE initial core schema: MySQL 8.4 or later, in an empty database.
-- Run with strict SQL mode enabled. Use UTC on every application connection.
-- This is a baseline, not an upgrade script; existing tables deliberately cause errors.
SET SESSION time_zone = '+00:00';

CREATE TABLE boxes
(
    box_id VARCHAR(64) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY,
    name         VARCHAR(100) NOT NULL,
    last_seen_at DATETIME(6) NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_as_cs;

CREATE TABLE app_users
(
    user_id       BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    auth_subject  VARCHAR(191) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_as_cs;

CREATE TABLE box_access
(
    user_id BIGINT UNSIGNED NOT NULL,
    box_id VARCHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    PRIMARY KEY (user_id, box_id),
    CONSTRAINT fk_access_user FOREIGN KEY (user_id) REFERENCES app_users (user_id),
    CONSTRAINT fk_access_box FOREIGN KEY (box_id) REFERENCES boxes (box_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_as_cs;

CREATE TABLE threshold_profiles
(
    profile_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY,
    box_id     VARCHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    lower_c     DECIMAL(5, 2) NOT NULL,
    upper_c     DECIMAL(5, 2) NOT NULL,
    warning_c   DECIMAL(5, 2) NOT NULL,
    source_note TEXT          NOT NULL,
    is_demo     BOOLEAN       NOT NULL DEFAULT TRUE,
    created_at  DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    UNIQUE KEY uq_profile_box (profile_id, box_id),
    CONSTRAINT fk_profile_box FOREIGN KEY (box_id) REFERENCES boxes (box_id),
    CONSTRAINT ck_profile_limits CHECK (lower_c < warning_c AND warning_c < upper_c),
    CONSTRAINT ck_profile_demo CHECK (is_demo IN (0, 1))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_as_cs;

CREATE TABLE temperature_samples
(
    sample_id  CHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY,
    box_id     VARCHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    sequence_no    BIGINT UNSIGNED NOT NULL,
    profile_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin    NOT NULL,
    observed_at    DATETIME(6) NULL,
    clock_reliable BOOLEAN     NOT NULL,
    received_at    DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    temperature_c  DECIMAL(5, 2) NULL,
    quality        ENUM('valid','sensor_error') NOT NULL,
    UNIQUE KEY uq_box_sequence (box_id, sequence_no),
    KEY            ix_box_time (box_id, observed_at),
    CONSTRAINT fk_sample_box FOREIGN KEY (box_id) REFERENCES boxes (box_id),
    CONSTRAINT fk_sample_profile_box FOREIGN KEY (profile_id, box_id)
        REFERENCES threshold_profiles (profile_id, box_id),
    CONSTRAINT ck_sample_clock_flag CHECK (clock_reliable IN (0, 1)),
    CONSTRAINT ck_sample_observation_time CHECK ((clock_reliable = 1 AND observed_at IS NOT NULL)
        OR (clock_reliable = 0 AND observed_at IS NULL)),
    CONSTRAINT ck_sample_quality CHECK ((quality = 'valid' AND temperature_c IS NOT NULL
        AND temperature_c BETWEEN -40 AND 80)
        OR (quality = 'sensor_error' AND temperature_c IS NULL))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_as_cs;

-- Should Have: latest acknowledgement for a flagged sample.
CREATE TABLE sample_reviews
(
    sample_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY,
    reviewed_by BIGINT UNSIGNED NOT NULL,
    reviewed_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    CONSTRAINT fk_review_sample FOREIGN KEY (sample_id) REFERENCES temperature_samples (sample_id),
    CONSTRAINT fk_review_user FOREIGN KEY (reviewed_by) REFERENCES app_users (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_as_cs;
