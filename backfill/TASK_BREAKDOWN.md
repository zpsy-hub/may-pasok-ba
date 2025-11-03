# Historical Data Backfill - Task Breakdown

## 📋 Overview
You need to populate the database with Sept 1 - Oct 31, 2025 data so the dashboard can show:
- ✅ Historical predictions with accuracy metrics
- ✅ Weather correlation analysis (rainfall vs suspensions)
- ✅ PAGASA impact analysis (typhoon warnings effect)
- ✅ LGU breakdown and comparison

---

## 📂 Folder Structure Created

```
backfill/
├── README.md                           # Complete documentation ✅ CREATED
├── config.json                         # Configuration settings ✅ CREATED
├── output/                             # Generated data files (empty for now)
│   ├── weather_sept_oct.json          # TODO: Generate in Step 1
│   ├── pagasa_sept_oct.json           # TODO: Generate in Step 2
│   ├── features_sept_oct.json         # TODO: Generate in Step 3
│   └── predictions_sept_oct.json      # TODO: Generate in Step 4
├── collect_historical_weather.py      # TODO: Create
├── collect_historical_pagasa.py       # TODO: Create
├── engineer_features.py               # TODO: Create
├── generate_predictions.py            # TODO: Create
├── upload_to_database.py              # TODO: Create
└── validate_data.py                   # TODO: Create
```

---

## 🎯 Tasks Breakdown (In Order)

### **Phase 1: Data Collection** (Tasks 4-6)

#### ✅ Task 4: Create folder structure
**Status**: COMPLETED
**Output**: 
- `backfill/` folder with `output/` subfolder
- `README.md` with full documentation
- `config.json` with settings

---

#### 🔲 Task 5: Build historical weather data collector
**Script**: `backfill/collect_historical_weather.py`
**What it does**:
1. Reads date range from `config.json` (Sept 1 - Oct 31, 2025)
2. Loops through each date and each LGU (17 LGUs × 61 days = 1,037 API calls)
3. Calls Open-Meteo Archive API: `https://archive-api.open-meteo.com/v1/archive`
4. Fetches: precipitation, temperature, wind, humidity, pressure, weather_code
5. Rate limits to 1 request/second (avoid throttling)
6. Saves to `output/weather_sept_oct.json`

**Output format**:
```json
{
  "2025-09-01": {
    "Manila": {
      "precipitation_sum": 12.5,
      "temperature_2m_max": 32.1,
      "temperature_2m_min": 24.3,
      "wind_speed_10m_max": 18.3,
      "wind_gusts_10m_max": 35.2,
      "relative_humidity_2m_mean": 78.5,
      "cloud_cover_max": 85.0,
      "pressure_msl_min": 1008.2,
      "weather_code": 61
    },
    "Quezon City": { ... }
  },
  "2025-09-02": { ... }
}
```

**Estimated time**: ~20 minutes (1,037 requests × 1 second + processing)

---

#### 🔲 Task 6: Build historical PAGASA data collector
**Script**: `backfill/collect_historical_pagasa.py`
**What it does**:
1. Attempts to scrape/fetch historical PAGASA bulletins for Sept-Oct 2025
2. **Challenge**: Historical bulletins may not be systematically available
3. **Fallback option**: Manual data entry based on known typhoons (check `config.json` for known_typhoons)
4. For each date, extract:
   - Typhoon status (name, TCWS level, Metro Manila affected)
   - Rainfall warnings (RED/ORANGE/YELLOW)
5. Saves to `output/pagasa_sept_oct.json`

**Output format**:
```json
{
  "2025-09-01": {
    "has_active_typhoon": false,
    "tcws_level": 0,
    "has_rainfall_warning": false
  },
  "2025-09-22": {
    "has_active_typhoon": true,
    "typhoon_name": "JULIAN",
    "typhoon_status": "ACTIVE",
    "metro_manila_affected": true,
    "tcws_level": 2,
    "has_rainfall_warning": true,
    "rainfall_warning_level": "ORANGE"
  }
}
```

