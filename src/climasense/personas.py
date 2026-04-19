"""Named beneficiary personas for ClimaSense demos and evaluation.

Every winning Gemma hackathon entry featured a named human beneficiary.
These personas ground the technology in real human impact.
"""

# Amina — Primary demo persona
AMINA = {
    "name": "Amina Otieno",
    "age": 34,
    "location": {
        "village": "Kadongo",
        "county": "Kisumu County",
        "country": "Kenya",
        "coordinates": (-0.0917, 34.7680),  # Near Kisumu, Lake Victoria basin
    },
    "language": "Swahili",  # Primary; also speaks Luo and some English
    "family": "Mother of 3 children (ages 4, 8, 11)",
    "farm": {
        "size_hectares": 0.8,  # ~2 acres — typical smallholder
        "crops": ["maize", "tomatoes", "kale (sukuma wiki)", "beans"],
        "livestock": "3 chickens, 1 dairy goat",
        "irrigation": "Rain-fed only (no irrigation)",
        "soil_type": "Clay-loam (Lake Victoria basin)",
    },
    "challenges": [
        "Loses ~30% of tomato crop annually to late blight and bacterial spot",
        "No access to soil testing — last test was 4 years ago via NGO",
        "Nearest agricultural extension officer is 22 km away in Kisumu town",
        "Gets weather info from radio, often too late for preventive action",
        "Sells at local market with no price information — middlemen set prices",
        "Lost entire maize crop in 2024 long rains due to unexpected flooding",
    ],
    "phone": "Basic Android smartphone (Tecno Spark 8, shared with husband)",
    "connectivity": "Intermittent 3G; no WiFi; ~2 hours of good signal per day",
    "income": "~KES 15,000/month (~$115 USD) from farm + occasional casual labor",
    "quote": (
        "I know when the rains should come, but now the weather surprises us. "
        "Last season I planted maize too early and lost everything to flooding. "
        "If I could know even 3 days ahead, I could protect my crops."
    ),
}

# Demo scenarios built around Amina's actual daily problems
DEMO_SCENARIOS = [
    {
        "id": "morning_check",
        "title": "Morning Weather Check",
        "description": "Amina checks weather before deciding whether to spray her tomatoes",
        "query": "Hali ya hewa ikoje wiki hii? Nina nyanya zangu zinahitaji dawa.",
        "query_english": "How is the weather this week? My tomatoes need spraying.",
        "location": AMINA["location"]["coordinates"],
        "language": "sw",
        "lang_code": "sw",
        "expected_tools": ["get_weather_forecast"],
        "context": (
            "Amina wakes at 5:30am. Her tomatoes have early signs of leaf curl. "
            "She needs to know if it will rain (spraying in rain wastes pesticide). "
            "This is a daily decision that costs her money if she gets it wrong."
        ),
    },
    {
        "id": "disease_diagnosis",
        "title": "Tomato Disease Emergency",
        "description": "Amina photographs brown spots spreading on her tomato leaves",
        "query": "Majani ya nyanya yangu yana madoa ya kahawia na pete. Ni ugonjwa gani?",
        "query_english": "My tomato leaves have brown spots with rings. What disease is this?",
        "location": AMINA["location"]["coordinates"],
        "language": "sw",
        "lang_code": "sw",
        "expected_tools": ["diagnose_crop_disease", "get_treatment_recommendation", "get_weather_forecast"],
        "context": (
            "It rained heavily 3 days ago. Now Amina sees brown spots with "
            "concentric rings spreading across her tomato patch. This is likely "
            "early blight (Alternaria solani), which thrives in warm, wet conditions. "
            "She lost 30% of her crop to this last season."
        ),
    },
    {
        "id": "planting_decision",
        "title": "Maize Planting Timing",
        "description": "Amina decides when to plant maize for the long rains season",
        "query": (
            "Nataka kupanda mahindi msimu huu. Ni wakati gani mzuri? "
            "Bei ya mahindi iko vipi sasa?"
        ),
        "query_english": (
            "I want to plant maize this season. When is the best time? "
            "How are maize prices right now?"
        ),
        "location": AMINA["location"]["coordinates"],
        "language": "sw",
        "lang_code": "sw",
        "expected_tools": ["get_planting_advisory", "get_commodity_prices", "get_soil_analysis"],
        "context": (
            "After losing her entire maize crop to flooding in 2024, Amina is "
            "cautious about planting timing. She wants data-driven advice, not "
            "just tradition. The long rains typically start mid-March in Kisumu, "
            "but climate change has made this unpredictable."
        ),
    },
    {
        "id": "market_timing",
        "title": "Tomato Harvest Market Decision",
        "description": "Amina's tomatoes are ripe — sell now at local market or wait?",
        "query": "Nyanya zangu zimeiva. Niuze sasa au ningojee? Bei iko vipi?",
        "query_english": "My tomatoes are ripe. Should I sell now or wait? What are prices like?",
        "location": AMINA["location"]["coordinates"],
        "language": "sw",
        "lang_code": "sw",
        "expected_tools": ["get_commodity_prices", "get_price_forecast", "get_weather_forecast"],
        "context": (
            "Amina has ~200 kg of ripe tomatoes. Middlemen at the farm gate "
            "offer KES 20/kg, but Kisumu market price is KES 50/kg. She needs "
            "to know if prices will go up or down, and whether weather will "
            "cause spoilage if she waits."
        ),
    },
    {
        "id": "flood_alert",
        "title": "Flood Risk Early Warning",
        "description": "Heavy rains forecast — Amina needs to protect her crops",
        "query": (
            "Nimesikia mvua kubwa inakuja. Mazao yangu yako hatarini? "
            "Nifanye nini?"
        ),
        "query_english": (
            "I heard heavy rains are coming. Are my crops at risk? "
            "What should I do?"
        ),
        "location": AMINA["location"]["coordinates"],
        "language": "sw",
        "lang_code": "sw",
        "expected_tools": ["get_weather_forecast", "get_climate_risk_alert"],
        "context": (
            "Amina's farm is in the Lake Victoria basin, prone to flooding "
            "during intense long rains. In 2024, she lost everything because "
            "she had no early warning. Now she's heard rumors of heavy rain "
            "and wants to act preemptively."
        ),
    },
]


def get_persona(name: str = "amina") -> dict:
    """Get a named persona."""
    personas = {"amina": AMINA}
    return personas.get(name.lower(), AMINA)


def get_demo_scenarios() -> list[dict]:
    """Get all demo scenarios for the primary persona."""
    return DEMO_SCENARIOS


def get_scenario(scenario_id: str) -> dict | None:
    """Get a specific demo scenario by ID."""
    for s in DEMO_SCENARIOS:
        if s["id"] == scenario_id:
            return s
    return None
