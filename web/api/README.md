# Database API Setup Instructions

## 🎯 Overview

The web dashboard now fetches predictions from a **database API** instead of static JSON files. This enables:
- ✅ Real-time data from Supabase
- ✅ Historical data queries by date
- ✅ Automatic risk tier calculation
- ✅ Fallback to JSON file if API is down

## 📋 Prerequisites

1. **Supabase database** with tables created (see `database/schema.sql`)
2. **Python 3.8+** installed
3. **Environment variables** set

## 🚀 Quick Start

### Step 1: Install Dependencies

```bash
cd c:\Users\zyra\Documents\new-capstone
pip install flask flask-cors supabase python-dotenv
```

### Step 2: Set Environment Variables

Create a `.env` file in the project root:

```bash
# .env file
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_service_role_key_here
```

### Step 3: Start the API Server

```bash
cd c:\Users\zyra\Documents\new-capstone
python web/api/get_predictions.py
```

You should see:
```
🚀 Starting May Pasok Ba API Server...
📡 API Endpoints:
   - GET /api/predictions/latest
   - GET /api/predictions/date/<YYYY-MM-DD>
   - GET /api/health

⚙️ Make sure SUPABASE_URL and SUPABASE_KEY are set!
🌐 Server running on http://localhost:5000
```

### Step 4: Start the Web Server (in a new terminal)

```bash
cd c:\Users\zyra\Documents\new-capstone\web
python -m http.server 8000
```

### Step 5: Open the Dashboard

Open your browser to: **http://localhost:8000/index.html**

The dashboard will now fetch data from the API!

## 🔍 API Endpoints

### 1. Get Latest Predictions

**Endpoint**: `GET /api/predictions/latest`

**Example**:
```bash
curl http://localhost:5000/api/predictions/latest
```

**Response**:
```json
{
  "generated_at": "2025-11-03T10:00:00",
  "prediction_date": "2025-11-03",
  "model_version": "v1.0.0",
  "pagasa_status": {
    "has_active_typhoon": false,
    "typhoon_name": null,
    "tcws_level": 0,
    "has_rainfall_warning": true,
    "rainfall_warning_level": "ORANGE"
  },
  "weather": {
    "precipitation_sum_mm": 35.5,
    "wind_speed_max_kmh": 45.2,
    "temperature_max_c": 29.8,
    "humidity_mean_pct": 82.3
  },
  "predictions": [
    {
      "prediction_date": "2025-11-03",
      "lgu": "Manila",
      "suspension_probability": 0.487,
      "predicted_suspended": false,
      "risk_tier": {
        "tier": "alert",
        "emoji": "🟠",
        "title": "WEATHER ALERT",
        ...
      },
      "weather_context": {...}
    }
    // ... 16 more LGUs
  ],
  "summary": {
    "total_lgus": 17,
    "predicted_suspensions": 3,
    "avg_probability": 0.435
  },
  "metadata": {
    "timestamp": "2025-11-03T10:00:00",
    "source": "database",
    "api_version": "1.0.0"
  }
}
```

### 2. Get Predictions by Date

**Endpoint**: `GET /api/predictions/date/<YYYY-MM-DD>`

**Example**:
```bash
curl http://localhost:5000/api/predictions/date/2025-11-02
```

### 3. Health Check

**Endpoint**: `GET /api/health`

**Example**:
```bash
curl http://localhost:5000/api/health
```

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-11-03T10:00:00",
  "database_connected": true
}
```

## 🔄 How It Works

1. **Dashboard loads** → Calls `/api/predictions/latest`
2. **API fetches** → Queries Supabase database for:
   - Latest predictions from `daily_predictions` table
   - Weather data from `weather_data` table
   - PAGASA status from `pagasa_status` table
3. **API calculates** → Generates risk tiers on-the-fly based on:
   - Suspension probability
   - Weather conditions
   - PAGASA advisories
4. **Dashboard renders** → Shows all 17 LGUs with risk tier UI

## 🎯 Fallback Mechanism

The dashboard has a **two-tier fallback system**:

1. **PRIMARY**: Fetch from database API (`http://localhost:5000/api/predictions/latest`)
2. **FALLBACK**: Fetch from JSON file (`predictions/latest.json`)

If the API is down, the dashboard automatically falls back to the JSON file.

## 🐛 Troubleshooting

### Problem: "Unable to connect to database"

**Solution**: Check that environment variables are set correctly:
```bash
echo $SUPABASE_URL
echo $SUPABASE_KEY
```

### Problem: "No predictions found"

**Solution**: Make sure you've uploaded predictions to the database:
```bash
cd c:\Users\zyra\Documents\new-capstone
python scripts/collect_and_log.py
```

### Problem: API returns 503 error

**Solution**: Check database connection:
```bash
python database/supabase_client.py
```

### Problem: CORS errors in browser console

**Solution**: The API already has CORS enabled. Make sure you're accessing the dashboard via `http://localhost:8000` (not `file://`)

## 🚀 Production Deployment

### Option 1: Deploy API to Vercel

1. Install Vercel CLI:
```bash
npm install -g vercel
```

2. Create `vercel.json`:
```json
{
  "version": 2,
  "builds": [
    {
      "src": "web/api/get_predictions.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "web/api/get_predictions.py"
    }
  ],
  "env": {
    "SUPABASE_URL": "@supabase-url",
    "SUPABASE_KEY": "@supabase-key"
  }
}
```

3. Deploy:
```bash
vercel --prod
```

4. Update dashboard to use production API URL:
```javascript
const apiUrl = 'https://your-project.vercel.app/api/predictions/latest';
```

### Option 2: Deploy API to Render

1. Create `render.yaml`:
```yaml
services:
  - type: web
    name: may-pasok-ba-api
    env: python
    buildCommand: "pip install -r requirements.txt"
    startCommand: "python web/api/get_predictions.py"
    envVars:
      - key: SUPABASE_URL
        sync: false
      - key: SUPABASE_KEY
        sync: false
```

2. Push to GitHub and connect to Render

3. Update dashboard API URL

### Option 3: Deploy API to Railway

1. Install Railway CLI:
```bash
npm install -g @railway/cli
```

2. Deploy:
```bash
railway init
railway up
```

3. Set environment variables in Railway dashboard

## 📦 Requirements File

Create `requirements.txt`:
```txt
flask==3.0.0
flask-cors==4.0.0
supabase==2.0.0
python-dotenv==1.0.0
pandas==2.0.3
```

## 🎉 Next Steps

1. ✅ API fetches from database
2. ✅ Dashboard displays all 17 LGUs
3. ⬜ Deploy API to production (Vercel/Render/Railway)
4. ⬜ Update GitHub Actions to log predictions to database
5. ⬜ Add historical data view (date range queries)

---

**Created**: November 3, 2025  
**Author**: May Pasok Ba Team  
**Version**: 1.0.0
