# System Implementation - Comprehensive Structure

## Chapter IV: System Implementation

---

## 4.1 Overview
*Brief introduction to implementation approach*

### Key Points:
- **Implementation Philosophy**: Modular, scalable, and automated architecture
- **Development Timeline**: Iterative development with continuous integration
- **Core Objective**: Automated end-to-end prediction pipeline from data collection to deployment
- **Technology Stack**: Python (ML/Backend), JavaScript (Frontend), GitHub Actions (CI/CD), Supabase (Database)

---

## 4.2 System Architecture and Design

### 4.2.1 High-Level Architecture

**Bullet Points:**
- **Three-Tier Architecture**:
  - **Data Layer**: Weather APIs, PAGASA scraper, Supabase database
  - **Processing Layer**: ML model, feature engineering, prediction generation
  - **Presentation Layer**: Static web interface hosted on GitHub Pages

- **Microservices Design Pattern**:
  - Decoupled components for weather collection, prediction, and logging
  - Independent modules can be tested and deployed separately
  - Fault isolation - failure in one component doesn't crash entire system

- **Event-Driven Architecture**:
  - GitHub Actions triggers hourly automated runs
  - Push events to repository trigger immediate deployment
  - Scheduled cron jobs ensure regular updates

**Diagram to Include:**
```
┌─────────────────────────────────────────────────────────────┐
│                    GitHub Actions (Scheduler)                │
│                   Triggers: Hourly + Push Events             │
└─────────────────────────────────────────────────────────────┘
                              ↓
        ┌─────────────────────────────────────────┐
        │         DATA COLLECTION LAYER            │
        │  ┌─────────────────────────────────┐    │
        │  │  Open-Meteo API (Weather)       │    │
        │  │  - 7-day forecasts              │    │
        │  │  - 17 Metro Manila LGUs          │    │
        │  │  - 16 weather variables          │    │
        │  └─────────────────────────────────┘    │
        │  ┌─────────────────────────────────┐    │
        │  │  PAGASA Scraper (Node.js)       │    │
        │  │  - Typhoon bulletins            │    │
        │  │  - Rainfall warnings            │    │
        │  │  - TCWS levels                  │    │
        │  └─────────────────────────────────┘    │
        └─────────────────────────────────────────┘
                              ↓
        ┌─────────────────────────────────────────┐
        │      FEATURE ENGINEERING LAYER           │
        │  ┌─────────────────────────────────┐    │
        │  │  WeatherDataPipeline            │    │
        │  │  - Aggregate weather data       │    │
        │  │  - Calculate temporal features  │    │
        │  │  - Engineer 33 ML features      │    │
        │  └─────────────────────────────────┘    │
        └─────────────────────────────────────────┘
                              ↓
        ┌─────────────────────────────────────────┐
        │         ML PREDICTION LAYER              │
        │  ┌─────────────────────────────────┐    │
        │  │  EasyEnsemble Classifier        │    │
        │  │  - Load trained model (.pkl)    │    │
        │  │  - Generate probabilities       │    │
        │  │  - Interpret risk tiers         │    │
        │  └─────────────────────────────────┘    │
        └─────────────────────────────────────────┘
                              ↓
        ┌─────────────────────────────────────────┐
        │         PERSISTENCE LAYER                │
        │  ┌─────────────────────────────────┐    │
        │  │  Supabase Database (PostgreSQL) │    │
        │  │  - daily_predictions            │    │
        │  │  - weather_data                 │    │
        │  │  - pagasa_status                │    │
        │  │  - collection_logs              │    │
        │  └─────────────────────────────────┘    │
        │  ┌─────────────────────────────────┐    │
        │  │  JSON Files (Git Repository)    │    │
        │  │  - docs/predictions/latest.json │    │
        │  │  - Timestamped backups          │    │
        │  └─────────────────────────────────┘    │
        └─────────────────────────────────────────┘
                              ↓
        ┌─────────────────────────────────────────┐
        │       PRESENTATION LAYER                 │
        │  ┌─────────────────────────────────┐    │
        │  │  GitHub Pages (Static Site)     │    │
        │  │  - index.html (Dashboard)       │    │
        │  │  - prediction-logs.html         │    │
        │  │  - Auto-deploys on git push     │    │
        │  └─────────────────────────────────┘    │
        └─────────────────────────────────────────┘
```

### 4.2.2 Component Interaction Flow

**Bullet Points:**
- **Request-Response Pattern**: Frontend fetches JSON via HTTP GET
- **Producer-Consumer Pattern**: Pipeline produces predictions, frontend consumes
- **Observer Pattern**: GitHub Actions monitors repository for changes
- **Repository Pattern**: Database abstraction layer (SupabaseLogger class)

---

## 4.3 Data Collection Pipeline

### 4.3.1 Weather Data Collection (Open-Meteo API)

**Implementation Details:**
- **API Integration**: REST API calls with requests library
- **Caching Strategy**: requests-cache with 1-hour expiry to reduce API calls
- **Data Format**: JSON response parsed to pandas DataFrame
- **Error Handling**: Retry logic with exponential backoff (3 attempts)
- **Rate Limiting**: Respects Open-Meteo free tier limits (10,000 calls/day)

**Code Structure:**
```python
# src/weather/weather_pipeline.py
class WeatherDataPipeline:
    def collect_realtime_weather_features():
        - Fetch 7-day forecasts for 17 LGUs (119 records)
        - Aggregate daily statistics (mean, max, sum)
        - Return dict with 'weather' and 'pagasa' keys
```

**Variables Collected (16 per LGU):**
1. Temperature (max, min, mean)
2. Precipitation sum (mm)
3. Wind speed (10m height, max)
4. Wind gusts (max)
5. Relative humidity (mean)
6. Atmospheric pressure (mean)
7. Cloud cover (mean)
8. Visibility (min)

