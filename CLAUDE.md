# ClimaSense — Gemma 4 Good Hackathon

## Project
Agentic climate risk intelligence for smallholder farmers using Gemma 4's multimodal + native function calling capabilities. Competition deadline: May 18, 2026.

## Architecture
- **Agent core** (`src/climasense/agent.py`): Agentic loop using Gemma 4 native function calling
- **Tools** (`src/climasense/tools/`): Weather, crop disease, market, soil, advisory
- **Multimodal** (`src/climasense/multimodal/`): Vision (crop photos, satellite) + audio (voice queries)
- **Edge** (`src/climasense/edge/`): On-device deployment with Gemma 4 E4B
- **Eval** (`src/climasense/eval/`): Kaggle Benchmarks SDK evaluation

## Engineering Standards
- Follow all standards from `../cognitive_ability/CLAUDE.md` (OOM resilience, checkpointing, tqdm, tmux)
- All Gemma 4 inference wrapped in try/except for OOM
- Temperature=0.0 for deterministic generation
- Function calling uses Gemma 4 native format via `apply_chat_template(tools=...)`
- Checkpoint/resume for any script >5 min
- Default paths: `/kaggle/working/` for outputs, `/kaggle/input/` for data

## Models
- Primary: `gemma-4-31b-it` (Kaggle, cloud)
- Edge: `gemma-4-e4b` (on-device)
- Fallback: `gemma-4-26b-it`

## Key APIs
- Open-Meteo (weather, free, no API key)
- PlantVillage dataset (crop diseases)
- FAO GIEWS (food prices)
- ISRIC SoilGrids (soil data)
