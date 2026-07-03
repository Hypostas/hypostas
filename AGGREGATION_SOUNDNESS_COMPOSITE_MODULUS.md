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

`q̂ = PHAT_P · PHAT_Q1 = 425801 · 549755813869 ≈ 2⁵⁷·⁷`, `p ≈ 2¹⁸·⁷`, `q₁ ≈ 2³⁹·⁰`. `q̂` is composite
because the SEP credential ring is `R_p`; the show needs the larger `q̂`.

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
equation in the FS scalars `μ`. Over the random `μ = mu_vector(t_A)`, `F ≡ 0 (mod p)` holds with probability
**`~1/p ≈ 2⁻¹⁸·⁷`**. The prover **grinds `t_A`** (re-randomises the commitment) until the FS-derived `μ`
zeroes the mod-`p` aggregate. Expected work: **`~2¹⁸·⁷` hashes.** Then `F(ŝ*) = 0` **honestly**, the masked
quadratic (layer 1) proves it truthfully, and the verifier accepts a witness with `r(ŝ*) ≠ 0`.

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
A cheater's planted row survives all `ℓ_agg` collapses only with probability `(1/p)^{ℓ_agg}`. With
`p ≈ 2¹⁸·⁷`, **`ℓ_agg = 7 ⇒ (1/p)⁷ ≈ 2⁻¹³¹ < 2⁻¹²⁸`**. Soundness becomes clean and unconditional — no
reliance on the §3 M-SIS-mod-`q₁` interaction, no per-component calibration subtlety.

**Mechanism (implementation).** `prove_agg` proves one `F=0`; extend it to a **vector** of `ℓ_agg`
relations sharing the *same* linear opening `(w, z1, z2)` and challenge `c`, with `ℓ_agg` garbage pairs
`(t0_j, t1_j)`:
- Prover: for each `j`, `e0_j = F_j.quad_part(y)`, `e1_j = F_j.cross(y,ŝ)+F_j.lin_part(y)`,
  `t0_j = ⟨b,y2⟩+e0_j`, `t1_j = ⟨b,s2⟩... ` — wait: the `⟨b,s2⟩` term is shared; only the relation part
  `e0_j/e1_j` differs. So `t0_j = ⟨b,y2⟩ + e0_j`, `t1_j = ⟨b,s2⟩ + e1_j`. Challenge `c` binds all `t0_j,t1_j`.
- Verifier: the same reconstruction per `j`; accept iff all `ℓ_agg` check.
- **Cost:** `+2(ℓ_agg−1)` ring elements over the current single garbage pair (`w, z1, z2` shared). For
  `ℓ_agg=7`: `+12` `R_q̂` elements. `w/z1/z2` (the bulk) are unchanged — the proof stays log-size in the ring
  depth `δ`.

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
3. `ℓ_agg` is a **calibration constant** `⌈128 / log₂ p⌉ = 7` (Ref: this doc §5) — a real constant traced to
   `p`, not a magic number. Add an estimator-style test asserting `(1/p)^{ℓ_agg} < 2⁻¹²⁸`.

**SEP note:** the SEP credential show is audited but behind `experimental-unaudited` and HYP-330-gated; this
is a genuine soundness strengthening of it, filed as its own issue and reviewed against the SEP show the same
way. It is NOT a silent change to shipped-verified behavior — the gate is still on.

---

## 7. Test plan (rule #27: integration + adversarial)

- **Attack regression (the point of the whole doc):** a `#[test]` that mounts §2 — construct `ŝ` with a
  `q₁`-multiple row, and assert that with `ℓ_agg=1` a single hand-chosen `μ` (μ ≡ 0 mod p) makes the aggregate
  vanish (demonstrating the weakness concretely), while with `ℓ_agg=7` no single grind survives (the honest
  path still verifies; the planted-violation path fails). This encodes the soundness *value*, not existence.
- **Round-trip:** honest witness → `ℓ_agg=7` vector prove → verify, for SEP, issuance-π, and SPRING.
- **Size:** assert the measured `+2(ℓ_agg−1)` ring-element cost.

---

## 8. Decision log

- 2026-07-03: Josh chose **design-first, stack-wide** (over "accept as HYP-330" and "amplify SPRING only").
- Recommendation: **ℓ_agg-fold the aggregation layer** (`ℓ_agg=7`), applied stack-wide, cost `+12` ring
  elements. Clean unconditional `2⁻¹³¹` soundness; no reliance on the §3 M-SIS-mod-`q₁` interaction.
- Open for Codex DESIGN-review: (a) is the §2 grinding attack correctly realizable (esp. the freedom to plant
  a `q₁`-multiple row under the shortness + binariness constraints)? (b) does §3(A) actually rescue the
  one-shot case, making this a hardening rather than a fix? (c) is `ℓ_agg=7` the right target, or should it key
  off `q₁` (if the reduction only needs the larger prime)? (d) the `rows()`/`aggregate_with` trait hook shape.
