# Klinos Phase 0 Roadmap

**Purpose:** when your wife (or her friend) asks *"when does Klinos actually let me open my doors full-service?"* — this is the honest answer.

**Companion doc:** `EPIC_GAP_ANALYSIS.md` lists what's missing. This doc says when each item lands and why the sequence is what it is.

**Disclaimer:** all timelines are best-estimate ranges with known external gating (certification processes, third-party integrations). Actual dates depend on engineering resource allocation and dependencies surfacing late. **Josh to validate / adjust based on real capacity.**

---

## The decision framework

For the wife's decision right now, **two questions matter:**

1. **Can I run a pilot practice in T+0 weeks?** — a dozen known patients, limited scope, I accept the gaps.
2. **Can I run a full practice in T+9 months?** — all patients, full insurance, controlled substances, compliance-grade.

Both need to be true-ish. The first gets her in the door; the second is what she's really signing up for when she quits her job.

---

## Sprint 0 — Pilot mode (T+0 to T+4 weeks)

**What the pilot cohort can do safely, today:**
- See a small self-selected patient panel (≤25 patients) paying cash or membership-only
- Use the AI-drafted note workflow on every visit
- Use Care view to hand off patient-facing info
- Use templates to shape AI behavior
- Send prescriptions as paper / call-in (not e-prescribe yet)
- Order labs via direct phone/fax to lab partner (not integrated yet)
- Document everything in Klinos; use paper for anything unsupported

**What they explicitly cannot do yet:**
- Prescribe controlled substances (no EPCS)
- Accept insurance-billed visits (no claims infrastructure)
- Send/receive imaging digitally
- Report immunizations to state registries
- Reliably check drug-drug or drug-allergy interactions

**Success criteria for pilot → Phase 0 graduation:** 25-50 patient visits logged, physician validates note quality, zero major clinical errors caught.

---

## Phase 0 — Safety + regulatory essentials (T+1 to T+3 months)

The "cannot practice without" bucket. Gate to ending pilot caveats.

### Safety layer
- **Drug-allergy checking** — structured allergy → drug cross-reference. Uses RxNorm + First Databank (or equivalent).
  - *Realistic: 6–8 weeks once DB licensed.*
- **Drug-drug interaction checking** — same data source, different rule set.
  - *Realistic: +2 weeks after drug-allergy lands (same integration).*
- **Pre-sign clinical warnings** — banner in the review phase when the AI drafts something that fails a safety check. Physician can override with a reason captured in the audit log.
  - *Realistic: 2–3 weeks UI work; parallelizable with DB integration.*

### Regulatory essentials
- **E-prescribe via Surescripts** — cert + integration. *Realistic: 3–4 months; starts during pilot.*
  - Sub-cert 1: Prescriber-to-pharmacy (send Rx)
  - Sub-cert 2: Refill requests
  - Sub-cert 3: Change / cancel
- **PDMP integration (first state)** — state-by-state; start with practice's home state. Via Bamboo Health / Appriss or Surescripts PDMP. *Realistic: 2 months after Surescripts base is up.*
- **E&M coding validation** — rule engine over CMS MDM tables (2021 revision). *Realistic: 4–6 weeks.*
- **Immunization registry reporting** — HL7 VXU messages to state registry. *Realistic: 4–6 weeks first state.*

### Practice ops
- **Real scheduling (MVP)** — provider slots, reschedule, cancel, visit-type-specific duration. *Realistic: 6–8 weeks.*
- **Staff roles + permissions (MVP)** — provider / MA / front-desk / billing. Uses DyadID grant model extended to practice-role scopes. *Realistic: 4–6 weeks.*

**Exit Phase 0 at:** E-prescribe certified, PDMP connected in home state, drug-drug + drug-allergy checks live, E&M validation live, scheduling MVP live, staff roles live. Pilot cohort can take insurance patients.

---

## Phase 0.5 — Controlled substances + real telehealth (T+3 to T+6 months)

### EPCS (Electronic Prescribing of Controlled Substances)
- Separate cert from base Surescripts
- DEA requires identity-proofing vendor (ID.me or equivalent) + 2FA at Rx time
- *Realistic: 2–3 months after base Surescripts cert.*

### Imaging
- **PACS viewer** — start with link-out to radiology group's existing viewer. Then embed.
  - *Realistic: 2 months for link-out, +2–3 months for embedded viewer.*
- **Imaging order dispatch** — via HL7 ORM. First partner: local radiology group. *Realistic: 2 months.*

### Lab integration (first partner)
- Quest OR LabCorp (practice choice). HL7 ORM + ORU.
- *Realistic: 2–3 months.*

### Patient communication
- **Telehealth video** — integrate with Zoom SDK or Doxy.me. HIPAA-compliant BAA in place. *Realistic: 4–6 weeks.*
- **Messages tab (Care view)** — UI ships on top of existing Anima thread infrastructure. *Realistic: 3–4 weeks.*

### Insurance prep
- **Eligibility verification (270/271)** — via clearinghouse (Change Healthcare / Availity). *Realistic: 2 months.*

**Exit Phase 0.5 at:** EPCS live, imaging link-out live, first lab partner integrated, telehealth video working, Care Messages tab shipped, eligibility check live. Full clinical workflow except claims submission.

---

## Phase 1 — Insurance + full operations (T+6 to T+9 months)

### Billing
- **Insurance claims (837) + remittance (835)** — via same clearinghouse as eligibility. Payer-specific rules per specialty. *Realistic: 3–4 months.*
- **Superbill / charge capture** — ICD+CPT → itemized claim. *Realistic: 2 months, parallelizable.*
- **Prior authorization** — CoverMyMeds or Surescripts PA. *Realistic: 2–3 months.*

