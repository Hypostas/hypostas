# Klinos — Pitches by length

Short-form pitch ammunition. Pick the length that fits the moment.

- **30 seconds** — the stranger-at-dinner pitch
- **90 seconds** — the "tell me more" pitch
- **5 minutes** — the intro-before-the-real-demo pitch
- **Twitter / LinkedIn one-liner** — the social version

All four say roughly the same thing at different resolutions. You don't need to memorize verbatim — these are scaffolds, not scripts.

Paired with the pitch-day walkthrough in `DEMO_SCRIPT.md`, the honest-gap assessment in `EPIC_GAP_ANALYSIS.md`, the sequencing in `PHASE_0_ROADMAP.md`, and the lived-experience narrative in `DAY_IN_THE_LIFE.md`. This is the short stuff.

---

## 30 seconds — the stranger-at-dinner pitch

> "I'm building a practice-management platform for independent doctors. The core idea is that the AI drafts every note on the doctor's own machine — nothing ever leaves the device — and every patient has their own AI that reads their chart back to them in plain language. It's the first EHR where both the doctor and the patient have their own AI, and it's built on a sovereignty protocol where the patient owns their data by default. My wife is a PCP. She'll be the first practice on it."

**What this does:** gives them enough to form a picture. Establishes positioning (not Epic), establishes differentiator (on-device AI + patient-owned data), establishes credibility (wife is first customer). Ends with a name-hook so if they have follow-up questions they can start with "so your wife…"

**What to do if they ask a follow-up:** go to the 90-second version.

---

## 90 seconds — the "tell me more" pitch

> "So the healthcare tech problem, as you know, is that the EHR — the electronic health record — is built for the hospital, not the doctor. Epic is the dominant one. It's incredible for billing and compliance, but doctors spend two to three hours a day typing into it, and patients log into MyChart and see raw clinical notes they can't parse.
>
> Klinos flips both of those. On the doctor side: the visit records itself, and the AI drafts the SOAP note on the doctor's own laptop — never the cloud. The doctor edits one sentence, signs, done. Twelve seconds. No typing. No per-draft API fee.
>
> On the patient side: the same note gets translated into plain language by the patient's own AI — they have a personal AI companion that already knows their health story — and the raw clinical note is still there if they want it, one tap away. The patient also has, by default, a visible record of every doctor who accessed their chart, what scope, when. They can revoke any grant in one tap.
>
> The business model is direct primary care — monthly membership per patient. Practices leave Epic, set up Klinos in weeks, keep their income because the practice collects the fees directly.
>
> My wife is a PCP. She's the first practice. We're piloting with her panel, and the architecture is built so any independent practice can join once it's validated."

**What this does:** explains the two-sided flip (doctor + patient), names the business model, grounds it in a specific first-customer story.

**The anchor moment for retention:** "twelve seconds. No typing." That's the concrete thing they remember.

---

## 5 minutes — the intro-before-the-real-demo pitch

Use this when someone has actual time — a coffee, an investor call, a physician friend. It's long enough to build real context but short enough that you can follow it with the live demo without losing the room.

