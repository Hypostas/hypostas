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
