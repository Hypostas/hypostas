# LABRADOR_FOLD_PORT.md — sovereign LaBRADOR re-implementation roadmap (HYP-358 chunk 2)

**Status:** port sub-design (chunk 2 of `ANCHOR_FOLD_DESIGN.md`). Source-of-truth READ complete (`refs/labrador`
+ `refs/lattirust` cloned for reference). Goal: a faithful, sovereign (zero-C, no alpha/git deps)
re-implementation of the LaBRADOR core over our existing proof ring `R_q̂`, so the κ anchor-bind openings
fold to O(log). **Multi-week, soundness-critical** — every constant traces to the reference; gate each
sub-chunk (Codex gpt-5.5/high).

---

## 0. Why a re-implementation, not a port (the dependency finding)

`refs/labrador` is **not self-contained**: its `fold_instance`/`prover`/`verifier` depend on the lattirust
research framework — `lattirust-arithmetic` (`PolyRing`, `Matrix`/`SymmetricMatrix`/`Vector`, the
`decomposition::balanced_decomposition` traits, `inner_products`, the `challenge_set`s), `relations`
(`Index`/`Instance`/`Witness`/`QuadraticConstraint`/`Size`), `lattice-estimator` (MSIS rank selection), and
`nimue` (Fiat–Shamir). All are `0.0.1-alpha` **git-only** crates. For sovereign `vouch-crypto` (strict
zero-C, minimal *audited* deps — the reason it avoids `bbs_plus`), pulling these is out. So we **re-implement
the needed subset** over what we already own:

| Need | Reuse / build |
|---|---|
| Poly ring `R_q̂` (NHAT=64, composite q̂) | **reuse** `proof_ring.rs` (`ProofRingElem`, ops, NTT) |
| base-`b` balanced decomposition | **reuse/extend** `sep_gadget.rs` (has base-`b`); needs the *balanced* (signed, 2-part) variant |
| MSIS rank selection (k/k1/k2) | **reuse** our validated M-SIS core-SVP estimator (the HYP-352 FU1 work) |
| Fiat–Shamir | **reuse** our SHA-256 FS pattern (as every `proof_*` module does); NOT nimue |
| Matrix / SymmetricMatrix / Vector over `R_q̂` | **build** (`labrador_fold::linalg`) — mechanical, low soundness-risk |
| `inner_products` (Gram `G`), `inner_products2` | **build** |
| challenge sets (`LabradorChallengeSet` c, `WeightedTernaryChallengeSet` Π) | **build** (the operator-norm / variance constants are soundness-critical) |
| relation model (`Index`/`Instance`/`Witness`/`QuadraticConstraint`/`Size`) | **build** (`labrador_fold::relation`) |
| CRS + norm tracking + recursion (`fold_instance`) | **build** (`labrador_fold::crs` + `::fold`) — the hardest, most soundness-critical |
| prover / verifier | **build** (`labrador_fold::{prover,verifier}`) |

---

## 1. The construction (what we are re-implementing — `prove_principal_relation_oneround`)

One round reduces a principal relation `{(A·sᵢ = tᵢ), Σ quadratic/linear dot-product constraints, ‖s‖² ≤ β²}`
to a SMALLER one, then recurses until the base case (`recurse()` = last-message-size ≤ proof-size):

1. **Msg 1 — commit.** `tᵢ = A·sᵢ` (k×r); decompose `t` in base `b1` (→ `t1×r×k`); Gram `G = ⟨sᵢ,sⱼ⟩`
   (upper-tri r×r); decompose `G` in base `b2`. Outer commit `u₁ = B·t_flat + C·G_flat`. Absorb `u₁`.
2. **Chal 1 — JL.** `Π` = 256 `WeightedTernary` projection matrices (r of them, 256×n).
3. **Msg 2 — JL projection.** `p[j] = Σᵢ ⟨πᵢⱼ, sᵢ⟩` (in `R::BaseRing^{256}`). Absorb `p` (proves `‖s‖`
   small via the 256-dim projection — the norm-check leg).
