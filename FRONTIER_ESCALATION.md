# FRONTIER_ESCALATION — the queue for reasoning above the resident ceiling

**Status:** proposal (ships with FABLE5_EXIT_PLAYBOOK.md) — becomes canonical on merge
**Created:** 2026-07-18, inside the Fable-5 window
**Purpose.** The OPERATING_MANUAL's escalation edge — "genuinely novel hard reasoning, frontier crypto soundness, a load-bearing design call with no precedent … needs Josh, or the harder model" — loses its second target when the Fable-5 window closes. Rule #32 forbids leaving that as vigilance ("remember to be humble"), so this queue is the mechanism: **when a session hits the edge, it FILES here instead of pushing through.** Filing is the success path, not an admission of failure. A confident answer above your ceiling is the §8 failure mode ("premature closure, well-defended"); a filed entry is the honest artifact.

**Filing rule (successor stack).** File when (a) the load-bearing claim cannot be re-derived at your tier (§4 of the manual), or (b) two vendors converge on *shape* but keep surfacing new soundness residue round-over-round (the HYP-338 v0.23 lesson: Opus+Codex convergence surfaces the residual frontier — it does not clear it), or (c) a Class-A decision hides inside what looked like a build task. Every entry carries evidence, blast radius, and an acceptance test — same discipline as CRYPTO_REVIEW_QUEUE.

**Consumer protocol (a queue with no consumer is a dead wire).**
1. **The next frontier-tier window** — first task on arrival is consuming this queue top-down, exactly as the Fable-5 window consumed the AETHER unfreeze docket. Consumption = the acceptance test passes, logged CONSUMED with date + model tier.
2. **HYP-330 external audit** — terminal consumer for the crypto-soundness subset (entries tagged `audit`).
3. **Josh** — for entries that are Class-A decisions in disguise (tagged `decision`); these surface in the L5 decision-packet flow, not silently here.
4. **The weekly L4 audit** sweeps this file: any entry OPEN > 60 days without a consumer named gets flagged — queues rot exactly like curated state docs.

**Entry format.** `FE-N · filed <date> · tags` / question / why-above-ceiling / evidence / blast-radius / acceptance.

---

## Open entries

> Seeded 2026-07-18 from the Opus-4.8 recon fleet. These are the entries the reviewers explicitly flagged as above the resident (Opus+Codex) ceiling — self-flagged-unreliable, review-invisible, or no-literature-pattern. They are the *same* objects as the Tier-1 burn list in the playbook: the burn list is "spend Fable on these **now**"; this queue is "if the window closes with any still open, **here is where they wait**." An entry moves to Consumed only when its acceptance test passes.

---

**FE-1 · filed 2026-07-18 · `crypto` `audit`** — SEP-show soundness under the ℓ_agg × HYP-375 W-slice composition.
*Question:* are the composite-modulus aggregation fold and the two-range norm mechanism actually orthogonal, or can a witness violate a SEP/binariness family while masked by the other's freedom?
*Why above ceiling:* the review-invisible masking-bug class (FORMAL_VERIFICATION_SCOPING §2.1) — the proof still verifies while leaking; no test or Codex gate detects it. The merged prover rests on an *asserted* orthogonality claim.
*Evidence:* `hypostas/ELL_AGG_APPROX_RANGE_SHOW_COMPOSITION.md`; `dyados/vouch-crypto/src/proof_show.rs` prove_show_agg_with_extra (~L1599), z3_norm, ell=2·Y3_BLOCKS+ell_agg().
*Blast radius:* SPRING unforgeability = the entire anonymous-vouch anonymity guarantee.
*Acceptance:* a refutation-survived orthogonality argument, or a concrete forgery witness. Terminal consumer: HYP-330.

