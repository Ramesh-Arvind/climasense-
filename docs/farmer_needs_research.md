# Farmer Needs Research: Gaps in AI Agricultural Advisors for Smallholders

**Scope:** Sub-Saharan Africa (SSA) and South Asia. **Horizon:** 7-10 days of build time per addition. **Goal:** additions that prevent real loss, not demo polish. **Deadline:** May 18, 2026.

---

## 1. The ten-tool stack already covers the crop-in-field problem

ClimaSense already hits real APIs for weather forecast, historical climate, crop disease diagnosis, treatment, WFP market prices, price forecast, ISRIC soil, NASA POWER planting calendar, climate risk alerts, and Sentinel-2 NDVI. That is essentially a complete **pre-harvest, in-field, single-crop** agronomic stack. What it does *not* cover is where smallholders lose the most money: **after harvest, in livestock, in the supply chain, and in bureaucratic access to money**. The research below ranks gaps by dollar-impact per smallholder household.

---

## 2. The competitive floor

- **Google ALU + AMED** (India Oct 2024; Malaysia/Indonesia/Vietnam/Japan April 2025 via API). Panoptic segmentation delivers field boundaries, trees, ponds, wells on S2-Level-13 cells. AMED (July 2025) adds crop type, acreage, sowing/harvest events at 15-day refresh. It is remote-sensing *data* — not an agentic advisor. ClimaSense can be the conversational layer. ([docs](https://developers.google.com/agricultural-understanding/landscape-understanding), [arXiv 2411.05359](https://arxiv.org/html/2411.05359v1))
- **Microsoft FarmVibes.AI** — open-source ingestion of ~30 geospatial datasets. No agent, no livestock, no post-harvest. ([GitHub](https://github.com/microsoft/farmvibes-ai))
- **DeepMind GraphCast / ECMWF AIFS** — upstream 10-day forecast models. Open-Meteo already exposes them. ([DeepMind](https://deepmind.google/blog/graphcast-ai-model-for-faster-and-more-accurate-global-weather-forecasting/))
- **CGIAR AgWise** — fertilizer/variety recommender at agwise.akilimo.org (+60 % rice, +69 % potato Rwanda). Limited crops/countries. ([CGIAR](https://www.cgiar.org/news-events/news/raising-productivity-and-profits-how-agwise-is-closing-yield-gaps-through-ai/))
- **IITA A-EWS + Aflasafe** — ML aflatoxin-hotspot mapping released 2025. Not yet a farmer-facing app. Clear opening. ([CGIAR](https://www.cgiar.org/news-events/news/ai-tool-makes-invisible-enemy-visible-tackling-aflatoxin-risk-in-africas-maize))
- **Apollo / Pula / ACRE Africa** — vertical fintech + parametric insurance. Proprietary; no public APIs. ([Pula-IFC](https://www.ifc.org/content/dam/ifc/doc/2024/pula-ifc-2024.pdf))

**Bottom line:** nobody ships a conversational, multimodal, offline-capable agent covering post-harvest + livestock + input-supply + scheme navigation. That is the opening.

---

## 3. Five high-impact additions (ranked by $ saved per smallholder)

### #1 — Aflatoxin + post-harvest storage risk advisor (HIGHEST IMPACT)

**Problem (one line):** 20–40 % of smallholder grain stored in Sub-Saharan Africa is lost or downgraded to mycotoxin contamination (aflatoxin, ochratoxin) that is invisible, carcinogenic, and detectable only by lab; farmers typically dry and store by habit, not by conditions. ([npj Science of Food 2023](https://www.nature.com/articles/s41538-023-00238-7), [CABI Agric. Biosci. 2024](https://cabiagbio.biomedcentral.com/articles/10.1186/s43170-024-00305-3))

**Data sources:**
- **Open-Meteo** (already integrated) for hourly temperature + relative humidity + rainfall at farm location. Free, no key.
- **NASA POWER** (already integrated) for historical climatology baselines.
- **APHLIS+ loss tables** — African Postharvest Losses Information System, downloadable CSV per country/crop/year at `https://www.aphlis.net/en/data/tables/dry-weight-losses/{ISO2}/all-crops/{year}` (e.g. `.../SN/all-crops/2021`). ([APHLIS](https://www.aphlis.net/en), [ADM Postharvest Institute](https://postharvestinstitute.illinois.edu/phl-data/)).
- **Published threshold rules** from FAO and CIMMYT: maize ≤ 13–14 % MC for safe storage, groundnut ≤ 7 % MC; A. flavus growth arrested below 0.65 water activity; 90 % RH + 25–35 °C = high risk. ([FAO X5036E control of aflatoxin](https://www.fao.org/4/x5036e/x5036e0s.htm), [CIMMYT grain drying](https://www.cimmyt.org/news/affordable-grain-drying-and-storage-technologies-cut-down-aflatoxins/), [ResearchGate 332144884](https://www.researchgate.net/publication/332144884_Effect_of_temperature_relative_humidity_and_moisture_on_aflatoxin_contamination_of_stored_maize_kernels))

**Tool signature sketch:**
```python
def aflatoxin_storage_risk(lat: float, lon: float, crop: str,
                           harvest_date: str, storage_type: str,
                           current_moisture_pct: float | None) -> dict:
    """
    Combines Open-Meteo 7-day forecast (T, RH, rain) + APHLIS baseline loss
    for (country, crop) + moisture thresholds.
    Returns: risk tier (low/med/high/critical), projected equilibrium moisture
    content under forecast conditions, days-to-safe-dry estimate, specific
    mitigation (sun-dry schedule, PICS bag recommendation, Aflasafe eligibility).
    """
```

**Why it beats the field:** no existing AI advisor produces **actionable drying schedules under tomorrow's weather**. Google ALU does not touch storage. Apollo is pre-harvest only. FAO guidance is static PDF.

**Effort:** 2 days. Open-Meteo is already wired; APHLIS tables are small CSV; threshold logic is a few dozen lines. Add PICS-bag and Aflasafe registration lookup as static country table (Aflasafe is registered in 12 SSA countries per [IITA](https://www.iita.org/news-item/scaling-aflasafe-from-lab-based-innovation-to-large-scale-aflatoxin-mitigation-across-africa/)).

---

### #2 — Livestock disease + vaccination calendar (BIGGEST COVERAGE GAP)

**Problem (one line):** 60–80 % of smallholders run poultry, goats, cattle alongside crops; Newcastle disease kills up to 80 % of unvaccinated flocks per outbreak, PPR causes 50–80 % morbidity in goats/sheep, and no AI advisor currently addresses animals. Vaccination coverage in Ethiopia/Uganda/Tanzania for Newcastle is only ~26–36 % — knowledge gap, not vaccine gap. ([PMC 10855203](https://pmc.ncbi.nlm.nih.gov/articles/PMC10855203/), [ILRI vaccines](https://www.ilri.org/tags/vaccines), [ILRI news making vaccination work](https://www.ilri.org/news/making-livestock-vaccination-campaigns-work-farmers-east-africa))

**Data sources:**
- **WOAH WAHIS** — World Animal Health Information System, global outbreak registry since 2005. Public web + dashboard; a reverse-engineered Python client exists at [GitHub loicleray/WOAH_WAHIS.ReportRetriever](https://github.com/loicleray/WOAH_WAHIS.ReportRetriever) and an R package at [GitHub ecohealthalliance/wahis](https://github.com/ecohealthalliance/wahis). Official page: [WAHIS at woah.org](https://www.woah.org/en/what-we-do/animal-health-and-welfare/disease-data-collection/world-animal-health-information-system/).
- **FAO EMPRES-i / EMPRES-AH** — Emergency Prevention System, covers Newcastle, PPR, ASF, HPAI officially, supports EMA-i mobile reports. ([FAO EMPRES-AH](https://www.fao.org/animal-health/our-programmes/emergency-prevention-system-for-animal-health-(empres-ah)/en))
- **ILRI priority-disease tables** — published participatory-epidemiology rankings for SSA sheep/goats/poultry: pasteurellosis, CCPP, PPR, Orf for small ruminants; Newcastle, Gumboro, coccidiosis for poultry ([Springer 10.1007/s11250-019-02187-4](https://link.springer.com/article/10.1007/s11250-019-02187-4)).

**Tool signature sketch:**
```python
def livestock_advisor(lat: float, lon: float, animal: str,
                      herd_size: int, last_vaccination: str | None) -> dict:
    """
    1) Query WAHIS scraper for outbreaks of diseases-of-interest within 500 km
       and last 90 days.
    2) Return region-specific vaccination calendar (Newcastle I-2 thermotolerant
       quarterly for chickens; PPR every 3 yrs for small ruminants; ECF ITM
       for cattle in East Africa highlands).
    3) Warn if outbreak-positive district nearby.
    4) Concurrent-vaccine bundling advice saves ~70 % cost per
       [ILRI concurrent vaccines](https://www.ilri.org/news/concurrent-vaccines-could-reduce-cost-disease-prevention-goats-and-sheep).
    """
```

**Why it beats the field:** every competitor ignores livestock. Adding one tool covers the other half of the smallholder income stream.

**Effort:** 3 days. WAHIS scraper exists; calendar rules are published; vaccination schedules are a static rule-table keyed on (country, species, age).

---

### #3 — Pest-outbreak proximity alerts (Fall armyworm + desert locust)

**Problem (one line):** Fall armyworm (FAW) has spread to 70+ countries since 2016 with 20–50 % maize yield loss in SSA; desert locust swarms reach 80 million adults per km² and wipe crops in a day. Farmers rarely know an outbreak is in the next district until it's on their plot. ([FAO FAW](https://www.fao.org/fall-armyworm/en/), [FAO Desert locust outbreak 2026](https://www.fao.org/plant-production-protection/news-and-events/news/news-detail/desert-locust-outbreak-persists-in-northwestern-africa-control-measures-must-increase-to-avoid-further-spread-in-2026/en))

**Data sources:**
- **FAO FAMEWS global platform** (Fall Armyworm Monitoring and Early Warning System) — mobile-app-fed pheromone-trap reports, mapped globally. ([FAMEWS global platform](https://www.fao.org/fall-armyworm/monitoring-tools/famews-global-platform/en/))
- **FAO Locust Hub** (ArcGIS) — layers for hoppers, bands, adults, swarms, control operations. Exact download endpoint confirmed: `https://data.apps.fao.org/catalog/dataset/desert-locusts-observations` → CSV with columns `category, lat, lon, start_date, area_impacted_in_ha, location_name`, CC-BY 3.0 IGO. A BigQuery endpoint also exists: `https://api.data.apps.fao.org/api/v2/bigquery?query=SELECT+...+FROM+fao-maps-review.fao_locusts.Adult_last_month`. ([FAO Locust Hub](https://locust-hub-hqfao.hub.arcgis.com/), [FAO data catalog locust observations](https://data.apps.fao.org/catalog/dataset/desert-locusts-observations))
- **PlantwisePlus Knowledge Bank (CABI)** — 4 000 pest factsheets, 15 000 content items; no public API but scrapable factsheet URLs. ([CABI PlantwisePlus](https://www.cabi.org/plantwiseplus/), [Knowledge Bank](https://plantwiseplusknowledgebank.org/))

**Tool signature sketch:**
```python
def pest_outbreak_proximity(lat: float, lon: float, radius_km: int = 200,
                            days_back: int = 30) -> dict:
    """
    Pull locust observations from FAO BigQuery endpoint filtered by bbox + date.
    Pull FAMEWS FAW trap counts by country.
    Return list of nearby outbreaks with distance, severity, and linked
    PlantwisePlus control factsheet URL.
    """
```

**Why it beats the field:** converts static situation bulletins into farmer-specific push-style warnings. Google ALU knows the field boundary but not the threat.

**Effort:** 1.5 days. CSV pull + haversine + join on species → factsheet URL.

---

### #4 — Soil moisture + evapotranspiration irrigation advisor

**Problem (one line):** Smallholders decide irrigation timing by habit or visual inspection; under-irrigation costs 15–30 % yield, over-irrigation wastes fuel/water. Real soil-moisture and ET data solve this but are locked behind geospatial tooling only a researcher can use.

**Data sources:**
- **NASA SMAP L3 Enhanced** 9 km daily soil moisture (`SPL3SMP_E`), via Earthdata login (free) or **Google Earth Engine** (`NASA/SMAP/SPL3SMP_E/006`) for free scripted access. ([NSIDC SPL3SMP_E v6](https://nsidc.org/data/spl3smp_e/versions/6), [GEE catalog SMAP](https://developers.google.com/earth-engine/datasets/catalog/NASA_SMAP_SPL3SMP_E_006))
- **MODIS MOD16A2 evapotranspiration** — 500 m, 8-day composite global vegetated ET. ([NTSG U Montana](https://www.umt.edu/numerical-terradynamic-simulation-group/project/modis/mod16.php), [LAADS MOD16A2](https://ladsweb.modaps.eosdis.nasa.gov/missions-and-measurements/products/MOD16A2))
- **NASA GRACE-FO groundwater drought indicator** (Goddard / U Nebraska-Lincoln weekly, 0.25°). ([nasagrace.unl.edu](https://nasagrace.unl.edu/), [GRACE JPL](https://grace.jpl.nasa.gov/data/get-data/))
- **Copernicus ERA5-Land hourly reanalysis** via `cdsapi`. ([CDS ERA5 single levels](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels))

**Tool signature sketch:**
```python
def irrigation_advisor(lat: float, lon: float, crop: str,
                       days_since_last_irrigation: int) -> dict:
    """
    Pull SMAP root-zone moisture, MOD16 ET for current 8-day window,
    Open-Meteo forecast rain next 7 days, GRACE groundwater anomaly.
    Compute crop-specific water-deficit index; return:
    - recommended irrigation depth (mm)
    - skip-irrigation flag if rain > ET in next 72 h
    - drought-context message if GRACE anomaly < -1 sigma
    """
```

**Why it beats the field:** FarmVibes has SMAP ingestion but no farmer-facing advisor. Google ALU detects wells visually but does not tell a farmer *when to pump*. This is straightforwardly actionable and saves diesel/electricity.

**Effort:** 2.5 days. Use GEE Python API for SMAP and MOD16 (no Earthdata credential needed); GRACE indicator is a single weekly raster.

---

### #5 — Government-scheme eligibility + deadline navigator

**Problem (one line):** Nigeria NIRSAL, Kenya e-voucher subsidy, India PM-Kisan (~$72/yr for 98M farmers) and e-NAM mandi prices exist, but farmers miss windows or are excluded because nobody explains in their language what they qualify for and by when. Kenya's e-voucher issued 836,000 vouchers for maize farmers in 10 counties — enrolment is by SMS but farmers don't know. ([IFPRI Kenya subsidy](https://www.ifpri.org/blog/how-kenyas-national-fertilizer-subsidy-program-working/), [Safaricom-MoA](https://www.safaricom.co.ke/media-center-landing/press-releases/ministry-of-agriculture-selects-safaricom-to-streamline-subsidy-voucher-program), [PM-Kisan portal](https://pmkisan.gov.in/))

**Data sources:**
- **India data.gov.in OGD APIs** — Agmarknet daily mandi prices via `https://api.data.gov.in/resource/{resource-id}?api-key=...&format=json`. Registration for key is free; 3,000 mandis × 200 commodities covered. ([data.gov.in catalog](https://www.data.gov.in/catalog/current-daily-price-various-commodities-various-markets-mandi), [data.gov.in APIs list](https://www.data.gov.in/apis)).
- **World Bank Enabling the Business of Agriculture (EBA)** — seed-registration, fertilizer-registration, finance-access, livestock, plant-health indicators for 101 countries. ([EBA topics](https://eba.worldbank.org/en/exploretopics), [World Bank Data Catalog](https://datacatalog.worldbank.org/search/dataset/0038944/enabling-the-business-of-agriculture)).
- **Scheme metadata tables** (hand-curated from NIRSAL, AFA Kenya, PM-Kisan, eNAM, FISP Zambia): sliding-window enrolment dates, crop lists, subsidy values. No central API exists — this is what ClimaSense can *become*.

**Tool signature sketch:**
```python
def scheme_navigator(country: str, crop: str | None, farm_size_ha: float,
                     holdings: list[str]) -> list[Scheme]:
    """
    Return open schemes:
     - name, eligibility check (crop/size/region), enrolment deadline,
       estimated value in local currency, required documents, registration URL.
    Agmarknet sub-call for India returns nearest mandi + next 3 days price trend.
    """
```

**Why it beats the field:** nobody does this. Apollo ties farmers to *Apollo* products; government schemes are free money farmers leave on the table. Bilingual + voice-queryable via Gemma 4 E2B is killer for low-literacy users.

**Effort:** 3 days for core schemes (India PM-Kisan + eNAM, Kenya AFA, Nigeria NIRSAL, Rwanda SNS, Ethiopia ATI, Zambia FISP). Data is a static YAML of rules; dynamic part is Agmarknet + WFP price pulls.

---

## 4. De-prioritised (good ideas, wrong trade-off)

- **Parametric-insurance quoting.** Apollo/Pula/ACRE have no public developer APIs; partnership-gated, 4 weeks too short.
- **Counterfeit-input detection.** Requires national supplier registries (Kenya KEPHIS, Nigeria NAFDAC) that are not public.
- **Re-implementing AMED / ALU / GraphCast.** We would be a thin wrapper. Better to consume them if admitted to trusted-tester, else skip.

---

## 5. Recommended 10-day build plan

| Day  | Add                                                  | Hrs |
|------|------------------------------------------------------|-----|
| 1–2  | Aflatoxin + post-harvest drying advisor (#1)         | 14  |
| 3–5  | Livestock + vaccination calendar (#2)                | 20  |
| 6    | Pest-outbreak proximity (#3)                         | 8   |
| 7–8  | Irrigation / soil-moisture / ET (#4)                 | 16  |
| 9–10 | Scheme navigator + Agmarknet (#5)                    | 18  |

Each tool prevents a *quantified* loss (grain mould, flock death, locust swarm, water waste, missed subsidy) via a named, free, documented data source. The resulting 15-tool agent covers post-harvest + livestock + pest + water + financial layers that none of Google ALU, FarmVibes, AgWise, Apollo, or Pula offer in one conversational agent.

---

## Sources

All URLs are cited inline in the sections above; the complete list (deduplicated) is:

Post-harvest / aflatoxin — https://www.aphlis.net/en • https://www.aphlis.net/en/data/tables/dry-weight-losses/SN/all-crops/2021 • https://postharvestinstitute.illinois.edu/phl-data/ • https://www.fao.org/4/x5036e/x5036e0s.htm • https://www.cimmyt.org/news/affordable-grain-drying-and-storage-technologies-cut-down-aflatoxins/ • https://www.nature.com/articles/s41538-023-00238-7 • https://cabiagbio.biomedcentral.com/articles/10.1186/s43170-024-00305-3 • https://www.researchgate.net/publication/332144884 • https://www.iita.org/news-item/scaling-aflasafe-from-lab-based-innovation-to-large-scale-aflatoxin-mitigation-across-africa/ • https://www.cgiar.org/news-events/news/ai-tool-makes-invisible-enemy-visible-tackling-aflatoxin-risk-in-africas-maize • https://e-catalogs.taat-africa.org/com/technologies/pics-hermetic-bags-for-safe-storage-of-grain

Livestock — https://www.woah.org/en/what-we-do/animal-health-and-welfare/disease-data-collection/world-animal-health-information-system/ • https://github.com/loicleray/WOAH_WAHIS.ReportRetriever • https://github.com/ecohealthalliance/wahis • https://www.fao.org/animal-health/our-programmes/emergency-prevention-system-for-animal-health-(empres-ah)/en • https://www.ilri.org/tags/vaccines • https://www.ilri.org/news/making-livestock-vaccination-campaigns-work-farmers-east-africa • https://www.ilri.org/news/concurrent-vaccines-could-reduce-cost-disease-prevention-goats-and-sheep • https://pmc.ncbi.nlm.nih.gov/articles/PMC10855203/ • https://link.springer.com/article/10.1007/s11250-019-02187-4

Pest outbreak — https://www.fao.org/fall-armyworm/en/ • https://www.fao.org/fall-armyworm/monitoring-tools/famews-global-platform/en/ • https://locust-hub-hqfao.hub.arcgis.com/ • https://data.apps.fao.org/catalog/dataset/desert-locusts-observations • https://www.fao.org/plant-production-protection/news-and-events/news/news-detail/desert-locust-outbreak-persists-in-northwestern-africa-control-measures-must-increase-to-avoid-further-spread-in-2026/en • https://www.cabi.org/plantwiseplus/ • https://plantwiseplusknowledgebank.org/

Water / irrigation — https://www.earthdata.nasa.gov/data/platforms/space-based-platforms/smap/data-access-tools • https://nsidc.org/data/spl3smp_e/versions/6 • https://developers.google.com/earth-engine/datasets/catalog/NASA_SMAP_SPL3SMP_E_006 • https://www.umt.edu/numerical-terradynamic-simulation-group/project/modis/mod16.php • https://ladsweb.modaps.eosdis.nasa.gov/missions-and-measurements/products/MOD16A2 • https://grace.jpl.nasa.gov/data/get-data/ • https://nasagrace.unl.edu/ • https://cds.climate.copernicus.eu/ • https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels

Schemes / markets — https://pmkisan.gov.in/ • https://www.data.gov.in/apis • https://www.data.gov.in/catalog/current-daily-price-various-commodities-various-markets-mandi • https://www.agmarknet.gov.in/ • https://eba.worldbank.org/en/exploretopics • https://datacatalog.worldbank.org/search/dataset/0038944/enabling-the-business-of-agriculture • https://www.safaricom.co.ke/media-center-landing/press-releases/ministry-of-agriculture-selects-safaricom-to-streamline-subsidy-voucher-program • https://www.ifpri.org/blog/how-kenyas-national-fertilizer-subsidy-program-working/

Competitive prior art — https://agri.withgoogle.com/ • https://developers.google.com/agricultural-understanding/landscape-understanding • https://arxiv.org/html/2411.05359v1 • https://blog.google/technology/ai/how-ai-is-improving-agriculture-sustainability-in-india/ • https://github.com/microsoft/farmvibes-ai • https://news.microsoft.com/source/features/ai/microsoft-open-sources-its-farm-of-the-future-toolkit/ • https://deepmind.google/blog/graphcast-ai-model-for-faster-and-more-accurate-global-weather-forecasting/ • https://github.com/google-deepmind/graphcast • https://www.cgiar.org/news-events/news/raising-productivity-and-profits-how-agwise-is-closing-yield-gaps-through-ai/ • https://github.com/AgWISE-EiA/AgWISE-generic • https://www.linkedin.com/company/apollo-agriculture/ • https://www.pula-advisors.com/post/growing-credit-access-for-farming-communities-through-embedded-insurance • https://www.ifc.org/content/dam/ifc/doc/2024/pula-ifc-2024.pdf