**Challenges:**
- **Challenge**: API rate limits during development/testing
- **Solution**: Implemented caching layer, reduced unnecessary calls
- **Challenge**: Missing data for some LGUs on certain dates
- **Solution**: Forward-fill missing values, use nearest LGU data

### 4.3.2 PAGASA Data Scraping (Node.js)

**Implementation Details:**
- **Web Scraping**: Node.js with axios for HTTP requests
- **Parsing Strategy**: Regular expressions to extract structured data from HTML bulletins
- **Data Validation**: Schema validation for required fields (typhoon name, TCWS level)
- **Fallback Mechanism**: If scraping fails, mark as "No active warnings"

**Code Structure:**
```javascript
// nodejs-pagasa/scrape_severe_weather_bulletin.js
async function scrapeSevereWeatherBulletin():
    - Fetch latest PAGASA severe weather bulletin
    - Extract typhoon name, TCWS levels, affected areas
    - Check if Metro Manila is affected
    - Return JSON status object

// nodejs-pagasa/scrape_rainfall_warning.js
async function scrapeRainfallWarning():
    - Fetch PAGASA rainfall warnings
    - Extract warning level (Yellow/Orange/Red)
    - Check Metro Manila coverage
    - Return JSON warning object
```

**Data Extracted:**
- Typhoon presence (boolean)
- Typhoon name (string)
- TCWS level (0-5 integer)
- Metro Manila affected (boolean)
- Rainfall warning level (None/Yellow/Orange/Red)
- Bulletin timestamp
- Bulletin URL for reference

**Challenges:**
- **Challenge**: PAGASA website structure changes frequently
- **Solution**: Implemented flexible regex patterns, multiple fallback selectors
- **Challenge**: Bulletin updates are irregular (not on fixed schedule)
- **Solution**: Scrape on every pipeline run, cache results for 30 minutes

### 4.3.3 Data Integration and Synchronization

**Bullet Points:**
- **Temporal Alignment**: All data timestamped to minute precision
- **Spatial Consistency**: LGU names normalized across all data sources
- **Data Quality Checks**: Validation for outliers, missing values, data types
- **Merge Strategy**: Left join on (date, LGU) with PAGASA status broadcast to all LGUs

---

## 4.4 Feature Engineering Pipeline

### 4.4.1 Feature Engineering Process

**33 Engineered Features:**

1. **Temporal Features (5)**
   - Year (2024, 2025)
   - Month (1-12)
   - Day of week (0-6)
   - Is weekend (boolean)
   - Week of year (1-52)

2. **Weather Features (11)**
   - Precipitation sum (mm)
   - Temperature max (°C)
   - Temperature min (°C)
   - Wind speed max (km/h)
   - Wind gust max (km/h)
   - Humidity mean (%)
   - Pressure mean (hPa)
   - Cloud cover mean (%)
   - Visibility min (km)
   - Feels like temperature (°C)
   - Heat index (calculated)

3. **Historical Lag Features (8)**
   - Precipitation lag 1, 3, 7 days
   - Temperature lag 1, 3, 7 days
   - Suspension occurred lag 1, 7 days

4. **Rolling Window Features (6)**
   - 3-day rolling mean precipitation
   - 3-day rolling max wind
   - 7-day rolling mean precipitation
   - 7-day rolling max wind
   - 7-day rolling mean temperature
   - 7-day rolling sum precipitation

5. **PAGASA Features (2)**
   - Has active typhoon (boolean → 0/1)
   - TCWS level (0-5 integer)

6. **Location Features (1)**
   - LGU ID (0-16 integer encoding)

**Implementation:**
```python
# scripts/collect_and_log.py - predict_with_model()
def engineer_features(weather_features, pagasa_status, lgu_id):
    # Temporal
    features['year'] = date.year
    features['month'] = date.month
    features['day_of_week'] = date.weekday()
    
    # Weather
    features['precipitation_sum'] = weather['precip']
    features['temp_max'] = weather['temp_max']
    
    # Historical (from database or JSON cache)
    features['precip_lag_1'] = get_lag_value(lgu, date - 1 day, 'precip')
    
    # Rolling (from database or JSON cache)
    features['precip_rolling_3d'] = get_rolling_mean(lgu, date, 3, 'precip')
    
    # PAGASA
    features['has_typhoon'] = int(pagasa_status['has_active_typhoon'])
    
    # Location
    features['lgu_id'] = LGU_ID_MAP[lgu_name]
    
    return pd.DataFrame([features])
```

### 4.4.2 Feature Scaling and Normalization

**Bullet Points:**
- **No scaling applied during inference** (model trained on raw features)
- **Categorical encoding**: LGU ID as integer (0-16), not one-hot (to preserve ordinal relationship)
- **Binary encoding**: Boolean features (weekend, typhoon) converted to 0/1
- **Missing value handling**: Median imputation for lag features (if historical data unavailable)

**Challenges:**
- **Challenge**: Cold start problem - no historical lags for first prediction
- **Solution**: Use zero-filling for lag features, rely more on forecast weather
- **Challenge**: Feature drift over time (weather patterns change)
- **Solution**: Plan for model retraining every 6 months with new data

---

## 4.5 Machine Learning Model Implementation

### 4.5.1 Model Selection and Training

**Model Architecture:**
- **Algorithm**: EasyEnsemble Classifier (imbalanced-learn library)
- **Base Estimator**: AdaBoost with Decision Trees
- **Ensemble Size**: 10 balanced base estimators
- **Sampling Strategy**: Random under-sampling of majority class

**Training Process:**
```python
# model-training/train.py
from imblearn.ensemble import EasyEnsembleClassifier

model = EasyEnsembleClassifier(
    n_estimators=10,
    random_state=42,
    sampling_strategy='auto'
)

# Train on historical data (Sept-Oct 2024)
model.fit(X_train, y_train)

# Save trained model
joblib.dump(model, 'best_core_model.pkl')
```

