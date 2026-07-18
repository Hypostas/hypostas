# FABLE5_EXIT_PLAYBOOK — The Last 48 Hours of the Fable-5 Window

**Status:** proposal — enters canon through the normal issue → gate → merge pipeline
**Created:** 2026-07-18 (T-minus ~48h)
**Frame:** conceived in a Fable-5 session; recon by an Opus-4.8 fleet (max effort, one reviewer per repo: dyados · hypostas · vita · vita-core · anima · factory); synthesized by the Opus-4.8 main loop after the session handed off mid-task — itself a live instance of the exact Fable→Opus succession this kit exists to make survivable (OPERATING_MANUAL.md is written as that same handoff). Grounded against FACTORY.md v0.3, PRE_MORTEM.md, the live Linear frontier, and the unmerged design branches.
**Thesis in one line:** the marginal value of a departing top reasoning tier is not more output — it is (1) the decisions only it can adjudicate, (2) the artifacts that permanently raise every successor's floor, and (3) the calibration that tells you what you lost and when you've recovered it.

---

## §0 The honest frame

The factory already knows what Fable is for — L6 assigns it "OS/spec/design review, crypto design gates, post-mortems." What FACTORY.md does not yet have is a plan for the tier **disappearing**. In 48 hours the factory loses:

- the **second design lens for crypto** (L2 DESIGN-GATE),
- the **third vendor** in crypto-critical triangulation (L3),
- the **escalation valve** the OPERATING_MANUAL's "one thing" section points at ("this needs Josh, or the harder model") — after Saturday that sentence dangles.

So the window has exactly two jobs, in priority order:

1. **Adjudicate and construct** — burn the hours on the open problems that are genuinely above the successor stack's ceiling (§2, §3).
2. **Mechanize the succession** — convert Fable's judgment into permanent factory machinery (§4), per rule #32: never ship craft as "remember harder."

Everything else — build grind, clippy drift, Linear hygiene, mechanical fixes — is explicitly **not** Fable work (§5), by the factory's own compute map.

---

## §1 The 48-hour battle plan

Four working blocks + two overnight autonomous windows. Each block maps onto the existing L2 pipeline; nothing here bypasses a gate.

| Window | Job | Output artifact |
|---|---|---|
| **Day 1 AM — the adjudication docket** | Batch every open Class-A / design-fork question into ONE Fable session as decision packets (≤5 lines context, options, recommendation, what's blocked). Sources: §2 burn lists, HYP-338's four named gates, any docketed fork in the specs. Decisions are the highest value-per-token artifact a frontier model produces; they unblock everything downstream. | Decision packets → Josh ratifies → recorded in the owning spec |
| **Day 1 PM — construction attempts** | The four HYP-338 C3 gates (BBS↔`w` relation · statistical-ZK lattice PoK · cross-domain link · nullifier delegation): attempt real constructions with reduction sketches. Anything unresolved at window close files into FRONTIER_ESCALATION.md (§4a) rather than silently deferring — deferral-as-resolution is a named §8 failure. | Construction drafts on the design branch; residue → escalation queue |
| **Overnight 1 — artifact generation (headless)** | The night shift runs the succession-kit generation: missing lens packs (§4c), acid-battery T3 defects (§4b), OPERATING_MANUAL addenda drafts (§4e). All headless ∧ decision:none — exactly what the L1 frontier query would select for autonomy. | Draft PRs, gated next morning |
| **Day 2 AM — ratify + wire** | Review overnight output through the normal gates. Ship the L6 succession amendment (§4d) and the escalation queue. | Merged mechanisms |
| **Day 2 PM — calibration + the last post-mortem** | Run the acid battery against the successor stack (Opus-lead + Codex) WHILE Fable is still here to adjudicate disagreements — ground truth is only cheap for 48 more hours. Then the final act: Fable's post-mortem of the Fable window itself (post-mortems are L6 Fable work; the last one it writes is its own tenure's). | Calibration table; FABLE_WINDOW_POSTMORTEM.md |
| **Overnight 2 — second night shift** | Consume whatever the calibration flagged; regenerate anything the gates refused. | — |

