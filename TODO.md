# ClimaSense — Master TODO

Based on gap analysis vs Gemma 3n winners + remaining implementation work.
Priority: 🔴 Critical (blocks winning) | 🟠 High | 🟡 Medium | 🟢 Nice-to-have

---

## Week 1: Close Critical Gaps (Apr 3–10)

### ~~🔴 P1: Offline Caching Layer~~ DONE
- [x] Created `src/climasense/cache/` module (store.py, cached_tool.py)
- [x] `@cached_tool` decorator wraps all 9 tools transparently
- [x] Cache weather, market, soil, advisory, disease data as JSON
- [x] Serve cached data with "Last updated: X ago" when offline
- [x] Tested: all 5 tool types caching correctly
- [ ] Test full agent loop with no internet (airplane mode simulation)

### ~~🔴 P2: Dual-Model Architecture in agent.py~~ DONE
- [x] `agent.py` rewritten with dual-model support
- [x] `audio_model_id` param: separate E4B for audio, 31B for reasoning
- [x] `run(audio=...)` accepts file path, numpy array, or tensor
- [x] Audio → E4B transcription → text query → primary model reasoning
- [x] Tested: MP3 voice → perfect transcription → tool calls → response
- [x] Dual-model tested on separate GPUs: E4B (16GB, GPU0) + 31B (62.5GB, GPU1)
- [x] Full pipeline: audio→E4B(1.2s)→transcription→31B(2.2s)→tool call→TTS
- [x] Total: 78.5GB across 2 GPUs, perfect transcription + correct tool dispatch

### 🔴 P3: Git First Commit + Public Repo
- [ ] Make first commit with all current code
- [ ] Create GitHub repo (public)
- [ ] Push to GitHub
- **Note**: Public commit history required for submission

### ~~🟠 P4: Voice-First UX Polish~~ DONE
- [x] Created `multimodal/tts.py` — gTTS multilingual TTS (en, sw, hi, fr + 50 more)
- [x] `agent.run(tts=True)` generates audio response automatically
- [x] Auto language detection + markdown cleaning for natural speech
- [x] Chunked TTS for long responses
- [x] Voice round-trip tested: audio→E4B(1.2s)→31B(2.2s)→TTS→MP3
- [ ] Add streaming-like response display
- [ ] Test with real non-English farmer audio (gTTS-generated tested OK)

---

## Week 2: Real User Story + Fine-tuning (Apr 11–17)

### ~~🔴 P5: Named Human Beneficiary / Real User Story~~ DONE
- [x] Created `src/climasense/personas.py` with Amina Otieno persona
  - Kadongo village, Kisumu County, Kenya; 34yo mother of 3
  - 0.8ha farm: maize, tomatoes, kale, beans; rain-fed only
  - 6 specific challenges (30% crop loss, 22km to extension officer, etc.)
  - Her own quote about climate unpredictability
- [x] 5 demo scenarios in Swahili with English translations + expected tools
- [ ] Find real farmer/NGO to test with and get feedback quote

### ~~🟠 P6: PlantVillage Real Crop Disease Images~~ DONE
- [x] Downloaded PlantVillage dataset (15 classes, ~20K images)
- [x] Benchmarked zero-shot E4B: **20% accuracy** (only "healthy" reliable)
- [x] LoRA fine-tuned E4B: **60% accuracy** (3x improvement, 13 min training)
- [x] Per-class: Bacterial Spot 100%, YLCV 100%, Healthy 100%, Leaf Mold 80%
- [x] LoRA adapter saved: `models/plantvillage_lora/` (54MB)
- [x] Script: `scripts/finetune_vision.py` (ClippableLinear workaround for PEFT)
- [ ] Curate 10–20 best example images for demo
- [ ] Train longer / more data for higher accuracy on blight classes

### ~~🟠 P7: Fine-tuning Improvements~~ DONE
- [x] Train with more per-class samples (100→300) and more epochs (3→8)
- [x] All 15 classes including Potato and Pepper already in dataset
- [x] Upgraded to r=32 LoRA with MLP layers (q/k/v/o + gate/up/down)
- [x] Added cosine LR scheduler
- [x] Training complete: loss 0.1263 → **0.0004** (315x improvement)
- [x] 4336 training samples, 436 val, 15 classes, ~100 min on H200
- [x] Adapter saved: `models/plantvillage_lora_v2/`
- [ ] Run accuracy benchmark on validation set to confirm >80%

---

## Week 3–4: Demo Construction (Apr 18–May 1)

### ~~🔴 P8: Kaggle Notebook Demo~~ DONE
- [x] Created `notebooks/climasense_demo.ipynb` (23 cells, 8 sections)
- [x] Full pipeline: tools → agent loop → multilingual → voice → cache → edge
- [x] Shows all 9 real-API tools with live data
- [x] Voice round-trip with TTS audio playback (IPython.display.Audio)
- [x] Auto-selects model based on GPU size (31B/E4B)
- [x] Amina persona framing throughout
- [ ] Test on actual Kaggle free GPU tier
- [ ] Add crop photo disease diagnosis cell (needs image upload)

### ~~🟡 P9: Architecture Diagram~~ DONE
- [x] Created `docs/architecture.md` with Mermaid flowchart
- [x] Full pipeline: Voice → E4B → 31B → 9 tools → TTS
- [x] Offline cache layer diagram
- [x] Edge deployment path + model deployment matrix
- [x] Rendered to PNG (354KB) + SVG (143KB) + data_flow.png (149KB)

