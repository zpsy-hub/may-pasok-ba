"""
Generate Prediction Logs with Performance Metrics

This script combines historical predictions with actual suspension outcomes
to calculate accuracy metrics and generate a formatted JSON for the dashboard.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple
from collections import defaultdict

# Paths
BACKFILL_DIR = Path(__file__).parent
OUTPUT_DIR = BACKFILL_DIR / 'output'
WEB_DIR = BACKFILL_DIR.parent / 'web'

PREDICTIONS_FILE = OUTPUT_DIR / 'predictions_sept_oct.json'
ACTUAL_SUSPENSIONS_FILE = BACKFILL_DIR / 'actual_suspensions_sept_oct.json'
WEATHER_FILE = OUTPUT_DIR / 'weather_sept_oct.json'
OUTPUT_FILE = WEB_DIR / 'prediction_logs.json'


def load_json(filepath: Path) -> Any:
    """Load JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def normalize_lgu_name(lgu: str) -> str:
    """Normalize LGU names for matching."""
    # Handle common variations
    mapping = {
        'las pinas': 'Las Piñas',
        'las piñas': 'Las Piñas',
        'las piã±as': 'Las Piñas',  # Fix UTF-8 encoding issue
        'paranaque': 'Parañaque',
        'parañaque': 'Parañaque',
        'paraã±aque': 'Parañaque',  # Fix UTF-8 encoding issue
        'quezon city': 'Quezon City',
        'san juan': 'San Juan',
    }
    
    normalized = lgu.strip()
    lower = normalized.lower()
    
    if lower in mapping:
        return mapping[lower]
    
    return normalized.title()


def build_actual_suspensions_lookup(actual_data: Dict) -> Dict[str, Dict[str, bool]]:
    """
    Build a lookup dict: {date: {lgu: was_suspended}}
    """
    lookup = defaultdict(lambda: defaultdict(bool))
    
    for suspension_day in actual_data['suspensions']:
        date = suspension_day['date']
        
        # Get all LGUs and their suspension status
        for lgu, details in suspension_day['suspension_details'].items():
            normalized_lgu = normalize_lgu_name(lgu)
            was_suspended = details.get('suspended', False)
            lookup[date][normalized_lgu] = was_suspended
    
    return dict(lookup)


def build_daily_weather_summary(weather_data: Dict) -> Dict[str, Dict[str, Any]]:
    """
    Build daily weather summary (averaged across all LGUs).
    Returns: {date: {avg_temp, avg_rainfall, max_wind, avg_humidity}}
    """
    daily_summary = {}
    
    for date, lgus_data in weather_data.items():
        temps = []
        rainfall = []
        winds = []
        humidity = []
        
        for lgu, weather in lgus_data.items():
            if weather.get('temperature_2m_max'):
                temps.append(weather['temperature_2m_max'])
            if weather.get('precipitation_sum'):
                rainfall.append(weather['precipitation_sum'])
            if weather.get('wind_speed_10m_max'):
                winds.append(weather['wind_speed_10m_max'])
            if weather.get('relative_humidity_2m_mean'):
                humidity.append(weather['relative_humidity_2m_mean'])
        
        daily_summary[date] = {
            'avg_temp': round(sum(temps) / len(temps), 1) if temps else None,
            'avg_rainfall': round(sum(rainfall) / len(rainfall), 1) if rainfall else None,
            'max_wind': round(max(winds), 1) if winds else None,
            'avg_humidity': round(sum(humidity) / len(humidity), 0) if humidity else None
        }
    
    return daily_summary


