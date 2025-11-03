# Risk Tier Integration - Web Dashboard

## Overview

The web dashboard (`web/index.html`) now displays **risk tier interpretations** instead of raw probabilities, providing actionable guidance for DepEd officials.

## What Changed

### 1. **Enhanced Prediction Card Rendering**

**Before** (raw probability):
```
┌────────────────────────────┐
│   56% Chance of Suspension │
│   ⛈️                       │
└────────────────────────────┘
```

**After** (risk tier):
```
┌─────────────────────────────────────────┐
│  🟠  WEATHER ALERT                      │
│      Enhanced monitoring needed         │
│                                          │
│  ⚠️ Recommendation:                     │
│  Prepare for possible suspension        │
│                                          │
│  📋 Recommended Actions:                │
│  ✓ Monitor updates every 2 hours        │
│  ✓ Prepare early dismissal plan         │
│  ✓ Coordinate with DRRM office          │
│                                          │
│  Weather: Very heavy rain expected      │
│  Forecast: 35.5mm precipitation         │
│  PAGASA: Orange Rainfall Warning        │
│                                          │
│  ⏰ Enhanced monitoring (every 2 hours) │
└─────────────────────────────────────────┘
```

### 2. **Backward Compatibility**

The dashboard automatically detects whether prediction data includes risk tiers:

- **New format** (with `risk_tier` and `weather_context`): Shows enhanced risk tier UI
- **Legacy format** (without risk tiers): Falls back to original UI

No breaking changes! Dashboard works with both old and new data formats.

### 3. **Data Flow**

```
Real-time Pipeline:
scripts/collect_and_log.py
    ↓ (generates predictions with risk tiers)
web/predictions/latest.json
    ↓ (fetched by dashboard)
web/index.html
    ↓ (renders risk tier UI)
User sees actionable guidance ✨

Historical Pipeline:
backfill/generate_predictions.py
    ↓ (generates 1,037 predictions with risk tiers)
backfill/output/predictions_sept_oct.json
    ↓ (uploaded to database)
web/api/get_historical_predictions.py (future)
    ↓ (serves historical data)
web/index.html
    ↓ (renders historical risk tiers)
```

## Code Changes

### Modified Functions

#### 1. `renderPredictionCard(recommendation, probability, riskTier, weatherContext)`
- **New parameters**: `riskTier`, `weatherContext` (optional)
- **Logic**: 
  - If `riskTier` exists → call `renderRiskTierCard()`
  - Else → use legacy rendering

#### 2. `renderRiskTierCard(riskTier, weatherContext, probability)`
- **New function**: Renders enhanced risk tier UI
- **Features**:
  - Color-coded tier cards (🟢/🟠/🔴)
  - Actionable recommendations
  - Action checklists (✓ checkmarks)
  - Weather context display
  - Monitoring interval guidance
  - Model confidence footer

#### 3. `renderLGUDetails(lguName)`
- **Updated**: Extracts `risk_tier` and `weather_context` from prediction data
- **Backward compatible**: Works if these fields are missing

#### 4. `renderMetroManilaSummary()`
- **Updated**: Aggregates risk tiers across all LGUs
- **Logic**:
  - Counts tier distribution (normal/alert/suspension)
  - Determines dominant tier
  - Uses dominant tier for Metro Manila summary

## JSON Schema

### New Prediction Format (with risk tiers)

```json
{
  "prediction_date": "2025-11-03",
  "lgu": "Manila",
  "suspension_probability": 0.487,
  "predicted_suspended": false,
  "risk_tier": {
    "tier": "alert",
    "color": "#f97316",
    "emoji": "🟠",
    "status_icon": "⚠️",
    "title": "WEATHER ALERT",
    "subtitle": "Enhanced monitoring needed",
    "recommendation": "Prepare for possible suspension",
    "actions": [
      "Monitor updates every 2 hours",
      "Prepare early dismissal plan",
      "Coordinate with DRRM office"
    ],
    "monitoring_interval": "Enhanced monitoring (every 2 hours)"
  },
  "weather_context": {
    "weather_desc": "Very heavy rain expected",
    "precipitation": "35.5mm precipitation",
    "pagasa_advisory": "PAGASA: Orange Rainfall Warning"
  }
}
```

### Legacy Format (backward compatible)

```json
{
  "prediction_date": "2025-11-03",
  "lgu": "Manila",
  "suspension_probability": 0.487,
  "predicted_suspended": false,
  "recommendation": "Monitor"
}
```

## Testing

### Test with Sample Data

