"""Refresh notebooks/climasense_demo.ipynb with the two newest tools
(satellite + postharvest) and a T4-simulation preflight cell, update
tool-count claims, and fix the repo URL. Run once before executing the
notebook."""
from __future__ import annotations

import json
from pathlib import Path

import nbformat as nbf

NB_PATH = Path("notebooks/climasense_demo.ipynb")
REPO = "Ramesh-Arvind/climasense-"

nb = nbf.read(NB_PATH, as_version=4)


def replace_in_cell(cell, old: str, new: str) -> None:
    src = cell.source
    if old in src:
        cell.source = src.replace(old, new)


for cell in nb.cells:
    replace_in_cell(cell, "your-repo/climasense", REPO)
    replace_in_cell(cell, "9 real-API tools", "11 real-API tools")
    replace_in_cell(cell, "9 tools", "11 tools")
    replace_in_cell(cell, "**9 tools**", "**11 tools**")
    replace_in_cell(cell, "9 real-API tools", "11 real-API tools")
    replace_in_cell(
        cell,
        "native function calling with 9 real-API tools",
        "native function calling with 11 real-API tools",
    )


preflight = nbf.v4.new_code_cell(
    source="""# T4 preflight — mirror what Kaggle's free Tesla T4 would show us.
# 16 GB VRAM bound, so we pin E4B (fp16 ~8 GB) as the default substrate.
import os, torch

# If you're running this on a bigger box, force Kaggle-like conditions:
#   os.environ.setdefault("CUDA_VISIBLE_DEVICES", "0")

if torch.cuda.is_available():
    props = torch.cuda.get_device_properties(0)
    total_gb = props.total_memory / 1e9
    print(f"GPU: {props.name}")
    print(f"VRAM: {total_gb:.1f} GB")
    if total_gb < 16:
        print("WARNING: Below Kaggle T4 baseline. E4B will swap; expect slow inference.")
    elif total_gb < 40:
        print("Kaggle-T4-class. E4B runs comfortably; 31B will not fit. Use E4B.")
    else:
        print("Large GPU. Both E4B and 31B fit. Notebook will pick E4B by default to stay Kaggle-reproducible.")
else:
    print("No CUDA. CPU fallback is not practical for Gemma 4 inference.")"""
)

satellite_md = nbf.v4.new_markdown_cell(
    source="""### Tool 10: Satellite NDVI (the "wow" moment)

Sentinel-2 via Microsoft Planetary Computer. The agent can ask this when a \
farmer's self-report is ambiguous or when independent corroboration is needed. \
This is the capability a RAG-only agent structurally cannot reproduce."""
)

satellite_code = nbf.v4.new_code_cell(
    source="""# Tool 10: Vegetation health via Sentinel-2 NDVI
# Location: Vidarbha cotton-sorghum belt (matches the demo video assets).
veg = TOOL_REGISTRY["get_vegetation_health"](latitude=20.7453, longitude=77.7500, buffer_m=60)
show_result("Vegetation Health — Vidarbha, Maharashtra (Sentinel-2 L2A)", veg)

if "error" not in veg:
    print(f"\\nCurrent NDVI: {veg['current_ndvi']} (observed {veg['current_observation_date']})")
    print(f"Prior NDVI:   {veg['prior_ndvi']} (observed {veg['prior_observation_date']})")
    print(f"Delta:        {veg['ndvi_delta']}  |  Stress: {veg['stress_level']}")
    print(f"Interpretation: {veg['interpretation']}")
    print(f"Source: {veg['source']}")"""
)

postharvest_md = nbf.v4.new_markdown_cell(
    source="""### Tool 11: Post-harvest aflatoxin + drying advisor

20–40% of smallholder grain is lost post-harvest to mould and mycotoxins — \
often more than in-field disease loss combined (APHLIS / FAO). No other \
public agri-agent ships this. Combines hourly weather + FAO/CIMMYT \
moisture thresholds + *Aspergillus flavus* growth window + the IITA \
Aflasafe country registry."""
)

