# The "Satellite Moment" — Demo Video Shot Script

The scene the hackathon writeup is built around. A farmer claims the crop is fine; the agent calls a tool; a satellite image 18 days old contradicts the claim. Captured from a real `get_vegetation_health` call — no mockups, no stock footage.

## Captured tool output (live, `src/climasense/tools/satellite.py`)

Location: Vidarbha cotton–sorghum belt, Maharashtra, India — `lat=20.7453, lon=77.7500`.

| Field                      | Value                                      |
|----------------------------|--------------------------------------------|
| `current_ndvi`             | **0.100**                                  |
| `current_observation_date` | **2026-03-26** (18 days before demo)       |
| `prior_ndvi`               | **0.168**                                  |
| `prior_observation_date`   | 2026-01-25                                 |
| `ndvi_delta`               | **−0.068** (≈40% loss in 2 months)         |
| `stress_level`             | `severe_stress`                            |
| `interpretation`           | *"Bare soil or severe stress — drought, disease, or failed crop likely"* |
| `source`                   | `Sentinel-2 L2A via Microsoft Planetary Computer (observed 2026-03-26)` |
| `cloud_cover_pct`          | 0.0                                        |
| `patch_hectares`           | 1.44                                       |

Saved images:
- `ndvi_20.7453_77.7500_now.png` (2026-03-26, NDVI 0.10)
- `ndvi_20.7453_77.7500_prior.png` (2026-01-25, NDVI 0.17)

## Four-beat script (≈ 45 seconds of video)

### Beat 1 — Farmer (3 s)
> *(phone recording, Marathi voice, English subtitle)*
> **"Saheb, maze sorghum theek aahe. Mi ajach vikaycha vichar karto."**
> "My sorghum looks fine. I'm thinking of selling today."

### Beat 2 — Agent thinks (5 s, on-screen chain-of-thought)
> `<tool_call>get_vegetation_health(lat=20.7453, lon=77.7500)</tool_call>`
>
> Text on screen: "ClimaSense is cross-checking the farmer's field against a Sentinel-2 satellite image."

### Beat 3 — The reveal (18 s)
Split screen.

**Left — Jan 25:** `ndvi_20.7453_77.7500_prior.png` with label *"NDVI 0.17 — already stressed, 2 months ago."*

**Right — Mar 26:** `ndvi_20.7453_77.7500_now.png` with label *"NDVI 0.10 — further decline, 18 days ago."*

Overlay ticker:
> *"Sentinel-2 L2A via Microsoft Planetary Computer (observed 2026-03-26). Patch: 1.44 ha. Cloud cover: 0%."*

### Beat 4 — Agent responds (19 s)
> *(Gemma 4 E4B voice, English then Marathi dub)*
> "Ramesh-ji, before you sell, there is something I want you to see.
> A satellite image of your field from 18 days ago shows your sorghum
> is under severe stress — the vegetation index dropped from 0.17 in
> January to 0.10 in March. That is a 40% decline.
> **This is what I see from Sentinel-2 — not what you might see walking the field.**
> It could be drought, disease, or a failed patch. Before setting a price,
> please walk the eastern edge, check the root zone, and message me a photo.
> If the grain is already damaged, selling it mixed with healthy grain
> could fail a buyer's moisture or aflatoxin test — and ruin your whole sale."

## Why this scene works

- **Honest freshness label.** The agent names the date (18 days ago), the source (Sentinel-2), and the patch size (1.44 ha) — not a black-box "AI says."
- **Contradiction, not confirmation.** Farmer.Chat's RAG can only retrieve advice that matches what the farmer said. ClimaSense can push back because it has a tool that pulls ground-truth imagery.
- **Zero fabrication.** The NDVI values, the dates, the interpretation string — all live output captured from `python -m climasense.tools.satellite` on 2026-04-19.
- **One-shot capable.** No cutaways. The split-screen NDVI images plus the agent's spoken contradiction fit in a single unbroken shot, which is the cinematic register the hackathon judges associate with "real demo, not a mockup."

## Filming notes

- Record the agent voice with **Gemma 4 E4B** (`google/gemma-4-E4B-it`) so the voice is the actual submission model, not a voice-over read by a human.
- Use the PNGs at native 512×512 — they are already Sentinel-2 true-scale NDVI, no resampling.
- Caption in English (primary) and Marathi (field language).
- Keep the "18 days ago" callout visible for a full 3 seconds — judges need time to register that the timestamp is earned, not invented.

## Alternate location if Vidarbha is politically sensitive

If the demo narration needs to avoid a region associated with farmer suicides, re-run the tool at:
- Kisumu maize belt: `(-0.0917, 34.7680)` — NDVI 0.07 severe, but delta is near-zero (less dramatic).
- Kumasi cocoa belt: `(6.6885, -1.6244)` — NDVI 0.09 severe, stable.

Vidarbha remains the most visually dramatic choice because of the -0.068 delta.
