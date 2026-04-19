# ClimaSense Competitive Landscape & Judge's Critique

*Prepared for the Gemma 4 Good Hackathon — Global Resilience Track. April 19, 2026.*

Judges on this panel have seen the agri-advisory space for years. Many of them have personally reviewed the Farmer.Chat arXiv paper, the PlantVillage Nuru deployment in sub-Saharan Africa, and Google's own ALU / AnthroKrishi work in India. "AI for smallholder farmers" is the most over-entered domain in every AI-for-good hackathon — which means this report is as much about **where ClimaSense must not sound like everyone else** as it is about what to build.

This document has three parts. Part 1 maps the competitor field with sourced citations. Part 2 extracts what actually won the Gemma 3n Impact Challenge (the direct predecessor). Part 3 is a ruthless judge's critique of ClimaSense, with three specific, effort-scoped improvements.

---

## Part 1: The Agri-Advisor Landscape — Who Has Done What

### Crop-disease diagnosis (vision)

**Plantix (PEAT GmbH, Berlin, acquired by HELM AG in May 2023).** The single most-downloaded agri-tech app globally. Convolutional-net image recognition on 800 symptoms across 60 crops, trained on an internal labelled dataset enriched by ICRISAT. Works in 18+ languages, >100 million crop queries answered, >10 M MAU in India. **Tech stack: TensorFlow, server-side inference with thumbnail upload; tight community feedback loop.** [plantix.net](https://plantix.net/en/blog/machine-learning-helps-small-farmers-identify-plant-pests-and-diseases/) / [Wikipedia](https://en.wikipedia.org/wiki/Plantix) / [GSMA case study](https://www.gsma.com/solutions-and-impact/connectivity-for-good/mobile-for-development/programme/agritech/detecting-and-managing-crop-pests-and-diseases-with-ai-insights-from-plantix/). **Limitation ClimaSense can exploit:** Plantix is single-modality (vision only) and requires an internet round-trip. It cannot weigh disease evidence against weather, soil, or market reality; it cannot hear a farmer narrate symptoms over the phone.

**PlantVillage Nuru (Penn State / FAO / IITA / CIMMYT).** On-device CNN for cassava CBSD / CMD / green-mite detection. Trained on 2,756 cassava images. **Runs 100% offline on Android**, demonstrated in field trials reporting **130–530% yield improvement** through timely intervention. Swahili voice support, integrated with iShamba SMS. [IITA announcement](https://www.iita.org/news-item/african-farmers-get-new-help-against-cassava-diseases-nuru-their-artificially-intelligent-assistant/) / [Frontiers in Plant Science paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC7775399/) / [PSU $4.96M grant announcement](https://www.psu.edu/news/research/story/plantvillage-receives-496-million-grant-combat-crop-loss-africa) / [Google blog](https://blog.google/innovation-and-ai/products/ai-takes-root-helping-farmers-identity-diseased-plants/). **Limitation:** narrow crop coverage (cassava-focused), not a reasoning agent. It identifies and advises, but cannot orchestrate multi-tool reasoning the way a language-model agent can.

### Conversational advisors (text/voice chat)

**Farmer.Chat (Digital Green + Gooey.AI + Karya + AI4Bharat).** The gold-standard baseline to beat. **RAG over curated Digital Green video transcripts + KCC logs + government factsheets**, **GPT-4 for filtering/reranking and GPT-3.5 for synthesis**, Whisper ASR, Google Translate, and TTS. Six languages (Swahili, Amharic, Hausa, Hindi, Odia, Telugu, English). Deployed in Kenya, India, Ethiopia, Nigeria with **>15,000 farmers and >300,000 queries**. [Digital Green page](https://digitalgreen.org/farmer-chat/) / [arXiv paper 2409.08916](https://arxiv.org/html/2409.08916v1) / [CGAP blog on women farmers](https://www.cgap.org/blog/beyond-chat-ai-powered-advice-for-women-farmers). Reported **75% query response accuracy**, 9-second median latency, Flesch-Kincaid 60–80 readability. **Documented limitations from their own paper:** 66% of unanswered queries stem from content gaps, 23% out-of-scope, 11% unsupported crops; only 53% of user prompts are "clearly" articulated on first try. **No agentic tool-calling** — it's strictly retrieval-then-generate. **No offline operation** — requires internet for every query. **No multimodal vision.** **No satellite ground-truthing.** These are the four concrete gaps ClimaSense must weaponise in its writeup.

**Jugalbandi (Microsoft + AI4Bharat + OpenNyAI).** WhatsApp-based voice/text bot for Indian government schemes, not strictly agri. AI4Bharat ASR → Bhashini MT → Azure OpenAI RAG → AI4Bharat TTS. 10 Indian languages, 171 programs indexed. [Microsoft Source Asia feature](https://news.microsoft.com/source/asia/features/with-help-from-next-generation-ai-indian-villagers-gain-easier-access-to-government-services/) / [MediaNama overview](https://www.medianama.com/2023/06/223-jugalbandi-chatbot-rural-india-what-to-know/) / [open-source repo](https://github.com/OpenNyAI/jugalbandi_chatbot). **Limitation:** purely retrieval, no tool-calling agentic loop, no crop-specific reasoning.

**KissanGPT / KissanAI.** GPT-3.5 + Whisper wrapper for Indian farmers. 10 languages. **Literal ChatGPT-for-farmers** — no specialised fine-tune documented publicly. [IndiaAI article](https://indiaai.gov.in/article/how-kissangpt-helps-indian-farmers-earn-profit) / [kissan.ai](https://kissan.ai/). **Limitation:** thin technical moat, no offline.

**ITC Krishi Mitra / MAARS.** AI co-pilot in 8 languages, answers weather/price/scheme queries. Part of ITC's "phygital" extension ecosystem. [newkerala.com report](https://www.newkerala.com/news/a/itc-expand-ai-services-rural-communities-organic-farmers-750.htm). **Limitation:** tied to ITC's supply chain, closed ecosystem, not open source.

**FarmerAI (Safaricom + Opportunity International, Feb 2025).** WhatsApp/SMS chatbot over DigiFarm. Pilot with 800–1,000 Kenyan potato farmers aligned to a crop cycle. [Opportunity press release](https://opportunity.org/news/press-releases/opportunity-international-and-safaricom-launch-new-ai-chatbot-for-smallholder-farmers) / [Safaricom release](https://www.safaricom.co.ke/media-center-landing/press-releases/opportunity-international-safaricom-launch-new-ai-chatbot-for-smallholder-farmers). **Limitation:** narrow pilot, single crop, no multimodal, no documented offline support.

**iShamba (Kenya).** Pre-LLM SMS/IVR platform, 550,000+ farmers. English/Swahili/local languages; call-center staff backstop the SMS. [iShamba](https://ishamba.com/) / [Torchbox case](https://torchbox.com/charity/blog/sms-support-kenyan-farmers/). **Limitation:** no generative AI, no vision; proves there is an installed voice-first user base waiting to be upgraded.

**Wadhwani AI Krishi Sahayak / SukhaRakshak AI.** Gemini 2.0 Flash + RAG, 22+ Indian languages via AI4Bharat TTS/STT. [Wadhwani AI](https://www.wadhwaniai.org/empowering-millions-of-indian-farmers-with-instant-ai-chatbot-support/). **Limitation:** Indian-market specific, no visible agentic tool-calling architecture.

### Geospatial / satellite-driven advisors

**Google Agricultural Landscape Understanding (ALU) / AnthroKrishi.** **Field-boundary segmentation from high-res satellite + classification of irrigation, roads, water bodies across India.** Research API released to partners (Ninjacart, Skymet, IIT Bombay). [agri.withgoogle.com](https://agri.withgoogle.com/) / [arXiv paper 2411.05359](https://arxiv.org/html/2411.05359v1) / [Google blog](https://blog.google/technology/ai/how-ai-is-improving-agriculture-sustainability-in-india/). **This is the 800-lb gorilla for spatial intelligence.** **Limitation ClimaSense can exploit:** ALU is a Google product for B2B partners, not a direct farmer-facing agent; it provides tiles, not a voice-first conversation in Swahili.

**Microsoft FarmBeats → Azure Data Manager for Agriculture + FarmVibes.AI.** Open-source geospatial ML toolkit, fuses Sentinel-2 + weather + drone imagery; recently partnered with AgriPilot.ai for a "living lab" at ADT Baramati across Indian smallholder farms. [Microsoft Source](https://news.microsoft.com/source/features/ai/microsoft-open-sources-its-farm-of-the-future-toolkit/) / [FarmVibes.AI GitHub](https://github.com/microsoft/farmvibes-ai) / [Agrospectrum India Nov 2025](https://agrospectrumindia.com/2025/11/22/microsofts-ai-stack-and-agripilots-field-innovation-deliver-indias-most-advanced-living-lab-for-smallholder-farming.html). **Limitation:** an SDK for data scientists, not a farmer-facing conversational agent; no LLM reasoning layer shipped.

**Tomorrow.io (formerly ClimaCell).** Proprietary weather satellites + AI models for hyperlocal forecasts; recent Philippines Department of Agriculture partnership. [Tomorrow.io agriculture](https://www.tomorrow.io/solutions/agriculture/) / [Philippines announcement](https://www.tomorrow.io/blog/tomorrow-io-to-bring-ai-powered-weather-forecasting-to-filipino-farmers/). **Limitation:** enterprise-priced; no smallholder-facing conversational UX.

**Climate FieldView (Bayer/Climate Corp).** Precision-ag platform for >20 countries, **60 M subscribed hectares on commercial-scale farms**; recently launched in South Africa. [climate.com](https://climate.com/en-us.html) / [Bayer launch](https://www.bayer.com/media/en-us/industry-leading-digital-farming-platform-climate-fieldviewtm-launches-in-south-africa/). **Limitation:** aimed at commercial farmers with John Deere-class equipment, not smallholders.

### Financial + advisory combined

**One Acre Fund.** ML + climate-data personalised recommendations targeting **1 M smallholder farmers by 2027** across sub-Saharan Africa. [oneacrefund.org Articles](https://oneacrefund.org/articles/bringing-digital-tools-one-million-smallholder-farmers). **Limitation:** relationship-driven, field-agent heavy; tech is a thin layer over a deep operational network.

**Apollo Agriculture (Kenya).** ML credit-scoring + remote-sensing + agronomy bundle, **>200K farmers**. [efdafrica](https://efdafrica.org/agriculture/apollo/). **Limitation:** finance-first, advisory is a tied service not the product.

**Hello Tractor.** Uber-for-tractors marketplace, 2.5 M smallholders, 20+ countries. [hellotractor.com](https://hellotractor.com/) / [ConnectingAfrica](https://www.connectingafrica.com/innovation-hub/four-agritech-startups-to-watch-in-2024). **Not a competitor** for advisory, but a proof of smallholder-scale digital engagement.

**Twiga Foods.** B2B marketplace, reduced post-harvest loss from 30% → 4% in Kenya. [thesupplychainlab](https://thesupplychainlab.blog/2019/11/11/twiga-foods-solving-africas-fragmented-agriculture-markets-with-technology/). **Not a competitor** but sets the impact bar.

### Carbon MRV (adjacent)

**Pachama (acquired by Carbon Direct, 2025).** Satellite + LiDAR MRV for forest carbon. [pachama.com](https://pachama.com/) / [ESG Today](https://www.esgtoday.com/carbon-direct-acquires-carbon-project-mrv-platform-pachama/). **Not a competitor** but referenced in Global Resilience track imaginaries.

### Direct Gemma 3n predecessor entries

**AgriGemma-3n and Gemma-3n-Swahili (Kaggle Gemma 3n Impact Challenge writeup, Aug 6 2025).** A fine-tuned Gemma 3n variant for crop disease + Swahili. [Kaggle writeup](https://www.kaggle.com/competitions/google-gemma-3n-hackathon/writeups/agrigemma-3n). **Did not win a prize.** The existence of this submission is itself a warning: "we fine-tuned Gemma on crop disease + added Swahili" is the obvious play. Anyone half-informed will file it.

**"A Fine-Tuned Plant Disease Detection Gemma Model using Unsloth and Application"** [Kaggle writeup](https://www.kaggle.com/competitions/google-gemma-3n-hackathon/writeups/a-fine-tuned-plant-disease-detection-model-and-app). Same shape, same fate.

**Open KCC fine-tune of Gemma-3n (Authorea preprint, 2025).** A reproducible LoRA+QLoRA+Unsloth pipeline on India's Kisan Call Centre transcripts. [Authorea paper](https://www.authorea.com/users/688278/articles/1372979/master/file/data/A%20Reproducible%20Pipeline%20for%20OnDevice%20Farmer%20Advisory%20Fine-Tuning%20Gemma-3n%20with%20Open%20KCC%20Data/A%20Reproducible%20Pipeline%20for%20OnDevice%20Farmer%20Advisory%20Fine-Tuning%20Gemma-3n%20with%20Open%20KCC%20Data.pdf?inline=true). **60-step pilot run.** Establishes the trivial baseline anyone on the arXiv-reading track knows.

### Academic baselines to beat

- **Farmer.Chat paper ([arXiv 2409.08916](https://arxiv.org/html/2409.08916v1))** — defines the SOTA for smallholder conversational AI. 75% accuracy, 15K users. Judges will have read this.
- **AgriGPT + Tri-RAG ([arXiv 2508.08632](https://arxiv.org/html/2508.08632v1))** — multi-agent data engine, 342K QA pairs, benchmark suite AgriBench-13K.
- **AgriGPT-VL ([arXiv 2510.04002](https://arxiv.org/html/2510.04002v3))** — vision-language variant for agricultural imagery.
- **AgroAskAI ([arXiv 2512.14910](https://arxiv.org/html/2512.14910))** — multi-agentic framework for global smallholder enquiries.
- **AgroLLM ([arXiv 2503.04788](https://arxiv.org/abs/2503.04788))** — RAG + BLEU benchmarking.
- **AIEP Initiative learnings ([arXiv 2601.11537](https://arxiv.org/html/2601.11537v1))** — candid write-up: latency is the #1 enemy of voice UX (sub-5-second responses are rare), low-resource languages break on ASR+MT compounding, content curation remains manual. This paper is gold because it is honest about what doesn't work.

---

## Part 2: What Actually Wins — Gemma 3n Impact Challenge Evidence

The Gemma 3n Impact Challenge (2024–2025) had **600+ submissions**, $150 K prize pool, and **8 winners** per the [Google blog](https://blog.google/innovation-and-ai/technology/developers-tools/developers-changing-lives-with-gemma-3n/) and the [startuphub.ai recap](https://www.startuphub.ai/ai-news/ai-research/2025/gemma-3n-powers-real-world-impact-at-the-edge/). **None of the 8 winners were agricultural.** Winners were Gemma Vision (blind assistance), Vite Vere Offline (cognitive disability), 3VA (AAC for cerebral palsy user "Eva"), Sixth Sense Security, Dream Assistant (custom voice), LENTERA (offline education microserver), a robotics entry, and a Jetson voice UI. Source: [Tommaso Giovannini's Kaggle writeup](https://www.kaggle.com/tommasogiovannini/writeups) / [Node Café LinkedIn summary](https://www.linkedin.com/posts/the-node-cafe_google-announces-8-winning-gemma-3n-projects-activity-7404862866022998016-2b8s).

**That is the single most actionable datapoint in this report.** Agriculture entries **did not win** in the direct predecessor despite being heavily submitted. Why? Because they pattern-match to "GPT wrapper + RAG over a farming PDF + Swahili TTS." Judges reward:

1. **A named human beneficiary.** Gemma Vision: the developer's blind brother. 3VA: Eva, a graphic designer with cerebral palsy. Personal stories beat aggregate stats. [blog.google](https://blog.google/innovation-and-ai/technology/developers-tools/developers-changing-lives-with-gemma-3n/).

2. **Offline / on-device as a core demonstration, not a footnote.** Every single winner operated without internet. LENTERA *made the offline capability its product*. The challenge brief literally asked "how can a private, offline-first, multimodal model make a tangible difference?" [Kaggle challenge overview](https://www.kaggle.com/competitions/google-gemma-3n-hackathon/overview).

3. **Voice UX polish.** The 1st-place winner's write-up details streaming responses, loading music to cover inference gaps, distinct sound effects per action, TalkBack/VoiceOver integration. Voice was not just a feature — it was *designed* end-to-end for a specific user who cannot see a screen.

4. **Documented failures.** Tommaso Giovannini's writeup enumerates **10 specific engineering challenges and solutions** — model download issues, camera positioning, controller pairing, text recognition accuracy. Honest failure-reporting reads as real craft.

5. **Fine-tuning for a narrow task.** 3VA fine-tuned on Apple MLX locally; the Unsloth prize winner fine-tuned on one person's speech. Generic fine-tuning doesn't win; fine-tuning that proves a **per-user or per-dataset transformation** does.

The Gemma 4 Good Hackathon rubric confirms the shape: **Impact & Vision 40% | Video Pitch 30% | Technical Depth 30%**. Sources: [Algomania summary](https://algo-mania.com/en/blog/hackathons-coding/gemma-4-hackathon-200000-to-create-ai-for-social-impact/), [Medium overview by Sudha Rani Maddala](https://sudhamsr.medium.com/the-gemma-4-good-hackathon-aef927f17ef1), [EdTech Innovation Hub coverage](https://www.edtechinnovationhub.com/news/kaggle-and-google-deepmind-open-gemma-4-hackathon-focused-on-ai-skills-and-real-world-impact). The Medium writeup explicitly warns: **"Success favors projects that solve one specific workflow, target one clear user, work end-to-end, and use Gemma 4 in a meaningful way — not generic demos, chatbots, or PDF assistants."**

Finally, a related signal: **better-ed** (a voice-enabled offline learning assessment platform, Predictive Systems Inc.) was publicly showcased as a Gemma 3n challenge entry — [better-ed.ai blog](https://better-ed.ai/blog/gemma-3n-better-ed). Voice + offline + narrow persona was the winning archetype, not the winning product.

---

## Part 3: Judge's Critique of ClimaSense

I'm a senior engineer on the DeepMind applied-AI side. I've personally read the Farmer.Chat paper. I've seen the cassava trials for PlantVillage Nuru. I know what Google's own ALU team is doing in India. Here is my honest read of ClimaSense.

### Where ClimaSense is genuinely novel and hard to replicate

**The agentic tool-calling loop is the single biggest moat.** Farmer.Chat is RAG-only — it retrieves documents and stitches. Jugalbandi is RAG-only. KissanGPT is a chat wrapper. AgriGPT's Tri-RAG is fancier retrieval, still not a tool-orchestrating agent. ClimaSense uses Gemma 4's native function-calling format (`<|"|>` tokens, the 6 special structured-call tokens per the [Hugging Face Gemma 4 blog](https://huggingface.co/blog/gemma4) and the [Google function-calling docs](https://ai.google.dev/gemma/docs/capabilities/text/function-calling-gemma4)) to chain **10 heterogeneous API tools in a single reasoning pass**. *Nobody in the agricultural literature I reviewed does this.* This is exactly the marquee Gemma 4 capability the judges are paid to reward.

**Sentinel-2 NDVI as a real-time ground-truth check against the farmer's claim is genuinely novel.** Farmer.Chat doesn't do this. FarmerAI doesn't do this. Nuru doesn't do this. The closest prior art is TechghilAgro in Mauritania (Sentinel-2 dashboards for rice farmers, source: [Sentinel success stories](https://sentinels.copernicus.eu/web/success-stories/-/empowering-agriculture-in-mauritania-with-sentinel-2-the-techghilagro-success-story)) but those are dashboards, not a conversational agent that fetches NDVI as a tool in response to a voice question. *Fetching NDVI via the Microsoft Planetary Computer STAC API as a tool the model decides to call* — that is a demonstrably new capability and one that separates you from a RAG wrapper.

**Dual-model architecture (E4B for audio + 31B for reasoning on separate GPUs, 78.5GB total) is a real engineering trick.** Most hackathon entries use one model. Splitting by modality is pragmatic and underexplored publicly; the only comparable public demo is [Parlor](https://github.com/fikrikarim/parlor) (Gemma 4 E2B + Kokoro TTS) which is voice-conversational, not tool-calling.

**The LoRA fine-tune on PlantVillage with documented accuracy lift (20% → 60% zero-shot → LoRA) is concrete technical evidence.** AgriGemma-3n did this for Gemma 3n and didn't place. You did it for Gemma 4 with a v2 at 300 samples × 8 epochs with r=32 LoRA + MLP layers (loss 0.1263 → 0.0004) per `TODO.md`. *If that v2 benchmark confirms >80% accuracy,* you have a stronger technical demonstration than anything in the direct prior work I found.

### Where ClimaSense is incremental and will look like every other entry

**"Smallholder farmer climate advisor" with Swahili voice.** Over-entered. AgriGemma-3n already shipped the Gemma 3n version of this premise; it didn't place. Farmer.Chat has Swahili, six languages, 15K real users. Unless you explicitly contrast the agentic loop and satellite tool against these baselines in your writeup and video, judges will pattern-match and move on.

**RAG over crop disease knowledge.** Every agri entry has this. The combination of WFP HDX + NASA POWER + ISRIC + Open-Meteo is a better set than most, but the *idea* of pulling free APIs is not itself a moat.

**"Works on a smartphone."** Every mobile-first Gemma entry claims this. LENTERA won by *making offline deployment its product.* You have offline caching, which is table stakes now — not a differentiator. See Nuru, see Vite Vere, see LENTERA.

**Impact framing "500M smallholder farmers."** Generic. Farmer.Chat cites the same 500M statistic. Judges have heard it in every entry.

**PlantVillage dataset.** The most-used dataset in plant-disease fine-tuning papers. Using it unmodified telegraphs "I searched the Kaggle datasets page." You need to *extend* it — with hard-to-classify field-condition images, or with Swahili/Hindi captions, or with expert-annotated severity grades — to claim a technical-depth point.

### Missing credibility (the judge's red-pen points)

**No named user.** `personas.py` has "Amina Otieno" from Kisumu County — that's a fictional persona, and a fictional persona is worse than no persona because it signals "I wrote this in a Claude turn, not in a village." Gemma Vision's blind brother was real. 3VA's Eva was real. The Gemma 3n winner pattern is unambiguous. *Either* find a real extension officer / NGO / farmer cooperative to test and quote in the writeup, *or* lean into a clearly-labelled "scenario persona drawn from FAO Kenya case studies" and cite those case studies by URL. The middle ground — a made-up name with no source — is the worst option.

**No before/after impact number.** Every winner had one. Nuru: "130–530% yield improvement." 3VA: "Eva can now express X in Y seconds vs Z before." ClimaSense has "0.885 composite eval" and "0.911 tool F1" — those are internal engineering metrics, not impact numbers. You need *at least one sentence* of the form: "Without ClimaSense, Amina's decision takes [N days, costs $X, results in Y% loss]; with ClimaSense, the same decision is [faster/cheaper/less risky] because [specific tool output]." Even a counterfactual simulation based on WFP price data would count.

**No field trial.** None. This is the single biggest gap. The Gemma 4 hackathon rubric weights **Impact & Vision 40%**; without a field test, your Impact ceiling is structurally capped. A 30-minute Zoom call with one Kenyan extension officer from a CGIAR-affiliated NGO (ICRAF, ILRI, CIAT, AICCRA) and a signed quote in the writeup would move this from "demo" to "deployment candidate" in judge scoring.

**The Kaggle notebook hasn't been tested on Kaggle's free GPU tier yet.** `TODO.md` admits this. Notebooks that fail to run on the public GPU are disqualifying. Non-negotiable.

**No Swahili accuracy number.** The eval shows "By language: English 0.954, Swahili 0.678" — this is a **direct weakness versus Farmer.Chat**, which claims 75% accuracy in Swahili with its RAG stack. You either close this gap or frame it honestly ("we're behind on Swahili content coverage; this is the next sprint").

### Underselling itself (things harder than they look, that you must flag)

**The 10-tool agentic loop with the correct Gemma 4 tool-call parser (including the `<|"|>` token quirk, per your own HANDOFF.md).** Parsing Gemma's structured output is non-trivial; most people hit the tokenisation bug once and give up. This is worth a paragraph in the Technical Depth writeup with a code snippet of the parser and a before/after latency metric.

**Microsoft Planetary Computer STAC integration for live Sentinel-2 fetch.** This is a research-tier geospatial engineering task. Most ML engineers have never written a STAC query. It is genuinely harder than "call an API." Flag it. Screenshot the STAC request → Sentinel tile → NDVI calculation in your video.

**Dual-GPU placement of 31B + E4B with different model weights on different devices.** Most developers cannot debug GPU memory placement for 78.5GB across two cards. This is the kind of detail that separates "built a demo" from "built a system." Include the GPU memory diagram in the architecture section.

**Offline cache with per-tool TTL policy and staleness labels.** "When we are offline, the soil tool returns cached ISRIC data with label `last_updated: 2d ago`; the weather tool, which is more time-sensitive, returns `stale, reconnect required`." That per-tool freshness policy is exactly the kind of systems-thinking judges notice — and nobody else will have it.

**PEFT/LoRA `ClippableLinear` workaround for the Gemma 4 vision head.** Per `TODO.md` you hit a real PEFT bug and solved it. That's a portable contribution the hackathon community will reuse. Link to the script in the repo and mention it in the writeup.

---

## Three Specific Improvements

Each ranked by effort (hours) × expected rubric lift.

### Improvement 1 — Secure one real domain-expert endorsement quote

**What:** Find one person from a CGIAR / ICRAF / AICCRA / OneAcreFund / Digital Green network. Do a 30-minute Zoom. Show them the Swahili voice round-trip. Ask: "If we gave this to a farmer in your county, what would they get right and wrong?" Record the response. Ask permission to quote two sentences by name and role in the writeup and the video's closing frame. Offer the repo under Apache 2.0 in return.

**Why this moves judges:** Closes the "no field trial" gap at the cheapest possible cost. Transforms Impact & Vision from abstract to concrete. A single sentence like *"Tested with M. Ochieng, extension officer, Siaya County — 'the soil layer is more precise than what my office gives farmers'"* is worth 10x any engineering paragraph.

**Effort:** 3–5 hours outreach + 1 hour interview + 1 hour editing.
**Expected lift:** Impact +6 pts (out of 40), Video +3 pts (out of 30). **Highest ROI improvement.**

### Improvement 2 — Publish a one-page "vs Farmer.Chat" comparison table in the writeup

**What:** Side-by-side table with Farmer.Chat (arXiv 2409.08916) on one column and ClimaSense on the other. Rows: Architecture (RAG-only vs agentic tool-calling), Tools (0 vs 10), Modalities (text+voice vs text+voice+vision+satellite), Offline (no vs yes with per-tool TTL), Satellite ground-truth (no vs yes Sentinel-2 via STAC), Model substrate (GPT-4/3.5 vs Gemma 4 31B + E4B, open weights), Swahili accuracy (75% vs your measured number), Fine-tune (unspecified vs LoRA on PlantVillage). Cite the arXiv paper in every "no" cell. Do **not** overstate — be honest in cells where Farmer.Chat is ahead (user base, field deployment months).

**Why this moves judges:** Positions ClimaSense against the published academic SOTA, not a vacuum. Signals "we did our lit review." Every senior reviewer mentally scores higher for entries that know what they're contending with. Also neutralises "you're just another farmer chatbot" pattern-matching.

**Effort:** 4 hours research + 2 hours drafting.
**Expected lift:** Technical Depth +5 pts, Impact +2 pts (clarifies moat). Shifts the "incremental" rows in the critique above into "explicit differentiators."

### Improvement 3 — Make the Sentinel-2 NDVI step visible in the video as the wow-moment

**What:** In the 2-minute video, the single clearest differentiator you have is the satellite ground-truth tool. Script it as: 15 seconds — Amina says in Swahili "my maize is fine." Model reasons: "let me verify." Cuts to screen-capture of STAC request running. Cuts to Sentinel-2 tile appearing. NDVI overlaid; model responds in Swahili: "Your northwest corner shows NDVI 0.3 — there is drought stress you may not see from ground level. Let me also check weather and soil." Three further tool calls fire visibly. Final spoken Swahili response synthesises all four data sources. Close the video on the NDVI tile, not on a dashboard. **That image is what judges will remember when they write their scores.**

**Why this moves judges:** Video Pitch is 30% of the score and the only dimension where a *single cinematic beat* can decisively beat 100 other entries. No other agri entry has a live satellite tile appearing in the agentic loop. This is your viral moment. The Gemma 3n winners all had one such beat (blind brother uses controller; Eva types with pictograms; LENTERA WiFi hotspot turns on in a disconnected village).

**Effort:** 6–10 hours — script + record screen-capture with timed voiceover + one retake if the STAC call takes >30 seconds (pre-cache the tile if needed, but disclose this in the writeup).
**Expected lift:** Video Pitch +8 pts, Impact +3 pts (vision feels tangible). This is the second-highest ROI after Improvement 1.

---

## Bottom line

ClimaSense is **technically stronger than any public agri-advisor entry in the Gemma 3n predecessor competition and stronger than the current state of the art in the published agri-advisor literature** (Farmer.Chat, AgriGPT, AgroLLM, AgriGemma-3n) along four specific axes: agentic tool-calling, satellite ground-truthing, dual-model architecture, and per-tool offline caching policy. Those four are your moat.

It is **strategically weaker on the one dimension the rubric weights highest (Impact & Vision 40%)** because the user is fictional, no field trial exists, and no before/after impact number is quantified. The three improvements above directly attack that weakness for ~20 hours of total effort.

The path to winning is not more tools and not more languages. It is **one real user quote, one comparison table against the published SOTA, and one cinematic satellite moment in the video.** Judges have seen 600 farmer chatbots. They have seen zero agentic loops that pull Sentinel-2 in response to a Swahili voice query. Make that the thing they cannot forget.

---

## Sources

### Competitor products & companies
- [Plantix company & API](https://plantix.net/en/) / [Plantix Wikipedia](https://en.wikipedia.org/wiki/Plantix) / [Plantix FAO case](https://www.fao.org/e-agriculture/news/plantix-lets-farmers-recognize-plant-diseases-pests-and-nutrient-diffidences-just-sending) / [GSMA AgriTech case study](https://www.gsma.com/solutions-and-impact/connectivity-for-good/mobile-for-development/programme/agritech/detecting-and-managing-crop-pests-and-diseases-with-ai-insights-from-plantix/) / [Plantix ML blog](https://plantix.net/en/blog/machine-learning-helps-small-farmers-identify-plant-pests-and-diseases/)
- [PlantVillage Nuru — IITA](https://www.iita.org/news-item/african-farmers-get-new-help-against-cassava-diseases-nuru-their-artificially-intelligent-assistant/) / [Nuru Frontiers in Plant Science paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC7775399/) / [Penn State $4.96M grant](https://www.psu.edu/news/research/story/plantvillage-receives-496-million-grant-combat-crop-loss-africa) / [Google blog AI takes root](https://blog.google/innovation-and-ai/products/ai-takes-root-helping-farmers-identity-diseased-plants/) / [PlantVillage projects](https://plantvillage.psu.edu/projects)
- [Farmer.Chat — Digital Green](https://digitalgreen.org/farmer-chat/) / [Farmer.Chat — Gooey.AI](https://www.help.gooey.ai/farmerchat) / [Farmer.Chat arXiv 2409.08916](https://arxiv.org/html/2409.08916v1) / [CGAP women farmers blog](https://www.cgap.org/blog/beyond-chat-ai-powered-advice-for-women-farmers) / [Rockefeller Foundation impact story](https://www.rockefellerfoundation.org/grantee-impact-stories/how-an-ai-based-app-is-bridging-the-information-gap-for-indias-farmers/) / [Analytics Vidhya Digital Green OpenAI](https://www.analyticsvidhya.com/blog/2024/05/openai-and-digital-green-is-helping-indian-farmers-with-farmer-chat/)
- [Jugalbandi — Microsoft Asia](https://news.microsoft.com/source/asia/features/with-help-from-next-generation-ai-indian-villagers-gain-easier-access-to-government-services/) / [Jugalbandi Medianama](https://www.medianama.com/2023/06/223-jugalbandi-chatbot-rural-india-what-to-know/) / [OpenNyAI repo](https://github.com/OpenNyAI/jugalbandi_chatbot) / [Analytics Insight overview](https://www.analyticsinsight.net/microsoft-launches-an-ai-based-multilingual-chatbot-for-rural-india/)
- [KissanGPT IndiaAI](https://indiaai.gov.in/article/how-kissangpt-helps-indian-farmers-earn-profit) / [KissanAI](https://kissan.ai/) / [Krishi Jagran](https://krishijagran.com/news/maximize-your-crop-yield-with-kissan-gpt-the-ai-chatbot-for-indian-farmers/)
- [ITC MAARS Krishi Mitra](https://www.newkerala.com/news/a/itc-expand-ai-services-rural-communities-organic-farmers-750.htm)
- [Wadhwani AI Krishi Sahayak](https://www.wadhwaniai.org/empowering-millions-of-indian-farmers-with-instant-ai-chatbot-support/)
- [FarmerAI Safaricom + Opportunity International](https://opportunity.org/news/press-releases/opportunity-international-and-safaricom-launch-new-ai-chatbot-for-smallholder-farmers) / [Safaricom press](https://www.safaricom.co.ke/media-center-landing/press-releases/opportunity-international-safaricom-launch-new-ai-chatbot-for-smallholder-farmers) / [TechAfrica News](https://techafricanews.com/2025/02/11/ai-meets-agriculture-as-safaricom-and-opportunity-international-unveil-farmerai/)
- [iShamba](https://ishamba.com/) / [Torchbox case study](https://torchbox.com/charity/blog/sms-support-kenyan-farmers/)
- [Google ALU / AnthroKrishi](https://agri.withgoogle.com/) / [ALU FAQ](https://agri.withgoogle.com/faq/) / [ALU arXiv 2411.05359](https://arxiv.org/html/2411.05359v1) / [Google blog](https://blog.google/technology/ai/how-ai-is-improving-agriculture-sustainability-in-india/) / [Geospatial World](https://geospatialworld.net/news/google-alu-farmers/) / [Deccan Herald](https://www.deccanherald.com/technology/google-to-launch-agricultural-landscape-understanding-alu-research-api-soon-in-india-3109168)
- [Microsoft FarmBeats / FarmVibes.AI](https://news.microsoft.com/source/features/ai/microsoft-open-sources-its-farm-of-the-future-toolkit/) / [FarmVibes.AI GitHub](https://github.com/microsoft/farmvibes-ai) / [FarmBeats research](https://www.microsoft.com/en-us/research/project/farmbeats-iot-agriculture/) / [FarmVibes docs](https://microsoft.github.io/farmvibes-ai/) / [AgriPilot living-lab](https://agrospectrumindia.com/2025/11/22/microsofts-ai-stack-and-agripilots-field-innovation-deliver-indias-most-advanced-living-lab-for-smallholder-farming.html)
- [Tomorrow.io agriculture](https://www.tomorrow.io/solutions/agriculture/) / [Tomorrow.io Wikipedia](https://en.wikipedia.org/wiki/Tomorrow.io) / [Philippines partnership](https://www.tomorrow.io/blog/tomorrow-io-to-bring-ai-powered-weather-forecasting-to-filipino-farmers/)
- [Climate FieldView](https://climate.com/en-us.html) / [Climate Corp Wikipedia](https://en.wikipedia.org/wiki/The_Climate_Corporation) / [FieldView South Africa launch](https://www.bayer.com/media/en-us/industry-leading-digital-farming-platform-climate-fieldviewtm-launches-in-south-africa/)
- [One Acre Fund digital tools](https://oneacrefund.org/articles/bringing-digital-tools-one-million-smallholder-farmers) / [One Acre model](https://oneacrefund.org/about-us/our-model)
- [Apollo Agriculture — EFD Africa](https://efdafrica.org/agriculture/apollo/) / [Techpoint Africa feature](https://techpoint.africa/feature/apollo-agriculture-feature/) / [GSMA Apollo insights](https://www.gsma.com/solutions-and-impact/connectivity-for-good/mobile-for-development/programme/agritech/ai-driven-smallholder-farmer-lending-in-africa-insights-from-apollo-agriculture/)
- [Hello Tractor](https://hellotractor.com/) / [ConnectingAfrica agritech](https://www.connectingafrica.com/innovation-hub/four-agritech-startups-to-watch-in-2024)
- [Twiga Foods supply-chain lab](https://thesupplychainlab.blog/2019/11/11/twiga-foods-solving-africas-fragmented-agriculture-markets-with-technology/) / [Afrobility transcript](https://afrobility.substack.com/p/transcript-64-twiga-foods-how-the)
- [Pachama / Carbon Direct acquisition](https://www.esgtoday.com/carbon-direct-acquires-carbon-project-mrv-platform-pachama/) / [pachama.com](https://pachama.com/)
- [TechghilAgro Sentinel-2 Mauritania](https://sentinels.copernicus.eu/web/success-stories/-/empowering-agriculture-in-mauritania-with-sentinel-2-the-techghilagro-success-story)

### Gemma 3n predecessor & winners
- [Kaggle Gemma 3n Impact Challenge overview](https://www.kaggle.com/competitions/google-gemma-3n-hackathon/overview) / [Writeups index](https://www.kaggle.com/competitions/google-gemma-3n-hackathon/writeups) / [Challenge rules](https://www.kaggle.com/competitions/google-gemma-3n-hackathon/rules)
- [Google blog — 8 winners](https://blog.google/innovation-and-ai/technology/developers-tools/developers-changing-lives-with-gemma-3n/) / [StartupHub recap](https://www.startuphub.ai/ai-news/ai-research/2025/gemma-3n-powers-real-world-impact-at-the-edge/) / [Nionee Nexus article](https://blogs.nionee.com/these-developers-are-changing-lives-with-gemma-3n/) / [Node Café LinkedIn](https://www.linkedin.com/posts/the-node-cafe_google-announces-8-winning-gemma-3n-projects-activity-7404862866022998016-2b8s) / [Google AI Devs LinkedIn](https://www.linkedin.com/posts/googleaidevs_gemma-3n-impact-challenge-projects-activity-7404582423897919489-YnMv) / [Tommaso Giovannini Kaggle writeups](https://www.kaggle.com/tommasogiovannini/writeups) / [better-ed Gemma 3n entry](https://better-ed.ai/blog/gemma-3n-better-ed)
- [AgriGemma-3n Kaggle writeup](https://www.kaggle.com/competitions/google-gemma-3n-hackathon/writeups/agrigemma-3n) / [Fine-tuned plant-disease Gemma 3n writeup](https://www.kaggle.com/competitions/google-gemma-3n-hackathon/writeups/a-fine-tuned-plant-disease-detection-model-and-app) / [EcoVision AI writeup](https://www.kaggle.com/competitions/google-gemma-3n-hackathon/writeups/ecovision-ai-democratizing-environmental)

### Gemma 4 Good Hackathon
- [Kaggle Gemma 4 Good Hackathon](https://www.kaggle.com/competitions/gemma-4-good-hackathon) / [EdTech Innovation Hub coverage](https://www.edtechinnovationhub.com/news/kaggle-and-google-deepmind-open-gemma-4-hackathon-focused-on-ai-skills-and-real-world-impact) / [Inner Detail writeup](https://theinnerdetail.com/google-announces-hackathon-on-ai-skills-using-gemma-4-with-200k-prize/) / [Algomania summary](https://algo-mania.com/en/blog/hackathons-coding/gemma-4-hackathon-200000-to-create-ai-for-social-impact/) / [Medium — Sudha Rani Maddala](https://sudhamsr.medium.com/the-gemma-4-good-hackathon-aef927f17ef1) / [Kaggle announcement LinkedIn](https://www.linkedin.com/posts/kaggle_now-available-on-kaggle-gemma-4-in-partnership-activity-7445505784228073472-QYnt)

### Gemma 4 technical
- [Gemma 4 Hugging Face blog](https://huggingface.co/blog/gemma4) / [Google function-calling docs](https://ai.google.dev/gemma/docs/capabilities/text/function-calling-gemma4) / [Gemma 4 model card](https://ai.google.dev/gemma/docs/core/model_card_4) / [Gemma 4 prompt formatting](https://ai.google.dev/gemma/docs/core/prompt-formatting-gemma4) / [Google bring-agentic-to-the-edge](https://developers.googleblog.com/bring-state-of-the-art-agentic-skills-to-the-edge-with-gemma-4/) / [Google blog launch](https://blog.google/innovation-and-ai/technology/developers-tools/gemma-4/) / [Gemma 4 DeepMind](https://deepmind.google/models/gemma/gemma-4/) / [Hugging Face recipes](https://github.com/huggingface/huggingface-gemma-recipes) / [Parlor on-device Gemma 4 + Kokoro](https://github.com/fikrikarim/parlor) / [MachineLearningMastery tool calling](https://machinelearningmastery.com/how-to-implement-tool-calling-with-gemma-4-and-python/) / [Analytics Vidhya tool calling guide](https://www.analyticsvidhya.com/blog/2026/04/gemma-4-tool-calling/)

### Academic baselines
- [Farmer.Chat arXiv 2409.08916](https://arxiv.org/abs/2409.08916) / [AIEP initiative arXiv 2601.11537](https://arxiv.org/html/2601.11537v1) / [Fine-Tuning & Evaluating Conversational AI arXiv 2603.03294](https://arxiv.org/html/2603.03294) / [AgroLLM arXiv 2503.04788](https://arxiv.org/abs/2503.04788) / [AgriGPT arXiv 2508.08632](https://arxiv.org/abs/2508.08632) / [AgriGPT-VL arXiv 2510.04002](https://arxiv.org/html/2510.04002v3) / [AgroAskAI arXiv 2512.14910](https://arxiv.org/html/2512.14910) / [AICCRA advisory gaps](https://aiccra.cgiar.org/news/mind-gap-making-ai-driven-advisories-work-all-farmers) / [Authorea KCC Gemma-3n fine-tune](https://www.authorea.com/users/688278/articles/1372979/master/file/data/A%20Reproducible%20Pipeline%20for%20OnDevice%20Farmer%20Advisory%20Fine-Tuning%20Gemma-3n%20with%20Open%20KCC%20Data/A%20Reproducible%20Pipeline%20for%20OnDevice%20Farmer%20Advisory%20Fine-Tuning%20Gemma-3n%20with%20Open%20KCC%20Data.pdf?inline=true) / [KCC dataset India AI](https://aikosh.indiaai.gov.in/home/datasets/details/kisan_call_centre_kcc_transcripts_of_farmers_queries_and_answers.html) / [Agri-LLaVA arXiv 2412.02158](https://arxiv.org/html/2412.02158v1)