def calculate_performance_metrics(predictions_with_actual: List[Dict]) -> Dict[str, Any]:
    """
    Calculate confusion matrix and performance metrics.
    
    Metrics:
    - True Positive (TP): Predicted suspension AND actually suspended
    - False Positive (FP): Predicted suspension BUT NOT suspended
    - True Negative (TN): Predicted no suspension AND correct
    - False Negative (FN): Predicted no suspension BUT WAS suspended
    """
    tp = 0  # Correctly predicted suspension
    fp = 0  # False alarm (predicted suspension, didn't happen)
    tn = 0  # Correctly predicted no suspension
    fn = 0  # Missed suspension (didn't predict, but it happened)
    
    correct_predictions = 0
    total_predictions = 0
    
    # Track predictions by risk tier
    tier_counts = defaultdict(int)
    tier_correct = defaultdict(int)
    
    # Track by LGU
    lgu_stats = defaultdict(lambda: {'total': 0, 'correct': 0, 'tp': 0, 'fp': 0, 'tn': 0, 'fn': 0})
    
    for pred in predictions_with_actual:
        # Skip if no actual outcome data
        if pred['actual_suspended'] is None:
            continue
        
        total_predictions += 1
        predicted = pred['predicted_suspended']
        actual = pred['actual_suspended']
        lgu = pred['lgu']
        tier = pred['risk_tier']['tier']
        
        # Calculate confusion matrix
        if predicted and actual:
            tp += 1
            lgu_stats[lgu]['tp'] += 1
        elif predicted and not actual:
            fp += 1
            lgu_stats[lgu]['fp'] += 1
        elif not predicted and not actual:
            tn += 1
            lgu_stats[lgu]['tn'] += 1
        elif not predicted and actual:
            fn += 1
            lgu_stats[lgu]['fn'] += 1
        
        # Track correctness
        is_correct = predicted == actual
        if is_correct:
            correct_predictions += 1
            tier_correct[tier] += 1
            lgu_stats[lgu]['correct'] += 1
        
        tier_counts[tier] += 1
        lgu_stats[lgu]['total'] += 1
    
    # Calculate metrics
    accuracy = correct_predictions / total_predictions if total_predictions > 0 else 0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    # False positive rate
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
    
    # Calculate per-tier accuracy
    tier_accuracy = {}
    for tier, count in tier_counts.items():
        tier_accuracy[tier] = (tier_correct[tier] / count) if count > 0 else 0
    
    # Calculate per-LGU metrics
    lgu_metrics = {}
    for lgu, stats in lgu_stats.items():
        total = stats['total']
        if total == 0:
            continue
        
        lgu_accuracy = stats['correct'] / total
        lgu_precision = stats['tp'] / (stats['tp'] + stats['fp']) if (stats['tp'] + stats['fp']) > 0 else 0
        lgu_recall = stats['tp'] / (stats['tp'] + stats['fn']) if (stats['tp'] + stats['fn']) > 0 else 0
        
        lgu_metrics[lgu] = {
            'accuracy': round(lgu_accuracy, 4),
            'precision': round(lgu_precision, 4),
            'recall': round(lgu_recall, 4),
            'total_predictions': total,
            'correct': stats['correct'],
            'tp': stats['tp'],
            'fp': stats['fp'],
            'tn': stats['tn'],
            'fn': stats['fn']
        }
    
    return {
        'confusion_matrix': {
            'true_positive': tp,
            'false_positive': fp,
            'true_negative': tn,
            'false_negative': fn
        },
        'overall_metrics': {
            'accuracy': round(accuracy, 4),
            'precision': round(precision, 4),
            'recall': round(recall, 4),
            'f1_score': round(f1_score, 4),
            'false_positive_rate': round(fpr, 4)
        },
        'prediction_summary': {
            'total_predictions': total_predictions,
            'correct_predictions': correct_predictions,
            'incorrect_predictions': total_predictions - correct_predictions,
            'accuracy_percentage': round(accuracy * 100, 2)
        },
        'tier_accuracy': {tier: round(acc, 4) for tier, acc in tier_accuracy.items()},
        'lgu_metrics': lgu_metrics
    }


