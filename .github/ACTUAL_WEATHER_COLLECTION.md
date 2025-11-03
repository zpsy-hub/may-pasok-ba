# GitHub Actions - Actual Weather Collection Step

## Overview
This guide explains how to add a step to the GitHub Actions workflow to collect **actual weather data** from 2 days ago using Open-Meteo's Historical Weather API.

## Why This is Needed

### The Problem
- Real-time predictions use **forecast data** (what weather is expected)
- To measure accuracy, we need **actual weather data** (what weather actually happened)
- Open-Meteo's historical API has a **2-day delay** (on Nov 3, actual data is available for Nov 1)

### The Solution
Add a daily GitHub Actions step that:
1. Runs after the prediction step
2. Fetches actual weather for 2 days ago
3. Stores it in the database with `data_type='actual'`
4. Enables forecast vs actual comparison

## Script Created

**File**: `scripts/collect_actual_weather.py`

**What it does**:
- Fetches actual weather for 2 days ago (default) or a specified date
- Collects same 11 variables as real-time forecasts
- Stores in `weather_data` table with `data_type='actual'`
- Uses upsert to handle duplicates gracefully
- Rate limited to 1 req/sec (17 LGUs × 1 sec = ~17 seconds)

**Usage**:
```bash
# Collect for 2 days ago (default)
python scripts/collect_actual_weather.py

# Or specify a date
python scripts/collect_actual_weather.py --date 2025-11-01
```

## GitHub Actions Integration

### Step 1: Add to `.github/workflows/deploy.yml`

Add this step **after** the prediction step:

```yaml
      # ... existing steps (checkout, setup python, install dependencies, collect weather, etc.) ...

      - name: Collect actual weather data (2 days ago)
        id: collect_actual
        run: |
          echo "Collecting actual weather data for 2 days ago..."
          python scripts/collect_actual_weather.py
        continue-on-error: true  # Don't fail workflow if this fails
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_KEY: ${{ secrets.SUPABASE_KEY }}

      # ... existing steps (commit, deploy, etc.) ...
```

### Step 2: Update Workflow Summary

Add to the summary section at the end of the workflow:

```yaml
      - name: Create summary
        run: |
          # ... existing summary code ...
          
          # Add actual weather collection status
          echo "### 📊 Actual Weather Collection" >> $GITHUB_STEP_SUMMARY
          if [ "${{ steps.collect_actual.outcome }}" == "success" ]; then
            echo "✅ Collected actual weather for 2 days ago" >> $GITHUB_STEP_SUMMARY
          else
            echo "⚠️ Failed to collect actual weather (non-critical)" >> $GITHUB_STEP_SUMMARY
          fi
```

## Complete Workflow Example

Here's how the updated workflow should look:

```yaml
name: Collect Weather & Generate Predictions

on:
  schedule:
    - cron: '0 * * * *'  # Run hourly
  workflow_dispatch:

jobs:
  collect-and-predict:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Collect weather and generate predictions
        id: predictions
        run: |
          python scripts/collect_and_log.py
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_KEY: ${{ secrets.SUPABASE_KEY }}
      
      - name: Collect actual weather (2 days ago)
        id: collect_actual
        run: |
          echo "Collecting actual weather for 2 days ago..."
          python scripts/collect_actual_weather.py
        continue-on-error: true
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_KEY: ${{ secrets.SUPABASE_KEY }}
      
      - name: Commit predictions
        run: |
          git config --local user.email "github-actions[bot]@users.noreply.github.com"
          git config --local user.name "github-actions[bot]"
          git add web/predictions/
          git commit -m "Update predictions $(date +'%Y-%m-%d %H:%M')" || echo "No changes"
          git push
      
      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./web
      
      - name: Create summary
        run: |
          echo "## 🎯 Prediction Summary" >> $GITHUB_STEP_SUMMARY
          echo "✅ Real-time predictions generated" >> $GITHUB_STEP_SUMMARY
          
          echo "" >> $GITHUB_STEP_SUMMARY
          echo "## 📊 Actual Weather Collection" >> $GITHUB_STEP_SUMMARY
          if [ "${{ steps.collect_actual.outcome }}" == "success" ]; then
            echo "✅ Collected actual weather for 2 days ago" >> $GITHUB_STEP_SUMMARY
          else
            echo "⚠️ Failed to collect actual weather (non-critical)" >> $GITHUB_STEP_SUMMARY
          fi
```

## Database Schema

