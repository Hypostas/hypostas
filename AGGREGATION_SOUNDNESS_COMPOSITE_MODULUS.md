# Aggregation Soundness over the Composite Proof Modulus (stack-wide)

**Status:** DESIGN — design-first per Josh (2026-07-03), Codex DESIGN-review pending, then implement.
**Scope:** the entire lattice proof stack (`vouch-crypto`), NOT SPRING alone. Touches the **audited** SEP
credential show. HYP-317 (SPRING) surfaced it; HYP-352 (SEP) shares the mechanism.
**Trigger:** Codex gate P1 on `spring_show.rs` (2026-07-03): "raising ℓ does not amplify membership
soundness — `membership_form` is a single unweighted `a:` summand." Investigation showed the weakness is
not membership-specific; it is a property of how *every* `FullRingRelation` aggregate is built.

---

## 1. The mechanism under review

The masked-quadratic show (`proof_agg_show::{prove_agg, verify_agg}`) proves **one** full-ring equation
`F(ŝ) = 0` over the committed witness, where `F` is a `FullRingRelation`. Its soundness has two independent
layers:

1. **Masked-quadratic layer** — the challenge `c ∈ C'` (`proof_challenge`) makes `c²·F(ŝ)` the verifier's
   residual; `c` is a **unit** in `R_q̂` (the challenge space is built so distinct-challenge differences,
   and `c` itself, are invertible — `qmin > (2ρ√κ)^κ`, thesis §7.4.1). So `c²·F(ŝ) = 0 ⟺ F(ŝ) = 0`
   **regardless of the composite modulus**. This layer is sound to `~1/|C'| ≈ 2⁻¹³⁰`. ✅ Not the problem.

2. **Aggregation layer** — `F` is itself a scalar-weighted sum of the `d` relation rows:
   ```
   F(ŝ) = aggregate_rows(rows(ŝ), μ) = Σ_{i,k} μ_{ik} · row_{ik}(ŝ) ,   μ = mu_vector(t_A, …) ∈ Z_q̂
   ```
   (`proof_show::{mu_vector, aggregate_rows}`). The `μ` are **independent Fiat–Shamir SCALARS mod q̂**,
   seeded from `t_A` (the witness commitment — so `ŝ` is bound before `μ`). Soundness of this layer is the
   implication **`F(ŝ)=0  ⟹  every row_{ik}(ŝ)=0`**, and THIS is where the composite modulus bites.

Users of the aggregation layer (all identical in shape):
- `proof_show::SepRelation` — the SEP signature equation (`a:` of the credential show). **Audited, shipped.**
- `proof_show::OpeningRelation` — the Model-B opening (`a:` of the blind-issuance π `prove_issuance_wf`).
- `spring_path::membership_form` — the SPRING accumulator relation (`a:` of `prove_spring_show`).
- The scalar `extra` families are aggregated the same way (`aggregate`, `mu_vector`), but they are **already
  ℓ-repeated** via the `h_i` rows (independent `γ_{i,·}` per row); the `a:` relation is **not**.

`q̂ = PHAT_P · PHAT_Q1` is composite because the SEP credential ring is `R_p`; the show needs the larger
`q̂`. Let **`p_min := min(PHAT_P, PHAT_Q1)`** — the smallest prime factor; it alone drives the aggregation
weakness below (`~1/p_min`) and the fix constant (`ℓ_agg`). **The specific values are PROVISIONAL
(HYP-330):** the illustrative `PHAT_P = 425801 (≈2¹⁸·⁷)`, `PHAT_Q1 = 549755813869 (≈2³⁹·⁰)` are marked in
this repo's HYP-330 notes as ILLUSTRATIVE and **failing the Lemma 7.7 ZK bound** — the show modulus must be
recalibrated regardless. So every numeric below is *conditional on the illustrative set* and recomputed once
HYP-330 fixes `q̂`; the mechanism (weakness `~1/p_min`, fix `ℓ_agg = ⌈λ / log₂ p_min⌉`) is what is
canonical, not the numbers. For the illustrative set `p_min ≈ 2¹⁸·⁷`.

