"""
Generate Historical Predictions for Sept-Oct 2025
==================================================

Loads the trained ML model and generates suspension predictions
for all historical feature vectors.

Input:
- model-training/data/processed/best_core_model.pkl (trained model)
- backfill/output/features_sept_oct.json (1,037 feature vectors)

Output:
- backfill/output/predictions_sept_oct.json (1,037 predictions)

Format matches web/predictions/latest.json for consistency.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
import joblib
import pandas as pd
import numpy as np

# Add src to path for risk_tiers import
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from weather.risk_tiers import interpret_prediction, get_tier_summary

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = Path(__file__).parent / "output"
FEATURES_FILE = OUTPUT_DIR / "features_sept_oct.json"
PREDICTIONS_OUTPUT = OUTPUT_DIR / "predictions_sept_oct.json"

# Model path
MODEL_DIR = PROJECT_ROOT / "model-training" / "data" / "processed"
MODEL_FILES = [
    "best_core_model.pkl",
    "core_model.pkl",
    "final_model.pkl"
]

# Prediction threshold
THRESHOLD = 0.5

# Feature order (must match model training)
FEATURE_ORDER = [
    'year', 'month', 'day', 'day_of_week', 'is_rainy_season',
    'month_from_sy_start', 'is_holiday', 'is_school_day', 'lgu_id',
    'mean_flood_risk_score', 'hist_precipitation_sum_t1',
    'hist_wind_speed_max_t1', 'hist_wind_gusts_max_t1',
    'hist_pressure_msl_min_t1', 'hist_temperature_max_t1',
    'hist_relative_humidity_mean_t1', 'hist_cloud_cover_max_t1',
    'hist_dew_point_mean_t1', 'hist_apparent_temperature_max_t1',
    'hist_weather_code_t1', 'hist_precip_sum_7d', 'hist_precip_sum_3d',
    'hist_wind_max_7d', 'fcst_precipitation_sum', 'fcst_precipitation_hours',
    'fcst_wind_speed_max', 'fcst_wind_gusts_max', 'fcst_pressure_msl_min',
    'fcst_temperature_max', 'fcst_relative_humidity_mean',
    'fcst_cloud_cover_max', 'fcst_dew_point_mean', 'fcst_cape_max'
]


def load_model():
    """Load the trained ML model."""
    print("📦 Loading ML model...")
    
    for model_file in MODEL_FILES:
        model_path = MODEL_DIR / model_file
        if model_path.exists():
            try:
                model = joblib.load(model_path)
                print(f"   ✅ Loaded: {model_file}")
                print(f"   Model type: {type(model).__name__}")
                return model
            except Exception as e:
                print(f"   ⚠️  Failed to load {model_file}: {e}")
                continue
    
    print("   ❌ No model found!")
    print(f"   Searched in: {MODEL_DIR}")
    print(f"   Looking for: {', '.join(MODEL_FILES)}")
    sys.exit(1)


def load_features():
    """Load feature vectors."""
    print("📥 Loading feature vectors...")
    
    with open(FEATURES_FILE, 'r') as f:
        data = json.load(f)
    
    feature_vectors = data['feature_vectors']
    print(f"   ✅ Loaded {len(feature_vectors)} feature vectors")
    
    return feature_vectors


def generate_predictions(model, feature_vectors):
    """
    Generate predictions for all feature vectors.
    
    Args:
        model: Trained scikit-learn model
        feature_vectors: List of feature vector dicts
    
    Returns:
        List of prediction dicts with risk tier interpretation
    """
    print()
    print("🔮 Generating predictions...")
    print()
    
    predictions = []
    dates_processed = set()
    
    for i, fv in enumerate(feature_vectors):
        date_str = fv['date']
        lgu = fv['lgu']
        features = fv['features']
        weather_data = fv.get('weather_data', {})
        pagasa_context = fv.get('pagasa_context', {})
        
        # Progress indicator
        if date_str not in dates_processed:
            print(f"   📅 Predicting {date_str}...")
            dates_processed.add(date_str)
        
        # Prepare feature DataFrame
        X = pd.DataFrame([features])[FEATURE_ORDER]
        
        # Get prediction
        try:
            # predict_proba returns [[prob_class_0, prob_class_1]]
            proba = model.predict_proba(X)[0, 1]
            
            # Apply threshold
            predicted_suspended = bool(proba >= THRESHOLD)
            
            # Get risk tier interpretation
            interpretation = interpret_prediction(
                probability=float(proba),
                lgu_name=lgu,
                date=date_str,
                precipitation_mm=weather_data.get('precipitation_sum'),
                weather_code=weather_data.get('weather_code'),
                pagasa_warning=pagasa_context.get('rainfall_warning'),
                tcws_level=pagasa_context.get('tcws_level', 0),
                typhoon_name=pagasa_context.get('active_typhoon')
            )
            
            # Create prediction record with risk tier
            prediction = {
                'prediction_date': date_str,
                'lgu': lgu,
                'suspension_probability': float(proba),
                'predicted_suspended': predicted_suspended,
                'risk_tier': interpretation['risk_tier'],
                'weather_context': interpretation['weather_context'],
                'model_version': 'v1.0.0',
                'threshold_used': THRESHOLD,
                # Include PAGASA context for analysis
                'pagasa_context': pagasa_context
            }
            
            predictions.append(prediction)
            
        except Exception as e:
            print(f"   ⚠️  Prediction failed for {date_str} - {lgu}: {e}")
            continue
    
    print()
    print(f"✅ Generated {len(predictions)} predictions")
    
    return predictions


def analyze_predictions(predictions):
    """Analyze prediction statistics including risk tier distribution."""
    print()
    print("=" * 70)
    print("📊 Prediction Analysis")
    print("=" * 70)
    
    # Overall statistics
    probabilities = [p['suspension_probability'] for p in predictions]
    suspended_count = sum(1 for p in predictions if p['predicted_suspended'])
    
    print(f"Total predictions: {len(predictions)}")
    print(f"Predicted suspensions: {suspended_count} "
          f"({suspended_count/len(predictions)*100:.1f}%)")
    print(f"Predicted no suspensions: {len(predictions) - suspended_count} "
          f"({(len(predictions) - suspended_count)/len(predictions)*100:.1f}%)")
    print()
    print("Probability statistics:")
    print(f"  Min: {min(probabilities):.4f}")
    print(f"  Max: {max(probabilities):.4f}")
    print(f"  Mean: {np.mean(probabilities):.4f}")
    print(f"  Median: {np.median(probabilities):.4f}")
    print(f"  Std: {np.std(probabilities):.4f}")
    print()
    
    # Risk tier distribution
    tier_summary = get_tier_summary(predictions)
    print("🚦 Risk Tier Distribution:")
    print(f"  🟢 GREEN (Normal): {tier_summary['tier_distribution']['green']['count']} "
          f"({tier_summary['tier_distribution']['green']['percentage']:.1f}%)")
    print(f"  🟠 ORANGE (Alert): {tier_summary['tier_distribution']['orange']['count']} "
          f"({tier_summary['tier_distribution']['orange']['percentage']:.1f}%)")
    print(f"  🔴 RED (Suspension): {tier_summary['tier_distribution']['red']['count']} "
          f"({tier_summary['tier_distribution']['red']['percentage']:.1f}%)")
    print(f"  ⚠️  Total alerts (Orange + Red): {tier_summary['highest_alert_count']}")
    print()
    
    # By date
    by_date = {}
    for p in predictions:
        date = p['prediction_date']
        if date not in by_date:
            by_date[date] = []
        by_date[date].append(p)
    
    suspension_days = []
    for date, preds in sorted(by_date.items()):
        suspended_lgus = sum(1 for p in preds if p['predicted_suspended'])
        if suspended_lgus > 0:
            # Get dominant risk tier for this day
            red_count = sum(1 for p in preds 
                          if p['risk_tier']['tier'] == 'suspension')
            orange_count = sum(1 for p in preds 
                             if p['risk_tier']['tier'] == 'alert')
            tier_emoji = "🔴" if red_count > orange_count else "🟠"
            suspension_days.append((date, suspended_lgus, tier_emoji))
    
    print(f"Days with predicted suspensions: {len(suspension_days)}")
    if suspension_days:
        print("\nTop 10 suspension days:")
        for date, count, emoji in sorted(suspension_days, 
                                        key=lambda x: x[1], 
                                        reverse=True)[:10]:
            print(f"  {emoji} {date}: {count}/17 LGUs ({count/17*100:.0f}%)")
    
    # By LGU
    by_lgu = {}
    for p in predictions:
        lgu = p['lgu']
        if lgu not in by_lgu:
            by_lgu[lgu] = []
        by_lgu[lgu].append(p)
    
    print()
    print("Most frequently predicted suspensions by LGU:")
    lgu_suspension_counts = []
    for lgu, preds in by_lgu.items():
        suspended_days = sum(1 for p in preds if p['predicted_suspended'])
        lgu_suspension_counts.append((lgu, suspended_days))
    
    for lgu, count in sorted(lgu_suspension_counts, 
                            key=lambda x: x[1], 
                            reverse=True)[:10]:
        total_days = len(by_lgu[lgu])
        print(f"  {lgu}: {count}/{total_days} days "
              f"({count/total_days*100:.1f}%)")
    
    # By TCWS level
    by_tcws = {}
    for p in predictions:
        tcws = p['pagasa_context']['tcws_level']
        if tcws not in by_tcws:
            by_tcws[tcws] = []
        by_tcws[tcws].append(p)
    
    print()
    print("Suspension rates by TCWS level:")
    for tcws in sorted(by_tcws.keys()):
        preds = by_tcws[tcws]
        suspended = sum(1 for p in preds if p['predicted_suspended'])
        print(f"  TCWS {tcws}: {suspended}/{len(preds)} "
              f"({suspended/len(preds)*100:.1f}%)")


def main():
    """Main prediction generation pipeline."""
    print("=" * 70)
    print("🔮 Historical Prediction Generation".center(70))
    print("=" * 70)
    print()
    
    # Load model and features
    model = load_model()
    feature_vectors = load_features()
    
    # Generate predictions
    predictions = generate_predictions(model, feature_vectors)
    
    # Analyze
    analyze_predictions(predictions)
    
    # Save to JSON
    print()
    print("=" * 70)
    print("💾 Saving Predictions")
    print("=" * 70)
    
    output_data = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "date_range": {
                "start": "2025-09-01",
                "end": "2025-10-31"
            },
            "model_version": "v1.0.0",
            "threshold": THRESHOLD,
            "prediction_count": len(predictions),
            "feature_count": 33,
            "note": "Historical predictions for Sept-Oct 2025 using trained ML model"
        },
        "predictions": predictions
    }
    
    with open(PREDICTIONS_OUTPUT, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    file_size_kb = PREDICTIONS_OUTPUT.stat().st_size / 1024
    
    print(f"File: {PREDICTIONS_OUTPUT.name}")
    print(f"Size: {file_size_kb:.1f} KB")
    print(f"Records: {len(predictions)}")
    print()
    
    print("=" * 70)
    print("✨ Prediction Generation Complete!")
    print("=" * 70)
    print()
    print("Next step:")
    print("  python backfill/upload_to_database.py")
    print()


if __name__ == "__main__":
    main()
