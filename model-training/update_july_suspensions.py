"""
Quick script to update July 23-25, 2025 suspension flags in master datasets
"""
import pandas as pd
from pathlib import Path

PROCESSED_DIR = Path(__file__).parent / "data" / "processed"

# Define the July suspension dates
JULY_SUSPENSIONS = {
    '2025-07-23': 'BAGYO',
    '2025-07-24': 'BAGYO',
    '2025-07-25': 'BAGYO'
}

def update_master_file(filename):
    """Update suspension flags for July 23-25, 2025"""
    filepath = PROCESSED_DIR / filename
    
    print(f"\n📄 Processing {filename}...")
    
    # Read the CSV
    df = pd.read_csv(filepath)
    
    # Show current state
    july_23_before = df[df['date'] == '2025-07-23']['suspension_occurred'].sum()
    july_24_before = df[df['date'] == '2025-07-24']['suspension_occurred'].sum()
    july_25_before = df[df['date'] == '2025-07-25']['suspension_occurred'].sum()
    
    print(f"   Before: July 23 suspensions = {july_23_before}/17, July 24 = {july_24_before}/17, July 25 = {july_25_before}/17")
    
    # Update July 23, 2025
    mask_july23 = df['date'] == '2025-07-23'
    df.loc[mask_july23, 'suspension_occurred'] = 1
    df.loc[mask_july23, 'reason_category'] = 'BAGYO'
    
    # Update July 24, 2025
    mask_july24 = df['date'] == '2025-07-24'
    df.loc[mask_july24, 'suspension_occurred'] = 1
    df.loc[mask_july24, 'reason_category'] = 'BAGYO'
    
    # Update July 25, 2025
    mask_july25 = df['date'] == '2025-07-25'
    df.loc[mask_july25, 'suspension_occurred'] = 1
    df.loc[mask_july25, 'reason_category'] = 'BAGYO'
    
    # Verify updates
    july_23_after = df[df['date'] == '2025-07-23']['suspension_occurred'].sum()
    july_24_after = df[df['date'] == '2025-07-24']['suspension_occurred'].sum()
    july_25_after = df[df['date'] == '2025-07-25']['suspension_occurred'].sum()
    
    print(f"   After:  July 23 = {july_23_after}/17, "
          f"July 24 = {july_24_after}/17, "
          f"July 25 = {july_25_after}/17")
    
    # Save back
    df.to_csv(filepath, index=False)
    print("   ✅ Updated and saved!")
    
    return df


if __name__ == "__main__":
    print("🔄 Updating July 23-25, 2025 suspension flags...")
    
    # Update all three master files
    files = ['master_train.csv', 'master_validation.csv', 'master_test.csv']
    for filename in files:
        try:
            update_master_file(filename)
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n✅ All master datasets updated!")
    print("\n📊 Summary:")
    
    # Show final counts
    test_df = pd.read_csv(PROCESSED_DIR / 'master_test.csv')
    
    print(f"   Total test rows: {len(test_df)}")
    
    for date in ['2025-07-23', '2025-07-24', '2025-07-25']:
        date_rows = len(test_df[test_df['date'] == date])
        suspensions = test_df[test_df['date'] == date]['suspension_occurred'].sum()
        print(f"   {date}: {date_rows} rows, {suspensions} suspensions")