---

## 2. The grinding attack on the aggregation layer

Fix any single row `r := row_{i*k*}`. A cheating prover wants `F(ŝ)=0` while `r(ŝ) ≠ 0` (a non-witness that
verifies). Work in the CRT decomposition `R_q̂ ≅ R_p × R_{q₁}`.

**Construction.** The prover commits a witness `ŝ*` in which the violated row is a **`q₁`-multiple**:
`r(ŝ*) = q₁·a` for a unit `a ∈ R_p` (so `r ≡ 0 (mod q₁)`, `r ≢ 0 (mod q̂)`). Because the prover chooses `ŝ*`
freely, and the rows are affine/quadratic images of `ŝ*`, a target row value is reachable (e.g. for the
SPRING key row `A_s·s − recompose(t_digits)`, set `t_digits` to recompose to `A_s·s − q₁·a`).

**Aggregate collapse.** `F(ŝ*) = Σ μ_{ik} row_{ik}`. Mod `q₁`: every deliberately-violated row is `≡ 0`, and
the honest rows are `0`, so `F ≡ 0 (mod q₁)` automatically. Mod `p`: `F ≡ Σ μ · (row/… )` — one scalar
equation in the FS scalars `μ`. Over the random `μ = mu_vector(t_A)`, `F ≡ 0 (mod p_min)` holds with
probability **`~1/p_min`** (`≈ 2⁻¹⁸·⁷` for the illustrative set). The prover **grinds `t_A`** (re-randomises
the commitment) until the FS-derived `μ` zeroes the mod-`p_min` aggregate. Expected work: **`~p_min` hashes**
(`≈ 2¹⁸·⁷` illustrative). Then `F(ŝ*) = 0` **honestly**, the masked quadratic (layer 1) proves it truthfully,
and the verifier accepts a witness with `r(ŝ*) ≠ 0`. (If `p_min` is the *smaller* factor the grind targets
the *other* factor's coset — symmetric; the cost is always `~p_min`.)

**Shortness does not stop it.** A `q₁`-sized coefficient (`~2³⁹`) contributes `2⁷⁸` to `‖·‖²`, under the
approx-range bound `B² ≈ 2⁸¹·⁸` (`B = c₂₅₆·σ₃·√256 ≈ 2⁴⁰·⁹`). Verified numerically. So the grinding witness
passes the witness-shortness leg.

**b4 / binariness do not stop it.** Those constrain `τ₀` of specific blocks; they are orthogonal to a
`q₁`-multiple planted in a *hash/opening* row.

Conclusion: the aggregation layer, as built, has a **`~2¹⁸·⁷`-work path to a zero aggregate with a nonzero
row** — for SEP and SPRING alike.

---

## 3. Is it exploitable to a real forgery? (the subtle part)

A zero aggregate with a nonzero row is necessary but not obviously sufficient for a *useful* forgery
(accepted proof by a true non-member). The planted violation is a `q₁`-multiple, i.e. the witness is **valid
mod q₁**. Two sub-cases for what "valid mod q₁ but not mod q̂" buys the attacker:

- **(A) Violate rows only as `q₁`-multiples.** The witness satisfies *every* membership relation mod `q₁`.
  For a genuine non-member (no known member secret, pubkey not in the ring), producing a witness valid mod
  `q₁` requires either a hash collision mod `q₁` or a pubkey preimage mod `q₁` — i.e. **breaking M-SIS/M-LWE
  mod q₁**. If M-SIS mod `q₁` is ≥128-bit hard (a C5 calibration target), this path is hard *despite* the
  cheap aggregate collapse: the `2¹⁸·⁷` grinding buys the mod-`p` collapse, but the mod-`q₁` half still
  demands a real lattice break. Net cost ≈ M-SIS(q₁), not `2¹⁸·⁷`.

- **(B) Violate rows as `p`-multiples instead** (`≡ 0 mod p`, `≠ 0 mod q₁`): symmetric — mod-`p` aggregate
  auto-zero, grind mod `q₁` at `~1/q₁ ≈ 2⁻³⁹`, witness valid mod `p`. For SPRING this needs M-SIS mod `p`
  (`p ≈ 2¹⁸·⁷` — **weak**), but a mod-`p`-only-valid witness is not a full accumulator witness; whether it
  forges depends on the same reduction.

**Determination.** The net forgery cost is bounded *below* by `min(` grind-p `2¹⁸·⁷`, grind-q₁ `2³⁹`, M-SIS
per component `)` **intertwined** with which component the reduction actually needs. I can construct the
`2¹⁸·⁷` aggregate-collapse concretely; I **cannot** currently prove the residual M-SIS-mod-`q₁` argument
closes the gap to ≥128 bits, and it rests on `min(p,q₁)`-component M-SIS calibration that is not yet done
(`p ≈ 2¹⁸·⁷` M-SIS is almost certainly **not** 128-bit hard by itself). Per rule #1 (never self-certify
soundness) and the memory *"missing soundness mechanisms are not deferrable"*, I will **not** ship on the
strength of the "(A) is saved by M-SIS(q₁)" argument. The clean fix removes the dependence entirely.

