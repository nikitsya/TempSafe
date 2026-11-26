-- Run as an administrator against the hosted temsafe schema.
-- Create the dedicated runtime account with a generated password first.
GRANT SELECT ON temsafe.app_users TO 'tempsafe_runtime'@'%';
GRANT SELECT ON temsafe.box_access TO 'tempsafe_runtime'@'%';
GRANT SELECT, INSERT, DELETE ON temsafe.user_sessions TO 'tempsafe_runtime'@'%';
-- SELECT FOR UPDATE serialises concurrent profile changes.
GRANT SELECT, UPDATE (name) ON temsafe.boxes TO 'tempsafe_runtime'@'%';
GRANT SELECT, INSERT ON temsafe.temperature_samples TO 'tempsafe_runtime'@'%';
GRANT SELECT, INSERT ON temsafe.threshold_profiles TO 'tempsafe_runtime'@'%';
GRANT SELECT, INSERT, UPDATE (profile_id, applied_profile_id) ON temsafe.box_configuration TO 'tempsafe_runtime'@'%';
