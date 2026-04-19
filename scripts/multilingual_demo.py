"""P10: Multilingual demo — test ClimaSense in Swahili, Hindi, French, English.

Runs real tool calls for each language, generates TTS audio output,
and records results for the writeup. Does NOT require GPU — uses tools directly.
"""

import json
import logging
import os
import time
from pathlib import Path

from climasense.tools import TOOL_REGISTRY
from climasense.multimodal.tts import text_to_speech, detect_language_code
from climasense.personas import AMINA

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

OUTPUT_DIR = Path("data/multilingual_demo")

# Multilingual scenarios — same agricultural question in 4 languages
MULTILINGUAL_SCENARIOS = [
    {
        "id": "weather_en",
        "language": "English",
        "lang_code": "en",
        "query": "What is the weather forecast for this week? My tomatoes need spraying.",
        "location": AMINA["location"]["coordinates"],
        "tools_to_call": [
            ("get_weather_forecast", {"latitude": AMINA["location"]["coordinates"][0],
                                       "longitude": AMINA["location"]["coordinates"][1]}),
        ],
    },
    {
        "id": "weather_sw",
        "language": "Swahili",
        "lang_code": "sw",
        "query": "Hali ya hewa ikoje wiki hii? Nina nyanya zangu zinahitaji dawa.",
        "location": AMINA["location"]["coordinates"],
        "tools_to_call": [
            ("get_weather_forecast", {"latitude": AMINA["location"]["coordinates"][0],
                                       "longitude": AMINA["location"]["coordinates"][1]}),
        ],
    },
    {
        "id": "weather_hi",
        "language": "Hindi",
        "lang_code": "hi",
        "query": "इस हफ्ते मौसम कैसा रहेगा? मेरे टमाटर के पौधों पर स्प्रे करना है।",
        "location": AMINA["location"]["coordinates"],
        "tools_to_call": [
            ("get_weather_forecast", {"latitude": AMINA["location"]["coordinates"][0],
                                       "longitude": AMINA["location"]["coordinates"][1]}),
        ],
    },
    {
        "id": "weather_fr",
        "language": "French",
        "lang_code": "fr",
        "query": "Quelles sont les previsions meteo cette semaine? Mes tomates ont besoin d'etre traitees.",
        "location": AMINA["location"]["coordinates"],
        "tools_to_call": [
            ("get_weather_forecast", {"latitude": AMINA["location"]["coordinates"][0],
                                       "longitude": AMINA["location"]["coordinates"][1]}),
        ],
    },
    {
        "id": "disease_sw",
        "language": "Swahili",
        "lang_code": "sw",
        "query": "Majani ya nyanya yangu yana madoa ya kahawia. Ni ugonjwa gani huu?",
        "tools_to_call": [
            ("diagnose_crop_disease", {"crop": "tomato", "symptoms": "brown spots on leaves with concentric rings"}),
            ("get_treatment_recommendation", {"disease_name": "early_blight"}),
        ],
    },
    {
        "id": "disease_hi",
        "language": "Hindi",
        "lang_code": "hi",
        "query": "मेरे टमाटर के पत्तों पर भूरे धब्बे हैं। यह कौन सी बीमारी है?",
        "tools_to_call": [
            ("diagnose_crop_disease", {"crop": "tomato", "symptoms": "brown spots on leaves with concentric rings"}),
            ("get_treatment_recommendation", {"disease_name": "early_blight"}),
        ],
    },
    {
        "id": "market_sw",
        "language": "Swahili",
        "lang_code": "sw",
        "query": "Bei ya mahindi iko vipi sasa hivi Kenya?",
        "tools_to_call": [
            ("get_commodity_prices", {"crop": "maize", "country": "kenya"}),
        ],
    },
    {
        "id": "market_fr",
        "language": "French",
        "lang_code": "fr",
        "query": "Quel est le prix du mais au marche actuellement?",
        "tools_to_call": [
            ("get_commodity_prices", {"crop": "maize", "country": "kenya"}),
        ],
    },
    {
        "id": "planting_sw",
        "language": "Swahili",
        "lang_code": "sw",
        "query": "Wakati gani mzuri wa kupanda mahindi msimu huu?",
        "tools_to_call": [
            ("get_planting_advisory", {"crop": "maize",
                                        "latitude": AMINA["location"]["coordinates"][0],
                                        "longitude": AMINA["location"]["coordinates"][1]}),
        ],
    },
    {
        "id": "soil_hi",
        "language": "Hindi",
        "lang_code": "hi",
        "query": "मेरे खेत की मिट्टी की गुणवत्ता कैसी है?",
        "tools_to_call": [
            ("get_soil_analysis", {"latitude": AMINA["location"]["coordinates"][0],
                                    "longitude": AMINA["location"]["coordinates"][1]}),
        ],
    },
    {
        "id": "risk_fr",
        "language": "French",
        "lang_code": "fr",
        "query": "Y a-t-il des risques climatiques pour mes cultures cette semaine?",
        "tools_to_call": [
            ("get_climate_risk_alert", {"crop": "maize",
                                         "latitude": AMINA["location"]["coordinates"][0],
                                         "longitude": AMINA["location"]["coordinates"][1],
                                         "growth_stage": "vegetative"}),
        ],
    },
    {
        "id": "comprehensive_en",
        "language": "English",
        "lang_code": "en",
        "query": "I want to plant maize. Check weather, soil, prices, and give me a planting plan.",
        "tools_to_call": [
            ("get_weather_forecast", {"latitude": AMINA["location"]["coordinates"][0],
                                       "longitude": AMINA["location"]["coordinates"][1]}),
            ("get_soil_analysis", {"latitude": AMINA["location"]["coordinates"][0],
                                    "longitude": AMINA["location"]["coordinates"][1]}),
            ("get_commodity_prices", {"crop": "maize", "country": "kenya"}),
            ("get_planting_advisory", {"crop": "maize",
                                        "latitude": AMINA["location"]["coordinates"][0],
                                        "longitude": AMINA["location"]["coordinates"][1]}),
        ],
    },
]