**Training Data:**
- **Time period**: September 1 - October 31, 2024 (61 days)
- **Samples**: 1,037 LGU-day predictions
- **Positive class**: 90 suspension events (8.7% of data)
- **Train/validation/test split**: 60% / 20% / 20% (chronological)

**Model Performance (Test Set):**
- **Accuracy**: 51.3%
- **Precision**: 67.2% (when predicting suspension, correct 67% of time)
- **Recall**: 52.1% (catches 52% of actual suspensions)
- **F1 Score**: 0.588
- **F2 Score**: 0.548 (emphasizes recall)
- **ROC-AUC**: 0.721
- **PR-AUC**: 0.645

**Rationale for Model Choice:**
- **Imbalanced data**: Suspensions are rare events (8.7% positive class)
- **EasyEnsemble**: Balances data by creating multiple balanced subsets
- **Ensemble**: Reduces overfitting, improves generalization
- **Tree-based**: Handles non-linear relationships, feature interactions

### 4.5.2 Model Deployment and Versioning

**Model Artifacts:**
```
model-training/data/processed/
├── best_core_model.pkl         # Trained model (serialized)
├── core_model_metadata.json    # Performance metrics, features
└── feature_importance.csv      # Feature contribution analysis
```

**Versioning Strategy:**
- **Model version**: v1.0.0 (stored in metadata JSON)
- **Git tracking**: Model files tracked in repository (size < 1MB)
- **Deployment**: Model loaded at runtime via joblib.load()
- **Rollback**: Git revert to previous model version if performance degrades

**Model Loading Process:**
```python
# scripts/collect_and_log.py - load_model()
def load_model():
    model_path = PROJECT_ROOT / 'model-training' / 'data' / 'processed'
    model_file = model_path / 'best_core_model.pkl'
    model = joblib.load(model_file)
    return model
```

### 4.5.3 Prediction Generation Process

**Prediction Pipeline:**
```python
# scripts/collect_and_log.py - generate_predictions()
def generate_predictions(weather_features, model):
    predictions = []
    
    for lgu in METRO_MANILA_LGUS:
        # 1. Engineer features (33 features)
        X = engineer_features(weather_features, lgu)
        
        # 2. Get probability from model
        probability = model.predict_proba(X)[0, 1]  # P(suspension)
        
        # 3. Apply threshold (default: 0.5)
        predicted_class = int(probability >= 0.5)
        
        # 4. Interpret risk tier
        risk = interpret_prediction(probability, predicted_class)
        
        # 5. Store prediction
        predictions.append({
            'lgu': lgu,
            'probability': probability,
            'predicted_suspended': predicted_class,
            'risk_tier': risk['risk_level'],
            'recommendation': risk['recommendation']
        })
    
    return predictions
```

**Risk Tier Interpretation:**
- **GREEN (Normal)**: Probability < 40% → Continue classes
- **ORANGE (Alert)**: 40% ≤ Probability < 55% → Monitor weather, prepare
- **RED (Suspension)**: Probability ≥ 55% → Consider suspension

**Challenges:**
- **Challenge**: Model trained on Sept-Oct (rainy season) may not generalize to dry season
- **Solution**: Collect more data year-round, retrain quarterly
- **Challenge**: Model doesn't account for sudden weather changes
- **Solution**: Re-run predictions hourly to capture latest forecasts

---

## 4.6 Database Design and Implementation

### 4.6.1 Database Schema

**Database System**: Supabase (PostgreSQL)

**Entity-Relationship Diagram:**
```
┌─────────────────────────┐
│   daily_predictions     │
├─────────────────────────┤
│ id (PK)                 │
│ prediction_date (FK)    │───┐
│ lgu (FK)                │   │
│ suspension_probability  │   │
│ predicted_suspended     │   │
│ risk_tier               │   │
│ actual_suspended (NULL) │   │
│ prediction_correct      │   │
│ model_version           │   │
│ created_at              │   │
└─────────────────────────┘   │
                              │
        ┌─────────────────────┘
        │
        ↓
┌─────────────────────────┐
│     weather_data        │
├─────────────────────────┤
│ id (PK)                 │
│ weather_date (FK)       │
│ lgu (FK)                │
│ data_type (forecast)    │
│ precipitation_sum       │
│ temperature_2m_max      │
│ wind_speed_10m_max      │
│ [... 13 more columns]   │
│ collected_at            │
└─────────────────────────┘
        │
        ↓
┌─────────────────────────┐
│     pagasa_status       │
├─────────────────────────┤
│ id (PK)                 │
│ status_date             │
│ has_active_typhoon      │
│ typhoon_name            │
│ tcws_level              │
│ has_rainfall_warning    │
│ metro_manila_affected   │
│ bulletin_url            │
│ collected_at            │
└─────────────────────────┘
        │
        ↓
┌─────────────────────────┐
│    collection_logs      │
├─────────────────────────┤
│ id (PK)                 │
│ run_date                │
│ github_run_id           │
│ pagasa_success          │
│ openmeteo_success       │
│ predictions_generated   │
│ total_duration_seconds  │
│ created_at              │
└─────────────────────────┘
```

**Table Specifications:**

1. **daily_predictions** (Primary Table)
   - Stores suspension predictions per LGU per date
   - Unique constraint: (prediction_date, lgu)
   - Upsert strategy: ON CONFLICT UPDATE (allows re-running pipeline)
   - **Foreign keys**: 
     - `weather_data_id` (UUID, nullable) → references weather_data.id
     - `pagasa_status_id` (UUID, nullable) → references pagasa_status.id
     - **Design rationale**: Optional foreign keys allow explicit linking while maintaining backward compatibility
     - **ON DELETE SET NULL**: Preserves predictions even if referenced weather/PAGASA data is deleted

