"""
Analyze Model Performance Against Actual Suspensions
=====================================================

Compares predicted suspensions vs actual suspensions for Sept-Oct 2025.
Calculates key metrics: True Positives, False Positives, False Negatives, True Negatives.
"""

import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Paths
BACKFILL_DIR = Path(__file__).parent
PREDICTIONS_FILE = BACKFILL_DIR / "output" / "predictions_sept_oct.json"
ACTUALS_FILE = BACKFILL_DIR / "actual_suspensions_sept_oct.json"

def load_data():
    """Load predictions and actual suspensions."""
    with open(PREDICTIONS_FILE, 'r', encoding='utf-8') as f:
        pred_data = json.load(f)
        predictions = pred_data.get('predictions', [])
    
    with open(ACTUALS_FILE, 'r', encoding='utf-8') as f:
        actuals = json.load(f)
    
    return predictions, actuals

def create_actual_suspension_set(actuals):
    """Create a set of (date, lgu) tuples for actual suspensions."""
    suspension_set = set()
    
    # Handle the nested structure
    suspensions = actuals.get('suspensions', [])
    
    for record in suspensions:
        date = record['date']
        suspension_details = record.get('suspension_details', {})
        
        for lgu, details in suspension_details.items():
            if details.get('suspended', False):
                suspension_set.add((date, lgu))
    
    return suspension_set

def analyze_predictions(predictions, actual_suspensions):
    """Analyze predictions against actual suspensions."""
    
    # Metrics
    true_positives = []  # Predicted suspension AND actually suspended
    false_positives = []  # Predicted suspension BUT not suspended
    false_negatives = []  # Did NOT predict BUT was suspended
    true_negatives = []  # Predicted normal AND was normal
    
    # Date-level analysis
    date_analysis = defaultdict(lambda: {
        'tp': 0, 'fp': 0, 'fn': 0, 'tn': 0,
        'predicted_lgus': [],
        'actual_lgus': []
    })
    
    # Process each prediction
    for pred in predictions:
        date = pred['prediction_date']
        lgu = pred['lgu']
        predicted_suspension = pred['predicted_suspended']
        prob = pred['suspension_probability']
        
        # Get risk tier info
        risk_tier = pred.get('risk_tier', {})
        risk_level = risk_tier.get('tier', 'unknown')
        
        actual_key = (date, lgu)
        actually_suspended = actual_key in actual_suspensions
        
        # Classify
        if predicted_suspension and actually_suspended:
            # TRUE POSITIVE: Correctly predicted suspension
            true_positives.append({
                'date': date,
                'lgu': lgu,
                'probability': prob,
                'risk_level': risk_level
            })
            date_analysis[date]['tp'] += 1
            date_analysis[date]['predicted_lgus'].append(lgu)
            date_analysis[date]['actual_lgus'].append(lgu)
            
        elif predicted_suspension and not actually_suspended:
            # FALSE POSITIVE: Predicted suspension but didn't happen
            false_positives.append({
                'date': date,
                'lgu': lgu,
                'probability': prob,
                'risk_level': risk_level
            })
            date_analysis[date]['fp'] += 1
            date_analysis[date]['predicted_lgus'].append(lgu)
            
        elif not predicted_suspension and actually_suspended:
            # FALSE NEGATIVE: Missed suspension
            false_negatives.append({
                'date': date,
                'lgu': lgu,
                'probability': prob,
                'risk_level': risk_level
            })
            date_analysis[date]['fn'] += 1
            date_analysis[date]['actual_lgus'].append(lgu)
            
        else:
            # TRUE NEGATIVE: Correctly predicted no suspension
            true_negatives.append({
                'date': date,
                'lgu': lgu,
                'probability': prob
            })
            date_analysis[date]['tn'] += 1
    
    return {
        'tp': true_positives,
        'fp': false_positives,
        'fn': false_negatives,
        'tn': true_negatives,
        'date_analysis': dict(date_analysis)
    }

def calculate_metrics(results):
    """Calculate performance metrics."""
    tp_count = len(results['tp'])
    fp_count = len(results['fp'])
    fn_count = len(results['fn'])
    tn_count = len(results['tn'])
    
    total = tp_count + fp_count + fn_count + tn_count
    
    # Metrics
    accuracy = (tp_count + tn_count) / total if total > 0 else 0
    precision = tp_count / (tp_count + fp_count) if (tp_count + fp_count) > 0 else 0
    recall = tp_count / (tp_count + fn_count) if (tp_count + fn_count) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    # F2 score (emphasizes recall)
    beta = 2
    f2 = (1 + beta**2) * (precision * recall) / (beta**2 * precision + recall) if (precision + recall) > 0 else 0
    
    # Specificity (True Negative Rate)
    specificity = tn_count / (tn_count + fp_count) if (tn_count + fp_count) > 0 else 0
    
    return {
        'total_predictions': total,
        'true_positives': tp_count,
        'false_positives': fp_count,
        'false_negatives': fn_count,
        'true_negatives': tn_count,
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1_score': f1,
        'f2_score': f2,
        'specificity': specificity
    }