**Estimated time**: 30 minutes - 2 hours (depending on data availability)
**Note**: If historical data unavailable, default to `has_active_typhoon: false` for most dates

---

### **Phase 2: Feature Engineering & Prediction** (Tasks 7-8)

#### 🔲 Task 7: Build feature engineering pipeline
**Script**: `backfill/engineer_features.py`
**What it does**:
1. Loads `weather_sept_oct.json` and `pagasa_sept_oct.json`
2. For each date and LGU, generates **33 features** (same as production):
   - **Temporal**: year, month, day, day_of_week, is_rainy_season, month_from_sy_start, is_holiday, is_school_day
   - **LGU**: lgu_id (0-16 mapping)
   - **Flood risk**: mean_flood_risk_score (default 0.5)
   - **Historical weather (t-1 day)**: hist_precipitation_sum_t1, hist_wind_speed_max_t1, etc.
   - **Historical aggregates**: hist_precip_sum_7d, hist_precip_sum_3d, hist_wind_max_7d
   - **Forecast features**: fcst_precipitation_sum, fcst_wind_speed_max, etc. (use actual data for backfill)
3. Handles missing data with defaults
4. Saves to `output/features_sept_oct.json`

**Output format**:
```json
[
  {
    "date": "2025-09-01",
    "lgu": "Manila",
    "features": {
      "year": 2025,
      "month": 9,
      "day": 1,
      "day_of_week": 0,
      "is_rainy_season": 1,
      "lgu_id": 0,
      "hist_precipitation_sum_t1": 5.2,
      "fcst_precipitation_sum": 12.5,
      ...
    }
  },
  ...
]
```

**Estimated time**: 5-10 minutes

---

#### 🔲 Task 8: Generate historical predictions
**Script**: `backfill/generate_predictions.py`
**What it does**:
1. Loads trained model: `model-training/data/processed/best_core_model.pkl`
2. Loads features from `output/features_sept_oct.json`
3. For each date/LGU combination (1,037 total):
   - Converts features to model input format (33-feature vector)
   - Runs `model.predict_proba(X)` to get suspension probability
   - Applies threshold (0.5) to get binary prediction
4. Saves to `output/predictions_sept_oct.json`

**Output format**:
```json
[
  {
    "prediction_date": "2025-09-01",
    "lgu": "Manila",
    "suspension_probability": 0.0234,
    "predicted_suspended": false,
    "model_version": "v1.0.0",
    "threshold_used": 0.5
  },
  ...
]
```

**Estimated time**: 1-2 minutes

---

### **Phase 3: Validation & Upload** (Tasks 9, 15)

#### 🔲 Task 15: Validate data integrity (do this BEFORE uploading!)
**Script**: `backfill/validate_data.py`
**What it does**:
1. Checks for missing dates (should have 61 days × 17 LGUs = 1,037 records)
2. Validates probability ranges (0.0 ≤ prob ≤ 1.0)
3. Checks for null/invalid weather values
4. Verifies feature engineering correctness (sample random dates)
5. Compares output format to production `web/predictions/latest.json`
6. Generates `validation_report.txt` with pass/fail status

**Output**: Console output + `validation_report.txt`

**Estimated time**: 2-3 minutes

---

#### 🔲 Task 9: Backfill to Supabase database
**Script**: `backfill/upload_to_database.py`
**What it does**:
1. Connects to Supabase using `database/supabase_client.py`
2. Loads all 3 JSON files from `output/`
3. Bulk inserts to 3 tables:
   - **daily_predictions**: 1,037 records
   - **weather_data**: 1,037 records (data_type='actual')
   - **pagasa_status**: 61 records (1 per day)
4. Uses UPSERT (ON CONFLICT DO UPDATE) to handle duplicates
5. Creates entry in **collection_logs** for tracking
6. Prints success/failure counts

**Command**:
```bash
# Set environment variables
export SUPABASE_URL="https://xxxxx.supabase.co"
export SUPABASE_KEY="your_service_role_key"

# Run upload
python backfill/upload_to_database.py
```

**Estimated time**: 5-10 seconds

---

