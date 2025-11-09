"""
Comprehensive Performance Testing for Prediction Pipeline
==========================================================

Tests and measures:
- PAGASA typhoon scraping latency
- Open-Meteo API connection and response time
- Feature engineering time
- Model loading time
- Prediction generation time
- Database logging latency
- Total end-to-end time

Usage:
    python test_performance.py
"""

import time
import sys
from pathlib import Path
from datetime import datetime, date

# Add project directories to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'backfill'))
sys.path.insert(0, str(project_root / 'nodejs-pagasa'))
import json
import statistics

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from database.supabase_client import SupabaseLogger
from src.weather.weather_pipeline import WeatherDataPipeline
import joblib


class PerformanceTest:
    def __init__(self):
        self.results = {
            'test_timestamp': datetime.now().isoformat(),
            'components': {},
            'iterations': 3,  # Test each component 3 times for average
            'summary': {}
        }
    
    def time_function(self, func, name, iterations=3):
        """Time a function over multiple iterations"""
        print(f"\n{'='*60}")
        print(f"Testing: {name}")
        print(f"{'='*60}")
        
        timings = []
        errors = []
        
        for i in range(iterations):
            print(f"  Iteration {i+1}/{iterations}...", end=' ', flush=True)
            start = time.time()
            
            try:
                result = func()
                elapsed = time.time() - start
                timings.append(elapsed)
                print(f"✅ {elapsed:.3f}s")
            except Exception as e:
                elapsed = time.time() - start
                errors.append(str(e))
                print(f"❌ Failed: {e}")
        
        if timings:
            avg_time = statistics.mean(timings)
            min_time = min(timings)
            max_time = max(timings)
            
            self.results['components'][name] = {
                'timings': timings,
                'average_ms': avg_time * 1000,
                'min_ms': min_time * 1000,
                'max_ms': max_time * 1000,
                'success_rate': len(timings) / iterations * 100,
                'errors': errors
            }
            
            print(f"\n  📊 Results:")
            print(f"     Average: {avg_time*1000:.1f}ms")
            print(f"     Min: {min_time*1000:.1f}ms")
            print(f"     Max: {max_time*1000:.1f}ms")
            print(f"     Success: {len(timings)}/{iterations}")
        else:
            print(f"\n  ❌ All iterations failed")
            self.results['components'][name] = {
                'timings': [],
                'average_ms': None,
                'errors': errors,
                'success_rate': 0
            }
    
    def test_pagasa_typhoon_scraping(self):
        """Test PAGASA typhoon bulletin scraping"""
        from src.weather.pagasa_checker import PAGASAChecker
        
        def run():
            checker = PAGASAChecker()
            result = checker.check_typhoon_status()
            return result
        
        self.time_function(run, "PAGASA Typhoon Scraping")
    
    def test_pagasa_rainfall_scraping(self):
        """Test PAGASA rainfall warning scraping"""
        from src.weather.pagasa_checker import PAGASAChecker
        
        def run():
            checker = PAGASAChecker()
            result = checker.get_rainfall_warning()
            return result
        
        self.time_function(run, "PAGASA Rainfall Warning Scraping")
    
    def test_openmeteo_connection(self):
        """Test Open-Meteo API connection"""
        from src.weather.openmeteo_collector import OpenMeteoCollector
        
        def run():
            collector = OpenMeteoCollector()
            # Test with single location
            test_coords = {'latitude': 14.5995, 'longitude': 120.9842}  # Manila
            data = collector.fetch_forecast(
                test_coords['latitude'],
                test_coords['longitude'],
                days=2
            )
            return data
        
        self.time_function(run, "Open-Meteo API Connection (Single Location)")
    
    def test_openmeteo_full_fetch(self):
        """Test full Open-Meteo fetch for all 17 LGUs"""
        from src.weather.openmeteo_collector import OpenMeteoCollector
        
        # Metro Manila LGU coordinates
        lgus = [
            {'name': 'Manila', 'lat': 14.5995, 'lon': 120.9842},
            {'name': 'Quezon City', 'lat': 14.6760, 'lon': 121.0437},
            {'name': 'Caloocan', 'lat': 14.6488, 'lon': 120.9830},
            {'name': 'Las Piñas', 'lat': 14.4453, 'lon': 120.9842},
            {'name': 'Makati', 'lat': 14.5547, 'lon': 121.0244},
            {'name': 'Malabon', 'lat': 14.6620, 'lon': 120.9633},
            {'name': 'Mandaluyong', 'lat': 14.5794, 'lon': 121.0359},
            {'name': 'Marikina', 'lat': 14.6507, 'lon': 121.1029},
            {'name': 'Muntinlupa', 'lat': 14.3832, 'lon': 121.0409},
            {'name': 'Navotas', 'lat': 14.6670, 'lon': 120.9401},
            {'name': 'Parañaque', 'lat': 14.4793, 'lon': 121.0198},
            {'name': 'Pasay', 'lat': 14.5378, 'lon': 120.9896},
            {'name': 'Pasig', 'lat': 14.5764, 'lon': 121.0851},
            {'name': 'Pateros', 'lat': 14.5408, 'lon': 121.0681},
            {'name': 'San Juan', 'lat': 14.6019, 'lon': 121.0355},
            {'name': 'Taguig', 'lat': 14.5176, 'lon': 121.0509},
            {'name': 'Valenzuela', 'lat': 14.6990, 'lon': 120.9830}
        ]
        
        def run():
            collector = OpenMeteoCollector()
            results = []
            for lgu in lgus:
                data = collector.fetch_forecast(lgu['lat'], lgu['lon'], days=2)
                results.append(data)
            return results
        
        self.time_function(run, "Open-Meteo Full Fetch (17 LGUs)", iterations=2)
    
    def test_feature_engineering(self):
        """Test feature engineering from raw data"""
        import pandas as pd
        import numpy as np
        
        # Create sample raw data
        sample_data = {
            'year': [2025] * 17,
            'month': [11] * 17,
            'day': [8] * 17,
            'day_of_week': [4] * 17,
            'lgu_id': list(range(1, 18)),
            'mean_flood_risk_score': [0.5] * 17,
            'precipitation_t1': [10.0] * 17,
            'wind_speed_t1': [20.0] * 17,
            'gusts_t1': [30.0] * 17,
            'pressure_t1': [1013.0] * 17,
            'temperature_t1': [28.0] * 17,
            'humidity_t1': [80.0] * 17,
            'cloud_cover_t1': [60.0] * 17,
            'dew_point_t1': [24.0] * 17,
            'apparent_temp_t1': [30.0] * 17,
            'weather_code_t1': [3] * 17,
            'precipitation_sum_7d': [50.0] * 17,
            'precipitation_sum_3d': [20.0] * 17,
            'wind_speed_max_7d': [40.0] * 17,
            'precipitation_sum': [35.0] * 17,
            'precipitation_hours': [6.0] * 17,
            'wind_speed_max': [55.0] * 17,
            'gusts_max': [70.0] * 17,
            'pressure_mean': [1012.0] * 17,
            'temperature_max': [32.0] * 17,
            'humidity_mean': [75.0] * 17,
            'cloud_cover_mean': [50.0] * 17,
            'dew_point_mean': [23.0] * 17,
            'cape_max': [1000.0] * 17
        }
        
        def run():
            df = pd.DataFrame(sample_data)
            
            # Add computed features
            df['is_rainy_season'] = df['month'].apply(lambda x: 1 if x in [6,7,8,9,10,11] else 0)
            df['month_from_sy_start'] = df['month'].apply(lambda x: x - 6 if x >= 6 else x + 6)
            df['is_holiday'] = 0
            df['is_school_day'] = df['day_of_week'].apply(lambda x: 1 if x < 5 else 0)
            
            # Normalize/scale features (simplified)
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            df_scaled = df[numeric_cols].copy()
            
            return df_scaled
        
        self.time_function(run, "Feature Engineering (17 LGUs)")
    
    def test_model_loading(self):
        """Test ML model loading time"""
        model_path = PROJECT_ROOT / 'model-training' / 'data' / 'processed' / 'best_core_model.pkl'
        
        def run():
            model = joblib.load(model_path)
            return model
        
        self.time_function(run, "ML Model Loading (EasyEnsemble)")
    
    def test_model_prediction(self):
        """Test prediction generation time"""
        import pandas as pd
        import numpy as np
        
        model_path = PROJECT_ROOT / 'model-training' / 'data' / 'processed' / 'best_core_model.pkl'
        model = joblib.load(model_path)
        
        # Create sample features (33 features)
        sample_features = pd.DataFrame({
            'year': [2025] * 17,
            'month': [11] * 17,
            'day': [8] * 17,
            'day_of_week': [4] * 17,
            'lgu_id': list(range(1, 18)),
            'mean_flood_risk_score': [0.5] * 17,
            'precipitation_t1': [10.0] * 17,
            'wind_speed_t1': [20.0] * 17,
            'gusts_t1': [30.0] * 17,
            'pressure_t1': [1013.0] * 17,
            'temperature_t1': [28.0] * 17,
            'humidity_t1': [80.0] * 17,
            'cloud_cover_t1': [60.0] * 17,
            'dew_point_t1': [24.0] * 17,
            'apparent_temp_t1': [30.0] * 17,
            'weather_code_t1': [3] * 17,
            'precipitation_sum_7d': [50.0] * 17,
            'precipitation_sum_3d': [20.0] * 17,
            'wind_speed_max_7d': [40.0] * 17,
            'precipitation_sum': [35.0] * 17,
            'precipitation_hours': [6.0] * 17,
            'wind_speed_max': [55.0] * 17,
            'gusts_max': [70.0] * 17,
            'pressure_mean': [1012.0] * 17,
            'temperature_max': [32.0] * 17,
            'humidity_mean': [75.0] * 17,
            'cloud_cover_mean': [50.0] * 17,
            'dew_point_mean': [23.0] * 17,
            'cape_max': [1000.0] * 17,
            'is_rainy_season': [1] * 17,
            'month_from_sy_start': [5] * 17,
            'is_holiday': [0] * 17,
            'is_school_day': [1] * 17
        })
        
        def run():
            predictions = model.predict_proba(sample_features)[:, 1]
            return predictions
        
        self.time_function(run, "Model Prediction (17 LGUs)")
    
    def test_database_logging(self):
        """Test Supabase database logging time"""
        import os
        
        if not os.getenv('SUPABASE_URL') or not os.getenv('SUPABASE_KEY'):
            print("\n⚠️  Skipping database test - no credentials")
            return
        
        def run():
            logger = SupabaseLogger()
            # Log a test entry
            logger.log_pagasa_status({
                'has_active_typhoon': 1,
                'typhoon_name': 'TEST',
                'tcws_level': 0,
                'has_rainfall_warning': 0,
                'rainfall_warning_level': 0
            })
            return True
        
        self.time_function(run, "Database Logging (Supabase)")
    
    def test_end_to_end(self):
        """Test complete end-to-end pipeline"""
        print(f"\n{'='*60}")
        print(f"Testing: Complete End-to-End Pipeline")
        print(f"{'='*60}")
        
        start = time.time()
        
        try:
            # This would run the full collect_and_log.py script
            # For now, simulate the pipeline
            print("  Running full pipeline simulation...")
            
            # 1. Data collection
            time.sleep(0.5)  # Simulate PAGASA
            time.sleep(2.0)  # Simulate Open-Meteo
            
            # 2. Feature engineering
            time.sleep(0.2)
            
            # 3. Model prediction
            time.sleep(0.1)
            
            # 4. Database logging
            time.sleep(0.3)
            
            elapsed = time.time() - start
            
            self.results['components']['End-to-End Pipeline'] = {
                'total_time_ms': elapsed * 1000,
                'note': 'Simulated - run scripts/collect_and_log.py for real test'
            }
            
            print(f"  ✅ Completed in {elapsed:.2f}s")
            
        except Exception as e:
            print(f"  ❌ Failed: {e}")
    
    def generate_summary(self):
        """Generate performance summary"""
        print(f"\n{'='*60}")
        print(f"PERFORMANCE SUMMARY")
        print(f"{'='*60}\n")
        
        # Calculate totals
        total_avg = 0
        component_count = 0
        
        for name, metrics in self.results['components'].items():
            if 'average_ms' in metrics and metrics['average_ms'] is not None:
                total_avg += metrics['average_ms']
                component_count += 1
                
                status = "✅" if metrics.get('success_rate', 0) == 100 else "⚠️"
                print(f"{status} {name:50} {metrics['average_ms']:8.1f}ms")
        
        print(f"\n{'='*60}")
        print(f"Total Average Time: {total_avg:.1f}ms ({total_avg/1000:.2f}s)")
        print(f"Components Tested: {component_count}")
        print(f"{'='*60}\n")
        
        # Recommendations
        print("📊 Performance Insights:\n")
        
        for name, metrics in self.results['components'].items():
            if 'average_ms' in metrics and metrics['average_ms'] is not None:
                avg = metrics['average_ms']
                
                if avg > 5000:
                    print(f"⚠️  {name}: SLOW ({avg:.0f}ms) - Consider optimization")
                elif avg > 2000:
                    print(f"🔸 {name}: Moderate ({avg:.0f}ms) - Acceptable")
                else:
                    print(f"✅ {name}: Fast ({avg:.0f}ms)")
        
        self.results['summary'] = {
            'total_average_ms': total_avg,
            'total_average_s': total_avg / 1000,
            'components_tested': component_count
        }
    
    def save_results(self):
        """Save results to JSON file"""
        output_file = PROJECT_ROOT / 'backfill' / 'output' / 'performance_test_results.json'
        output_file.parent.mkdir(exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n💾 Results saved to: {output_file}")
    
    def run_all_tests(self):
        """Run all performance tests"""
        print(f"\n{'#'*60}")
        print(f"# PREDICTION PIPELINE PERFORMANCE TEST")
        print(f"# {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'#'*60}\n")
        
        # Run all component tests
        self.test_pagasa_typhoon_scraping()
        self.test_pagasa_rainfall_scraping()
        self.test_openmeteo_connection()
        self.test_openmeteo_full_fetch()
        self.test_feature_engineering()
        self.test_model_loading()
        self.test_model_prediction()
        self.test_database_logging()
        
        # Generate summary
        self.generate_summary()
        
        # Save results
        self.save_results()


if __name__ == '__main__':
    tester = PerformanceTest()
    tester.run_all_tests()
