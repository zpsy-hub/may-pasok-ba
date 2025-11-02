-- ============================================================================
-- SUSPENSION PREDICTION DATABASE SCHEMA (Supabase/PostgreSQL)
-- ============================================================================
-- Purpose: Log predictions, weather data, and PAGASA status for analysis
-- Deployment: GitHub Actions → Supabase (free tier)
-- ============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- TABLE 1: Daily Predictions
-- ============================================================================
-- Stores model predictions for each LGU each day
CREATE TABLE daily_predictions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Date and LGU
    prediction_date DATE NOT NULL,
    lgu TEXT NOT NULL,
    
    -- Model predictions
    suspension_probability DECIMAL(5, 4) NOT NULL,  -- 0.0000 to 1.0000
    predicted_suspended BOOLEAN NOT NULL,
    model_version TEXT NOT NULL,
    threshold_used DECIMAL(5, 4) NOT NULL,
    
    -- Actual outcome (filled in later)
    actual_suspended BOOLEAN DEFAULT NULL,
    prediction_correct BOOLEAN DEFAULT NULL,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    github_run_id TEXT,  -- GitHub Actions run ID for tracking
    
    -- Constraints
    CONSTRAINT unique_prediction_per_day_lgu UNIQUE (prediction_date, lgu),
    CONSTRAINT valid_probability CHECK (suspension_probability >= 0 AND suspension_probability <= 1),
    CONSTRAINT valid_threshold CHECK (threshold_used >= 0 AND threshold_used <= 1)
);

-- Indexes for fast queries
CREATE INDEX idx_predictions_date ON daily_predictions(prediction_date DESC);
CREATE INDEX idx_predictions_lgu ON daily_predictions(lgu);
CREATE INDEX idx_predictions_date_lgu ON daily_predictions(prediction_date DESC, lgu);
CREATE INDEX idx_predictions_actual ON daily_predictions(actual_suspended) WHERE actual_suspended IS NOT NULL;

-- ============================================================================
-- TABLE 2: Weather Data (Open-Meteo)
-- ============================================================================
-- Stores weather forecasts and observations
CREATE TABLE weather_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Date and location
    weather_date DATE NOT NULL,
    lgu TEXT NOT NULL,
    data_type TEXT NOT NULL,  -- 'forecast' or 'actual'
    
    -- Weather variables
    precipitation_sum DECIMAL(6, 2),  -- mm
    temperature_2m_max DECIMAL(4, 1),  -- °C
    wind_speed_10m_max DECIMAL(5, 1),  -- km/h
    wind_gusts_10m_max DECIMAL(5, 1),  -- km/h
    relative_humidity_2m_mean DECIMAL(4, 1),  -- %
    cloud_cover_max DECIMAL(4, 1),  -- %
    pressure_msl_min DECIMAL(6, 1),  -- hPa
    weather_code INTEGER,  -- WMO code
    
    -- Additional forecast-specific fields
    precipitation_probability_max DECIMAL(4, 1),  -- % (forecast only)
    
    -- Metadata
    collected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    source TEXT DEFAULT 'open-meteo',
    
    -- Constraints
    CONSTRAINT unique_weather_per_day_lgu_type UNIQUE (weather_date, lgu, data_type),
    CONSTRAINT valid_data_type CHECK (data_type IN ('forecast', 'actual'))
);

-- Indexes
CREATE INDEX idx_weather_date ON weather_data(weather_date DESC);
CREATE INDEX idx_weather_lgu ON weather_data(lgu);
CREATE INDEX idx_weather_date_type ON weather_data(weather_date DESC, data_type);

-- ============================================================================
-- TABLE 3: PAGASA Status
-- ============================================================================
-- Stores PAGASA typhoon and rainfall data
CREATE TABLE pagasa_status (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Date and time
    status_date DATE NOT NULL,
    status_time TIME NOT NULL,
    
    -- Typhoon information
    has_active_typhoon BOOLEAN NOT NULL,
    typhoon_name TEXT,
    typhoon_status TEXT,  -- 'ACTIVE', 'PASSING', etc.
    bulletin_number INTEGER,
    bulletin_age TEXT,  -- e.g., "8.5 hours ago"
    
    -- Metro Manila impact
    metro_manila_affected BOOLEAN NOT NULL,
    tcws_level INTEGER NOT NULL DEFAULT 0,  -- 0-5
    
    -- Rainfall warning
    has_rainfall_warning BOOLEAN NOT NULL,
    rainfall_warning_level TEXT,  -- 'RED', 'ORANGE', 'YELLOW'
    metro_manila_rainfall_status TEXT,  -- e.g., "ORANGE WARNING"
    
    -- Metadata
    collected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    bulletin_url TEXT,
    
    -- Constraints
    CONSTRAINT valid_tcws_level CHECK (tcws_level >= 0 AND tcws_level <= 5),
    CONSTRAINT valid_rainfall_level CHECK (
        rainfall_warning_level IS NULL OR 
        rainfall_warning_level IN ('RED', 'ORANGE', 'YELLOW')
    )
);