### **Phase 4: Dashboard Integration** (Tasks 10-14)

#### 🔲 Task 10: Build dashboard API endpoint
**Script**: `web/api/get_historical_predictions.py` (Flask/FastAPI)
**What it does**:
1. Creates REST API endpoint: `GET /api/historical-predictions`
2. Query params: `start_date`, `end_date`, `lgu` (optional)
3. Fetches from Supabase with JOINs:
   ```sql
   SELECT p.*, w.*, ps.*
   FROM daily_predictions p
   LEFT JOIN weather_data w ON p.prediction_date = w.weather_date AND p.lgu = w.lgu
   LEFT JOIN pagasa_status ps ON p.prediction_date = ps.status_date
   WHERE p.prediction_date BETWEEN start_date AND end_date
   ```
4. Returns JSON array of predictions with nested weather/pagasa data
5. Enables CORS for GitHub Pages
6. Rate limits to 100 req/min

**Estimated time**: 30-45 minutes

---

#### 🔲 Task 11: Update dashboard to fetch historical data
**File**: `web/index.html` (JavaScript section)
**What it does**:
1. Adds date range selector (Sept 1 - Oct 31, 2025)
2. Fetches historical data from API when user selects date range
3. Displays alongside current predictions
4. Shows accuracy metrics (if actual_suspended data available):
   - Precision = TP / (TP + FP)
   - Recall = TP / (TP + FN)
   - F1 = 2 × (Precision × Recall) / (Precision + Recall)
5. Creates historical trends chart (Chart.js line chart)
6. Allows filtering by LGU

**Estimated time**: 1-2 hours

---

#### 🔲 Task 12: Add weather correlation visualization
**What it does**:
1. Scatter plot: Rainfall (x-axis) vs Suspension Rate (y-axis)
2. Color points by TCWS level (blue=0, yellow=1-2, red=3+)
3. Add trendline showing correlation
4. Display Pearson correlation coefficient (r)
5. Tooltip on hover with date + weather details

**Estimated time**: 45 minutes - 1 hour

---

#### 🔲 Task 13: Add PAGASA impact analysis section
**What it does**:
1. Bar chart comparing suspension rates:
   - No Typhoon vs TCWS 1-2 vs TCWS 3+
   - No Warning vs Yellow vs Orange vs Red rainfall
2. Show sample sizes (n=X days) for each category
3. Display average suspension probability per category
4. Use `pagasa_impact_analysis` view from database

**Estimated time**: 45 minutes - 1 hour

---

#### 🔲 Task 14: Add LGU breakdown and comparison
**What it does**:
1. Heatmap (Chart.js matrix): 17 LGUs × 61 days
2. Color gradient: green (0-20%) → yellow → orange → red (70-100%)
3. Click LGU to show detailed timeline
4. Show top 5 most/least frequently suspended LGUs
5. Calculate LGU similarity matrix (which LGUs suspend together)

**Estimated time**: 1-2 hours

---

### **Phase 5: Testing** (Task 16)

#### 🔲 Task 16: Add comprehensive test suite
**What it does**:
1. Create `tests/test_backfill.py` with pytest
2. Test weather collection (mock API responses)
3. Test feature engineering (validate calculations)
4. Test model predictions (check output format)
5. Test database operations (use test database)
6. Test JSON output format validation

**Estimated time**: 2-3 hours

---

## 📊 Time Estimates

| Phase | Tasks | Estimated Time |
|-------|-------|----------------|
| **Phase 1: Data Collection** | 4-6 | ~1-2 hours |
| **Phase 2: Feature Engineering & Prediction** | 7-8 | ~15-20 minutes |
| **Phase 3: Validation & Upload** | 9, 15 | ~15-20 minutes |
| **Phase 4: Dashboard Integration** | 10-14 | ~4-6 hours |
| **Phase 5: Testing** | 16 | ~2-3 hours |
| **TOTAL** | | **~8-12 hours** |

---

## 🚀 Recommended Execution Order