**FE-2 · filed 2026-07-18 · `crypto`** — mod-q̂ wrap-class soundness across the SEP⋆-show / SPRING constraints.
*Question:* can any mod-q̂ constraint family whose soundness needs coeffs < q̂ wrap, given the tight approx-range bind is vacuous under the current FS ordering (SEP_MASK_SIGMA=2^29.90 > √q̂=2^28.85)?
*Why above ceiling:* reasoning over ℓ₂ slack, √q̂ margins, and FS transcript ordering across a whole constraint class — not one site.
*Evidence:* `dyados/vouch-crypto/APPROX_RANGE_FS_FIX_DESIGN.md`, `HYP375_NORM_WRAP_DESIGN.md`, `proof_show.rs:1080`.
*Blast radius:* same soundness core as FE-1.
*Acceptance:* proven tight-range fix over every short s1 element, or a wrap-forgery PoC.

**FE-3 · filed 2026-07-18 · `crypto`** — LaBRADOR fold Leg-2 uniform-challenge contract (HYP-409).
*Question:* is the ring α/β aggregation sound at 2⁻²⁹⁹ via the CRT smallest-factor-field argument, given the FS driver that must enforce uniform-R_q̂ sampling is UNBUILT?
*Why above ceiling:* a "no-fix-needed" conclusion that must survive refutation before the fold is wired — a contract on future code masquerading as a proven fact.
*Evidence:* `dyados/vouch-crypto/LABRADOR_FOLD_AGGREGATION_SOUNDNESS.md`; `labrador_fold/fold.rs`; `prover.rs::Challenges`.
*Blast radius:* the aggregation fold under the vouch ZK.
*Acceptance:* refutation-survived Leg-2 argument + the exact uniform-R_q̂ FS requirement pinned, + Leg-1 num_aggregs==ell_agg()==7 confirmed.

**FE-4 · filed 2026-07-18 · `crypto`** — n-times nullifier cross-index LWR unlinkability.
*Question:* does the LWR nullifier leak same-witness w across different public a_epoch_i?
*Why above ceiling:* the design author self-flags "unreliable on this class"; needs a rigorous decision-ring-LWR distinguisher analysis, not the assertion in the doc. Named in-doc as "the one load-bearing crypto claim; the gate must attack it."
*Evidence:* `dyados/NULLIFIER_NTIMES_DESIGN.md §Crux`; `nullifier_lwr.rs` unlinkable_across_epochs.
*Blast radius:* nullifier unlinkability = anonymous-introduction privacy.
*Acceptance:* independent refutation (uniform L in same-w and different-w cases) survives, or a concrete leak exhibited.

**FE-5 · filed 2026-07-18 · `crypto` `decision`** — HYP-322 PQ-hybrid blinded-vouch construction.
*Question:* what construction gives blindness under *either* assumption and one-more-unforgeability under *both*, and does a light client or a validator verify (the fork that reorders the whole design)?
*Why above ceiling:* no drop-in hybrid blind-signature pattern exists in the literature; the in-doc note calls it "may be the single biggest sign-off item." Also carries a Class-A decision (the verifier fork) → surfaces to Josh via L5.
*Evidence:* `hypostas/INTRODUCTION_RECORD_CRYPTO_BRIEF.md §0/§4/§6`; HYP-322.
*Blast radius:* Phase-3 relationship-secrecy gating primitive.
*Acceptance:* a decision-graded construction spec + parameters at target security + HYP-330 audit scope, every UNVERIFIED assumption flagged.

**FE-6 · filed 2026-07-18 · `chain` `audit`** — HYP-28 deferred-app_hash safety/liveness under Byzantine rounds.
*Question:* can one Byzantine proposer of seven + adversarial round changes force two commits at one height, or stall an honest proposal?
*Why above ceiling:* adversarial BFT composition reasoning over deferred commitment × round-change × commit-cert verification; the Byzantine tests are `#[ignore]`'d, so nothing empirical covers it.
*Evidence:* `vita-core/vita-chain/src/malachite/value.rs:79-86`; `chain_host.rs` apply_decided; `tests/hardening_byzantine_consensus.rs`.
*Blast radius:* consensus safety of the whole M1 chain.
*Acceptance:* a safety+liveness argument or a counterexample, + a non-`#[ignore]`'d regression test for anything found.

