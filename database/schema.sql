CREATE TABLE boxes
(
    box_id       VARCHAR(64) PRIMARY KEY,
    name         VARCHAR(100) NOT NULL,
    last_seen_at DATETIME(6) NULL
) ENGINE=InnoDB;

CREATE TABLE app_users
(
    user_id       BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    auth_subject  VARCHAR(191) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL
) ENGINE=InnoDB;

CREATE TABLE box_access
(
    user_id BIGINT UNSIGNED NOT NULL,
    box_id  VARCHAR(64) NOT NULL,
    PRIMARY KEY (user_id, box_id),
    FOREIGN KEY (user_id) REFERENCES app_users (user_id),
    FOREIGN KEY (box_id) REFERENCES boxes (box_id)
) ENGINE=InnoDB;

CREATE TABLE threshold_profiles
(
    profile_id  CHAR(36) PRIMARY KEY,
    box_id      VARCHAR(64)   NOT NULL,
    lower_c     DECIMAL(5, 2) NOT NULL,
    upper_c     DECIMAL(5, 2) NOT NULL,
    warning_c   DECIMAL(5, 2) NOT NULL,
    source_note TEXT          NOT NULL,
    is_demo     BOOLEAN       NOT NULL DEFAULT TRUE,
    created_at  DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    UNIQUE KEY uq_profile_box (profile_id, box_id),
    FOREIGN KEY (box_id) REFERENCES boxes (box_id),
    CHECK (lower_c < warning_c AND warning_c < upper_c),
    CHECK (is_demo IN (0, 1))
) ENGINE=InnoDB;

CREATE TABLE temperature_samples
(
    sample_id      CHAR(36) PRIMARY KEY,
    box_id         VARCHAR(64) NOT NULL,
    sequence_no    BIGINT UNSIGNED NOT NULL,
    profile_id     CHAR(36)    NOT NULL,
    observed_at    DATETIME(6) NULL,
    clock_reliable BOOLEAN     NOT NULL,
    received_at    DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    temperature_c  DECIMAL(5, 2) NULL,
    quality        ENUM('valid','sensor_error') NOT NULL,
    UNIQUE KEY uq_box_sequence (box_id, sequence_no),
    KEY            ix_box_time (box_id, observed_at),
    FOREIGN KEY (box_id) REFERENCES boxes (box_id),
    FOREIGN KEY (profile_id, box_id)
        REFERENCES threshold_profiles (profile_id, box_id),
    CHECK (clock_reliable IN (0, 1)),
    CHECK ((clock_reliable = 1 AND observed_at IS NOT NULL)
        OR (clock_reliable = 0 AND observed_at IS NULL)),
    CHECK ((quality = 'valid' AND temperature_c IS NOT NULL
        AND temperature_c BETWEEN -40 AND 80)
        OR (quality = 'sensor_error' AND temperature_c IS NULL))
) ENGINE=InnoDB;

-- Should Have: latest acknowledgement for a flagged sample.
CREATE TABLE sample_reviews
(
    sample_id   CHAR(36) PRIMARY KEY,
    reviewed_by BIGINT UNSIGNED NOT NULL,
    reviewed_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    FOREIGN KEY (sample_id) REFERENCES temperature_samples (sample_id),
    FOREIGN KEY (reviewed_by) REFERENCES app_users (user_id)
) ENGINE=InnoDB;
