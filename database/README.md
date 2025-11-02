# Database Setup Guide - Supabase

## 🎯 Quick Setup (5 minutes)

### Step 1: Create Supabase Account
1. Go to [supabase.com](https://supabase.com)
2. Click "Start your project"
3. Sign in with GitHub
4. Create new project:
   - **Name**: `suspension-predictions`
   - **Database Password**: Generate strong password (save it!)
   - **Region**: Choose closest to Philippines (Singapore recommended)
   - **Plan**: Free tier (500MB, perfect for this project)

### Step 2: Run Database Schema
1. In Supabase dashboard, go to **SQL Editor**
2. Click "New query"
3. Copy entire contents of `database/schema.sql`
4. Paste and click **Run**
5. ✅ Should see "Success. No rows returned" (this is normal!)

### Step 3: Get API Credentials
1. Go to **Project Settings** (gear icon) → **API**
2. Copy these values:
   - **Project URL**: `https://xxxxx.supabase.co`
   - **`service_role` key** (NOT anon key): `eyJhbG...` (long string)

### Step 4: Add to GitHub Secrets
1. Go to your GitHub repo → **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Add two secrets:
   - `SUPABASE_URL` = your project URL
   - `SUPABASE_KEY` = your service_role key

### Step 5: Install Python Package
```powershell
pip install supabase
```

### Step 6: Test Connection
```powershell
# Set environment variables (Windows PowerShell)
$env:SUPABASE_URL = "https://xxxxx.supabase.co"
$env:SUPABASE_KEY = "eyJhbG..."

# Test the database client
python database/supabase_client.py
```

✅ You should see successful inserts and reads!

---

## 📊 Database Tables

### 1. `daily_predictions`
Stores model predictions for each LGU each day.

**Columns:**
- `prediction_date`, `lgu` - Identifies the prediction
- `suspension_probability` - Model output (0.0-1.0)
- `predicted_suspended` - Binary classification (True/False)
- `actual_suspended` - Real outcome (filled in later)
- `prediction_correct` - Auto-calculated accuracy
- `model_version`, `threshold_used` - Tracking
- `github_run_id` - Links to GitHub Actions run

**Unique constraint:** One prediction per (date, LGU) pair

### 2. `weather_data`
Stores weather forecasts and observations from Open-Meteo.

**Columns:**
- `weather_date`, `lgu`, `data_type` - Identifies the record
- Weather variables: `precipitation_sum`, `temperature_2m_max`, `wind_speed_10m_max`, etc.
- `data_type` - 'forecast' or 'actual'
- `collected_at` - Timestamp of collection

**Unique constraint:** One record per (date, LGU, type) combo

### 3. `pagasa_status`
Stores PAGASA typhoon and rainfall warnings.

**Columns:**
- `status_date`, `status_time` - When status was checked
- Typhoon: `has_active_typhoon`, `typhoon_name`, `tcws_level`
- Rainfall: `has_rainfall_warning`, `rainfall_warning_level`
- `metro_manila_affected` - Impact flag
- `bulletin_url` - Link to PAGASA bulletin

### 4. `collection_logs`
Tracks GitHub Actions runs and success/failure.

**Columns:**
- `run_date`, `run_time`, `github_run_id`
- Success flags: `pagasa_collection_success`, `openmeteo_collection_success`, `predictions_generated`
- Error messages: `pagasa_error`, `openmeteo_error`, `predictions_error`
- Performance: `total_duration_seconds`

### 5. `model_metadata`
Tracks model versions and performance metrics.

**Columns:**
- `model_version`, `model_name` - Identifier
- Metrics: `validation_accuracy`, `validation_f1`, `validation_auc`
- `optimal_threshold` - Best classification threshold
- `feature_importance` - JSON with feature weights
- `is_active` - Whether this model is currently deployed

---

## 📈 Analytics Views

### `prediction_accuracy_by_lgu`
Shows accuracy stats per LGU.
```sql
SELECT * FROM prediction_accuracy_by_lgu;
```

### `weather_suspension_correlation`
Correlates weather with suspensions.
```sql
SELECT * FROM weather_suspension_correlation;
```

### `pagasa_impact_analysis`
Shows PAGASA warning impact.
```sql
SELECT * FROM pagasa_impact_analysis;
```

### `collection_reliability`
Tracks collection success rate.
```sql
SELECT * FROM collection_reliability;
```

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
    'weather_date': ['2025-11-02'],
    'lgu': ['Manila'],
    'precipitation_sum': [15.5],
    'temperature_2m_max': [32.1]
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

### Update Actual Outcome
```python
from datetime import date

logger.update_actual_outcome(
    prediction_date=date(2025, 11, 2),
    lgu='Manila',
    actual_suspended=True
)
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

## 🚀 Integration with GitHub Actions

### In your workflow (`deploy.yml`):
```yaml
name: Deploy and Collect Data

on:
  schedule:
    - cron: '0 */1 * * *'  # Every hour
  workflow_dispatch:

jobs:
  collect:
    runs-on: ubuntu-latest
    env:
      SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
      SUPABASE_KEY: ${{ secrets.SUPABASE_KEY }}
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install supabase pandas numpy
          pip install openmeteo-requests requests-cache
      
      - name: Collect and log data
        run: python scripts/collect_and_log.py
```

### In your collection script:
```python
# scripts/collect_and_log.py
import time
from datetime import date
from database.supabase_client import SupabaseLogger
from src.weather.weather_pipeline import WeatherDataPipeline

start_time = time.time()
logger = SupabaseLogger()
pipeline = WeatherDataPipeline()

try:
    # Collect weather
    features = pipeline.collect_realtime_weather_features()
    logger.log_weather_data(features['weather'], data_type='forecast')
    logger.log_pagasa_status(features['pagasa'])
    
    # Generate predictions (your model here)
    predictions = generate_predictions(features)
    logger.log_predictions(predictions, model_version='v1.0.0', threshold=0.5)
    
    # Log success
    duration = int(time.time() - start_time)
    logger.log_collection_run(
        pagasa_success=True,
        openmeteo_success=True,
        openmeteo_records=len(features['weather']),
        predictions_success=True,
        predictions_count=len(predictions),
        duration_seconds=duration
    )
    
except Exception as e:
    # Log failure
    logger.log_collection_run(
        pagasa_success=False,
        pagasa_error=str(e),
        openmeteo_success=False,
        predictions_success=False
    )
    raise
```

---

## 📊 Dashboard Integration (GitHub Pages)

### Fetch data for dashboard:
```javascript
// In your web/js/dashboard.js
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
        {
            headers: {
                'apikey': SUPABASE_ANON_KEY,
                'Authorization': `Bearer ${SUPABASE_ANON_KEY}`
            }
        }
    );
    return await response.json();
}
```

---

## 🔒 Security Notes

1. **Never commit secrets**: Use GitHub Secrets for `SUPABASE_KEY`
2. **Use service_role for writes**: GitHub Actions uses service_role key
3. **Use anon key for reads**: Dashboard uses anon key (read-only)
4. **Row Level Security**: Enabled with public read access, service role bypasses RLS automatically for writes
5. **HTTPS only**: Supabase enforces HTTPS automatically

**Important**: The `service_role` key bypasses RLS by default, which is why GitHub Actions can write to the database. The anon key respects RLS and only has read access.

---

## 💾 Data Retention

**Free tier limits:**
- 500MB database storage
- 2GB bandwidth/month
- Unlimited API requests

**Estimated usage:**
- ~100 predictions/day × 365 days = 36,500 records/year ≈ 5MB
- ~3,400 weather records/day × 365 = 1.2M records/year ≈ 180MB
- **Total first year**: ~200MB (well within 500MB limit!)

**If you exceed limits:**
- Archive old data (export to JSON/CSV)
- Delete records older than 1 year
- Upgrade to Pro plan ($25/month for 8GB)

---

## 🐛 Troubleshooting

### "Invalid API key"
- Make sure you're using `service_role` key, not `anon` key
- Check that secret is correctly set in GitHub

### "Relation does not exist"
- Run `schema.sql` in Supabase SQL Editor
- Make sure you're connected to the right project

### "Row Level Security policy violation"
- Service role key bypasses RLS automatically (no policy checks needed)
- If using anon key, RLS only allows SELECT (read-only)
- Make sure you're using the correct key for your operation

### "Duplicate key violation"
- Predictions use upsert (INSERT ... ON CONFLICT)
- Make sure prediction_date + lgu are unique per insert

### Connection timeout
- Check SUPABASE_URL is correct
- Verify internet connection
- Try from different network (firewall issue?)

---

## 📚 Additional Resources

- [Supabase Python Docs](https://supabase.com/docs/reference/python/introduction)
- [Supabase REST API](https://supabase.com/docs/guides/api)
- [PostgreSQL Docs](https://www.postgresql.org/docs/)
- [Row Level Security Guide](https://supabase.com/docs/guides/auth/row-level-security)

---

## ✅ Checklist

- [ ] Created Supabase account
- [ ] Created new project
- [ ] Ran `schema.sql` in SQL Editor
- [ ] Copied Project URL and service_role key
- [ ] Added secrets to GitHub repo
- [ ] Installed `supabase` Python package
- [ ] Tested connection with `supabase_client.py`
- [ ] Updated GitHub Actions workflow
- [ ] Created collection script
- [ ] Tested end-to-end flow

**Setup time**: ~5-10 minutes  
**Maintenance**: Zero (fully managed)  
**Cost**: Free forever for this use case

---

Need help? Check the Supabase dashboard logs or contact [Supabase support](https://supabase.com/docs/support).
