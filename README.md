# ClimaSense 🌾

**Agentic Climate Risk Intelligence for Smallholder Farmers**

*Gemma 4 Good Hackathon — Global Resilience Track*

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Ramesh-Arvind/climasense-/blob/main/notebooks/colab_demo.ipynb)

→ Click the badge above to run the full agent in Google Colab (free T4 GPU). You'll need a Hugging Face token (Colab secret named `HF_TOKEN`) and to have accepted the Gemma 4 license on HF.

## What is ClimaSense?

ClimaSense transforms a farmer's smartphone into an autonomous agricultural intelligence agent. Powered by Gemma 4's multimodal capabilities and native function calling, it provides:

- **Crop Disease Diagnosis** — Photo-based disease detection with treatment recommendations
- **Weather Risk Alerts** — Proactive frost, drought, and flood warnings
- **Market Intelligence** — Optimal harvest timing based on price forecasts
- **Soil Analysis** — Location-based soil assessment and crop recommendations
- **Voice Interaction** — Queries in 140+ languages, works offline

## Architecture

```
Farmer's Phone (Gemma 4 E4B, offline)
    ├── Camera → Crop disease detection
    ├── Microphone → Voice queries (140+ languages)
    └── GPS → Location-aware advice
         │
         ▼
Agentic Reasoning Engine (Gemma 4 26B/31B)
    ├── Tool: Weather API (Open-Meteo)
    ├── Tool: Crop Disease DB (FAO/CABI)
    ├── Tool: Market Prices (FAO GIEWS)
    ├── Tool: Soil Analysis (ISRIC SoilGrids)
    └── Tool: Agricultural Advisory
         │
         ▼
Actionable Advice in Farmer's Language
```

## Quick Start

```bash
pip install -e ".[dev]"
python -m climasense.agent  # Run demo scenarios
```

## Project Structure

```
src/climasense/
├── agent.py           # Core agentic loop with Gemma 4 function calling
├── tools/             # 5 specialized agricultural tools
│   ├── weather.py     # Open-Meteo integration
│   ├── crop_disease.py # Disease diagnosis & treatment
│   ├── market.py      # Commodity prices & forecasts
│   ├── soil.py        # ISRIC SoilGrids integration
│   └── advisory.py    # Planting calendars & risk alerts
├── multimodal/        # Vision + audio processing
├── edge/              # On-device deployment (E4B)
└── eval/              # Evaluation benchmark
```

## Key Gemma 4 Features Used

| Feature | How We Use It |
|---------|--------------|
| Native Function Calling | 9 tool functions for weather, disease, soil, market, advisory |
| Multimodal Vision | Crop photo diagnosis, satellite imagery analysis |
| Audio Input | Voice queries in farmer's native language |
| 128K Context | Full season weather history + agricultural guides |
| Thinking Mode | Multi-factor risk reasoning (weather × soil × crop × market) |
| Edge (E4B) | Offline on Android phones <1.5GB RAM |
| 140+ Languages | Global reach for smallholder farmers |

## Impact

- **500M+** smallholder farmers globally could benefit
- **33%** of global food production comes from small-scale farming
- **20-40%** annual crop losses in developing countries from undiagnosed disease
- **15-25%** potential income improvement from market timing intelligence
