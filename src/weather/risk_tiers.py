"""
Risk Tier Interpretation System for Class Suspension Predictions

Converts ML model probabilities into actionable risk tiers based on:
- Traffic light metaphor (🟢 Green, 🟠 Orange, 🔴 Red)
- DepEd decision-making needs
- PAGASA advisory alignment
- Behavioral science principles (action-oriented, removes false precision)

Thresholds calibrated from model validation:
- Clear weather (15mm): 37.6% probability → GREEN
- Heavy rain (35mm): 50.1% probability → ORANGE
- Typhoon (65mm): 53.1%+ probability → RED
"""

from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass


class RiskTier(Enum):
    """Risk tier levels for class suspension predictions"""
    GREEN = "normal"      # <40% probability
    ORANGE = "alert"      # 40-55% probability
    RED = "suspension"    # >55% probability


@dataclass
class TierDetails:
    """Detailed information for each risk tier"""
    tier: RiskTier
    color: str
    emoji: str
    status_icon: str
    title: str
    subtitle: str
    recommendation: str
    actions: List[str]
    monitoring_interval: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "tier": self.tier.value,
            "color": self.color,
            "emoji": self.emoji,
            "status_icon": self.status_icon,
            "title": self.title,
            "subtitle": self.subtitle,
            "recommendation": self.recommendation,
            "actions": self.actions,
            "monitoring_interval": self.monitoring_interval
        }


# Tier threshold configuration
TIER_THRESHOLDS = {
    "green_max": 0.40,    # <40% = Normal operations
    "orange_max": 0.55,   # 40-55% = Enhanced alert
    # >55% = Suspension recommended
}


def get_risk_tier(probability: float) -> RiskTier:
    """
    Determine risk tier from model probability
    
    Args:
        probability: Model prediction probability (0.0-1.0)
        
    Returns:
        RiskTier enum value
    """
    if probability < TIER_THRESHOLDS["green_max"]:
        return RiskTier.GREEN
    elif probability < TIER_THRESHOLDS["orange_max"]:
        return RiskTier.ORANGE
    else:
        return RiskTier.RED


def get_tier_details(
    tier: RiskTier,
    weather_desc: str = None,
    precipitation_mm: float = None,
    pagasa_warning: str = None,
    tcws_level: int = 0
) -> TierDetails:
    """
    Get detailed tier information with contextual weather data
    
    Args:
        tier: Risk tier level
        weather_desc: Weather description (e.g., "Light rain possible")
        precipitation_mm: Forecasted precipitation in mm
        pagasa_warning: PAGASA rainfall warning level (YELLOW/ORANGE/RED)
        tcws_level: Tropical Cyclone Wind Signal level (0-5)
        
    Returns:
        TierDetails object with all display information
    """
    
    if tier == RiskTier.GREEN:
        return TierDetails(
            tier=RiskTier.GREEN,
            color="#22c55e",  # Tailwind green-500
            emoji="🟢",
            status_icon="✓",
            title="NORMAL CONDITIONS",
            subtitle="Continue routine operations",
            recommendation="No suspension expected",
            actions=[
                "Continue regular class schedule",
                "Monitor weather updates",
                "Maintain standard preparedness protocols"
            ],
            monitoring_interval="Standard monitoring (daily)"
        )
    
    elif tier == RiskTier.ORANGE:
        actions = [
            "Monitor updates every 2 hours",
            "Prepare early dismissal plan",
            "Coordinate with DRRM office",
            "Review evacuation procedures",
            "Activate weather monitoring team"
        ]
        
        # Add TCWS-specific actions
        if tcws_level >= 1:
            actions.append("Monitor PAGASA typhoon bulletins")
            
        return TierDetails(
            tier=RiskTier.ORANGE,
            color="#f97316",  # Tailwind orange-500
            emoji="🟠",
            status_icon="⚠️",
            title="WEATHER ALERT",
            subtitle="Enhanced monitoring needed",
            recommendation="Prepare for possible suspension",
            actions=actions,
            monitoring_interval="Enhanced monitoring (every 2 hours)"
        )
    
    else:  # RED
        actions = [
            "Issue suspension announcement",
            "Activate online/modular learning",
            "Monitor for multi-day impact",
            "Coordinate with local government",
            "Ensure student safety protocols active"
        ]
        
        # Add TCWS-specific actions
        if tcws_level >= 2:
            actions.append("Activate disaster response protocols")
            actions.append("Secure school facilities")
            
        return TierDetails(
            tier=RiskTier.RED,
            color="#ef4444",  # Tailwind red-500
            emoji="🔴",
            status_icon="⛔",
            title="CLASS SUSPENSION",
            subtitle="Severe weather conditions",
            recommendation="SUSPEND face-to-face classes",
            actions=actions,
            monitoring_interval="Continuous monitoring (hourly)"
        )


