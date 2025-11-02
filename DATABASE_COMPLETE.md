# 🗄️ Database Integration Complete

## 📊 What We Built

### Complete Supabase PostgreSQL database for logging:
1. **5 Tables**: predictions, weather, PAGASA status, collection logs, model metadata
2. **4 Analytics Views**: accuracy, weather correlation, PAGASA impact, reliability
3. **Python Client**: Easy-to-use logger with 10+ methods
4. **GitHub Actions Integration**: Automated hourly collection
5. **Dashboard Support**: Public read access via REST API

---

## 🎯 Why Supabase?

**Perfect for your GitHub Actions + Pages setup:**

✅ **Free tier**: 500MB database (enough for 1+ year of data)  
✅ **Zero maintenance**: Fully managed PostgreSQL  
✅ **Easy setup**: 5 minutes to deploy  
✅ **Python SDK**: Simple `pip install supabase`  
✅ **REST API**: Built-in for dashboard access  
✅ **No credit card**: Free tier doesn't require payment  
✅ **Real-time**: Optional subscriptions for live updates  
✅ **Secure**: Row Level Security built-in  

**Alternatives considered but rejected:**
- ❌ JSON files in repo: Not queryable, grows repo size
- ❌ Firebase: NoSQL, more complex for structured data
- ❌ MongoDB Atlas: Connection limits on free tier
- ❌ PlanetScale: MySQL, more setup required

---

## 📁 Files Created

```
database/
├── schema.sql                 # PostgreSQL schema (5 tables, 4 views)
├── supabase_client.py         # Python client wrapper
└── README.md                  # Complete setup guide

scripts/
└── collect_and_log.py         # Integration script for GitHub Actions

requirements.txt               # Updated with supabase + openmeteo
```

---

## 🗄️ Database Schema Overview

### Table 1: `daily_predictions`
**Purpose**: Store model predictions for each LGU each day

| Column | Type | Description |
|--------|------|-------------|
| `prediction_date` | DATE | Date of prediction |
| `lgu` | TEXT | LGU name (Manila, Quezon City, etc.) |
| `suspension_probability` | DECIMAL | Model output (0.0-1.0) |
| `predicted_suspended` | BOOLEAN | Binary classification |
| `actual_suspended` | BOOLEAN | Real outcome (filled later) |
| `prediction_correct` | BOOLEAN | Auto-calculated accuracy |
| `model_version` | TEXT | Model identifier (v1.0.0, etc.) |
| `threshold_used` | DECIMAL | Classification threshold |
| `github_run_id` | TEXT | Links to GitHub Actions run |

**Unique constraint**: One prediction per (date, LGU)  
**Indexes**: Fast lookup by date, LGU, actual outcome

### Table 2: `weather_data`
**Purpose**: Store weather forecasts and observations

| Column | Type | Description |
|--------|------|-------------|
| `weather_date` | DATE | Date of weather |
| `lgu` | TEXT | LGU name |
| `data_type` | TEXT | 'forecast' or 'actual' |
| `precipitation_sum` | DECIMAL | Rainfall (mm) |
| `temperature_2m_max` | DECIMAL | Max temp (°C) |
| `wind_speed_10m_max` | DECIMAL | Max wind speed (km/h) |
| `wind_gusts_10m_max` | DECIMAL | Max wind gusts (km/h) |
| `relative_humidity_2m_mean` | DECIMAL | Avg humidity (%) |
| `cloud_cover_max` | DECIMAL | Max cloud cover (%) |
| `pressure_msl_min` | DECIMAL | Min pressure (hPa) |
| `weather_code` | INTEGER | WMO weather code |

**Unique constraint**: One record per (date, LGU, type)  
**Indexes**: Fast lookup by date, LGU, data type

### Table 3: `pagasa_status`
**Purpose**: Store PAGASA typhoon and rainfall warnings

| Column | Type | Description |
|--------|------|-------------|
| `status_date` | DATE | Date of status check |
| `status_time` | TIME | Time of status check |
| `has_active_typhoon` | BOOLEAN | Active typhoon present |
| `typhoon_name` | TEXT | Name (TINO, etc.) |
| `tcws_level` | INTEGER | Tropical cyclone warning (0-5) |
| `has_rainfall_warning` | BOOLEAN | Rainfall warning active |
| `rainfall_warning_level` | TEXT | RED/ORANGE/YELLOW |
| `metro_manila_affected` | BOOLEAN | Impact on Metro Manila |
| `bulletin_url` | TEXT | Link to PAGASA bulletin |

