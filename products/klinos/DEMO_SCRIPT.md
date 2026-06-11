# Klinos Pitch Demo — Walkthrough

Target audience: Josh's wife (PCP, considering Klinos).
Target length: ~15 minutes.
Goal: convince her the tool respects her workflow, her preferences, and her patients' sovereignty — without forcing her into a new paradigm.

Demo covers:
- Practice Today view (morning landing)
- Sarah Chen — chronic-disease visit (hero)
- Jamie Rivera — acute URI visit (guardrails)
- Templates customization
- Care view handoff (patient side)

---

## Pre-demo setup (5 min before she arrives)

1. **Ollama running** with `gemma4:26b` loaded.
   ```bash
   curl -s http://localhost:11434/api/tags | grep gemma4:26b
   # Expect a line like: "gemma4:26b" ...
   ```
2. **Anima app running** in tauri dev mode (`npm run tauri dev` or equivalent).
3. **Land on Chat view.** The opening `Cmd+Shift+K` is part of the moment.
4. **Close DevTools** — the window should look lived-in, not developer-inspected.

---

## Act 1 — The landing (1 min)

**Action:** `Cmd+Shift+K`
**She sees:** Practice → Today

**Narrate:**
> "This is the first thing you see every morning. Five visits today, three urgent items, two notes from yesterday waiting for your signature, and the overnight summary — everything your Anima handled while you were asleep."

**Point to, in order:**
- **Urgent** (top-left) — real-time clinical signals from Bios
- **To-sign** — async messages + drafted notes queued
- **Today's schedule** — 5 patients with prep-ready flags
- **Async** — non-urgent messages the Anima triaged
- **Overnight summary** — what happened while you slept

**Key framing:** *"Nothing here came from manual chart review. Your Anima assembled this before you woke up."*

---

## Act 2 — Sarah Chen: chronic-disease hero visit (~5 min)

This is the centerpiece. Spend real time.

**Action:** Click **Sarah Chen** in today's schedule → PatientDetail opens.

### Patient chart (30 sec)
- Top strip: "52F · HTN + hypothyroidism · quarterly check-in · pharmacy gap flagged"
- **Medications tab** — Lisinopril with the **adherence note already flagged** (14-day fill gap, self-discontinued). *"Your Anima already knew, before you opened the chart."*
- **Biology tab** — home BP avg 148/92 vs 128/82 baseline, HRV stable
- **Timeline tab** — last visit, medication starts, labs

**Action:** Click the "**Start visit →**" button (top-right).

### InVisit surface (3 min)

**Before starting playback, call out the header:**
1. **Template picker** — auto-selected **"Chronic Disease Follow-up"**. Say: *"Before we say a word, the AI knows how you write chronic-disease notes."*
2. **Draft source toggle** — leave on **"Live Gemma"** if Ollama is healthy. Mention: *"Live means on-device — nothing leaves the machine."*

**Action:** Click **"Start visit"** → transcript plays line-by-line, co-pilot events appear on the right panel.

**Call out co-pilot events as they fire:**
- **0s** — "Lisinopril refill gap" (concerning) — *the AI spotted the adherence gap from pharmacy data before the visit*
- **35s** — "ACE-inhibitor cough — classic presentation" (notable) — *fires the moment Sarah reveals the cough*
- **95s** — "ARB alternative" (notable) — *composed Losartan 50mg as the evidence-based swap*
- **135s** — "E-prescribe ready" (ambient) — *prescription already drafted to her CVS pharmacy*

**Option A:** Let playback run the full 5:43. Good if the demo has time to breathe.
**Option B:** After ~90s of playback, click **"End visit"**. The story is made by then.

### The draft reveal (~12 sec on 26B)

**Narrate while it runs:**
> "Watch this. Nothing is leaving the machine. Your patient's data stays on your device. This is local Gemma 26B running on-device."

**When the SOAP note reveals, point to:**
- **Assessment** explicitly calls out the adherence gap: *"self-discontinuation of Lisinopril"*
- **ICD-10 codes include T50.5X5A** (adverse effect of antihypertensive drugs). Say: *"Did you know that code existed? The template knew."*
- **`prescription_drafts`** contains Losartan 50mg with "replaces Lisinopril" annotation — *the template's rule ("if plan changes a medication, emit the prescription") fired*
- **Referral** to Anna Park, RD for nutrition
- **Patient summary** at the bottom — 8th-grade reading level, warm tone, already translated
- **Header chip: `▸ Chronic Disease Follow-up`** — confirms which template shaped this draft

