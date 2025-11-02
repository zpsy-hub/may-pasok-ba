# Weather Data Collection System

Complete weather data pipeline combining PAGASA typhoon data with Open-Meteo weather forecasts for school suspension predictions.

---

## 🌍 Data Sources

### 1. PAGASA (Philippine Weather Service)
**What it provides:**
- Typhoon/Tropical Cyclone Wind Signals (TCWS) levels 1-5
- Metro Manila affected status
- Rainfall warnings (RED/ORANGE/YELLOW)
- Severe weather bulletins

**Technology**: Node.js web scraping + PDF parsing  
**Coverage**: Real-time, Philippines-specific  
**Update frequency**: Every hour (via GitHub Actions)

### 2. Open-Meteo (European Weather API)
**What it provides:**
- Historical weather observations (2022-present)
- Historical forecasts (2021-present)  
- Real-time 7-day forecasts
- 17 weather variables per location

**Technology**: REST API with Python client  
**Coverage**: Global, 17 Metro Manila locations  
**Update frequency**: Hourly updates, cached for 1 hour

---

## 📁 System Architecture

```
src/weather/
├── pagasa_checker.py          # Python wrapper for PAGASA (Node.js bridge)
├── openmeteo_collector.py     # Open-Meteo API client
├── weather_pipeline.py        # Integrated data pipeline
└── __init__.py

nodejs-pagasa/
├── pagasa_parser.js           # Main PAGASA orchestrator
├── scrape_rainfall_warning.js # NCR rainfall scraper
├── scrape_severe_weather_bulletin.js  # Web fallback
└── test_pagasa_parser.js      # Tests

.github/workflows/
└── deploy.yml                 # Hourly automated collection

model-training/notebooks/
└── 02_eda_and_core_model_all features.ipynb  # Demo integration
```

---

## 🚀 Quick Start

### Installation

```powershell
# Install Python dependencies
pip install openmeteo-requests requests-cache retry-requests pandas numpy

# Install Node.js dependencies
cd nodejs-pagasa
npm install
```

### Basic Usage

#### 1. Real-time Weather Features (for predictions)

```python
from src.weather.weather_pipeline import WeatherDataPipeline

pipeline = WeatherDataPipeline()

# Get today's weather features
features = pipeline.collect_realtime_weather_features()

print(f"TCWS Level: {features['tcws_level']}")
print(f"Precipitation: {features['forecast_precipitation_sum']}mm")
print(f"Wind Speed: {features['forecast_wind_speed_max']} km/h")
```

**Output features:**
```python
{
    # PAGASA features
    'tcws_level': 0-5,
    'metro_manila_affected': 0/1,
    'has_active_typhoon': 0/1,
    'has_rainfall_warning': 0/1,
    'rainfall_warning_level': 0-3,
    
    # Open-Meteo features
    'forecast_precipitation_sum': float,  # mm
    'forecast_precipitation_probability': float,  # %
    'forecast_wind_speed_max': float,  # km/h
    'forecast_wind_gusts_max': float,  # km/h
    'forecast_temperature_max': float,  # °C
    'forecast_humidity_mean': float,  # %
    'forecast_cloud_cover': float,  # %
    'forecast_weather_code': int  # WMO code
}
```

#### 2. Historical Weather (for training)

```python
from datetime import datetime, timedelta

today = datetime.now().date()
start = today - timedelta(days=90)

# Fetch last 90 days
historical_df = pipeline.collect_historical_weather(
    start_date=str(start),
    end_date=str(today),
    include_forecasts=True
)

print(f"Shape: {historical_df.shape}")
# Output: Shape: (1530, 30)  # 90 days * 17 LGUs = 1530 rows
```

#### 3. Merge with Suspension Data

```python
import pandas as pd

# Load your master dataset
master_df = pd.read_csv('master_dataset.csv')

# Fetch weather data
weather_df = pipeline.collect_historical_weather(
    start_date='2022-08-01',
    end_date='2025-10-31'
)

# Merge
enriched_df = pipeline.update_master_dataset_with_weather(
    master_df=master_df,
    weather_df=weather_df
)

print(f"Original columns: {len(master_df.columns)}")
print(f"Enriched columns: {len(enriched_df.columns)}")
# Output: Original columns: 25, Enriched columns: 38 (+13 weather features)
```

---

## 📊 Weather Variables

### Open-Meteo Historical Observations

