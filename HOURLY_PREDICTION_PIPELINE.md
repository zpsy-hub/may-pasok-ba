# Hourly Prediction Pipeline - GitHub Actions

## Overview
Automated pipeline that runs **every hour** to generate class suspension predictions for Metro Manila LGUs.

## Workflow File
`.github/workflows/hourly-predictions.yml`

## Schedule
- **Cron**: `5 * * * *` (runs at 5 minutes past every hour)
- **Manual**: Can be triggered manually from GitHub Actions tab

## What It Does

### 1. **Data Collection** 📡
- **PAGASA Data**: Fetches typhoon status, TCWS levels, rainfall warnings
- **Open-Meteo API**: Collects 2-day weather forecast
  - Precipitation, wind speed, temperature
  - Humidity, pressure, cloud cover
  - Historical weather (t-1 features)

### 2. **Feature Engineering** 🔧
- Creates 33 engineered features:
  - **Temporal** (8): year, month, day, day_of_week, is_rainy_season, etc.
  - **Geographic** (2): lgu_id, mean_flood_risk_score
  - **Historical Weather** (13): t-1 precipitation, wind, pressure, etc.
  - **Forecast Weather** (10): precipitation_sum, wind_max, temp_max, etc.

### 3. **ML Model Prediction** 🤖
- Uses **EasyEnsemble** model (`best_core_model.pkl`)
- Generates predictions for all 17 Metro Manila LGUs
- Calculates suspension probability (0-100%)
- Assigns risk tiers: Normal (<40%), Alert (40-55%), Suspension (>55%)

### 4. **Output Generation** 📄
- Overwrites `docs/predictions/latest.json`
- Creates timestamped backup: `predictions_YYYYMMDD_HHMMSS.json`
- JSON structure compatible with `index.html` dashboard

### 5. **Error Logging** 🔍
Tracks and reports failures in:
- ❌ PAGASA webscraping failures
- ❌ Weather API connection issues
- ❌ Feature engineering errors
- ❌ Model loading/prediction failures
- ❌ Database logging errors

### 6. **Deployment** 🚀
- Commits predictions to GitHub
- Triggers GitHub Pages deployment (via `deploy-pages-only.yml`)
- Dashboard updates automatically within 2-3 minutes

## Monitoring

### View Workflow Status
https://github.com/zpsy-hub/may-pasok-ba/actions

### Check Latest Run
1. Go to Actions tab
2. Click "Hourly Prediction Pipeline"
3. View latest run

### Summary Report Includes:
- ✅ Pipeline status (each step)
- 📊 Prediction results (date, count, suspensions, avg probability)
- ⚠️ Error details (if any)
- 📤 Deployment status

### Download Logs
- Pipeline logs saved as artifacts
- Retention: 7 days
- Download from Actions run page

## Manual Trigger

To run predictions immediately:
1. Go to: https://github.com/zpsy-hub/may-pasok-ba/actions
2. Click "Hourly Prediction Pipeline"
3. Click "Run workflow" → "Run workflow"

Or locally:
```bash
# Set environment variables
$env:SUPABASE_URL = "https://wdcjfmpkpfqlxrntgizr.supabase.co"
$env:SUPABASE_KEY = "your-key"

# Run script
python scripts/collect_and_log.py

# Push to GitHub
git add docs/predictions/
git commit -m "Update predictions manually"
git push origin main
```

## Troubleshooting

### Pipeline Fails
- Check the summary report in Actions run
- Look for specific error flags (PAGASA, Weather, Model, etc.)
- Download pipeline logs artifact for detailed debugging

### Predictions Not Updating
1. Check if workflow ran successfully (green checkmark ✅)
2. Verify predictions were committed to main branch
3. Check GitHub Pages deployment status
4. Hard refresh browser (`Ctrl + Shift + R`)

### Model Not Found
- Ensure `model-training/data/processed/best_core_model.pkl` exists in repo
- File is tracked despite `.gitignore` (added with `git add -f`)

### Supabase Connection Failed
- Verify secrets are set: `SUPABASE_URL` and `SUPABASE_KEY`
- Go to: Settings → Secrets and variables → Actions
- Predictions will still generate, but won't log to database

## Dependencies

### Python Packages (requirements.txt)
- supabase==2.12.0
- openmeteo-requests==1.3.0
- requests-cache==1.2.1
- scikit-learn==1.7.2
- imbalanced-learn==0.12.4
- pandas, numpy, joblib

### Node.js Packages (nodejs-pagasa)
- cheerio (for HTML parsing)
- node-fetch
- js-yaml

## Output Format

### `docs/predictions/latest.json`
```json
{
  "generated_at": "2025-11-08T02:16:47.249847",
  "prediction_date": "2025-11-08",
  "model_version": "v1.0.0",
  "pagasa_status": { ... },
  "weather": { ... },
  "predictions": [
    {
      "prediction_date": "2025-11-08",
      "lgu": "Manila",
      "suspension_probability": 0.588,
      "predicted_suspended": true,
      "risk_tier": {
        "tier": "suspension",
        "color": "#ef4444",
        "emoji": "🔴",
        ...
      }
    }
  ]
}
```

## Next Steps

✅ Workflow is now active and will run hourly
✅ Predictions will auto-update on dashboard
✅ Comprehensive logging for debugging
✅ Manual trigger available when needed

Monitor the first few runs to ensure everything works correctly!