4. **Chal 2 — `psi`, `omega`** (aggregate the constant-coefficient constraints into `num_aggregs` of them).
5. **Msg 3 — aggregate ct.** `a''`, `phi''` (via `psi`/`omega`, incl. the `σ_{-1}` conjugation over Π — the
   `ct` trick), `b''ₖ = Σ a''ₖ[i,j]·G[i,j] + Σ ⟨phi''ₖᵢ, sᵢ⟩`. Absorb `b''`.
6. **Chal 3 — `alpha`, `beta`** (aggregate ALL quadratic + the ct-aggregated constraints into ONE).
7. **Msg 4 — commit H.** `phi = Σ alpha·phiₖ + Σ beta·phi''ₖ`; `H = ½(⟨phi,s⟩ + ⟨s,phi⟩)` (symmetric r×r);
   decompose `H` in base `b1`. Outer commit `u₂ = D·H_flat`. Absorb `u₂`.
8. **Chal 4 — `c`** (`LabradorChallengeSet`, r challenges — the amortization coefficients).
9. **Amortize + fold.** `z = Σ cᵢ·sᵢ`; decompose `z` in base `b` (2 parts `z₀,z₁`). The next **witness** is
   `(z₀, z₁, t_flat, G_flat, H_flat)` laid out by `Layouter`; the next **instance** is the 6 constraint
   families `fold_instance` emits (Az=Σcᵢtᵢ ; ⟨z,z⟩=Σgᵢⱼcᵢcⱼ ; Σ⟨phiᵢ,z⟩cᵢ=Σhᵢⱼcᵢcⱼ ; Σaᵢⱼgᵢⱼ+Σhᵢᵢ=b ;
   u₁ ; u₂). Recurse with `next_crs`.

The **verifier** mirrors: recompute the outer commitments / the JL / the aggregation challenges from FS,
check each round's constraints hold on the folded witness, terminate at the base case.

---

## 2. The constants that MUST trace to the reference (soundness-critical)

From `common_reference_string.rs` — re-derive, do NOT hardcode blindly; gate each:
- **`b`** (main decomp basis) `= ceil_to_even( sqrt( r·‖c‖∞·⌊β⌋ ) )`; `assert b>1`.
- **`(t1,b1)`**: `t1 = round(log₂q / log₂b)`, `b1 = round_to_even( q^{1/t1} )`.
- **`(t2,b2)`**: from `s_dev² = β²/(r·n·d)`, `tmp = sqrt(24·n·d)·s_dev²`, `t2 = round(log₂tmp/log₂b)`,
  `b2 = round_to_even( tmp^{1/t2} )`.
- **`num_aggregs` = ceil(128 / log₂q)** (the constant-constraint aggregation count = the `ct`-trick width).
- **`MAX_RECURSION_DEPTH = 7`**; `β² *= sqrt(128/30)^7` slack pre-multiplier; `assert β < sqrt(30/128)·q/125`.
- **`next_norm_bound_sq`** (§5.4 of the paper) — the per-round norm growth; the single most important
  soundness formula (decides whether the folded instance is still a valid SIS relation). Port EXACTLY.
- **`k` / `k1=k2`** — MSIS-hard commitment ranks via our estimator at the round's `norm_bound_1`.
- challenge-set constants: `LINF_NORM`, `OPERATOR_NORM_THRESHOLD`, `VARIANCE_SUM_COEFFS` (the `c` set);
  the WeightedTernary distribution (Π). These bound `‖c‖`, `‖z‖` — soundness-critical.
- JL = **256** projections; the projection norm-check threshold.

---

## 3. Build order — sub-chunks (each: tests + Codex gpt-5.5/high gate)

Order chosen so each lands WITHOUT regressing anything (all additive in a new `labrador_fold/` module tree;
the existing `proof_anchor_bind.rs` is untouched until chunk 3 of `ANCHOR_FOLD_DESIGN`):

- **2a — linalg + relation model** (LOW soundness-risk, mechanical): `Matrix`/`SymmetricMatrix`/`Vector`
  over `ProofRingElem`; `inner_products`(Gram)/`inner_products2`; `flatten_*`; `Index`/`Instance`/`Witness`/
  `QuadraticConstraint`/`Size`. Tests: matrix-algebra round-trips, `is_wellformed_{instance,witness}`,
  Gram symmetry. *Start here.*