-- Indexes
CREATE INDEX idx_pagasa_date ON pagasa_status(status_date DESC);
CREATE INDEX idx_pagasa_datetime ON pagasa_status(status_date DESC, status_time DESC);
CREATE INDEX idx_pagasa_tcws ON pagasa_status(tcws_level) WHERE tcws_level > 0;
CREATE INDEX idx_pagasa_typhoon ON pagasa_status(has_active_typhoon) WHERE has_active_typhoon = TRUE;

-- ============================================================================
-- TABLE 4: Collection Logs
-- ============================================================================
-- Tracks GitHub Actions runs and data collection status
CREATE TABLE collection_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Run information
    run_date DATE NOT NULL,
    run_time TIME NOT NULL,
    github_run_id TEXT,
    github_workflow TEXT DEFAULT 'deploy.yml',
    
    -- Collection status
    pagasa_collection_success BOOLEAN NOT NULL,
    pagasa_error TEXT,
    
    openmeteo_collection_success BOOLEAN NOT NULL,
    openmeteo_records_collected INTEGER,
    openmeteo_error TEXT,
    
    predictions_generated BOOLEAN NOT NULL,
    predictions_count INTEGER,
    predictions_error TEXT,
    
    -- Performance
    total_duration_seconds INTEGER,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_logs_date ON collection_logs(run_date DESC);
CREATE INDEX idx_logs_datetime ON collection_logs(run_date DESC, run_time DESC);
CREATE INDEX idx_logs_status ON collection_logs(
    pagasa_collection_success, 
    openmeteo_collection_success, 
    predictions_generated
);

-- ============================================================================
-- TABLE 5: Model Metadata
-- ============================================================================
-- Tracks model versions and performance
CREATE TABLE model_metadata (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Model information
    model_version TEXT NOT NULL UNIQUE,
    model_name TEXT NOT NULL,  -- e.g., 'EasyEnsemble', 'RandomForest'
    training_date DATE NOT NULL,
    
    -- Performance metrics
    validation_accuracy DECIMAL(5, 4),
    validation_precision DECIMAL(5, 4),
    validation_recall DECIMAL(5, 4),
    validation_f1 DECIMAL(5, 4),
    validation_auc DECIMAL(5, 4),
    
    optimal_threshold DECIMAL(5, 4),
    
    -- Feature importance (JSON)
    feature_importance JSONB,
    
    -- Training details (JSON)
    hyperparameters JSONB,
    training_samples INTEGER,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    deployed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    notes TEXT
);

