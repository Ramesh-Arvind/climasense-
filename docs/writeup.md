# ClimaSense: Agentic Climate Risk Intelligence for Smallholder Farmers

## The Problem

Over 500 million smallholder farmers feed a third of the world's population, yet they are the most vulnerable to climate change. A single unexpected frost, pest outbreak, or drought can destroy an entire season's income. These farmers typically lack access to timely weather intelligence, disease diagnostics, and market information — all of which exist digitally but remain inaccessible due to connectivity, language, and literacy barriers.

## Our Solution

**ClimaSense** is an autonomous agricultural intelligence agent powered by Gemma 4 that transforms a farmer's smartphone into a personal agronomist. Unlike traditional chatbots, ClimaSense is an *agentic* system that proactively monitors conditions and chains multiple tools to deliver comprehensive, actionable advice.

### How It Works

A farmer in rural Tanzania photographs their wilting cassava and speaks a question in Swahili. ClimaSense:

1. **Sees** the crop photo via Gemma 4's vision capabilities, identifying early signs of Cassava Mosaic Disease
2. **Hears** the voice query in Swahili, understanding the farmer's specific concern
3. **Reasons** using thinking mode to connect symptoms with environmental factors
4. **Acts** by autonomously calling tools: weather API reveals 3 weeks of drought, soil analysis shows low organic carbon, and the disease database confirms whitefly-transmitted mosaic virus
5. **Advises** in Swahili: immediate whitefly control with neem oil, irrigation recommendations, and a market timing suggestion to sell remaining healthy tubers before prices drop

All of this happens in a single interaction, with the edge model (Gemma 4 E4B) handling basic diagnosis offline, and the full model (26B/31B) providing comprehensive analysis when connectivity is available.

## Architecture

ClimaSense leverages every major Gemma 4 capability:

- **Native Function Calling**: 5 specialized tools (weather, crop disease, soil, market prices, agricultural advisory) defined as Python functions with type hints, automatically converted to Gemma 4's tool schema
- **Multimodal Input**: Crop photos for disease diagnosis + satellite imagery for drought detection + voice queries in 140+ languages
- **128K Context**: Ingests an entire growing season's weather history alongside regional agricultural guidelines for informed reasoning
- **Thinking Mode**: Complex multi-factor risk assessment (weather × soil × crop stage × market) using Gemma 4's internal reasoning
- **Edge Deployment**: Gemma 4 E4B runs offline on mid-range Android phones (<1.5GB RAM) via LiteRT with int4 quantization

## Impact

ClimaSense addresses climate resilience at the intersection of three critical challenges:

1. **Climate Adaptation**: Real-time risk alerts (frost, drought, flooding) with crop-specific mitigation advice
2. **Food Security**: Disease diagnosis prevents the 20-40% crop losses that occur annually in developing countries
3. **Economic Empowerment**: Market timing intelligence helps farmers sell at optimal prices, improving income by an estimated 15-25%

The system is designed for the hardest deployment contexts: offline-capable, voice-driven, multilingual, and runnable on the cheapest smartphones. By building on Gemma 4's Apache 2.0 license, ClimaSense can be freely adapted by agricultural extension services, NGOs, and governments worldwide.

## Evaluation

We evaluate ClimaSense across 6 curated scenarios spanning weather advisory, disease diagnosis, market timing, soil assessment, multi-risk analysis, and comprehensive season planning. Metrics include tool selection accuracy (F1), response keyword coverage, actionable advice rate, and composite scoring weighted by scenario difficulty.

## Technical Stack

- **Model**: Gemma 4 31B-IT (cloud) + E4B (edge)
- **Inference**: vLLM on Kaggle, LiteRT-LM on device
- **APIs**: Open-Meteo (weather), ISRIC SoilGrids (soil), FAO GIEWS (prices)
- **Framework**: Python, transformers, torch
- **License**: Apache 2.0 (matches Gemma 4)