```powershell
# Copy sample data with risk tiers
cd c:\Users\zyra\Documents\new-capstone\web
Copy-Item predictions\sample_with_tiers.json predictions\latest.json

# Open dashboard
explorer.exe index.html

# Test scenarios:
# 1. Select "Manila" → See 🟠 ORANGE tier (alert)
# 2. Select "Quezon City" → See 🟠 ORANGE tier (alert, suspended)
# 3. Select "Caloocan" → See 🟢 GREEN tier (normal)
```

### Restore Original Data

```powershell
# Restore backup
Copy-Item predictions\latest_backup.json predictions\latest.json
```

## Deployment

### 1. Update Real-time Pipeline

The pipeline is already integrated! Next run of `scripts/collect_and_log.py` will:
- Generate predictions with risk tiers
- Save to `web/predictions/latest.json`
- Dashboard automatically displays risk tier UI

### 2. Deploy to GitHub Pages

```powershell
# Commit updated files
git add web/index.html web/predictions/sample_with_tiers.json
git commit -m "feat: integrate risk tier UI in dashboard"
git push origin main

# GitHub Actions will:
# 1. Run collect_and_log.py (generates risk tier data)
# 2. Deploy to GitHub Pages
# 3. Users see risk tier UI automatically
```

### 3. Database Integration (Future)

When historical data API is ready:
- `web/api/get_historical_predictions.py` will include risk tier data
- Dashboard will fetch and render historical risk tiers
- Users can compare risk tier predictions vs actual outcomes

## UI Features

### Color Coding

| Tier | Color | Background | Use Case |
|------|-------|------------|----------|
| 🟢 GREEN | `#22c55e` | Light green gradient | Probability <40% |
| 🟠 ORANGE | `#f97316` | Light orange gradient | Probability 40-55% |
| 🔴 RED | `#ef4444` | Light red gradient | Probability >55% |

### Metro Manila Aggregation

When viewing "Metro Manila" (all LGUs):
- Dashboard counts tier distribution across 17 LGUs
- Displays **dominant tier** (most common)
- Example:
  - 10 LGUs = 🟢 GREEN
  - 5 LGUs = 🟠 ORANGE
  - 2 LGUs = 🔴 RED
  - **Result**: Shows 🟢 GREEN (dominant)

### Responsive Design

- Mobile-friendly card layout
- Action checklists adapt to screen size
- Weather context wraps gracefully

## Benefits

### For DepEd Officials
✅ **Clear decisions**: No "is 52% enough?" confusion  
✅ **Actionable steps**: Know what to do immediately  
✅ **Monitoring guidance**: Explicit check-in intervals  
✅ **PAGASA alignment**: Cross-validated with official advisories

### For System
✅ **Backward compatible**: Works with old and new data  
✅ **No API changes**: Existing endpoints still work  
✅ **Progressive enhancement**: Better UI when tier data available  
✅ **Easy rollback**: Remove tier logic if needed

## Troubleshooting

### Issue: Dashboard shows raw probability instead of tier

**Cause**: Prediction data doesn't have `risk_tier` field

**Fix**:
1. Check if `latest.json` has `risk_tier` in predictions
2. If missing, re-run `scripts/collect_and_log.py`
3. Verify risk tier module imported correctly

### Issue: Tier colors not showing

**Cause**: CSS not rendering gradient backgrounds

**Fix**:
1. Check browser console for errors
2. Ensure `renderRiskTierCard()` function exists
3. Clear browser cache

### Issue: Metro Manila tier incorrect

**Cause**: Tier aggregation logic issue

**Fix**:
1. Open browser dev tools → Console
2. Look for `Risk tier aggregation:` log
3. Verify tier counts match expectations

## Future Enhancements

1. **Historical Tier Trends**: Show tier distribution over time (chart)
2. **LGU Tier Comparison**: Side-by-side tier view for all LGUs
3. **Tier Change Alerts**: Notify when tier escalates (🟢→🟠→🔴)
4. **Accuracy Tracking**: Show tier prediction accuracy vs actual
5. **Custom Thresholds**: Allow users to adjust 40%/55% thresholds

## Files Modified

- ✅ `web/index.html` - Added risk tier rendering functions
- ✅ `web/predictions/sample_with_tiers.json` - Test data
- ✅ `scripts/collect_and_log.py` - Already integrated (no changes needed!)
- ✅ `backfill/generate_predictions.py` - Already integrated (no changes needed!)

## Related Documentation

- `src/weather/RISK_TIERS.md` - Full risk tier system specification
- `RISK_TIER_INTEGRATION_SUMMARY.md` - Implementation summary
- `web/risk-tier-preview.html` - Standalone tier UI preview

---

**Status**: ✅ Fully integrated and tested  
**Deployment**: Ready for production  
**Backward Compatibility**: 100% maintained
