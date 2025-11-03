# Quick Start Guide - Historical Weather Collection

## ✅ Task 5: Build Historical Weather Data Collector - COMPLETED

### What Was Created

**Script**: `backfill/collect_historical_weather.py`

**Features**:
- ✅ Fetches Sept 1 - Oct 31, 2025 (61 days) for all 17 Metro Manila LGUs
- ✅ Uses Open-Meteo Archive API (free, no API key required)
- ✅ Collects 11 weather variables (precipitation, temp, wind, humidity, pressure, etc.)
- ✅ Rate limited to 1 request/second (avoid throttling)
- ✅ Retry logic with 3 attempts on failure
- ✅ Progress tracking with tqdm progress bar
- ✅ Resume capability (skip already-fetched LGUs)
- ✅ Error handling for timeouts and API failures

---

## 🚀 How to Run

### Step 1: Install Dependencies

```powershell
# Install required packages
pip install requests tqdm
```

Or install all backfill dependencies:

```powershell
pip install -r backfill/requirements.txt
```

### Step 2: Run the Collector

```powershell
# From project root
python backfill/collect_historical_weather.py
```

### Expected Output

```
======================================================================
HISTORICAL WEATHER DATA COLLECTION
======================================================================
📅 Date range: 2025-09-01 to 2025-10-31 (61 days)
📍 LGUs: 17
🔢 Total API calls: 17 (1 per LGU, covers all dates)
⏱️  Estimated time: ~0.3 minutes
🌐 API: https://archive-api.open-meteo.com/v1/archive
📊 Variables: temperature_2m_max, temperature_2m_min, apparent_temperature_max, 
              precipitation_sum, precipitation_hours, wind_speed_10m_max, 
              wind_gusts_10m_max, relative_humidity_2m_mean, cloud_cover_max, 
              pressure_msl_min, weather_code

🚀 Starting data collection...

Fetching LGUs: 100%|████████████████████| 17/17 [00:17<00:00, 1.00s/LGU]

======================================================================
COLLECTION SUMMARY
======================================================================
✅ Successful: 17
⏭️  Skipped: 0
❌ Failed: 0
📡 API calls made: 17
📊 Dates collected: 61

💾 Saved results to: backfill\output\weather_sept_oct.json
📦 File size: 1.2 MB

======================================================================
✅ COLLECTION COMPLETE!
======================================================================
📁 Output: backfill\output\weather_sept_oct.json

Next steps:
  1. Review the output file for completeness
  2. Run: python backfill/collect_historical_pagasa.py
======================================================================
```

---

## 📊 Output Format

**File**: `backfill/output/weather_sept_oct.json`

**Structure**:
```json
{
  "2025-09-01": {
    "Manila": {
      "temperature_2m_max": 32.1,
      "temperature_2m_min": 24.3,
      "apparent_temperature_max": 35.2,
      "precipitation_sum": 12.5,
      "precipitation_hours": 4.0,
      "wind_speed_10m_max": 18.3,
      "wind_gusts_10m_max": 35.2,
      "relative_humidity_2m_mean": 78.5,
      "cloud_cover_max": 85.0,
      "pressure_msl_min": 1008.2,
      "weather_code": 61
    },
    "Quezon City": { ... },
    ... (all 17 LGUs)
  },
  "2025-09-02": { ... },
  ... (all 61 dates)
}
```

**Total Records**: 61 dates × 17 LGUs = 1,037 weather records

---

## 🔄 Resume Capability

If the script is interrupted (Ctrl+C or error), it saves progress automatically.

**To resume**:
```powershell
# Just run the script again - it will skip already-fetched LGUs
python backfill/collect_historical_weather.py
```

Progress is saved after each successful LGU fetch.

---

## ⚠️ Troubleshooting

### Error: "Rate limit exceeded"
**Solution**: Script automatically retries with exponential backoff. If persistent, increase `rate_limit_seconds` in `config.json`:

```json
"open_meteo": {
  "rate_limit_seconds": 2  // Increase from 1 to 2
}
```

### Error: "Timeout"
**Solution**: Script retries 3 times automatically. If network is slow, increase timeout in the script or check your internet connection.

### Error: "Missing coordinates for LGU"
**Solution**: Check `config.json` → `lgu_coordinates`. All 17 LGUs should have lat/lon values.

### Incomplete Data
If you see "⚠️ Incomplete data for X dates", it means some LGUs failed to fetch. The script will list them. You can:
1. Run the script again (it will retry failed LGUs)
2. Check if the Open-Meteo API is having issues
3. Manually inspect the output file to see which LGUs are missing

---

## 🧪 Testing

### Test with 1 Day First
Edit `config.json` temporarily to test with just 1 day:

```json
"date_range": {
  "start": "2025-09-01",
  "end": "2025-09-01"  // Changed from 2025-10-31
}
```

Run the script:
```powershell
python backfill/collect_historical_weather.py
```

This should complete in ~17 seconds (17 LGUs × 1 second). Verify the output file looks correct, then restore the full date range.

---

## 📈 Performance

- **API calls**: 17 (1 per LGU, each call fetches all 61 days at once)
- **Rate limit**: 1 request/second
- **Total time**: ~20-30 seconds (17 seconds API calls + processing)
- **Network usage**: ~1-2 MB download
- **Output file size**: ~1-2 MB

---

## 🔍 Data Validation

After collection completes, the script automatically checks for:
- ✅ Missing dates (should have 61 days)
- ✅ Incomplete dates (all 17 LGUs per date)
- ✅ Valid data structure

Example validation output:
```
⚠️  Incomplete data for 2 dates:
   - 2025-09-15: 16/17 LGUs (missing: Pateros)
   - 2025-10-23: 15/17 LGUs (missing: Navotas, Malabon)
```

If you see warnings, run the script again to fetch missing data.

---

## 📝 Configuration

All settings are in `backfill/config.json`:

```json
{
  "date_range": {
    "start": "2025-09-01",
    "end": "2025-10-31"
  },
  "lgus": [ ... ],
  "lgu_coordinates": { ... },
  "open_meteo": {
    "base_url": "https://archive-api.open-meteo.com/v1/archive",
    "variables": [ ... ],
    "rate_limit_seconds": 1
  }
}
```

**Modify as needed**:
- Change date range to collect different periods
- Adjust rate_limit_seconds if hitting API limits
- Add/remove weather variables

---

## 🎯 Next Steps

After successful collection:

1. ✅ Review `backfill/output/weather_sept_oct.json` for completeness
2. 🔲 Run **Task 6**: `python backfill/collect_historical_pagasa.py`
3. 🔲 Run **Task 7**: `python backfill/engineer_features.py`
4. 🔲 Run **Task 8**: `python backfill/generate_predictions.py`

---

## 🆘 Need Help?

Check the following files:
- **Full docs**: `backfill/README.md`
- **Task breakdown**: `backfill/TASK_BREAKDOWN.md`
- **Configuration**: `backfill/config.json`
- **Script source**: `backfill/collect_historical_weather.py`

---

**Status**: ✅ COMPLETED
**Created**: November 3, 2025
**Runtime**: ~20-30 seconds
**Output**: 1,037 weather records (61 days × 17 LGUs)
