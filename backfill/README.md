# Historical Data Backfill (Sept-Oct 2025)

## Overview
This folder contains scripts to collect and process historical weather data, generate predictions for September-October 2025, and upload them to the Supabase database for dashboard visualization.

## Purpose
The dashboard needs historical data to:
1. Show prediction accuracy (how well the model performed in past)
2. Display weather correlation analysis (rainfall vs suspensions)
3. Demonstrate PAGASA impact (typhoon warnings effect)
4. Compare LGU suspension patterns over time

## Folder Structure
```
backfill/
├── README.md                           # This file
├── config.json                         # Configuration (date ranges, LGU list)
├── output/                             # Generated data files
│   ├── weather_sept_oct.json          # Historical weather from Open-Meteo
│   ├── pagasa_sept_oct.json           # Historical PAGASA bulletins
│   ├── features_sept_oct.json         # Engineered features
│   └── predictions_sept_oct.json      # Model predictions
├── collect_historical_weather.py      # Step 1: Fetch weather data
├── collect_historical_pagasa.py       # Step 2: Fetch PAGASA data
├── engineer_features.py               # Step 3: Generate 33 features
├── generate_predictions.py            # Step 4: Run model predictions
├── upload_to_database.py              # Step 5: Insert to Supabase
└── validate_data.py                   # Validate data integrity
```

## Workflow

### Step 1: Collect Historical Weather
```bash
python backfill/collect_historical_weather.py
```
- Fetches Sept 1 - Oct 31, 2025 weather for all 17 Metro Manila LGUs
- Uses Open-Meteo Historical Weather API (archive endpoint)
- Rate limited to 1 req/sec (avoid throttling)
- Output: `output/weather_sept_oct.json`

### Step 2: Collect Historical PAGASA Data
```bash
python backfill/collect_historical_pagasa.py
```
- Attempts to fetch historical typhoon bulletins for Sept-Oct 2025
- May require manual data entry (historical bulletins not always available)
- Extracts: typhoon name, TCWS level, rainfall warnings
- Output: `output/pagasa_sept_oct.json`

### Step 3: Engineer Features
```bash
python backfill/engineer_features.py
```
- Loads weather + PAGASA data from output/
- Generates same 33 features as production pipeline
- Properly handles historical aggregates (t-1, t-7 day windows)
- Output: `output/features_sept_oct.json`

### Step 4: Generate Predictions
```bash
python backfill/generate_predictions.py
```
- Loads trained model: `model-training/data/processed/best_core_model.pkl`
- Generates predictions for 61 days × 17 LGUs = 1,037 predictions
- Uses production threshold (0.5)
- Output: `output/predictions_sept_oct.json`

### Step 5: Validate Data
```bash
python backfill/validate_data.py
```
- Checks for missing dates (should have 1,037 records)
- Validates probability ranges (0.0-1.0)
- Verifies feature calculations
- Output: `validation_report.txt`

### Step 6: Upload to Database
```bash
# Set environment variables first
export SUPABASE_URL="https://xxxxx.supabase.co"
export SUPABASE_KEY="eyJhbG..."

python backfill/upload_to_database.py
```
- Bulk inserts to: daily_predictions, weather_data, pagasa_status
- Handles duplicates (upsert on unique constraints)
- Creates collection_logs entry for backfill
- Logs success/failure counts

## Data Format

### weather_sept_oct.json
```json
{
  "2025-09-01": {
    "Manila": {
      "precipitation_sum": 12.5,
      "temperature_max": 32.1,
      "wind_speed_max": 18.3,
      ...
    },
    "Quezon City": { ... }
  },
  "2025-09-02": { ... }
}
```

### pagasa_sept_oct.json
```json
{
  "2025-09-01": {
    "has_active_typhoon": false,
    "tcws_level": 0,
    "has_rainfall_warning": false
  },
  "2025-09-15": {
    "has_active_typhoon": true,
    "typhoon_name": "JULIAN",
    "tcws_level": 2,
    "metro_manila_affected": true,
    "has_rainfall_warning": true,
    "rainfall_warning_level": "ORANGE"
  }
}
```

