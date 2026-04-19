"""Re-score the existing eval run with the multilingual-aware scorer.

The full 20-scenario eval takes ~40 min on 31B. Rather than re-running, we
keep the saved tool_calls + response payloads and just re-apply the new
score_result() to each. This is how we validate that the Swahili gap was a
scoring artifact rather than a behavior problem.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from climasense.eval.benchmark import EVAL_SCENARIOS, score_result

CHECKPOINT = Path("logs/checkpoint_eval.json")
RESPONSES = Path("logs/eval_responses.json")

scenario_by_id = {s["id"]: s for s in EVAL_SCENARIOS}
saved = json.loads(CHECKPOINT.read_text())
saved_results = saved.get("results", [])

# The checkpoint stores scored results; it doesn't preserve the raw response
# text needed to re-score. If a richer responses file exists, prefer it.
responses_by_id: dict[str, dict] = {}
if RESPONSES.exists():
    raw = json.loads(RESPONSES.read_text())
    for item in raw:
        responses_by_id[item["id"]] = item


def reconstruct_agent_result(prev: dict) -> dict | None:
    """Build an agent.run-style result from a previous scored record.

    Prefer fields saved on the scored record itself (new eval runs include
    _response / _tool_calls_full). Fall back to a separate responses file
    for backward compatibility with older checkpoints.
    """
    if "_response" in prev:
        return {
            "response": prev.get("_response", ""),
            "tool_calls": prev.get("_tool_calls_full") or [
                {"tool": t, "args": {}, "result": {}} for t in prev.get("tools_called", [])
            ],
        }
    raw = responses_by_id.get(prev["scenario_id"])
    if raw is None:
        return None
    return {
        "response": raw.get("response", ""),
        "tool_calls": raw.get("tool_calls") or [
            {"tool": t, "args": {}, "result": {}} for t in prev.get("tools_called", [])
        ],
    }


have_embedded = any("_response" in r for r in saved_results)
if not responses_by_id and not have_embedded:
    print("No response text available (checkpoint predates response persistence).")
    print("Re-run the eval once — future rescoring will work without re-running.")
    sys.exit(1)

rescored = []
for prev in saved_results:
    sid = prev["scenario_id"]
    scenario = scenario_by_id.get(sid)
    if scenario is None:
        continue
    agent_result = reconstruct_agent_result(prev)
    if agent_result is None:
        continue
    scored = score_result(scenario, agent_result)
    rescored.append(scored)

# Side-by-side diff, focused on Swahili
print(f"{'id':<28} {'lang':<4} {'old_kw':>6} {'new_kw':>6} {'old_comp':>8} {'new_comp':>8}")
for old, new in zip(saved_results, rescored):
    print(
        f"{old['scenario_id']:<28} {new['language']:<4} "
        f"{old['keyword_coverage']:>6.2f} {new['keyword_coverage']:>6.2f} "
        f"{old['composite_score']:>8.2f} {new['composite_score']:>8.2f}"
    )

def avg(xs, key):
    return round(sum(x[key] for x in xs) / max(len(xs), 1), 3)

sw_old = [r for r in saved_results if r["language"] == "sw"]
sw_new = [r for r in rescored if r["language"] == "sw"]
en_old = [r for r in saved_results if r["language"] == "en"]
en_new = [r for r in rescored if r["language"] == "en"]

print()
print(f"Swahili composite: {avg(sw_old, 'composite_score'):.3f} -> {avg(sw_new, 'composite_score'):.3f}")
print(f"English composite: {avg(en_old, 'composite_score'):.3f} -> {avg(en_new, 'composite_score'):.3f}")
print(f"Overall composite: {avg(saved_results, 'composite_score'):.3f} -> {avg(rescored, 'composite_score'):.3f}")