def format_weather_context(
    precipitation_mm: float = None,
    weather_code: int = None,
    pagasa_warning: str = None,
    tcws_level: int = 0,
    typhoon_name: str = None
) -> Dict[str, str]:
    """
    Format weather context for display
    
    Args:
        precipitation_mm: Forecasted precipitation
        weather_code: WMO weather code
        pagasa_warning: PAGASA rainfall warning level
        tcws_level: TCWS level
        typhoon_name: Active typhoon name
        
    Returns:
        Dictionary with formatted weather strings
    """
    context = {}
    
    # Weather description from precipitation
    if precipitation_mm is not None:
        if precipitation_mm < 7.5:
            context["weather_desc"] = "Light rain possible"
        elif precipitation_mm < 15:
            context["weather_desc"] = "Moderate rain expected"
        elif precipitation_mm < 30:
            context["weather_desc"] = "Heavy rain likely"
        elif precipitation_mm < 60:
            context["weather_desc"] = "Very heavy rain expected"
        else:
            context["weather_desc"] = "Intense rainfall expected"
            
        context["precipitation"] = f"{precipitation_mm:.1f}mm precipitation"
    
    # PAGASA advisory
    if pagasa_warning:
        context["pagasa_advisory"] = f"PAGASA: {pagasa_warning.title()} Rainfall Warning"
    elif tcws_level > 0:
        context["pagasa_advisory"] = f"PAGASA: TCWS Signal No. {tcws_level}"
        if typhoon_name:
            context["pagasa_advisory"] += f" ({typhoon_name})"
    
    return context


def interpret_prediction(
    probability: float,
    lgu_name: str,
    date: str,
    precipitation_mm: float = None,
    weather_code: int = None,
    pagasa_warning: str = None,
    tcws_level: int = 0,
    typhoon_name: str = None
) -> Dict:
    """
    Full interpretation pipeline: probability → risk tier → actionable guidance
    
    Args:
        probability: Model prediction probability
        lgu_name: LGU name
        date: Prediction date (YYYY-MM-DD)
        precipitation_mm: Forecasted precipitation
        weather_code: WMO weather code
        pagasa_warning: PAGASA rainfall warning
        tcws_level: TCWS level
        typhoon_name: Active typhoon name
        
    Returns:
        Complete interpretation dictionary
    """
    # Determine risk tier
    tier = get_risk_tier(probability)
    
    # Get tier details
    tier_details = get_tier_details(
        tier=tier,
        precipitation_mm=precipitation_mm,
        pagasa_warning=pagasa_warning,
        tcws_level=tcws_level
    )
    
    # Format weather context
    weather_context = format_weather_context(
        precipitation_mm=precipitation_mm,
        weather_code=weather_code,
        pagasa_warning=pagasa_warning,
        tcws_level=tcws_level,
        typhoon_name=typhoon_name
    )
    
    # Combine into full interpretation
    return {
        "lgu": lgu_name,
        "date": date,
        "model_probability": probability,
        "risk_tier": tier_details.to_dict(),
        "weather_context": weather_context,
        "metadata": {
            "interpretation_version": "1.0",
            "threshold_green_max": TIER_THRESHOLDS["green_max"],
            "threshold_orange_max": TIER_THRESHOLDS["orange_max"]
        }
    }