### Week 1: Backend (Data Pipeline)
1. ✅ **Task 4**: Create folder structure (DONE)
2. **Task 5**: Build weather collector → Test with 1-2 days first
3. **Task 6**: Build PAGASA collector → May need manual entry
4. **Task 7**: Build feature engineering → Verify output format
5. **Task 8**: Generate predictions → Compare to existing October data
6. **Task 15**: Validate data → Fix any issues found
7. **Task 9**: Upload to database → Verify in Supabase dashboard

### Week 2: Frontend (Dashboard)
8. **Task 10**: Build API endpoint → Test with Postman/curl
9. **Task 11**: Update dashboard JavaScript → Start with simple list view
10. **Task 12**: Add weather correlation chart → Use Chart.js
11. **Task 13**: Add PAGASA impact analysis → Bar charts
12. **Task 14**: Add LGU comparison heatmap → Most complex visualization

### Week 3: Polish
13. **Task 16**: Write tests → Ensure everything works

---

## 🎯 Priority Levels

### HIGH PRIORITY (Core Functionality)
- Task 5: Weather collector
- Task 7: Feature engineering
- Task 8: Generate predictions
- Task 9: Upload to database
- Task 10: API endpoint
- Task 11: Dashboard integration

### MEDIUM PRIORITY (Enhanced Features)
- Task 6: PAGASA collector (fallback to defaults OK)
- Task 12: Weather correlation visualization
- Task 13: PAGASA impact analysis
- Task 15: Data validation

### LOW PRIORITY (Nice-to-Have)
- Task 14: LGU comparison heatmap
- Task 16: Comprehensive tests

---

## 📝 Key Decisions Made

1. **Date Range**: Sept 1 - Oct 31, 2025 (61 days)
2. **Data Source**: Open-Meteo Archive API (free, reliable)
3. **PAGASA Data**: Manual entry fallback if historical bulletins unavailable
4. **Feature Engineering**: Reuse production pipeline (33 features)
5. **Model**: Same model as production (`best_core_model.pkl`)
6. **Database**: Supabase with existing schema
7. **API**: REST endpoint (Flask or standalone script)
8. **Frontend**: Integrate into existing `web/index.html`
9. **Visualizations**: Chart.js (already used in project)

---

## 🔧 Tools & Technologies

- **Python**: Data collection, feature engineering, predictions
- **Open-Meteo Archive API**: Historical weather data
- **Pandas**: Data manipulation
- **Joblib**: Load ML model
- **Supabase (PostgreSQL)**: Database storage
- **Flask/FastAPI**: API endpoint (optional)
- **JavaScript**: Frontend logic
- **Chart.js**: Visualizations
- **Pytest**: Testing

---

## 📚 References

- **Open-Meteo Archive API**: https://open-meteo.com/en/docs/historical-weather-api
- **Supabase Docs**: https://supabase.com/docs
- **Chart.js Docs**: https://www.chartjs.org/docs/latest/
- **Your existing code**: `scripts/collect_and_log.py` for reference

---

## ❓ Questions to Answer

1. **Do you have actual suspension data for Sept-Oct 2025?**
   - If YES: Add to `daily_predictions.actual_suspended` column → enables accuracy metrics
   - If NO: Leave as NULL for now, focus on predictions only

2. **Are historical PAGASA bulletins available?**
   - Check: https://www.pagasa.dost.gov.ph/climate/tropical-cyclone-information
   - If NO: Use manual entry from `config.json` known_typhoons

3. **Do you want to deploy API to cloud or run locally?**
   - Cloud (Vercel/Render): Persistent endpoint, better for production
   - Local: Faster development, need to run server manually

4. **Priority: Accuracy metrics or visualizations first?**
   - If you have actual suspension data → prioritize accuracy metrics
   - If not → focus on visualizations (correlation, PAGASA impact)

---

## 🎉 Next Steps

1. Review this breakdown
2. Start with **Task 5** (weather collector) - it's the longest running task
3. Test with 1-2 days first before running full 61 days
4. Let me know if you need help with any specific script!

---

**Created**: November 3, 2025
**Status**: Planning Complete ✅
**Ready to implement**: Task 5 onwards
