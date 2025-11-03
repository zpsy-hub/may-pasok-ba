"""
Historical Weather Data Collector
==================================

Fetches historical weather data from Open-Meteo Archive API for Sept 1 - Oct 31, 2025.

Usage:
------
python backfill/collect_historical_weather.py

Output:
-------
backfill/output/weather_sept_oct.json

Features:
---------
- Collects data for all 17 Metro Manila LGUs
- Rate limited to 1 request/second (avoid API throttling)
- Handles API errors with retries
- Caches results to avoid re-fetching
- Progress tracking with visual feedback
"""

import json
import time
import sys
from pathlib import Path
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional
import requests
from tqdm import tqdm

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load configuration
CONFIG_FILE = Path(__file__).parent / 'config.json'
OUTPUT_DIR = Path(__file__).parent / 'output'
OUTPUT_FILE = OUTPUT_DIR / 'weather_sept_oct.json'


def load_config() -> dict:
    """Load configuration from config.json."""
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)


def parse_date(date_str: str) -> date:
    """Parse date string in YYYY-MM-DD format."""
    return datetime.strptime(date_str, '%Y-%m-%d').date()


def generate_date_range(start_date: date, end_date: date) -> List[date]:
    """Generate list of dates between start and end (inclusive)."""
    dates = []
    current = start_date
    while current <= end_date:
        dates.append(current)
        current += timedelta(days=1)
    return dates


