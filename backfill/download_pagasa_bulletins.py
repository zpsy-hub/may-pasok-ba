"""
Download PAGASA Tropical Cyclone Bulletins for Nando and Opong
and extract TCWS information for Metro Manila
"""

import requests
import json
from datetime import datetime
from pathlib import Path

# Bulletin URLs for key dates during suspensions
BULLETINS_TO_DOWNLOAD = {
    "nando": [
        {"number": 21, "url": "https://pubfiles.pagasa.dost.gov.ph/tamss/weather/bulletin/TCB%2321_nando.pdf", "date": "2025-09-22", "time": "00:39"},  # Sept 22 start
        {"number": 25, "url": "https://pubfiles.pagasa.dost.gov.ph/tamss/weather/bulletin/TCB%2325_nando.pdf", "date": "2025-09-22", "time": "12:54"},  # Sept 22 midday
        {"number": 28, "url": "https://pubfiles.pagasa.dost.gov.ph/tamss/weather/bulletin/TCB%2328_nando.pdf", "date": "2025-09-23", "time": "04:07"},  # Sept 23 peak
        {"number": 30, "url": "https://pubfiles.pagasa.dost.gov.ph/tamss/weather/bulletin/TCB%2330_nando.pdf", "date": "2025-09-23", "time": "15:40"},  # Sept 23 afternoon
        {"number": 31, "url": "https://pubfiles.pagasa.dost.gov.ph/tamss/weather/bulletin/TCB%2331F_nando.pdf", "date": "2025-09-23", "time": "21:53"},  # Sept 23 final
    ],
    "opong": [
        {"number": 1, "url": "https://pubfiles.pagasa.dost.gov.ph/tamss/weather/bulletin/TCB%231_opong.pdf", "date": "2025-09-23", "time": "10:01"},  # Sept 23 start
        {"number": 4, "url": "https://pubfiles.pagasa.dost.gov.ph/tamss/weather/bulletin/TCB%234_opong.pdf", "date": "2025-09-24", "time": "03:46"},  # Sept 24
        {"number": 7, "url": "https://pubfiles.pagasa.dost.gov.ph/tamss/weather/bulletin/TCB%237_opong.pdf", "date": "2025-09-25", "time": "07:07"},  # Sept 25
        {"number": 10, "url": "https://pubfiles.pagasa.dost.gov.ph/tamss/weather/bulletin/TCB%2310_opong.pdf", "date": "2025-09-25", "time": "07:08"},  # Sept 25
        {"number": 15, "url": "https://pubfiles.pagasa.dost.gov.ph/tamss/weather/bulletin/TCB%2315_opong.pdf", "date": "2025-09-26", "time": "03:32"},  # Sept 26
        {"number": 20, "url": "https://pubfiles.pagasa.dost.gov.ph/tamss/weather/bulletin/TCB%2320_opong.pdf", "date": "2025-09-26", "time": "12:01"},  # Sept 26
    ]
}

def download_bulletin(typhoon_name, bulletin_info, output_dir):
    """Download a single bulletin PDF"""
    url = bulletin_info["url"]
    number = bulletin_info["number"]
    
    filename = f"TCB_{number}_{typhoon_name}.pdf"
    filepath = output_dir / filename
    
    # Skip if already downloaded
    if filepath.exists():
        print(f"✓ Already downloaded: {filename}")
        return filepath
    
    print(f"📥 Downloading {filename}...")
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        print(f"✓ Downloaded {filename} ({len(response.content)} bytes)")
        return filepath
    
    except Exception as e:
        print(f"❌ Error downloading {filename}: {e}")
        return None

def main():
    # Create output directory
    output_dir = Path(__file__).parent / "output" / "pagasa_bulletins"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 70)
    print("PAGASA Bulletin Downloader")
    print("=" * 70)
    print(f"Output directory: {output_dir}\n")
    
    downloaded = []
    
    # Download bulletins for each typhoon
    for typhoon_name, bulletins in BULLETINS_TO_DOWNLOAD.items():
        print(f"\n🌀 {typhoon_name.upper()}")
        print("-" * 70)
        
        for bulletin_info in bulletins:
            filepath = download_bulletin(typhoon_name, bulletin_info, output_dir)
            if filepath:
                downloaded.append({
                    "typhoon": typhoon_name,
                    "number": bulletin_info["number"],
                    "date": bulletin_info["date"],
                    "time": bulletin_info["time"],
                    "filepath": str(filepath),
                    "url": bulletin_info["url"]
                })
    
    # Save download log
    log_file = output_dir / "download_log.json"
    with open(log_file, 'w') as f:
        json.dump({
            "downloaded_at": datetime.now().isoformat(),
            "total_bulletins": len(downloaded),
            "bulletins": downloaded
        }, f, indent=2)
    
    print("\n" + "=" * 70)
    print(f"✅ Downloaded {len(downloaded)} bulletins")
    print(f"📋 Log saved to: {log_file}")
    print("=" * 70)
    print("\n⚠️  NEXT STEP: Manually read PDFs to extract TCWS levels for Metro Manila")
    print("    Look for phrases like:")
    print("    - 'Signal No. 3' or 'TCWS #3'")
    print("    - 'Metro Manila' or 'National Capital Region'")
    print("    - Area affected lists")

if __name__ == "__main__":
    main()
