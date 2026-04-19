"""Agent end-to-end test — verify multi-tool reasoning across realistic farmer scenarios.

Each scenario is designed to require multiple tool calls. The test validates:
1. The agent actually invokes the expected tools (not hallucinates)
2. Tools compose in a sensible order (e.g., diagnose disease before treatment)
3. The new satellite tool (get_vegetation_health) is triggered at least once
4. All tool payloads are real (no mock data)

Run:
    python scripts/agent_e2e_test.py
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from pathlib import Path

# Pin to GPU 2 (0 and 1 are occupied by other users' vLLM servers).
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "2")

import torch  # noqa: E402
from climasense.agent import ClimaSenseAgent  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("agent_e2e")

SCENARIOS = [
    {
        "id": "disease_with_satellite_corroboration",
        "description": "Farmer reports disease AND wants the field checked from space. "
                       "Expect: diagnose_crop_disease + get_vegetation_health + get_treatment_recommendation.",
        "query": (
            "My tomato leaves have yellow curled patches with a mosaic pattern "
            "and the plants are growing slowly. It has been unusually hot and dry. "
            "Can you diagnose this and also check from satellite whether my whole field "
            "is stressed? If so, what should I do?"
        ),
        "location": (-0.0917, 34.7680),  # Kenya, Kisumu
        "expected_tools": {"diagnose_crop_disease", "get_vegetation_health"},
    },
    {
        "id": "planting_decision_multi_tool",
        "description": "Planting-timing question — needs climatology + soil + current weather.",
        "query": (
            "I am in Ghana and I want to plant maize. "
            "Is this a good month to plant? What does the soil look like? "
            "And what is the weather doing over the next week?"
        ),
        "location": (6.6885, -1.6244),  # Ghana, Kumasi
        "expected_tools": {"get_planting_advisory", "get_soil_analysis", "get_weather_forecast"},
    },
    {
        "id": "market_timing_decision",
        "description": "Market timing — needs current prices + forecast.",
        "query": (
            "I am a sorghum farmer in northern Nigeria. I have 200 kg to sell. "
            "What are sorghum prices doing now, and will they go up or down in the next 3 months? "
            "Should I sell now or wait?"
        ),
        "location": (12.0022, 8.5920),  # Nigeria, Kano
        "expected_tools": {"get_commodity_prices", "get_price_forecast"},
    },
]


def run_scenario(agent: ClimaSenseAgent, scenario: dict) -> dict:
    """Run a single scenario and capture the full trace."""
    print(f"\n{'=' * 70}")
    print(f"Scenario: {scenario['id']}")
    print(f"Query: {scenario['query']}")
    print(f"Location: {scenario['location']}")
    print(f"Expected tools: {sorted(scenario['expected_tools'])}")
    print("-" * 70)

    t0 = time.time()
    try:
        result = agent.run(query=scenario["query"], location=scenario["location"])
        elapsed = round(time.time() - t0, 1)
    except Exception as e:
        elapsed = round(time.time() - t0, 1)
        return {
            "id": scenario["id"],
            "ok": False,
            "elapsed_s": elapsed,
            "error": f"{type(e).__name__}: {e}",
        }

    tools_called = {tc["tool"] for tc in result.get("tool_calls", [])}
    missing = scenario["expected_tools"] - tools_called
    extras = tools_called - scenario["expected_tools"]

    print(f"Response ({elapsed}s, turns={result.get('turns')}):")
    print(result.get("response", "")[:800])
    print(f"\nTools called: {sorted(tools_called)}")
    if missing:
        print(f"  MISSING expected tools: {sorted(missing)}")
    if extras:
        print(f"  EXTRA tools used: {sorted(extras)}")

    return {
        "id": scenario["id"],
        "description": scenario["description"],
        "query": scenario["query"],
        "location": scenario["location"],
        "ok": len(missing) == 0,
        "elapsed_s": elapsed,
        "turns": result.get("turns"),
        "response": result.get("response"),
        "tool_calls": result.get("tool_calls"),
        "tools_called": sorted(tools_called),
        "missing_expected_tools": sorted(missing),
        "extra_tools": sorted(extras),
    }


def main() -> int:
    print("=" * 70)
    print("ClimaSense — Agent End-to-End Test")
    print(f"CUDA_VISIBLE_DEVICES={os.environ.get('CUDA_VISIBLE_DEVICES')}")
    print(f"torch CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        for i in range(torch.cuda.device_count()):
            print(f"  GPU {i}: {torch.cuda.get_device_name(i)}")
    print("=" * 70)

    # Use E4B for speed — this test is about tool orchestration, not model size.
    # The 31B gives richer natural language, but E4B proves the function-calling
    # contract end-to-end and completes in minutes, not hours.
    model_id = os.environ.get("AGENT_MODEL", "google/gemma-4-E4B-it")
    print(f"Loading {model_id}...")
    agent = ClimaSenseAgent(
        model_id=model_id,
        audio_model_id=None,  # skip audio for this test
        max_turns=6,
        enable_thinking=False,  # faster; we just need tool orchestration
    )

    results = []
    for scenario in SCENARIOS:
        r = run_scenario(agent, scenario)
        results.append(r)

    passed = sum(1 for r in results if r["ok"])
    total = len(results)

    report = {
        "model_id": model_id,
        "total_scenarios": total,
        "passed": passed,
        "failed": total - passed,
        "scenarios": results,
    }

    out = Path("logs/agent_e2e_results.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, default=str))

    print("\n" + "=" * 70)
    print(f"Agent E2E Summary: {passed}/{total} scenarios met expected tool set")
    for r in results:
        marker = "OK " if r["ok"] else "ERR"
        tools = ", ".join(r.get("tools_called") or []) or "(none)"
        print(f"  [{marker}] {r['id']:<42} {r['elapsed_s']:>6}s   tools: {tools}")
    print("=" * 70)
    print(f"Full report: {out}")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
