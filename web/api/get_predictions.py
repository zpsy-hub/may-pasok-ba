"""
Flask API endpoint to serve predictions from Supabase database
==============================================================

This API fetches the latest predictions from the database and serves them
to the web dashboard.

Setup:
------
1. Install dependencies:
   pip install flask flask-cors supabase python-dotenv

2. Set environment variables:
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_service_role_key

3. Run:
   python api/get_predictions.py

4. API will be available at:
   http://localhost:5000/api/predictions/latest

Deployment:
----------
Deploy to Vercel, Render, or Railway for production use.
"""

import os
import sys
from datetime import datetime, date
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv

# Add parent directory to path to import database client
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from database.supabase_client import SupabaseLogger

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize Supabase client
try:
    db = SupabaseLogger()
    print("✅ Connected to Supabase")
except Exception as e:
    print(f"❌ Failed to connect to Supabase: {e}")
    db = None


@app.route('/api/predictions/latest', methods=['GET'])
def get_latest_predictions():
    """
    Get latest predictions for all LGUs.
    
    Returns:
        JSON with predictions in the format expected by the dashboard:
        {
            "generated_at": "2025-11-03T10:00:00",
            "prediction_date": "2025-11-03",
            "model_version": "v1.0.0",
            "pagasa_status": {...},
            "weather": {...},
            "predictions": [...],
            "summary": {...},
            "metadata": {...}
        }
    """
    if not db:
        return jsonify({
            'error': 'Database not available',
            'message': 'Unable to connect to database. Please check configuration.'
        }), 503
    
    try:
        # Get latest predictions from database
        predictions_data = db.get_latest_predictions(limit=100)
        
        if not predictions_data:
            return jsonify({
                'error': 'No predictions found',
                'message': 'No predictions available in database.'
            }), 404
        
        # Get the most recent prediction date
        latest_date = max(pred['prediction_date'] for pred in predictions_data)
        
        # Filter predictions for the latest date
        latest_predictions = [
            pred for pred in predictions_data 
            if pred['prediction_date'] == latest_date
        ]
        
        # Get latest weather data
        weather_data = db.get_latest_weather(data_type='forecast', limit=100)
        latest_weather = [w for w in weather_data if w['weather_date'] == latest_date]
        
        # Get latest PAGASA status
        pagasa_response = db.client.table('pagasa_status')\
            .select('*')\
            .order('status_date', desc=True)\
            .order('status_time', desc=True)\
            .limit(1)\
            .execute()
        
        pagasa_data = pagasa_response.data[0] if pagasa_response.data else {}
        
        # Calculate aggregated weather metrics (for Metro Manila summary)
        weather_metrics = calculate_weather_metrics(latest_weather)
        
        # Format predictions for dashboard
        formatted_predictions = []
        for pred in latest_predictions:
            formatted_pred = {
                'prediction_date': pred['prediction_date'],
                'lgu': pred['lgu'],
                'suspension_probability': pred['suspension_probability'],
                'predicted_suspended': pred['predicted_suspended']
            }
            
            # Add risk tier if available (from separate column if you added it)
            # For now, calculate it on the fly based on probability
            risk_tier = calculate_risk_tier(
                pred['suspension_probability'],
                weather_metrics,
                pagasa_data
            )
            formatted_pred['risk_tier'] = risk_tier
            
            # Add weather context
            lgu_weather = next((w for w in latest_weather if w['lgu'] == pred['lgu']), {})
            formatted_pred['weather_context'] = format_weather_context(lgu_weather, pagasa_data)
            
            formatted_predictions.append(formatted_pred)
        
        # Build response in dashboard format
        response = {
            'generated_at': datetime.now().isoformat(),
            'prediction_date': latest_date,
            'model_version': latest_predictions[0].get('model_version', 'v1.0.0'),
            'pagasa_status': {
                'has_active_typhoon': pagasa_data.get('has_active_typhoon', False),
                'typhoon_name': pagasa_data.get('typhoon_name'),
                'tcws_level': pagasa_data.get('tcws_level', 0),
                'has_rainfall_warning': pagasa_data.get('has_rainfall_warning', False),
                'rainfall_warning_level': pagasa_data.get('rainfall_warning_level')
            },
            'weather': weather_metrics,
            'predictions': formatted_predictions,
            'summary': {
                'total_lgus': len(formatted_predictions),
                'predicted_suspensions': sum(1 for p in formatted_predictions if p['predicted_suspended']),
                'avg_probability': sum(p['suspension_probability'] for p in formatted_predictions) / len(formatted_predictions)
            },
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'source': 'database',
                'api_version': '1.0.0'
            }
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500