---

## 4. Why [LNP22] does not have this

The thesis aggregates exact relations over a **prime** `q` (fully/partially splitting), where there is no
sub-modulus to hide a violation in; a nonzero row is nonzero in every CRT field, and the aggregation error
is `~1/q^{d}` per splitting field plus the challenge boosting. Our `q̂ = p·q₁` is a **deviation** forced by
the SEP credential's `R_p` structure, and the FS-scalar `aggregate_rows` inherits the *smallest*-prime
error `1/p`. The deviation — not [LNP22] — is the source. So this is a **faithfulness gap in our port**,
localized to the aggregation layer.

---

## 5. Fix: ℓ-fold the aggregation (recommended)

Replace the single FS-scalar aggregate with **`ℓ_agg` independent aggregates**, all proven zero:
```
F_j(ŝ) = Σ_{i,k} μ^{(j)}_{ik} · row_{ik}(ŝ) = 0    for j = 1..ℓ_agg ,   μ^{(j)} independent FS scalars
```
A cheater's planted row survives all `ℓ_agg` collapses only with probability `(1/p_min)^{ℓ_agg}`. So the fix
constant is a **formula keyed to the calibrated modulus**, not a hard number:
```
ℓ_agg = ⌈ λ / log₂ p_min ⌉ ,   λ = 128
```
For the illustrative `p_min ≈ 2¹⁸·⁷` this is `ℓ_agg = 7` (`(1/p_min)⁷ ≈ 2⁻¹³¹ < 2⁻¹²⁸`) — but **`ℓ_agg` is
recomputed from whatever `p_min` HYP-330's modulus calibration selects** (a larger smallest factor ⇒ smaller
`ℓ_agg`; e.g. a `p_min ≈ 2⁶⁴` factor ⇒ `ℓ_agg = 2`). Encode it as `⌈λ / log₂ p_min⌉` in code with a param-gate
assertion `(1/p_min)^{ℓ_agg} < 2⁻λ`, so an uncalibrated or mis-set modulus is rejected, not silently shipped.
Soundness then becomes clean and unconditional — no reliance on the §3 M-SIS-mod-`q₁` interaction, no
per-component calibration subtlety.

**Mechanism (implementation).** `prove_agg` proves one `F=0`; extend it to a **vector** of `ℓ_agg`
relations sharing the *same* linear opening `(w, z1, z2)` and challenge `c` — but with **independently-masked**
garbage pairs `(t0_j, t1_j)`.

