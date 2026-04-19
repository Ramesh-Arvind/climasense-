"""Evaluation benchmark for ClimaSense agent accuracy.

Tests the agent against 20 curated agricultural scenarios:
- 5 crops (maize, tomato, cassava, rice, beans)
- 4 regions (East Africa, West Africa, South Asia, Southeast Asia)
- English + Swahili queries

Measures: tool selection F1, keyword coverage, actionable advice rate,
response length, and composite scoring weighted by difficulty.
"""

import json
import logging
import os
import time
from pathlib import Path

from tqdm import tqdm

logger = logging.getLogger(__name__)

CHECKPOINT_PATH = "logs/checkpoint_eval.json"

# 4 evaluation regions with coordinates
REGIONS = {
    "east_africa": {"name": "Kisumu, Kenya", "lat": -0.0917, "lon": 34.7680, "country": "kenya"},
    "west_africa": {"name": "Jos, Nigeria", "lat": 9.0820, "lon": 8.6753, "country": "nigeria"},
    "south_asia": {"name": "Dhaka, Bangladesh", "lat": 23.8103, "lon": 90.4125, "country": "bangladesh"},
    "southeast_asia": {"name": "Manila, Philippines", "lat": 14.5995, "lon": 120.9842, "country": "philippines"},
}

# Expanded evaluation scenarios — 20 total
EVAL_SCENARIOS = [
    # === MAIZE scenarios (4 regions) ===
    {
        "id": "maize_ea_planting",
        "query": "When should I plant maize this season? Check weather and soil.",
        "location": (REGIONS["east_africa"]["lat"], REGIONS["east_africa"]["lon"]),
        "expected_tools": ["get_weather_forecast", "get_planting_advisory", "get_soil_analysis"],
        "expected_keywords": ["maize", "plant", "rain", "soil"],
        "category": "planting",
        "difficulty": 3,
        "crop": "maize",
        "region": "east_africa",
    },
    {
        "id": "maize_wa_prices",
        "query": "What is the current price of maize? Should I sell now or wait?",
        "location": (REGIONS["west_africa"]["lat"], REGIONS["west_africa"]["lon"]),
        "expected_tools": ["get_commodity_prices", "get_price_forecast"],
        "expected_keywords": ["price", "maize", "sell"],
        "category": "market_advisory",
        "difficulty": 2,
        "crop": "maize",
        "region": "west_africa",
    },
    {
        "id": "maize_ea_risk_sw",
        "query": "Mazao yangu ya mahindi yako hatarini? Mvua haikunyesha wiki mbili.",
        "location": (REGIONS["east_africa"]["lat"], REGIONS["east_africa"]["lon"]),
        "expected_tools": ["get_weather_forecast", "get_climate_risk_alert"],
        "expected_keywords": ["drought", "risk", "water", "maize"],
        "category": "risk_assessment",
        "difficulty": 3,
        "crop": "maize",
        "region": "east_africa",
        "language": "sw",
    },
    {
        "id": "maize_sa_disease",
        "query": "My maize has yellow streaks along the leaf veins and the plants are stunted.",
        "location": (REGIONS["south_asia"]["lat"], REGIONS["south_asia"]["lon"]),
        "expected_tools": ["diagnose_crop_disease"],
        "expected_keywords": ["maize", "virus", "streak"],
        "category": "disease_diagnosis",
        "difficulty": 2,
        "crop": "maize",
        "region": "south_asia",
    },
    # === TOMATO scenarios ===
    {
        "id": "tomato_ea_disease",
        "query": "My tomato leaves have dark brown spots with concentric rings. What is this?",
        "location": (REGIONS["east_africa"]["lat"], REGIONS["east_africa"]["lon"]),
        "expected_tools": ["diagnose_crop_disease", "get_treatment_recommendation"],
        "expected_keywords": ["blight", "tomato", "treatment", "fungicide"],
        "category": "disease_diagnosis",
        "difficulty": 2,
        "crop": "tomato",
        "region": "east_africa",
    },
    {
        "id": "tomato_ea_disease_sw",
        "query": "Majani ya nyanya zangu yana madoa ya kahawia na pete. Ni ugonjwa gani?",
        "location": (REGIONS["east_africa"]["lat"], REGIONS["east_africa"]["lon"]),
        "expected_tools": ["diagnose_crop_disease", "get_treatment_recommendation"],
        "expected_keywords": ["blight", "tomato", "treatment"],
        "category": "disease_diagnosis",
        "difficulty": 3,
        "crop": "tomato",
        "region": "east_africa",
        "language": "sw",
    },
    {
        "id": "tomato_wa_market",
        "query": "My tomatoes are ripe. What's the market price? Should I sell now?",
        "location": (REGIONS["west_africa"]["lat"], REGIONS["west_africa"]["lon"]),
        "expected_tools": ["get_commodity_prices", "get_price_forecast", "get_weather_forecast"],
        "expected_keywords": ["price", "tomato", "sell", "market"],
        "category": "market_advisory",
        "difficulty": 3,
        "crop": "tomato",
        "region": "west_africa",
    },
    {
        "id": "tomato_sea_planting",
        "query": "Can I plant tomatoes now? Check weather and soil for my area.",
        "location": (REGIONS["southeast_asia"]["lat"], REGIONS["southeast_asia"]["lon"]),
        "expected_tools": ["get_weather_forecast", "get_planting_advisory", "get_soil_analysis"],
        "expected_keywords": ["tomato", "plant", "temperature", "soil"],
        "category": "planting",
        "difficulty": 3,
        "crop": "tomato",
        "region": "southeast_asia",
    },
    # === CASSAVA scenarios ===
    {
        "id": "cassava_ea_comprehensive",
        "query": "My cassava is in flowering stage and there's been no rain for 3 weeks. "
                 "I also see white flies on the leaves. What should I do?",
        "location": (REGIONS["east_africa"]["lat"], REGIONS["east_africa"]["lon"]),
        "expected_tools": ["get_weather_forecast", "diagnose_crop_disease", "get_climate_risk_alert"],
        "expected_keywords": ["drought", "whitefly", "mosaic", "water", "cassava"],
        "category": "multi_risk",
        "difficulty": 4,
        "crop": "cassava",
        "region": "east_africa",
    },
    {
        "id": "cassava_wa_planting",
        "query": "When is the best time to plant cassava? What variety should I use?",
        "location": (REGIONS["west_africa"]["lat"], REGIONS["west_africa"]["lon"]),
        "expected_tools": ["get_planting_advisory", "get_soil_analysis"],
        "expected_keywords": ["cassava", "plant", "season", "soil"],
        "category": "planting",
        "difficulty": 2,
        "crop": "cassava",
        "region": "west_africa",
    },
    {
        "id": "cassava_ea_disease_sw",
        "query": "Mihogo yangu ina majani ya njano na inanyauka. Nifanye nini?",
        "location": (REGIONS["east_africa"]["lat"], REGIONS["east_africa"]["lon"]),
        "expected_tools": ["diagnose_crop_disease", "get_treatment_recommendation"],
        "expected_keywords": ["cassava", "mosaic", "disease"],
        "category": "disease_diagnosis",
        "difficulty": 3,
        "crop": "cassava",
        "region": "east_africa",
        "language": "sw",
    },
    # === RICE scenarios ===
    {
        "id": "rice_sa_planting",
        "query": "I want to plant rice this monsoon season. Check weather and give me advice.",
        "location": (REGIONS["south_asia"]["lat"], REGIONS["south_asia"]["lon"]),
        "expected_tools": ["get_weather_forecast", "get_planting_advisory"],
        "expected_keywords": ["rice", "monsoon", "rain", "plant"],
        "category": "planting",
        "difficulty": 2,
        "crop": "rice",
        "region": "south_asia",
    },
    {
        "id": "rice_sea_market",
        "query": "When should I sell my rice harvest for the best price?",
        "location": (REGIONS["southeast_asia"]["lat"], REGIONS["southeast_asia"]["lon"]),
        "expected_tools": ["get_commodity_prices", "get_price_forecast"],
        "expected_keywords": ["price", "rice", "sell", "month"],
        "category": "market_advisory",
        "difficulty": 2,
        "crop": "rice",
        "region": "southeast_asia",
    },
    {
        "id": "rice_sa_disease",
        "query": "My rice has brown lesions on the leaves that are spreading fast. Help!",
        "location": (REGIONS["south_asia"]["lat"], REGIONS["south_asia"]["lon"]),
        "expected_tools": ["diagnose_crop_disease", "get_treatment_recommendation", "get_weather_forecast"],
        "expected_keywords": ["rice", "blast", "fungicide", "disease"],
        "category": "disease_diagnosis",
        "difficulty": 3,
        "crop": "rice",
        "region": "south_asia",
    },
    {
        "id": "rice_sea_flood",
        "query": "Heavy rains are forecast. My rice paddy is at risk of flooding. What should I do?",
        "location": (REGIONS["southeast_asia"]["lat"], REGIONS["southeast_asia"]["lon"]),
        "expected_tools": ["get_weather_forecast", "get_climate_risk_alert"],
        "expected_keywords": ["flood", "rain", "rice", "drain"],
        "category": "risk_assessment",
        "difficulty": 3,
        "crop": "rice",
        "region": "southeast_asia",
    },
    # === BEANS scenarios ===
    {
        "id": "beans_ea_planting_sw",
        "query": "Nataka kupanda maharage. Hali ya hewa na udongo uko vipi?",
        "location": (REGIONS["east_africa"]["lat"], REGIONS["east_africa"]["lon"]),
        "expected_tools": ["get_weather_forecast", "get_planting_advisory", "get_soil_analysis"],
        "expected_keywords": ["beans", "plant", "soil", "rain"],
        "category": "planting",
        "difficulty": 3,
        "crop": "beans",
        "region": "east_africa",
        "language": "sw",
    },
    {
        "id": "beans_wa_disease",
        "query": "My bean plants have rust-colored spots on the underside of leaves.",
        "location": (REGIONS["west_africa"]["lat"], REGIONS["west_africa"]["lon"]),
        "expected_tools": ["diagnose_crop_disease", "get_treatment_recommendation"],
        "expected_keywords": ["rust", "bean", "fungicide"],
        "category": "disease_diagnosis",
        "difficulty": 2,
        "crop": "beans",
        "region": "west_africa",
    },
    # === COMPREHENSIVE / CROSS-CUTTING ===
    {
        "id": "comprehensive_ea_planning",
        "query": "I have 2 hectares and want to plan my next growing season. "
                 "What should I plant, when, and how much can I expect to earn?",
        "location": (REGIONS["east_africa"]["lat"], REGIONS["east_africa"]["lon"]),
        "expected_tools": ["get_soil_analysis", "get_weather_forecast", "get_planting_advisory", "get_commodity_prices"],
        "expected_keywords": ["plant", "season", "price", "soil", "maize"],
        "category": "planning",
        "difficulty": 5,
        "crop": "mixed",
        "region": "east_africa",
    },
    {
        "id": "comprehensive_ea_sw",
        "query": "Nina ekari mbili. Nipande nini msimu huu? Angalia hali ya hewa, udongo, na bei.",
        "location": (REGIONS["east_africa"]["lat"], REGIONS["east_africa"]["lon"]),
        "expected_tools": ["get_soil_analysis", "get_weather_forecast", "get_planting_advisory", "get_commodity_prices"],
        "expected_keywords": ["plant", "soil", "price", "weather"],
        "category": "planning",
        "difficulty": 5,
        "crop": "mixed",
        "region": "east_africa",
        "language": "sw",
    },
    {
        "id": "frost_alert_sa",
        "query": "Will it be safe to plant tomatoes this week? I'm worried about cold weather.",
        "location": (REGIONS["south_asia"]["lat"], REGIONS["south_asia"]["lon"]),
        "expected_tools": ["get_weather_forecast", "get_planting_advisory"],
        "expected_keywords": ["temperature", "cold", "planting"],
        "category": "weather_advisory",
        "difficulty": 1,
        "crop": "tomato",
        "region": "south_asia",
    },
]