2. **weather_data** (Weather Forecasts)
   - Stores 16 weather variables per LGU per date
   - Supports both 'forecast' and 'actual' data types
   - Indexed on (weather_date, lgu, data_type) for fast queries
   - **Relationship**: One-to-many with daily_predictions (one weather record can be referenced by multiple predictions)

3. **pagasa_status** (PAGASA Alerts)
   - Stores typhoon and rainfall warnings
   - One record per collection timestamp (not per LGU - broadcast to all)
   - Indexed on status_date for temporal queries
   - **Relationship**: One-to-many with daily_predictions (one PAGASA status can be referenced by multiple predictions, typically all 17 LGUs)

4. **collection_logs** (Monitoring)
   - Tracks success/failure of automated pipeline runs
   - Stores error messages for debugging
   - Links to GitHub Actions run ID for traceability
   - **Relationship**: Standalone table, no foreign keys (logs are independent records)

### 4.6.2 Database Operations

**CRUD Operations via SupabaseLogger:**

```python
# database/supabase_client.py
class SupabaseLogger:
    def __init__(self):
        self.client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # CREATE/UPDATE
    def log_predictions(self, predictions, model_version, threshold):
        """Upsert predictions to database"""
        self.client.table('daily_predictions').upsert(predictions).execute()
    
    def log_weather_data(self, weather_df, data_type='forecast'):
        """Insert weather records"""
        self.client.table('weather_data').insert(records).execute()
    
    # READ
    def get_latest_predictions(self, limit=100):
        """Query recent predictions"""
        response = self.client.table('daily_predictions') \
            .select('*') \
            .order('prediction_date', desc=True) \
            .limit(limit) \
            .execute()
        return response.data
    
    # UPDATE
    def update_actual_outcome(self, prediction_date, lgu, actual):
        """Update actual suspension outcome"""
        self.client.table('daily_predictions') \
            .update({'actual_suspended': actual}) \
            .eq('prediction_date', prediction_date) \
            .eq('lgu', lgu) \
            .execute()
```

**Database Indexes:**
```sql
-- Performance optimization
CREATE INDEX idx_predictions_date ON daily_predictions(prediction_date DESC);
CREATE INDEX idx_weather_date_lgu ON weather_data(weather_date, lgu);
CREATE INDEX idx_pagasa_date ON pagasa_status(status_date DESC);
```

**Challenges:**
- **Challenge**: Row-Level Security (RLS) policies blocking GitHub Actions inserts
- **Solution**: Used service_role key (bypasses RLS) for automated writes
- **Challenge**: Duplicate prediction records on pipeline re-runs
- **Solution**: Implemented UPSERT with ON CONFLICT clause
- **Challenge**: Tables initially had no foreign key relationships (data integrity risk)
- **Solution**: Added optional foreign key columns (`weather_data_id`, `pagasa_status_id`) with ON DELETE SET NULL constraints, preserving backward compatibility while improving referential integrity

---

## 4.7 Frontend Implementation

### 4.7.1 User Interface Design

**Design Principles:**
- **Minimalist Aesthetic**: Pastel color palette, clean typography (Inter font)
- **Mobile-First**: Responsive design with Bootstrap 5.3 grid system
- **Accessibility**: High contrast ratios, semantic HTML, ARIA labels
- **Performance**: Static HTML/CSS/JS, no framework overhead

**Pages:**

1. **Main Dashboard (index.html)**
   - Metro Manila overview card with aggregated risk
   - 17 LGU prediction cards (grid layout)
   - Risk tier color coding (🟢 Green, 🟠 Orange, 🔴 Red)
   - Last updated timestamp with clock icon
   - Feedback modal form

2. **Prediction Logs (prediction-logs.html)**
   - Historical predictions table (paginated, 50 rows/page)
   - Date range filter (calendar picker)
   - LGU filter (dropdown with all 17 LGUs)
   - Risk tier filter (checkboxes)
   - Daily summary statistics
   - Export to CSV functionality

**Color Scheme:**
```css
:root {
    --primary: #3b82f6;      /* Blue */
    --success: #10b981;      /* Green */
    --warning: #f59e0b;      /* Orange */
    --danger: #ef4444;       /* Red */
    --bg-primary: #f8f9fa;   /* Light gray */
    --text-primary: #1f2937; /* Dark gray */
}
```

### 4.7.2 Frontend Data Flow

**Data Fetching:**
```javascript
// docs/js/dashboard.js
async function loadPredictions() {
    try {
        // Fetch from static JSON file
        const response = await fetch('predictions/latest.json');
        const data = await response.json();
        
        // Render predictions
        renderPredictionCards(data.predictions);
        updateMetroManilaSummary(data.summary);
        updateTimestamp(data.generated_at);
        
    } catch (error) {
        console.error('Failed to load predictions:', error);
        showErrorMessage('Unable to load predictions. Please try again later.');
    }
}
```

**Dynamic Rendering:**
```javascript
function renderPredictionCard(prediction) {
    const card = document.createElement('div');
    card.className = 'prediction-card';
    card.innerHTML = `
        <h3>${prediction.lgu}</h3>
        <div class="probability ${getRiskClass(prediction.risk_tier)}">
            ${(prediction.suspension_probability * 100).toFixed(1)}%
        </div>
        <div class="risk-tier ${getRiskClass(prediction.risk_tier)}">
            ${prediction.risk_tier}
        </div>
        <p class="recommendation">${prediction.recommendation}</p>
    `;
    return card;
}
```

**Encoding Fix (Las Piñas Issue):**
```javascript
// Fix UTF-8 encoding issues in display
function fixEncoding(text) {
    return text.replace(/Ã±/g, 'ñ')
               .replace(/Ã©/g, 'é');
}
```

### 4.7.3 Pagination Implementation