-- Index
CREATE INDEX idx_model_active ON model_metadata(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_model_version ON model_metadata(model_version);

-- ============================================================================
-- VIEWS FOR ANALYTICS
-- ============================================================================

-- View 1: Daily prediction accuracy by LGU
CREATE OR REPLACE VIEW prediction_accuracy_by_lgu AS
SELECT 
    lgu,
    COUNT(*) as total_predictions,
    COUNT(CASE WHEN prediction_correct = TRUE THEN 1 END) as correct_predictions,
    ROUND(
        COUNT(CASE WHEN prediction_correct = TRUE THEN 1 END)::DECIMAL / 
        NULLIF(COUNT(CASE WHEN actual_suspended IS NOT NULL THEN 1 END), 0) * 100,
        2
    ) as accuracy_percentage,
    AVG(suspension_probability) as avg_probability
FROM daily_predictions
WHERE actual_suspended IS NOT NULL
GROUP BY lgu
ORDER BY accuracy_percentage DESC;

-- View 2: Weather correlation with suspensions
CREATE OR REPLACE VIEW weather_suspension_correlation AS
SELECT 
    w.weather_date,
    COUNT(DISTINCT p.lgu) as lgus_suspended,
    AVG(w.precipitation_sum) as avg_precipitation,
    AVG(w.wind_speed_10m_max) as avg_wind_speed,
    MAX(w.precipitation_sum) as max_precipitation,
    MAX(w.wind_speed_10m_max) as max_wind_speed
FROM weather_data w
LEFT JOIN daily_predictions p 
    ON w.weather_date = p.prediction_date 
    AND w.lgu = p.lgu 
    AND p.actual_suspended = TRUE
    AND w.data_type = 'actual'
GROUP BY w.weather_date
ORDER BY w.weather_date DESC;

-- View 3: PAGASA impact analysis
CREATE OR REPLACE VIEW pagasa_impact_analysis AS
SELECT 
    ps.status_date,
    ps.has_active_typhoon,
    ps.tcws_level,
    ps.has_rainfall_warning,
    COUNT(DISTINCT p.lgu) as lgus_suspended,
    ROUND(AVG(p.suspension_probability) * 100, 2) as avg_suspension_probability
FROM pagasa_status ps
LEFT JOIN daily_predictions p ON ps.status_date = p.prediction_date
WHERE p.actual_suspended = TRUE
GROUP BY ps.status_date, ps.has_active_typhoon, ps.tcws_level, ps.has_rainfall_warning
ORDER BY ps.status_date DESC;

-- View 4: Collection reliability
CREATE OR REPLACE VIEW collection_reliability AS
SELECT 
    DATE_TRUNC('day', run_date) as date,
    COUNT(*) as total_runs,
    COUNT(CASE WHEN pagasa_collection_success THEN 1 END) as pagasa_success_count,
    COUNT(CASE WHEN openmeteo_collection_success THEN 1 END) as openmeteo_success_count,
    COUNT(CASE WHEN predictions_generated THEN 1 END) as predictions_success_count,
    ROUND(AVG(total_duration_seconds), 2) as avg_duration_seconds
FROM collection_logs
GROUP BY DATE_TRUNC('day', run_date)
ORDER BY date DESC;

-- ============================================================================
-- FUNCTIONS
-- ============================================================================

-- Function to update prediction accuracy when actual outcome is recorded
CREATE OR REPLACE FUNCTION update_prediction_accuracy()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.actual_suspended IS NOT NULL AND OLD.actual_suspended IS NULL THEN
        NEW.prediction_correct := (NEW.predicted_suspended = NEW.actual_suspended);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update prediction_correct
CREATE TRIGGER trg_update_prediction_accuracy
    BEFORE UPDATE ON daily_predictions
    FOR EACH ROW
    EXECUTE FUNCTION update_prediction_accuracy();

-- ============================================================================
-- ROW LEVEL SECURITY (Optional - for public read access)
-- ============================================================================

-- Enable RLS
ALTER TABLE daily_predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE weather_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE pagasa_status ENABLE ROW LEVEL SECURITY;
ALTER TABLE collection_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE model_metadata ENABLE ROW LEVEL SECURITY;

-- Public read access (for GitHub Pages dashboard)
CREATE POLICY "Public read access" ON daily_predictions FOR SELECT USING (true);
CREATE POLICY "Public read access" ON weather_data FOR SELECT USING (true);
CREATE POLICY "Public read access" ON pagasa_status FOR SELECT USING (true);
CREATE POLICY "Public read access" ON collection_logs FOR SELECT USING (true);
CREATE POLICY "Public read access" ON model_metadata FOR SELECT USING (true);

-- Service role write access (for GitHub Actions with service key)
-- Note: service_role bypasses RLS by default, but we define policies for clarity
CREATE POLICY "Service role write access" ON daily_predictions FOR INSERT 
    WITH CHECK (true);
CREATE POLICY "Service role update access" ON daily_predictions FOR UPDATE 
    USING (true) WITH CHECK (true);

CREATE POLICY "Service role write access" ON weather_data FOR INSERT 
    WITH CHECK (true);

CREATE POLICY "Service role write access" ON pagasa_status FOR INSERT 
    WITH CHECK (true);

CREATE POLICY "Service role write access" ON collection_logs FOR INSERT 
    WITH CHECK (true);

CREATE POLICY "Service role write access" ON model_metadata FOR INSERT 
    WITH CHECK (true);

-- ============================================================================
-- SAMPLE QUERIES
-- ============================================================================

/*
-- Get latest predictions
SELECT * FROM daily_predictions 
WHERE prediction_date = CURRENT_DATE 
ORDER BY suspension_probability DESC;

-- Get today's weather
SELECT * FROM weather_data 
WHERE weather_date = CURRENT_DATE AND data_type = 'forecast';

-- Get active typhoon status
SELECT * FROM pagasa_status 
WHERE has_active_typhoon = TRUE 
ORDER BY collected_at DESC LIMIT 1;

-- Check collection success rate
SELECT * FROM collection_reliability 
WHERE date >= CURRENT_DATE - INTERVAL '7 days';

-- LGU prediction accuracy
SELECT * FROM prediction_accuracy_by_lgu;
*/

-- ============================================================================
-- NOTES
-- ============================================================================
-- 1. Run this script in Supabase SQL Editor
-- 2. Save service_role key in GitHub Secrets as SUPABASE_KEY
-- 3. Save project URL in GitHub Secrets as SUPABASE_URL
-- 4. Use Python supabase-py client for insertions
-- 5. Tables auto-create indexes for foreign keys
-- 6. UUIDs provide global uniqueness
-- 7. TIMESTAMP WITH TIME ZONE for proper timezone handling
-- 8. Row Level Security allows public dashboard access
-- ============================================================================