> ⚠️ **The mask MUST be independent per `j`** (Codex DESIGN-review P1, 2026-07-03). Naïvely sharing the
> single garbage mask — `t0_j = ⟨b,y2⟩ + e0_j`, `t1_j = ⟨b,s2⟩ + e1_j` — is a **ZK break**: the shared
> `⟨b,·⟩` cancels in `t1_j − t1_k = e1_j − e1_k`, exposing a witness-linear relation difference (`e1` carries
> `F.cross(y,ŝ)`), i.e. exactly the §C-iv multi-garbage leak the single-garbage design was built to avoid.
> Do not implement the shared-mask form.

- **Prover:** the CRS carries `ℓ_agg` INDEPENDENT BDLOP garbage generators `b^{(1)}..b^{(ℓ_agg)}` (CRS is not
  proof size). For each `j`: `e0_j = F_j.quad_part(y)`, `e1_j = F_j.cross(y,ŝ) + F_j.lin_part(y)`, then
  `t0_j = ⟨b^{(j)}, y2⟩ + e0_j`, `t1_j = ⟨b^{(j)}, s2⟩ + e1_j`. Now the mask is per-`j`:
  `t1_j − t1_k = ⟨b^{(j)}−b^{(k)}, s2⟩ + (e1_j − e1_k)` — the leading term is a fresh independent commitment
  to `0` under the SECRET `s2` with an independent generator, so the difference is uniform and reveals
  nothing (each `(t0_j,t1_j)` is individually a BDLOP commitment of `e·_j`, simulatable without the witness).
  The challenge `c = FS(t_A, t_B, w, {t0_j,t1_j}_j, context)` binds ALL garbage pairs (no adaptive `μ^{(j)}`).