- **2b — balanced decomposition** over `R_q̂`: signed base-`b` decompose of vectors + symmetric matrices,
  2-part `z` decomposition. Reuse/extend `sep_gadget`. Tests: `recompose(decompose(x)) == x`; norm of parts.
- **2c — challenge sets**: `LabradorChallengeSet` (c) + `WeightedTernary` (Π) with the exact norm/operator-
  norm/variance constants (§2). Tests: encode the constants; assert `‖c‖∞`, operator-norm bounds.
- **2d — CRS + norm tracking** (HIGH soundness-risk): `b/b1/b2/t1/t2`, `num_aggregs`, `next_norm_bound_sq`,
  `k/k1/k2` via our MSIS estimator, the A/B/C/D matrices, `next_size`/`FoldedSize`, the recursive `next_crs`.
  Tests: reproduce the reference's param table for a known `Size`; assert `next_norm_bound_sq` matches the
  paper §5.4 on a worked example.
- **2e — `fold_instance`** (HIGH soundness-risk): the 6 constraint families + the `Layouter`. Tests: the
  folded instance is well-formed; an honest witness satisfies every emitted constraint.
- **2f — prover** (`prove_principal_relation_oneround` + the recursion loop) over our SHA-256 FS. Tests: a
  full prove runs; the transcript is deterministic under a fixed seed.
