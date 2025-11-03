"""
Quick test to verify ML model responds to different weather conditions.
"""
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.collect_and_log import load_model, generate_predictions

# Load the model
model = load_model()
print(f"Model loaded: {model is not None}")
print()

# Test scenarios
scenarios = [
    {
        "name": "Clear Weather",
        "features": {
            'forecast_precipitation_sum': 0,
            'forecast_wind_speed_max': 15,
            'forecast_wind_gusts_max': 25,
            'forecast_temperature_max': 32,
            'forecast_humidity_mean': 65,
            'forecast_cloud_cover': 20,
            'forecast_weather_code': 0,
            'forecast_precipitation_probability': 10,
            'tcws_level': 0,
            'has_active_typhoon': 0,
            'has_rainfall_warning': 0,
        }
    },
    {
        "name": "Heavy Rain",
        "features": {
            'forecast_precipitation_sum': 80,
            'forecast_wind_speed_max': 40,
            'forecast_wind_gusts_max': 70,
            'forecast_temperature_max': 28,
            'forecast_humidity_mean': 90,
            'forecast_cloud_cover': 100,
            'forecast_weather_code': 95,
            'forecast_precipitation_probability': 95,
            'tcws_level': 0,
            'has_active_typhoon': 0,
            'has_rainfall_warning': 1,
        }
    },
    {
        "name": "Typhoon Signal #3",
        "features": {
            'forecast_precipitation_sum': 150,
            'forecast_wind_speed_max': 100,
            'forecast_wind_gusts_max': 150,
            'forecast_temperature_max': 26,
            'forecast_humidity_mean': 95,
            'forecast_cloud_cover': 100,
            'forecast_weather_code': 96,
            'forecast_precipitation_probability': 100,
            'tcws_level': 3,
            'has_active_typhoon': 1,
            'has_rainfall_warning': 1,
        }
    },
]

for scenario in scenarios:
    print(f"{'='*60}")
    print(f"Scenario: {scenario['name']}")
    print(f"{'='*60}")
    
    predictions = generate_predictions(
        scenario['features'],
        model_version='test',
        model=model
    )
    
    # Calculate stats
    avg_prob = sum(p['suspension_probability'] for p in predictions) / len(predictions)
    suspended = sum(1 for p in predictions if p['predicted_suspended'])
    
    print(f"Average Probability: {avg_prob:.2%}")
    print(f"Predicted Suspensions: {suspended}/17 LGUs")
    
    # Show top 5
    top_5 = sorted(predictions, key=lambda x: x['suspension_probability'], reverse=True)[:5]
    print(f"\nTop 5 at Risk:")
    for p in top_5:
        status = "🔴 SUSPEND" if p['predicted_suspended'] else "🟢 NO SUSPEND"
        print(f"  {p['lgu']:20s} {p['suspension_probability']:6.2%}  {status}")
    print()