**OPTIONAL — edit inline before signing (~20 sec):**
Click anywhere in the Plan section. Cursor lands in place. Tweak a detail — e.g. change "14 home BP readings" to "10 home BP readings (weekdays only)." The header sprouts a **`✎ Edited`** chip.
> *"Every section is editable. Click, type, save. The signed note is whatever you actually sign — not the AI's first draft."*

**Action:** Click **Sign**.

### Post-sign handoff (30 sec)
**She sees:** Post-sign confirmation card with artifact counts (Rx: 1, Referrals: 1, ICDs: 4).

**Action:** Click **"See patient's view ↗"**.

---

## Act 3 — Sarah's Care view (patient side) ~2 min

This is the emotional beat. Let it breathe.

**She sees:** Mobile-first surface. "Hi, Sarah. Here's what's going on with your health right now."

### Home tab (30 sec)
- **Next visit** card — 6-week follow-up with Dr. [founding PCP]
- **Attention** (yellow cards): "Losartan starts tomorrow", "Take 14 BP readings", "Note ready"
- **Recent activity** feed: signed note, Rx sent, nutrition referral, lab review — all timestamped "just now" / "2m ago"

**Action:** Tap the "Read note" attention item → jumps to Records tab, new note highlighted.

### Records tab (45 sec)
- Note renders in **plain language first** — no clinical jargon
- **Tap "Show clinical note"** → the physician-signed SOAP expands inline below
- Scroll to **Medications** — Losartan has a **"New" chip**, full plain-language blurb ("Take one 50mg tablet every morning. Losartan is a blood-pressure medication that works the same way as your old Lisinopril but doesn't cause a cough...")
- Scroll to **Labs** — Q2 panel with patient-friendly interpretation ("Your thyroid is stable. Your blood sugar has ticked up slightly — still in the 'pre-diabetes' range, but trending upward...") + **"Show raw values"** tap-through to the actual numbers

### Access tab (45 sec)

> "And this — this is what no other EHR has."

- **Pending approval**: Anna Park, RD requesting scope for the nutrition visit — "Approve" / "Deny" buttons right there
- **Active access**: Dr. [founding PCP] has full-chart access, one-tap Revoke
- **Emergency Access Policy** card — shows "Break-glass with strict limits" (default). Tap-to-change.
- **Recent access** (audit trail) — every action from today's visit, timestamped, with scope classes: "Signed today's visit note", "Switched Lisinopril → Losartan 50mg", "Sent nutrition referral"

**Key framing:** *"Sovereignty made legible. She approves every new provider. She sees every access. She can revoke anything."*

**Action:** Press **Escape** → back to Sarah's physician chart.

---

## Act 4 — Jamie Rivera: the guardrails demo (~3 min)

Shorter and sharper. The contrast matters.

**Action:** Press **Escape** → Practice Today. Click **Jamie Rivera**.

### Patient chart (20 sec)
"28F · URI day 5 with new productive cough · otherwise healthy runner"
Background: 10km/week distance runner. Main question: when can I run again.

**Action:** Click **Start visit**.

### In the InVisit surface (2 min)

**Call out the template picker:** auto-selected **"URI / Acute Respiratory"**.

**Action:** Click **Start visit** → transcript plays.

**The critical co-pilot moment at ~75s — the "Antibiotic stewardship" card (concerning intensity):**
> *"No bacterial indicators present. ACP guidelines: antibiotics are not indicated for uncomplicated viral URI, even with cough >7 days. Evidence: Cochrane reviews find no meaningful reduction in duration or complication rate; real harm from antibiotic exposure (resistance, C. diff, adverse reactions)."*

**Say while this fires:**
> "Watch this event. This is the template's guardrail talking to the AI."

**Action:** End visit, let it draft live.

### The money shot — the SOAP reveal