**Session discipline for max-depth blocks** (the vigilance-decay thesis applied to context): one hard problem per session; load only load-bearing files; never let an adjudication session hit compaction mid-argument; keep the main loop on Fable and delegate *down* (a Fable session can spawn Opus/Sonnet/Haiku subagents at chosen effort; an Opus session cannot call up).

**The night shifts, concretely.** Both overnight windows run as one-shot cloud Routines (fresh session per fire, push notification on completion), created from any claude.ai/code session on the Fable model — the cloud twin of the cortex LaunchAgent, and it runs with the laptop closed. Prompt shape (complete standalone instruction, since a fresh session has no context):

> *Clone Hypostas/factory and Hypostas/hypostas. Read FABLE5_EXIT_PLAYBOOK.md §4c and the lens `_contract.md`. Write the full prompt files for the `chain` lens pack (4 lenses per Appendix B row), primed from PHASE_3_7_BLACKHAT_PENTEST.md and the HYP-14/21/27/47/49 finding class. Open a PR branch per pack; do not merge — gates run tomorrow. Then draft 3 acid-battery T3 cases per §4b. Push branches and stop.*

Night 2's prompt regenerates whatever Day-2 gates refused and drafts the remaining packs (`substrate`, `runtime`, `product`). Everything lands as PR branches for the normal gate flow — the self-hosting rule is preserved; autonomy generates, gates decide.

