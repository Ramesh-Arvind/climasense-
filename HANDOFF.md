# ClimaSense — Handoff Notes (2026-04-04)

## Session 2 (Apr 4) — Major Progress

### Completed This Session

**P4: Voice-First UX**
- Created `src/climasense/multimodal/tts.py` — gTTS multilingual TTS (en, sw, hi, fr)
- `agent.run(tts=True)` generates audio response automatically
- Auto language detection + markdown cleaning for natural speech
- Chunked TTS for long responses

**P5: Named Beneficiary**
- Created `src/climasense/personas.py` — Amina Otieno, Kadongo, Kisumu County, Kenya
- 5 demo scenarios in Swahili with English translations + expected tools

**P7: Fine-tuning v2**
- Upgraded: r=16→32, 100→300/class, 3→8 epochs, MLP layers, cosine LR
- Loss: 0.1263 → **0.0004** (315x improvement)
- Adapter: `models/plantvillage_lora_v2/` (4336 train samples, 15 classes)

**P8: Kaggle Notebook**
- Created `notebooks/climasense_demo.ipynb` (23 cells, 8 sections)
- Full pipeline demo: tools → agent → multilingual → voice → cache → edge

**P9: Architecture Diagrams**
- `docs/architecture.png` (354KB) — full system diagram with matplotlib
- `docs/data_flow.png` (149KB) — 6-step pipeline flow
- `docs/architecture.svg` (143KB)
- `docs/architecture.md` — Mermaid source

**P10: Multilingual Demo**
- `scripts/multilingual_demo.py` — 12 scenarios across 4 languages
- 17/17 tool calls successful, 12/12 TTS audio files generated

**P11: Evaluation Benchmark**
- Expanded to 20 scenarios (5 crops × 4 regions × EN/SW)
- **Results: 0.885 composite score, 0.911 tool F1**
- Weather advisory: 1.0, Market: 0.973, Planting: 0.954
- Results: `logs/eval_results.json`

**P12: Edge Deployment**
- Rewrote `edge/deploy.py` with real int4 quantization benchmarks
- Benchmarked: 23.4 tok/s, 5.6s avg response on H200
- Full LiteRT-LM + AI Edge Gallery deployment guide

**Dual-Model Test**
- E4B (16GB, GPU0) + 31B (62.5GB, GPU1) on separate GPUs
- Full pipeline: audio(1.2s) → transcription → tool call(2.2s) → TTS
- 78.5GB total across 2 GPUs

### Verification
- All 9 module test suites pass (TTS, personas, tools, cache, eval, edge, agent, audio, vision)
- All 9 tools working with real APIs (9/9)

---

# Session 1 (Apr 3) — Foundation

## What's Been Done This Session

### 1. Project Setup
- **Git repo initialized** in `/data/home/rnaa/gemma4_hackathon/`
- `.gitignore` created (excludes pycache, model weights, logs, data, venv)
- **Virtual environment** at `.venv/` with Python 3.12
- **Fixed `pyproject.toml`** — build backend was wrong (`setuptools.backends._legacy:_Backend` → `setuptools.build_meta`)
- Installed: `transformers==5.5.0`, `torch==2.11.0+cu130`, `accelerate==1.13.0`, `torchvision==0.26.0`, `requests`, `Pillow`, `soundfile`, `librosa`
- Package installed in editable mode (`pip install -e .`)

### 2. All 9 Tools Tested and Working

| Tool | API Source | Status | Notes |
|------|-----------|--------|-------|
| `get_weather_forecast` | Open-Meteo (live) | WORKING | Real 7-day forecasts with agricultural risk flags |
| `get_historical_weather` | Open-Meteo Archive (live) | WORKING | Historical stats (frost days, dry days, etc.) |
| `diagnose_crop_disease` | Curated DB + Wikipedia API | WORKING | 8 diseases in DB + Wikipedia fallback for unknowns |
| `get_treatment_recommendation` | Curated DB + Wikipedia API | WORKING | Detailed treatment steps + Wikipedia fallback |
| `get_commodity_prices` | WFP HDX CKAN API (live) | WORKING | Real food prices from 24 countries (Africa + South Asia) |
| `get_price_forecast` | WFP historical seasonal | WORKING | Seasonal patterns from real historical data |
| `get_soil_analysis` | ISRIC SoilGrids + fallback | WORKING | ISRIC API is 503 intermittently; regional fallback added |
| `get_planting_advisory` | NASA POWER Climatology (live) | WORKING | Data-driven planting windows from real climate data |
| `get_climate_risk_alert` | NASA POWER + growth models | WORKING | Real climate data + crop growth stage vulnerability |

