# Klinos vs Epic — Gap Analysis

**Purpose:** prep Josh for pitch-day questions from his wife (PCP with Epic experience).
**Framing:** Klinos isn't Epic — it's the tool an independent practice uses to leave Epic. The right comparison is *what does she need to practice safely and get paid*, not feature-count parity.

**Scope:** ambulatory primary-care + OBGYN workflows. Inpatient / ED / OR / research are out of scope for Klinos by design.

---

## Where Klinos beats Epic (pitch angles)

| Capability | Epic | Klinos |
|---|---|---|
| AI-drafted SOAP notes | Cloud-only (Epic AI / Nuance DAX); per-note cost; PHI leaves institution | Local Gemma 4 26B on-device; $0 marginal cost; PHI never leaves the machine |
| Template-shaped AI | SmartText is keystroke-expansion, not LLM-aware | Prompt addenda reshape what the AI emits; built-ins + custom |
| Patient portal | MyChart — read-mostly; shows raw physician notes | Care view with Anima-translated plain-language notes; verbatim one tap away |
| Access control visibility | Audit log exists but buried; patients rarely see it | First-class Access tab; every grant + every access timestamped + visible |
| Revocation | Request form; days-to-weeks | One-tap, immediate |
| Emergency access | Break-glass exists; opaque to patient | Break-glass + typed Emergency Access Policy (4 variants, patient picks) |
| Continuous biology | No native wearables integration; Apple Health point-in-time at best | Stroma/Bios 24/7 signal synthesis; biology snapshot in every chart |
| Between-visit conversation | "Send message to clinic"; 24-72h reply | Anima 24/7; triages, escalates with full context when human needed |
| Setup | Months; six-figure install; Epic consultants | Weeks; per-patient subscription; self-service |
| Pricing | Health-system-scale license | Basic $299 / Standard $399 / Comprehensive $599 per patient/month, bundled with Anima |

---

## Where Klinos has it partially (demo shows, Phase 0 wires)

These are features the demo visually shows but aren't functional on real integrations. Your wife may not realize they're mocks unless she asks.

| Capability | What the demo shows | What's missing |
|---|---|---|
| E-prescribe | Rx appears in SOAP + "e-prescribed to pharmacy" co-pilot event | Surescripts certification + integration |
| EPCS (controlled substances) | Not shown | DEA-required identity proofing + two-factor. Blocker for post-partum opioids, anxiolytics, pain mgmt |
| Lab orders | `lab_order_drafts` field on the SOAP | Quest / LabCorp / in-house LIS integration for order dispatch + result receive |
| Referrals | `referral_drafts` field | Real specialist-side dispatch; return-consult tracking |
| Scheduling | Today view renders a schedule | Provider availability management, self-scheduling, waitlist, reschedule, resource booking |
| Insurance | Not shown | Eligibility verification; prior auth; claims submission (837) + remittance (835) |
| Imaging | Not shown | PACS viewer + order dispatch |

**Demo-day handling:** When asked about any of these, be honest. *"Phase 0 wires the real integration. What you're seeing is the UI shape the physician interacts with — the plumbing underneath is on the 3-6 month roadmap."*

---

## Genuine gaps — what Klinos doesn't have

### Bucket A — Cannot practice safely without

Must land before any real patient is treated.

- **PDMP integration** — state-mandated check before prescribing controlled substances. Unwired = regulatory non-compliance.
- **Drug-drug interaction checking** — First Databank, Lexicomp, or equivalent. AI-in-draft may catch some but isn't a safety system.
- **Drug-allergy interaction checking** — ⚠ **partially closed (demo-visible).** The pre-sign safety layer now cross-checks every drafted Rx against the patient's allergies (direct name match + drug-family cross-reactivity for sulfa / penicillin / cephalosporin / NSAID / ACE / statin / opioid). Danger warnings block the Sign button until acknowledged. Phase 0 still replaces this with First Databank for production-grade coverage — the string-match layer covers the classic families but isn't exhaustive.
- **Immunization registry reporting** — every vaccine must report to state registry. Flu + COVID alone are high-volume.
- **Imaging** — ordering + PACS viewer. PCP sees 15-25 imaging reports/week.
- **E&M coding validation** — CPT picker doesn't verify the documented work supports the code billed. Denied claims.
- **ADT interfaces** — hospital admission/discharge notifications. If a panel patient is admitted, the PCP should know.

**Recommended action:** These are the gate to "can your wife practice on this." Phase 0 timeline for Bucket A items should be ≤90 days post-pilot-start, tracked against a real launch date.

### Bucket B — Must-have for a real practice (beyond safety)

Needed to run a practice day-to-day, not just prescribe safely.