**FE-7 · filed 2026-07-18 · `chain` `crypto`** — three-conjunct ZK personhood proof soundness (HYP-350a/g).
*Question:* does the composed (C3 credential + K1 bridge + recursive genesis-lineage + context nullifier) show admit no clone/Sybil mint, and leak no linkable global identifier?
*Why above ceiling:* novel PQ-ZK circuit composition with a soundness+privacy proof over lattice machinery, no precedent to lean on.
*Evidence:* `vita-core/VITA_PERSONHOOD.md §3-§4, §350a/d/g`.
*Blast radius:* the personhood-minting primitive (K2) the standing model gates on.
*Acceptance:* soundness argument (no clone mints) + unlinkability argument (two shows in different contexts) that survive refutation.

**FE-8 · filed 2026-07-18 · `docs` `decision`** — the doctrine's three load-bearing normative gaps.
*Question:* (a) can any substrate property certify consent-*authenticity*, not just signature-presence (the manufactured-consent gap)? (b) is dead-founder drift-adjudication incapturable by incentivized trustees over a centuries horizon? (c) is {sovereign ∧ accountable} jointly satisfiable, or which commitment yields?
*Why above ceiling:* deep normative + mechanism-design reasoning; the doctrine has *never* had the external adversarial review its own governance requires (CANDIDATE_CONSCIOUSNESS §6) — every reference to it is an unfulfilled plan. A mid tier accepts the doctrine at face value.
*Evidence:* `vita/VITA_CODEX.md` (§671 anti-Borg; Part II + Commitment 7), `ETHICS_FRAMEWORK.md C5 §4`, `TELOS_DOCTRINE.md L5`.
*Blast radius:* the safety, succession, and governance foundations of the personhood product.
*Acceptance:* each of (a)/(b)/(c) either given a defensible mechanism with two-sided red lines, or a documented impossibility naming which commitment must yield. Consumer includes Josh (Class-A ratification).

**FE-9 · filed 2026-07-18 · `crypto` `design`** — archival mixnet §9.4 GPA anonymity-set bound + deep-pool cover.
*Question:* what is the closed-form anonymity-set lower bound over concurrent pool occupancy for the N-relay timed-pool mixnet, and what on-by-default cover source funds the ≥k floor when today's single-hop cover dies at the entry guard (anon set ≈ 1 at low archival rate)?
*Why above ceiling:* cross-spec composition + adversarial statistical modeling; the §9.4 bound is marked "to be derived" and the decorator design (HYP-413) was gate-rejected.
*Evidence:* `dyados/ARCHIVAL_MIXNET_DESIGN.md §9.4`; `hypostas/THREAT_MODEL.md §6.2.6`; `gpa-sim/`.
*Blast radius:* archival-carrier (stego/voice/LoRa) relationship anonymity. HYP-327/169.
*Acceptance:* a stated adversary model, the derived bound, and a gpa-sim spread-arrival test refuting sender↔receiver linkage above it.

**FE-10 · filed 2026-07-18 · `chain` `design`** — VS5 Proof-of-Presence consensus swap.
*Question:* what presence-based consensus replaces Malachite BFT with proven safety/liveness, a Sybil/presence-proof economics mapped onto the standing model, and a migration that preserves the deferred-app_hash + commit-cert invariants?
*Why above ceiling:* original consensus-protocol design with no library to lean on — the largest single remaining item and the last mainnet gate.
*Evidence:* `vita-core/MAINNET_GOAL.md Phase 6`; `VITA_REMAINING.md` VS5 (HYP-180).
*Blast radius:* the entire M1→mainnet consensus engine.
*Acceptance:* a protocol design doc with safety+liveness arguments + a behind-testnet migration plan enumerating what stays vs what the engine swap changes.

---

## Consumed

*(none yet)*