| Variable | Description | Unit |
|----------|-------------|------|
| `weather_code` | WMO weather condition code | - |
| `precipitation_sum` | Total daily precipitation | mm |
| `wind_speed_10m_max` | Maximum wind speed at 10m | km/h |
| `wind_gusts_10m_max` | Maximum wind gusts | km/h |
| `temperature_2m_max` | Maximum temperature | °C |
| `apparent_temperature_max` | Maximum feels-like temp | °C |
| `relative_humidity_2m_mean` | Average humidity | % |
| `cloud_cover_max` | Maximum cloud coverage | % |
| `pressure_msl_min` | Minimum sea-level pressure | hPa |
| `dew_point_2m_mean` | Average dew point | °C |
| `vapour_pressure_deficit_max` | Max VPD | kPa |
| `shortwave_radiation_sum` | Solar radiation | MJ/m² |
| `et0_fao_evapotranspiration` | Evapotranspiration | mm |

### Open-Meteo Historical Forecasts (additional)

| Variable | Description | Unit |
|----------|-------------|------|
| `precipitation_hours` | Duration of precipitation | hours |
| `precipitation_probability_max` | Max chance of rain | % |
| `cape_max` | Convective Available Potential Energy | J/kg |
| `updraft_max` | Maximum updraft velocity | m/s |

### PAGASA Features

| Variable | Description | Values |
|----------|-------------|--------|
| `tcws_level` | Tropical Cyclone Wind Signal | 0-5 |
| `metro_manila_affected` | MM under TCWS | 0/1 |
| `has_active_typhoon` | Active typhoon in Philippines | 0/1 |
| `has_rainfall_warning` | Active rainfall warning | 0/1 |
| `rainfall_warning_level` | Warning severity | 0-3 (YELLOW/ORANGE/RED) |

---

## 🔄 Automated Collection (GitHub Actions)

The `.github/workflows/deploy.yml` workflow runs every hour:

```yaml
schedule:
  - cron: '0 * * * *'  # Every hour
```

**What it does:**
1. Installs Node.js 18 + Python 3.10
2. Runs `pagasa_parser.js` → `pagasa_status.json`
3. Runs Open-Meteo collector → 7-day forecast
4. Deploys to GitHub Pages

**Setup:**
1. Enable GitHub Actions in your repo
2. Enable GitHub Pages (Settings → Pages → `gh-pages` branch)
3. Push workflow file to `.github/workflows/deploy.yml`

---

## 📦 Output Files

### Real-time Collection
```
weather_data/
├── realtime_features_20251102_143022.json  # Timestamped features
├── daily_forecast_20251102.csv             # Today's 7-day forecast
└── daily_collection_log.jsonl              # Append-only log
```

### Historical Collection
```
weather_data/
├── weather_actual_2022-08-01_2025-10-31.csv     # Observations
├── weather_forecast_2022-08-01_2025-10-31.csv   # Historical forecasts
└── weather_combined_2022-08-01_2025-10-31.csv   # Merged (actual + forecast)
```

### PAGASA Output
```
pagasa_status.json  # Project root
```
```json
{
  "hasActiveTyphoon": true,
  "typhoonName": "TINO",
  "tcwsLevel": 0,
  "metroManilaAffected": false,
  "rainfallWarning": {
    "hasActiveWarning": false,
    "metroManilaStatus": "NO WARNING"
  }
}
```

---

## 💡 Usage Examples

### Example 1: Add Weather to Training Data

```python
from src.weather.weather_pipeline import WeatherDataPipeline
import pandas as pd

pipeline = WeatherDataPipeline()

# Load existing master dataset
master = pd.read_csv('model-training/data/processed/master_train.csv')

# Fetch weather for training period
weather = pipeline.collect_historical_weather(
    start_date='2022-08-01',
    end_date='2024-08-31',
    include_forecasts=False
)

# Merge
enriched = pipeline.update_master_dataset_with_weather(master, weather)

# Save
enriched.to_csv('model-training/data/processed/master_train_with_weather.csv', 
                index=False)
```

### Example 2: Real-time Prediction

```python
from src.weather.weather_pipeline import WeatherDataPipeline
import joblib
import pandas as pd
from datetime import datetime

# Load trained model
model = joblib.load('models/best_model.pkl')

# Get today's weather
pipeline = WeatherDataPipeline()
weather_features = pipeline.collect_realtime_weather_features()

# Add other features (calendar, etc.)
today = datetime.now()
features = {
    **weather_features,
    'is_monday': int(today.weekday() == 0),
    'month': today.month,
    # ... other features
}

# Create feature vector
X_today = pd.DataFrame([features])

# Predict
prediction = model.predict_proba(X_today)[:, 1][0]

print(f"Suspension probability: {prediction:.1%}")

if weather_features['tcws_level'] >= 2:
    print("⚠️  TCWS Level 2+ detected!")
```

