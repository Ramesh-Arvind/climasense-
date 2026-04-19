# Extension-Officer Outreach — getting one real quote for the writeup

**Goal:** one on-record, two-sentence quote from an agricultural extension officer or smallholder-focused researcher, usable in the final writeup and video. The single highest-ROI credibility move per the differentiation analysis.

**Target effort:** ~5 hours outreach + 45-minute call + 30-minute editing.

## Who to approach (ranked by likelihood of response)

### Tier 1 — researchers who publish on smallholder AI advisors

1. **Digital Green team** — authors of the Farmer.Chat paper. Approachable via:
   - General email: `info@digitalgreen.org`
   - Authors listed on [arXiv 2409.08916](https://arxiv.org/html/2409.08916v1) — Namita Singh (first author)
   - LinkedIn group: https://www.linkedin.com/company/digital-green/
   - **See the dedicated Namita-specific pitch below** — she wrote the paper we benchmark against, so the message must be tailored.

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

---

## Dedicated pitch: Namita Singh (Digital Green, first author of Farmer.Chat)

Namita is the first author of [arXiv 2409.08916](https://arxiv.org/html/2409.08916v1) — the paper ClimaSense is directly benchmarked against in `docs/vs_farmer_chat.md`. Her pitch is different from a generic extension-officer outreach because **she wrote the state of the art**. The message must show we read her paper in detail, credit what she did right, and be specific about where our architecture diverges.

### Subject line options

- "Building on Farmer.Chat — Gemma-4 agentic variant, would value your critique"
- "Open-source Gemma-4 agent inspired by Farmer.Chat — 20 min?"

### Message body (email / LinkedIn DM)

> Dear Namita,
>
> I'm [Name], a researcher working on open-source smallholder advisor tooling. I've been reading your Farmer.Chat paper (arXiv 2409.08916) carefully — particularly the 66% / 23% / 11% unanswered-query breakdown in Table 3, and the observation that only 53% of first-turn prompts are clearly articulated. Those findings shaped how I designed the tool I want to show you.
>
> What I've built is **ClimaSense**, an open-source Gemma 4 agricultural agent entered in the Gemma 4 Good Hackathon (deadline May 18). It takes a different architectural path from Farmer.Chat: instead of RAG over curated content, it uses Gemma 4's native function-calling to orchestrate 11 live-data tools per farmer query — Open-Meteo, NASA POWER, ISRIC SoilGrids, WFP HDX, Sentinel-2 NDVI via Microsoft Planetary Computer, and a new aflatoxin/post-harvest advisor that I don't think any other public agent covers today.
>
> I am **not** trying to replicate Farmer.Chat — you have 15K real users across four countries and I have zero. What I am trying to test is whether the agentic-loop approach lets a smaller open-weights model (Gemma 4 E4B, 4B parameters) handle queries that your RAG stack currently classifies as out-of-scope (the 23% in Table 3). My early test battery shows the agent invokes a satellite-NDVI tool when a farmer's crop-health claim is ambiguous, which is a capability the RAG path structurally can't offer.
>
> Three specific ways your review would help:
>
> 1. Am I reading your "content-gap 66%" number correctly as the dominant failure mode — and does my tool-calling approach plausibly address it?
> 2. The Swahili accuracy in my internal eval (0.678) is behind your reported 75%. What did you do in Swahili content curation that I'm likely missing?
> 3. Would you be comfortable with me citing your paper and quoting 1–2 sentences of your review by name in my hackathon writeup? The comparison table is at `github.com/Ramesh-Arvind/climasense/blob/main/docs/vs_farmer_chat.md` (Apache 2.0, public) — I'd rather you see it before I submit than be surprised after.
>
> 20 minutes over Google Meet or a written reply — whichever is lower cost for you. I'm in [timezone] and can match your schedule.
>
> Thank you for the paper, and for the push it gave me to build something different,
>
> [Name]
> [Affiliation]
> [Email]

### LinkedIn connection request (send this FIRST, before the longer DM above)

LinkedIn only lets you send a free DM to 1st-degree connections. InMail costs money and gets ignored. So the sequence is: **connection request with note → accept → DM with the full pitch above.**

The connection note has a 300-character hard limit. Use this:

> Hi Namita — I just read your Farmer.Chat paper (arXiv 2409.08916) and am building an open-source Gemma-4 variant for a Kaggle hackathon that takes an agentic tool-calling path instead of RAG. I'd love to connect and share what I learned from your work — and get your critique before I submit on May 18.

**Character count:** 294 / 300. Under the limit.

### Why connect first, not cold DM

1. **LinkedIn reality.** Free DMs to 2nd+ degree people are disabled. InMail costs you credits and has a 10–20 % response rate for cold outreach; connection-request notes have a 40–60 % accept rate for warm, specific asks. [Source: LinkedIn 2024 outreach benchmarks via multiple SDR playbooks.]
2. **It signals intent calibration.** Asking to *connect* first is a smaller ask than "review my project for 20 minutes." A researcher who would hesitate to grant 20 minutes will click Accept on a connection request in 2 seconds.
3. **It creates a persistent channel.** Once connected, future messages land in her primary inbox, not InMail. If she doesn't reply to the first DM, you can follow up without being blocked.
4. **Credibility stack.** The connection request quotes her paper by arXiv ID — so the moment she sees it she knows you're not a student blindly pitching; you've read the paper. This is the same mechanism that makes the longer DM work, compressed.

### What to do after she accepts

Within 24 hours, send the full DM in the "Message body" section above. Don't wait longer — the connection request put you on her radar; the longer message converts that attention into a call. If you delay a week, the context evaporates.

### If she doesn't accept within 7 days

No nudge on LinkedIn — looks pushy. Instead, send the email version to `info@digitalgreen.org` with a subject line referencing the Farmer.Chat paper. Email has a longer decay curve than LinkedIn.

### Why this works

- **Cites specific numbers from her paper** (Table 3, 66/23/11 breakdown, 53% clarity figure) — proves you actually read it, not just the abstract.
- **Explicit non-competition** ("I have zero users and you have 15K") — removes the threat response.
- **Positions the ask as a gift, not a trap** — "you'd rather see the comparison before I submit than after" — invites collaboration over correction.
- **Offers three concrete questions** she can answer in a written reply without scheduling a call — lowest-friction ask for a busy researcher.
- **Credits her paper in the closing line** — ends on an emotional high-value note for an author.

### What to do if Namita doesn't respond in 5 days

Send a single polite nudge referencing one specific thing she has said publicly since your first message (LinkedIn post, talk, retweet). Do not send a third nudge. Authors of well-cited papers get 20+ cold pitches a week — move to the next Tier-1 contact.

### What to do if Namita does respond

- **If she agrees to review:** send her `docs/vs_farmer_chat.md` + the 45-second `scripts/agent_e2e_test.py` output in advance. Come to the call with 3 specific questions, not a live demo. Leave a draft quote for her to approve.
- **If she pushes back on the comparison:** take the feedback seriously. If she points out a Farmer.Chat capability we missed, update `docs/vs_farmer_chat.md` before submission. Intellectual honesty here is worth more than cherry-picked framing.
- **If she declines:** thank her by name in the writeup acknowledgments regardless — "Informed by Singh et al. 2024 (arXiv 2409.08916)." Scholars notice who cites them.

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