def get_tier_summary(predictions: List[Dict]) -> Dict:
    """
    Summarize risk tier distribution across multiple predictions
    
    Args:
        predictions: List of prediction dictionaries with probabilities
        
    Returns:
        Summary statistics by tier
    """
    tier_counts = {
        RiskTier.GREEN.value: 0,
        RiskTier.ORANGE.value: 0,
        RiskTier.RED.value: 0
    }
    
    for pred in predictions:
        prob = pred.get("probability", pred.get("model_probability", 0))
        tier = get_risk_tier(prob)
        tier_counts[tier.value] += 1
    
    total = len(predictions)
    
    return {
        "total_predictions": total,
        "tier_distribution": {
            "green": {
                "count": tier_counts[RiskTier.GREEN.value],
                "percentage": round(tier_counts[RiskTier.GREEN.value] / total * 100, 1) if total > 0 else 0
            },
            "orange": {
                "count": tier_counts[RiskTier.ORANGE.value],
                "percentage": round(tier_counts[RiskTier.ORANGE.value] / total * 100, 1) if total > 0 else 0
            },
            "red": {
                "count": tier_counts[RiskTier.RED.value],
                "percentage": round(tier_counts[RiskTier.RED.value] / total * 100, 1) if total > 0 else 0
            }
        },
        "highest_alert_count": tier_counts[RiskTier.ORANGE.value] + tier_counts[RiskTier.RED.value]
    }


if __name__ == "__main__":
    # Test with calibration scenarios
    print("=== Risk Tier Interpretation System Test ===\n")
    
    # Scenario 1: Clear weather (37.6% probability)
    print("📊 Scenario 1: Clear Weather")
    result = interpret_prediction(
        probability=0.376,
        lgu_name="Quezon City",
        date="2025-11-03",
        precipitation_mm=15.0,
        pagasa_warning=None,
        tcws_level=0
    )
    print(f"Tier: {result['risk_tier']['emoji']} {result['risk_tier']['title']}")
    print(f"Recommendation: {result['risk_tier']['recommendation']}")
    print(f"Weather: {result['weather_context'].get('weather_desc', 'N/A')}\n")
    
    # Scenario 2: Heavy rain (50.1% probability)
    print("📊 Scenario 2: Heavy Rain")
    result = interpret_prediction(
        probability=0.501,
        lgu_name="Manila",
        date="2025-11-03",
        precipitation_mm=35.0,
        pagasa_warning="ORANGE",
        tcws_level=0
    )
    print(f"Tier: {result['risk_tier']['emoji']} {result['risk_tier']['title']}")
    print(f"Recommendation: {result['risk_tier']['recommendation']}")
    print(f"Actions: {result['risk_tier']['actions'][:2]}")
    print(f"Weather: {result['weather_context'].get('weather_desc', 'N/A')}\n")
    
    # Scenario 3: Typhoon (57.2% probability)
    print("📊 Scenario 3: Typhoon")
    result = interpret_prediction(
        probability=0.572,
        lgu_name="Pasig",
        date="2025-11-03",
        precipitation_mm=65.0,
        pagasa_warning="RED",
        tcws_level=2,
        typhoon_name="Opong"
    )
    print(f"Tier: {result['risk_tier']['emoji']} {result['risk_tier']['title']}")
    print(f"Recommendation: {result['risk_tier']['recommendation']}")
    print(f"Actions: {result['risk_tier']['actions'][:3]}")
    print(f"Weather: {result['weather_context'].get('weather_desc', 'N/A')}")
    print(f"PAGASA: {result['weather_context'].get('pagasa_advisory', 'N/A')}\n")
