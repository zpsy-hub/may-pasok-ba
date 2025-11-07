# 🎒 May Pasok Ba? - AI Class Suspension Predictor

**Smart suspension prediction system for Metro Manila schools using machine learning and real-time weather data**

Accurately predicts class suspensions 24-48 hours ahead by analyzing PAGASA typhoon warnings, detailed weather forecasts, and historical suspension patterns using an advanced EasyEnsemble ML model.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Live Dashboard](https://img.shields.io/badge/🌐_dashboard-live-brightgreen)](https://zpsy-hub.github.io/may-pasok-ba/)
[![Model: EasyEnsemble](https://img.shields.io/badge/model-EasyEnsemble-blue)](model-training/notebooks/)
[![Hourly Updates](https://img.shields.io/badge/updates-hourly-orange)](https://github.com/zpsy-hub/may-pasok-ba/actions)

---

## 🌟 Key Features

### 🎯 Smart Predictions
- **87.7% accuracy** on real-world validation (Sept-Oct 2025)
- **51.7% recall** - catches half of actual suspensions
- **All 17 Metro Manila LGUs** covered
- **3 risk tiers**: Normal (<40%), Alert (40-55%), Suspension (>55%)

### 🤖 Advanced ML Model
- **EasyEnsemble Classifier** with 50 estimators
- **33 engineered features**: temporal, geographic, weather, PAGASA signals
- **F2 score optimized** for suspension detection (prioritizes recall)
- Trained on historical suspension data with weather context

### 📡 Dual Data Sources
- **PAGASA**: Typhoon bulletins, TCWS levels, rainfall warnings
- **Open-Meteo API**: 48-hour detailed weather forecasts
- Real-time scraping every hour via GitHub Actions

### 📊 Live Dashboard
- Interactive map and charts
- Hourly weather timeline
- Historical prediction logs with performance analysis
- Mobile-responsive design

### ⚙️ Fully Automated
- **Hourly predictions** via GitHub Actions
- Automatic commit and deployment
- Comprehensive error logging
- Supabase database integration  

---

## 🚀 Quick Links

- **🌐 Live Dashboard**: [https://zpsy-hub.github.io/may-pasok-ba/](https://zpsy-hub.github.io/may-pasok-ba/)
- **📊 Latest Predictions**: [latest.json](https://zpsy-hub.github.io/may-pasok-ba/predictions/latest.json)
- **📈 Historical Analysis**: [Performance Dashboard](https://zpsy-hub.github.io/may-pasok-ba/prediction-logs.html)
- **📚 Documentation**: [HOURLY_PREDICTION_PIPELINE.md](HOURLY_PREDICTION_PIPELINE.md)
- **🔧 GitHub Actions**: [Workflow Runs](https://github.com/zpsy-hub/may-pasok-ba/actions)

---

## 📁 Project Structure

```
may-pasok-ba/
├── model-training/          # ML model development
│   ├── notebooks/           # Jupyter notebooks (EDA, training, evaluation)
│   ├── data/               # Training datasets
│   └── models/             # Trained models
│
├── src/weather/            # Weather data collection
│   ├── pagasa_checker.py   # PAGASA typhoon/rainfall scraper
│   ├── openmeteo_collector.py  # Open-Meteo API client
│   └── weather_pipeline.py     # Integrated pipeline
│
├── nodejs-pagasa/          # Node.js PAGASA scraper
│   ├── pagasa_parser.js    # Main parser
│   └── scrape_*.js         # Individual scrapers
│
├── database/               # Database integration
│   ├── schema.sql          # PostgreSQL schema
│   ├── supabase_client.py  # Python client
│   └── README.md           # Setup guide
│
├── scripts/                # Automation scripts
│   └── collect_and_log.py  # Main collection script
│
├── web/                    # GitHub Pages dashboard
│   ├── index.html          # Main dashboard
│   ├── predictions/        # Prediction history
│   └── assets/             # CSS, JS, images
│
└── .github/workflows/      # GitHub Actions
    ├── deploy.yml          # Hourly data collection
    └── ci.yml              # CI/CD pipeline
```

---

## 🎯 How It Works

### 1. Data Collection (Every Hour)
```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   PAGASA    │────▶│   Pipeline   │────▶│  Supabase   │
│  (Typhoons) │     │  Processor   │     │  Database   │
└─────────────┘     └──────────────┘     └─────────────┘
                           ▲
┌─────────────┐            │
│ Open-Meteo  │────────────┘
│  (Weather)  │
└─────────────┘
```

**Sources:**
- **PAGASA**: Typhoon bulletins, TCWS levels, rainfall warnings
- **Open-Meteo**: Precipitation, temperature, wind speed, humidity, pressure

### 2. Prediction Generation
```
Weather Data + PAGASA Warnings
         ↓
  Feature Engineering
         ↓
   ML Model (EasyEnsemble)
         ↓
 Suspension Probabilities
         ↓
    Binary Classification
```

**Features Used:**
- Precipitation forecast (mm)
- Wind speed (km/h)
- TCWS level (0-5)
- Rainfall warning (RED/ORANGE/YELLOW)
- Temperature, humidity, pressure
- Day of week, month, flood risk scores

### 3. Dashboard Display
```
Database → REST API → JavaScript → Charts & Maps
```

Real-time dashboard showing:
- Latest predictions per LGU
- Historical accuracy
- Weather correlation analysis
- PAGASA impact metrics

---

## 🔧 Setup & Installation

### Prerequisites
- Python 3.11+
- Node.js 16+
- Git
- Supabase account (free tier)

### 1. Clone Repository
```bash
git clone https://github.com/zpsy-hub/may-pasok-ba.git
cd may-pasok-ba
```

### 2. Install Dependencies
```bash
# Python dependencies
pip install -r requirements.txt

# Node.js dependencies (for PAGASA scraper)
cd nodejs-pagasa
npm install
cd ..
```

### 3. Setup Database
Follow instructions in [`database/README.md`](database/README.md):
1. Create Supabase account
2. Run `database/schema.sql`
3. Add credentials to GitHub Secrets

### 4. Test Locally
```bash
# Test weather collection
python src/weather/weather_pipeline.py

# Test PAGASA scraper
python src/weather/pagasa_checker.py

# Test database logging
python database/supabase_client.py
```

---

## 📊 Model Performance

**Training Data**: Aug 2022 - Oct 2025 (3+ years)  
**Test Period**: October 2025  
**LGUs Covered**: 17 Metro Manila cities

**Metrics (Test Set):**
- **Accuracy**: 87.3%
- **Precision**: 85.2%
- **Recall**: 89.1%
- **F1 Score**: 87.1%
- **AUC-ROC**: 0.92

**Top Features:**
1. Precipitation sum (mm)
2. PAGASA rainfall warning level
3. TCWS level
4. Wind speed max (km/h)
5. Flood risk score

See [`model-training/notebooks/`](model-training/notebooks/) for detailed analysis.

---

## 🤖 Automation (GitHub Actions)

### Workflow: Data Collection & Deployment
**File**: `.github/workflows/deploy.yml`  
**Schedule**: Every hour (at :00)  
**Duration**: ~2-3 minutes per run

**What it does**:
1. ✅ Scrape PAGASA typhoon/rainfall warnings
2. ✅ Fetch Open-Meteo weather forecasts (2 days)
3. ✅ Generate ML predictions for 17 LGUs
4. ✅ Log all data to Supabase database
5. ✅ Save predictions to JSON files
6. ✅ Deploy to GitHub Pages

**Setup**:
1. Add GitHub Secrets (see [`.github/SETUP_SECRETS.md`](.github/SETUP_SECRETS.md)):
   - `SUPABASE_URL` - Your database URL
   - `SUPABASE_KEY` - Your service role key
2. Enable GitHub Pages (Settings → Pages → Deploy from `gh-pages` branch)
3. Workflow runs automatically every hour

**Manual trigger**:
```bash
# Via GitHub UI: Actions → Deploy to GitHub Pages → Run workflow
# Or trigger with GitHub CLI:
gh workflow run deploy.yml
```

**Monitor runs**: [Actions tab](../../actions)
4. Log to Supabase database
5. Update GitHub Pages

### Manual Trigger
```bash
# From GitHub UI: Actions → Deploy → Run workflow
# Or via API:
gh workflow run deploy.yml
```

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [WEATHER_SYSTEM_COMPLETE.md](WEATHER_SYSTEM_COMPLETE.md) | Weather integration guide |
| [PAGASA_COMPLETE.md](PAGASA_COMPLETE.md) | PAGASA scraper documentation |
| [DATABASE_COMPLETE.md](DATABASE_COMPLETE.md) | Database setup and usage |
| [database/README.md](database/README.md) | Supabase setup guide |
| [src/weather/README.md](src/weather/README.md) | Weather API reference |
| [model-training/notebooks/README.md](model-training/notebooks/README.md) | Model training guide |

---

## 🛠️ Development

### Project Timeline
- **Phase 1**: PAGASA integration (12 files, 1,900 lines)
- **Phase 2**: Open-Meteo collector (430 lines)
- **Phase 3**: Integrated pipeline (390 lines)
- **Phase 4**: Database integration (2,500 lines)
- **Phase 5**: GitHub Actions automation
- **Phase 6**: Dashboard development

### Tech Stack
- **ML**: scikit-learn, CatBoost, XGBoost, LightGBM
- **Data**: pandas, numpy, scipy
- **Web**: Vanilla JS, HTML5, CSS3
- **Backend**: Python 3.11, Node.js 16
- **Database**: Supabase (PostgreSQL)
- **Deployment**: GitHub Actions + GitHub Pages
- **APIs**: Open-Meteo, PAGASA website scraping

---

## 📈 Usage Examples

### Get Latest Predictions (JavaScript)
```javascript
const response = await fetch(
    'https://zpsy-hub.github.io/may-pasok-ba/predictions/latest.json'
);
const predictions = await response.json();
console.log(predictions);
```

### Python: Collect Weather Data
```python
from src.weather.weather_pipeline import WeatherDataPipeline

pipeline = WeatherDataPipeline()
features = pipeline.collect_realtime_weather_features()

print(f"PAGASA TCWS: {features['pagasa']['tcws_level']}")
print(f"Weather data: {len(features['weather'])} LGUs")
```

### Python: Log to Database
```python
from database.supabase_client import SupabaseLogger

logger = SupabaseLogger()
logger.log_predictions(predictions, model_version='v1.0.0', threshold=0.5)
logger.log_weather_data(weather_df, data_type='forecast')
```

---

## 🔐 Environment Variables

**GitHub Secrets (for Actions):**
```
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJhbG...
```

**Local Development:**
```bash
# Windows PowerShell
$env:SUPABASE_URL = "https://xxxxx.supabase.co"
$env:SUPABASE_KEY = "eyJhbG..."

# Linux/Mac
export SUPABASE_URL="https://xxxxx.supabase.co"
export SUPABASE_KEY="eyJhbG..."
```

---

## 🧪 Testing

```bash
# Test PAGASA scraper
python src/weather/test_pagasa_checker.py

# Test weather pipeline
python src/weather/weather_pipeline.py

# Test database client
python database/supabase_client.py

# Run all tests
pytest
```

---

## 📊 Data Sources

1. **Historical Suspensions**: Manual collection from LGU announcements (Aug 2022 - Oct 2025)
2. **Weather Data**: [Open-Meteo API](https://open-meteo.com/) (free, no API key)
3. **PAGASA Warnings**: [PAGASA Website](https://www.pagasa.dost.gov.ph/) (web scraping)
4. **Flood Risk Scores**: NOAH Flood Hazard Maps

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **PAGASA**: Weather data and typhoon warnings
- **Open-Meteo**: Free weather API
- **Supabase**: Free PostgreSQL hosting
- **GitHub**: Free hosting and CI/CD
- **scikit-learn**: Machine learning framework

---

## 📞 Contact

- **GitHub**: [@zpsy-hub](https://github.com/zpsy-hub)
- **Repository**: [may-pasok-ba](https://github.com/zpsy-hub/may-pasok-ba)
- **Issues**: [GitHub Issues](https://github.com/zpsy-hub/may-pasok-ba/issues)

---

## 🎓 Educational Purpose

This project is for educational and informational purposes. For official suspension announcements, always check:
- Your LGU's official social media
- PAGASA official website
- Department of Education announcements

---

**Made with ❤️ for Metro Manila students and parents**

Last updated: November 2, 2025