**Indexes**: Fast lookup by date, TCWS level, typhoon presence

### Table 4: `collection_logs`
**Purpose**: Track GitHub Actions runs and success/failure

| Column | Type | Description |
|--------|------|-------------|
| `run_date` | DATE | Date of run |
| `run_time` | TIME | Time of run |
| `github_run_id` | TEXT | GitHub Actions run ID |
| `pagasa_collection_success` | BOOLEAN | PAGASA collection status |
| `pagasa_error` | TEXT | Error message if failed |
| `openmeteo_collection_success` | BOOLEAN | Weather collection status |
| `openmeteo_records_collected` | INTEGER | Number of weather records |
| `openmeteo_error` | TEXT | Error message if failed |
| `predictions_generated` | BOOLEAN | Prediction status |
| `predictions_count` | INTEGER | Number of predictions |
| `predictions_error` | TEXT | Error message if failed |
| `total_duration_seconds` | INTEGER | Run duration |

**Indexes**: Fast lookup by date, success status

### Table 5: `model_metadata`
**Purpose**: Track model versions and performance

| Column | Type | Description |
|--------|------|-------------|
| `model_version` | TEXT | Version identifier (v1.0.0) |
| `model_name` | TEXT | Model type (EasyEnsemble, etc.) |
| `validation_accuracy` | DECIMAL | Validation accuracy |
| `validation_f1` | DECIMAL | F1 score |
| `validation_auc` | DECIMAL | AUC-ROC |
| `optimal_threshold` | DECIMAL | Best classification threshold |
| `feature_importance` | JSONB | Feature weights (JSON) |
| `hyperparameters` | JSONB | Model hyperparameters (JSON) |
| `is_active` | BOOLEAN | Currently deployed |

---

## 📈 Analytics Views

### 1. `prediction_accuracy_by_lgu`
Shows prediction accuracy per LGU (once actual outcomes are filled in)

```sql
SELECT * FROM prediction_accuracy_by_lgu;
```

**Columns**: lgu, total_predictions, correct_predictions, accuracy_percentage, avg_probability

### 2. `weather_suspension_correlation`
Correlates weather conditions with suspensions

```sql
SELECT * FROM weather_suspension_correlation;
```

**Columns**: weather_date, lgus_suspended, avg_precipitation, max_precipitation, avg/max wind

### 3. `pagasa_impact_analysis`
Shows PAGASA warning impact on suspensions

```sql
SELECT * FROM pagasa_impact_analysis;
```

**Columns**: status_date, has_active_typhoon, tcws_level, lgus_suspended, avg_probability

### 4. `collection_reliability`
Tracks collection success rate over time

```sql
SELECT * FROM collection_reliability;
```

**Columns**: date, total_runs, success_counts, avg_duration

---

## 🚀 Quick Start (5 minutes)