### predictions_sept_oct.json
```json
[
  {
    "prediction_date": "2025-09-01",
    "lgu": "Manila",
    "suspension_probability": 0.0234,
    "predicted_suspended": false,
    "model_version": "v1.0.0"
  },
  ...
]
```

## Configuration (config.json)

```json
{
  "date_range": {
    "start": "2025-09-01",
    "end": "2025-10-31"
  },
  "lgus": [
    "Manila", "Quezon City", "Caloocan", "Las Piñas", "Makati",
    "Malabon", "Mandaluyong", "Marikina", "Muntinlupa", "Navotas",
    "Parañaque", "Pasay", "Pasig", "Pateros", "San Juan",
    "Taguig", "Valenzuela"
  ],
  "lgu_coordinates": {
    "Manila": {"lat": 14.5995, "lon": 120.9842},
    ...
  },
  "open_meteo": {
    "base_url": "https://archive-api.open-meteo.com/v1/archive",
    "variables": [
      "temperature_2m_max",
      "precipitation_sum",
      "wind_speed_10m_max",
      "wind_gusts_10m_max",
      "relative_humidity_2m_mean",
      "cloud_cover_max",
      "pressure_msl_min",
      "weather_code"
    ],
    "rate_limit_seconds": 1
  },
  "model": {
    "path": "../model-training/data/processed/best_core_model.pkl",
    "version": "v1.0.0",
    "threshold": 0.5
  }
}
```

## Notes

### Open-Meteo Historical API
- Free tier: Up to 10,000 requests/day
- Rate limit: 1 request/second recommended
- Historical data available from 1940 onwards
- No API key required

### PAGASA Historical Data
- Official bulletins may not be systematically archived
- Manual data entry may be needed for certain dates
- Alternative: Use DepEd suspension announcements as ground truth
- Consider Twitter/social media archives for typhoon dates

### Database Constraints
- `daily_predictions`: UNIQUE (prediction_date, lgu)
- `weather_data`: UNIQUE (weather_date, lgu, data_type)
- `pagasa_status`: No unique constraint (multiple bulletins per day OK)
- Use UPSERT (ON CONFLICT UPDATE) to avoid duplicate errors

### Performance
- Weather collection: ~17 LGUs × 61 days = 1,037 API calls ≈ 17 minutes
- Feature engineering: ~5-10 seconds
- Prediction generation: ~1-2 seconds
- Database upload: ~5-10 seconds (bulk insert)
- **Total time: ~20-25 minutes**

## Troubleshooting

### Open-Meteo API errors
- Error 429 (Too Many Requests): Increase rate_limit_seconds in config.json
- Error 503 (Service Unavailable): Retry after 5 minutes
- Missing data for certain dates: Check if date is in future or before 1940

### Feature engineering errors
- Missing historical data (t-1, t-7): Use forward fill or defaults
- Date parsing issues: Ensure all dates are ISO format (YYYY-MM-DD)
- NaN values: Replace with median or mode from available data

### Database upload errors
- Duplicate key violations: Script should handle with UPSERT
- Connection timeout: Check SUPABASE_URL and SUPABASE_KEY
- RLS (Row Level Security) errors: Use service_role key, not anon key

## Next Steps After Backfill

1. **Dashboard API**: Create web/api/get_historical_predictions.py endpoint
2. **Frontend Integration**: Modify web/index.html to fetch historical data
3. **Visualizations**: Add Chart.js plots for accuracy, correlation, PAGASA impact
4. **LGU Comparison**: Build heatmap showing suspension patterns
5. **Testing**: Write pytest tests for backfill scripts

## References
- Open-Meteo Archive API: https://open-meteo.com/en/docs/historical-weather-api
- PAGASA Website: https://www.pagasa.dost.gov.ph/
- Supabase Docs: https://supabase.com/docs