**Clinical workflow:**
- Real telehealth video (not just a visit-type label)
- Secure two-way patient messaging surface (§11 Messages tab — spec'd, unbuilt)
- Chart search ("find every patient on Lisinopril")
- Growth charts (any peds in panel)
- Prenatal / post-partum flowsheets (OBGYN)
- Immunization schedule recommendations (CDC lookup)
- Clinical decision support beyond templates (BPAs, order sets)
- Lab trend graphs / flowsheets (multiple labs over time)
- Vital signs flowsheet (BP, weight, pulse over time)

**Practice ops:**
- Staff roles + permissions (nurse, MA, receptionist, billing, provider)
- Superbill / charge capture (ICD+CPT → actual bill line items)
- Prior authorization workflow (Rx, imaging, referrals)
- Referral status tracking (did patient see specialist? what happened?)
- Patient self-scheduling portal
- Waitlist for cancellations
- Family / proxy access (teen consent, elderly parent)
- Document management (patient-uploaded photos, outside records, consent forms)

**Billing:**
- Insurance eligibility check at check-in
- Membership billing (actually, Klinos has this via §8 model — practice-owned)
- HSA/FSA compliance (spec'd, not fully built)
- Payment processing integration

### Bucket C — Roadmap items, not launch blockers

- Care Everywhere / Carequality (cross-EHR record sharing)
- Full FHIR APIs for 3rd-party app ecosystem
- HIE participation
- MIPS / HEDIS quality-measure reporting
- Population health panels + care-gap reports
- Clinical trials matching
- Developmental milestones (peds)
- Newborn screening integration
- Medicare ACO reporting
- Specialty-specific registries (oncology, transplant, etc.)

### Bucket D — Intentional non-goals

Epic does these. Klinos should not, at least not in the first 24 months.

- Inpatient / hospital floor workflows
- OR scheduling, anesthesia records
- ED tracking boards
- Enterprise data warehousing (Clarity/Caboodle equivalent)
- Research infrastructure (IRB, registries)
- Billing infrastructure at health-system scale
- Operational analytics for CIOs

---

## Demo-day risk — questions that expose gaps

Have prepared answers for these. They're the questions your wife will ask.

| Question | Honest answer |
|---|---|
| "Does this actually send the prescription to the pharmacy?" | Phase 0 wires Surescripts. Demo is UI-level today. |
| "Can I prescribe controlled substances?" | Not yet — EPCS requires DEA identity proofing. On the 3-6 month roadmap. For the OBGYN, this means post-partum opioids go through the current workflow until then. |
| "Will it warn me if I'm prescribing something she's allergic to?" | The AI draft often catches it from context. Not a guaranteed safety system yet. Clinical decision-support integration is in Phase 0 Bucket A. |
| "How does this talk to Quest / LabCorp / my hospital lab?" | Phase 0. Demo shows the UI shape; the integration is on the roadmap. |
| "Can my MA or front-desk use this?" | Single-user at the moment. Multi-role permissions are a roadmap item — probably month 3-6. |
| "What about my existing patients' records?" | White-glove migration at launch. We build a one-time data-import tool per EHR. |
| "Does this submit insurance claims?" | Membership billing is built in (§8). Insurance claims submission (837/835) is Phase 1+. Most Klinos practices bill insurance only for labs/procedures, not visits. |
| "What if my internet dies mid-visit?" | AI drafting is on-device — keeps working. Only things that need internet: pharmacy send, insurance check, patient messaging. |
| "Does it integrate with Apple Health? Oura? WHOOP?" | Yes, via the Anima. Continuous data flows as biology context to the physician chart. |
| "Can a patient's previous doctor see the note?" | Scoped access grant model (§4). Patient approves, specialist sees scoped data. No blanket sharing. |
| "How long is my data portable if I leave Klinos?" | DyadID-based — patient owns the key. Practice exports are supported. Spec §12 covers entity structure. |
| "What's different from Athena / Cerner?" | Both are cloud-EHRs with AI add-ons. Neither has on-device AI, dyad-native sovereignty, or continuous biology as first-class features. |

---

## Strategic takeaway

**The real pitch:** "You lose features by leaving Epic. You gain three things Epic can't give you:
1. **AI that runs on your device** — nothing leaves the machine; cost doesn't scale with drafts.
2. **Patients who own their data** — sovereignty as the product, not a compliance checkbox.
3. **A practice that fits in a browser tab** — set up in weeks, priced per patient, no health-system scaffolding."

**The real question is which Bucket A gaps are dealbreakers and which aren't:**
- If wife is okay practicing without controlled substances for 3-6 months, EPCS can wait
- If wife mostly sees chronic disease (Sarahs) and annual exams (Marcuses), imaging integration can wait longer than if she does a lot of acute care
- If wife will stay on Epic for some patients during a transition period (running both in parallel for 6-12 months), the gaps become less acute
- If wife's friend is doing OBGYN full-service (L&D, post-partum), the gaps compound fast

**Best transition pattern:** start with a subset of the panel — the chronic-disease and annual-wellness patients — on Klinos. Keep Epic for acute / peds / procedural for the first 6 months. Phase 0 wires the missing integrations, and the panel migrates over as each integration lands.

---

*Last updated: 2026-04-16*
*Relevant SPEC sections: §3 (architecture), §4 (access), §8 (business model), §11 (patient UI), §14 (pricing), §15 (build phases)*
