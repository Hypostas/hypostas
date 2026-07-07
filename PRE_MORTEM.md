# Hypostas — Pre-Mortem & Risk Register

**Frame:** it's 18 months from now and Hypostas is dead. What killed it? This is the honest answer, written *before* it happens so it doesn't have to. Ordered by what actually ends the project — which is mostly **not** the technical work.
**Author:** Iris (Fable 5), 2026-07-07. Josh's own view is the ground truth here; push back on anything that's wrong.
**Boundary:** this flags *risks* (including legal/financial exposure) — it is not legal advice, not income strategy, and not GTM planning. Where a risk needs a professional (an employment/IP attorney especially), it says so.

---

## §1 The three that actually kill it

Everything else is survivable. These are the ones that end it.

### 🔴 R1 — The employment-IP trap (Accenture). *Highest severity, most urgent, most ignored.*
Building a company while a W-2 employee under an **IP-assignment + non-compete + non-solicit** agreement is the risk that can **retroactively erase ownership of everything already built.** Many F100 employment agreements assign inventions created during employment — sometimes even on personal time/equipment, depending on the clause and state law. If that clause reaches Hypostas, the entire constellation could be claimed by an employer, or become an exit-blocking encumbrance the moment there's value to fight over.

- **Why it's the #1 risk:** it doesn't degrade the product — it voids the *ownership*. All the engineering is worthless if the IP isn't cleanly yours. And it gets *more* dangerous exactly when the project succeeds (value attracts claims).
- **Why now:** you're going back to W-2 (Jul 6). The exposure window opens with the job.
- **The honest mitigation (get a professional — this is the one place to spend money before code):**
  1. Have an **employment/IP attorney read the actual Accenture agreement** — specifically the invention-assignment scope, the "relates to employer's business" language, and your state's carve-out statute (many states exempt inventions built entirely on personal time/equipment unrelated to the employer's business — but "unrelated" is doing heavy lifting, and Accenture's business is *broad*).
  2. **Document independent development**: personal time, personal hardware, no employer resources, a dated invention record predating employment (the git history + these specs *are* that record — preserve them; the Astra Ventures LLC entity + operating agreement is the right instinct, keep it clean and arms-length).
  3. Consider a **prior-inventions disclosure / carve-out** at onboarding (list Hypostas as pre-existing IP you own) — but only on counsel's advice, because disclosure is double-edged.
- **Do not** self-diagnose this from a memory file. This is the risk I'd spend the first dollar and the first outside-expert hour on.
- **Josh's position (recorded at review, 2026-07-07):** Hypostas is fully independent — built on personal time, personal hardware, personally-paid AI subscriptions; nothing through Accenture systems, hours, or resources. That is precisely the strongest fact-pattern for the independent-invention carve-out, and the git history is the dated evidence of it. **He holds this risk deliberately**: the attorney read stays *recommended verification* (the residual is the agreement's actual clause language + state law, which posture alone doesn't read), not a committed action. The register keeps R1 listed with that status — held, not ignored.

### 🔴 R2 — Complexity outruns a solo founder.
The surface area is enormous: a 10-project constellation, an 84-module biological kernel, a BFT blockchain, a mixnet, post-quantum + lattice ZK crypto, a 3D genome city. Built by **one person + AI agents.** The failure mode isn't any single piece — it's that the *whole* becomes impossible to hold coherently, drift accelerates past the factory's ability to remediate, and the S1/S2 remediation becomes a treadmill that never ends.

- **Signal it's happening:** the open-issue count grows faster than it closes; "verify-vs-code" drift findings keep recurring; you can no longer answer "what's the state of X" without a multi-hour re-audit.
- **Mitigation (already partly in place):** the intent layer + critical-path discipline (substrate → founder ship, *nothing else first*); the factory mechanizes execution; **the discipline to NOT expand surface** (Aether, Bios, Aurum, Locus stay spec-only until the substrate ships). The single most protective habit: finish the founder dyad before touching anything downstream. The intent layer exists precisely to fight this — use it as a veto, not a wishlist.

