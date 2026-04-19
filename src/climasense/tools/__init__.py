"""ClimaSense tool definitions for Gemma 4 native function calling."""

from climasense.tools.weather import get_weather_forecast, get_historical_weather
from climasense.tools.crop_disease import diagnose_crop_disease, get_treatment_recommendation
from climasense.tools.market import get_commodity_prices, get_price_forecast
from climasense.tools.soil import get_soil_analysis
from climasense.tools.advisory import get_planting_advisory, get_climate_risk_alert
from climasense.tools.satellite import get_vegetation_health
from climasense.tools.postharvest import get_postharvest_risk

TOOL_REGISTRY = {
    "get_weather_forecast": get_weather_forecast,
    "get_historical_weather": get_historical_weather,
    "diagnose_crop_disease": diagnose_crop_disease,
    "get_treatment_recommendation": get_treatment_recommendation,
    "get_commodity_prices": get_commodity_prices,
    "get_price_forecast": get_price_forecast,
    "get_soil_analysis": get_soil_analysis,
    "get_planting_advisory": get_planting_advisory,
    "get_climate_risk_alert": get_climate_risk_alert,
    "get_vegetation_health": get_vegetation_health,
    "get_postharvest_risk": get_postharvest_risk,
}

ALL_TOOLS = list(TOOL_REGISTRY.values())