- **Verifier:** the masked-garbage reconstruction per `j` against `b^{(j)}`; accept iff all `ℓ_agg` checks pass.
- **ZK obligation (build-time):** a simulator producing `{(t0_j,t1_j)}` from `(z1,z2,c)` + the public `F_j`
  without the witness, and a test that pairwise differences do NOT cancel the mask. This is the acceptance
  gate for the construction (rule #27 — the adversarial half).
- **Cost:** `+2(ℓ_agg−1)` ring elements over the current single garbage pair (`w, z1, z2` shared, `b^{(j)}` are
  CRS) — `+12` `R_q̂` elements for the illustrative `ℓ_agg=7`. The bulk `w/z1/z2` is unchanged, so the proof
  stays log-size in the ring depth `δ`.

**Simpler equivalent (preferred if it type-checks against `proof_garbage`):** the show ALREADY commits `ℓ`
zero-const-coeff garbage polys `g_i` in `m̂` and reveals leak-free `h_i` — the *existing* leak-free boosting
mechanism. If the `ℓ_agg` quadratic aggregates can be carried as additional garbage slots in `m̂` (each with
its own `g`), the independent-mask property is inherited from the audited `h_i` construction rather than
re-derived. Prefer this over new `b^{(j)}` generators if the quadratic `e0/e1` terms fit the `m̂`/`h_i`
shape; fall back to independent `b^{(j)}` if they do not. The build's first step is to determine which.

**A cheaper structural alternative (note, not chosen):** give SPRING its own **prime** proof ring
(SPRING keys are independent of the SEP credential, §3.0). Then one-shot aggregation is `~1/q_prime`, and a
single `ℓ_agg=2..3` suffices. Rejected for now: it forks `proof_ring`/`proof_agg_show`/`proof_challenge`
onto a second modulus (large blast radius), whereas ℓ-folding is a localized change that *also* fixes SEP.

**Automorphism-faithful alternative (note):** aggregate with the `σ`-automorphism + a challenge-derived unit
weight (true [LNP22] Fig 7.x). More faithful, but still `~1/p` in the smallest CRT field over composite `q̂`
(the automorphism spreads coefficients, it does not change which primes divide the modulus), so it *also*
needs `ℓ_agg` repetition here. ℓ-folding is therefore the essential ingredient regardless; do it directly.

---

## 6. Stack-wide application

`ℓ_agg`-folding is applied at the aggregation layer, so it covers every `a:` user at once:
1. `proof_agg_show`: add `prove_agg_vec` / `verify_agg_vec` (the ℓ_agg-vector masked quadratic) — or a
   `AggVecProof { t0s, t1s, lin }`. Keep `prove_agg` as `ℓ_agg=1` for callers that are provably single-row.
2. `SepRelation` / `OpeningRelation` / SPRING membership: derive `ℓ_agg` independent `μ^{(j)}` (domain-separated
   `mu_vector` seeds `…/agg/j`), expose the rows so the vector prover can re-aggregate per `j` (the relations
   already hold their `rows`; the `FullRingRelation` trait may need a `rows()`/`aggregate_with(μ)` hook).
3. `ℓ_agg = ⌈λ / log₂ p_min⌉` is **computed from the calibrated modulus** (Ref: this doc §5), NOT a hard
   constant — `= 7` only for the illustrative `p_min ≈ 2¹⁸·⁷`. Compute it in code from `p_min`; add a
   param-gate test asserting `(1/p_min)^{ℓ_agg} < 2⁻λ`. This couples `ℓ_agg` to the SAME HYP-330 modulus
   calibration that must already fix the Lemma 7.7 ZK bound (the illustrative `q̂` fails it) — one joint
   solve, not two.

**SEP note:** the SEP credential show is audited but behind `experimental-unaudited` and HYP-330-gated; this
is a genuine soundness strengthening of it, filed as its own issue and reviewed against the SEP show the same
way. It is NOT a silent change to shipped-verified behavior — the gate is still on.

---

## 7. Test plan (rule #27: integration + adversarial)

- **Attack regression (the point of the whole doc):** a `#[test]` that mounts §2 — construct `ŝ` with a
  `p_min`-coset-multiple row, and assert that with `ℓ_agg=1` a single hand-chosen `μ` (`μ ≡ 0 mod p_min`)
  makes the aggregate vanish (demonstrating the weakness concretely), while with the calibrated `ℓ_agg` no
  single grind survives (the honest path still verifies; the planted-violation path fails). Encodes the
  soundness *value*, not existence.
- **Round-trip:** honest witness → `ℓ_agg`-vector prove → verify, for SEP, issuance-π, and SPRING.
- **Size:** assert the measured `+2(ℓ_agg−1)` ring-element cost.

---

## 8. Decision log

- 2026-07-03: Josh chose **design-first, stack-wide** (over "accept as HYP-330" and "amplify SPRING only").
- Recommendation: **ℓ_agg-fold the aggregation layer** (`ℓ_agg = ⌈λ/log₂ p_min⌉`; `= 7`, `+12` ring elements,
  for the illustrative `p_min ≈ 2¹⁸·⁷`), applied stack-wide. Clean unconditional `<2⁻λ` soundness; no reliance
  on the §3 M-SIS-mod-`q₁` interaction.
- 2026-07-03 (Codex DESIGN-review, gpt-5.5/high): analysis ACCEPTED; one P1 — do not hard-code the
  illustrative `q̂`/`ℓ_agg`. Folded in: modulus + `p_min` + `ℓ_agg` are now symbolic/formula-driven, coupled to
  the HYP-330 modulus calibration (which must fix the Lemma 7.7 ZK bound anyway).
- Open for Codex DESIGN-review: (a) is the §2 grinding attack correctly realizable (esp. the freedom to plant
  a `q₁`-multiple row under the shortness + binariness constraints)? (b) does §3(A) actually rescue the
  one-shot case, making this a hardening rather than a fix? (c) is `ℓ_agg=7` the right target, or should it key
  off `q₁` (if the reduction only needs the larger prime)? (d) the `rows()`/`aggregate_with` trait hook shape.
- **2026-07-03 (chunk 1 done → scope broadened, §9 below).** Building the fix surfaced that §1 UNDERSTATED the
  scope: the one-shot weakness is at TWO levels, and the scalar families are NOT "already ℓ-amplified" as §1
  claimed. §9 corrects this; the recommendation now covers the scalar τ0 families and `ELL_AMP` too.

---

## 9. Scope correction — the weakness is at TWO aggregation levels (supersedes §1's scalar-family claim)

§1 said the scalar `extra` families "are already ℓ-amplified via the `h_i` rows" and only the `a:` relation is
one-shot. **That is wrong.** There are TWO aggregation levels, and only one of them is `h_i`-amplified:

- **Across-family (γ):** each `h_i = g_i + Σ_f γ_{i,f}·τ0(fam_f) + approx`, checked `τ0(h_i)=0` for `ℓ`
  independent `γ_i` rows. This IS amplified — a nonzero `τ0(fam_f)` is caught with `(1/p_min)^ℓ`. ✅
- **Within-family (μ):** each family is itself a ONE-SHOT FS-scalar aggregate of its sub-constraints —
  `s_binariness = aggregate(ETA binariness constraints, scalar_mu(t_A))` (`spring_scalar`), and identically
  `issuance_binariness = aggregate(constraints, mu_vector(t_A))` in the AUDITED SEP show (`proof_show`). The
  `h_i` only ever see `τ0(fam_f)` — the pre-aggregated value — so if a prover grinds `t_A` until a violated
  sub-constraint's within-family aggregate `τ0(fam_f)=0` (`~1/p_min`, and a binariness defect `≈ q₁` is
  reachable with a short `s` coeff `≈ 2^{19.5} < B`), ALL `ℓ` rows see `0`. **The within-family μ is NOT
  amplified.** ❌ Same `~1/p_min` grinding as the `a:` relation.