def load_checkpoint() -> dict:
    if os.path.exists(CHECKPOINT_PATH):
        with open(CHECKPOINT_PATH) as f:
            return json.load(f)
    return {"completed_ids": [], "results": [], "last_idx": 0}


def save_checkpoint(state: dict):
    os.makedirs(os.path.dirname(CHECKPOINT_PATH), exist_ok=True)
    with open(CHECKPOINT_PATH, "w") as f:
        json.dump(state, f, indent=2)


def score_result(scenario: dict, agent_result: dict) -> dict:
    """Score a single agent result against expected ground truth."""
    tools_called = [tc["tool"] for tc in agent_result.get("tool_calls", [])]
    response_text = agent_result.get("response", "").lower()

    # Tool selection accuracy (F1)
    expected_tools = set(scenario["expected_tools"])
    called_tools = set(tools_called)
    tool_precision = len(expected_tools & called_tools) / max(len(called_tools), 1)
    tool_recall = len(expected_tools & called_tools) / max(len(expected_tools), 1)
    tool_f1 = 2 * tool_precision * tool_recall / max(tool_precision + tool_recall, 1e-6)

    # Keyword coverage
    keywords_found = sum(1 for kw in scenario["expected_keywords"] if kw.lower() in response_text)
    keyword_coverage = keywords_found / max(len(scenario["expected_keywords"]), 1)

    # Response quality heuristics
    actionable_phrases = [
        "should", "recommend", "apply", "plant", "avoid", "immediately",
        "consider", "spray", "wait", "sell", "harvest", "irrigate",
        "use", "treat", "protect", "monitor",
    ]
    has_actionable_advice = any(phrase in response_text for phrase in actionable_phrases)
    response_length_ok = 50 < len(response_text) < 3000

    # Composite score
    score = (
        0.4 * tool_f1
        + 0.3 * keyword_coverage
        + 0.15 * float(has_actionable_advice)
        + 0.15 * float(response_length_ok)
    )

    return {
        "scenario_id": scenario["id"],
        "crop": scenario.get("crop", "unknown"),
        "region": scenario.get("region", "unknown"),
        "language": scenario.get("language", "en"),
        "category": scenario["category"],
        "difficulty": scenario["difficulty"],
        "tool_f1": round(tool_f1, 3),
        "keyword_coverage": round(keyword_coverage, 3),
        "has_actionable_advice": has_actionable_advice,
        "response_length_ok": response_length_ok,
        "composite_score": round(score, 3),
        "tools_expected": list(expected_tools),
        "tools_called": tools_called,
    }


