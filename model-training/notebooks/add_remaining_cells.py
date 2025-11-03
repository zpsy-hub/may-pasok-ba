"""
Script to add remaining cells to the calibration threshold analysis notebook
"""
import json
from pathlib import Path

notebook_path = Path("06_calibration_threshold_analysis.ipynb")

# Read existing notebook
with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Define remaining cells to add
remaining_cells = [
    # Section 7: Threshold Analysis Tables
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "---\n",
            "## 📋 Section 7: Threshold Analysis Tables (Key Methods)"
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            'print("="*80)\n',
            'print("THRESHOLD ANALYSIS: KEY METHODS")\n',
            'print("="*80)\n',
            '\n',
            '# Select key methods to display\n',
            "key_methods = ['Uncalibrated', 'Temp_T0_5', 'Temp_T2_0', 'Platt', 'Isotonic']\n",
            'key_methods = [m for m in key_methods if m in calibration_methods]\n',
            '\n',
            'for method_key in key_methods:\n',
            '    method_name = calibration_methods[method_key][\'name\']\n',
            '    method_data = threshold_df[threshold_df[\'Method_Key\'] == method_key].copy()\n',
            '    \n',
            '    print(f"\\n{\'=\'*80}")\n',
            '    print(f"Method: {method_name}")\n',
            '    print(f"{\'=\'*80}")\n',
            '    \n',
            '    # Get a constant metric to show it\'s truly constant\n',
            '    mean_prob = method_data[\'Overall_Mean_Prob\'].iloc[0]\n',
            '    ece = method_data[\'ECE\'].iloc[0]\n',
            '    sep = method_data[\'Separation\'].iloc[0]\n',
            '    \n',
            '    print(f"\\n📌 CONSTANT METRICS (threshold-independent):")\n',
            '    print(f"   Overall Mean Probability: {mean_prob:.4f} ({mean_prob:.2%})")\n',
            '    print(f"   ECE: {ece:.4f}")\n',
            '    print(f"   Separation: {sep:.4f}")\n',
            '    \n',
            '    print(f"\\n📊 VARYING METRICS (threshold-dependent):")\n',
            '    print("-" * 100)\n',
            '    print(f"{\'Thresh\':>8} {\'F2\':>8} {\'Recall\':>8} {\'Prec\':>8} {\'N_Pred\':>10} {\'TP\':>6} {\'FP\':>6} {\'FN\':>6}")\n',
            '    print("-" * 100)\n',
            '    \n',
            '    for _, row in method_data.iterrows():\n',
            '        print(f"{row[\'Threshold\']:>8.2f} "\n',
            '              f"{row[\'F2\']:>8.4f} "\n',
            '              f"{row[\'Recall\']:>8.4f} "\n',
            '              f"{row[\'Precision\']:>8.4f} "\n',
            '              f"{row[\'N_Predicted_Positive\']:>10d} "\n',
            '              f"{row[\'TP\']:>6d} "\n',
            '              f"{row[\'FP\']:>6d} "\n',
            '              f"{row[\'FN\']:>6d}")\n',
            '    \n',
            '    print("-" * 100)\n',
            '    \n',
            '    # Find best threshold for F2\n',
            '    best_row = method_data.loc[method_data[\'F2\'].idxmax()]\n',
            '    print(f"\\n✅ Best F2: {best_row[\'F2\']:.4f} at threshold = {best_row[\'Threshold\']:.2f}")\n',
            '    print(f"   Recall: {best_row[\'Recall\']:.4f}, Precision: {best_row[\'Precision\']:.4f}")\n',
            '    print(f"   Predictions: {best_row[\'N_Predicted_Positive\']}/{len(y_test)} ({best_row[\'N_Predicted_Positive\']/len(y_test):.2%})")'
        ]
    },
]

# Add cells to notebook
nb['cells'].extend(remaining_cells)

# Save
with open(notebook_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print(f"Added {len(remaining_cells)} cells. Total cells now: {len(nb['cells'])}")