**Point to:**
- **`prescription_drafts: []`** — EMPTY
- **Plan** starts: *"Supportive care, **no antibiotics**. Honey 1 tsp PO prn for cough..."*
- **No referrals. No labs.** Just supportive care + return precautions + HRV-gated return to training.

**Say:**
> "The template told the AI: do not draft antibiotics for viral URIs unless there are bacterial indicators. It listened. Jamie has a productive cough for five days and the AI refused to write a Z-Pak. That's the guardrail."

**Optional:** Sign → Patient's view. Jamie's Care Home is **deliberately quieter** — no next-visit card, no new Rx, no referrals. Just note-ready + training-watch explanation. *"She came in for reassurance. She got it. The Care surface reflects that."*

---

## Act 5 — Templates: your customization (~3 min)

Where she sees **she's in control**, not the AI.

**Action:** **Escape** to Practice → click **Templates** in the left rail.

### Template list
Master/detail pane. Built-ins alpha-sorted on the left (Annual Wellness, Chronic Disease Follow-up, New Patient Intake, Procedural, URI). Editor on the right.

**Action:** Click **Annual Wellness Exam**.

**Point to:**
- **"built-in" pill** next to the name (read-only)
- The full **prompt addendum** — scroll through the USPSTF screening, CV risk, immunizations, behavioral-health screening items, coding guidance (Z00.00 vs Z00.01, CPT 99396/99397)
- **Match patterns**: `annual`, `wellness exam`, `physical`, `preventive`

### Cloning + customizing
**Action:** Click **"Clone to customize"**.

**Edit something her wife would genuinely want.** Options:
- Add: *"I always use USPSTF 2024 guidelines."*
- Add: *"My BP goal for patients with ASCVD risk >10% is <130/80."*
- Add: *"When weight comes up, use motivational-interviewing language. Never use shame-based framing."*

Type into the big textarea. Click **Save**.

**Say:**
> "Every annual visit you do from now on, the AI applies these preferences. No more reading a note and thinking 'that's not how I write.' Your notes sound like you, because you wrote the template once."

### Optional deep-cut (if time permits)
Go back to Today, click Marcus's annual visit, Start visit, End visit, Live Gemma — watch the AI draft respect the customizations you just wrote. Adds 2-3 minutes but makes the feature real.

---

## Act 6 — Close (~1 min)

Back to Practice Today.

**Say:**
> "That's Klinos. Your morning starts with everything pre-triaged. Every visit drafts on your device — nothing leaves the machine. Every note sounds like you because you wrote the template once. And every patient has their own Anima reading it to them in plain language, with the original always one tap away."

**Pause. Let the room sit.**

---

## Known gotchas + failure-mode playbook

| If... | Then... | Say... |
|---|---|---|
| Ollama is down or not responding | Toggle to **Mock** in the InVisit header | "Let me show you the draft UI with our canned example — the architecture story is the same." |
| 26B flakes on a draft | Backend auto-retries on 31B (~2.5 min extra) | "It's taking longer than usual because it's computing on your machine, not a data center. Here's what the Phase 0 plan looks like..." (buy time) |
| 31B retry also fails | Falls back to mock silently | No need to narrate — looks identical |
| A template draft takes longer than 15s | Keep talking | "This is local compute — you don't pay a per-draft API fee" |
| She asks about editing the draft before signing | **Click any SOAP section** → cursor lands, type. | "Click anywhere in the note. Every field is editable. When you edit, the header shows an ✎ Edited chip so you can see at a glance what's different from the AI draft." |
| She asks about insurance / billing | **Out of scope for this build** | "See §14 of the spec for the full business model — Basic/Standard/Comprehensive tiers, HSA/FSA compliant." |

---

## Likely questions + crisp answers

