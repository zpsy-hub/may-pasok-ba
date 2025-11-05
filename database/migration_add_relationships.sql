-- ============================================================================
-- MIGRATION: Add Relationships Between Tables (Safe, No Data Loss)
-- ============================================================================
-- Purpose: Improve data integrity with foreign keys and junction tables
-- Date: 2025-11-05
-- Rollback: See section at bottom
-- ============================================================================

-- BEFORE RUNNING:
-- 1. Backup your database (Supabase Dashboard > Settings > Database > Backup)
-- 2. Test in development environment first
-- 3. This migration is SAFE - it only ADDS constraints, doesn't DELETE data

-- ============================================================================
-- STEP 1: Add Helper Columns (Nullable, Won't Break Existing Data)
-- ============================================================================

-- Add weather_data_id to daily_predictions (optional reference)
-- This allows explicit linking when needed
ALTER TABLE daily_predictions 
ADD COLUMN IF NOT EXISTS weather_data_id UUID;

-- Add pagasa_status_id to daily_predictions (optional reference)
ALTER TABLE daily_predictions 
ADD COLUMN IF NOT EXISTS pagasa_status_id UUID;

-- Add index for performance
CREATE INDEX IF NOT EXISTS idx_predictions_weather_id 
ON daily_predictions(weather_data_id);

CREATE INDEX IF NOT EXISTS idx_predictions_pagasa_id 
ON daily_predictions(pagasa_status_id);

-- ============================================================================
-- STEP 2: Add Foreign Key Constraints (With ON DELETE SET NULL)
-- ============================================================================
-- Using SET NULL means if weather/pagasa record is deleted,
-- prediction stays but reference becomes NULL (preserves predictions)

-- Weather data foreign key (optional relationship)
ALTER TABLE daily_predictions
ADD CONSTRAINT fk_weather_data
FOREIGN KEY (weather_data_id) 
REFERENCES weather_data(id)
ON DELETE SET NULL  -- Don't delete prediction if weather deleted
ON UPDATE CASCADE;

-- PAGASA status foreign key (optional relationship)
ALTER TABLE daily_predictions
ADD CONSTRAINT fk_pagasa_status
FOREIGN KEY (pagasa_status_id) 
REFERENCES pagasa_status(id)
ON DELETE SET NULL  -- Don't delete prediction if PAGASA deleted
ON UPDATE CASCADE;

-- ============================================================================
-- STEP 3: Create Helper Function to Link Existing Records
-- ============================================================================
-- This function will populate the foreign keys for existing predictions
-- by matching on date + LGU

CREATE OR REPLACE FUNCTION link_predictions_to_weather()
RETURNS TABLE(
    predictions_updated INT,
    predictions_with_weather INT,
    predictions_without_weather INT
) AS $$
DECLARE
    updated_count INT := 0;
    with_weather_count INT := 0;
    without_weather_count INT := 0;
BEGIN
    -- Update predictions with matching weather data (forecast type, same date/LGU)
    UPDATE daily_predictions dp
    SET weather_data_id = w.id
    FROM (
        SELECT DISTINCT ON (weather_date, lgu)
            id, weather_date, lgu
        FROM weather_data
        WHERE data_type = 'forecast'
        ORDER BY weather_date, lgu, collected_at DESC  -- Use latest forecast
    ) w
    WHERE dp.prediction_date = w.weather_date
      AND dp.lgu = w.lgu
      AND dp.weather_data_id IS NULL;  -- Only update if not already linked
    
    GET DIAGNOSTICS updated_count = ROW_COUNT;
    
    -- Count predictions with weather link
    SELECT COUNT(*) INTO with_weather_count
    FROM daily_predictions
    WHERE weather_data_id IS NOT NULL;
    
    -- Count predictions without weather link
    SELECT COUNT(*) INTO without_weather_count
    FROM daily_predictions
    WHERE weather_data_id IS NULL;
    
    RETURN QUERY SELECT updated_count, with_weather_count, without_weather_count;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION link_predictions_to_pagasa()
RETURNS TABLE(
    predictions_updated INT,
    predictions_with_pagasa INT,
    predictions_without_pagasa INT
) AS $$
DECLARE
    updated_count INT := 0;
    with_pagasa_count INT := 0;
    without_pagasa_count INT := 0;
BEGIN
    -- Update predictions with matching PAGASA status (same date, latest status)
    UPDATE daily_predictions dp
    SET pagasa_status_id = p.id
    FROM (
        SELECT DISTINCT ON (status_date)
            id, status_date
        FROM pagasa_status
        ORDER BY status_date, collected_at DESC  -- Use latest status for each date
    ) p
    WHERE dp.prediction_date = p.status_date
      AND dp.pagasa_status_id IS NULL;  -- Only update if not already linked
    
    GET DIAGNOSTICS updated_count = ROW_COUNT;
    
    -- Count predictions with PAGASA link
    SELECT COUNT(*) INTO with_pagasa_count
    FROM daily_predictions
    WHERE pagasa_status_id IS NOT NULL;
    
    -- Count predictions without PAGASA link
    SELECT COUNT(*) INTO without_pagasa_count
    FROM daily_predictions
    WHERE pagasa_status_id IS NULL;
    
    RETURN QUERY SELECT updated_count, with_pagasa_count, without_pagasa_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- STEP 4: Run Linking Functions (Execute AFTER migration)
-- ============================================================================
-- Uncomment to link existing records:

-- Link predictions to weather data
-- SELECT * FROM link_predictions_to_weather();

-- Link predictions to PAGASA status
-- SELECT * FROM link_predictions_to_pagasa();

-- ============================================================================
-- STEP 5: Create View for Easy Joined Queries
-- ============================================================================

-- Drop old view if exists
DROP VIEW IF EXISTS prediction_with_context;

-- Create new view with all related data
CREATE OR REPLACE VIEW prediction_with_context AS
SELECT 
    -- Prediction data
    dp.id AS prediction_id,
    dp.prediction_date,
    dp.lgu,
    dp.suspension_probability,
    dp.predicted_suspended,
    dp.actual_suspended,
    dp.prediction_correct,
    dp.model_version,
    dp.threshold_used,
    dp.created_at AS prediction_created_at,
    
    -- Weather data (if linked)
    w.id AS weather_id,
    w.precipitation_sum,
    w.temperature_2m_max,
    w.wind_speed_10m_max,
    w.wind_gusts_10m_max,
    w.relative_humidity_2m_mean,
    w.cloud_cover_max,
    w.pressure_msl_min,
    w.weather_code,
    w.data_type AS weather_data_type,
    
    -- PAGASA data (if linked)
    ps.id AS pagasa_id,
    ps.has_active_typhoon,
    ps.typhoon_name,
    ps.tcws_level,
    ps.has_rainfall_warning,
    ps.rainfall_warning_level,
    ps.metro_manila_affected,
    ps.bulletin_url
    
FROM daily_predictions dp
LEFT JOIN weather_data w ON dp.weather_data_id = w.id
LEFT JOIN pagasa_status ps ON dp.pagasa_status_id = ps.id
ORDER BY dp.prediction_date DESC, dp.lgu;

-- Add comment
COMMENT ON VIEW prediction_with_context IS 
'Complete prediction data with related weather and PAGASA information. 
Uses LEFT JOIN so predictions without links still appear.';

-- ============================================================================
-- STEP 6: Update Application Code Hints
-- ============================================================================

-- New insert pattern (optional - backward compatible)
/*
When inserting predictions, optionally include foreign keys:

INSERT INTO daily_predictions (
    prediction_date, 
    lgu, 
    suspension_probability,
    predicted_suspended,
    model_version,
    threshold_used,
    weather_data_id,  -- NEW: optional
    pagasa_status_id  -- NEW: optional
) VALUES (
    '2025-11-06',
    'Manila',
    0.75,
    true,
    'v1.0.0',
    0.5,
    (SELECT id FROM weather_data 
     WHERE weather_date = '2025-11-06' 
       AND lgu = 'Manila' 
       AND data_type = 'forecast' 
     ORDER BY collected_at DESC 
     LIMIT 1),  -- Get latest forecast
    (SELECT id FROM pagasa_status 
     WHERE status_date = '2025-11-06' 
     ORDER BY collected_at DESC 
     LIMIT 1)   -- Get latest status
);

Or use the existing pattern (still works):

INSERT INTO daily_predictions (
    prediction_date, 
    lgu, 
    suspension_probability,
    predicted_suspended,
    model_version,
    threshold_used
) VALUES (...);  -- Foreign keys will be NULL (still valid)
*/

-- ============================================================================
-- STEP 7: Verification Queries
-- ============================================================================

-- Check how many predictions have weather links
SELECT 
    'Predictions with weather' AS category,
    COUNT(*) AS count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM daily_predictions), 2) AS percentage