def generate_metadata(predictions: List[Dict], performance: Dict) -> Dict[str, Any]:
    """Generate metadata summary."""
    dates = set()
    lgus = set()
    probabilities = []
    risk_distribution = defaultdict(int)
    pagasa_trigger_count = 0
    
    for pred in predictions:
        dates.add(pred['prediction_date'])
        lgus.add(pred['lgu'])
        probabilities.append(pred['suspension_probability'])
        risk_distribution[pred['risk_tier']['tier']] += 1
        
        if pred.get('pagasa_context', {}).get('has_active_typhoon'):
            pagasa_trigger_count += 1
    
    return {
        'total_predictions': len(predictions),
        'unique_dates': len(dates),
        'unique_lgus': len(lgus),
        'average_probability': round(sum(probabilities) / len(probabilities), 4),
        'max_probability': round(max(probabilities), 4),
        'min_probability': round(min(probabilities), 4),
        'risk_distribution': dict(risk_distribution),
        'predictions_with_pagasa_triggers': pagasa_trigger_count,
        'accuracy': performance['overall_metrics']['accuracy'],
        'precision': performance['overall_metrics']['precision'],
        'recall': performance['overall_metrics']['recall'],
        'f1_score': performance['overall_metrics']['f1_score'],
        'last_updated': datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
        'data_period': {
            'start': '2024-09-01',
            'end': '2024-10-31'
        }
    }


def format_prediction_for_dashboard(pred: Dict, actual_suspended: bool = None) -> Dict:
    """Format a prediction for the dashboard."""
    # Extract weather data if available
    weather = pred.get('weather_context', {})
    
    # Determine if prediction was correct
    prediction_correct = None
    if actual_suspended is not None:
        prediction_correct = pred['predicted_suspended'] == actual_suspended
    
    return {
        'prediction_date': pred['prediction_date'],
        'prediction_time': '06:00:00',  # Historical predictions made at 6 AM
        'lgu': normalize_lgu_name(pred['lgu']),  # Fix UTF-8 encoding issues
        'suspension_probability': round(pred['suspension_probability'], 4),
        'predicted_suspended': pred['predicted_suspended'],
        'risk_level': pred['risk_tier']['tier'].upper(),
        'risk_tier': pred['risk_tier']['title'],
        'recommendation': pred['risk_tier']['recommendation'],
        'model_used': pred.get('model_version', 'v1.0.0'),
        'threshold_used': pred.get('threshold_used', 0.5),
        
        # PAGASA context
        'has_pagasa_triggers': pred.get('pagasa_context', {}).get('has_active_typhoon', False),
        'typhoon_name': pred.get('pagasa_context', {}).get('typhoon_name'),
        'tcws_level': pred.get('pagasa_context', {}).get('tcws_level', 0),
        'rainfall_warning': pred.get('pagasa_context', {}).get('rainfall_warning'),
        
        # Weather metrics (if available in weather_context)
        'rainfall_24h': weather.get('precipitation_sum'),
        'temp_max': weather.get('temperature_max'),
        'wind_speed': weather.get('wind_speed_max'),
        'humidity': weather.get('relative_humidity_max'),
        
        # Actual outcome and validation
        'actual_suspended': actual_suspended,
        'prediction_correct': prediction_correct
    }


