# Risk Tier Interpretation System

## Overview

The Risk Tier system converts raw ML model probabilities into actionable, human-centered guidance for DepEd officials making class suspension decisions.

## Design Principles

1. **Traffic Light Metaphor**: Universal understanding (🟢 = Safe, 🟠 = Caution, 🔴 = Stop)
2. **Action-Oriented**: Focuses on what to do, not just prediction
3. **Removes False Precision**: No raw percentages shown to end users
4. **DepEd-Aligned**: Matches decision-making workflow
5. **PAGASA Integration**: Cross-validates with official weather advisories

## Tier Definitions

### 🟢 GREEN - Normal Operations (<40% probability)

**User Message**:
```
┌─────────────────────────────────┐
│   🟢 NORMAL CONDITIONS           │
│                                  │
│   Continue routine operations    │
│   No suspension expected         │
│                                  │
│   Weather: Light rain possible   │
│   Forecast: 15mm precipitation   │
└─────────────────────────────────┘
```

**Actions**:
- Continue regular class schedule
- Monitor weather updates
- Maintain standard preparedness protocols

**Monitoring Interval**: Standard (daily)

**Threshold**: Model probability < 40%

**Calibration**: Based on clear weather scenario (37.6% probability at 15mm rainfall)

---

### 🟠 ORANGE - Enhanced Alert (40-55% probability)

**User Message**:
```
┌─────────────────────────────────┐
│   🟠 WEATHER ALERT               │
│                                  │
│   ⚠️  Enhanced monitoring needed │
│   Prepare for possible suspension│
│                                  │
│   Weather: Heavy rain likely     │
│   Forecast: 35mm precipitation   │
│   PAGASA: Orange Advisory        │
│                                  │
│   📋 Recommendation:             │
│   • Monitor updates every 2 hours│
│   • Prepare early dismissal plan │
│   • Coordinate with DRRM office  │
└─────────────────────────────────┘
```

**Actions**:
- Monitor updates every 2 hours
- Prepare early dismissal plan
- Coordinate with DRRM office
- Review evacuation procedures
- Activate weather monitoring team
- (If TCWS ≥1) Monitor PAGASA typhoon bulletins

**Monitoring Interval**: Enhanced (every 2 hours)

**Threshold**: 40% ≤ Model probability < 55%

**Calibration**: Based on heavy rain scenario (50.1% probability at 35mm rainfall)

---

### 🔴 RED - Suspension Recommended (>55% probability)

**User Message**:
```
┌─────────────────────────────────┐
│   🔴 CLASS SUSPENSION            │
│                                  │
│   ⛔ STRONG SUSPENSION SIGNAL    │
│   Severe weather conditions      │
│                                  │
│   Weather: Very heavy rain       │
│   Forecast: 65mm precipitation   │
│   PAGASA: Red Rainfall Warning   │
│                                  │
│   🎓 DepEd Recommendation:       │
│   SUSPEND face-to-face classes   │
│                                  │
│   📱 Next steps:                 │
│   • Issue suspension announcement│
│   • Activate online learning     │
│   • Monitor for multi-day impact │
└─────────────────────────────────┘
```

**Actions**:
- Issue suspension announcement
- Activate online/modular learning
- Monitor for multi-day impact
- Coordinate with local government
- Ensure student safety protocols active
- (If TCWS ≥2) Activate disaster response protocols
- (If TCWS ≥2) Secure school facilities

**Monitoring Interval**: Continuous (hourly)

**Threshold**: Model probability ≥ 55%

**Calibration**: Based on typhoon scenario (57.2% probability at 65mm rainfall)

---

## Weather Context Integration

Each tier includes contextual weather information:

### Precipitation Descriptions
- < 7.5mm: "Light rain possible"
- 7.5-15mm: "Moderate rain expected"
- 15-30mm: "Heavy rain likely"
- 30-60mm: "Very heavy rain expected"
- ≥60mm: "Intense rainfall expected"

### PAGASA Advisory Display
- If rainfall warning exists: "PAGASA: {YELLOW/ORANGE/RED} Rainfall Warning"
- If TCWS active: "PAGASA: TCWS Signal No. {1-5} ({Typhoon Name})"

---

## Implementation

### Python Module: `src/weather/risk_tiers.py`