### 3. Tools Upgraded from Static → Real APIs

- **Market prices**: Was simulated with `random.seed()` → Now uses **WFP Food Price Monitoring via HDX** (real prices from 24 countries)
- **Advisory/Planting**: Was hardcoded 3-zone calendar → Now uses **NASA POWER Climatology** (location-specific climate data, any point on Earth)
- **Crop disease**: Was 6-disease keyword matcher → Now 8 diseases + **Wikipedia MediaWiki API** for broader coverage
- **Soil**: Added **regional fallback data** (East Africa, West Africa, South Asia) when ISRIC API is down

### 4. Gemma 4 Model Testing

#### GPU Setup
- **3x NVIDIA H200 NVL** (141GB HBM3e each)
- GPU 0: ~50GB used (has room for models)
- GPU 1: VLLM server running (~124GB used) — DO NOT USE
- GPU 2: Free (best for testing)

#### Model Compatibility Matrix
| Feature | E2B (2B) | E4B (4B) | 26B-A4B (MoE) | 31B (Dense) |
|---------|----------|----------|---------------|-------------|
| Text | Yes | Yes | Yes | Yes |
| Vision | Yes | Yes | Yes | Yes |
| **Audio** | **Yes** | **Yes** | **No** | **No** |
| Function Calling | Yes | Yes | Yes | Yes |
| Context | 128K | 128K | 256K | 256K |
| VRAM (bf16) | ~10GB | ~18GB | ~55GB | ~65GB |

#### Correct HuggingFace Model IDs
- `google/gemma-4-E4B-it` (NOT `gemma-4-e4b`)
- `google/gemma-4-31B-it` (NOT `gemma-4-31b-it`)
- `google/gemma-4-26B-A4B-it` (NOT `gemma-4-26b-it`)
- `google/gemma-4-E2B-it`

#### All 4 models are cached locally at:
`/data/home/rnaa/.cache/huggingface/hub/models--google--gemma-4-*`

#### What Was Tested Successfully
1. **E4B text generation** — Working (16.8GB VRAM)
2. **E4B function calling** — Working! Model correctly calls tools using `<|tool_call>call:func{args}<tool_call|>` format
3. **E4B vision** — Working (model analyzed a synthetic test image correctly)
4. **E4B full agentic loop** — Working! Model calls tools → gets real results → synthesizes farmer-friendly response
5. **31B text generation** — Working (loaded on GPUs 0+2, ~50GB, 46.9s load, 5.1s generation)
6. **E4B audio** — WORKING! English transcription perfect. Uses `processor(text=..., audio=[array])` with `input_features` tensor

### 5. Agent Architecture Updated (`agent.py`)

Key changes made:
- **Tool call parser fixed** — Now handles Gemma 4's actual format: `key:<|"|>str_val<|"|>` for strings, `key:number` for numbers
- **`dtype` instead of `torch_dtype`** — `torch_dtype` is deprecated in transformers 5.5
- **Prompt-based generation** — Switched from message-dict approach to text-prompt approach for proper tool response handling
- **Correct Gemma 4 tool response format** — Uses `call:response:func_name{json}<tool_response|>` followed by `<|turn>model`
- **Default model ID** updated to `google/gemma-4-31B-it` (correct casing)

### 6. Recommended Architecture: Two Models
- **Primary agent**: `gemma-4-31B-it` — reasoning, vision, function calling (9 tools)
- **Audio handler**: `gemma-4-E4B-it` — farmer voice queries → text transcription
- Both fit on a single H200 (~80GB combined in bf16)

## Audio Testing Results

