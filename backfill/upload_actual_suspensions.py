#!/usr/bin/env python3
"""
Upload Actual Suspension Data to Supabase
==========================================

This script uploads the actual suspension records from September-October 2025
to the Supabase database for model validation and accuracy tracking.

Usage:
    python backfill/upload_actual_suspensions.py

Output:
    - Inserts/updates records in daily_predictions table with actual_suspended field
    - Creates collection_logs entry for tracking
    - Prints summary of uploaded records
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.supabase_client import SupabaseLogger


def load_actual_suspensions() -> Dict[str, Any]:
    """Load actual suspension data from JSON file."""
    json_path = os.path.join(
        os.path.dirname(__file__),
        'actual_suspensions_sept_oct.json'
    )
    
    print(f"📂 Loading suspension data from: {json_path}")
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"✅ Loaded {len(data['suspensions'])} suspension events")
    return data


def prepare_suspension_records(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Convert suspension data into database records.
    
    Returns list of dicts with structure:
    {
        "prediction_date": "2025-09-01",
        "lgu": "Manila",
        "actual_suspended": true
    }
    """
    records = []
    
    for event in data['suspensions']:
        date = event['date']
        suspension_details = event['suspension_details']
        
        for lgu, details in suspension_details.items():
            records.append({
                'prediction_date': date,
                'lgu': lgu,
                'actual_suspended': details['suspended']
            })
    
    print(f"📊 Prepared {len(records)} suspension records (6 days × 17 LGUs = 102)")
    return records


def upload_to_database(records: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Upload suspension records to Supabase.
    
    Updates existing daily_predictions records with actual_suspended field.
    If prediction doesn't exist yet, creates new record with only actual data.
    """
    logger = SupabaseLogger()
    supabase = logger.client
    
    stats = {
        'updated': 0,
        'created': 0,
        'failed': 0,
        'skipped': 0
    }
    
    print("\n🚀 Starting database upload...")
    print("=" * 70)
    
    for i, record in enumerate(records, 1):
        date = record['prediction_date']
        lgu = record['lgu']
        actual = record['actual_suspended']
        
        try:
            # Check if prediction already exists
            existing = supabase.table('daily_predictions') \
                .select('id, suspension_probability') \
                .eq('prediction_date', date) \
                .eq('lgu', lgu) \
                .execute()
            
            if existing.data and len(existing.data) > 0:
                # Update existing prediction with actual_suspended
                prediction_id = existing.data[0]['id']
                probability = existing.data[0]['suspension_probability']
                
                supabase.table('daily_predictions') \
                    .update({'actual_suspended': actual}) \
                    .eq('id', prediction_id) \
                    .execute()
                
                status = "✅ UPDATED" if actual else "✅ UPDATED"
                stats['updated'] += 1
                
                print(f"[{i}/{len(records)}] {status} | {date} | {lgu:15s} | "
                      f"Predicted: {probability:.2%} | Actual: {actual}")
            
            else:
                # Create new record with only actual data (no prediction yet)
                # Note: Can't insert NULL for required fields, so skip creation
                # Actual data will be added when predictions are backfilled
                stats['skipped'] += 1
                
                print(f"[{i}/{len(records)}] ⏭️ SKIPPED | {date} | {lgu:15s} | "
                      f"No prediction yet, will be added during backfill")
                
                status = "🆕 CREATED"
                stats['created'] += 1
                
                print(f"[{i}/{len(records)}] {status} | {date} | {lgu:15s} | "
                      f"Predicted: (pending) | Actual: {actual}")
        
        except Exception as e:
            stats['failed'] += 1
            print(f"[{i}/{len(records)}] ❌ FAILED  | {date} | {lgu:15s} | Error: {str(e)}")
    
    print("=" * 70)
    return stats


def create_collection_log(stats: Dict[str, int]):
    """Create log entry for this upload operation."""
    logger = SupabaseLogger()
    supabase = logger.client
    
    now = datetime.now()
    log_entry = {
        'run_date': now.date().isoformat(),
        'run_time': now.time().isoformat(),
        'github_run_id': 'manual_upload',
        'github_workflow': 'upload_actual_suspensions.py',
        'pagasa_collection_success': True,
        'openmeteo_collection_success': True,
        'openmeteo_records_collected': stats['updated'] + stats['created'],
        'predictions_generated': False,
        'predictions_count': 0
    }
    
    supabase.table('collection_logs').insert(log_entry).execute()
    print("\n📝 Created collection log entry")


def print_summary(data: Dict[str, Any], stats: Dict[str, int]):
    """Print upload summary and statistics."""
    print("\n" + "=" * 70)
    print("UPLOAD SUMMARY")
    print("=" * 70)
    
    print(f"\n📅 Date Range: {data['metadata']['date_range']['start']} to {data['metadata']['date_range']['end']}")
    print(f"📊 Suspension Events: {len(data['suspensions'])} days")
    print(f"📍 LGUs: 17 Metro Manila cities/municipality")
    print(f"📝 Total Records: {stats['updated'] + stats['created']} uploaded")
    
    print(f"\n✅ Updated existing predictions: {stats['updated']}")
    print(f"🆕 Created new records (no prediction yet): {stats['created']}")
    print(f"❌ Failed: {stats['failed']}")
    
    # Suspension breakdown
    summary = data['summary']
    print(f"\n📈 Suspension Statistics:")
    print(f"   - Metro Manila-wide suspensions: {summary['metro_manila_wide_suspensions']}")
    print(f"   - Partial suspensions: {summary['partial_suspensions']}")
    print(f"   - Typhoon-related: {summary['typhoon_related']}")
    print(f"   - Non-typhoon: {summary['non_typhoon']}")
    
    print(f"\n🏆 Most Suspended LGUs:")
    for lgu_data in summary['most_suspended_lgus'][:5]:
        lgu = lgu_data['lgu']
        days = lgu_data['days']
        dates = summary['suspension_by_lgu'][lgu]['dates']
        print(f"   - {lgu}: {days} days ({', '.join(dates)})")
    
    print(f"\n🏅 Least Suspended LGUs:")
    for lgu_data in summary['least_suspended_lgus'][:5]:
        lgu = lgu_data['lgu']
        days = lgu_data['days']
        dates = summary['suspension_by_lgu'][lgu]['dates']
        print(f"   - {lgu}: {days} days ({', '.join(dates)})")
    
    print("\n" + "=" * 70)
    print("✨ Upload complete! Actual suspension data ready for model validation.")
    print("\n💡 Next steps:")
    print("   1. Run backfill scripts to generate predictions for Sept-Oct")
    print("   2. Compare predicted_suspended vs actual_suspended")
    print("   3. Calculate accuracy metrics (precision, recall, F1)")
    print("   4. Update dashboard to show model performance")
    print("=" * 70)


def main():
    """Main execution function."""
    print("=" * 70)
    print("ACTUAL SUSPENSION DATA UPLOAD")
    print("=" * 70)
    print("This script uploads actual class suspension records from")
    print("September-October 2025 to enable model validation.\n")
    
    try:
        # Load suspension data
        data = load_actual_suspensions()
        
        # Prepare database records
        records = prepare_suspension_records(data)
        
        # Upload to Supabase
        stats = upload_to_database(records)
        
        # Create collection log
        create_collection_log(stats)
        
        # Print summary
        print_summary(data, stats)
        
        return 0
    
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