postharvest_code = nbf.v4.new_code_cell(
    source="""# Tool 11: Post-harvest aflatoxin + drying window
# Running for Kumasi cocoa-maize belt (humid coast) for a dramatic signal.
ph = TOOL_REGISTRY["get_postharvest_risk"](
    latitude=6.6885, longitude=-1.6244,
    crop="groundnut", country="ghana", storage_type="traditional",
)
show_result("Post-harvest Risk — Kumasi, Ghana (Open-Meteo + FAO/CIMMYT + IITA)", ph)

if "error" not in ph:
    print(f"\\nRisk tier: {ph.get('risk_tier')}")
    print(f"Days to safe moisture: {ph.get('days_to_safe_moisture')}")
    hc = ph.get('hour_counts', {})
    print(f"Aflatoxin-critical hours (next 7 days): {hc.get('aflatoxin_critical')}")
    print(f"Good drying hours: {hc.get('good_drying')}")
    print(f"Aflasafe eligibility: {ph.get('aflasafe_eligible')}")"""
)

satellite_scenario_md = nbf.v4.new_markdown_cell(
    source="""### Scenario 3: The satellite contradiction (cinematic demo)

A farmer claims their sorghum is fine and is ready to sell. The agent cross-\
checks with Sentinel-2. If the satellite shows declining vegetation, the \
agent pushes back with evidence rather than accepting the self-report."""
)

satellite_scenario_code = nbf.v4.new_code_cell(
    source="""# Scenario 3: Farmer says "fine" — agent checks satellite and contradicts
print("=" * 60)
print("SCENARIO 3: Self-report vs satellite ground-truth")
print('Farmer: "My sorghum is fine, I am ready to sell today."')
print("=" * 60)

import time
t0 = time.time()
result_sat = agent.run(
    query=(
        "My sorghum in Maharashtra is fine, I am ready to sell today. "
        "Can you double-check with satellite data before I call the buyer?"
    ),
    location=(20.7453, 77.7500),
)
elapsed = time.time() - t0

print(f"\\nTools called: {[tc['tool'] for tc in result_sat['tool_calls']]}")
print(f"Turns: {result_sat['turns']} | Time: {elapsed:.1f}s")
print("\\n--- Agent Response ---")
display(Markdown(result_sat['response']))"""
)


def find_cell_index(predicate):
    for i, c in enumerate(nb.cells):
        if predicate(c):
            return i
    return -1


setup_idx = find_cell_index(lambda c: c.cell_type == "code" and "ClimaSense already installed" in c.source)
if setup_idx >= 0:
    nb.cells.insert(setup_idx + 1, preflight)

tools_header_idx = find_cell_index(
    lambda c: c.cell_type == "markdown" and "Real-API Tools Demo" in c.source
)
agentic_header_idx = find_cell_index(
    lambda c: c.cell_type == "markdown" and "Gemma 4 Agentic Loop" in c.source
)
if 0 < tools_header_idx < agentic_header_idx:
    insert_at = agentic_header_idx
    for new_cell in (satellite_md, satellite_code, postharvest_md, postharvest_code):
        nb.cells.insert(insert_at, new_cell)
        insert_at += 1

multilingual_idx = find_cell_index(
    lambda c: c.cell_type == "markdown" and "Multilingual Support" in c.source
)
if multilingual_idx > 0:
    nb.cells.insert(multilingual_idx, satellite_scenario_md)
    nb.cells.insert(multilingual_idx + 1, satellite_scenario_code)

for cell in nb.cells:
    if cell.cell_type == "code" and "Clean up GPU memory" in cell.source:
        cell.source = cell.source.replace(
            f"https://github.com/{REPO}",
            f"https://github.com/{REPO}",
        )

impact_cell_idx = find_cell_index(
    lambda c: c.cell_type == "markdown" and "Impact Summary" in c.source
)
if impact_cell_idx >= 0:
    cell = nb.cells[impact_cell_idx]
    cell.source = cell.source.replace(
        "- **9 real-API tools**",
        "- **11 real-API tools** (weather, historical weather, disease, treatment, market prices, price forecast, soil, planting advisory, climate risk, satellite NDVI, post-harvest aflatoxin)",
    )

nb.metadata.setdefault("kernelspec", {
    "display_name": "Python 3",
    "language": "python",
    "name": "python3",
})

nbf.write(nb, NB_PATH)
print(f"Notebook updated: {len(nb.cells)} cells total.")
for i, c in enumerate(nb.cells):
    first = (c.source or "").strip().split("\n")[0][:70]
    print(f"  [{i:2d}] {c.cell_type:<8} {first}")