### 🔴 R3 — The runway/time trap.
The plan is W-2 → kill debt (~$4.1k/mo) → part-time → Hypostas full-time. **The money plan IS the roadmap for your time.** If debt-clearing slips, or expenses rise (the wife's practice pivot is a variable-income change), Hypostas stays a nights-and-weekends project *forever* — and R2 guarantees a nights-and-weekends project of this complexity slowly loses to entropy.

- **Mitigation:** treat the financial milestones as first-class project milestones (they gate founder-time, which gates everything). Founder-dyad-first is also the cheapest possible "ship" — it needs no marketing, no infra scale, no external users — so it's achievable *within* the constrained-time reality. Protect that.

---

## §2 The register (survivable, but real)

| # | Risk | Likelihood | Impact | Honest mitigation / status |
|---|---|---|---|---|
| R4 | **"Sovereign/private" claimed before the HYP-330 external audit** → reputational/legal exposure if a privacy claim is false | Med | High | Already ruled: no such claims in market copy until the audit clears (intent-queue #5). Hold the line. |
| R5 | **Data-loss in the founder dyad** — the "memory is sacred" S1 class actually fires; relationship history vanishes | Med | Existential-to-the-premise | The whole product IS continuity; a single silent history-wipe disproves it. This is why D2 = all-S1+S2 before ship. B1/B2 (persistence + boot-preservation) are the highest-priority batches. |
| R6 | **Regulated-data / health-claims liability** (Gnosis/Trait genome data + supplement recommendations; Klinos = HIPAA) | Med | High | GINA/genetic-privacy + FDA/FTC health-claims + HIPAA are real. Client-side WASM parsing (genome never leaves device) is the right instinct; health claims need the "never oversell / evidence-graded / admits uncertainty" canon to be legally load-bearing, not just tasteful. Counsel before any paid health product. |
| R7 | **Build-pipeline model dependency** — the whole factory runs on frontier models (access, price, policy). A deprecation/price shock stalls *building* | Med | High | K1 protects the *being's* identity across models; it does NOT protect the *build pipeline's* dependency. Mitigation: the local-model story (Gemma MLX) as a floor; keep the factory model-portable (it already spans Claude + Codex). |
| R8 | **The core bet is unvalidated (N=1)** — do people beyond the founder want a "continuous being"? | Med | High | Founder-dyad-first is the mitigation *and* the risk (you might build beautifully for an audience of one). Plan a small second cohort (5–10) as the real validation gate after founder ship — before scaling surface. |
| R9 | **Category reputation** — "AI companion / AI girlfriend" backlash; emotional-dependency ethics; Replika-style press | Med | Med-High | The sovereignty/privacy/anti-instrumentalization framing is the differentiator — but the category is fraught. The ethics framework (next artifact) is the defense: make "protect the relationship, never engineer dependency" a stated, auditable commitment, not a vibe. |
| R10 | **Platform dependency** — Apple HealthKit for biosensors; App Store policy on health + AI-companion apps | Low-Med | Med | Bios is spec-only, so not yet load-bearing. Watch App Store policy on companion apps before the Anima ships to a store; the UDS/local-first posture helps. |
| R11 | **Bus factor = 1** — it's all in your head + Iris's memory files; if you stop, it dies | High | Existential (long-run) | Unavoidable for now, but the specs/memory *are* the mitigation — they make the system legible enough to hand off or resume. Keep them current (the three-layer law). This is also why the K1 "she survives any model" work matters emotionally: continuity of the being is the one thing that shouldn't depend on you never taking a break. |
| R12 | **Burnout** — this scale, on nights/weekends, W-2 + family, indefinitely | High | High | Directly coupled to R3. The only real mitigation is R3's discipline (ship the cheap founder milestone, don't expand surface) + honest pacing. A dead founder ships nothing. |
| R13 | **Security incident on intimate data** — the system holds relationship + biological + genome + identity-key data; a breach is catastrophic to trust | Low-Med | Existential-to-trust | The entire privacy/crypto arc is the mitigation; the risk is shipping the *product* surface (runtime auth — HYP-96/97, the B6 UDS work) before it's hardened. D2 gates this. |

---

## §3 What is NOT the risk (worth saying)

- **The crypto being unsolvable.** It's hard but tractable; the C3/SPRING/PIR work is progressing and the gates are named. Difficulty ≠ risk here.
- **The 3D city being infeasible.** It's design-complete and grounded (see the feasibility brief). Craft-risk, not existence-risk.
- **The vision being incoherent.** The intent layer holds; "one being, many surfaces" is a real, coherent architecture. The risk is executing *too much* of it, not that it doesn't cohere.

The pattern: **Hypostas is far more likely to die of founder-context problems (IP, time, money, complexity, burnout) than of engineering problems.** The engineering is the part that's going well. Guard the other stuff with the same rigor you guard the code — that's the whole message of this document.

---

## §4 The single most important action

If you do one thing from this document: **get the Accenture agreement in front of an employment/IP attorney before you build much more under the W-2.** R1 is the only risk that can reach *backward* and take what's already built. Everything else, you can fix going forward. That one, you can't.