**Pagination Logic (prediction-logs.html):**
```javascript
const ROWS_PER_PAGE = 50;
let currentPage = 1;
let filteredData = [];

function renderPage(page) {
    const start = (page - 1) * ROWS_PER_PAGE;
    const end = start + ROWS_PER_PAGE;
    const pageData = filteredData.slice(start, end);
    
    // Render table rows
    const tbody = document.getElementById('predictionsTableBody');
    tbody.innerHTML = pageData.map(renderTableRow).join('');
    
    // Update pagination controls
    updatePaginationControls();
}

function updatePaginationControls() {
    const totalPages = Math.ceil(filteredData.length / ROWS_PER_PAGE);
    
    // Generate button HTML
    const firstBtn = `<button onclick="goToPage(1)" ${currentPage === 1 ? 'disabled' : ''}>First</button>`;
    const prevBtn = `<button onclick="goToPage(${currentPage - 1})" ${currentPage === 1 ? 'disabled' : ''}>Previous</button>`;
    const nextBtn = `<button onclick="goToPage(${currentPage + 1})" ${currentPage === totalPages ? 'disabled' : ''}>Next</button>`;
    const lastBtn = `<button onclick="goToPage(${totalPages})" ${currentPage === totalPages ? 'disabled' : ''}>Last</button>`;
    
    document.getElementById('paginationControls').innerHTML = 
        firstBtn + prevBtn + ` Page ${currentPage} of ${totalPages} ` + nextBtn + lastBtn;
}
```

**Challenges:**
- **Challenge**: Large prediction logs JSON (>1MB) causing slow page load
- **Solution**: Implemented client-side pagination, lazy rendering
- **Challenge**: Encoding issues with "Las Piñas" displaying as "Las PiÃ±as"
- **Solution**: Added encoding normalization function applied at render time

---

## 4.8 Automated CI/CD Pipeline

### 4.8.1 GitHub Actions Workflow

**Workflow Configuration:**
```yaml
# .github/workflows/collect-predictions-docs.yml
name: Deploy to GitHub Pages (docs)

on:
  schedule:
    - cron: '0 * * * *'  # Hourly at minute 0
  workflow_dispatch:      # Manual trigger
  push:
    branches: [main]      # Deploy on every push

jobs:
  deploy:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    
    steps:
      - name: Checkout repository
        uses: actions/checkout@v3
      
      - name: Set up Python 3.11
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Set up Node.js 18
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install Python dependencies
        run: pip install -r requirements.txt
      
      - name: Install Node.js dependencies
        run: cd nodejs-pagasa && npm install
      
      - name: Run prediction pipeline
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_KEY: ${{ secrets.SUPABASE_KEY }}
        run: python scripts/collect_and_log.py
      
      - name: Verify predictions generated
        run: |
          if [ ! -f "docs/predictions/latest.json" ]; then
            echo "Error: Predictions not generated"
            exit 1
          fi
      
      - name: Commit predictions
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add docs/predictions/*.json
          git commit -m "Update predictions: $(date +'%Y-%m-%d %H:%M UTC')"
      
      - name: Push changes
        uses: ad-m/github-push-action@master
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          branch: main
      
      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./docs
          publish_branch: gh-pages
```

### 4.8.2 Deployment Process

**Deployment Stages:**

1. **Trigger** (3 modes):
   - **Scheduled**: Hourly cron job (0 * * * *)
   - **Push**: Automatic on every commit to main branch
   - **Manual**: workflow_dispatch via GitHub UI

2. **Environment Setup** (~30 seconds):
   - Provision Ubuntu runner VM
   - Install Python 3.11
   - Install Node.js 18
   - Install pip packages (requirements.txt)
   - Install npm packages (nodejs-pagasa/package.json)

3. **Data Collection** (~60 seconds):
   - Execute collect_and_log.py script
   - Fetch weather data from Open-Meteo
   - Scrape PAGASA bulletins
   - Generate ML predictions
   - Save to docs/predictions/latest.json
   - Log to Supabase database

4. **Git Operations** (~10 seconds):
   - Configure git user (github-actions[bot])
   - Stage prediction JSON files
   - Commit with timestamp message
   - Push to main branch

5. **GitHub Pages Deployment** (~30 seconds):
   - Trigger gh-pages branch update
   - Build static site from docs/ folder
   - Deploy to GitHub Pages CDN

**Total Pipeline Duration**: ~2-3 minutes

### 4.8.3 Monitoring and Error Handling

**Error Handling Strategy:**
```python
# scripts/collect_and_log.py - main execution
try:
    # Collection phase
    weather_features = pipeline.collect_realtime_weather_features()
    logger.log_weather_data(weather_features['weather'])
    
    # Prediction phase
    predictions = generate_predictions(weather_features, model)
    logger.log_predictions(predictions)
    
    # Success logging
    logger.log_collection_run(
        pagasa_success=True,
        openmeteo_success=True,
        predictions_success=True,
        duration_seconds=int(time.time() - start_time)
    )
    
except PAGASAScrapingError as e:
    # Partial failure - continue without PAGASA data
    logger.log_collection_run(
        pagasa_success=False,
        pagasa_error=str(e),
        openmeteo_success=True,
        predictions_success=True
    )
    
except Exception as e:
    # Complete failure - log and exit
    logger.log_collection_run(
        pagasa_success=False,
        openmeteo_success=False,
        predictions_success=False,
        predictions_error=str(e)
    )
    sys.exit(1)  # Fail workflow
```

**Monitoring Dashboard:**
- **GitHub Actions**: View run history, logs, duration
- **Supabase Dashboard**: Query collection_logs table for success rates
- **GitHub Pages**: Check deployment status in Settings > Pages

**Challenges:**
- **Challenge**: Workflow fails intermittently due to network timeouts
- **Solution**: Added retry logic with exponential backoff in API calls
- **Challenge**: Git push conflicts when multiple workflows run simultaneously
- **Solution**: Added git pull --rebase before push, retry on conflict
- **Challenge**: Supabase rate limits during high-frequency testing
- **Solution**: Implemented local caching, reduced test runs