FROM daily_predictions
WHERE weather_data_id IS NOT NULL

UNION ALL

SELECT 
    'Predictions without weather',
    COUNT(*),
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM daily_predictions), 2)
FROM daily_predictions
WHERE weather_data_id IS NULL;

-- Check how many predictions have PAGASA links
SELECT 
    'Predictions with PAGASA' AS category,
    COUNT(*) AS count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM daily_predictions), 2) AS percentage
FROM pagasa_status
WHERE pagasa_status_id IS NOT NULL

UNION ALL

SELECT 
    'Predictions without PAGASA',
    COUNT(*),
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM daily_predictions), 2)
FROM daily_predictions
WHERE pagasa_status_id IS NULL;

-- Test the new view
SELECT * FROM prediction_with_context LIMIT 5;

-- ============================================================================
-- ROLLBACK SCRIPT (If Something Goes Wrong)
-- ============================================================================

/*
-- Rollback Step 1: Remove foreign key constraints
ALTER TABLE daily_predictions DROP CONSTRAINT IF EXISTS fk_weather_data;
ALTER TABLE daily_predictions DROP CONSTRAINT IF EXISTS fk_pagasa_status;

-- Rollback Step 2: Drop indexes
DROP INDEX IF EXISTS idx_predictions_weather_id;
DROP INDEX IF EXISTS idx_predictions_pagasa_id;

-- Rollback Step 3: Remove columns (WARNING: This deletes the link data)
-- Only run if you want to completely undo the migration
-- ALTER TABLE daily_predictions DROP COLUMN IF EXISTS weather_data_id;
-- ALTER TABLE daily_predictions DROP COLUMN IF EXISTS pagasa_status_id;

-- Rollback Step 4: Drop helper functions
DROP FUNCTION IF EXISTS link_predictions_to_weather();
DROP FUNCTION IF EXISTS link_predictions_to_pagasa();

-- Rollback Step 5: Drop view
DROP VIEW IF EXISTS prediction_with_context;

-- Verify rollback
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'daily_predictions';
*/

-- ============================================================================
-- SUMMARY
-- ============================================================================
/*
What this migration does:
✅ Adds optional foreign key columns (weather_data_id, pagasa_status_id)
✅ Creates foreign key constraints with ON DELETE SET NULL (safe)
✅ Provides helper functions to link existing records
✅ Creates view for easy querying with joins
✅ Fully backward compatible (existing code still works)
✅ Zero data loss (all constraints are nullable)
✅ Can be rolled back completely

What this migration DOES NOT do:
❌ Does NOT delete any existing data
❌ Does NOT require changes to existing code (backward compatible)
❌ Does NOT break existing UPSERT operations
❌ Does NOT enforce mandatory relationships (all nullable)

Next steps:
1. Backup database
2. Run this migration script in Supabase SQL Editor
3. Execute link functions to populate foreign keys for existing data
4. Update supabase_client.py to optionally set foreign keys on insert
5. Update thesis ER diagram to show these relationships
*/