> **"Let me frame this in two parts: what's broken, and what we're doing about it.
>
> **What's broken.** The EHR is the most important piece of software in medicine, and it's built wrong for the people who use it most. Doctors spend roughly a third of their clinical time typing into Epic or Cerner or Athena — documentation that exists mostly for billing and compliance. Burnout in American PCPs is running 50% or higher. Practices are consolidating into health systems because they can't afford to run their own infrastructure, and independent practices are closing. Patients, meanwhile, log into patient portals and see their raw SOAP notes and either skip them or Google their way into anxiety. There's no translation. There's no continuity between visits. There's no sense that anyone is watching the patient's long-term story — the EHR is point-in-time and defensive.
>
> **What we're doing.** Klinos is the EHR built for the world where every clinical note can be drafted by an AI that runs on the doctor's laptop, and every patient has their own AI companion that can translate, triage, and hold context between visits.
>
> Three things are different.
>
> **First, the AI is on the doctor's device.** We run Gemma 4 26B locally. The visit transcript, the patient's history, the biomarkers, the drafted note — none of it ever leaves the machine. We don't have a per-note API cost. The doctor doesn't have to wonder what's happening to their patient's data. It's a sovereignty product, not a compliance product.
>
> **Second, every note is shaped by the doctor.** Not templates in the Epic SmartText sense — LLM-aware templates. The doctor writes, once, 'for my annual exams, always cover these screenings and always use this language.' The AI applies those instructions on every matching visit. Five built-in templates for the common visit types. The doctor clones and customizes them. Their notes sound like them because they wrote the template once.
>
> **Third, the patient has their own AI.** Not a portal. A continuous companion that already knows the patient's health story, reads the doctor's notes back to them in plain language, triages their between-visit questions, and escalates with context when something needs human attention. Sovereignty means the patient owns their data by default; the Anima is what makes that sovereignty useful instead of burdensome.
>
> **The business model is direct primary care.** Practices sell memberships — $299, $399, $599 per patient per month — and Klinos takes a platform fee. Practices leave Epic in weeks, not months. They keep their income because they collect the membership fees directly. The launch cohort gets a 50% platform-fee discount for 24 months.
>
> **My wife is the first practice.** She's a PCP. Her best friend is an OBGYN. Both are independent and unhappy with the EHR they're on now. We're piloting with a small panel — a dozen patients — on a scoped release, and the full Phase 0 plan — Surescripts, PDMP, insurance claims, full telehealth — lands over the next six to nine months. By month nine, a practice can run Klinos as their only EHR.
>
> **The demo I'll show you next is real.** It runs on my laptop. The AI draft you see is not a simulation — it's Gemma writing the note from the actual transcript. The patient-side Care view is the same data the doctor just signed, translated. And the gap I'll flag at the end — things Epic has that Klinos doesn't — is honest. Some of them are Phase 0 blockers. Some of them are intentional non-goals. The `EPIC_GAP_ANALYSIS` doc has the full breakdown.
>
> **That's the pitch.** Want to see it?"**

**Timing check:** read aloud at natural pace, this is almost exactly 5 minutes. Trim the business-model paragraph if you need to cut 30 seconds. Trim the third paragraph under "What's doing" if you need to cut 60.

**Transition to demo:** end on "Want to see it?" and open the Practice view.

---

## Twitter / LinkedIn one-liner

Pick your favorite:

> The AI that drafts your clinical notes runs on your laptop. Your patient's AI reads those same notes back to them in plain language. Built on the sovereignty protocol. This is the EHR for the independent practice.

> Epic is for health systems. Klinos is for the independent doctor who wants her practice back.

> An EHR where on-device AI drafts every note in 12 seconds, and every patient has their own AI that actually knows them. First practice: my wife.

> Doctors have spent a decade typing into Epic. We're shipping the last decade of their career back to them.

---

## "What do you do?" — the really short one

> "I'm building the EHR for independent doctors. On-device AI, patient-owned data, built for the future where every practice has its own practice again."

---

## Speaking notes — reusable phrases that stick

Use these in any length. They're the ones that travel.

- **"Twelve seconds. No typing."** — the concrete anchor for doctors
- **"Nothing ever leaves the device."** — the sovereignty anchor for patients + investors
- **"An EHR where both sides have their own AI."** — the framing anchor for anyone
- **"Practices leave Epic in weeks, not months."** — the operational anchor for practice owners
- **"My wife is the first practice."** — the credibility anchor for everyone
- **"The AI is a scribe. I'm still the doctor."** — the safety anchor for clinicians

Memorize these six. The rest of the pitch falls into place around them.

---

## When NOT to pitch

- If they ask "what do you do?" at a funeral, a medical emergency, or in a bathroom. Say "I'm working on a thing." Move on.
- If they're a competitor. Be vague, stay polite, stop.
- If they're a pharma rep looking for a channel. Politely redirect.
- If you're tired and the pitch won't land well. Reschedule. A bad pitch is worse than no pitch.

---

*Paired docs: `DEMO_SCRIPT.md`, `EPIC_GAP_ANALYSIS.md`, `PHASE_0_ROADMAP.md`, `DAY_IN_THE_LIFE.md`.*