Two consequences the design must now carry:

1. **Scalar-family fix (simpler than the quadratic one): DE-AGGREGATE.** Feed the RAW sub-constraints into the
   `h_i` (no within-family `scalar_mu`/`mu_vector` pre-aggregation). Then the across-constraint `γ` sum — which
   is already the `h_i` mechanism — carries every sub-constraint directly, so a violated sub-constraint is
   caught with `(1/p_min)^ℓ`. Cost: the `h_i` sum widens from `n_families` to `n_sub_constraints` γ-terms (FS
   scalars are free; `h_i` stay the same ring size). No new primitive — it is a change to how the families are
   handed to the show. Applies to SPRING `binariness_families` AND SEP `issuance_binariness`.
2. **`ELL_AMP` must be `ℓ_agg`, not 1.** The `h_i` row count `ELL_AMP` (currently `1` in both `spring_show` and
   the SEP show) IS the across-family amplification exponent. `ELL_AMP=1` gives only `(1/p_min)¹` — the fix
   needs `ELL_AMP = ℓ_agg = ⌈λ/log₂ p_min⌉`. This is a one-line param change but a real soundness constant
   (traced to `p_min`), and it grows the proof by `ℓ_agg−1` extra garbage rows + `h_i`.

**Unified statement of the fix (stack-wide):** `ℓ_agg = ⌈λ/log₂ p_min⌉` is the single soundness exponent, and
it must appear in THREE places — (i) the `a:` quadratic relation → `prove_agg_vec` ℓ_agg independent aggregates
(chunk 1 primitive done); (ii) the scalar families → de-aggregated raw sub-constraints; (iii) `ELL_AMP = ℓ_agg`
h_i rows. All three, in both SPRING and the audited SEP show. Chunks 2–4 must implement all three, not just (i).
This is still within Josh's "fix the aggregation soundness stack-wide" decision — it is the same one-shot
FS-scalar-over-composite-`q̂` weakness, found at a second level.