### Example 3: Metro Manila Average

```python
from src.weather.openmeteo_collector import OpenMeteoCollector

collector = OpenMeteoCollector()

# Fetch data for all 17 LGUs
historical = collector.fetch_historical_weather(
    start_date='2025-10-01',
    end_date='2025-10-31'
)

# Calculate Metro Manila average
mm_avg = collector.get_metro_manila_average(historical)

print(mm_avg[['date', 'precipitation_sum', 'temperature_2m_max']].head())
```

---

## 🧪 Testing

### Test PAGASA Integration
```powershell
cd nodejs-pagasa
node test_pagasa_parser.js
```

### Test Python Wrapper
```powershell
cd src\weather
python test_pagasa_checker.py
```

### Test Open-Meteo Collector
```powershell
cd src\weather
python openmeteo_collector.py  # Runs demo
```

### Test Full Pipeline
```powershell
cd src\weather
python weather_pipeline.py  # Runs demo
```

---

## 🔧 Configuration

### Metro Manila Coordinates

Modify `METRO_MANILA_COORDS` in `openmeteo_collector.py`:

```python
METRO_MANILA_COORDS = {
    'manila': {'lat': 14.5995, 'lon': 120.9842},
    'quezon_city': {'lat': 14.6760, 'lon': 121.0437},
    # ... 17 total LGUs
}
```

### Cache Settings

```python
# Adjust cache duration (seconds)
cache_session = requests_cache.CachedSession(
    '.cache',
    expire_after=3600  # 1 hour
)
```

### API Timeout

```python
# In openmeteo_collector.py
retry_session = retry(
    cache_session,
    retries=5,          # Max retries
    backoff_factor=0.2  # Wait between retries
)
```

---

## 📈 Performance

| Operation | Time | Records | Notes |
|-----------|------|---------|-------|
| PAGASA real-time | ~500ms | 1 status | Includes PDF parsing |
| Open-Meteo forecast (7d) | ~1-2s | 119 rows | 17 LGUs × 7 days |
| Open-Meteo historical (90d) | ~10-15s | 1,530 rows | 17 LGUs × 90 days |
| Open-Meteo historical (3y) | ~60-90s | 18,615 rows | 17 LGUs × ~1095 days |

**Caching**: Responses cached for 1 hour, subsequent calls instant

---

## 🐛 Troubleshooting

### "Node.js not found"
```powershell
# Install Node.js 18+
winget install OpenJS.NodeJS
```

### "Module 'openmeteo_requests' not found"
```powershell
pip install openmeteo-requests
```

### "404 PDF parsing error" (PAGASA)
- **Not an error!** System falls back to web scraping
- Happens when specific PDF URLs are unavailable
- Check `pagasa_status.json` for results

### "No data for date X"
- Open-Meteo historical data starts from 2022-08-01
- Forecasts available from 2021-08-22
- Use `include_forecasts=True` for earlier dates

### Rate limiting
- Open-Meteo: 10,000 requests/day (free tier)
- Caching reduces API calls
- Use batch requests for multiple dates

---

## 📚 Resources

- [Open-Meteo API Docs](https://open-meteo.com/en/docs)
- [Open-Meteo Historical API](https://open-meteo.com/en/docs/historical-weather-api)
- [PAGASA Official Site](https://www.pagasa.dost.gov.ph/)
- [pagasa-parser npm package](https://www.npmjs.com/package/pagasa-parser)
- [WMO Weather Codes](https://www.nodc.noaa.gov/archive/arc0021/0002199/1.1/data/0-data/HTML/WMO-CODE/WMO4677.HTM)

---

## ✅ Success Checklist

- [x] ✅ PAGASA integration working
- [x] ✅ Open-Meteo API client working
- [x] ✅ Integrated pipeline working
- [x] ✅ All tests passing
- [x] ✅ GitHub Actions configured
- [x] ✅ Demo notebook cell added
- [x] ✅ Documentation complete

**System Status**: 🟢 FULLY OPERATIONAL

---

**Last Updated**: November 2, 2025  
**Tested With**: Python 3.10+, Node.js 18+  
**License**: MIT