The actual weather data is stored in the existing `weather_data` table:

```sql
-- Example insert
INSERT INTO weather_data (
    weather_date,
    lgu,
    data_type,  -- 'actual' vs 'forecast'
    precipitation_sum,
    temperature_2m_max,
    wind_speed_10m_max,
    ...
) VALUES (
    '2025-11-01',
    'Manila',
    'actual',  -- ← Key difference
    12.5,
    32.1,
    18.3,
    ...
);
```

**Unique constraint**: `(weather_date, lgu, data_type)`
- This allows storing both forecast and actual data for the same date/LGU

## Data Flow

```
Day 0 (Nov 1):
├─ GitHub Actions runs
├─ Collects forecast for Nov 1 → stores with data_type='forecast'
└─ Makes prediction for Nov 1

Day 1 (Nov 2):
├─ GitHub Actions runs
├─ Collects forecast for Nov 2 → stores with data_type='forecast'
├─ Makes prediction for Nov 2
└─ (No actual data for Oct 31 yet - only 1 day delay)

Day 2 (Nov 3):
├─ GitHub Actions runs
├─ Collects forecast for Nov 3 → stores with data_type='forecast'
├─ Makes prediction for Nov 3
└─ ✅ Collects ACTUAL weather for Nov 1 → stores with data_type='actual'
    (Now we can compare Nov 1 forecast vs actual!)
```

## Benefits

1. **Accuracy Tracking**: Compare forecasts vs actual weather
2. **Model Improvement**: Identify systematic forecast errors
3. **Historical Record**: Build complete dataset for analysis
4. **Dashboard Features**: 
   - Show "Forecast was X, actual was Y"
   - Calculate forecast accuracy metrics
   - Visualize forecast vs actual trends

## Performance Impact

- **Additional API calls**: 17 (1 per LGU)
- **Runtime**: ~17-20 seconds
- **Workflow impact**: Minimal (runs in parallel)
- **Database impact**: +17 rows per day

## Testing

### Manual Test
```bash
# Test the script locally
export SUPABASE_URL="your_url"
export SUPABASE_KEY="your_key"

python scripts/collect_actual_weather.py --date 2025-11-01
```

Expected output:
```
======================================================================
ACTUAL WEATHER DATA COLLECTION
======================================================================
📅 Target date: 2025-11-01
📍 LGUs: 17
🌐 API: Open-Meteo Historical Weather (archive)
💾 Storage: Supabase weather_data table (data_type='actual')

✅ Connected to Supabase

🚀 Starting data collection...

📡 Fetching Manila... ✅
📡 Fetching Quezon City... ✅
...
📡 Fetching Pateros... ✅

======================================================================
COLLECTION SUMMARY
======================================================================
✅ Successful: 17/17
❌ Failed: 0/17

✅ All LGUs collected successfully!

💡 Data stored in Supabase weather_data table:
   - weather_date: 2025-11-01
   - data_type: 'actual'
   - LGUs: 17
```

### Verify in Supabase

```sql
-- Check if data was inserted
SELECT 
    weather_date,
    lgu,
    data_type,
    precipitation_sum,
    temperature_2m_max
FROM weather_data
WHERE weather_date = '2025-11-01'
  AND data_type = 'actual'
ORDER BY lgu;

-- Should return 17 rows (one per LGU)
```

## Troubleshooting

### Error: "Data not available yet"
- Open-Meteo has a 2-day delay
- On Nov 3, only data up to Nov 1 is available
- Solution: Don't try to fetch data newer than 2 days ago

### Error: "Duplicate key violation"
- Upsert should handle this automatically
- If it fails, check the unique constraint: `(weather_date, lgu, data_type)`

### Error: "Connection timeout"
- Network issue or API down
- Script has `continue-on-error: true` so workflow won't fail
- Data will be collected on next run

## Future Enhancements

1. **Backfill missing dates**: Run script for past dates that failed
2. **Accuracy dashboard**: Compare forecast vs actual in web UI
3. **Email alerts**: Notify if actual data collection fails multiple days
4. **Retry logic**: Automatically retry failed LGUs

## Related Files

- **Script**: `scripts/collect_actual_weather.py`
- **Workflow**: `.github/workflows/deploy.yml`
- **Database**: `database/schema.sql` (weather_data table)
- **Config**: Uses existing Supabase credentials

---

**Status**: Ready to implement
**Priority**: High (enables accuracy tracking)
**Estimated effort**: 15-20 minutes to update workflow
