"""
Generate prediction_logs.json for the dashboard
Combines predictions with performance analysis
"""
import json
from datetime import datetime

# Load the predictions
with open('output/predictions_sept_oct.json', 'r') as f:
    predictions_data = json.load(f)

# Load the performance analysis
with open('output/performance_analysis.json', 'r') as f:
    performance = json.load(f)

# Load actual suspensions
with open('actual_suspensions_sept_oct.json', 'r') as f:
    actual_data = json.load(f)

# Create a set of (date, lgu) tuples for actual suspensions
actual_suspensions = set()
for suspension in actual_data.get('suspensions', []):
    date = suspension['date']
    for lgu, details in suspension.get('suspension_details', {}).items():
        if details.get('suspended', False):
            actual_suspensions.add((date, lgu))

predictions = predictions_data['predictions']
metadata = predictions_data['metadata']

# Add validation fields to each prediction
for p in predictions:
    date = p['prediction_date']
    lgu = p['lgu']
    predicted = p['predicted_suspended']
    actual = (date, lgu) in actual_suspensions
    
    # Add validation fields
    p['actual_suspended'] = actual if (date, lgu) in actual_suspensions or any(s['date'] == date for s in actual_data.get('suspensions', [])) else None
    if p['actual_suspended'] is not None:
        p['prediction_correct'] = (predicted == actual)
    else:
        p['prediction_correct'] = None

# Calculate statistics
total_predictions = len(predictions)
probabilities = [p['suspension_probability'] for p in predictions]
avg_prob = sum(probabilities) / len(probabilities)
max_prob = max(probabilities)
min_prob = min(probabilities)

# Count risk distribution
risk_dist = {'normal': 0, 'alert': 0, 'suspension': 0}
for p in predictions:
    tier = p['risk_tier']['tier']
    risk_dist[tier] += 1

# Count PAGASA triggers
pagasa_count = sum(1 for p in predictions if p['pagasa_context']['has_active_typhoon'] or 
                   p['pagasa_context']['rainfall_warning'] not in ['NONE', 'None'])

# Get unique dates and LGUs
unique_dates = len(set(p['prediction_date'] for p in predictions))
unique_lgus = len(set(p['lgu'] for p in predictions))

# Calculate daily weather summary
daily_weather = {}
for p in predictions:
    date = p['prediction_date']
    if date not in daily_weather:
        daily_weather[date] = {
            'temps': [],
            'rainfall': [],
            'wind': [],
            'humidity': []
        }
    
    # Extract weather data if available (these would come from the prediction context)
    # For now, we'll leave this empty as the data isn't in the predictions
    # This would need to be populated from the actual weather data sources

# Build the output JSON
output = {
    "metadata": {
        "total_predictions": total_predictions,
        "unique_dates": unique_dates,
        "unique_lgus": unique_lgus,
        "average_probability": round(avg_prob, 4),
        "max_probability": round(max_prob, 4),
        "min_probability": round(min_prob, 4),
        "risk_distribution": risk_dist,
        "predictions_with_pagasa_triggers": pagasa_count,
        "accuracy": round(performance['metrics']['accuracy'], 4),
        "precision": round(performance['metrics']['precision'], 4),
        "recall": round(performance['metrics']['recall'], 4),
        "f1_score": round(performance['metrics']['f1_score'], 4),
        "f2_score": round(performance['metrics']['f2_score'], 4),
        "last_updated": datetime.now().isoformat(),
        "data_period": {
            "start": metadata['date_range']['start'],
            "end": metadata['date_range']['end']
        }
    },
    "performance_metrics": {
        "confusion_matrix": {
            "true_positive": performance['metrics']['true_positives'],
            "false_positive": performance['metrics']['false_positives'],
            "true_negative": performance['metrics']['true_negatives'],
            "false_negative": performance['metrics']['false_negatives']
        },
        "overall_metrics": {
            "accuracy": round(performance['metrics']['accuracy'], 4),
            "precision": round(performance['metrics']['precision'], 4),
            "recall": round(performance['metrics']['recall'], 4),
            "f1_score": round(performance['metrics']['f1_score'], 4),
            "f2_score": round(performance['metrics']['f2_score'], 4),
            "specificity": round(performance['metrics']['specificity'], 4)
        },
        "prediction_summary": {
            "total_predictions": total_predictions,
            "correct_predictions": performance['metrics']['true_positives'] + performance['metrics']['true_negatives'],
            "incorrect_predictions": performance['metrics']['false_positives'] + performance['metrics']['false_negatives'],
            "accuracy_percentage": round(performance['metrics']['accuracy'] * 100, 2)
        }
    },
    "daily_weather_summary": {},  # Would need actual weather data
    "predictions": predictions
}

# Save to docs folder
output_path = '../docs/prediction_logs.json'
with open(output_path, 'w') as f:
    json.dump(output, f, indent=2)

print(f"✅ Generated prediction_logs.json")
print(f"   Total predictions: {total_predictions:,}")
print(f"   Accuracy: {performance['metrics']['accuracy']*100:.1f}%")
print(f"   Precision: {performance['metrics']['precision']*100:.1f}%")
print(f"   Recall: {performance['metrics']['recall']*100:.1f}%")
print(f"   F2 Score: {performance['metrics']['f2_score']:.4f}")
print(f"\n   Confusion Matrix:")
print(f"   ├─ True Positives:  {performance['metrics']['true_positives']}")
print(f"   ├─ False Positives: {performance['metrics']['false_positives']}")
print(f"   ├─ False Negatives: {performance['metrics']['false_negatives']}")
print(f"   └─ True Negatives:  {performance['metrics']['true_negatives']}")
print(f"\n   Risk Distribution:")
print(f"   ├─ 🟢 Normal:     {risk_dist['normal']}")
print(f"   ├─ 🟠 Alert:      {risk_dist['alert']}")
print(f"   └─ 🔴 Suspension: {risk_dist['suspension']}")
print(f"\n   Saved to: {output_path}")
