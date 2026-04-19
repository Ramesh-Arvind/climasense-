# ClimaSense Architecture

## System Overview (Mermaid)

```mermaid
flowchart TB
    subgraph Input["Farmer Input"]
        voice["Voice Query<br/>(Swahili, Hindi, French, English)"]
        text["Text Query"]
        photo["Crop Photo"]
    end

    subgraph Edge["Edge Device (Gemma 4 E4B — 1.5GB int4)"]
        audio_proc["Audio Processing<br/>16kHz mel spectrogram"]
        transcribe["Speech → Text<br/>Language Detection"]
        basic_diag["Basic Diagnosis<br/>(LoRA fine-tuned, 60%→80%+ acc)"]
        cache["Offline Cache Layer<br/>JSON + TTL per tool"]
    end

    subgraph Cloud["Cloud / Kaggle (Gemma 4 31B-IT)"]
        agent["Agentic Reasoning Loop<br/>max 5 turns, thinking mode"]
        fc["Native Function Calling<br/>tool_call → response → model"]
    end

    subgraph Tools["9 Real-API Tools"]
        weather["Weather Forecast<br/>Open-Meteo API"]
        hist_weather["Historical Weather<br/>Open-Meteo Archive"]
        disease["Crop Disease DB<br/>Curated + Wikipedia"]
        treatment["Treatment Recs<br/>Curated + Wikipedia"]
        market["Market Prices<br/>WFP HDX CKAN"]
        price_fc["Price Forecast<br/>WFP Seasonal"]
        soil["Soil Analysis<br/>ISRIC SoilGrids"]
        planting["Planting Advisory<br/>NASA POWER"]
        climate["Climate Risk Alert<br/>NASA POWER + Models"]
    end

    subgraph Output["Farmer Output"]
        text_resp["Text Response<br/>(farmer's language)"]
        voice_resp["Voice Response<br/>gTTS multilingual"]
        advice["Actionable Advice<br/>with risk levels"]
    end

    voice --> audio_proc --> transcribe
    text --> agent
    photo --> basic_diag
    photo --> agent

    transcribe -->|transcribed text| agent
    basic_diag -->|offline diagnosis| cache
    cache -->|cached data when offline| text_resp

    agent --> fc
    fc --> weather & hist_weather & disease & treatment & market & price_fc & soil & planting & climate
    weather & hist_weather & disease & treatment & market & price_fc & soil & planting & climate -->|tool results| fc
    fc -->|"call:response:tool{json}"| agent

    agent --> text_resp
    text_resp --> voice_resp
    agent --> advice

    weather & hist_weather & disease & treatment & market & price_fc & soil & planting & climate -.->|cache results| cache

    style Edge fill:#e8f5e9,stroke:#2e7d32
    style Cloud fill:#e3f2fd,stroke:#1565c0
    style Tools fill:#fff3e0,stroke:#e65100
    style Input fill:#fce4ec,stroke:#c62828
    style Output fill:#f3e5f5,stroke:#6a1b9a
```

## Data Flow

```
Farmer speaks Swahili into phone
    │
    ▼
┌──────────────────────┐
│  Gemma 4 E4B (Edge)  │  ← 1.5GB int4, runs on $100 phone
│  Audio → Text         │
│  Language: Swahili    │
└──────────┬───────────┘
           │ transcribed text
           ▼
┌──────────────────────┐
│  Gemma 4 31B (Cloud) │  ← Reasoning engine
│  System: ClimaSense  │
│  Thinking mode: ON   │
│  Tools: 9 available  │
└──────────┬───────────┘
           │ tool calls
           ▼
┌──────────────────────────────────────────────┐
│  Tool Execution (real APIs, no mock data)     │
│                                               │
│  get_weather_forecast(lat, lon)     → Open-Meteo
│  get_commodity_prices(crop, country) → WFP HDX
│  get_soil_analysis(lat, lon)        → ISRIC
│  get_planting_advisory(crop, lat, lon) → NASA POWER
│  diagnose_crop_disease(symptoms)     → DB + Wikipedia
│  ... (4 more tools)                           │
└──────────────────┬───────────────────────────┘
                   │ tool results (JSON)
                   ▼
┌──────────────────────┐
│  31B Synthesizes      │
│  Farmer-friendly      │
│  advice in Swahili    │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  gTTS (Swahili)      │  ← Voice response
│  MP3 audio output    │
└──────────────────────┘
```

## Offline Architecture

```
┌─────────────────────────────────────────┐
│           Offline Mode (No Internet)     │
│                                          │
│  ┌──────────┐    ┌──────────────────┐   │
│  │  E4B     │───>│  Offline Cache   │   │
│  │  (local) │    │  JSON + TTL      │   │
│  └──────────┘    │                  │   │
│                  │  Weather: 1hr    │   │
│                  │  Soil: 30 days   │   │
│                  │  Prices: 24hr    │   │
│                  │  Disease: 7 days │   │
│                  └────────┬─────────┘   │
│                           │             │
│                  "Last updated: 3h ago" │
│                  + cached tool results  │
└─────────────────────────────────────────┘
```

## Model Deployment Matrix

| Component | Model | Size | Device | Purpose |
|-----------|-------|------|--------|---------|
| Audio transcription | Gemma 4 E4B | 1.5GB (int4) | Phone/Edge | Voice → text |
| Basic crop diagnosis | Gemma 4 E4B + LoRA | 1.6GB | Phone/Edge | Photo → disease |
| Full reasoning | Gemma 4 31B-IT | ~65GB (bf16) | Cloud GPU | Agentic loop |
| Fallback reasoning | Gemma 4 26B-A4B-IT | ~55GB (bf16) | Cloud GPU | MoE fallback |
