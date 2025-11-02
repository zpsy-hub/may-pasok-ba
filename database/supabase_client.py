"""
Supabase Database Client for Suspension Prediction System
==========================================================

Handles all database operations:
- Log predictions to database
- Store weather data
- Record PAGASA status
- Track collection runs
- Update actual outcomes

Setup:
------
1. Install: pip install supabase
2. Set environment variables:
   - SUPABASE_URL: Your project URL
   - SUPABASE_KEY: Your service_role key

Usage:
------
from database.supabase_client import SupabaseLogger

logger = SupabaseLogger()
logger.log_predictions(predictions_df)
logger.log_weather_data(weather_df)
logger.log_pagasa_status(pagasa_data)
"""

import os
from datetime import datetime, date, time
from typing import Dict, List, Optional, Any
import pandas as pd
from supabase import create_client, Client


class SupabaseLogger:
    """Database logger for suspension prediction system."""
    
    def __init__(self, url: Optional[str] = None, key: Optional[str] = None):
        """
        Initialize Supabase client.
        
        Args:
            url: Supabase project URL (defaults to SUPABASE_URL env var)
            key: Supabase service_role key (defaults to SUPABASE_KEY env var)
        """
        self.url = url or os.getenv('SUPABASE_URL')
        self.key = key or os.getenv('SUPABASE_KEY')
        
        if not self.url or not self.key:
            raise ValueError(
                "Supabase credentials not found. Set SUPABASE_URL and SUPABASE_KEY "
                "environment variables or pass them to constructor."
            )
        
        self.client: Client = create_client(self.url, self.key)
        self.github_run_id = os.getenv('GITHUB_RUN_ID', 'local')
    
    def log_predictions(
        self, 
        predictions: List[Dict[str, Any]],
        model_version: str,
        threshold: float
    ) -> Dict[str, Any]:
        """
        Log daily predictions to database.
        
        Args:
            predictions: List of prediction dicts with keys:
                - prediction_date (date or str)
                - lgu (str)
                - suspension_probability (float)
                - predicted_suspended (bool)
            model_version: Model version identifier
            threshold: Threshold used for classification
        
        Returns:
            Response from Supabase insert
        
        Example:
            predictions = [
                {
                    'prediction_date': '2025-11-02',
                    'lgu': 'Manila',
                    'suspension_probability': 0.8234,
                    'predicted_suspended': True
                }
            ]
            logger.log_predictions(predictions, 'v1.0.0', 0.5)
        """
        records = []
        for pred in predictions:
            record = {
                'prediction_date': str(pred['prediction_date']),
                'lgu': pred['lgu'],
                'suspension_probability': float(pred['suspension_probability']),
                'predicted_suspended': bool(pred['predicted_suspended']),
                'model_version': model_version,
                'threshold_used': float(threshold),
                'github_run_id': self.github_run_id
            }
            records.append(record)
        
        response = self.client.table('daily_predictions').upsert(
            records,
            on_conflict='prediction_date,lgu'
        ).execute()
        
        return response.data
    
    def log_weather_data(
        self,
        weather_df: pd.DataFrame,
        data_type: str = 'forecast'
    ) -> Dict[str, Any]:
        """
        Log weather data to database.
        
        Args:
            weather_df: DataFrame with columns:
                - weather_date (date or str)
                - lgu (str)
                - precipitation_sum, temperature_2m_max, etc.
            data_type: 'forecast' or 'actual'
        
        Returns:
            Response from Supabase insert
        
        Example:
            weather_df = pd.DataFrame({
                'weather_date': ['2025-11-02', '2025-11-02'],
                'lgu': ['Manila', 'Quezon City'],
                'precipitation_sum': [15.5, 12.3],
                'temperature_2m_max': [32.1, 31.8],
                ...
            })
            logger.log_weather_data(weather_df, data_type='forecast')
        """
        records = []
        for _, row in weather_df.iterrows():
            record = {
                'weather_date': str(row['weather_date']) if 'weather_date' in row else str(row.get('date')),
                'lgu': row['lgu'],
                'data_type': data_type,
                'source': 'open-meteo'
            }
            
            # Add weather variables if present
            weather_fields = [
                'precipitation_sum', 'temperature_2m_max', 'wind_speed_10m_max',
                'wind_gusts_10m_max', 'relative_humidity_2m_mean', 'cloud_cover_max',
                'pressure_msl_min', 'weather_code', 'precipitation_probability_max'
            ]
            
            for field in weather_fields:
                if field in row and pd.notna(row[field]):
                    record[field] = float(row[field])
            
            records.append(record)
        
        response = self.client.table('weather_data').upsert(
            records,
            on_conflict='weather_date,lgu,data_type'
        ).execute()
        
        return response.data
    
    def log_pagasa_status(
        self,
        status_data: Dict[str, Any],
        status_date: Optional[date] = None,
        status_time: Optional[time] = None
    ) -> Dict[str, Any]:
        """
        Log PAGASA status to database.
        
        Args:
            status_data: Dict with PAGASA status from pagasa_checker
            status_date: Date of status (defaults to today)
            status_time: Time of status (defaults to now)
        
        Returns:
            Response from Supabase insert
        
        Example:
            status = {
                'has_active_typhoon': True,
                'typhoon_name': 'TINO',
                'metro_manila_affected': True,
                'tcws_level': 2,
                'has_rainfall_warning': True,
                'rainfall_warning_level': 'ORANGE'
            }
            logger.log_pagasa_status(status)
        """
        now = datetime.now()
        
        record = {
            'status_date': str(status_date or now.date()),
            'status_time': str(status_time or now.time()),
            'has_active_typhoon': bool(status_data.get('has_active_typhoon', False)),
            'typhoon_name': status_data.get('typhoon_name'),
            'typhoon_status': status_data.get('typhoon_status'),
            'bulletin_number': status_data.get('bulletin_number'),
            'bulletin_age': status_data.get('bulletin_age'),
            'metro_manila_affected': bool(status_data.get('metro_manila_affected', False)),
            'tcws_level': int(status_data.get('tcws_level', 0)),
            'has_rainfall_warning': bool(status_data.get('has_rainfall_warning', False)),
            'rainfall_warning_level': status_data.get('rainfall_warning_level'),
            'metro_manila_rainfall_status': status_data.get('metro_manila_rainfall_status'),
            'bulletin_url': status_data.get('bulletin_url')
        }
        
        response = self.client.table('pagasa_status').insert(record).execute()
        return response.data
    
    def log_collection_run(
        self,
        run_date: Optional[date] = None,
        pagasa_success: bool = False,
        pagasa_error: Optional[str] = None,
        openmeteo_success: bool = False,
        openmeteo_records: int = 0,
        openmeteo_error: Optional[str] = None,
        predictions_success: bool = False,
        predictions_count: int = 0,
        predictions_error: Optional[str] = None,
        duration_seconds: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Log collection run status to database.
        
        Args:
            run_date: Date of run (defaults to today)
            pagasa_success: Whether PAGASA collection succeeded
            pagasa_error: Error message if failed
            openmeteo_success: Whether Open-Meteo collection succeeded
            openmeteo_records: Number of weather records collected
            openmeteo_error: Error message if failed
            predictions_success: Whether predictions were generated
            predictions_count: Number of predictions generated
            predictions_error: Error message if failed
            duration_seconds: Total run duration
        
        Returns:
            Response from Supabase insert
        
        Example:
            logger.log_collection_run(
                pagasa_success=True,
                openmeteo_success=True,
                openmeteo_records=51,
                predictions_success=True,
                predictions_count=17,
                duration_seconds=45
            )
        """
        now = datetime.now()
        
        record = {
            'run_date': str(run_date or now.date()),
            'run_time': str(now.time()),
            'github_run_id': self.github_run_id,
            'github_workflow': os.getenv('GITHUB_WORKFLOW', 'deploy.yml'),
            'pagasa_collection_success': pagasa_success,
            'pagasa_error': pagasa_error,
            'openmeteo_collection_success': openmeteo_success,
            'openmeteo_records_collected': openmeteo_records,
            'openmeteo_error': openmeteo_error,
            'predictions_generated': predictions_success,
            'predictions_count': predictions_count,
            'predictions_error': predictions_error,
            'total_duration_seconds': duration_seconds
        }
        
        response = self.client.table('collection_logs').insert(record).execute()
        return response.data
    
    def update_actual_outcome(
        self,
        prediction_date: date,
        lgu: str,
        actual_suspended: bool
    ) -> Dict[str, Any]:
        """
        Update actual suspension outcome for a prediction.
        
        Args:
            prediction_date: Date of prediction
            lgu: LGU name
            actual_suspended: Whether suspension actually occurred
        
        Returns:
            Response from Supabase update
        
        Example:
            logger.update_actual_outcome(
                date(2025, 11, 2),
                'Manila',
                actual_suspended=True
            )
        """
        response = self.client.table('daily_predictions').update({
            'actual_suspended': actual_suspended
        }).eq('prediction_date', str(prediction_date)).eq('lgu', lgu).execute()
        
        return response.data
    
    def get_latest_predictions(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get latest predictions from database.
        
        Args:
            limit: Maximum number of records to return
        
        Returns:
            List of prediction records
        """
        response = self.client.table('daily_predictions')\
            .select('*')\
            .order('prediction_date', desc=True)\
            .limit(limit)\
            .execute()
        
        return response.data
    
    def get_latest_weather(
        self,
        data_type: str = 'forecast',
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get latest weather data from database.
        
        Args:
            data_type: 'forecast' or 'actual'
            limit: Maximum number of records to return
        
        Returns:
            List of weather records
        """
        response = self.client.table('weather_data')\
            .select('*')\
            .eq('data_type', data_type)\
            .order('weather_date', desc=True)\
            .limit(limit)\
            .execute()
        
        return response.data
    
    def get_prediction_accuracy(self) -> List[Dict[str, Any]]:
        """
        Get prediction accuracy by LGU.
        
        Returns:
            List of accuracy records from view
        """
        response = self.client.table('prediction_accuracy_by_lgu')\
            .select('*')\
            .execute()
        
        return response.data
    
    def get_collection_reliability(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Get collection reliability stats.
        
        Args:
            days: Number of days to look back
        
        Returns:
            List of reliability records from view
        """
        response = self.client.table('collection_reliability')\
            .select('*')\
            .limit(days)\
            .execute()
        
        return response.data


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == '__main__':
    """
    Demo of database logging functionality.
    
    Before running:
    1. Set SUPABASE_URL and SUPABASE_KEY environment variables
    2. Run schema.sql in Supabase SQL Editor
    """
    import sys
    from datetime import date, timedelta
    
    try:
        # Initialize logger
        logger = SupabaseLogger()
        print("✅ Connected to Supabase")
        
        # Example 1: Log predictions
        print("\n📊 Logging predictions...")
        predictions = [
            {
                'prediction_date': date.today(),
                'lgu': 'Manila',
                'suspension_probability': 0.8234,
                'predicted_suspended': True
            },
            {
                'prediction_date': date.today(),
                'lgu': 'Quezon City',
                'suspension_probability': 0.6123,
                'predicted_suspended': True
            }
        ]
        result = logger.log_predictions(predictions, model_version='v1.0.0', threshold=0.5)
        print(f"✅ Logged {len(result)} predictions")
        
        # Example 2: Log weather data
        print("\n🌤️ Logging weather data...")
        weather_df = pd.DataFrame({
            'weather_date': [date.today(), date.today()],
            'lgu': ['Manila', 'Quezon City'],
            'precipitation_sum': [15.5, 12.3],
            'temperature_2m_max': [32.1, 31.8],
            'wind_speed_10m_max': [25.4, 23.1]
        })
        result = logger.log_weather_data(weather_df, data_type='forecast')
        print(f"✅ Logged {len(result)} weather records")
        
        # Example 3: Log PAGASA status
        print("\n🌀 Logging PAGASA status...")
        pagasa_status = {
            'has_active_typhoon': True,
            'typhoon_name': 'TINO',
            'metro_manila_affected': True,
            'tcws_level': 2,
            'has_rainfall_warning': True,
            'rainfall_warning_level': 'ORANGE'
        }
        result = logger.log_pagasa_status(pagasa_status)
        print(f"✅ Logged PAGASA status")
        
        # Example 4: Log collection run
        print("\n📝 Logging collection run...")
        result = logger.log_collection_run(
            pagasa_success=True,
            openmeteo_success=True,
            openmeteo_records=34,
            predictions_success=True,
            predictions_count=17,
            duration_seconds=45
        )
        print(f"✅ Logged collection run")
        
        # Example 5: Get latest predictions
        print("\n📖 Reading latest predictions...")
        predictions = logger.get_latest_predictions(limit=5)
        print(f"✅ Retrieved {len(predictions)} predictions")
        for pred in predictions[:3]:
            print(f"   {pred['prediction_date']} - {pred['lgu']}: {pred['suspension_probability']:.2%}")
        
        # Example 6: Get accuracy stats
        print("\n📈 Checking accuracy...")
        accuracy = logger.get_prediction_accuracy()
        if accuracy:
            print(f"✅ Retrieved accuracy for {len(accuracy)} LGUs")
            for acc in accuracy[:3]:
                print(f"   {acc['lgu']}: {acc.get('accuracy_percentage', 'N/A')}% accuracy")
        else:
            print("   ℹ️ No accuracy data yet (need actual outcomes)")
        
        print("\n✅ All database operations successful!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure:")
        print("1. SUPABASE_URL and SUPABASE_KEY are set")
        print("2. schema.sql has been run in Supabase")
        sys.exit(1)