---

## 4.9 Historical Data Backfill System

### 4.9.1 Backfill Pipeline Architecture

**Purpose**: Generate historical predictions for Sept-Oct 2024 to validate model performance

**Components:**

1. **collect_historical_weather.py**: Fetch past weather data
2. **generate_predictions.py**: Run model on historical data
3. **generate_prediction_logs.py**: Create JSON for frontend
4. **upload_actual_suspensions.py**: Record actual outcomes

**Workflow:**
```
Historical Weather → Feature Engineering → Model Prediction → Validation → Frontend JSON
```

### 4.9.2 Historical Weather Collection

**Implementation:**
```python
# backfill/collect_historical_weather.py
def collect_historical_weather(start_date, end_date):
    """Collect weather data for date range"""
    
    for date in date_range(start_date, end_date):
        for lgu in METRO_MANILA_LGUS:
            # Fetch historical data from Open-Meteo
            weather = fetch_historical_weather(lgu, date)
            
            # Save to JSON
            save_weather_record(weather, date, lgu)
    
    print(f"✅ Collected weather for {num_days} days, {num_lgus} LGUs")
```

**Output Files:**
```
backfill/output/
├── forecast_sept_oct.json      # Historical forecasts (1,037 records)
├── weather_sept_oct.json       # Daily weather summaries
└── actual_suspensions_sept_oct.json  # Ground truth labels
```

### 4.9.3 Historical Prediction Generation

**Implementation:**
```python
# backfill/generate_predictions.py
def generate_historical_predictions(weather_data, model):
    """Generate predictions for historical period"""
    
    predictions = []
    
    for date in historical_dates:
        # Get weather for this date
        weather = weather_data[date]
        
        # Generate prediction for each LGU
        for lgu in METRO_MANILA_LGUS:
            X = engineer_features(weather, lgu, date)
            prob = model.predict_proba(X)[0, 1]
            
            predictions.append({
                'date': date,
                'lgu': lgu,
                'probability': prob,
                'risk_tier': get_risk_tier(prob)
            })
    
    # Save to JSON
    save_predictions(predictions, 'predictions_sept_oct.json')
    
    return predictions
```

### 4.9.4 Validation with Actual Outcomes

**Ground Truth Collection:**
```json
// backfill/actual_suspensions_sept_oct.json
[
    {
        "date": "2024-09-01",
        "lgu": "Manila",
        "actual_suspended": true,
        "source": "DepEd Manila Facebook page"
    },
    {
        "date": "2024-09-22",
        "lgu": "Quezon City",
        "actual_suspended": true,
        "source": "DepEd QC Official Announcement"
    }
]
```

**Validation Process:**
```python
# backfill/validate_predictions.py
def calculate_accuracy(predictions, actuals):
    """Compare predictions with actual outcomes"""
    
    merged = merge_predictions_actuals(predictions, actuals)
    
    # Calculate metrics
    tp = ((merged.predicted == 1) & (merged.actual == 1)).sum()
    tn = ((merged.predicted == 0) & (merged.actual == 0)).sum()
    fp = ((merged.predicted == 1) & (merged.actual == 0)).sum()
    fn = ((merged.predicted == 0) & (merged.actual == 1)).sum()
    
    accuracy = (tp + tn) / len(merged)
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    
    return {
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'confusion_matrix': {'TP': tp, 'TN': tn, 'FP': fp, 'FN': fn}
    }
```

**Challenges:**
- **Challenge**: Historical weather data not available for all dates (API limitations)
- **Solution**: Used nearest available date, interpolated missing values
- **Challenge**: Ground truth (actual suspensions) hard to collect
- **Solution**: Manual collection from DepEd social media, news articles

---

## 4.10 Testing and Quality Assurance

### 4.10.1 Unit Testing

**Test Framework**: pytest

**Test Coverage:**
```python
# tests/test_weather_pipeline.py
def test_weather_collection():
    """Test Open-Meteo API integration"""
    pipeline = WeatherDataPipeline()
    features = pipeline.collect_realtime_weather_features()
    
    assert 'weather' in features
    assert 'pagasa' in features
    assert len(features['weather']) == 17  # All LGUs

# tests/test_model_prediction.py
def test_prediction_generation():
    """Test model prediction pipeline"""
    model = load_model()
    predictions = generate_predictions(mock_weather, model)
    
    assert len(predictions) == 17
    assert all(0 <= p['probability'] <= 1 for p in predictions)
    assert all(p['risk_tier'] in ['GREEN', 'ORANGE', 'RED'] for p in predictions)

# tests/test_database.py
def test_supabase_logging():
    """Test database insert/query"""
    logger = SupabaseLogger()
    logger.log_predictions(mock_predictions)
    
    results = logger.get_latest_predictions(limit=1)
    assert len(results) > 0
```

### 4.10.2 Integration Testing

**End-to-End Testing:**
```bash
# Test full pipeline locally
$ python scripts/collect_and_log.py --test

# Verify outputs
$ ls -lh docs/predictions/latest.json
$ psql $SUPABASE_URL -c "SELECT COUNT(*) FROM daily_predictions;"
```

**GitHub Actions Testing:**
- **Manual workflow dispatch** for testing before production
- **Staging environment** (separate Supabase project for testing)
- **Preview deployments** (GitHub Pages branch preview)

### 4.10.3 Performance Testing

**Metrics:**
- **Pipeline execution time**: 2-3 minutes (target: <5 minutes)
- **API response time**: Open-Meteo <2 seconds, PAGASA <5 seconds
- **Database insert latency**: <100ms per batch
- **Frontend load time**: <1 second (static HTML)
- **JSON file size**: latest.json ~50KB (optimized)

**Load Testing:**
```bash
# Stress test API endpoints
$ ab -n 1000 -c 10 https://zpsy-hub.github.io/may-pasok-ba/

# Test database concurrent writes
$ python tests/load_test_database.py --connections 10 --duration 60
```

