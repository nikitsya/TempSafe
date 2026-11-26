CREATE TABLE push_subscriptions (
    endpoint_id CHAR(64) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY,
    user_id BIGINT UNSIGNED NOT NULL,
    endpoint TEXT NOT NULL,
    p256dh VARCHAR(100) NOT NULL,
    auth_secret VARCHAR(32) NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    FOREIGN KEY (user_id) REFERENCES app_users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE push_box_state (
    box_id VARCHAR(64) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY,
    sequence_no BIGINT UNSIGNED NOT NULL,
    observed_at DATETIME(6) NOT NULL,
    state ENUM('Normal','Warning','Alert') NOT NULL,
    episode_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    FOREIGN KEY (box_id) REFERENCES boxes(box_id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE push_deliveries (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    sample_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    endpoint_id CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    state ENUM('Warning','Alert') NOT NULL,
    status ENUM('pending','accepted','failed','cancelled') NOT NULL DEFAULT 'pending',
    attempts INT UNSIGNED NOT NULL DEFAULT 0,
    next_attempt DATETIME(6) NOT NULL,
    http_status INT NULL,
    UNIQUE KEY uq_push_event (sample_id, endpoint_id),
    KEY ix_push_pending (status, next_attempt),
    FOREIGN KEY (sample_id) REFERENCES temperature_samples(sample_id) ON DELETE CASCADE,
    FOREIGN KEY (endpoint_id) REFERENCES push_subscriptions(endpoint_id) ON DELETE CASCADE
) ENGINE=InnoDB;