### Care coordination
- **Referral tracking** — status of outbound referrals, consult notes received. *Realistic: 2 months.*
- **Chart search across panel** — "every patient on Lisinopril" type queries. *Realistic: 4–6 weeks.*
- **Document management** — patient-uploaded photos, outside records, consent forms. *Realistic: 4–6 weeks.*

### Specialty foundations (OBGYN — for your wife's friend)
- **Prenatal flowsheets** — structured prenatal visits, routine labs, fundal height tracking. *Realistic: 2 months.*
- **Post-partum workflows** — 6-week visit, contraception counseling, PPD screening. *Realistic: 1 month after prenatal.*

### Specialty foundations (peds — if applicable)
- **Growth charts** — CDC + WHO chart integration. *Realistic: 1 month.*
- **Immunization schedule recommendations** — CDC lookup engine. *Realistic: 1 month.*
- **Developmental milestones tracking.** *Realistic: 1 month.*

**Exit Phase 1 at:** insurance claims submitting + reconciling, prior auth flowing, referral lifecycle tracked, core OBGYN + peds coverage live. **This is "full practice" feature parity for most PCPs.**

---

## Phase 1.5 — Interop + migration (T+9 to T+12 months)

### Legacy EHR migration
- **Epic chart import tool** — white-glove service for practices leaving Epic. Uses FHIR export where available, chart-extraction where not. *Realistic: 3 months, per-EHR.*
- **Athena / Cerner / eClinicalWorks** — secondary targets.

### Cross-EHR interop
- **Care Everywhere / Carequality participation** — become a participating node. *Realistic: 3–4 months including governance process.*
- **HIE participation** — state/regional HIE. *Realistic: 2 months per HIE.*

### Additional states + integrations
- **PDMP — additional states.** 1–2 months per.
- **Immunization registries — additional states.** 1 month per.
- **Additional lab partners.** 4–6 weeks per.

**Exit Phase 1.5 at:** Klinos is a legitimate Epic alternative for PCP / OBGYN independent practices. Cross-EHR patient record sharing works. Migration tooling in place.

---

## Phase 2 — Quality, population health, ecosystem (Year 2)

- **MIPS / HEDIS quality-measure reporting** — CMS-certified reporting module. *Realistic: 4–6 months.*
- **Population health panels** — care-gap reports, chronic-disease cohorts, proactive outreach. *Realistic: 3 months.*
- **FHIR APIs for third-party apps** — SMART-on-FHIR compatible. *Realistic: 3–4 months.*
- **Specialty-specific registries** — oncology, transplant, endocrine, etc. Per-specialty.
- **Medicare ACO reporting** — if practices opt in.
- **Clinical trial matching** — integrate with ClinicalTrials.gov or TrialNet.

---

## Intentional non-goals (not on any timeline)

Epic has these. Klinos should not pursue them even at scale.

- Inpatient / hospital floor workflows
- OR scheduling, anesthesia records
- ED tracking boards
- Enterprise data warehousing (Clarity/Caboodle scale)
- Research infrastructure (IRB, registries at scale)
- Operational analytics for hospital CIOs
- Health-system billing (facility + pro-fee)

---

## What the wife's transition plan looks like

**Week 0 — decision to join as pilot.** She doesn't quit her day job. She sees a small cohort (≤25 self-selected patients) on Klinos on the side or during a transition period.

**Month 1-3 — Phase 0 ships.** She can now prescribe via Surescripts, check allergies, validate E&M codes, schedule properly, have her MA use the system. She begins migrating appropriate patients from Epic.

**Month 3-6 — Phase 0.5 ships.** She can now prescribe controlled substances, do real telehealth, order imaging, get labs back digitally. She can see most of her panel on Klinos without paper workarounds.

**Month 6-9 — Phase 1 ships.** She can bill insurance claims. She can leave Epic entirely if she wants.

**Month 9-12 — Phase 1.5 ships.** Migration tools mature; she can formally wind down Epic access. Interop lets her send records to the hospital when admitting.

**Realistic quit-her-day-job moment:** Month 6-9, once claims submission is live and she's validated the workflow on 100+ patients.

**For her OBGYN friend:** add 2-3 months because of prenatal flowsheet dependency + L&D considerations. Realistic full-OBGYN launch: Month 9-12.

---

## Critical path callouts

Three items have hard external gating and need to start the certification process as early as possible:

1. **Surescripts cert** — start immediately after pilot begins. Can't be compressed.
2. **EPCS cert** — parallel to Surescripts; depends on DEA identity-proofing infrastructure.
3. **Insurance clearinghouse contracts** — start negotiating during Phase 0, ready for Phase 1.

Anything else can sequence around these.

---

## Dependencies Josh needs to validate

- **Eng capacity assumption:** this roadmap assumes 2-3 full-time engineers beyond Josh, including one with healthcare-integration experience. If staffing is lighter, timelines stretch proportionally.
- **Third-party costs:** Surescripts ($), Clearinghouse ($$), FDB / Lexicomp drug DB ($$), ID.me ($), BAA legal review ($) — all ongoing line items; budget needs to reflect.
- **Regulatory / legal:** HIPAA security risk assessment, SOC 2 Type I by end of Phase 0.5, SOC 2 Type II by end of Phase 1 (practices will start asking once panels grow).

---

*Last updated: 2026-04-16*
*Companion: `EPIC_GAP_ANALYSIS.md`, `DEMO_SCRIPT.md`, `SPEC.md` §15 (build phases)*
