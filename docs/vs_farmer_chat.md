# ClimaSense vs Farmer.Chat — Head-to-Head

Farmer.Chat (Digital Green / Gooey.AI / Karya / AI4Bharat) is the published state of the art for smallholder conversational AI: [arXiv 2409.08916](https://arxiv.org/html/2409.08916v1). 15,000+ farmers across Kenya / India / Ethiopia / Nigeria. The hackathon judges will have read the paper. This table positions ClimaSense honestly against it.

## Architectural comparison

| Axis                                  | Farmer.Chat (arXiv 2409.08916)             | ClimaSense                                              |
|---------------------------------------|--------------------------------------------|---------------------------------------------------------|
| **Architecture**                      | RAG over curated Digital Green video transcripts + KCC logs + factsheets | **Agentic loop** using Gemma 4 native function-calling  |
| **Tools invoked per query**           | 0 (retrieval only, no tool calls)          | **1–5 live API tools** orchestrated per farmer query    |
| **Tool count available**              | 0                                          | **11**                                                  |
| **Model substrate**                   | GPT-4 (filtering / rerank) + GPT-3.5 (synthesis) | **Gemma 4 31B** (reasoning) + **Gemma 4 E4B** (audio), open weights |
| **Modalities**                        | Text + voice (Whisper ASR, Google TTS)     | Text + voice + **vision (leaf photos)** + **satellite (Sentinel-2 NDVI)** |
| **Languages supported**               | 6 (Swahili, Amharic, Hausa, Hindi, Odia, Telugu, English) | 7+ via Gemma 4 multilingual + gTTS                       |
| **Offline capability**                | No — every query requires internet round-trip to OpenAI | **Per-tool cache with TTL + honest freshness labels** when offline |
| **Satellite ground-truth**            | No                                         | **Sentinel-2 NDVI via Microsoft Planetary Computer STAC**, invoked by the agent when the farmer's claim needs verification |
| **Post-harvest / aflatoxin advice**   | Retrieval of static FAO PDF                | **Dynamic tool**: hourly weather + FAO/CIMMYT thresholds + Aflasafe eligibility |
| **Market price integration**          | Mentioned but not tool-invoked             | **WFP HDX live prices** + seasonal forecast tool        |
| **Soil data**                         | Not integrated                             | **ISRIC SoilGrids** with nearest-pixel retry            |
| **Planting calendar**                 | Text-retrieval from extension docs         | **NASA POWER climatology** computed per-farm GPS        |
| **Crop disease diagnosis**            | Retrieval + LLM rephrasing                 | **Symptom → disease matcher** + curated treatment DB + LoRA fine-tune on PlantVillage |

## Performance comparison (self-reported)

| Metric                                | Farmer.Chat                                | ClimaSense (internal eval, 2026-04-19)                  |
|---------------------------------------|--------------------------------------------|---------------------------------------------------------|
| Response accuracy (self-reported)     | 75%                                        | 0.885 composite (10 scenarios, 2-model ensemble)        |
| Swahili-specific accuracy             | ~75% (inferred from paper)                 | **0.678 (behind — closing gap is a P3 in next sprint)** |
| Median response latency               | 9 s                                        | ~35 s for full agentic turn on E4B (2–3 tool calls)     |
| Tool-calling F1                       | N/A (no tools)                             | 0.911                                                   |
| Integration-test pass rate            | Not reported                               | **60/62 = 96.8% on live APIs, 6 real communities**      |
| Field-deployment months               | 12+                                        | 0 (not yet deployed)                                    |
| Real users                            | **15,000+**                                | 0 (field trial pending)                                 |

## Where ClimaSense wins

1. **Agentic tool-calling.** Farmer.Chat cannot verify a farmer's claim against independent data. ClimaSense can: when Amina says *"my maize is fine,"* the agent calls `get_vegetation_health` and corroborates from a Sentinel-2 tile taken 3 days ago.
2. **Satellite ground-truth as a tool, not a dashboard.** TechghilAgro has S2 dashboards in Mauritania. Nobody else has NDVI as a tool the model invokes mid-conversation.
3. **Open weights, reproducible, Apache 2.0.** Farmer.Chat core stack is GPT-4 closed-model + Gooey.AI platform. A researcher at ICRAF cannot deploy Farmer.Chat without signing contracts. ClimaSense ships as a pip-installable package + a Kaggle notebook.
4. **Honest offline labels.** Soil tool returns `"ISRIC SoilGrids v2.0 (nearest valid pixel ~785 m away)"` when the exact coord is in a coverage gap. Farmer.Chat has no equivalent trust signal.
5. **Post-harvest coverage.** Aflatoxin alone is 20-40% of grain loss in SSA. Neither Farmer.Chat nor Plantix nor Google ALU touches post-harvest. ClimaSense does.

## Where Farmer.Chat wins

1. **Real users at scale.** 15K vs 0 is a decisive gap that only a field trial closes.
2. **Swahili accuracy.** 75% vs our 67.8%. We have homework here.
3. **Curated content library.** Digital Green has 10+ years of extension-video transcripts and Karya-annotated KCC logs. Our knowledge base is thinner.
4. **Deployment-hardened voice UX.** They have shipped in 4 countries over a year. Our voice pipeline is test-bench only.

## What this table tells the judges

- ClimaSense is **not** "another Farmer.Chat." The architecture is different (agentic vs RAG), the data coverage is broader (+satellite + post-harvest + soil), and the substrate is open (Gemma 4 vs OpenAI).
- Where we are behind, we are honest about it: no real users yet, Swahili lag, no field trial. The next-sprint plan targets all three (`docs/differentiation_analysis.md`).
- What we bring that nobody ships today: a Gemma-4-native agentic loop that pulls Sentinel-2 satellite imagery and post-harvest aflatoxin risk in response to a voice-driven smallholder question.

## Sources

- Farmer.Chat paper: [arXiv 2409.08916](https://arxiv.org/html/2409.08916v1)
- Farmer.Chat product page: [digitalgreen.org/farmer-chat](https://digitalgreen.org/farmer-chat/)
- Digital Green impact story: [Rockefeller Foundation](https://www.rockefellerfoundation.org/grantee-impact-stories/how-an-ai-based-app-is-bridging-the-information-gap-for-indias-farmers/)
- TechghilAgro (nearest published Sentinel-2-for-smallholder precedent): [Copernicus Success Stories](https://sentinels.copernicus.eu/web/success-stories/-/empowering-agriculture-in-mauritania-with-sentinel-2-the-techghilagro-success-story)
- Plantix (vision-only competitor): [Wikipedia](https://en.wikipedia.org/wiki/Plantix)
- Nuru PlantVillage (on-device disease ID): [Frontiers in Plant Science](https://pmc.ncbi.nlm.nih.gov/articles/PMC7775399/)
- Gemma 4 function-calling format: [Google docs](https://ai.google.dev/gemma/docs/capabilities/text/function-calling-gemma4)