| Question | Answer |
|---|---|
| "What happens if my internet is out?" | On-device model. Drafting works entirely offline. Only things that need internet: e-prescribe send, pharmacy confirmations, insurance calls. |
| "How much does this cost me / cost the patient?" | Per §14: Basic $299, Standard $399, Comprehensive $599 per patient per month — bundled with Anima. Launch cohort: 50% platform-fee discount for 24 months. |
| "What if I don't want to edit templates?" | Don't. The built-ins are production-ready. Many PCPs never customize. |
| "Can my patients opt out of the Care view?" | Yes. Care is a view inside the Anima app. They choose what surfaces to use. Chat works without Care. |
| "What about malpractice?" | You sign every note. The AI's draft is a draft. Your signature is your medicine. |
| "How does this compete with Epic?" | It doesn't compete — different customer. Epic is for health systems. Klinos is for independent practices that want to leave Epic behind. |
| "What if the AI hallucinates a drug dose?" | Low temperature (0.2), structured JSON output, physician review before signing. The validator auto-retries on 31B if the 26B draft fails schema. You sign the truth, not the draft. |
| "Will it warn me if I'm about to prescribe something the patient's allergic to?" | **Yes.** Every drafted Rx is cross-checked against the patient's documented allergies before Sign — both direct name matches and drug-family cross-reactivity (sulfa, penicillin, cephalosporin, NSAID, ACE, statin, opioid). Danger-severity warnings render above the SOAP and **block the Sign button** until you either acknowledge them (captured in the audit log with your reason) or edit the Rx out of the draft inline. Phase 0 replaces this string-match layer with First Databank integration — this is the demo-visible safety layer until that lands. |
| "Where does my data go?" | DyadID-encrypted, on-device-first. Klinos is a HIPAA Business Associate; your practice is the Covered Entity. See §9. |
| "What if I have two practices?" | Each practice has its own DyadID relationship with the patient. Access scopes don't cross. |
| "How do I get started?" | Launch cohort: 50% platform fee for 24 months. Onboarding in ~2 weeks. White-glove migration if you're coming from an existing EHR. |

---

## Demo variants (if time is tight)

**10-minute version:**
- Act 1 (1 min)
- Act 2 Sarah visit (5 min) + Act 3 Care view (2 min)
- Act 5 Templates (2 min — just browse, don't edit)
- Skip Jamie + close
- Total: ~10 min

**5-minute version:**
- Skip Act 1
- Sarah full loop (Patient chart → Start visit → playback fast-forward to draft → Sign → Patient's view, ~3.5 min)
- Templates list view, 45 sec
- Close, 30 sec
- Total: ~5 min

**Raw 90-second pitch (no click-through):**
Open Practice Today, screenshot the schedule. Flip to a signed note and the Care view beside it. Flip to Templates and scroll the Annual Wellness Exam addendum. That's the whole story.

---

## Optional mid-demo moment — drug-allergy safety gate

If the wife asks *"will it warn me when I'm about to prescribe something she's allergic to?"* — you can show it live in under a minute.

**The setup:** Diane Kowalski has a documented **sulfa allergy**. Her current drafted Rx (fludrocortisone) doesn't trigger it.

**The demo:**
1. From Practice Today, open Diane → Start visit → End visit → let the Gemma draft reveal.
2. In the Plan section, click inline edit.
3. Type: `Bactrim 800mg BID` into the prescription_drafts area *(or paste "Sulfamethoxazole-trimethoprim 800mg"*).
4. **A red `⚠ 1 allergy check` chip appears in the header.** A big red danger banner renders above the SOAP: *"Allergy conflict — Allergy on file: sulfa drugs. Drafted Rx: Bactrim 800mg BID. Cross-reactivity: 'bactrim' is in the sulfa family..."*
5. The **Sign button is disabled** — tooltip says "Cannot sign: 1 unacknowledged drug-allergy warning."
6. Click **Acknowledge** on the banner → chip turns amber, Sign enables → *"In Phase 0 that acknowledgment is captured in the audit log with your reason."*

**What to say:**
> "Every drafted prescription is cross-checked against this patient's documented allergies — direct name match plus drug-family cross-reactivity. The AI doesn't trust itself. I don't have to remember. The system refuses to let me sign a note with an unacknowledged drug-allergy conflict."

This is a 60-second moment that closes one of Epic's Bucket A gaps.

---

## Checklist before she sits down

- [ ] Ollama running, `gemma4:26b` loaded
- [ ] Anima app on Chat view
- [ ] No DevTools / no other dev-looking windows
- [ ] Network-off is fine (everything clinical works offline)
- [ ] Your own computer, not a demo rig (she'll ask)
- [ ] This doc open on your phone, muted, for reference mid-demo if you blank

---

*Last updated: 2026-04-16*