### audio.py Rewritten (was scaffold, now fully working)
- Loads audio from files (WAV/MP3/FLAC) or numpy arrays
- Resamples to 16kHz, converts stereo→mono
- Uses correct `processor(text=..., audio=[array], sampling_rate=16000)` call
- Two functions: `process_voice_query()` (full analysis) and `transcribe_audio()` (text only)

### Test Results
- **English speech**: PERFECT transcription — "My tomato plants have brown spots on the leaves. What disease could this be? Should I spray something?" Language=English, Urgency=Concerning
- **Swahili speech**: Pipeline works but gTTS-generated Swahili confused the model (output Korean). Needs real farmer speech samples for proper testing.
- **Audio features**: Correctly generates `input_features` tensor (mel spectrogram) — shape `[1, 772, 128]` for 7.7s audio

### Test audio files generated
- `data/test_farmer_query.mp3` — English farmer asking about tomato disease
- `data/test_farmer_swahili.mp3` — Swahili farmer query

## What's NOT Done Yet

1. **Git first commit** — repo initialized but no commits
3. **Dual-model architecture in agent.py** — agent.py uses one model; need to add E4B audio preprocessing
4. **Kaggle notebook** — no demo notebook for submission
5. **PlantVillage real images** — tested with synthetic image, need real crop disease photos
6. **Multilingual demo** — not tested yet (Gemma 4 supports 140+ languages)
7. **Edge deployment** — `edge/deploy.py` is scaffold only
8. **Evaluation benchmark** — `eval/benchmark.py` needs updating for new tool signatures
9. **Video demo** — 2-minute competition video not started
10. **Writeup polish** — `docs/writeup.md` needs updating with real results

## Full End-to-End Test Result

Tested with this scenario:
> "I want to plant maize this season. Is now a good time? What are the current market prices? And check my soil quality." (Location: Nairobi, Kenya)

The agent:
1. Autonomously called 3 tools: `get_planting_advisory`, `get_commodity_prices`, `get_soil_analysis`
2. Got real data from NASA POWER, WFP HDX, and soil analysis
3. Synthesized a comprehensive response with planting advice, market analysis, and soil assessment
4. Response was farmer-friendly with clear sections, action items, and practical advice

## Competition Context
- **Gemma 4 Good Hackathon** — $200K prize, 5 tracks
- **Our track**: Global Resilience (zero previous winners — wide open!)
- **Deadline**: May 18, 2026 (~6.5 weeks)
- **Only 7 teams enrolled** as of April 3
- **Judging**: Impact (40%), Technical Depth (30%), Creativity (20%), Presentation (10%)
- **Submission**: Kaggle Writeup + 2-min video demo

## File Structure
```
gemma4_hackathon/
├── CLAUDE.md                    # Engineering standards
├── HANDOFF.md                   # This file
├── README.md                    # Project overview
├── pyproject.toml               # Package config (fixed build backend)
├── .gitignore                   # Git ignores
├── src/climasense/
│   ├── __init__.py
│   ├── agent.py                 # Agentic loop (UPDATED: correct Gemma 4 format)
│   ├── tools/
│   │   ├── __init__.py          # Tool registry (9 tools)
│   │   ├── weather.py           # Open-Meteo API (real)
│   │   ├── crop_disease.py      # Curated DB + Wikipedia API (UPDATED)
│   │   ├── market.py            # WFP HDX API (REWRITTEN: real prices)
│   │   ├── soil.py              # ISRIC API + regional fallback (UPDATED)
│   │   └── advisory.py          # NASA POWER API (REWRITTEN: real climate data)
│   ├── multimodal/
│   │   ├── vision.py            # Scaffold
│   │   └── audio.py             # Scaffold
│   ├── edge/
│   │   └── deploy.py            # Scaffold
│   └── eval/
│       └── benchmark.py         # Needs updating
├── config/
│   └── tools_schema.json        # Function calling schemas
├── docs/
│   ├── research.md              # Competition analysis
│   └── writeup.md               # Draft writeup
├── data/
│   └── test_leaf.png            # Synthetic test image
├── notebooks/                   # Empty (need Kaggle notebook)
├── tests/                       # Empty
└── logs/                        # Empty
```