### ~~🟠 P10: Multilingual Demo~~ DONE
- [x] Created `scripts/multilingual_demo.py` with 12 scenarios
- [x] Tested Swahili (4 scenarios), Hindi (3), French (3), English (2)
- [x] All 17/17 tool calls successful across all languages
- [x] TTS audio generated for all 12 queries (data/multilingual_demo/audio/)
- [x] Language detection: 4/4 languages detected correctly
- [x] Results saved: data/multilingual_demo/multilingual_results.json

### ~~🟡 P11: Evaluation Benchmark Update~~ DONE
- [x] Expanded `eval/benchmark.py` to 20 scenarios (5 crops × 4 regions × EN/SW)
- [x] Updated all tool signatures (lat/lon, crop, country params)
- [x] Added per-crop, per-region, per-language breakdown in scoring
- [x] Added `print_results_table()` for formatted writeup output
- [x] Full eval with 31B model: **0.885 composite, 0.911 tool F1** (20/20 scenarios)
  - Best: weather_advisory (1.0), market (0.973), planting (0.954)
  - By region: SE Asia 1.0, S Asia 0.93, W Africa 0.96, E Africa 0.79
  - By language: English 0.954, Swahili 0.678 (room for improvement)

### ~~🟡 P12: Edge Deployment Demo~~ DONE
- [x] Rewrote `edge/deploy.py` with real int4 quantization (bitsandbytes NF4 + double quant)
- [x] EdgeModel class: load, generate, profile, benchmark methods
- [x] Benchmarked on H200: 23.4 tok/s, 5.6s avg response, 9.3GB (bnb int4)
- [x] Full LiteRT-LM + AI Edge Gallery deployment guide with code samples
- [x] Documented offline vs online tool split + cache TTLs
- [x] Results saved: logs/edge_benchmark.json

---

## Week 5–6: Polish and Submit (May 2–18)

### 🔴 P13: 2-Minute Video Demo
**Gap**: Competition centerpiece. "Potential to go viral" is valued.
- [ ] Script the video:
  1. Open: "Amina" scenario — farmer speaking Swahili into phone (10s)
  2. Show tool calls happening in real-time (15s)
  3. Show response in Swahili with audio (10s)
  4. Disease diagnosis from real leaf photo (15s)
  5. Architecture overview (20s)
  6. Impact statistics + offline capability (15s)
  7. Close: back to human story (10s)
- [ ] Record with screen capture + voice narration
- [ ] Edit to exactly 2 minutes (only first 2 min judged)
- [ ] Make it emotionally grounded — human story, not just tech

### 🔴 P14: Writeup Polish
**Gap**: Winners documented failures, not just successes.
- [ ] Update `docs/writeup.md` with:
  - Named beneficiary story
  - Architecture diagram
  - Real benchmark results
  - 10+ engineering challenges solved:
    1. pyproject.toml build backend fix
    2. Gemma 4 tool call parser format (`<|"|>` tokens)
    3. ISRIC SoilGrids 503 errors → regional fallback
    4. `torch_dtype` deprecation → `dtype`
    5. 46.9s 31B model load time → optimization
    6. WFP HDX CSV parsing edge cases
    7. Audio pipeline: `audio=` not `audios=` parameter name
    8. Swahili TTS audio quality issues
    9. Offline caching strategy
    10. Dual-model GPU placement
  - Impact framing: 500M farmers, $2.6T sector
  - Offline-first story
- [ ] Format as Kaggle Writeup (rich, multimedia)

### 🔴 P15: Final Submission
- [ ] Test all 9 tools one final time
- [ ] Ensure Kaggle notebook runs clean on free GPU
- [ ] Submit Kaggle writeup + video + notebook
- [ ] Deadline: May 18, 2026 23:59 UTC

---

## Status Key
- [ ] Not started
- [x] Completed
- [~] In progress / partial

## Already Completed
- [x] Project setup (git, venv, pyproject.toml fix)
- [x] All 9 tools implemented with real APIs
- [x] Weather tool (Open-Meteo) — tested, working
- [x] Crop disease tool (curated DB + Wikipedia) — tested, working
- [x] Market tool (WFP HDX) — tested, working
- [x] Soil tool (ISRIC + fallback) — tested, working
- [x] Advisory tool (NASA POWER) — tested, working
- [x] Agent.py — correct Gemma 4 tool call parser, prompt-based generation
- [x] E4B model loading + text generation — tested, 16.8GB VRAM
- [x] E4B function calling — tested, works with 9 tools
- [x] E4B vision — tested with synthetic image
- [x] 31B model loading + text generation — tested, 50GB on 2 GPUs
- [x] E4B audio pipeline — tested, English transcription perfect
- [x] audio.py rewritten — loads files, correct processor call
- [x] Full end-to-end agent test — 3 tools called, farmer-friendly response
- [x] Offline caching layer — `@cached_tool` decorator on all 9 tools, JSON cache with TTL
- [x] Dual-model architecture — agent.py supports E4B audio + 31B reasoning
- [x] Audio → Agent pipeline — MP3 voice → transcription → tool calls → response (tested)
- [x] PlantVillage dataset downloaded (15 classes, ~20K images)
- [x] Zero-shot vision benchmark: 20% accuracy
- [x] LoRA fine-tuning: 20% → 60% accuracy in 13 min (PEFT + ClippableLinear workaround)
- [x] Fine-tuned adapter saved at models/plantvillage_lora/