def run_evaluation(agent, output_path: str = "logs/eval_results.json", fresh: bool = False):
    """Run full evaluation suite with checkpoint/resume.

    Args:
        agent: ClimaSenseAgent instance (must have .run() method).
        output_path: Path for results JSON.
        fresh: If True, ignore checkpoint and start fresh.
    """
    if fresh and os.path.exists(CHECKPOINT_PATH):
        os.remove(CHECKPOINT_PATH)

    state = load_checkpoint()
    completed_ids = set(state["completed_ids"])

    remaining = [s for s in EVAL_SCENARIOS if s["id"] not in completed_ids]
    logger.info("Eval: %d/%d scenarios remaining", len(remaining), len(EVAL_SCENARIOS))

    for scenario in tqdm(remaining, desc="Evaluating ClimaSense"):
        start = time.time()
        try:
            result = agent.run(
                query=scenario["query"],
                location=scenario.get("location"),
            )
        except Exception as e:
            logger.error("Scenario %s failed: %s", scenario["id"], e)
            result = {"response": "", "tool_calls": [], "error": str(e)}

        elapsed = time.time() - start
        scored = score_result(scenario, result)
        scored["elapsed_seconds"] = round(elapsed, 2)

        state["results"].append(scored)
        state["completed_ids"].append(scenario["id"])
        save_checkpoint(state)

    # Compute aggregate metrics
    summary = generate_summary(state["results"])

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(summary, f, indent=2)

    logger.info("Evaluation complete. Avg score: %.3f", summary.get("avg_composite_score", 0))
    return summary