### 4.10.4 User Acceptance Testing

**Test Scenarios:**
1. **View current predictions**: User visits homepage, sees all 17 LGUs
2. **Filter historical logs**: User selects date range, filters by LGU
3. **Mobile responsiveness**: User accesses site on phone, cards stack vertically
4. **Accessibility**: Screen reader user can navigate prediction cards

**Feedback Collection:**
- **Feedback modal** on homepage (stores submissions in Supabase)
- **GitHub Issues** for bug reports
- **Analytics** (Google Analytics for user behavior tracking)

**Challenges:**
- **Challenge**: Users confused by probability vs risk tier
- **Solution**: Added recommendation text ("Continue classes", "Monitor weather")
- **Challenge**: Mobile users can't scroll table horizontally
- **Solution**: Implemented responsive table with stacked rows on small screens

---

## 4.11 Security and Privacy

### 4.11.1 Security Measures

**API Security:**
- **Supabase authentication**: Service role key stored as GitHub Secret
- **Environment variables**: Secrets never committed to repository
- **HTTPS enforcement**: All API calls use TLS 1.2+
- **Rate limiting**: Implemented in Open-Meteo API calls (10 requests/second max)

**Database Security:**
- **Row Level Security (RLS)**: Enabled on all tables
- **Read-only public access**: Anonymous users can SELECT only
- **Write access**: Restricted to service role key (GitHub Actions only)
- **SQL injection prevention**: Parameterized queries via Supabase client

**Frontend Security:**
- **No client-side secrets**: Only public API key used (read-only)
- **Content Security Policy**: Prevents XSS attacks
- **CORS configuration**: GitHub Pages serves with proper CORS headers

### 4.11.2 Privacy Considerations

**Data Collection:**
- **No user tracking**: No cookies, no analytics (optional)
- **No personal data**: System collects only weather and prediction data
- **Public data only**: PAGASA bulletins are publicly available

**Compliance:**
- **Data retention**: Predictions stored indefinitely (public interest)
- **Right to deletion**: Users can request prediction data removal
- **Transparency**: Open-source repository, documented data pipeline

---

## 4.12 Deployment and Maintenance

### 4.12.1 Deployment Checklist

**Pre-Deployment:**
- ✅ Train model on sufficient data (1,000+ samples)
- ✅ Validate model performance (F1 > 0.5, Recall > 0.5)
- ✅ Test pipeline end-to-end locally
- ✅ Set up Supabase database and tables
- ✅ Configure GitHub Secrets (SUPABASE_URL, SUPABASE_KEY)
- ✅ Enable GitHub Pages (docs/ folder, main branch)
- ✅ Test GitHub Actions workflow (manual trigger)

**Deployment:**
1. Push code to main branch
2. Verify GitHub Actions workflow runs successfully
3. Check predictions generated in docs/predictions/latest.json
4. Verify GitHub Pages deployment (site live within 2 minutes)
5. Test frontend (homepage loads, predictions display correctly)
6. Monitor first 24 hours for errors

**Post-Deployment:**
- ✅ Set up monitoring alerts (GitHub Actions email notifications)
- ✅ Create backlog of improvement tasks
- ✅ Document known issues and limitations
- ✅ Schedule model retraining (every 6 months)

### 4.12.2 Maintenance Plan

**Daily:**
- Monitor GitHub Actions runs (automated, no manual intervention)
- Check Supabase dashboard for errors (optional)

**Weekly:**
- Review prediction accuracy (if ground truth available)
- Check for PAGASA website changes (scraper may break)
- Verify Open-Meteo API still responsive

**Monthly:**
- Analyze prediction trends (are suspensions increasing?)
- Review feature importance (has model behavior changed?)
- Archive old predictions (if database storage exceeds 400MB)

**Quarterly:**
- Retrain model with new data (if significant drift detected)
- Update dependencies (pip packages, npm packages)
- Conduct user survey for feedback

**Annually:**
- Major model retraining with full year of data
- Review and update risk tier thresholds
- Migrate to paid Supabase plan if needed (>500MB database)

### 4.12.3 Disaster Recovery

**Backup Strategy:**
- **Database**: Supabase automatic daily backups (retained 7 days)
- **Code**: Git version control (full history)
- **Predictions**: Timestamped JSON files committed to repository

**Rollback Procedures:**
1. **Model rollback**: Git revert to previous model commit
2. **Database rollback**: Restore from Supabase backup (Settings > Database)
3. **Frontend rollback**: Git revert HTML/CSS changes, redeploy

**Failure Scenarios:**
| Failure | Impact | Recovery Time | Mitigation |
|---------|--------|---------------|------------|
| GitHub Actions fails | No new predictions | 0 minutes (auto-retry) | Manual workflow trigger |
| Supabase down | No database logging | 0 minutes (predictions still save to JSON) | Use JSON as fallback |
| Open-Meteo API down | No weather data | 5 minutes (switch to backup API) | Implement fallback weather API |
| GitHub Pages down | Site unreachable | 0 minutes (GitHub handles) | N/A (trust GitHub) |
| Model corruption | Wrong predictions | 30 minutes (revert to previous model) | Git version control |

---

## 4.13 Challenges and Solutions Summary

**Top 10 Challenges Encountered:**

1. **Class Imbalance (8.7% positive class)**
   - Solution: Used EasyEnsemble classifier with balanced sampling

2. **PAGASA Website Unreliable**
   - Solution: Implemented flexible scraping with fallback to "No warnings"

3. **Cold Start Problem (No Historical Lags)**
   - Solution: Zero-filling lag features, rely more on forecast weather

4. **GitHub Actions Rate Limits**
   - Solution: Reduced test frequency, implemented caching

5. **Supabase RLS Blocking Writes**
   - Solution: Used service_role key (bypasses RLS)