@app.route('/api/predictions/date/<date_str>', methods=['GET'])
def get_predictions_by_date(date_str):
    """
    Get predictions for a specific date.
    
    Args:
        date_str: Date in format YYYY-MM-DD
    
    Returns:
        JSON with predictions for that date
    """
    if not db:
        return jsonify({'error': 'Database not available'}), 503
    
    try:
        # Validate date format
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({
                'error': 'Invalid date format',
                'message': 'Date must be in YYYY-MM-DD format'
            }), 400
        
        # Get predictions for specific date
        response = db.client.table('daily_predictions')\
            .select('*')\
            .eq('prediction_date', str(target_date))\
            .execute()
        
        predictions_data = response.data
        
        if not predictions_data:
            return jsonify({
                'error': 'No predictions found',
                'message': f'No predictions available for {date_str}'
            }), 404
        
        # Get weather data for that date
        weather_response = db.client.table('weather_data')\
            .select('*')\
            .eq('weather_date', str(target_date))\
            .eq('data_type', 'forecast')\
            .execute()
        
        weather_data = weather_response.data
        
        # Get PAGASA status for that date
        pagasa_response = db.client.table('pagasa_status')\
            .select('*')\
            .eq('status_date', str(target_date))\
            .order('status_time', desc=True)\
            .limit(1)\
            .execute()
        
        pagasa_data = pagasa_response.data[0] if pagasa_response.data else {}
        
        # Format response
        weather_metrics = calculate_weather_metrics(weather_data)
        
        formatted_predictions = []
        for pred in predictions_data:
            formatted_pred = {
                'prediction_date': pred['prediction_date'],
                'lgu': pred['lgu'],
                'suspension_probability': pred['suspension_probability'],
                'predicted_suspended': pred['predicted_suspended']
            }
            
            # Add risk tier
            risk_tier = calculate_risk_tier(
                pred['suspension_probability'],
                weather_metrics,
                pagasa_data
            )
            formatted_pred['risk_tier'] = risk_tier
            
            # Add weather context
            lgu_weather = next((w for w in weather_data if w['lgu'] == pred['lgu']), {})
            formatted_pred['weather_context'] = format_weather_context(lgu_weather, pagasa_data)
            
            formatted_predictions.append(formatted_pred)
        
        response = {
            'generated_at': datetime.now().isoformat(),
            'prediction_date': str(target_date),
            'model_version': predictions_data[0].get('model_version', 'v1.0.0'),
            'pagasa_status': {
                'has_active_typhoon': pagasa_data.get('has_active_typhoon', False),
                'typhoon_name': pagasa_data.get('typhoon_name'),
                'tcws_level': pagasa_data.get('tcws_level', 0),
                'has_rainfall_warning': pagasa_data.get('has_rainfall_warning', False),
                'rainfall_warning_level': pagasa_data.get('rainfall_warning_level')
            },
            'weather': weather_metrics,
            'predictions': formatted_predictions,
            'summary': {
                'total_lgus': len(formatted_predictions),
                'predicted_suspensions': sum(1 for p in formatted_predictions if p['predicted_suspended']),
                'avg_probability': sum(p['suspension_probability'] for p in formatted_predictions) / len(formatted_predictions)
            },
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'source': 'database',
                'date_requested': date_str
            }
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'database_connected': db is not None
    })


# Helper functions

