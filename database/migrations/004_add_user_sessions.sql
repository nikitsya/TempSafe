CREATE TABLE user_sessions
(
    token_hash CHAR(64) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY,
    user_id    BIGINT UNSIGNED NOT NULL,
    expires_at DATETIME(6) NOT NULL,
    INDEX      ix_session_expiry (expires_at),
    FOREIGN KEY (user_id) REFERENCES app_users (user_id) ON DELETE CASCADE
) ENGINE = InnoDB;
