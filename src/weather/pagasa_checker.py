"""
PAGASA Typhoon Checker - Python Wrapper
Bridges Python code to Node.js PAGASA parser
"""

import subprocess
import json
import os
from pathlib import Path
from typing import Dict, Optional, Any
from datetime import datetime


class PAGASAChecker:
    """
    Python wrapper for Node.js PAGASA parser.
    Spawns Node.js subprocess to fetch and parse typhoon data.
    """
    
    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize PAGASA checker.
        
        Args:
            project_root: Path to project root. If None, auto-detects from file location.
        """
        if project_root is None:
            # Auto-detect: go up 3 levels from this file
            # src/weather/pagasa_checker.py → new-capstone/
            self.project_root = Path(__file__).parent.parent.parent
        else:
            self.project_root = Path(project_root)
        
        self.nodejs_dir = self.project_root / "nodejs-pagasa"
        self.nodejs_script = self.nodejs_dir / "pagasa_parser.js"
        self.output_file = self.project_root / "pagasa_status.json"
        
        # Verify Node.js script exists
        if not self.nodejs_script.exists():
            raise FileNotFoundError(
                f"Node.js parser not found at: {self.nodejs_script}\n"
                "Please run: cd nodejs-pagasa && npm install"
            )
    
    def check_typhoon_status(self, timeout: int = 30) -> Dict[str, Any]:
        """
        Check current typhoon status by running Node.js parser.
        
        Args:
            timeout: Timeout in seconds (default: 30)
        
        Returns:
            Dictionary containing typhoon status data
        
        Raises:
            subprocess.TimeoutExpired: If Node.js script takes too long
            subprocess.CalledProcessError: If Node.js script fails
            json.JSONDecodeError: If output file is invalid JSON
        """
        try:
            print("🌀 Fetching typhoon status from PAGASA...")
            
            # Run Node.js parser
            result = subprocess.run(
                ['node', str(self.nodejs_script)],
                cwd=str(self.nodejs_dir),
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding='utf-8',
                errors='replace'
            )
            
            # Check for errors
            if result.returncode != 0:
                error_msg = result.stderr if result.stderr else "Unknown error"
                print(f"❌ Node.js parser error: {error_msg}")
                return self._create_error_response(error_msg)
            
            # Read output file
            if not self.output_file.exists():
                return self._create_error_response("Output file not created")
            
            with open(self.output_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print(f"✅ Status retrieved: {data.get('message', 'Success')}")
            return data
            
        except subprocess.TimeoutExpired:
            print(f"❌ Timeout: Node.js script took longer than {timeout}s")
            return self._create_error_response(f"Timeout after {timeout}s")
        
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in output file: {e}")
            return self._create_error_response(f"Invalid JSON: {e}")
        
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return self._create_error_response(str(e))
    
    def get_tcws_level_for_metro_manila(self) -> int:
        """
        Get TCWS (Tropical Cyclone Wind Signal) level for Metro Manila.
        
        Returns:
            int: TCWS level (0-5), or 0 if no active signal
        """
        status = self.check_typhoon_status()
        return status.get('tcwsLevel', 0)
    
    def is_metro_manila_affected(self) -> bool:
        """
        Check if Metro Manila is currently affected by a typhoon.
        
        Returns:
            bool: True if Metro Manila has active TCWS, False otherwise
        """
        status = self.check_typhoon_status()
        return status.get('metroManilaAffected', False)
    
    def get_current_typhoon_info(self) -> Optional[Dict[str, Any]]:
        """
        Get information about the current active typhoon.
        
        Returns:
            Dictionary with typhoon info, or None if no active typhoon
        """
        status = self.check_typhoon_status()
        
        if not status.get('hasActiveTyphoon', False):
            return None
        
        return {
            'name': status.get('typhoonName'),
            'bulletin_number': status.get('bulletinNumber'),
            'bulletin_date': status.get('bulletinDate'),
            'bulletin_url': status.get('bulletinUrl'),
            'bulletin_age': status.get('bulletinAge'),
            'status': status.get('typhoonStatus'),
            'metro_manila_tcws': status.get('tcwsLevel', 0),
            'metro_manila_affected': status.get('metroManilaAffected', False),
            'affected_areas': status.get('affectedAreas', []),
            'last_checked': status.get('lastChecked')
        }
    
    def get_rainfall_warning(self) -> Optional[Dict[str, Any]]:
        """
        Get current rainfall warning status.
        
        Returns:
            Dictionary with rainfall warning info, or None if no warning
        """
        status = self.check_typhoon_status()
        rainfall_data = status.get('rainfallWarning', {})
        
        if not rainfall_data.get('hasActiveWarning', False):
            return None
        
        return rainfall_data
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create error response dictionary."""
        return {
            'hasActiveTyphoon': False,
            'typhoonStatus': 'ERROR',
            'metroManilaAffected': False,
            'tcwsLevel': 0,
            'affectedAreas': [],
            'rainfallWarning': {'hasActiveWarning': False},
            'lastChecked': datetime.utcnow().isoformat() + 'Z',
            'error': error_message,
            'message': f'Error checking typhoon status: {error_message}'
        }


def main():
    """Test the PAGASA checker."""
    checker = PAGASAChecker()
    
    print("=" * 60)
    print("PAGASA TYPHOON CHECKER - PYTHON WRAPPER TEST")
    print("=" * 60)
    
    # Check full status
    status = checker.check_typhoon_status()
    
    print(f"\nHas Active Typhoon: {status.get('hasActiveTyphoon')}")
    
    if status.get('hasActiveTyphoon'):
        typhoon = checker.get_current_typhoon_info()
        print(f"Typhoon Name: {typhoon['name']}")
        print(f"Bulletin #{typhoon['bulletin_number']}")
        print(f"Metro Manila TCWS: Level {typhoon['metro_manila_tcws']}")
        print(f"Metro Manila Affected: {typhoon['metro_manila_affected']}")
    
    # Check rainfall warning
    rainfall = checker.get_rainfall_warning()
    if rainfall:
        print(f"\n⚠️  Rainfall Warning: {rainfall.get('warningLevel')} ({rainfall.get('metroManilaStatus')})")
    else:
        print("\n✅ No rainfall warning")
    
    print(f"\nLast Checked: {status.get('lastChecked')}")
    print("=" * 60)


if __name__ == "__main__":
    main()