def calculate_weather_metrics(weather_data):
    """Calculate aggregated weather metrics."""
    if not weather_data:
        return {
            'precipitation_sum_mm': 0,
            'wind_speed_max_kmh': 0,
            'temperature_max_c': 0,
            'humidity_mean_pct': 0
        }
    
    return {
        'precipitation_sum_mm': sum(w.get('precipitation_sum', 0) for w in weather_data) / len(weather_data),
        'wind_speed_max_kmh': max(w.get('wind_speed_10m_max', 0) for w in weather_data),
        'temperature_max_c': max(w.get('temperature_2m_max', 0) for w in weather_data),
        'humidity_mean_pct': sum(w.get('relative_humidity_2m_mean', 0) for w in weather_data) / len(weather_data)
    }


def calculate_risk_tier(probability, weather_metrics, pagasa_data):
    """
    Calculate risk tier based on probability and weather conditions.
    
    This replicates the logic from src/weather/risk_tiers.py
    """
    # Base tier from probability
    if probability >= 0.55:
        tier = 'suspension'
        emoji = '🔴'
        color = '#ef4444'
        title = 'SUSPENSION LIKELY'
        subtitle = 'Immediate action required'
        recommendation = 'Suspension highly probable'
        actions = [
            'Announce suspension decision NOW',
            'Activate communication protocols',
            'Ensure all stakeholders notified',
            'Monitor for updates',
            'Prepare for next-day operations'
        ]
        monitoring = 'Continuous monitoring'
    elif probability >= 0.40:
        tier = 'alert'
        emoji = '🟠'
        color = '#f97316'
        title = 'WEATHER ALERT'
        subtitle = 'Enhanced monitoring needed'
        recommendation = 'Prepare for possible suspension'
        actions = [
            'Monitor updates every 2 hours',
            'Prepare early dismissal plan',
            'Coordinate with DRRM office',
            'Review evacuation procedures',
            'Activate weather monitoring team'
        ]
        monitoring = 'Enhanced monitoring (every 2 hours)'
    else:
        tier = 'normal'
        emoji = '🟢'
        color = '#22c55e'
        title = 'NORMAL CONDITIONS'
        subtitle = 'Continue routine operations'
        recommendation = 'No suspension expected'
        actions = [
            'Continue regular class schedule',
            'Monitor weather updates',
            'Maintain standard preparedness protocols'
        ]
        monitoring = 'Standard monitoring (daily)'
    
    return {
        'tier': tier,
        'color': color,
        'emoji': emoji,
        'status_icon': {'suspension': '⛔', 'alert': '⚠️', 'normal': '✓'}[tier],
        'title': title,
        'subtitle': subtitle,
        'recommendation': recommendation,
        'actions': actions,
        'monitoring_interval': monitoring
    }


def format_weather_context(weather_data, pagasa_data):
    """Format weather context for display with full LGU-specific details."""
    if not weather_data:
        return {}
    
    precip = weather_data.get('precipitation_sum', 0)
    temp = weather_data.get('temperature_max', 0)
    wind = weather_data.get('wind_speed_max', 0)
    humidity = weather_data.get('humidity_mean', 0)
    
    # Classify weather description
    if precip >= 30:
        weather_desc = 'Very heavy rain expected'
    elif precip >= 15:
        weather_desc = 'Heavy rain likely'
    elif precip >= 7.5:
        weather_desc = 'Moderate rain possible'
    elif precip > 0:
        weather_desc = 'Light rain possible'
    else:
        weather_desc = 'Mostly dry conditions'
    
    context = {
        'weather_desc': weather_desc,
        'precipitation': f"{precip:.1f}mm",
        'temperature': f"{temp:.1f}°C",
        'wind_speed': f"{wind:.1f} km/h",
        'humidity': f"{humidity:.0f}%"
    }
    
    # Add PAGASA advisory if present
    if pagasa_data.get('has_rainfall_warning'):
        level = pagasa_data.get('rainfall_warning_level', 'YELLOW')
        context['pagasa_advisory'] = f"PAGASA: {level.title()} Rainfall Warning"
    
    return context


if __name__ == '__main__':
    print("🚀 Starting May Pasok Ba API Server...")
    print("📡 API Endpoints:")
    print("   - GET /api/predictions/latest")
    print("   - GET /api/predictions/date/<YYYY-MM-DD>")
    print("   - GET /api/health")
    print("\n⚙️ Make sure SUPABASE_URL and SUPABASE_KEY are set!")
    print("🌐 Server running on http://localhost:5000\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
