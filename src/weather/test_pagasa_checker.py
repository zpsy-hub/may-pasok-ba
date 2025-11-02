"""
Test PAGASA Checker - Python Wrapper
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from weather.pagasa_checker import PAGASAChecker


def test_basic_functionality():
    """Test basic PAGASA checker functionality."""
    print("🧪 Testing PAGASA Checker Python Wrapper\n")
    
    checker = PAGASAChecker()
    
    # Test 1: Check typhoon status
    print("Test 1: Check typhoon status")
    status = checker.check_typhoon_status()
    assert isinstance(status, dict), "Status should be a dictionary"
    assert 'hasActiveTyphoon' in status, "Missing hasActiveTyphoon field"
    assert 'metroManilaAffected' in status, "Missing metroManilaAffected field"
    assert 'tcwsLevel' in status, "Missing tcwsLevel field"
    print("✅ Status check passed\n")
    
    # Test 2: Get TCWS level
    print("Test 2: Get TCWS level for Metro Manila")
    tcws = checker.get_tcws_level_for_metro_manila()
    assert isinstance(tcws, int), "TCWS should be an integer"
    assert 0 <= tcws <= 5, f"TCWS {tcws} out of range (0-5)"
    print(f"✅ TCWS Level: {tcws}\n")
    
    # Test 3: Check if Metro Manila affected
    print("Test 3: Check if Metro Manila affected")
    affected = checker.is_metro_manila_affected()
    assert isinstance(affected, bool), "Affected status should be boolean"
    print(f"✅ Metro Manila Affected: {affected}\n")
    
    # Test 4: Get typhoon info
    print("Test 4: Get current typhoon info")
    typhoon = checker.get_current_typhoon_info()
    if typhoon:
        assert 'name' in typhoon, "Missing typhoon name"
        assert 'metro_manila_tcws' in typhoon, "Missing Metro Manila TCWS"
        print(f"✅ Typhoon Info: {typhoon['name']}")
    else:
        print("ℹ️  No active typhoon")
    print()
    
    # Test 5: Get rainfall warning
    print("Test 5: Get rainfall warning")
    rainfall = checker.get_rainfall_warning()
    if rainfall:
        assert 'warningLevel' in rainfall, "Missing warning level"
        print(f"✅ Rainfall Warning: {rainfall['warningLevel']}")
    else:
        print("ℹ️  No rainfall warning")
    print()
    
    # Print summary
    print("=" * 60)
    print("FULL STATUS RESPONSE:")
    print("=" * 60)
    import json
    print(json.dumps(status, indent=2))
    print("=" * 60)
    print("✅ All Python wrapper tests passed!")


if __name__ == "__main__":
    try:
        test_basic_functionality()
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