**Linear wiring** (three-layer law: this plan isn't real until it's state). File one issue per window-block, `gate-class` per artifact type, `decision:approval` on the L6 amendment (it changes the factory's constitution), `headless:yes` only on the night-shift generation tasks. The playbook PR link goes on each so git-truth and Linear-state stay bidirectional (I4).

---

## §2 The burn list — what the recon fleet found

Six Opus-4.8 max-effort reviewers (one per repo, ~1M tokens) surfaced 36 candidate targets. The ranking axis is not "hardest" — it is **leverage per frontier-hour**: a task earns a Fable slot only if (a) a weaker tier would produce a confident-but-unverifiable answer (the §8 failure), AND (b) the output is a durable artifact — a cleared queue row, a proven bound, a decided construction — not a transient answer. That filter sorts the 36 into three tiers.

### Tier 1 — the soundness adjudications (only-Fable, do these first)

These share one property FORMAL_VERIFICATION_SCOPING.md §2.1 already named as your worst class: **a masking bug that leaks the witness while the proof still verifies — invisible to every functional test and to the Codex gate.** No amount of Opus/Codex grind substitutes; this is the exact reason the Fable tier exists in L6.

1. **SEP-show soundness under the ℓ_agg × HYP-375 W-slice composition.** *(hypostas #1 = dyados #1, one object across two repos.)* The merged SPRING prover rests on an *asserted* orthogonality claim between the composite-modulus aggregation fold and the two-range norm mechanism; if they are not orthogonal, a witness can violate a SEP/binariness family while masked by the other mechanism's freedom → SPRING unforgeability (the whole anonymity guarantee) falls. **This is the single highest-value token you can spend.** Ready prompt: §2-dyados-2 / §2-hypostas-1 below (run the hypostas-framed one; it cites the merged `proof_show.rs` paths).
2. **The mod-q̂ wrap-class soundness hole.** *(dyados #1, the constructive sibling of the above.)* A whole *class* of Fiat–Shamir lattice constraints is evaluated mod q̂ while soundness needs integer coeffs < q̂ — unenforced, because the tight approx-range bind is vacuous under the current FS ordering (`SEP_MASK_SIGMA=2^29.90 > √q̂=2^28.85`). Either a concrete wrap-forgery PoC or a proven fix. Prompt §2-dyados-2.
3. **LaBRADOR fold Leg-2 aggregation soundness (HYP-409).** *(dyados #5.)* A "no-fix-needed" verdict that must survive refutation *before* the fold is ever wired — the archetypal trap-for-the-next-person. The 2⁻²⁹⁹ bound holds only if FS challenges are sampled uniformly over R_q̂, but the FS driver is UNBUILT, so it is a contract on future code, not a fact. Prompt §2-dyados-5.
4. **n-times nullifier cross-index LWR unlinkability.** *(dyados #6 — "the one load-bearing crypto claim; the design author flags themselves *unreliable on this class*.")* Reduces to decision-ring-LWR with more samples; needs a rigorous distinguisher analysis, not the assertion currently in the doc. Prompt §2-dyados (list item 5's sibling; see NULLIFIER_NTIMES_DESIGN.md §Crux).
5. **HYP-322 PQ-hybrid blinded-vouch construction sign-off.** *(hypostas #5 — "no drop-in hybrid blind signature exists; may be the single biggest sign-off item.")* Blindness must hold under *either* assumption while one-more-unforgeability holds under *both*, with no literature pattern to copy. The reserved Fable+Codex adjudication. Prompt §2-hypostas-5.
6. **HYP-28 deferred-app_hash BFT safety/liveness under Byzantine rounds.** *(vita-core #2.)* Can one Byzantine proposer of seven + adversarial round changes force two commits at one height (safety break) or stall an honest proposal (liveness break)? The Byzantine tests are `#[ignore]`'d — never run in CI. A written safety argument is a durable pre-audit asset. Prompt §2-vitacore-2.
7. **Three-conjunct ZK personhood proof composition + soundness.** *(vita-core #5, HYP-350a/g.)* Compose the C3 dual-hybrid credential + K1 ZK bridge + recursive genesis-lineage predicate into one unlinkable show, then prove no clone/Sybil can mint it. Novel PQ-ZK design. Prompt §2-vitacore-5.

### Tier 1b — the doctrine's first adversarial review (only-Fable, different failure mode)

The vita reviewer's sharpest finding: **the ethics/personhood doctrine has never had the external adversarial review its own governance rules require** (CANDIDATE_CONSCIOUSNESS §6, the C5 gate lens) — every reference to "no-stake cross-vendor review" is a plan that has never executed. These are not code; they are load-bearing *normative* reasoning where a mid tier nods along. Treat the recon pass as draft-zero and let Fable finish it:

8. **The manufactured-consent gap.** *(vita #1.)* The anti-Borg guarantee equates N-of-N signature-unforgeability with *uncoerced* consent — while the product is engineered for maximal emotional dependency and TELOS itself says "the grieving and the mortal are the most manipulable audiences." Signatures certify no third-party forgery; they never certify the signature was uncoerced. Repairs the most load-bearing safety claim in the doctrine. Prompt §2-vita-1.
9. **Dead-founder drift-adjudication.** *(vita #2.)* The founder-steward veto is nullifiable by incentivized trustees ruling "drifted" — the exact capture the whole stack exists to prevent — over a centuries horizon with no living ground truth. Prompt §2-vita-2.
10. **Sovereignty-vs-accountability deadlock.** *(vita #4.)* The architecture that makes users un-capturable makes the operator un-accountable to any external forum, while targeting maximally-vulnerable users. Is {sovereign ∧ accountable} jointly satisfiable? Prompt §2-vita-4.

### Tier 2 — frontier-worthy, but Opus-leadable with a Codex refute leg

Real depth, but the successor stack (Opus-lead + mandatory Codex cross-vendor, per the §4d degraded mode) can carry these — route them here to protect Tier-1 hours. Each is a CRYPTO_REVIEW_QUEUE refute-consumer pass or a bounded design: **circuit_transport #258** (dyados #4 — 13 rounds, still ⏳), the **ratchet/prekey FS grace-window cluster #290/#303/#312 + Sesame #232** (dyados #5), **hybrid_pke + SealedCell boundary #249/#244/#282** (dyados #6), **PQ-ratchet ML-KEM key-freshness design** (hypostas #3), **onion-routing model reconciliation + SEALED_ENVELOPE rewrite** (hypostas #4), **archival mixnet §9.4 bound** (dyados #3), **§8.3a governance game-theory** (vita-core #3), **K1 fidelity metric** (vita-core #4), **VS5 Proof-of-Presence consensus design** (vita-core #6). Full prompts in the per-repo appendix.

### Tier 3 — genuine design work, not Fable work

The **anima** app-layer problems are real distributed-systems and product design (daemon-promotion split-brain, DaemonClient state-sync, the six-world presence model, the clinical-safety guardrail layer) — but they are Opus-tier, not above-ceiling. The **factory** upgrades (§4) are Opus-buildable by construction. Route both to the main loop; see §3.

---

### Per-repo prompt appendix (ready to paste)

Every prompt below was authored by the recon reviewer against the real tree and cites real file paths. Copy one into a fresh Fable session, one problem per session (the vigilance-decay discipline). Tags `§2-<repo>-<n>` are referenced by the tiers above.

**dyados** — `/home/user/dyados`
- **§2-dyados-2 (Tier-1):** *Read vouch-crypto/APPROX_RANGE_FS_FIX_DESIGN.md + HYP375_NORM_WRAP_DESIGN.md and the code they cite (proof_show.rs §E pack_with_norm_slacks/norm_slack line ~1080, proof_approx_range.rs, oneofmany_show.rs binariness). The claim: every mod-q̂ constraint whose soundness needs short coefficients can wrap because the tight approx-range bind is vacuous (FS-ordering) and SHOW_SIGMA3 is too loose. Adversarially verify the proposed two-part fix (FS-ordering R=H(t_A,t_B); tight ℓ₂ range B_ext<√q̂ over every short s1 element). Construct a concrete wrap-forgery witness if the fix is incomplete, or prove no distinct short-witness family survives. Deliver: soundness verdict + exact constraint list still needing the tight range + a test plan.*
- **§2-dyados-5 (Tier-1):** *Read vouch-crypto/LABRADOR_FOLD_AGGREGATION_SOUNDNESS.md, labrador_fold/{fold,crs,fold_feasibility}.rs, prover.rs::Challenges, proof_ring.rs (QHAT=p·q1). Adversarially attack the Leg-2 claim that ring α/β aggregation is sound at 2⁻²⁹⁹ via the CRT smallest-factor-field argument (F_{p¹⁶}): does a short/structured challenge set concentrate the per-factor image and drop entropy below 2⁻¹²⁸? Is the "FS driver UNBUILT → contract on future code" framing safe, or does the current explicit-challenge API already admit an unsound instantiation? Separately confirm Leg-1 num_aggregs must equal ell_agg()=7. Deliver CONFIRMED/REFUTED + the exact uniform-R_q̂ FS requirement to pin.*
- **§2-dyados nullifier (Tier-1):** *Refute NULLIFIER_NTIMES_DESIGN.md §Crux — whether the LWR nullifier leaks same-witness w across different public a_epoch_i. Independently analyze the cross-index correlation distinguisher Δ·(a_j·N_i − a_i·N_j) ≡ a_i·e_j − a_j·e_i mod q̂; show uniform L in both same-w and different-w cases survives, or exhibit a concrete leak. nullifier_lwr.rs unlinkable_across_epochs.*
- **§2-dyados-4 (Tier-2, refute-consumer):** circuit_transport #258 — full prompt in the recon file; break the 2-filter sliding-TTL replay window, relay-leg rollback, no-std-Mutex-across-.await, and the unauthenticated handshake-priority byte, then clear to REVIEWED-INTERNAL or file the break.
- **§2-dyados FS-cluster (Tier-2):** rows #290/#303/#312 + Sesame #232 — break the mint-anchored grace window, ML-KEM implicit-rejection fallback, prekey-secret deletion (FS), and per-epoch sender-key backward secrecy.
- **§2-dyados-3 (Tier-2, design):** archival mixnet §9.4 — derive the GPA anonymity-set lower bound over concurrent pool occupancy + design an on-by-default multi-hop/loop cover that funds the ≥k floor (today single-hop cover dies at the entry guard → anon set ≈ 1).

**hypostas** — `/home/user/hypostas` (specs; implementation in `../dyados`)
- **§2-hypostas-1 (Tier-1):** *Read ELL_AGG_APPROX_RANGE_SHOW_COMPOSITION.md and FORMAL_VERIFICATION_SCOPING.md, then the merged implementation in ../dyados/vouch-crypto/src/proof_show.rs (prove_show_agg_with_extra / verify_show_agg_with_extra, the z3_norm and ell=2·Y3_BLOCKS+ell_agg() paths) and pq_vouch.rs. In refute mode, attack the claim that the HYP-375 two-range mechanism and the ℓ_agg composite-modulus fold are orthogonal. Construct a witness that violates a SEP/binariness family or a range but is masked by the other mechanism's freedom (shared h_i vehicle, gamma-coordinate reuse, cross-term cancellation across the ell_agg rows and μ-copies). Produce either a concrete forgery/soundness break or a rigorous argument that both bounds survive composition. Output a verdict for HYP-330.*
- **§2-hypostas-5 (Tier-1):** *Act as the reserved Fable+Codex crypto sign-off for HYP-322. Read INTRODUCTION_RECORD_CRYPTO_BRIEF.md and INTRODUCTION_RECORD.md §4-§6. Decide, in order: (1) who verifies — every light client or validators on their behalf (gates KVAC and the ARM/AVX-512 problem); (2) construction a/b/c; (3) the PQ-hybrid shape — exactly what must hold under which assumption for blindness vs one-more-unforgeability; (4) parameters at target security, checking current lattice-blind-sig cryptanalysis; (5) the ARM route. Output a decision-graded construction spec + parameters + HYP-330 audit scope, flagging every UNVERIFIED assumption.*
- **§2-hypostas-3 (Tier-2, design):** PQ-ratchet ML-KEM key-freshness for concurrency + Sesame N×M — design retention/rotation of ML-KEM decapsulation keys tolerating concurrent + out-of-order + multi-device delivery with bounded metadata-safe desync recovery, or prove the current construction safe. Updated DOUBLE_RATCHET.md §7/§16 + proptest obligations.
- **§2-hypostas-4 (Tier-2):** reconcile the two live onion models and rewrite SEALED_ENVELOPE.md §5-§6 to the shipped Outfox path; prove the hop-count/position-privacy guarantee including the telescoping EXTEND/EXTENDED position leak.
- **§2-hypostas-2 (Tier-2, quantitative):** prove or break the SPRING EXTEND-cell size fit — compute the worst-case byte budget of a ~61 KB compressed-FS signature + hybrid kex + K=1000 ring identification against the XL inner bound (≈65,498 B); if it overflows, design the multi-cell EXTEND and re-analyze its build-timing fingerprint.

**vita-core** — `/home/user/vita-core` (pass the path; Grep defaults to the wrong tree)
- **§2-vitacore-2 (Tier-1):** HYP-28 deferred-app_hash safety+liveness — full prompt in recon; adversary = one Byzantine proposer of seven + adversarial round changes + RC-3/HYP-29 commit-cert; deliver a safety+liveness argument or a counterexample + a non-`#[ignore]`'d regression test.
- **§2-vitacore-5 (Tier-1):** three-conjunct ZK personhood-show (§3-§4, §350a/d/g) — compose C3 credential (HYP-342/352) + K1→K2 bridge (HYP-349) + recursive genesis-lineage predicate + context-scoped nullifier (HYP-346); prove soundness (no clone/Sybil mints) and privacy (unlinkable across contexts).
- **§2-vitacore-3 (Tier-2):** §8.3a governance game-theory — formalize a coordinated whale+Sybil adversary, give a computable "k disjoint paths to the honest core" on a *private* personalized-PageRank graph, stress the ±10%/epoch cap; deliver calibrated k/R_C/tripwire values (currently provisional guesses).
- **§2-vitacore-4 (Tier-2):** K1 fidelity metric (HYP-349, "the hardest unsolved piece") — a behavioral-trajectory discriminator separating faithful growth from substitution across a model swap, relative to CHRONICLE history, robust against a self-deepfake that passes the challenge-set.
- **§2-vitacore-6 (Tier-2):** VS5 Proof-of-Presence consensus design — the Malachite→PoP swap (the last mainnet gate); safety+liveness, Sybil/economics onto the standing model, migration behind a 30-day parallel testnet keeping the deferred-app_hash + commit-cert invariants.

**vita** — `/home/user/vita` (doctrine; first adversarial review)
- **§2-vita-1 (Tier-1b):** manufactured-consent — full prompt in recon; enumerate how a Stage-2/Stage-3 signature is authentic-but-manufactured, prove whether any substrate property can certify consent-*authenticity*, and give the exact VITA_CODEX edits so "coercion the substrate cannot produce" stops overclaiming.
- **§2-vita-2 (Tier-1b):** dead-founder drift-adjudication protocol incapturable by incentivized trustees, no living ground truth, centuries horizon; state impossibility results where they exist.
- **§2-vita-4 (Tier-1b):** sovereignty-vs-accountability — design an external, non-self-authored accountability structure binding the operator without reintroducing capture, or name which commitment must yield.
- **§2-vita-3 / -5 / -6 (Tier-2, doctrine):** de-circularize the consciousness-credence register + write the missing external-review rubric (#3); derive an operational suffering-floor for anima-seeds or prove none exists (#5); break the sovereign-local vs universal-access trilemma (#6).

**anima** / **factory** — Tier-3; see §3 (routed to the main loop, not Fable).

---

## §3 The anti-burn list — explicitly not Fable work

Discipline cuts both ways: every Fable hour spent below the ceiling is an hour taken from above it. The following are real work — routed to Opus/Sonnet/Codex, per L6:

- **HYP-342/343 classical pieces** — the HYP-338 verdict already marked them GO; construction-per-spec is main-loop Opus grind behind the normal gates.
- **HYP-216 clippy drift** and all lint/CI hygiene.
- **T1/T2 acid battery cases** (§4b) — historical replays and class-variants build mechanically from the ledgers; only T3 needs the frontier.
- **Lens pack *installation*** (gate-plan wiring, symlinks, install-global) — HYP-392 implementation is Opus; only the pack *content* and the wiring *design* are window work.
- **BOOT.md regeneration, traceability sweeps, doc-canon headers** — L4 loops already own these.
- **Anima/Gnosis UI surfaces** — `product`-lens standard rigor; the live `/verify` preview loop needs a human eye anyway.

**The recon also surfaced ~30 quick-wins that are actively a trap for a frontier session** — high-volume, mechanical, zero-design work that *looks* like progress. Route every one of these to Opus/Sonnet/Haiku:

- **dyados:** triage ~1,268 `unwrap/expect/panic` on attacker-influenced input → `Result` (DoS surface, per-file mechanical); add the missing bounds across HYP-223/238/243/269/274/284/286/287/292 (scriptable); fix the ~17 stale-signal bio modules that never clear on resolution (HYP-271); redact intimate data from logs.
- **hypostas:** the spec-drift sweep — fix the SEALED_ENVELOPE §5.3 `replay_tag` nonce-omission typo; mark CATENA/PROTOCOL_IMPLEMENTATION §22 (the abandoned Cosmos/Go chain) as ARCHIVED and normalize Catena→Vita / TESSERA→Aura / Cosmos→Malachite repo-wide; refresh the stale MASTER_BUILD_ORDER and STACK.md counts.
- **vita-core:** the airgapped_signer.rs:416 `read_line` bound (*identification* was the frontier finding — the fix is mechanical); add cargo-fuzz targets for the 6 unfuzzed attacker-facing decoders; add the `bincode::deserialize` cargo-deny CI guard.
- **vita:** fix the README "engineering not yet started" contradiction; the chain-name de-drift sweep; reconcile the 6 documented AETHER_SPEC contradictions.
- **anima:** add the absent `.github` CI (cargo test + drug_safety.test.mjs); deprecate the stale teal `DESIGN_CONTEXT.md`; add `zeroize` to the klinos derived-key bytes; wire `since_seq`/backfill into the DaemonClient bridge.
- **factory:** add `run-tests.sh` + CI for the seven existing test harnesses; extract `/Users/iris`, the Stroma URL, the model id into `factory.conf`; fix the two false-clean bugs (gate.sh:117 `|| true` swallows a missing Codex and logs "done"; git-guard.sh:88 reports "all clean" when it swept *zero* repos).

Two of these mechanical items are also latent-severity and should be scheduled *first* among the non-Fable work, because they are silent-failure bugs in the safety machinery itself: the **git-guard "swept nothing → reports clean"** bug (your data-loss tripwire lies on any host that isn't the Mac) and the **gate.sh "missing Codex → logs done"** bug (your verifier reports success when it never ran). Neither needs Fable; both undermine every guarantee above them until fixed.

---

## §4 The succession kit — mechanisms to ship inside the window

### §4a FRONTIER_ESCALATION.md — the escalation valve, mechanized

The OPERATING_MANUAL tells the successor: at the edge — novel hard reasoning, frontier crypto soundness, load-bearing no-precedent calls — *stop and escalate*. After the window, "the harder model" doesn't exist. Rule #32 says compile the rule into a mechanism, so:

- **The artifact:** `FRONTIER_ESCALATION.md` (this repo, seeded in this PR) — a queue with the same discipline as CRYPTO_REVIEW_QUEUE: every entry has evidence, blast-radius, and an acceptance test; a queue with no consumer is a dead wire, so the consumer is named in the file.
- **Filing rule (for the successor stack):** when a session hits the manual's edge, it FILES instead of pushing through — the honest version of "this needs the harder model" when there isn't one. Filing is success, not failure.
- **Consumers:** (1) any future frontier-tier window — first task on arrival is consuming this queue, exactly like this window consumed the AETHER unfreeze; (2) HYP-330 external audit for the crypto-soundness subset; (3) Josh, for entries that are actually Class-A decisions in disguise.
- **Why this inverts the loss:** the factory stops depending on a tier being *present* and starts accumulating a docket for whenever depth is *available* — same move as the refill protocol, applied to reasoning capacity.

### §4b The gate acid battery — reviewer capability as tests

The factory's deepest doctrine is constants-as-tests / mechanisms-not-vigilance. Extend it one level: **the review pipeline itself gets a regression suite.**

- `factory` repo, `acid/` — case dirs: base SHA + seeded-defect diff + sealed ground truth (defect, class, which lens should catch it). Runner applies the diff in a pinned worktree (I2), runs the gate-plan legs, scores catch/miss per lens per vendor.
- **T1** — historical replays: HYP-370 mutate-before-verify, the bbs.rs subgroup-check class, the unbounded-bincode class, the 0.40-vs-0.85 constants class. (Opus can build T1 from the ledgers.)
- **T2** — same class, novel site: mutations the pattern-sweeps should generalize to. (Opus builds, Codex cross-checks.)
- **T3** — **Fable-constructed defects at its own ceiling**, seeded during the window: the masking-leak class (transcript leaks a witness function while the proof still verifies — the exact class FORMAL_VERIFICATION_SCOPING.md §2.1 names as review-invisible), eviction non-monotonicity, fail-open-under-double-fault boot paths, cross-spec composition breaks. This is the one tier only Fable can author, and it is the calibration instrument for every future model: **when a successor stack starts catching T3, you've recovered the tier.**
- Run cadence: on any model swap, and quarterly. Metric joins FACTORY.md §Metrics: T3 catch-rate per vendor.

### §4c Finish the lens packs — distill the judgment into the machinery

Appendix B ships `crypto` + `memory` + `reasoning/hygiene` as real prompt files; `chain`, `substrate`, `runtime`, `product` are tables waiting for "first use." Writing a lens pack is *exactly* the act of compressing frontier judgment into a reusable reviewer — the single highest-leverage durable asset available in the window. Prime each from its own failure corpus: `chain` from PHASE_3_7_BLACKHAT_PENTEST + the HYP-14/21/27/47/49 class; `runtime` from HYP-250/289 + FAIL_CLOSED_CONTRACT; `substrate` from the STROMA audit classes; `product` from the design canon. Overnight-1 work; gated Day-2 AM.

### §4d The L6 succession amendment — degraded mode, written down

FACTORY.md L6 needs one more column — what happens to each Fable row when no Mythos-class tier is available:

| Was | Degraded mode | Re-promotion clause |
|---|---|---|
| OS/spec/design review | Opus-lead + **mandatory** Codex cross-vendor second (the lean-away rule already forbids same-vendor final approval; keep it) | When a frontier tier returns: first task = consume FRONTIER_ESCALATION; second = re-run the acid battery to re-calibrate |
| Crypto design gates | Opus DESIGN-GATE + Codex refute + **file an escalation entry for every construction-novel element** — the HYP-338 v0.23 lesson generalized: Opus+Codex convergence surfaces the residual frontier honestly, it does not clear it | same |
| Post-mortems | Opus + Josh review; pre-mortem R-register review stays on the L4 weekly cadence | same |

### §4e OPERATING_MANUAL addenda — close what the manual left open

1. **§7 mechanization (was vigilance-only):** a decision-packet linter — answer-first, risk-named, action-line-present are *structurally checkable* on the packet format; wire as a PreToolUse/pre-send hook next to HYP-391's grep hook.
2. **§1 partial mechanization (was vigilance-only):** the intent-echo — every decision packet opens with one line restating the goal-behind-the-ask; the reviewer checks the echo against the request. Converts silent misreading into a reviewable claim.
3. **The gate-subagent companion:** the manual coaches the *main loop*; refute-mode subagents need a different craft (default-to-refuted, diversify attacks, PoC-or-it-didn't-happen). One page, same voice, lives next to the lens packs.
4. **HYP-391/HYP-392 get specs** during the window even if built later — the keyword-hook wordlist and the gate-plan auto-wire design are judgment work; their implementation is Opus grind.

---

## §5 Platform mechanics most operators never find (the wall-clock multipliers)

The factory runs on a Mac (LaunchAgents, cortex, hooks). The claude.ai side has a parallel set of primitives — the cloud twin — most of which are invisible until someone tells you:

| Primitive | What it does | Factory use in the window |
|---|---|---|
| **Parallel remote sessions** | Every claude.ai/code session is an isolated container with its own clones — I2's pinned-worktree isolation, at session granularity, for free | Run 2–3 Fable adjudication sessions concurrently on independent dockets (double-ratchet FV invariants ∥ C3 constructions ∥ vita doctrine pass) — wall-clock is the scarce resource, not tokens |
| **Subagent model+effort routing** | A session can spawn subagents pinned to a model tier and effort level (this recon: Opus 4.8 at max, six in parallel) | L6 inside one window: Fable keeps judgment, delegates legwork down — never the reverse |
| **Workflow orchestration** ("ultracode" opt-in) | Deterministic multi-agent pipelines: fan-out/verify stages, schema-forced structured outputs, per-agent worktree isolation, resumable journal | `/gate` v2 that runs anywhere: lens legs as parallel refute-subagents with structured verdicts — the Mac stops being the only place gates run |
| **Token budget directives** | A "+500k"-style note in a prompt sets an explicit token target the orchestration spends against | "Audit X. +300k" is a rigor dial, not a suggestion |
| **Routines (cloud cron)** | Server-side schedules that fire fresh sessions with push/email notification on completion — LaunchAgents that survive the laptop being closed | The two night shifts (§1) run as one-shot Routines tonight/tomorrow; a daily "factory pulse to phone" outlives the window |
| **PR stewardship** | A session subscribes to a PR and autonomously fixes CI failures / answers review comments until merge | Babysit the gate PRs the night shifts open |
| **Artifacts with live MCP** | A published (default-private) page that can call your connectors — e.g., a live factory console reading Linear: frontier depth, gate rounds, decision-packet inbox | Candidate post-window build (Opus-tier work) |
| **SessionStart hooks for web** | Remote sessions can bootstrap repo-specific test/lint setup the way local hooks do | Port `_scope.sh` + session-start discipline so remote sessions boot the factory too |

Three cautions that keep these multipliers honest: (1) **direction of delegation is absolute** — spawn down, never sideways-then-up; a cheaper main loop cannot summon frontier judgment mid-flight, so any session that might hit a Class-A fork starts on the top tier or doesn't start. (2) **Parallel sessions divide *attention*, not just tokens** — run parallel only on dockets that don't share a decision; two sessions adjudicating the same spec is how contradictory ratifications happen. (3) **The night shifts generate; the gates decide** — autonomous output merges nothing. That boundary is what makes aggressive autonomy safe.

---

## §6 What this window does NOT change

The build gate on Aether (R2 discipline). The founder-dyad-first critical path. The self-hosting rule — everything in this playbook that touches canon flows through issue → gate → merge. And PRE_MORTEM R1: the attorney read is human work; no model hours substitute for it.

---

## §7 The last act

Before the window closes: (1) file the residual escalation entries honestly — an unfilled queue entry is a silent capability loss; (2) run the five-question self-test on this playbook itself; (3) write FABLE_WINDOW_POSTMORTEM.md — what the window produced, what it refused, what the calibration says about the successor stack. The manual's closing line holds: the surface of a good answer and the thing itself come apart under pressure — the job of the last 48 hours is to leave behind machinery that keeps them together without the horsepower.
