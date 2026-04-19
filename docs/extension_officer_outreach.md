# Extension-Officer Outreach — getting one real quote for the writeup

**Goal:** one on-record, two-sentence quote from an agricultural extension officer or smallholder-focused researcher, usable in the final writeup and video. The single highest-ROI credibility move per the differentiation analysis.

**Target effort:** ~5 hours outreach + 45-minute call + 30-minute editing.

## Who to approach (ranked by likelihood of response)

### Tier 1 — researchers who publish on smallholder AI advisors

1. **Digital Green team** — authors of the Farmer.Chat paper. Approachable via:
   - General email: `info@digitalgreen.org`
   - Authors listed on [arXiv 2409.08916](https://arxiv.org/html/2409.08916v1) — Namita Singh (first author)
   - LinkedIn group: https://www.linkedin.com/company/digital-green/

2. **AICCRA** (Accelerating Impacts of CGIAR Climate Research for Africa) — they actively seek AI-for-smallholder partners.
   - Portal: https://aiccra.cgiar.org/
   - Contact form on site; they usually respond within a week.
   - Named contact in recent news: Dr. James Kinyangi (coordinator)

3. **Wadhwani AI** — built Krishi Sahayak with Gemini + AI4Bharat. India-focused but agnostic.
   - Contact: https://www.wadhwaniai.org/contact/
   - LinkedIn: company/wadhwani-ai

### Tier 2 — field-oriented NGOs with known AI-receptivity

4. **One Acre Fund**. 1M farmers by 2027 target. Tech team.
   - https://oneacrefund.org/careers-tech (proxy for tech-team DMs on LinkedIn)
   - Email general: communications@oneacrefund.org

5. **Apollo Agriculture** (Kenya). ML credit + agronomy.
   - https://www.apolloagriculture.com/
   - LinkedIn: company/apollo-agriculture (message one of the agronomy leads)

6. **CABI PlantwisePlus** — they maintain the pest factsheets you linked.
   - https://www.cabi.org/plantwiseplus/contact/
   - Keep the message short, reference Plantwise Knowledge Bank usage in your tool.

### Tier 3 — researcher-first (longer latency but higher prestige if they respond)

7. **IITA Aflasafe team** — Dr. Ranajit Bandyopadhyay (principal scientist) and the Aflasafe comms lead. They are *very* interested in smallholder-facing aflatoxin tools.
   - https://www.iita.org/contact-us/
   - Twitter/X: @IITA_CGIAR

8. **ICRAF / CIFOR-ICRAF** — agroforestry + smallholder research.
   - https://www.cifor-icraf.org/contact-us/

9. **Penn State PlantVillage** — Dr. David Hughes (built Nuru).
   - https://plantvillage.psu.edu/about
   - Email: drhughes@psu.edu (public)

## What to send — email template

Subject line options (pick one, keep under 60 chars):

- "30-min review: Gemma-4 agri agent for smallholders"
- "Seeking your critique on a smallholder AI advisor demo"
- "Quick feedback on agentic crop advisor for Kenya / India"

### Template body

> Dear [Dr./Prof./Mr./Ms.] [Last name],
>
> I'm [Name], a researcher building ClimaSense — an open-source agricultural advisor for smallholder farmers, entered in the Gemma 4 Good Hackathon (Kaggle, deadline May 18).
>
> Unlike most agri-chatbots, ClimaSense uses Gemma 4's native function-calling to orchestrate 11 live-data tools in one farmer query: Open-Meteo weather, ISRIC SoilGrids soil, NASA POWER planting calendar, WFP HDX market prices, Sentinel-2 NDVI satellite imagery via Microsoft Planetary Computer, PlantVillage disease matcher, and a new aflatoxin/post-harvest drying advisor that combines hourly weather with FAO/CIMMYT moisture thresholds. It runs on Gemma 4 E4B for on-device voice and 31B for reasoning.
>
> I'd value 20–30 minutes of your time to walk you through one Kenya (Kisumu) and one India (Maharashtra) scenario end-to-end and hear what a farmer in your network would get wrong about the output. The repository is Apache 2.0: https://github.com/Ramesh-Arvind/climasense
>
> If the tool is useful, I'd like your permission to quote 1–2 sentences by name and role in the final writeup and the 2-minute video submission, with a link back to your organisation. If it isn't useful, that's honest feedback I need too.
>
> I'm flexible Mon–Fri this week and next; a 15-minute call works equally well. Would a [Tuesday 3 pm CET / Thursday 9 am EAT / Wednesday 2 pm IST] slot work?
>
> Thank you for considering,
>
> [Name]
> [Affiliation]
> [Email] · [Phone]

### LinkedIn DM variant (shorter — 600 char limit)

> Hi [Name], I'm building an open-source Gemma-4 agricultural advisor (ClimaSense) that orchestrates 11 live-data tools — weather, soil, satellite NDVI, post-harvest aflatoxin — for smallholders in SSA and S. Asia. Hackathon deadline May 18. Could I show you a 15-min Kenya + India scenario and get your critique? Apache 2.0, no commercial ask. If the tool helps, I'd like to quote you by name in the submission. Flexible scheduling.

### Twitter/X variant

> Building a Gemma-4 agri-advisor (@GoogleDeepMind hackathon) that calls Sentinel-2 NDVI + WFP prices + FAO aflatoxin thresholds in one conversational turn. Open-source. Would love 15 min of feedback from someone who actually works with smallholders. Reply or DM — thanks!

## What to cover in the 20-minute call

1. **Introduce the scenario.** "Amina, maize farmer in Kisumu County. She messages: 'leaves curling yellow, unusually hot and dry.' Let me show you what ClimaSense does."
2. **Show the agentic loop live.** Run the Kenya Kisumu scenario from `scripts/agent_e2e_test.py` — takes 45 seconds. Let them see which tools fire.
3. **Ask the three specific questions:**
   - "If a farmer you work with saw this output, what would they *do* with it?"
   - "Which of the 11 data sources do they already trust? Which would they ignore?"
   - "What's missing that they need more than what's shown?"
4. **Close:** "May I quote you by name — 'X, role at Y' — in the writeup? Two sentences max. You'll see the quote before submission."

## What you'll paste into the final writeup

Target sentence template (tune to the actual quote):

> *"[Reviewer Name], [role] at [organisation], reviewed ClimaSense during a 30-minute session on [date]: 'the [specific tool or output] is more precise than what we currently give farmers. The main gap is [honest limitation]. I would pilot this with [specific farmer group].'"*

The specificity of the honest-limitation clause is the credibility lever. Judges notice.

## Tracking

Keep a simple log in `docs/outreach_log.md` (create when you start):

```
| Date       | Contact                       | Channel    | Status     | Notes |
|------------|-------------------------------|------------|------------|-------|
| 2026-04-20 | Namita Singh (Digital Green)  | Email      | Sent       |       |
| 2026-04-22 | AICCRA contact form           | Web        | Replied    | meeting scheduled May 5 |
```

Aim to contact 5–8 people in the first day. One responder in the first week is typical and sufficient.
