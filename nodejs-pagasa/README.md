# PAGASA Weather Integration

This system integrates PAGASA (Philippine Atmospheric, Geophysical and Astronomical Services Administration) weather data into the suspension prediction system.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Python ML Pipeline (model-training/)                   │
│  ├── src/weather/pagasa_checker.py (Python Wrapper)    │
│  └── Uses subprocess to call Node.js                    │
└──────────────────┬──────────────────────────────────────┘
                   │
                   │ subprocess.run()
                   │
┌──────────────────▼──────────────────────────────────────┐
│  Node.js Scraper (nodejs-pagasa/)                       │
│  ├── pagasa_parser.js (Main Orchestrator)              │
│  ├── scrape_rainfall_warning.js (NCR Rainfall)         │
│  └── scrape_severe_weather_bulletin.js (Fallback)      │
└──────────────────┬──────────────────────────────────────┘
                   │
                   │ HTTP Requests
                   │
┌──────────────────▼──────────────────────────────────────┐
│  PAGASA Websites                                         │
│  ├── Severe Weather Bulletin (PDF + Web)               │
│  └── NCR Rainfall Warning (Web)                        │
└─────────────────────────────────────────────────────────┘
```

## Components

### 1. Node.js Scraper (`nodejs-pagasa/`)
- **pagasa_parser.js**: Main orchestrator that fetches typhoon bulletins and rainfall warnings
- **scrape_rainfall_warning.js**: Scrapes PAGASA NCR rainfall warning page
- **scrape_severe_weather_bulletin.js**: Web scraping fallback for bulletin data
- **Output**: `pagasa_status.json` with structured typhoon and rainfall data

### 2. Python Wrapper (`src/weather/pagasa_checker.py`)
- **PAGASAChecker** class: Python interface to Node.js scraper
- Methods:
  - `check_typhoon_status()`: Get full typhoon status
  - `get_tcws_level_for_metro_manila()`: Get TCWS level (0-5)
  - `is_metro_manila_affected()`: Check if Metro Manila has active TCWS
  - `get_current_typhoon_info()`: Get active typhoon details
  - `get_rainfall_warning()`: Get rainfall warning status

### 3. GitHub Actions (`..github/workflows/deploy.yml`)
- Runs hourly to fetch latest PAGASA data
- Deploys to GitHub Pages with updated status
- Can be triggered manually via workflow_dispatch

## Installation

### Prerequisites
- Node.js 18+
- Python 3.10+

### Setup
```powershell
# Install Node.js dependencies
cd nodejs-pagasa
npm install

# Install Python dependencies
cd ..
pip install -r requirements.txt
```

## Usage

### Node.js Direct
```bash
cd nodejs-pagasa
node pagasa_parser.js
```

### Python Wrapper
```python
from src.weather.pagasa_checker import PAGASAChecker

checker = PAGASAChecker()
status = checker.check_typhoon_status()

if status['hasActiveTyphoon']:
    print(f"Typhoon: {status['typhoonName']}")
    print(f"Metro Manila TCWS: Level {status['tcwsLevel']}")
```

### Testing
```powershell
# Test Node.js parser
cd nodejs-pagasa
node test_pagasa_parser.js

# Test Python wrapper
cd src/weather
python test_pagasa_checker.py
```

## Output Format (`pagasa_status.json`)

```json
{
  "hasActiveTyphoon": true,
  "typhoonName": "PEPITO",
  "typhoonStatus": "ACTIVE",
  "bulletinNumber": 15,
  "bulletinDate": "2024-11-17 05:00 AM",
  "bulletinUrl": "https://...",
  "bulletinAge": "2 hours ago",
  "metroManilaAffected": true,
  "tcwsLevel": 2,
  "affectedAreas": [
    {
      "name": "Metro Manila",
      "signal": 2,
      "part": false,
      "includes": null
    }
  ],
  "rainfallWarning": {
    "hasActiveWarning": true,
    "warningLevel": "ORANGE",
    "metroManilaStatus": "ORANGE WARNING",
    "affectedAreas": [...],
    "hazards": ["FLOODING"]
  },
  "lastChecked": "2024-11-17T07:30:00.000Z"
}
```

## Integration with ML Model

The PAGASA data can be integrated into the suspension prediction model:

```python
from src.weather.pagasa_checker import PAGASAChecker

checker = PAGASAChecker()

# Get typhoon status
tcws = checker.get_tcws_level_for_metro_manila()

# Use in feature engineering
features = {
    'tcws_level': tcws,
    'metro_manila_affected': checker.is_metro_manila_affected(),
    # ... other features
}
```

## Deployment

The system automatically deploys to GitHub Pages via GitHub Actions:
1. Every hour, the workflow runs
2. Fetches latest PAGASA data
3. Generates `pagasa_status.json`
4. Deploys to `gh-pages` branch

## Troubleshooting

### Node.js Script Fails
- Check internet connection to PAGASA websites
- Verify Node.js version (18+)
- Run `npm install` to ensure dependencies are installed

### Python Wrapper Fails
- Ensure Node.js script exists at `nodejs-pagasa/pagasa_parser.js`
- Check that `pagasa_status.json` is created
- Verify subprocess permissions

### No Data Found
- PAGASA may not have active typhoons (expected behavior)
- Check PAGASA websites are accessible
- Review scraper logs for parsing errors

## License
MIT

## Credits
- PAGASA for weather data
- pagasa-parser library by @altJake
