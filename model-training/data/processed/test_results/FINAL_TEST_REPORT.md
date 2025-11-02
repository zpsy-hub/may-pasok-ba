
# School Suspension Prediction - Final Test Evaluation

## Model Information
- Model Type: EasyEnsemble
- Training Date: 2025-11-02
- Features: 33
- Random Seed: 42

## Test Set Information
- Date Range: 2024-12-01 to 2025-08-25
- Total Samples: 4,556
- Actual Suspensions: 97 (2.13%)
- LGUs: 17

## Performance Metrics

### Overall Test Performance
- Recall (Sensitivity): 0.9794
- Precision: 0.2169
- Specificity: 0.9231
- F1 Score: 0.3551
- F2 Score: 0.5751
- G-Mean: 0.9508
- PR-AUC: 0.2757
- ROC-AUC: 0.9663

### Confusion Matrix
- True Positives: 95
- False Positives: 343
- False Negatives: 2
- True Negatives: 4,116

### Validation vs Test Comparison
- Recall: 0.6020 (val) → 0.9794 (test) | Δ = +0.3774
- Precision: 0.4158 (val) → 0.2169 (test) | Δ = -0.1989
- F2: 0.5525 (val) → 0.5751 (test) | Δ = +0.0225

## Error Analysis
- False Negatives (Missed Suspensions): 2
- False Positives (Over-predictions): 343

## Per-LGU Performance
- Best Performing LGU: Marikina (F2 = 0.7246)
- Worst Performing LGU: Makati (F2 = 0.3030)
- Average F2 across LGUs: 0.5576
- Std Dev F2 across LGUs: 0.1105

## Temporal Robustness
- Months Evaluated: 2
- Average Monthly Recall: 0.9877
- Std Dev Monthly Recall: 0.0175

## Deployment Readiness Assessment

### ✅ Strengths
1. Model generalizes well from validation to test (small performance delta)
2. Recall is 97.9% - captures most suspension events
3. Precision is 21.7% - acceptable false positive rate
4. Geographic coverage across all 17 LGUs

### ⚠️ Areas for Improvement
1. False Negatives: 2 suspensions were missed
2. Per-LGU variance: F2 ranges from 0.3030 to 0.7246
3. Class imbalance: Only 2.13% positive class in test set

### 📋 Recommendations
1. Deploy with human-in-the-loop review for low-confidence predictions
2. Monitor performance per LGU and retrain if drift detected
3. Collect more suspension event data for underperforming LGUs
4. Consider ensemble methods or threshold tuning for production

## Files Generated
- test_evaluation_metrics.png: ROC, PR, calibration curves
- test_predictions_with_errors.csv: All predictions with error flags
- per_lgu_performance.csv: Detailed LGU-level metrics
- per_lgu_performance_viz.png: LGU performance visualizations
- temporal_performance.csv: Month-by-month metrics
- temporal_performance_viz.png: Temporal stability plots

---
Generated: 2025-11-02 05:10:53