def print_results(results, metrics):
    """Print analysis results."""
    
    print("=" * 80)
    print("📊 SUSPENSION PREDICTION ANALYSIS")
    print("=" * 80)
    print()
    
    # Overall metrics
    print("🎯 OVERALL METRICS")
    print("-" * 80)
    print(f"Total Predictions: {metrics['total_predictions']:,}")
    print(f"Accuracy: {metrics['accuracy']:.1%}")
    print(f"Precision: {metrics['precision']:.1%}")
    print(f"Recall (Sensitivity): {metrics['recall']:.1%}")
    print(f"F1 Score: {metrics['f1_score']:.4f}")
    print(f"F2 Score: {metrics['f2_score']:.4f}")
    print(f"Specificity: {metrics['specificity']:.1%}")
    print()
    
    # Confusion Matrix
    print("📋 CONFUSION MATRIX")
    print("-" * 80)
    print(f"                    Predicted NO  │  Predicted YES")
    print(f"Actually NO    │    {metrics['true_negatives']:>6}       │    {metrics['false_positives']:>6}")
    print(f"Actually YES   │    {metrics['false_negatives']:>6}       │    {metrics['true_positives']:>6}")
    print()
    
    # True Positives
    print("✅ TRUE POSITIVES (Correctly Predicted Suspensions)")
    print("-" * 80)
    if results['tp']:
        print(f"Total: {len(results['tp'])} suspension events correctly predicted")
        
        # Group by date
        tp_by_date = defaultdict(list)
        for tp in results['tp']:
            tp_by_date[tp['date']].append(tp['lgu'])
        
        print(f"\nDates with correct predictions:")
        for date in sorted(tp_by_date.keys()):
            lgus = tp_by_date[date]
            print(f"  📅 {date}: {len(lgus)} LGUs - {', '.join(sorted(lgus)[:3])}{'...' if len(lgus) > 3 else ''}")
    else:
        print("None - Model did not correctly predict any suspensions")
    print()
    
    # False Negatives (Missed Suspensions)
    print("❌ FALSE NEGATIVES (Missed Suspension Announcements)")
    print("-" * 80)
    if results['fn']:
        print(f"Total: {len(results['fn'])} suspension events MISSED by model")
        
        # Group by date
        fn_by_date = defaultdict(list)
        for fn in results['fn']:
            fn_by_date[fn['date']].append((fn['lgu'], fn['probability']))
        
        print(f"\nMissed suspension dates:")
        for date in sorted(fn_by_date.keys()):
            items = fn_by_date[date]
            lgus = [lgu for lgu, _ in items]
            avg_prob = sum(prob for _, prob in items) / len(items)
            print(f"  ⚠️  {date}: {len(lgus)} LGUs missed (avg prob: {avg_prob:.1%})")
            for lgu, prob in sorted(items, key=lambda x: x[1], reverse=True)[:5]:
                print(f"      • {lgu}: {prob:.1%}")
    else:
        print("None - Model caught all suspensions!")
    print()
    
    # False Positives
    print("⚡ FALSE POSITIVES (False Alarms)")
    print("-" * 80)
    if results['fp']:
        print(f"Total: {len(results['fp'])} false alarms")
        
        # Group by date
        fp_by_date = defaultdict(list)
        for fp in results['fp']:
            fp_by_date[fp['date']].append((fp['lgu'], fp['probability']))
        
        print(f"\nDates with false alarms:")
        for date in sorted(fp_by_date.keys())[:10]:  # Show first 10
            items = fp_by_date[date]
            lgus = [lgu for lgu, _ in items]
            avg_prob = sum(prob for _, prob in items) / len(items)
            print(f"  🔔 {date}: {len(lgus)} LGUs (avg prob: {avg_prob:.1%})")
    else:
        print("None - No false alarms!")
    print()
    
    # Date-level analysis
    print("📅 DATE-LEVEL PERFORMANCE")
    print("-" * 80)
    
    date_stats = results['date_analysis']
    dates_with_suspensions = [d for d, stats in date_stats.items() 
                             if stats['tp'] > 0 or stats['fn'] > 0]
    
    if dates_with_suspensions:
        print(f"Dates with actual suspensions: {len(dates_with_suspensions)}\n")
        
        for date in sorted(dates_with_suspensions):
            stats = date_stats[date]
            tp = stats['tp']
            fn = stats['fn']
            fp = stats['fp']
            total_actual = tp + fn
            
            if total_actual > 0:
                date_recall = tp / total_actual
                status = "✅" if date_recall >= 0.8 else "⚠️" if date_recall >= 0.5 else "❌"
                
                print(f"{status} {date}:")
                print(f"   Caught: {tp}/{total_actual} LGUs ({date_recall:.1%})")
                if fn > 0:
                    print(f"   Missed: {fn} LGUs")
                if fp > 0:
                    print(f"   False alarms: {fp} LGUs")
                print()
    
    print("=" * 80)

def main():
    """Main analysis function."""
    print("\n🔍 Loading data...")
    predictions, actuals = load_data()
    
    print(f"   Predictions: {len(predictions)} records")
    print(f"   Actuals: {len(actuals)} records")
    
    # Create set of actual suspensions
    actual_suspensions = create_actual_suspension_set(actuals)
    print(f"   Actual suspensions: {len(actual_suspensions)} events")
    print()
    
    # Analyze
    results = analyze_predictions(predictions, actual_suspensions)
    metrics = calculate_metrics(results)
    
    # Print results
    print_results(results, metrics)
    
    # Save detailed results
    output = {
        'analysis_date': datetime.now().isoformat(),
        'metrics': metrics,
        'true_positives': results['tp'][:20],  # Sample
        'false_negatives': results['fn'],  # All missed suspensions
        'date_summary': {
            date: {
                'tp': stats['tp'],
                'fp': stats['fp'],
                'fn': stats['fn'],
                'tn': stats['tn']
            }
            for date, stats in results['date_analysis'].items()
        }
    }
    
    output_file = BACKFILL_DIR / "output" / "performance_analysis.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Detailed results saved to: {output_file}")

if __name__ == "__main__":
    main()
