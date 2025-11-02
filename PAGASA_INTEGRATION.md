# PAGASA Integration Quick Start

## ✅ System Status: OPERATIONAL

The PAGASA typhoon parser is fully integrated and tested!

**Current Status**: Typhoon TINO detected (not affecting Metro Manila, TCWS Level 0)

---

## 🚀 Quick Start

### 1. Install Dependencies
```powershell
# Install Node.js packages
cd nodejs-pagasa
npm install

# Install Python dependencies (if not already installed)
cd ..
pip install -r requirements.txt
```

### 2. Run from Node.js
```powershell
cd nodejs-pagasa
node pagasa_parser.js
```

**Output**: `pagasa_status.json` in project root

### 3. Run from Python
```python
from src.weather.pagasa_checker import PAGASAChecker

checker = PAGASAChecker()

# Get full status
status = checker.check_typhoon_status()
print(f"Active typhoon: {status['hasActiveTyphoon']}")

# Check Metro Manila TCWS level (0-5)
tcws = checker.get_tcws_level_for_metro_manila()
print(f"Metro Manila TCWS: Level {tcws}")

# Get typhoon info
typhoon = checker.get_current_typhoon_info()
if typhoon:
    print(f"Name: {typhoon['name']}")
    print(f"Bulletin #{typhoon['bulletin_number']}")
```

---

## 📁 File Structure

```
new-capstone/
├── nodejs-pagasa/                     # Node.js scraping module
│   ├── pagasa_parser.js              # Main orchestrator
│   ├── scrape_rainfall_warning.js    # NCR rainfall scraper
│   ├── scrape_severe_weather_bulletin.js  # Web fallback
│   ├── test_pagasa_parser.js         # Node.js tests
│   ├── package.json                   # NPM dependencies
│   ├── .env.example                   # Configuration template
│   └── README.md                      # Documentation
│
├── src/weather/                       # Python integration
│   ├── pagasa_checker.py             # Python wrapper class
│   ├── test_pagasa_checker.py        # Python tests
│   └── __init__.py                    # Module init
│
├── .github/workflows/                 # CI/CD automation
│   └── deploy.yml                     # GitHub Actions workflow
│
└── pagasa_status.json                # Output (auto-generated)
```

---

## 🔍 Testing

### Test Node.js Parser
```powershell
cd nodejs-pagasa
node test_pagasa_parser.js
```

### Test Python Wrapper
```powershell
cd src\weather
python test_pagasa_checker.py
```

**Both tests passed! ✅**

---

## 🌐 GitHub Actions Deployment

The workflow (`.github/workflows/deploy.yml`) automatically:
1. ✅ Runs every hour to fetch latest PAGASA data
2. ✅ Can be triggered manually via GitHub Actions UI
3. ✅ Deploys to GitHub Pages with updated `pagasa_status.json`

### Setup GitHub Pages
1. Go to your repository Settings → Pages
2. Source: Deploy from a branch
3. Branch: `gh-pages` / `root`
4. Save

The workflow will automatically deploy to: `https://<username>.github.io/<repo-name>/`

---

## 📊 Integration with ML Model

### Example: Feature Engineering

```python
from src.weather.pagasa_checker import PAGASAChecker
import pandas as pd

# Initialize checker
checker = PAGASAChecker()

# Get current status
tcws = checker.get_tcws_level_for_metro_manila()
affected = checker.is_metro_manila_affected()
rainfall = checker.get_rainfall_warning()

# Create features
features = {
    'tcws_level': tcws,
    'metro_manila_affected': int(affected),
    'rainfall_warning': int(rainfall is not None),
    'rainfall_level': 0 if not rainfall else 
                      {'RED': 3, 'ORANGE': 2, 'YELLOW': 1}.get(rainfall.get('warningLevel'), 0)
}

# Add to your dataset
df = pd.DataFrame([features])
print(df)
```

### Example: Real-time Predictions

```python
from src.weather.pagasa_checker import PAGASAChecker
import joblib

# Load your trained model
model = joblib.load('models/best_model.pkl')

# Get PAGASA data
checker = PAGASAChecker()
status = checker.check_typhoon_status()

# Create feature vector
X_realtime = [
    status['tcwsLevel'],
    int(status['metroManilaAffected']),
    # ... other features
]

# Predict
prediction = model.predict([X_realtime])
print(f"Suspension likelihood: {prediction[0]}")
```

---

## 📈 Output Format

### `pagasa_status.json` Structure

```json
{
  "hasActiveTyphoon": true,
  "typhoonName": "TINO",
  "typhoonStatus": "PASSING",
  "bulletinNumber": 2,
  "bulletinDate": "2025-11-02T01:36:00.000Z",
  "bulletinAge": "8.3 hours ago",
  "metroManilaAffected": false,
  "tcwsLevel": 0,
  "affectedAreas": [],
  "rainfallWarning": {
    "hasActiveWarning": false,
    "metroManilaStatus": "NO WARNING"
  },
  "lastChecked": "2025-11-02T09:52:11.696Z",
  "message": "Typhoon TINO is active but not affecting Metro Manila"
}
```

### TCWS Levels (0-5)
- **0**: No signal
- **1**: Winds 39-61 kph
- **2**: Winds 62-88 kph  
- **3**: Winds 89-117 kph
- **4**: Winds 118-184 kph
- **5**: Winds >185 kph

### Rainfall Warning Levels
- **YELLOW**: 7.5-15mm/hour, 2-3 hours
- **ORANGE**: 15-30mm/hour, 3 hours  
- **RED**: >30mm/hour or >300mm/6 hours

---

## 🐛 Troubleshooting

### "Output file not created"
- Ensure Node.js is installed: `node --version`
- Check internet connection to PAGASA websites
- Run manually: `cd nodejs-pagasa && node pagasa_parser.js`

### Unicode errors in Python
- Already fixed! Uses `encoding='utf-8', errors='replace'` in subprocess

### "404 PDF parsing error"
- Normal behavior! System falls back to web scraping
- Only appears when specific PDF URLs return 404

### No active typhoon
- Not an error! System correctly detects when there are no typhoons
- Returns `hasActiveTyphoon: false` with TCWS level 0

---

## 📝 Next Steps

### 1. Integrate with Notebook 05 (Production)
Add PAGASA data fetching to your production deployment notebook

### 2. Schedule Predictions
Use PAGASA data to trigger real-time suspension predictions

### 3. Create Dashboard
Display live PAGASA status on your web interface

### 4. Historical Tracking
Store `pagasa_status.json` over time for trend analysis

---

## 🎯 Success Criteria

✅ Node.js parser runs successfully  
✅ Python wrapper communicates with Node.js  
✅ Both test suites pass  
✅ JSON output created in project root  
✅ GitHub Actions workflow configured  
✅ Ready for production deployment  

**All criteria met! System is production-ready! 🎉**