```python
from src.weather.risk_tiers import interpret_prediction, get_tier_summary

# For individual prediction
interpretation = interpret_prediction(
    probability=0.572,
    lgu_name="Manila",
    date="2025-11-03",
    precipitation_mm=65.0,
    weather_code=63,
    pagasa_warning="RED",
    tcws_level=2,
    typhoon_name="Opong"
)

# Returns:
{
    "lgu": "Manila",
    "date": "2025-11-03",
    "model_probability": 0.572,
    "risk_tier": {
        "tier": "suspension",
        "color": "#ef4444",
        "emoji": "🔴",
        "status_icon": "⛔",
        "title": "CLASS SUSPENSION",
        "subtitle": "Severe weather conditions",
        "recommendation": "SUSPEND face-to-face classes",
        "actions": [...],
        "monitoring_interval": "Continuous monitoring (hourly)"
    },
    "weather_context": {
        "weather_desc": "Intense rainfall expected",
        "precipitation": "65.0mm precipitation",
        "pagasa_advisory": "PAGASA: TCWS Signal No. 2 (Opong)"
    }
}

# For summary statistics
tier_summary = get_tier_summary(predictions)
# Returns distribution: green/orange/red counts and percentages
```

### Integration Points

1. **Historical Predictions** (`backfill/generate_predictions.py`):
   - Adds `risk_tier` and `weather_context` to each prediction
   - Includes tier distribution in analysis output
   - Shows tier emojis in suspension day rankings

2. **Real-time Pipeline** (`scripts/collect_and_log.py`):
   - Interprets live predictions before saving
   - Adds risk tier to JSON output for dashboard
   - Enables actionable display in web UI

3. **Web Dashboard** (future integration):
   - Display tier color and emoji
   - Show recommendation and actions
   - Hide raw probability from end users
   - Update monitoring interval based on tier

---

## Validation Against Real Data (Sept-Oct 2025)

### Historical Performance

**Actual Suspension Days** (6 days):
- Sept 1, 22-26

**Model Risk Tier Predictions**:
- Sept 21-22: 🔴 RED tier (100% LGU suspension rate)
- Sept 23: 🟠 ORANGE tier (76% LGU suspension rate)
- Sept 25: 🟠 ORANGE tier (88% LGU suspension rate)
- Sept 26: 🟠 ORANGE tier (41% LGU suspension rate)

**TCWS Correlation**:
- TCWS 0: 10.8% suspension rate (enhanced monsoon effect)
- TCWS 1: 88.2% suspension rate (Opong approaching, Sept 25)
- TCWS 2: 41.2% suspension rate (Opong direct threat, Sept 26)

**Key Insight**: Model correctly elevated risk on enhanced monsoon days (Sept 22-23) despite TCWS 0, validating weather-first (not TCWS-first) approach.

---

## Behavioral Science Rationale

### Why Not Show Raw Probabilities?

1. **False Precision**: 56.3% vs 58.7% creates illusion of certainty
2. **Decision Paralysis**: "Is 52% enough to suspend?" leads to inconsistent decisions
3. **Threshold Confusion**: Different officials use different cutoffs

### Why Three Tiers?

1. **Green**: Clear go-ahead (routine operations)
2. **Orange**: Prepares decision-makers without forcing decision (enhanced monitoring)
3. **Red**: Strong signal to act (suspend classes)

More tiers = more confusion. Fewer tiers = insufficient granularity.

### Why Action Lists?

**Instead of**: "48% chance of suspension"
**Users need**: "Monitor updates every 2 hours, prepare early dismissal plan"

Decision-makers need **operational guidance**, not probability estimates.

---

## Threshold Calibration History

| Version | Green Max | Orange Max | Rationale |
|---------|-----------|------------|-----------|
| v1.0 | 40% | 55% | Based on clear (37.6%), heavy rain (50.1%), typhoon (57.2%) calibration scenarios |

Future versions may adjust based on:
- False positive/negative rates in production
- DepEd feedback on actionability
- Regional variations in risk tolerance

---

## Future Enhancements

1. **Regional Thresholds**: Different thresholds for flood-prone LGUs
2. **Multi-Day Outlook**: Show tier forecast for next 3 days
3. **Confidence Intervals**: Add "High/Medium/Low confidence" qualifier
4. **Historical Context**: "Worst in X days" messaging
5. **Mobile Alerts**: Push notifications on tier changes

---

## References

- Traffic light metaphor: ISO 3864 safety colors
- Action-oriented design: Behavioral Insights Team (UK)
- DepEd suspension protocols: DepEd Order No. 37, s. 2022
- PAGASA rainfall warnings: PAGASA Circular 2024
- Threshold calibration: Model validation (Sept-Oct 2025)
