"""
PAGASA Integration Demo
Shows how to use PAGASA data in your suspension prediction system
"""

from src.weather.pagasa_checker import PAGASAChecker
import json


def main():
    print("=" * 70)
    print("PAGASA TYPHOON CHECKER - INTEGRATION DEMO")
    print("=" * 70)
    print()
    
    # Initialize checker
    checker = PAGASAChecker()
    
    # Get full status
    print("📡 Fetching latest PAGASA data...")
    status = checker.check_typhoon_status()
    
    print("\n" + "=" * 70)
    print("TYPHOON STATUS")
    print("=" * 70)
    
    if status.get('hasActiveTyphoon'):
        print(f"🌀 Active Typhoon: {status['typhoonName']}")
        print(f"📋 Bulletin #{status['bulletinNumber']}")
        print(f"📅 Issued: {status['bulletinAge']}")
        print(f"📊 Status: {status['typhoonStatus']}")
        
        print(f"\n📍 Metro Manila Impact:")
        if status['metroManilaAffected']:
            print(f"   ⚠️  AFFECTED - TCWS Level {status['tcwsLevel']}")
            
            # Show affected areas
            mm_areas = [a for a in status.get('affectedAreas', []) 
                       if 'metro manila' in a.get('name', '').lower()]
            for area in mm_areas:
                print(f"   • {area['name']}: Signal #{area['signal']}")
        else:
            print(f"   ✅ Not affected (TCWS Level {status['tcwsLevel']})")
    else:
        print("✅ No active typhoon affecting the Philippines")
    
    # Rainfall warning
    print("\n" + "=" * 70)
    print("RAINFALL WARNING")
    print("=" * 70)
    
    rainfall = status.get('rainfallWarning', {})
    if rainfall.get('hasActiveWarning'):
        print(f"⚠️  Active Warning: {rainfall['warningLevel']}")
        print(f"📍 Metro Manila Status: {rainfall['metroManilaStatus']}")
        
        if rainfall.get('warningNumber'):
            print(f"📋 Warning #{rainfall['warningNumber']}")
        
        if rainfall.get('hazards'):
            print(f"🚨 Hazards: {', '.join(rainfall['hazards'])}")
    else:
        print(f"✅ No rainfall warning (Status: {rainfall['metroManilaStatus']})")
    
    # API demonstration
    print("\n" + "=" * 70)
    print("API METHODS DEMONSTRATION")
    print("=" * 70)
    
    print("\n1️⃣ get_tcws_level_for_metro_manila()")
    tcws = checker.get_tcws_level_for_metro_manila()
    print(f"   Result: {tcws}")
    print(f"   Type: {type(tcws).__name__}")
    
    print("\n2️⃣ is_metro_manila_affected()")
    affected = checker.is_metro_manila_affected()
    print(f"   Result: {affected}")
    print(f"   Type: {type(affected).__name__}")
    
    print("\n3️⃣ get_current_typhoon_info()")
    typhoon = checker.get_current_typhoon_info()
    if typhoon:
        print(f"   Name: {typhoon['name']}")
        print(f"   Metro Manila TCWS: Level {typhoon['metro_manila_tcws']}")
        print(f"   Bulletin: #{typhoon['bulletin_number']}")
    else:
        print("   Result: None (no active typhoon)")
    
    print("\n4️⃣ get_rainfall_warning()")
    rainfall_obj = checker.get_rainfall_warning()
    if rainfall_obj:
        print(f"   Level: {rainfall_obj['warningLevel']}")
        print(f"   Metro Manila: {rainfall_obj['metroManilaStatus']}")
    else:
        print("   Result: None (no active warning)")
    
    # ML Feature Engineering Example
    print("\n" + "=" * 70)
    print("ML FEATURE ENGINEERING EXAMPLE")
    print("=" * 70)
    
    features = {
        'tcws_level': tcws,
        'metro_manila_affected': int(affected),
        'has_rainfall_warning': int(rainfall_obj is not None),
        'rainfall_severity': 0 if not rainfall_obj else 
                           {'RED': 3, 'ORANGE': 2, 'YELLOW': 1}.get(
                               rainfall_obj.get('warningLevel'), 0
                           )
    }
    
    print("\nFeatures for ML model:")
    for key, value in features.items():
        print(f"   {key}: {value}")
    
    # Suspension decision logic example
    print("\n" + "=" * 70)
    print("SUSPENSION DECISION LOGIC EXAMPLE")
    print("=" * 70)
    
    suspension_score = 0
    
    if features['tcws_level'] >= 3:
        suspension_score += 50
        print("   • TCWS ≥3: +50 points")
    elif features['tcws_level'] >= 2:
        suspension_score += 30
        print("   • TCWS ≥2: +30 points")
    elif features['tcws_level'] >= 1:
        suspension_score += 15
        print("   • TCWS ≥1: +15 points")
    
    if features['rainfall_severity'] == 3:
        suspension_score += 40
        print("   • RED rainfall warning: +40 points")
    elif features['rainfall_severity'] == 2:
        suspension_score += 25
        print("   • ORANGE rainfall warning: +25 points")
    elif features['rainfall_severity'] == 1:
        suspension_score += 10
        print("   • YELLOW rainfall warning: +10 points")
    
    print(f"\n🎯 Total Suspension Score: {suspension_score}/100")
    
    if suspension_score >= 70:
        print("   ⛔ HIGH LIKELIHOOD - Suspension recommended")
    elif suspension_score >= 40:
        print("   ⚠️  MODERATE LIKELIHOOD - Monitor situation")
    elif suspension_score >= 20:
        print("   ⚡ LOW LIKELIHOOD - Be prepared")
    else:
        print("   ✅ MINIMAL LIKELIHOOD - Normal operations")
    
    print("\n" + "=" * 70)
    print("FULL JSON OUTPUT")
    print("=" * 70)
    print(json.dumps(status, indent=2))
    
    print("\n" + "=" * 70)
    print("✅ Demo complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
