"""Run just the 5 Swahili scenarios through E4B to validate the scoring fix.

The 31B eval takes ~40 minutes. E4B runs each Swahili scenario in ~30s, so we
can get real numbers (not synthetic) in ~3 min. If composite climbs, the fix
is real; if not, there's a behavior problem we missed.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("CUDA_VISIBLE_DEVICES", "2")  # GPU0 is busy; GPU1 is VLLM
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from climasense.agent import ClimaSenseAgent
from climasense.eval.benchmark import EVAL_SCENARIOS, score_result

OUTPUT = Path("logs/eval_swahili_e4b.json")


def main():
    sw_scenarios = [s for s in EVAL_SCENARIOS if s.get("language") == "sw"]
    print(f"Running {len(sw_scenarios)} Swahili scenarios on Gemma 4 E4B...")

    agent = ClimaSenseAgent(model_id="google/gemma-4-e4b-it")

    results = []
    for scen in sw_scenarios:
        print(f"\n--- {scen['id']} ---")
        print(f"  query: {scen['query']}")
        t0 = time.time()
        try:
            agent_result = agent.run(query=scen["query"], location=scen.get("location"))
        except Exception as e:
            print(f"  FAILED: {e}")
            agent_result = {"response": "", "tool_calls": [], "error": str(e)}
        elapsed = time.time() - t0

        scored = score_result(scen, agent_result)
        scored["elapsed_seconds"] = round(elapsed, 2)
        # Keep the raw response so we can rescore offline later without re-running.
        scored["_response_preview"] = agent_result.get("response", "")[:400]
        scored["_tool_calls"] = [tc.get("tool") for tc in agent_result.get("tool_calls", [])]

        print(f"  tools_called: {scored['_tool_calls']}")
        print(f"  response[:200]: {scored['_response_preview'][:200]!r}")
        print(f"  tool_f1: {scored['tool_f1']}  keyword_cov: {scored['keyword_coverage']}  composite: {scored['composite_score']}")
        results.append({"scenario_id": scen["id"], "scored": scored, "response": agent_result.get("response", "")})

    # Compare with old checkpoint values for the same IDs
    old = {r["scenario_id"]: r for r in json.loads(Path("logs/checkpoint_eval.json").read_text())["results"]}
    print("\n=== OLD vs NEW ===")
    print(f"{'id':<28} {'old_kw':>6} {'new_kw':>6} {'old_comp':>8} {'new_comp':>8}")
    old_comps, new_comps = [], []
    for r in results:
        sid = r["scenario_id"]
        o = old.get(sid, {})
        n = r["scored"]
        ok, nk = o.get("keyword_coverage", 0.0), n["keyword_coverage"]
        oc, nc = o.get("composite_score", 0.0), n["composite_score"]
        old_comps.append(oc)
        new_comps.append(nc)
        print(f"{sid:<28} {ok:>6.2f} {nk:>6.2f} {oc:>8.2f} {nc:>8.2f}")

    if old_comps:
        print(f"\nSwahili avg composite: {sum(old_comps)/len(old_comps):.3f} (31B old) -> {sum(new_comps)/len(new_comps):.3f} (E4B new)")
        print("Note: 31B->E4B is a weaker model, so if new>=old, the scoring fix is load-bearing.")

    OUTPUT.parent.mkdir(exist_ok=True)
    OUTPUT.write_text(json.dumps(results, indent=2, default=str))
    print(f"\nSaved -> {OUTPUT}")


if __name__ == "__main__":
    main()