def main():
    print("\n" + "="*60)
    print("GENERATING PREDICTION LOGS WITH PERFORMANCE METRICS")
    print("="*60)
    
    # Load data
    print("\n📂 Loading data...")
    predictions_data = load_json(PREDICTIONS_FILE)
    actual_suspensions = load_json(ACTUAL_SUSPENSIONS_FILE)
    weather_data = load_json(WEATHER_FILE)
    
    # Extract predictions array
    predictions_raw = predictions_data.get('predictions', predictions_data)
    
    print(f"   ✓ Loaded {len(predictions_raw)} predictions")
    print(f"   ✓ Loaded {len(actual_suspensions['suspensions'])} suspension days")
    print(f"   ✓ Loaded weather data for {len(weather_data)} days")
    
    # Build actual suspensions lookup
    print("\n🔍 Building suspension lookup...")
    actual_lookup = build_actual_suspensions_lookup(actual_suspensions)
    dates_with_outcomes = len(actual_lookup)
    print(f"   ✓ Indexed {dates_with_outcomes} dates with suspension outcomes")
    
    # Build weather summary
    print("\n🌤️  Building daily weather summary...")
    weather_summary = build_daily_weather_summary(weather_data)
    print(f"   ✓ Summarized weather for {len(weather_summary)} days")
    
    # Process predictions and match with actual outcomes
    print("\n🔗 Matching predictions with actual outcomes...")
    predictions_with_actual = []
    matched_count = 0
    
    for pred_raw in predictions_raw:
        date = pred_raw['prediction_date']
        lgu = normalize_lgu_name(pred_raw['lgu'])
        
        # Get actual outcome
        actual_suspended = None
        if date in actual_lookup and lgu in actual_lookup[date]:
            actual_suspended = actual_lookup[date][lgu]
            matched_count += 1
        
        # Add actual outcome to prediction
        pred_with_actual = pred_raw.copy()
        pred_with_actual['actual_suspended'] = actual_suspended
        predictions_with_actual.append(pred_with_actual)
    
    print(f"   ✓ Matched {matched_count} predictions with actual outcomes")
    print(f"   ⚠ {len(predictions_raw) - matched_count} predictions without outcome data")
    
    # Calculate performance metrics
    print("\n📊 Calculating performance metrics...")
    performance = calculate_performance_metrics(predictions_with_actual)
    
    cm = performance['confusion_matrix']
    om = performance['overall_metrics']
    
    print(f"\n   Confusion Matrix:")
    print(f"   ┌─────────────────┬─────────┬─────────┐")
    print(f"   │                 │ Actual+ │ Actual- │")
    print(f"   ├─────────────────┼─────────┼─────────┤")
    print(f"   │ Predicted+      │   {cm['true_positive']:>3}   │   {cm['false_positive']:>3}   │")
    print(f"   │ Predicted-      │   {cm['false_negative']:>3}   │   {cm['true_negative']:>3}   │")
    print(f"   └─────────────────┴─────────┴─────────┘")
    
    print(f"\n   Overall Metrics:")
    print(f"   • Accuracy:  {om['accuracy']*100:.2f}%")
    print(f"   • Precision: {om['precision']*100:.2f}%")
    print(f"   • Recall:    {om['recall']*100:.2f}%")
    print(f"   • F1 Score:  {om['f1_score']:.4f}")
    
    # Generate metadata
    print("\n📋 Generating metadata...")
    metadata = generate_metadata(predictions_with_actual, performance)
    
    # Format predictions for dashboard
    print("\n📝 Formatting predictions for dashboard...")
    formatted_predictions = []
    for pred in predictions_with_actual:
        formatted = format_prediction_for_dashboard(
            pred,
            pred['actual_suspended']
        )
        formatted_predictions.append(formatted)
    
    # Create final output
    output = {
        'metadata': metadata,
        'performance_metrics': performance,
        'daily_weather_summary': weather_summary,
        'predictions': formatted_predictions
    }
    
    # Save to file
    print(f"\n💾 Saving to {OUTPUT_FILE}...")
    OUTPUT_FILE.parent.mkdir(exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"   ✓ Saved {len(formatted_predictions)} predictions")
    print(f"   ✓ File size: {OUTPUT_FILE.stat().st_size / 1024:.1f} KB")
    
    # Summary
    print("\n" + "="*60)
    print("✨ GENERATION COMPLETE!")
    print("="*60)
    print(f"\nKey Statistics:")
    print(f"• Total Predictions: {metadata['total_predictions']}")
    print(f"• Date Range: {metadata['data_period']['start']} to {metadata['data_period']['end']}")
    print(f"• Unique LGUs: {metadata['unique_lgus']}")
    print(f"• Model Accuracy: {om['accuracy']*100:.2f}%")
    print(f"• True Positives: {cm['true_positive']} (correctly predicted suspensions)")
    print(f"• False Positives: {cm['false_positive']} (false alarms)")
    print(f"• False Negatives: {cm['false_negative']} (missed suspensions)")
    print(f"\nOutput: {OUTPUT_FILE}")
    print("\n✓ Ready to display in prediction-logs.html dashboard!")
    

if __name__ == '__main__':
    main()
