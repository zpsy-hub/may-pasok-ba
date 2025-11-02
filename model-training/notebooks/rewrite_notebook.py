import json
import sys

# Read user's template code
template_code = """# %% [markdown]

# # EDA and Model Training for Class Suspension Prediction

# 

# **Purpose:** Comprehensive EDA, model training, and evaluation for rainfall-based class suspension prediction

# 

# **Focus:** Test ALL model types and compare ALL metrics at the end

# 

# **Structure:**

# - Section 0-4: Setup, data loading, EDA, feature prep (NO feature selection)

# - Section 5-8: Baseline and tree-based models (RF, XGBoost, LightGBM)

# - Section 9: Additional ensemble models (ExtraTrees, BalancedRF, GradientBoosting)

# - Section 10: Cost-sensitive models

# - Section 11: Neural networks (multiple architectures)

# - Section 12: FINAL COMPREHENSIVE COMPARISON

# %%

# Cell 1: Import ALL libraries

import pandas as pd

import numpy as np

import matplotlib.pyplot as plt

import seaborn as sns

import warnings

from pathlib import Path

from collections import Counter

import joblib

# Machine Learning

from sklearn.dummy import DummyClassifier

from sklearn.linear_model import LogisticRegression

from sklearn.ensemble import RandomForestClassifier, IsolationForest, ExtraTreesClassifier, GradientBoostingClassifier

from sklearn.model_selection import TimeSeriesSplit, cross_val_score

from sklearn.metrics import (

    confusion_matrix, recall_score, precision_score, f1_score, fbeta_score,

    average_precision_score, brier_score_loss, precision_recall_curve,

    roc_auc_score, ConfusionMatrixDisplay, PrecisionRecallDisplay

)

from sklearn.inspection import PartialDependenceDisplay

from sklearn.calibration import calibration_curve, CalibratedClassifierCV

from sklearn.preprocessing import StandardScaler

# Imbalanced learning

from imblearn.over_sampling import SMOTE

from imblearn.ensemble import BalancedRandomForestClassifier

# Gradient boosting

import xgboost as xgb

import lightgbm as lgb

# Explainability

import shap

# Neural networks

try:

    import tensorflow as tf

    from tensorflow import keras

    from tensorflow.keras import layers

    from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau

    TENSORFLOW_AVAILABLE = True

    print(f"✅ TensorFlow {tf.__version__} available")

except ImportError:

    TENSORFLOW_AVAILABLE = False

    print("⚠️  TensorFlow not available - neural network section will be skipped")

# Display settings

pd.set_option('display.max_columns', None)

pd.set_option('display.max_rows', 100)

plt.style.use('seaborn-v0_8-darkgrid')

sns.set_palette('husl')

warnings.filterwarnings('ignore')

print("✅ All libraries imported successfully")

print(f"Pandas: {pd.__version__}")

print(f"NumPy: {np.__version__}")

print(f"XGBoost: {xgb.__version__}")

print(f"LightGBM: {lgb.__version__}")

print(f"SHAP: {shap.__version__}")

# %%

# Cell 2: Set constants and paths

RANDOM_SEED = 42

np.random.seed(RANDOM_SEED)

tf.random.set_seed(RANDOM_SEED) if TENSORFLOW_AVAILABLE else None

# LGU mapping (17 cities/municipalities)

LOCATION_MAPPING = {

    0: 'Manila', 1: 'Quezon City', 2: 'Caloocan', 3: 'Las Piñas',

    4: 'Makati', 5: 'Malabon', 6: 'Mandaluyong', 7: 'Marikina',

    8: 'Muntinlupa', 9: 'Navotas', 10: 'Parañaque', 11: 'Pasay',

    12: 'Pasig', 13: 'Pateros', 14: 'San Juan', 15: 'Taguig', 16: 'Valenzuela'

}

# File paths

DATA_DIR = Path('../data')

PROCESSED_DIR = DATA_DIR / 'processed'

MODELS_DIR = Path('../models')

MODELS_DIR.mkdir(parents=True, exist_ok=True)

# Rainy season months (June-November)

RAINY_MONTHS = [6, 7, 8, 9, 10, 11]

print("✅ Constants defined")

print(f"Random seed: {RANDOM_SEED}")

print(f"Total LGUs: {len(LOCATION_MAPPING)}")

# %%

# Cell 3: Define comprehensive metrics function

def compute_all_metrics(y_true, y_pred, y_proba=None, model_name="Model"):

    \"\"\"

    Compute all 8 core metrics for rare-event classification.

    

    Metrics:

    1. Recall/Sensitivity/TPR (primary for rare events)

    2. Precision/PPV

    3. Specificity/TNR

    4. F1 Score

    5. F2 Score (prioritizes recall)

    6. G-Mean (geometric mean of recall and specificity)

    7. PR-AUC (area under precision-recall curve)

    8. Brier Score (calibration quality)

    \"\"\"

    # Confusion matrix

    cm = confusion_matrix(y_true, y_pred)

    tn, fp, fn, tp = cm.ravel()

    

    # Core metrics

    recall = recall_score(y_true, y_pred, zero_division=0)

    precision = precision_score(y_true, y_pred, zero_division=0)

    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0

    f1 = f1_score(y_true, y_pred, zero_division=0)

    f2 = fbeta_score(y_true, y_pred, beta=2, zero_division=0)

    g_mean = np.sqrt(recall * specificity)

    

    # Probability-based metrics

    pr_auc = None

    brier = None

    if y_proba is not None:

        if len(y_proba.shape) > 1 and y_proba.shape[1] == 2:

            pr_auc = average_precision_score(y_true, y_proba[:, 1])

            brier = brier_score_loss(y_true, y_proba[:, 1])

        else:

            pr_auc = average_precision_score(y_true, y_proba)

            brier = brier_score_loss(y_true, y_proba)

    

    return {

        'Model': model_name,

        'TP': int(tp),

        'FP': int(fp),

        'FN': int(fn),

        'TN': int(tn),

        'Recall': recall,

        'Precision': precision,

        'Specificity': specificity,

        'F1': f1,

        'F2': f2,

        'G-Mean': g_mean,

        'PR-AUC': pr_auc,

        'Brier': brier

    }

def display_metrics(metrics_dict):

    \"\"\"Pretty print metrics dictionary.\"\"\"

    print(f"\\n{'='*60}")

    print(f"{metrics_dict['Model']}")

    print(f"{'='*60}")

    print(f"TP={metrics_dict['TP']}, FP={metrics_dict['FP']}, FN={metrics_dict['FN']}, TN={metrics_dict['TN']}")

    print(f"\\n  Recall:      {metrics_dict['Recall']:.4f}")

    print(f"  Precision:   {metrics_dict['Precision']:.4f}")

    print(f"  Specificity: {metrics_dict['Specificity']:.4f}")

    print(f"  F1:          {metrics_dict['F1']:.4f}")

    print(f"  F2:          {metrics_dict['F2']:.4f} ⭐")

    print(f"  G-Mean:      {metrics_dict['G-Mean']:.4f}")

    if metrics_dict['PR-AUC']:

        print(f"  PR-AUC:      {metrics_dict['PR-AUC']:.4f}")

    if metrics_dict['Brier']:

        print(f"  Brier:       {metrics_dict['Brier']:.4f}")

    print(f"{'='*60}\\n")

print("✅ Metrics functions defined")

# %% [markdown]

# ## Section 1: Data Loading & Validation

# %%

# Cell 4: Load pre-split datasets

print("Loading pre-split datasets...\\n")

train_df = pd.read_csv(PROCESSED_DIR / 'master_train.csv')

val_df = pd.read_csv(PROCESSED_DIR / 'master_validation.csv')

test_df = pd.read_csv(PROCESSED_DIR / 'master_test.csv')

# Parse dates

train_df['date'] = pd.to_datetime(train_df['date'])

val_df['date'] = pd.to_datetime(val_df['date'])

test_df['date'] = pd.to_datetime(test_df['date'])

print(f"✅ Loaded datasets:")

print(f"   Train:      {len(train_df):,} rows")

print(f"   Validation: {len(val_df):,} rows")

print(f"   Test:       {len(test_df):,} rows")

# Class imbalance

for name, df in [('Train', train_df), ('Val', val_df), ('Test', test_df)]:

    n_pos = df['suspension_occurred'].sum()

    ratio = (df['suspension_occurred'] == 0).sum() / n_pos if n_pos > 0 else 0

    print(f"\\n   {name}: {n_pos} suspensions ({df['suspension_occurred'].mean():.2%}), ratio {ratio:.1f}:1")

# %% [markdown]

# ## Section 2: Quick EDA (Visual Only)

# %%

# Cell 5: Quick EDA visualizations

fig, axes = plt.subplots(2, 2, figsize=(16, 10))

# 1. Class distribution

ax = axes[0, 0]

split_data = []

for name, df in [('Train', train_df), ('Val', val_df), ('Test', test_df)]:

    counts = df['suspension_occurred'].value_counts()

    split_data.append({'Split': name, 'No Suspension': counts.get(0, 0), 'Suspension': counts.get(1, 0)})

split_summary = pd.DataFrame(split_data)

x = np.arange(len(split_summary))

width = 0.35

ax.bar(x - width/2, split_summary['No Suspension'], width, label='No Suspension', alpha=0.8)

ax.bar(x + width/2, split_summary['Suspension'], width, label='Suspension', alpha=0.8)

ax.set_xlabel('Split')

ax.set_ylabel('Count')

ax.set_title('Class Distribution by Split')

ax.set_xticks(x)

ax.set_xticklabels(split_summary['Split'])

ax.legend()

ax.grid(axis='y', alpha=0.3)

# 2. Suspensions by LGU

ax = axes[0, 1]

lgu_susp = train_df.groupby('lgu_name')['suspension_occurred'].sum().sort_values(ascending=False)

ax.barh(lgu_susp.index, lgu_susp.values, alpha=0.8)

ax.set_xlabel('Total Suspensions')

ax.set_title('Suspensions by LGU (Training)')

ax.grid(axis='x', alpha=0.3)

# 3. Temporal pattern

ax = axes[1, 0]

daily_susp = train_df.groupby('date')['suspension_occurred'].sum()

ax.plot(daily_susp.index, daily_susp.values, alpha=0.6, linewidth=0.8)

ax.set_xlabel('Date')

ax.set_ylabel('Daily Suspensions')

ax.set_title('Suspensions Over Time')

ax.grid(alpha=0.3)

# 4. Monthly suspension rate

ax = axes[1, 1]

monthly_rate = train_df.groupby(train_df['date'].dt.month)['suspension_occurred'].mean()

bars = ax.bar(monthly_rate.index, monthly_rate.values * 100, alpha=0.8)

for i, bar in enumerate(bars):

    if monthly_rate.index[i] in RAINY_MONTHS:

        bar.set_color('steelblue')

    else:

        bar.set_color('lightcoral')

ax.set_xlabel('Month')

ax.set_ylabel('Suspension Rate (%)')

ax.set_title('Suspension Rate by Month')

ax.set_xticks(monthly_rate.index)

ax.set_xticklabels(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])

ax.grid(axis='y', alpha=0.3)

plt.tight_layout()

plt.show()

print("✅ EDA Complete")

# %% [markdown]

# ## Section 3: Feature Preparation (NO FEATURE SELECTION - Keep ALL)

# %%

# Cell 6: Feature preparation - KEEP ALL FEATURES

drop_cols = ['date', 'lgu_name', 'school_year', 'reason_category', 'flood_risk_classification']

# Get all feature columns

temporal_features = ['year', 'month', 'day', 'day_of_week', 'is_rainy_season', 'month_from_sy_start', 'is_school_day', 'is_holiday']

geography_features = ['lgu_id', 'mean_flood_risk_score']

weather_features = [col for col in train_df.columns if col.startswith('hist_') or col.startswith('fcst_')]

all_feature_cols = temporal_features + geography_features + weather_features

print("="*60)

print("FEATURE PREPARATION - KEEPING ALL FEATURES")

print("="*60)

print(f"\\n📊 Feature Groups:")

print(f"   Temporal:    {len(temporal_features)}")

print(f"   Geography:   {len(geography_features)}")

print(f"   Weather:     {len(weather_features)}")

print(f"   TOTAL:       {len(all_feature_cols)}")

# Handle missing values

for col in all_feature_cols:

    if train_df[col].isna().any():

        median_val = train_df[col].median()

        train_df[col] = train_df[col].fillna(median_val)

        val_df[col] = val_df[col].fillna(median_val)

        test_df[col] = test_df[col].fillna(median_val)

# Create X/y splits

X_train = train_df[all_feature_cols].copy()

y_train = train_df['suspension_occurred'].copy()

X_val = val_df[all_feature_cols].copy()

y_val = val_df['suspension_occurred'].copy()

X_test = test_df[all_feature_cols].copy()

y_test = test_df['suspension_occurred'].copy()

print(f"\\n✅ X/y splits created:")

print(f"   X_train: {X_train.shape}")

print(f"   X_val:   {X_val.shape}")

print(f"   X_test:  {X_test.shape}")

# Apply SMOTE once

print(f"\\n⚙️  Applying SMOTE...")

smote = SMOTE(random_state=RANDOM_SEED)

X_train_smote, y_train_smote = smote.fit_resample(X_train, y_train)

print(f"   Original: {Counter(y_train)}")

print(f"   SMOTE:    {Counter(y_train_smote)}")

# Calculate scale_pos_weight for XGBoost/LightGBM

n_neg = (y_train == 0).sum()

n_pos = (y_train == 1).sum()

scale_pos_weight = n_neg / n_pos

print(f"\\n✅ Feature preparation complete")

# Store all results

results_df = pd.DataFrame()

# %% [markdown]

# ## Section 4: Baseline Models

# %%

# Cell 7: Baseline models

print("="*60)

print("BASELINE MODELS")

print("="*60)

# 1. Dummy Classifier

print("\\n[1/3] Dummy Classifier...")

dummy_clf = DummyClassifier(strategy='most_frequent', random_state=RANDOM_SEED)

dummy_clf.fit(X_train, y_train)

y_pred = dummy_clf.predict(X_val)

y_proba = dummy_clf.predict_proba(X_val)

metrics = compute_all_metrics(y_val, y_pred, y_proba, "Dummy (Majority)")

display_metrics(metrics)

results_df = pd.concat([results_df, pd.DataFrame([metrics])], ignore_index=True)

# 2. Logistic Regression (default)

print("\\n[2/3] Logistic Regression (default)...")

lr_default = LogisticRegression(random_state=RANDOM_SEED, max_iter=1000)

lr_default.fit(X_train, y_train)

y_pred = lr_default.predict(X_val)

y_proba = lr_default.predict_proba(X_val)

metrics = compute_all_metrics(y_val, y_pred, y_proba, "LogReg (default)")

display_metrics(metrics)

results_df = pd.concat([results_df, pd.DataFrame([metrics])], ignore_index=True)

# 3. Logistic Regression (balanced)

print("\\n[3/3] Logistic Regression (balanced)...")

lr_balanced = LogisticRegression(class_weight='balanced', random_state=RANDOM_SEED, max_iter=1000)

lr_balanced.fit(X_train, y_train)

y_pred = lr_balanced.predict(X_val)

y_proba = lr_balanced.predict_proba(X_val)

metrics = compute_all_metrics(y_val, y_pred, y_proba, "LogReg (balanced)")

display_metrics(metrics)

results_df = pd.concat([results_df, pd.DataFrame([metrics])], ignore_index=True)

print(f"✅ Baseline models complete: {len(results_df)} models")

# %% [markdown]

# ## Section 5: Random Forest Models

# %%

# Cell 8: Random Forest - 4 configurations

print("="*60)

print("RANDOM FOREST MODELS")

print("="*60)

# 1. RF default

print("\\n[1/4] RF (default)...")

rf_default = RandomForestClassifier(n_estimators=100, random_state=RANDOM_SEED, n_jobs=-1)

rf_default.fit(X_train, y_train)

y_pred = rf_default.predict(X_val)

y_proba = rf_default.predict_proba(X_val)

metrics = compute_all_metrics(y_val, y_pred, y_proba, "RF (default)")

display_metrics(metrics)

results_df = pd.concat([results_df, pd.DataFrame([metrics])], ignore_index=True)

# 2. RF balanced

print("\\n[2/4] RF (balanced)...")

rf_balanced = RandomForestClassifier(n_estimators=100, class_weight='balanced', random_state=RANDOM_SEED, n_jobs=-1)

rf_balanced.fit(X_train, y_train)

y_pred = rf_balanced.predict(X_val)

y_proba = rf_balanced.predict_proba(X_val)

metrics = compute_all_metrics(y_val, y_pred, y_proba, "RF (balanced)")

display_metrics(metrics)

results_df = pd.concat([results_df, pd.DataFrame([metrics])], ignore_index=True)

# 3. RF + SMOTE

print("\\n[3/4] RF + SMOTE...")

rf_smote = RandomForestClassifier(n_estimators=100, random_state=RANDOM_SEED, n_jobs=-1)

rf_smote.fit(X_train_smote, y_train_smote)

y_pred = rf_smote.predict(X_val)

y_proba = rf_smote.predict_proba(X_val)

metrics = compute_all_metrics(y_val, y_pred, y_proba, "RF + SMOTE")

display_metrics(metrics)

results_df = pd.concat([results_df, pd.DataFrame([metrics])], ignore_index=True)

# 4. RF + SMOTE + balanced

print("\\n[4/4] RF + SMOTE + balanced...")

rf_smote_bal = RandomForestClassifier(n_estimators=100, class_weight='balanced', random_state=RANDOM_SEED, n_jobs=-1)

rf_smote_bal.fit(X_train_smote, y_train_smote)

y_pred = rf_smote_bal.predict(X_val)

y_proba = rf_smote_bal.predict_proba(X_val)

metrics = compute_all_metrics(y_val, y_pred, y_proba, "RF + SMOTE + balanced")

display_metrics(metrics)

results_df = pd.concat([results_df, pd.DataFrame([metrics])], ignore_index=True)

print(f"✅ Random Forest complete: {len(results_df)} total models")

# %% [markdown]

# ## Section 6: XGBoost Models

# %%

# Cell 9: XGBoost - 4 configurations

print("="*60)

print("XGBOOST MODELS")

print("="*60)

print(f"scale_pos_weight = {scale_pos_weight:.2f}")

# 1. XGBoost default

print("\\n[1/4] XGBoost (default)...")

xgb_default = xgb.XGBClassifier(n_estimators=100, random_state=RANDOM_SEED, eval_metric='logloss', use_label_encoder=False)

xgb_default.fit(X_train, y_train)

y_pred = xgb_default.predict(X_val)

y_proba = xgb_default.predict_proba(X_val)

metrics = compute_all_metrics(y_val, y_pred, y_proba, "XGBoost (default)")

display_metrics(metrics)

results_df = pd.concat([results_df, pd.DataFrame([metrics])], ignore_index=True)

# 2. XGBoost weighted

print("\\n[2/4] XGBoost (scale_pos_weight)...")

xgb_weighted = xgb.XGBClassifier(n_estimators=100, scale_pos_weight=scale_pos_weight, 

                                  random_state=RANDOM_SEED, eval_metric='logloss', use_label_encoder=False)

xgb_weighted.fit(X_train, y_train)

y_pred = xgb_weighted.predict(X_val)

y_proba = xgb_weighted.predict_proba(X_val)

metrics = compute_all_metrics(y_val, y_pred, y_proba, "XGBoost (weighted)")

display_metrics(metrics)

results_df = pd.concat([results_df, pd.DataFrame([metrics])], ignore_index=True)

# 3. XGBoost + SMOTE

print("\\n[3/4] XGBoost + SMOTE...")

xgb_smote = xgb.XGBClassifier(n_estimators=100, random_state=RANDOM_SEED, eval_metric='logloss', use_label_encoder=False)

xgb_smote.fit(X_train_smote, y_train_smote)

y_pred = xgb_smote.predict(X_val)

y_proba = xgb_smote.predict_proba(X_val)

metrics = compute_all_metrics(y_val, y_pred, y_proba, "XGBoost + SMOTE")

display_metrics(metrics)

results_df = pd.concat([results_df, pd.DataFrame([metrics])], ignore_index=True)

# 4. XGBoost + SMOTE + weighted

print("\\n[4/4] XGBoost + SMOTE + weighted...")

xgb_smote_w = xgb.XGBClassifier(n_estimators=100, scale_pos_weight=scale_pos_weight,

                                 random_state=RANDOM_SEED, eval_metric='logloss', use_label_encoder=False)

xgb_smote_w.fit(X_train_smote, y_train_smote)

y_pred = xgb_smote_w.predict(X_val)

y_proba = xgb_smote_w.predict_proba(X_val)

metrics = compute_all_metrics(y_val, y_pred, y_proba, "XGBoost + SMOTE + weighted")

display_metrics(metrics)

results_df = pd.concat([results_df, pd.DataFrame([metrics])], ignore_index=True)

print(f"✅ XGBoost complete: {len(results_df)} total models")

# %% [markdown]

# ## Section 7: LightGBM Models

# %%

# Cell 10: LightGBM - 4 configurations

print("="*60)

print("LIGHTGBM MODELS")

print("="*60)

# 1. LightGBM default

print("\\n[1/4] LightGBM (default)...")

lgb_default = lgb.LGBMClassifier(n_estimators=100, random_state=RANDOM_SEED, verbose=-1)

lgb_default.fit(X_train, y_train)

y_pred = lgb_default.predict(X_val)

y_proba = lgb_default.predict_proba(X_val)

metrics = compute_all_metrics(y_val, y_pred, y_proba, "LightGBM (default)")

display_metrics(metrics)

results_df = pd.concat([results_df, pd.DataFrame([metrics])], ignore_index=True)

# 2. LightGBM unbalanced

print("\\n[2/4] LightGBM (is_unbalance)...")

lgb_unbal = lgb.LGBMClassifier(n_estimators=100, is_unbalance=True, random_state=RANDOM_SEED, verbose=-1)

lgb_unbal.fit(X_train, y_train)

y_pred = lgb_unbal.predict(X_val)

y_proba = lgb_unbal.predict_proba(X_val)

metrics = compute_all_metrics(y_val, y_pred, y_proba, "LightGBM (is_unbalance)")

display_metrics(metrics)

results_df = pd.concat([results_df, pd.DataFrame([metrics])], ignore_index=True)

# 3. LightGBM + SMOTE

print("\\n[3/4] LightGBM + SMOTE...")

lgb_smote = lgb.LGBMClassifier(n_estimators=100, random_state=RANDOM_SEED, verbose=-1)

lgb_smote.fit(X_train_smote, y_train_smote)

y_pred = lgb_smote.predict(X_val)

y_proba = lgb_smote.predict_proba(X_val)

metrics = compute_all_metrics(y_val, y_pred, y_proba, "LightGBM + SMOTE")

display_metrics(metrics)

results_df = pd.concat([results_df, pd.DataFrame([metrics])], ignore_index=True)

# 4. LightGBM + SMOTE + unbalanced

print("\\n[4/4] LightGBM + SMOTE + is_unbalance...")

lgb_smote_u = lgb.LGBMClassifier(n_estimators=100, is_unbalance=True, random_state=RANDOM_SEED, verbose=-1)

lgb_smote_u.fit(X_train_smote, y_train_smote)

y_pred = lgb_smote_u.predict(X_val)

y_proba = lgb_smote_u.predict_proba(X_val)

metrics = compute_all_metrics(y_val, y_pred, y_proba, "LightGBM + SMOTE + is_unbalance")

display_metrics(metrics)

results_df = pd.concat([results_df, pd.DataFrame([metrics])], ignore_index=True)

print(f"✅ LightGBM complete: {len(results_df)} total models")

# %% [markdown]

# ## Section 8: Additional Ensemble Models

# %%

# Cell 11: Additional ensemble models

print("="*60)

print("ADDITIONAL ENSEMBLE MODELS")

print("="*60)

# 1. ExtraTreesClassifier

print("\\n[1/3] ExtraTreesClassifier + SMOTE...")

et_clf = ExtraTreesClassifier(n_estimators=100, min_samples_split=20, min_samples_leaf=10,

                               random_state=RANDOM_SEED, n_jobs=-1)

et_clf.fit(X_train_smote, y_train_smote)

y_pred = et_clf.predict(X_val)

y_proba = et_clf.predict_proba(X_val)

metrics = compute_all_metrics(y_val, y_pred, y_proba, "ExtraTrees + SMOTE")

display_metrics(metrics)

results_df = pd.concat([results_df, pd.DataFrame([metrics])], ignore_index=True)

# 2. BalancedRandomForestClassifier

print("\\n[2/3] BalancedRandomForestClassifier...")

brf_clf = BalancedRandomForestClassifier(n_estimators=100, random_state=RANDOM_SEED, n_jobs=-1)

brf_clf.fit(X_train, y_train)

y_pred = brf_clf.predict(X_val)

y_proba = brf_clf.predict_proba(X_val)

metrics = compute_all_metrics(y_val, y_pred, y_proba, "BalancedRF")

display_metrics(metrics)

results_df = pd.concat([results_df, pd.DataFrame([metrics])], ignore_index=True)

# 3. GradientBoostingClassifier

print("\\n[3/3] GradientBoostingClassifier + SMOTE...")

gb_clf = GradientBoostingClassifier(n_estimators=100, learning_rate=0.05, max_depth=3,

                                     min_samples_split=20, random_state=RANDOM_SEED)

gb_clf.fit(X_train_smote, y_train_smote)

y_pred = gb_clf.predict(X_val)

y_proba = gb_clf.predict_proba(X_val)

metrics = compute_all_metrics(y_val, y_pred, y_proba, "GradientBoosting + SMOTE")

display_metrics(metrics)

results_df = pd.concat([results_df, pd.DataFrame([metrics])], ignore_index=True)

print(f"✅ Additional ensembles complete: {len(results_df)} total models")

# %% [markdown]

# ## Section 9: Cost-Sensitive Models

# %%

# Cell 12: Cost-sensitive variants

print("="*60)

print("COST-SENSITIVE MODELS (Reduced False Positives)")

print("="*60)

reduced_weight = scale_pos_weight * 0.25

print(f"Reduced weight: {reduced_weight:.2f}")

# 1. XGBoost conservative

print("\\n[1/2] XGBoost (conservative)...")

xgb_cons = xgb.XGBClassifier(n_estimators=100, scale_pos_weight=reduced_weight,

                              random_state=RANDOM_SEED, eval_metric='logloss', use_label_encoder=False)

xgb_cons.fit(X_train, y_train)

y_pred = xgb_cons.predict(X_val)

y_proba = xgb_cons.predict_proba(X_val)

metrics = compute_all_metrics(y_val, y_pred, y_proba, "XGBoost (conservative)")

display_metrics(metrics)

results_df = pd.concat([results_df, pd.DataFrame([metrics])], ignore_index=True)

# 2. LightGBM conservative

print("\\n[2/2] LightGBM (conservative)...")

lgb_cons = lgb.LGBMClassifier(n_estimators=100, class_weight={0: 1.0, 1: reduced_weight},

                               random_state=RANDOM_SEED, verbose=-1)

lgb_cons.fit(X_train, y_train)

y_pred = lgb_cons.predict(X_val)

y_proba = lgb_cons.predict_proba(X_val)

metrics = compute_all_metrics(y_val, y_pred, y_proba, "LightGBM (conservative)")

display_metrics(metrics)

results_df = pd.concat([results_df, pd.DataFrame([metrics])], ignore_index=True)

print(f"✅ Cost-sensitive models complete: {len(results_df)} total models")

# %% [markdown]

# ## Section 10: Neural Network Models

# %%

# Cell 13: Neural networks with multiple architectures

if TENSORFLOW_AVAILABLE:

    print("="*60)

    print("NEURAL NETWORK MODELS")

    print("="*60)

    

    # Prepare data

    lgu_id_col = 'lgu_id'

    other_cols = [col for col in X_train.columns if col != lgu_id_col]

    

    scaler = StandardScaler()

    X_train_scaled = scaler.fit_transform(X_train[other_cols])

    X_val_scaled = scaler.transform(X_val[other_cols])

    

    lgu_train = X_train[lgu_id_col].values

    lgu_val = X_val[lgu_id_col].values

    

    # Focal Loss

    def focal_loss(gamma=2.0, alpha=0.25):

        def loss(y_true, y_pred):

            y_pred = tf.clip_by_value(y_pred, 1e-7, 1.0 - 1e-7)

            p_t = tf.where(tf.equal(y_true, 1), y_pred, 1 - y_pred)

            alpha_t = tf.where(tf.equal(y_true, 1), alpha, 1 - alpha)

            focal_weight = alpha_t * tf.pow((1 - p_t), gamma)

            ce_loss = -tf.log(p_t)

            return tf.reduce_mean(focal_weight * ce_loss)

        return loss

    

    # Architecture 1: Small network

    print("\\n[1/3] Neural Network (Small)...")

    lgu_input = keras.Input(shape=(1,), name='lgu')

    feat_input = keras.Input(shape=(len(other_cols),), name='features')

    

    lgu_emb = layers.Embedding(17, 4, name='lgu_embedding')(lgu_input)

    lgu_flat = layers.Flatten()(lgu_emb)

    

    concat = layers.Concatenate()([lgu_flat, feat_input])

    x = layers.Dense(64, activation='relu')(concat)

    x = layers.BatchNormalization()(x)

    x = layers.Dropout(0.3)(x)

    x = layers.Dense(32, activation='relu')(x)

    x = layers.Dropout(0.2)(x)

    output = layers.Dense(1, activation='sigmoid')(x)

    

    model_small = keras.Model(inputs=[lgu_input, feat_input], outputs=output)

    model_small.compile(optimizer='adam', loss=focal_loss(), metrics=['accuracy'])

    

    early_stop = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)

    

    model_small.fit(

        [lgu_train, X_train_scaled], y_train,

        validation_data=([lgu_val, X_val_scaled], y_val),

        epochs=50, batch_size=32, callbacks=[early_stop], verbose=0

    )

    

    y_proba_nn = model_small.predict([lgu_val, X_val_scaled], verbose=0).flatten()

    y_proba_nn_2d = np.column_stack([1 - y_proba_nn, y_proba_nn])

    y_pred_nn = (y_proba_nn >= 0.5).astype(int)

    metrics = compute_all_metrics(y_val, y_pred_nn, y_proba_nn_2d, "NeuralNet (Small + Focal)")

    display_metrics(metrics)

    results_df = pd.concat([results_df, pd.DataFrame([metrics])], ignore_index=True)

    

    # Architecture 2: Deep network

    print("\\n[2/3] Neural Network (Deep)...")

    lgu_input = keras.Input(shape=(1,), name='lgu')

    feat_input = keras.Input(shape=(len(other_cols),), name='features')

    

    lgu_emb = layers.Embedding(17, 8, name='lgu_embedding')(lgu_input)

    lgu_flat = layers.Flatten()(lgu_emb)

    

    concat = layers.Concatenate()([lgu_flat, feat_input])

    x = layers.Dense(128, activation='relu')(concat)

    x = layers.BatchNormalization()(x)

    x = layers.Dropout(0.4)(x)

    x = layers.Dense(64, activation='relu')(x)

    x = layers.BatchNormalization()(x)

    x = layers.Dropout(0.3)(x)

    x = layers.Dense(32, activation='relu')(x)

    x = layers.Dropout(0.2)(x)

    output = layers.Dense(1, activation='sigmoid')(x)

    

    model_deep = keras.Model(inputs=[lgu_input, feat_input], outputs=output)

    model_deep.compile(optimizer='adam', loss=focal_loss(), metrics=['accuracy'])

    

    model_deep.fit(

        [lgu_train, X_train_scaled], y_train,

        validation_data=([lgu_val, X_val_scaled], y_val),

        epochs=50, batch_size=32, callbacks=[early_stop], verbose=0

    )

    

    y_proba_nn = model_deep.predict([lgu_val, X_val_scaled], verbose=0).flatten()

    y_proba_nn_2d = np.column_stack([1 - y_proba_nn, y_proba_nn])

    y_pred_nn = (y_proba_nn >= 0.5).astype(int)

    metrics = compute_all_metrics(y_val, y_pred_nn, y_proba_nn_2d, "NeuralNet (Deep + Focal)")

    display_metrics(metrics)

    results_df = pd.concat([results_df, pd.DataFrame([metrics])], ignore_index=True)

    

    # Architecture 3: With class weights

    print("\\n[3/3] Neural Network (Deep + Class Weight)...")

    class_weight = {0: 1.0, 1: scale_pos_weight * 0.5}

    

    lgu_input = keras.Input(shape=(1,), name='lgu')

    feat_input = keras.Input(shape=(len(other_cols),), name='features')

    

    lgu_emb = layers.Embedding(17, 8, name='lgu_embedding')(lgu_input)

    lgu_flat = layers.Flatten()(lgu_emb)

    

    concat = layers.Concatenate()([lgu_flat, feat_input])

    x = layers.Dense(128, activation='relu', kernel_regularizer=keras.regularizers.l2(0.01))(concat)

    x = layers.BatchNormalization()(x)

    x = layers.Dropout(0.4)(x)

    x = layers.Dense(64, activation='relu', kernel_regularizer=keras.regularizers.l2(0.01))(x)

    x = layers.BatchNormalization()(x)

    x = layers.Dropout(0.3)(x)

    x = layers.Dense(32, activation='relu')(x)

    x = layers.Dropout(0.2)(x)

    output = layers.Dense(1, activation='sigmoid')(x)

    

    model_weighted = keras.Model(inputs=[lgu_input, feat_input], outputs=output)

    model_weighted.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

    

    model_weighted.fit(

        [lgu_train, X_train_scaled], y_train,

        validation_data=([lgu_val, X_val_scaled], y_val),

        epochs=50, batch_size=32, class_weight=class_weight, callbacks=[early_stop], verbose=0

    )

    

    y_proba_nn = model_weighted.predict([lgu_val, X_val_scaled], verbose=0).flatten()

    y_proba_nn_2d = np.column_stack([1 - y_proba_nn, y_proba_nn])

    y_pred_nn = (y_proba_nn >= 0.5).astype(int)

    metrics = compute_all_metrics(y_val, y_pred_nn, y_proba_nn_2d, "NeuralNet (Deep + ClassWeight)")

    display_metrics(metrics)

    results_df = pd.concat([results_df, pd.DataFrame([metrics])], ignore_index=True)

    

    print(f"✅ Neural networks complete: {len(results_df)} total models")

else:

    print("⚠️  TensorFlow not available - skipping neural networks")

# %% [markdown]

# ## Section 11: COMPREHENSIVE COMPARISON OF ALL MODELS

# %%

# Cell 14: Final comprehensive comparison

print("\\n" + "="*100)

print("FINAL COMPREHENSIVE COMPARISON - ALL MODELS")

print("="*100)

# Sort by F2 (primary), then Recall, then Precision

results_final = results_df.sort_values(by=['F2', 'Recall', 'Precision'], ascending=[False, False, False]).reset_index(drop=True)

results_final.insert(0, 'Rank', range(1, len(results_final) + 1))

# Display full table

print(f"\\n📊 ALL {len(results_final)} MODELS RANKED BY F2 SCORE")

print("="*100)

print(f"{'Rank':<5} {'Model':<40} {'Recall':<8} {'Precision':<10} {'F1':<7} {'F2':<7} {'G-Mean':<8} {'PR-AUC':<8}")

print("="*100)

for _, row in results_final.iterrows():

    print(f"{row['Rank']:<5} {row['Model']:<40} {row['Recall']:<8.4f} {row['Precision']:<10.4f} "

          f"{row['F1']:<7.4f} {row['F2']:<7.4f} {row['G-Mean']:<8.4f} {row['PR-AUC']:<8.4f}")

print("="*100)

# Top 5 models

print(f"\\n🏆 TOP 5 MODELS:")

for _, row in results_final.head(5).iterrows():

    print(f"\\n   {int(row['Rank'])}. {row['Model']}")

    print(f"      F2:         {row['F2']:.4f} ⭐")

    print(f"      Recall:     {row['Recall']:.4f}")

    print(f"      Precision:  {row['Precision']:.4f}")

    print(f"      G-Mean:     {row['G-Mean']:.4f}")

# Best by each metric

print(f"\\n📈 BEST BY EACH METRIC:")

print(f"   Best F2:         {results_final.iloc[0]['Model']} ({results_final.iloc[0]['F2']:.4f})")

print(f"   Best Recall:     {results_final.loc[results_final['Recall'].idxmax(), 'Model']} ({results_final['Recall'].max():.4f})")

print(f"   Best Precision:  {results_final.loc[results_final['Precision'].idxmax(), 'Model']} ({results_final['Precision'].max():.4f})")

print(f"   Best G-Mean:     {results_final.loc[results_final['G-Mean'].idxmax(), 'Model']} ({results_final['G-Mean'].max():.4f})")

print(f"   Best PR-AUC:     {results_final.loc[results_final['PR-AUC'].idxmax(), 'Model']} ({results_final['PR-AUC'].max():.4f})")

# Model family comparison

print(f"\\n📊 MODEL FAMILY COMPARISON:")

families = {

    'Random Forest': results_final[results_final['Model'].str.contains('RF')],

    'XGBoost': results_final[results_final['Model'].str.contains('XGBoost')],

    'LightGBM': results_final[results_final['Model'].str.contains('LightGBM')],

    'Neural Network': results_final[results_final['Model'].str.contains('Neural')],

    'Other Ensemble': results_final[results_final['Model'].str.contains('Extra|Balanced|Gradient')]

}

for family_name, family_df in families.items():

    if len(family_df) > 0:

        print(f"\\n   {family_name}:")

        print(f"      Models tested: {len(family_df)}")

        print(f"      Avg F2:        {family_df['F2'].mean():.4f}")

        print(f"      Avg Recall:    {family_df['Recall'].mean():.4f}")

        print(f"      Avg Precision: {family_df['Precision'].mean():.4f}")

        print(f"      Best model:    {family_df.iloc[0]['Model']} (F2={family_df.iloc[0]['F2']:.4f})")

# SMOTE impact

smote_models = results_final[results_final['Model'].str.contains('SMOTE')]

no_smote = results_final[~results_final['Model'].str.contains('SMOTE')]

if len(smote_models) > 0 and len(no_smote) > 0:

    print(f"\\n📊 SMOTE IMPACT:")

    print(f"   With SMOTE ({len(smote_models)} models):")

    print(f"      Avg Recall:    {smote_models['Recall'].mean():.4f}")

    print(f"      Avg Precision: {smote_models['Precision'].mean():.4f}")

    print(f"      Avg F2:        {smote_models['F2'].mean():.4f}")

    print(f"   Without SMOTE ({len(no_smote)} models):")

    print(f"      Avg Recall:    {no_smote['Recall'].mean():.4f}")

    print(f"      Avg Precision: {no_smote['Precision'].mean():.4f}")

    print(f"      Avg F2:        {no_smote['F2'].mean():.4f}")

    print(f"   → Recall improvement: +{smote_models['Recall'].mean() - no_smote['Recall'].mean():.4f}")

    print(f"   → Precision change:   {smote_models['Precision'].mean() - no_smote['Precision'].mean():.4f}")

# Save results

results_path = PROCESSED_DIR / 'model_results_comprehensive.csv'

results_final.to_csv(results_path, index=False)

print(f"\\n✅ Results saved to: {results_path}")

# %% [markdown]

# ## Section 12: Visualization of Results

# %%

# Cell 15: Comprehensive visualizations

fig, axes = plt.subplots(2, 3, figsize=(20, 12))

# 1. Top 15 by F2

ax = axes[0, 0]

top_15 = results_final.head(15)

ax.barh(range(len(top_15)), top_15['F2'], alpha=0.8)

ax.set_yticks(range(len(top_15)))

ax.set_yticklabels(top_15['Model'], fontsize=8)

ax.set_xlabel('F2 Score')

ax.set_title('Top 15 Models by F2 Score')

ax.invert_yaxis()

ax.grid(axis='x', alpha=0.3)

# 2. Recall vs Precision scatter

ax = axes[0, 1]

scatter = ax.scatter(results_final['Recall'], results_final['Precision'],

                    s=results_final['F2']*500, alpha=0.6, c=results_final['F2'], cmap='viridis')

ax.set_xlabel('Recall')

ax.set_ylabel('Precision')

ax.set_title('Recall vs Precision (bubble size = F2)')

ax.grid(alpha=0.3)

plt.colorbar(scatter, ax=ax, label='F2 Score')

# 3. G-Mean distribution

ax = axes[0, 2]

ax.hist(results_final['G-Mean'], bins=20, alpha=0.7, edgecolor='black')

ax.set_xlabel('G-Mean')

ax.set_ylabel('Count')

ax.set_title('G-Mean Distribution')

ax.axvline(results_final['G-Mean'].mean(), color='r', linestyle='--', label=f'Mean: {results_final["G-Mean"].mean():.3f}')

ax.legend()

ax.grid(axis='y', alpha=0.3)

# 4. Model family comparison

ax = axes[1, 0]

family_means = pd.DataFrame([

    {'Family': name, 'F2': df['F2'].mean(), 'Recall': df['Recall'].mean(), 'Precision': df['Precision'].mean()}

    for name, df in families.items() if len(df) > 0

])

x = np.arange(len(family_means))

width = 0.25

ax.bar(x - width, family_means['F2'], width, label='F2', alpha=0.8)

ax.bar(x, family_means['Recall'], width, label='Recall', alpha=0.8)

ax.bar(x + width, family_means['Precision'], width, label='Precision', alpha=0.8)

ax.set_xlabel('Model Family')

ax.set_ylabel('Score')

ax.set_title('Average Performance by Model Family')

ax.set_xticks(x)

ax.set_xticklabels(family_means['Family'], rotation=45, ha='right')

ax.legend()

ax.grid(axis='y', alpha=0.3)

# 5. Top 10 comparison across all metrics

ax = axes[1, 1]

top_10 = results_final.head(10)

metrics_plot = ['Recall', 'Precision', 'F1', 'F2', 'G-Mean']

x = np.arange(len(metrics_plot))

width = 0.08

for i, (_, row) in enumerate(top_10.iterrows()):

    values = [row[m] for m in metrics_plot]

    ax.bar(x + i*width, values, width, label=row['Model'][:20], alpha=0.8)

ax.set_xlabel('Metrics')

ax.set_ylabel('Score')

ax.set_title('Top 10 Models: Multi-Metric Comparison')

ax.set_xticks(x + width * 4.5)

ax.set_xticklabels(metrics_plot)

ax.legend(fontsize=6, loc='upper left', bbox_to_anchor=(1, 1))

ax.grid(axis='y', alpha=0.3)

# 6. SMOTE comparison

ax = axes[1, 2]

if len(smote_models) > 0 and len(no_smote) > 0:

    comparison_data = pd.DataFrame([

        {'Category': 'With SMOTE', 'Recall': smote_models['Recall'].mean(), 

         'Precision': smote_models['Precision'].mean(), 'F2': smote_models['F2'].mean()},

        {'Category': 'Without SMOTE', 'Recall': no_smote['Recall'].mean(),

         'Precision': no_smote['Precision'].mean(), 'F2': no_smote['F2'].mean()}

    ])

    x = np.arange(len(comparison_data))

    width = 0.25

    ax.bar(x - width, comparison_data['Recall'], width, label='Recall', alpha=0.8)

    ax.bar(x, comparison_data['Precision'], width, label='Precision', alpha=0.8)

    ax.bar(x + width, comparison_data['F2'], width, label='F2', alpha=0.8)

    ax.set_xlabel('Category')

    ax.set_ylabel('Score')

    ax.set_title('SMOTE Impact on Performance')

    ax.set_xticks(x)

    ax.set_xticklabels(comparison_data['Category'])

    ax.legend()

    ax.grid(axis='y', alpha=0.3)

plt.tight_layout()

plt.savefig('comprehensive_model_comparison.png', dpi=300, bbox_inches='tight')

print("\\n✅ Saved: comprehensive_model_comparison.png")

plt.show()

# %%

# Cell 16: Final summary

print("\\n" + "="*100)

print("FINAL SUMMARY")

print("="*100)

print(f"\\n📊 DATASET:")

print(f"   Total models tested: {len(results_final)}")

print(f"   Training samples:    {len(X_train):,} ({y_train.sum()} suspensions, {y_train.mean():.2%})")

print(f"   Features used:       {len(all_feature_cols)} (NO feature selection)")

print(f"\\n🏆 BEST MODEL:")

best = results_final.iloc[0]

print(f"   {best['Model']}")

print(f"   F2:         {best['F2']:.4f}")

print(f"   Recall:     {best['Recall']:.4f}")

print(f"   Precision:  {best['Precision']:.4f}")

print(f"   G-Mean:     {best['G-Mean']:.4f}")

print(f"\\n📈 KEY FINDINGS:")

print(f"   1. {len(smote_models)} models used SMOTE - avg F2: {smote_models['F2'].mean():.4f}")

print(f"   2. Best model family: {max(families.items(), key=lambda x: x[1]['F2'].mean() if len(x[1]) > 0 else 0)[0]}")

print(f"   3. Recall range: {results_final['Recall'].min():.4f} to {results_final['Recall'].max():.4f}")

print(f"   4. Precision range: {results_final['Precision'].min():.4f} to {results_final['Precision'].max():.4f}")

print(f"\\n✅ ALL TESTING COMPLETE")

print(f"   Results saved to: {results_path}")

print(f"   Visualization saved: comprehensive_model_comparison.png")

# %%
"""