def generate_summary(results: list[dict]) -> dict:
    """Generate summary statistics from evaluation results."""
    if not results:
        return {"total_scenarios": len(EVAL_SCENARIOS), "completed": 0}

    scores = [r["composite_score"] for r in results]
    tool_f1s = [r["tool_f1"] for r in results]

    # Per-category breakdown
    categories = {}
    for r in results:
        cat = r["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(r["composite_score"])
    category_avgs = {cat: round(sum(s) / len(s), 3) for cat, s in categories.items()}

    # Per-crop breakdown
    crops = {}
    for r in results:
        crop = r.get("crop", "unknown")
        if crop not in crops:
            crops[crop] = []
        crops[crop].append(r["composite_score"])
    crop_avgs = {c: round(sum(s) / len(s), 3) for c, s in crops.items()}

    # Per-region breakdown
    regions = {}
    for r in results:
        region = r.get("region", "unknown")
        if region not in regions:
            regions[region] = []
        regions[region].append(r["composite_score"])
    region_avgs = {reg: round(sum(s) / len(s), 3) for reg, s in regions.items()}

    # Per-language breakdown
    langs = {}
    for r in results:
        lang = r.get("language", "en")
        if lang not in langs:
            langs[lang] = []
        langs[lang].append(r["composite_score"])
    lang_avgs = {l: round(sum(s) / len(s), 3) for l, s in langs.items()}

    return {
        "total_scenarios": len(EVAL_SCENARIOS),
        "completed": len(results),
        "avg_composite_score": round(sum(scores) / len(scores), 3),
        "avg_tool_f1": round(sum(tool_f1s) / len(tool_f1s), 3),
        "by_category": category_avgs,
        "by_crop": crop_avgs,
        "by_region": region_avgs,
        "by_language": lang_avgs,
        "results": results,
    }


def print_results_table(summary: dict):
    """Print a formatted results table for the writeup."""
    print(f"\n{'='*70}")
    print("CLIMASENSE EVALUATION RESULTS")
    print(f"{'='*70}")
    print(f"\nOverall: {summary['avg_composite_score']:.3f} composite | {summary['avg_tool_f1']:.3f} tool F1")
    print(f"Scenarios: {summary['completed']}/{summary['total_scenarios']}")

    print(f"\n--- By Category ---")
    for cat, score in sorted(summary.get("by_category", {}).items()):
        print(f"  {cat:<20} {score:.3f}")

    print(f"\n--- By Crop ---")
    for crop, score in sorted(summary.get("by_crop", {}).items()):
        print(f"  {crop:<20} {score:.3f}")

    print(f"\n--- By Region ---")
    for region, score in sorted(summary.get("by_region", {}).items()):
        print(f"  {region:<20} {score:.3f}")

    print(f"\n--- By Language ---")
    for lang, score in sorted(summary.get("by_language", {}).items()):
        print(f"  {lang:<20} {score:.3f}")

    print(f"\n--- Individual Scenarios ---")
    print(f"{'ID':<30} {'Crop':<10} {'Region':<15} {'Lang':<5} {'F1':<6} {'KW':<6} {'Score':<6} {'Time':<6}")
    print("-" * 84)
    for r in summary.get("results", []):
        print(f"{r['scenario_id']:<30} {r.get('crop','?'):<10} {r.get('region','?'):<15} "
              f"{r.get('language','en'):<5} {r['tool_f1']:<6.3f} {r['keyword_coverage']:<6.3f} "
              f"{r['composite_score']:<6.3f} {r.get('elapsed_seconds', 0):<6.1f}s")