def fetch_weather_for_lgu(
    lgu: str,
    lat: float,
    lon: float,
    start_date: date,
    end_date: date,
    variables: List[str],
    base_url: str,
    retry_count: int = 3,
    retry_delay: int = 5
) -> Optional[Dict]:
    """
    Fetch historical weather data for a single LGU.
    
    Args:
        lgu: LGU name
        lat: Latitude
        lon: Longitude
        start_date: Start date
        end_date: End date
        variables: List of weather variables to fetch
        base_url: Open-Meteo API base URL
        retry_count: Number of retries on failure
        retry_delay: Delay between retries (seconds)
    
    Returns:
        Dict with daily weather data or None on failure
    """
    params = {
        'latitude': lat,
        'longitude': lon,
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'daily': ','.join(variables),
        'timezone': 'Asia/Manila'
    }
    
    for attempt in range(retry_count):
        try:
            response = requests.get(base_url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate response structure
                if 'daily' not in data:
                    raise ValueError(f"Missing 'daily' key in response for {lgu}")
                
                return data['daily']
            
            elif response.status_code == 429:
                # Rate limit exceeded
                wait_time = retry_delay * (attempt + 1)
                print(f"\n⚠️  Rate limit exceeded for {lgu}. Waiting {wait_time}s...")
                time.sleep(wait_time)
                continue
            
            else:
                print(f"\n❌ API error for {lgu}: HTTP {response.status_code}")
                if attempt < retry_count - 1:
                    time.sleep(retry_delay)
                    continue
                return None
        
        except requests.exceptions.Timeout:
            print(f"\n⚠️  Timeout for {lgu} (attempt {attempt + 1}/{retry_count})")
            if attempt < retry_count - 1:
                time.sleep(retry_delay)
                continue
            return None
        
        except requests.exceptions.RequestException as e:
            print(f"\n❌ Request error for {lgu}: {e}")
            if attempt < retry_count - 1:
                time.sleep(retry_delay)
                continue
            return None
        
        except Exception as e:
            print(f"\n❌ Unexpected error for {lgu}: {e}")
            return None
    
    return None


def transform_weather_data(
    raw_data: Dict,
    dates: List[date]
) -> Dict[str, Dict]:
    """
    Transform Open-Meteo API response to our desired format.
    
    Args:
        raw_data: Raw API response (daily dict with time and variables arrays)
        dates: List of dates in range
    
    Returns:
        Dict mapping date strings to weather data dicts
    """
    result = {}
    
    # Get time array from response
    time_array = raw_data.get('time', [])
    
    for i, date_str in enumerate(time_array):
        # Parse date from API response
        date_obj = parse_date(date_str)
        
        if date_obj not in dates:
            continue
        
        # Build weather dict for this date
        weather = {}
        for key, values in raw_data.items():
            if key == 'time':
                continue
            
            # Get value at this index (handle missing data)
            value = values[i] if i < len(values) else None
            weather[key] = value
        
        result[date_str] = weather
    
    return result


def collect_historical_weather(
    config: dict,
    resume: bool = True
) -> Dict[str, Dict[str, Dict]]:
    """
    Main function to collect historical weather for all LGUs.
    
    Args:
        config: Configuration dict from config.json
        resume: If True, load existing data and skip already-fetched LGUs
    
    Returns:
        Dict mapping date strings to LGU weather data:
        {
            "2025-09-01": {
                "Manila": { "precipitation_sum": 12.5, ... },
                "Quezon City": { ... }
            },
            ...
        }
    """
    # Parse configuration
    start_date = parse_date(config['date_range']['start'])
    end_date = parse_date(config['date_range']['end'])
    lgus = config['lgus']
    lgu_coords = config['lgu_coordinates']
    api_config = config['open_meteo']
    base_url = api_config['base_url']
    variables = api_config['variables']
    rate_limit = api_config['rate_limit_seconds']
    
    # Generate date range
    dates = generate_date_range(start_date, end_date)
    total_days = len(dates)
    
    print("=" * 70)
    print("HISTORICAL WEATHER DATA COLLECTION")
    print("=" * 70)
    print(f"📅 Date range: {start_date} to {end_date} ({total_days} days)")
    print(f"📍 LGUs: {len(lgus)}")
    print(f"🔢 Total API calls: {len(lgus)} (1 per LGU, covers all dates)")
    print(f"⏱️  Estimated time: ~{len(lgus) * rate_limit / 60:.1f} minutes")
    print(f"🌐 API: {base_url}")
    print(f"📊 Variables: {', '.join(variables)}")
    print()
    
    # Load existing data if resuming
    existing_data = {}
    if resume and OUTPUT_FILE.exists():
        print("📂 Loading existing data...")
        with open(OUTPUT_FILE, 'r') as f:
            existing_data = json.load(f)
        print(f"✅ Loaded data for {len(existing_data)} dates")
        print()
    
    # Initialize result structure with existing data
    # Structure: { "2025-09-01": { "Manila": {...}, "Quezon City": {...} }, ... }
    results = existing_data.copy()
    
    # Initialize date structure if not exists
    for d in dates:
        date_str = d.strftime('%Y-%m-%d')
        if date_str not in results:
            results[date_str] = {}
    
    # Track statistics
    stats = {
        'total_lgus': len(lgus),
        'successful': 0,
        'failed': 0,
        'skipped': 0,
        'api_calls': 0
    }
    
    # Fetch data for each LGU
    print("🚀 Starting data collection...")
    print()
    
    with tqdm(total=len(lgus), desc="Fetching LGUs", unit="LGU") as pbar:
        for lgu in lgus:
            # Check if we already have data for this LGU
            if resume:
                # Check if all dates have data for this LGU
                has_all_data = all(
                    lgu in results.get(d.strftime('%Y-%m-%d'), {})
                    for d in dates
                )
                
                if has_all_data:
                    stats['skipped'] += 1
                    pbar.set_postfix({
                        'Status': 'Skipped',
                        'Success': stats['successful'],
                        'Failed': stats['failed']
                    })
                    pbar.update(1)
                    continue
            
            # Get coordinates
            coords = lgu_coords.get(lgu)
            if not coords:
                print(f"\n⚠️  No coordinates found for {lgu}, skipping...")
                stats['failed'] += 1
                pbar.update(1)
                continue
            
            # Fetch weather data
            pbar.set_postfix({'Status': f'Fetching {lgu}...'})
            raw_data = fetch_weather_for_lgu(
                lgu=lgu,
                lat=coords['lat'],
                lon=coords['lon'],
                start_date=start_date,
                end_date=end_date,
                variables=variables,
                base_url=base_url
            )
            
            stats['api_calls'] += 1
            
            if raw_data:
                # Transform data to our format
                transformed = transform_weather_data(raw_data, dates)
                
                # Merge into results
                for date_str, weather_data in transformed.items():
                    if date_str in results:
                        results[date_str][lgu] = weather_data
                
                stats['successful'] += 1
                pbar.set_postfix({
                    'Status': 'Success',
                    'Success': stats['successful'],
                    'Failed': stats['failed']
                })
            else:
                stats['failed'] += 1
                pbar.set_postfix({
                    'Status': 'Failed',
                    'Success': stats['successful'],
                    'Failed': stats['failed']
                })
            
            pbar.update(1)
            
            # Rate limiting (except for last LGU)
            if lgu != lgus[-1]:
                time.sleep(rate_limit)
    
    print()
    print("=" * 70)
    print("COLLECTION SUMMARY")
    print("=" * 70)
    print(f"✅ Successful: {stats['successful']}")
    print(f"⏭️  Skipped: {stats['skipped']}")
    print(f"❌ Failed: {stats['failed']}")
    print(f"📡 API calls made: {stats['api_calls']}")
    print(f"📊 Dates collected: {len([d for d in results.values() if d])}")
    print()
    
    # Validate results
    missing_dates = []
    incomplete_dates = []
    
    for d in dates:
        date_str = d.strftime('%Y-%m-%d')
        if date_str not in results or not results[date_str]:
            missing_dates.append(date_str)
        elif len(results[date_str]) < len(lgus):
            incomplete_dates.append(date_str)
    
    if missing_dates:
        print(f"⚠️  Missing data for {len(missing_dates)} dates:")
        for d in missing_dates[:5]:
            print(f"   - {d}")
        if len(missing_dates) > 5:
            print(f"   ... and {len(missing_dates) - 5} more")
        print()
    
    if incomplete_dates:
        print(f"⚠️  Incomplete data for {len(incomplete_dates)} dates:")
        for d in incomplete_dates[:5]:
            lgu_count = len(results[d])
            print(f"   - {d}: {lgu_count}/{len(lgus)} LGUs")
        if len(incomplete_dates) > 5:
            print(f"   ... and {len(incomplete_dates) - 5} more")
        print()
    
    return results


def save_results(results: Dict, output_file: Path):
    """Save results to JSON file."""
    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to file
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"💾 Saved results to: {output_file}")
    
    # Calculate file size
    file_size = output_file.stat().st_size
    if file_size < 1024:
        size_str = f"{file_size} bytes"
    elif file_size < 1024 * 1024:
        size_str = f"{file_size / 1024:.1f} KB"
    else:
        size_str = f"{file_size / (1024 * 1024):.1f} MB"
    
    print(f"📦 File size: {size_str}")


def main():
    """Main entry point."""
    try:
        # Load configuration
        config = load_config()
        
        # Collect weather data
        results = collect_historical_weather(config, resume=True)
        
        # Save results
        save_results(results, OUTPUT_FILE)
        
        print()
        print("=" * 70)
        print("✅ COLLECTION COMPLETE!")
        print("=" * 70)
        print(f"📁 Output: {OUTPUT_FILE}")
        print()
        print("Next steps:")
        print("  1. Review the output file for completeness")
        print("  2. Run: python backfill/collect_historical_pagasa.py")
        print("=" * 70)
        
        return 0
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Collection interrupted by user")
        print("💡 Progress has been saved. Run again to resume.")
        return 1
    
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