### Step 1: Create Supabase Account
1. Go to [supabase.com](https://supabase.com)
2. Sign in with GitHub
3. Create project: `suspension-predictions`
4. Choose Singapore region (closest to Philippines)
5. Generate strong database password

### Step 2: Run Schema
1. Open **SQL Editor** in Supabase dashboard
2. Copy entire `database/schema.sql`
3. Paste and click **Run**
4. ✅ Success!

### Step 3: Get Credentials
1. Go to **Project Settings** → **API**
2. Copy **Project URL**: `https://xxxxx.supabase.co`
3. Copy **service_role key** (NOT anon key): `eyJhbG...`

### Step 4: Add to GitHub Secrets
1. GitHub repo → **Settings** → **Secrets and variables** → **Actions**
2. Add `SUPABASE_URL` = your project URL
3. Add `SUPABASE_KEY` = your service_role key

### Step 5: Install and Test
```powershell
# Install package
pip install supabase

# Set environment variables (Windows)
$env:SUPABASE_URL = "https://xxxxx.supabase.co"
$env:SUPABASE_KEY = "eyJhbG..."

# Test connection
python database/supabase_client.py
```

✅ You should see successful inserts and reads!

---

## 🔧 Usage Examples

### Log Predictions
```python
from database.supabase_client import SupabaseLogger

logger = SupabaseLogger()

predictions = [
    {
        'prediction_date': '2025-11-02',
        'lgu': 'Manila',
        'suspension_probability': 0.8234,
        'predicted_suspended': True
    }
]

logger.log_predictions(predictions, model_version='v1.0.0', threshold=0.5)
```

### Log Weather Data
```python
import pandas as pd

weather_df = pd.DataFrame({
    'weather_date': ['2025-11-02', '2025-11-02'],
    'lgu': ['Manila', 'Quezon City'],
    'precipitation_sum': [15.5, 12.3],
    'temperature_2m_max': [32.1, 31.8]
})

logger.log_weather_data(weather_df, data_type='forecast')
```

### Log PAGASA Status
```python
pagasa_status = {
    'has_active_typhoon': True,
    'typhoon_name': 'TINO',
    'tcws_level': 2,
    'has_rainfall_warning': True
}

logger.log_pagasa_status(pagasa_status)
```

### Get Latest Data
```python
# Get predictions
predictions = logger.get_latest_predictions(limit=10)

# Get accuracy stats
accuracy = logger.get_prediction_accuracy()

# Get weather
weather = logger.get_latest_weather(data_type='forecast')
```

---

## 🤖 GitHub Actions Integration

### Complete collection script ready:
**File**: `scripts/collect_and_log.py`

**What it does:**
1. Collects PAGASA status (typhoon, TCWS, rainfall)
2. Collects Open-Meteo weather (17 LGUs, 13 variables)
3. Generates suspension predictions
4. Logs everything to Supabase
5. Tracks success/failure and duration

**Run from GitHub Actions:**
```yaml
name: Collect and Log Data

on:
  schedule:
    - cron: '0 */1 * * *'  # Every hour

jobs:
  collect:
    runs-on: ubuntu-latest
    env:
      SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
      SUPABASE_KEY: ${{ secrets.SUPABASE_KEY }}
    
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Collect and log data
        run: python scripts/collect_and_log.py
```

---

## 📊 Dashboard Integration

### Fetch data from JavaScript (for GitHub Pages):
```javascript
const SUPABASE_URL = 'https://xxxxx.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbG...';  // Use anon key for public read

async function getLatestPredictions() {
    const response = await fetch(
        `${SUPABASE_URL}/rest/v1/daily_predictions?order=prediction_date.desc&limit=100`,
        {
            headers: {
                'apikey': SUPABASE_ANON_KEY,
                'Authorization': `Bearer ${SUPABASE_ANON_KEY}`
            }
        }
    );
    return await response.json();
}

async function getAccuracy() {
    const response = await fetch(
        `${SUPABASE_URL}/rest/v1/prediction_accuracy_by_lgu`,
        { headers: { 'apikey': SUPABASE_ANON_KEY } }
    );
    return await response.json();
}
```

---

## 💾 Data Retention Estimates

**Free tier**: 500MB database storage

**Estimated usage per year:**
- Daily predictions: 17 LGUs × 365 days = 6,205 records ≈ 1MB
- Weather data: 17 LGUs × 365 days × 2 (forecast + actual) = 12,410 records ≈ 15MB
- PAGASA status: 24 checks/day × 365 days = 8,760 records ≈ 2MB
- Collection logs: 24 runs/day × 365 days = 8,760 records ≈ 1MB

**Total first year**: ~20MB (4% of 500MB limit!)

**You can run this for 20+ years on free tier** 🎉

---

## 🔒 Security

✅ **Service role key** for GitHub Actions (write access)  
✅ **Anon key** for dashboard (read-only access)  
✅ **Row Level Security** enabled (public read, authenticated write)  
✅ **HTTPS only** (enforced by Supabase)  
✅ **GitHub Secrets** (never commit keys to repo)

---

## ✅ Next Steps

1. **Create Supabase account** (2 minutes)
2. **Run schema.sql** (30 seconds)
3. **Add GitHub Secrets** (1 minute)
4. **Test locally** (2 minutes)
5. **Update GitHub Actions workflow** (5 minutes)
6. **Deploy and monitor** (automated)

---

## 📚 Documentation

- **Setup**: `database/README.md` (comprehensive guide)
- **Schema**: `database/schema.sql` (SQL with comments)
- **Client**: `database/supabase_client.py` (Python wrapper)
- **Integration**: `scripts/collect_and_log.py` (complete example)

---

## 🎉 Summary

**Database solution**: Supabase PostgreSQL (free, managed, perfect fit)  
**Setup time**: 5-10 minutes  
**Maintenance**: Zero (fully managed)  
**Cost**: Free forever for this use case  
**Features**: 5 tables, 4 views, Python client, REST API  
**Integration**: Ready for GitHub Actions + Pages  

**Status**: ✅ Complete and ready to deploy!

---

Need help? All documentation is in `database/README.md` with step-by-step instructions, troubleshooting, and examples.