# Split template into cells
cells = []
lines = template_code.strip().split('\n')

current_cell = []
current_type = None

for line in lines:
    if line.startswith('# %%'):
        if current_cell:
            cells.append({
                'cell_type': current_type,
                'source': '\n'.join(current_cell)
            })
        current_cell = []
        if '[markdown]' in line:
            current_type = 'markdown'
        else:
            current_type = 'code'
    else:
        if line.startswith('# '):
            # Remove leading '# ' for markdown cells
            if current_type == 'markdown':
                current_cell.append(line[2:])
            else:
                current_cell.append(line)
        else:
            current_cell.append(line)

if current_cell:
    cells.append({
        'cell_type': current_type,
        'source': '\n'.join(current_cell)
    })

# Create notebook structure
notebook = {
    "cells": [],
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3"
        },
        "language_info": {
            "name": "python",
            "version": "3.8.0"
        }
    },
    "nbformat": 4,
    "nbformat_minor": 4
}

for cell_data in cells:
    cell = {
        "cell_type": cell_data['cell_type'],
        "metadata": {},
        "source": cell_data['source'].split('\n')
    }
    notebook["cells"].append(cell)

# Write notebook
with open('02_eda_and_model_training.ipynb', 'w', encoding='utf-8') as f:
    json.dump(notebook, f, indent=1, ensure_ascii=False)

print(f"✅ Notebook rewritten with {len(cells)} cells")