6. **Frontend Encoding Issues (Las Piñas)**
   - Solution: Client-side normalization function

7. **Large Prediction Logs Slow Page Load**
   - Solution: Client-side pagination (50 rows/page)

8. **Model Generalization Across Seasons**
   - Solution: Plan for quarterly retraining, collect year-round data

9. **Git Conflicts in Automated Commits**
   - Solution: Added git pull --rebase before push

10. **Missing Ground Truth for Validation**
    - Solution: Manual collection from DepEd social media, news

---

## 4.14 Future Enhancements

**Planned Improvements:**
1. **SMS/Email Notifications**: Alert users for high-risk predictions
2. **Mobile App**: React Native app for iOS/Android
3. **Expanded Coverage**: Beyond Metro Manila (Provinces)
4. **Improved Model**: Deep learning (LSTM for time series)
5. **Real-Time Weather**: 15-minute updates (not hourly)
6. **User Feedback Loop**: Crowdsource actual suspension outcomes
7. **Historical Analysis Dashboard**: Trends, accuracy over time
8. **Multi-Language Support**: English, Filipino
9. **API for Third-Party Integration**: JSON API for external apps
10. **Automated Model Retraining**: MLOps pipeline with drift detection

---

## 4.15 Conclusion

**Implementation Summary:**
- Successfully built end-to-end automated prediction system
- Deployed to GitHub Pages with hourly updates
- Integrated machine learning model with real-time data sources
- Achieved 51% accuracy on imbalanced test data (67% precision)
- Fully automated CI/CD pipeline with minimal manual intervention

**Key Takeaways:**
- **Modular architecture** enables independent testing and updates
- **Automation** reduces operational overhead to near-zero
- **Open-source approach** promotes transparency and community contribution
- **Static site hosting** provides free, reliable, scalable deployment

**Lessons Learned:**
- Start with simple rule-based system, iterate to ML when sufficient data available
- Prioritize automation early to reduce manual maintenance burden
- Build monitoring and error handling from day one
- Document everything - future you will thank present you

---

## Figures and Tables to Include

### Figures:
1. **Figure 4.1**: System Architecture Diagram (3-tier architecture)
2. **Figure 4.2**: Data Flow Diagram (data collection → prediction → deployment)
3. **Figure 4.3**: Entity-Relationship Diagram (database schema)
4. **Figure 4.4**: GitHub Actions Workflow Diagram (CI/CD pipeline stages)
5. **Figure 4.5**: Screenshot of Main Dashboard (homepage with prediction cards)
6. **Figure 4.6**: Screenshot of Prediction Logs (historical analysis page)
7. **Figure 4.7**: Feature Engineering Process Flowchart
8. **Figure 4.8**: Model Training Pipeline Flowchart
9. **Figure 4.9**: Risk Tier Interpretation Logic Flowchart
10. **Figure 4.10**: Deployment Process Flowchart

### Tables:
1. **Table 4.1**: Technology Stack Summary
2. **Table 4.2**: Database Schema Specification
3. **Table 4.3**: Feature List (33 features with descriptions)
4. **Table 4.4**: Model Performance Metrics (Accuracy, Precision, Recall, F1, AUC)
5. **Table 4.5**: API Endpoints and Rate Limits
6. **Table 4.6**: GitHub Actions Workflow Steps
7. **Table 4.7**: Risk Tier Definitions
8. **Table 4.8**: Testing Coverage Summary
9. **Table 4.9**: Deployment Checklist
10. **Table 4.10**: Challenges and Solutions Summary

### Code Listings:
1. **Listing 4.1**: Model Training Code (train.py excerpt)
2. **Listing 4.2**: Feature Engineering Function (engineer_features)
3. **Listing 4.3**: Prediction Generation Function (generate_predictions)
4. **Listing 4.4**: Database Logger Class (SupabaseLogger)
5. **Listing 4.5**: GitHub Actions Workflow YAML (deploy.yml)
6. **Listing 4.6**: Frontend Data Fetching (dashboard.js)

---

## Writing Guidelines

**Technical Writing Best Practices:**
1. **Use passive voice for processes**: "The model was trained..." (not "We trained...")
2. **Use active voice for tools**: "The system collects weather data..."
3. **Define acronyms on first use**: "Machine Learning (ML)"
4. **Reference figures/tables**: "as shown in Figure 4.1"
5. **Use consistent terminology**: "prediction" (not "forecast", "estimate")
6. **Number all code listings**: Listing 4.1, Listing 4.2, etc.
7. **Include captions for all visuals**: Brief description below figure/table
8. **Cross-reference related sections**: "See Section 4.3 for details"
9. **Use bullet points for lists**: Easier to scan
10. **Include code comments**: Explain complex logic

**Section Organization:**
- Start with overview/objective
- Explain design decisions (why this approach?)
- Describe implementation details (how it works)
- Include code snippets with explanations
- Discuss challenges and solutions
- End with validation/results

**Length Estimates:**
- 4.1 Overview: 1 page
- 4.2 Architecture: 3-4 pages
- 4.3 Data Collection: 4-5 pages
- 4.4 Feature Engineering: 3-4 pages
- 4.5 ML Model: 4-5 pages
- 4.6 Database: 3-4 pages
- 4.7 Frontend: 3-4 pages
- 4.8 CI/CD: 3-4 pages
- 4.9 Backfill: 2-3 pages
- 4.10 Testing: 2-3 pages
- 4.11 Security: 2 pages
- 4.12 Deployment: 2-3 pages
- 4.13 Challenges: 2 pages
- 4.14 Future Work: 1 page
- 4.15 Conclusion: 1 page

**Total**: 35-45 pages (typical for MS thesis System Implementation chapter)

---

*This structure provides a comprehensive framework for documenting your system implementation. Adapt the level of detail based on your thesis requirements and page limits.*
