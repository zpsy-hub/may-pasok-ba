# 🚀 Supabase Quick Reference

## 📋 One-Page Setup Guide

### 1️⃣ Create Account (2 min)
```
1. Go to: https://supabase.com
2. Sign in with GitHub
3. Click "New Project"
   - Name: suspension-predictions
   - Region: Singapore
   - Password: Generate strong password
   - Plan: Free
```

### 2️⃣ Run Schema (30 sec)
```
1. Open SQL Editor in Supabase dashboard
2. Copy database/schema.sql
3. Paste and click "Run"
```

### 3️⃣ Get Credentials (30 sec)
```
Settings → API:
- Project URL: https://xxxxx.supabase.co
- service_role key: eyJhbG... (long string)
```

### 4️⃣ Add to GitHub (1 min)
```
Repo → Settings → Secrets → Actions:
- SUPABASE_URL = <project URL>
- SUPABASE_KEY = <service_role key>
```

### 5️⃣ Test Locally (1 min)
```powershell
pip install supabase
$env:SUPABASE_URL = "https://xxxxx.supabase.co"
$env:SUPABASE_KEY = "eyJhbG..."
python database/supabase_client.py
```

---

## 💻 Python Quick Start

### Basic Usage
```python
from database.supabase_client import SupabaseLogger

logger = SupabaseLogger()

# Log predictions
predictions = [{
    'prediction_date': '2025-11-02',
    'lgu': 'Manila',
    'suspension_probability': 0.82,
    'predicted_suspended': True
}]
logger.log_predictions(predictions, 'v1.0.0', 0.5)

# Log weather
weather_df = pd.DataFrame({
    'weather_date': ['2025-11-02'],
    'lgu': ['Manila'],
    'precipitation_sum': [15.5]
})
logger.log_weather_data(weather_df, 'forecast')

# Log PAGASA
pagasa = {
    'has_active_typhoon': True,
    'typhoon_name': 'TINO',
    'tcws_level': 2
}
logger.log_pagasa_status(pagasa)

# Get data
predictions = logger.get_latest_predictions(limit=10)
accuracy = logger.get_prediction_accuracy()
```

---

## 🌐 JavaScript Quick Start (Dashboard)

### Fetch Data
```javascript
const SUPABASE_URL = 'https://xxxxx.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbG...';  // Use anon key!

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

## 🗄️ Tables Summary

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `daily_predictions` | Model predictions | date, lgu, probability, actual |
| `weather_data` | Weather observations | date, lgu, precipitation, wind |
| `pagasa_status` | Typhoon warnings | date, typhoon_name, tcws_level |
| `collection_logs` | Run tracking | date, success flags, errors |
| `model_metadata` | Model versions | version, accuracy, f1, auc |

---

## 📊 Analytics Views

```sql
-- Prediction accuracy per LGU
SELECT * FROM prediction_accuracy_by_lgu;

-- Weather correlation with suspensions
SELECT * FROM weather_suspension_correlation;

-- PAGASA impact analysis
SELECT * FROM pagasa_impact_analysis;

-- Collection reliability
SELECT * FROM collection_reliability;
```

---

## 🔑 Keys Explained

| Key Type | Use Case | Access Level |
|----------|----------|--------------|
| `service_role` | GitHub Actions | Full write access |
| `anon` | Dashboard | Read-only access |

**Never commit keys to repo! Use GitHub Secrets.**

---

## 📈 Free Tier Limits

| Resource | Limit | Your Usage | Status |
|----------|-------|------------|--------|
| Storage | 500 MB | ~20 MB/year | ✅ 4% |
| Bandwidth | 2 GB/month | ~54 MB/month | ✅ 2.7% |
| API Requests | Unlimited | Unlimited | ✅ |

**Can run 20+ years on free tier!**

---

## 🚨 Troubleshooting

| Error | Solution |
|-------|----------|
| "Invalid API key" | Use service_role (not anon) for writes |
| "Relation does not exist" | Run schema.sql in SQL Editor |
| "Duplicate key violation" | Predictions use upsert (auto-handles) |
| Connection timeout | Check SUPABASE_URL is correct |

---

## 🔗 Important Links

- **Dashboard**: https://app.supabase.com
- **Docs**: https://supabase.com/docs
- **Python Client**: https://supabase.com/docs/reference/python
- **REST API**: https://supabase.com/docs/guides/api

---

## 📂 File Locations

```
database/
├── schema.sql              # Run this in Supabase SQL Editor
├── supabase_client.py      # Python wrapper (import this)
├── README.md               # Full documentation
└── ARCHITECTURE.md         # System diagram

scripts/
└── collect_and_log.py      # Integration example

requirements.txt            # Updated with supabase
```

---

## ⚡ Common Commands

```powershell
# Install
pip install supabase

# Set credentials (Windows)
$env:SUPABASE_URL = "https://xxxxx.supabase.co"
$env:SUPABASE_KEY = "eyJhbG..."

# Test connection
python database/supabase_client.py

# Run collection
python scripts/collect_and_log.py
```

---

## ✅ Deployment Checklist

- [ ] Created Supabase account
- [ ] Ran schema.sql
- [ ] Added GitHub Secrets
- [ ] Tested locally
- [ ] Updated workflow
- [ ] First successful run

**Setup time: 5-10 minutes total**

---

## 🎯 Key Benefits

✅ Zero maintenance (fully managed)  
✅ Free forever (for this use case)  
✅ Easy Python integration  
✅ Built-in REST API for dashboard  
✅ Real-time capabilities  
✅ Automatic backups  
✅ Row Level Security  

---

**Need help?** See `database/README.md` for full documentation!