- **2g — verifier** + the base case. Tests (rule #27): **honest prove→verify round-trips at small params**;
  a tampered `z`/`c`/commitment **rejects**; the recursion terminates. Gate against transcribed reference
  vectors where feasible (run `refs/labrador`'s own tests to extract expected intermediate values).

Then `ANCHOR_FOLD_DESIGN` chunks 1+3+4 (un-compress the FS in `proof_anchor_bind.rs`, express the anchor
relation `R_j` + `ct`-pins as a LaBRADOR `Instance`, re-compose into `pq_vouch`, re-measure size).

---

## 4. Soundness obligations carried from `ANCHOR_FOLD_DESIGN` §3 (close per-chunk, gate)

(a) LaBRADOR extractor over κ openings of ONE commitment `t_A` — the amortization's `c`-invertibility over q̂.
(b) Norm bound `B²` propagation through the base-`b` recursion = `next_norm_bound_sq`, validated in 2d.
(c) The anchor digit-pins are `ct`-linear ⇒ expressible as `QuadraticConstraint::ct` (the `psi`/`omega`
    aggregation in 2e). (d) ZK / HVZK — no `s1` leak beyond `bind.rs` (the JL + the amortization masks).

---

## 5. Honest scope

This is a multi-session, research-grade build. 2a–2c are mechanical/bounded (days). 2d–2e are the
soundness-critical heart (the norm tracking + the recursion) — slow, every constant validated. 2f–2g compose
+ test. Each sub-chunk is a self-contained, additive, gate-clean commit; nothing in the live C3 path changes
until `ANCHOR_FOLD_DESIGN` chunk 3 wires the fold into `proof_anchor_bind.rs`. Process: this roadmap →
Codex DESIGN-review → 2a → … → 2g → fold-wire.

---

## 6. De-risking findings (2026-06-30 parameter study) — the plan is now CONCRETE and simpler than §5 feared

**Done + gate-clean (12 sub-chunks):** 2a (linalg+relation), 2b (balanced decomposition), 2c (challenge
set + sovereign Jacobi operator-norm + FS sampling), 2d-i (`next_norm_bound_sq`), 2d-ii(a) (sovereign MSIS
estimator, δ=1.0045), 2d-ii(b1) (`select_params`), 2d-ii(b2) (`next_size`, the `Crs` struct + XOF-derived
A/B/C/D matrices, `proof_size`/`last_prover_message_size`/`is_base_case`, the recursive `next_crs` chain +
`InflationPolicy`). Plus `fold_feasibility.rs` — a `#[cfg(test)]` q-parametric mirror of the recursion,
cross-checked against production at `q=QHAT`, that drove the findings below.

**THREE bugs in the lattirust 0.0.1-alpha reference (it can't compact as-is; do NOT faithfully port these):**
1. **`recurse()` is inverted.** `last>proof` is its chain TERMINATOR, so it folds only while `last≤proof` —
   but `last>proof` holds for every realistic instance → it never folds. Corrected: `is_base_case = last≤proof`
   (fold WHILE compression helps). A free size-opt within the slack budget (every round is independently
   sound). Already applied in `crs.rs::is_base_case`.
2. **Norm recurrence is a PRODUCT, must be a SUM.** `next_norm_bound_sq = (2/b²)γ² + γ1²·γ2²`. The folded
   witness is a CONCATENATION (z,t,g,h) → norm² = `γ1²+γ2²` (triangle inequality). The product over-estimates
   and explodes ∝ r³ → infeasible before any base case. **NOT yet applied to `crs.rs` — soundness-critical,
   needs the paper (eprint 2022/1341 §5) to confirm the exact recurrence.**
3. **`next_size` GROWS r, must keep r SMALL.** It balances the components; LaBRADOR balances next-proof
   Gram(∝r²) vs witness(∝n) → `r_next ~ total^(1/3)`. With the ref's growth, r explodes → witness never
   shrinks → no compaction even with bug 2 fixed. **NOT yet applied — same paper-confirm gate as bug 2.**

**Empirical validation (gate-clean, honest raw-tail accounting):** SUM + r^(1/3) packing COMPACTS. On the
REAL anchor relation estimate (~57MB ≈ 123k ring elements, n~131072, β²~1e12–1e15): **30–57× compaction**.
**Modulus: ~2^62 suffices** (2^64 → 57×, 20MB→346KB; a SMALLER q compacts BETTER). ⇒ the fold-ring is a
modest **i64-coefficient / i128-product ring** (same structure as `proof_ring`, just a bigger NTT prime) —
**NO 2^256 bignum / u256 / RNS** (the earlier fear is dead).

**Revised build order (concrete):**
- **(P) Paper-confirm** bugs 2+3 vs eprint 2022/1341 §5 (the exact norm recurrence + the (r,n) packing rule).
  BLOCKING for the production change; un-fetchable in-session (Cloudflare) — needs the PDF in `refs/`.
- **2x — fold-ring** (`fold_ring.rs`): a `proof_ring`-style ring at a ~2^62 NTT-friendly prime `q≡1 mod 128`
  (i64 coeffs, i128 products fit since `q²<2^124<i128::MAX`). Mirror `ProofRingElem` (add/sub/mul negacyclic,
  `sample_uniform`, `conjugate`, `centered_coeffs`). Paper-INDEPENDENT — can build anytime.
- **2d-fix** — apply bug-2 (sum) to `next_norm_bound_sq` + bug-3 (`r_next~total^(1/3)`) to `next_size`, and
  re-target `crs.rs` from `QHAT` to the fold-ring modulus. Regression: the fold chain now reaches a base case
  + the real relation compacts ≥19×.
- **2e/2f/2g** over the fold-ring (the recursion mechanics, prover, verifier — unchanged plan from above).
- **ANCHOR_FOLD 1+3+4** — ⚠️ **SUPERSEDED (2026-06-30): the fold is a BASE CASE for the real anchor relation.**
  Measured `r=κ=128, n≈769, β²≈8.4e14 ⇒ depth=1, ratio=1.0× across q∈{2^58..2^80}` (`proof_anchor_bind::
  measure_real_anchor_opening_size` + `fold_feasibility::compaction_at_real_anchor_shape`). 114k-element /
  β²≈8.4e14 relations are below LaBRADOR's useful threshold (per-round overhead ≥ the witness), so the recursive
  fold does NOT compact the κ openings — do NOT wire it into `pq_vouch`. The structural fold (2e/2f/2g, complete
  + completeness-proven, `vouch-crypto/src/labrador_fold/`) stays a reusable primitive. The anchor compaction
  pivoted to shrinking the openings at the source — see `ANCHOR_RANGE_COMPACT_DESIGN.md` (≈2.6–3.5×) +
  natural-bit-width serialization (~3.7×). The original `57MB→~350KB` target was the (now-disproven) recursive
  premise.

---

## 7. The folded-norm derivation (the missing soundness proof for the SUM — gates the 2d-fix swap)

*Status: Iris's derivation, pending Codex gate-of-design + (ideally) BS23 §5 confirmation. `next_norm_bound_sq`
keeps the conservative reference PRODUCT in production until this is confirmed (Codex gate P1, 2026-06-30 —
the norm bound IS the soundness, so it must not use an unproven smaller estimate). This §7 is the proof the
gate asked for.*

**Claim.** The per-round folded squared-norm bound is `(2/b²)·γ² + (γ1² + γ2²)` — a **SUM** — not the
reference's `(2/b²)·γ² + γ1²·γ2²` **PRODUCT**. The product is a transcription bug (`·` for `+`); it has no
structural justification and explodes ∝ r³, which is why the lattirust `0.0.1-alpha` port never compacts.

**Derivation.** After one LaBRADOR fold, the next round's witness vector is the **concatenation** of the
balanced-decomposed components the prover commits to:
- `z` — the amortized witness `z = Σ_i c_i·s_i`, decomposed into `2` parts in base `b`;
- `t` — the inner commitments `t_i = A·s_i`, decomposed into `t1` parts in base `b1`;
- `g` — the Gram matrix `g_ij = ⟨s_i, s_j⟩` (i ≤ j), decomposed into `t2` parts in base `b2`;
- `h` — the linearization vector, decomposed into `t1` parts in base `b1`.

The next witness is `s' = (z‖t‖g‖h)`, an **orthogonal direct sum** (the components occupy disjoint
coordinates). Hence `‖s'‖² = ‖z‖² + ‖t‖² + ‖g‖² + ‖h‖²` — a SUM with **no cross terms**. Grouping the
reference's `γ`-variables onto these components:
- `(2/b²)·γ²` = `‖z-decomposition‖²` (the 2 base-`b` parts of the amortized `z`; `γ² = β²·τ`);
- `γ1² = b1²·t1/12·(r·k·d) + b2²·t2/12·(r(r+1)/2·d)` = `‖t-decomp‖² + ‖g-decomp‖²`;
- `γ2² = b1²·t1/12·(r(r+1)/2·d)` = `‖h-decomp‖²`.

So `‖s'‖² = (2/b²)γ² + γ1² + γ2²` — the SUM. ∎

**Resolving the gate's Cauchy–Schwarz P1.** The gate's concern was that `g_ij = ⟨s_i,s_j⟩` is bounded by a
**product** `‖s_i‖·‖s_j‖ ≤ β²` (Cauchy–Schwarz), so a product term "should" appear. It does — but in the
**sizing of `b2`**, not in the folded-norm sum. The decomposition base for `g` is chosen as
`b2 ≈ (g-entry magnitude)^{1/t2} ≈ (β²)^{1/t2}` precisely because each `g_ij ≤ β²` (the Cauchy–Schwarz
product). The decomposed `g`-parts then have coefficients `≤ b2/2`, contributing `‖g-decomp‖² =
b2²·t2/12·(r(r+1)/2·d)` to `γ1²` — an **additive** term. The product is fully accounted for by `b2`'s value;
adding it *again* as `γ1²·γ2²` would double-count it (and is dimensionally a squared-norm times a
squared-norm — not a norm bound). So the SUM is the correct, tight, **sound** extractor bound: the extracted
witness `s'` is a concatenation, and its norm is the root-sum-square of the (correctly Cauchy–Schwarz-sized)
component norms.

**Consequence.** Once this §7 passes the Codex gate-of-design (and/or BS23 §5 confirms the same), the 2d-fix
swap of `next_norm_bound_sq` to the SUM is justified and re-applied to production with this proof cited
inline. The `r_next ~ total^(1/3)` packing (bug 3) is independently soundness-neutral (it only reshapes the
instance; the norm bound is computed correctly for whatever `(r,n)` results), so it can land with the sum.
