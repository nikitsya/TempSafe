-- Upgrade existing MySQL 8.4 installations, including those predating migration 005.
-- Build one ALTER statement from the legacy objects present in the selected database.
SET @box_changes = CONCAT_WS(', ',
    (SELECT 'DROP CHECK ck_box_heartbeat_interval' FROM information_schema.TABLE_CONSTRAINTS
     WHERE CONSTRAINT_SCHEMA = DATABASE() AND TABLE_NAME = 'boxes'
       AND CONSTRAINT_NAME = 'ck_box_heartbeat_interval' AND CONSTRAINT_TYPE = 'CHECK'),
    (SELECT 'DROP COLUMN heartbeat_interval_seconds' FROM information_schema.COLUMNS
     WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'boxes' AND COLUMN_NAME = 'heartbeat_interval_seconds'),
    (SELECT 'DROP COLUMN last_seen_at' FROM information_schema.COLUMNS
     WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'boxes' AND COLUMN_NAME = 'last_seen_at')
);
SET @box_upgrade = IF(@box_changes = '', 'SELECT 1', CONCAT('ALTER TABLE boxes ', @box_changes));
PREPARE box_upgrade FROM @box_upgrade;
EXECUTE box_upgrade;
DEALLOCATE PREPARE box_upgrade;