def run_scenario(scenario: dict) -> dict:
    """Run a single multilingual scenario using real tools."""
    result = {
        "id": scenario["id"],
        "language": scenario["language"],
        "lang_code": scenario["lang_code"],
        "query": scenario["query"],
        "tool_results": [],
        "tts_path": None,
    }

    # Execute tools
    for tool_name, tool_args in scenario["tools_to_call"]:
        start = time.time()
        try:
            tool_result = TOOL_REGISTRY[tool_name](**tool_args)
            elapsed = time.time() - start
            result["tool_results"].append({
                "tool": tool_name,
                "args": tool_args,
                "result": tool_result,
                "elapsed_s": round(elapsed, 2),
                "status": "success",
            })
            logger.info("  %s: OK (%.1fs)", tool_name, elapsed)
        except Exception as e:
            elapsed = time.time() - start
            result["tool_results"].append({
                "tool": tool_name,
                "args": tool_args,
                "error": str(e),
                "elapsed_s": round(elapsed, 2),
                "status": "error",
            })
            logger.warning("  %s: FAILED (%s)", tool_name, e)

    # Generate TTS for the query (proves multilingual TTS works)
    try:
        tts_dir = OUTPUT_DIR / "audio"
        tts_dir.mkdir(parents=True, exist_ok=True)
        tts_path = text_to_speech(
            scenario["query"],
            output_path=tts_dir / f"{scenario['id']}.mp3",
            lang=scenario["lang_code"],
        )
        result["tts_path"] = str(tts_path)
        result["tts_size_bytes"] = os.path.getsize(tts_path)
        logger.info("  TTS: %s (%d bytes)", tts_path, result["tts_size_bytes"])
    except Exception as e:
        logger.warning("  TTS failed: %s", e)
        result["tts_error"] = str(e)

    return result


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"{'='*70}")
    print("ClimaSense Multilingual Demo")
    print(f"Persona: {AMINA['name']} — {AMINA['location']['village']}, {AMINA['location']['county']}")
    print(f"Languages: English, Swahili, Hindi, French")
    print(f"Scenarios: {len(MULTILINGUAL_SCENARIOS)}")
    print(f"{'='*70}\n")

    all_results = []
    lang_stats = {}

    for scenario in MULTILINGUAL_SCENARIOS:
        print(f"\n--- [{scenario['language']}] {scenario['id']} ---")
        print(f"  Query: {scenario['query']}")

        result = run_scenario(scenario)
        all_results.append(result)

        # Track per-language stats
        lang = scenario["language"]
        if lang not in lang_stats:
            lang_stats[lang] = {"total": 0, "tools_ok": 0, "tools_fail": 0, "tts_ok": 0}
        lang_stats[lang]["total"] += 1
        for tr in result["tool_results"]:
            if tr["status"] == "success":
                lang_stats[lang]["tools_ok"] += 1
            else:
                lang_stats[lang]["tools_fail"] += 1
        if result.get("tts_path"):
            lang_stats[lang]["tts_ok"] += 1

    # Summary
    print(f"\n{'='*70}")
    print("RESULTS SUMMARY")
    print(f"{'='*70}")
    print(f"\n{'Language':<12} {'Scenarios':<12} {'Tools OK':<12} {'Tools Fail':<12} {'TTS OK':<10}")
    print("-" * 58)
    for lang, stats in lang_stats.items():
        print(f"{lang:<12} {stats['total']:<12} {stats['tools_ok']:<12} {stats['tools_fail']:<12} {stats['tts_ok']:<10}")

    total_tools = sum(s["tools_ok"] + s["tools_fail"] for s in lang_stats.values())
    total_ok = sum(s["tools_ok"] for s in lang_stats.values())
    print(f"\nOverall tool success rate: {total_ok}/{total_tools} ({100*total_ok/max(total_tools,1):.0f}%)")

    # Save results
    output_file = OUTPUT_DIR / "multilingual_results.json"
    with open(output_file, "w") as f:
        json.dump({
            "persona": AMINA["name"],
            "location": AMINA["location"],
            "scenarios": all_results,
            "language_stats": lang_stats,
        }, f, indent=2, default=str)
    print(f"\nResults saved to: {output_file}")


if __name__ == "__main__":
    main()
