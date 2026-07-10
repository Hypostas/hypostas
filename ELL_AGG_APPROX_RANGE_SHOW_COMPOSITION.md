# ℓ_agg × HYP-375 W-slice — SEP-show composition (design-first)

**Status:** DESIGN, pending Codex DESIGN-review (2026-07-10, Iris + Josh). Governs the `iris/ell-agg-foundation` build.
**Layer:** spec/intent — in-repo; the ℓ_agg foundation PR implements against it.

## Why this doc exists

`main` and the SPRING branch line each carry a *different, independent* soundness fix to the SEP credential
show + blind-issuance-π (`proof_show::prove_show_agg_with_extra` / `verify_show_agg_with_extra` and the
issuance twins), and **neither has the other's**:

- **`main` has the HYP-375 approx-range fix** — a SECOND range family (the W *scoped-norm-slice* `z3_norm`)
  alongside the global Y range, plus Fiat–Shamir *with aborts* and the `R = H(t_A, t_B)` post-commitment
  projection (`APPROX_RANGE_FS_FIX_DESIGN`). But its family aggregation is **one-shot**: `ell = 1`, one
  `h_i` row, `[nc1, nc2, aggregated_binariness]`, `prove_agg` → one `(t0,t1)` garbage pair
  (`AggQuadProof`). This is the `~1/p_min ≈ 2⁻¹⁹` composite-`q̂` grindable-aggregation gap.
- **The SPRING branch has the ℓ_agg fold** (`AGGREGATION_SOUNDNESS_COMPOSITE_MODULUS.md`) — the two-axis
  amplification `ELL_AMP = ell_agg()` `h_i` rows × `ell_agg()` μ-copies of `SumRelation{SepRelation::
  new_indexed(j), sep_scalar_form(mus⁽ʲ⁾)}` via `prove_agg_vec` (`AggVecProof`, `ell_agg` garbage pairs),
  de-aggregated families (`sep_show_families`). But it predates HYP-375 → **one range only** (`ell =
  params.ell − Y3_BLOCKS`, `stride = APPROX_DIM + n_f`, `R = H(t_A)`).

The merged SEP show must carry **both**: the W-slice second range AND the ℓ_agg fold. Each mechanism got
its own design doc + Codex DESIGN-review before it was built; composing them is not a mechanical merge
(22 conflict hunks in `proof_show.rs` + 2 in `pq_vouch.rs`), so it gets the same rigor.

## The claim: the two mechanisms are ORTHOGONAL

**Re-derived from the two prove bodies, not assumed.** In `main`'s HYP-375 prove (`proof_show.rs:1563`),
each `h_i` is built from a gamma vector partitioned into **three disjoint coordinate ranges**:

```
gammas[i*stride .. (i+1)*stride]  =  [ g_approx (APPROX_DIM=256) | g_slice (APPROX_DIM=256) | family γ (n_f) ]
                                        └── Y global range ──┘   └── W scoped slice ──┘   └── families ──┘
h_i = g[i]
    + Σ_b conj(Γ(g_approx,b))·Y_b + Σ_β conj(ρ(g_approx,R,β))·s1_β − (γ_approx·z3)·1        // Y range
    + Σ_b conj(Γ(g_slice,b))·W_b + Σ_β' conj(ρ(g_slice,R_slice,β'))·s1_{slice_idx[β']} − (γ_slice·z3_norm)·1  // W range
    + Σ_f γ_{i,f}·family_f                                                                   // families
```

- The **range mechanism** (Y, W) lives entirely in the first `2·APPROX_DIM` gamma coordinates + the
  `z3`/`z3_norm` responses + the FS-with-aborts loop that binds `R,R_slice = H(t_A,t_B)`. It does **not**
  depend on `ell` (the row count), on the μ-copies, or on how the families are aggregated. Adding rows or
  μ-copies re-indexes `g_approx`/`g_slice` per row but changes nothing about *how* the range binds.
- The **family-aggregation mechanism** (ℓ_agg) lives in `ell` (row count), the `family γ` gamma tail, the
  de-aggregation of families, and the μ-copy count fed to `prove_agg_vec`. It does **not** touch the range
  coordinates.

The two share only the *vehicle* — the `h_i` vector and its `τ0(h_i)=0` reveal — into which both fold as
**additive terms over disjoint gamma coordinates**. So they compose by superposition: take `main`'s
2-range `h_i` weave verbatim, and run it under the ℓ_agg fold's row/μ-copy regime.

## The merged prove (`prove_show_agg_with_extra`, and the issuance twin)

```
ell = params.ell.checked_sub(2 * Y3_BLOCKS)?;      // params.ell = 2·Y3_BLOCKS + ell_agg()  (both ranges + fold)
if ell != ell_agg() { return None; }               // ℓ_agg: pin the row count so verify rebuilds identically

// RANGE (HYP-375, verbatim from main): FS-with-aborts, TWO ranges, R,R_slice = H(t_A, t_B).
slice_idx = short_witness_indices(vk, m1); slice_s1 = slice_elems(s1, slice_idx);
g = sample_garbage(ell, rng);                       // ell = ell_agg() garbage polys (was 1 on main)
loop { y3, y3_norm ← sample_mask; Y,W ← pack_y3; m_hat = [Y | W | g_1..g_{ell_agg}];
       t_b = commit_garbage(m_hat); seed = H(t_a,t_b); R = derive(seed); R_slice = derive(slice_seed(seed));
       z3 = project_response(y3,R,s1); z3_norm = project_response(y3_norm,R_slice,slice_s1);
       until z3_in_bound(z3) && z3_in_bound(z3_norm) }

// FAMILIES (ℓ_agg): DE-AGGREGATED, not [nc1,nc2,aggregated_binariness].
families = sep_show_families(vk, slack1_blk, slack2_blk, extra);   n_f = families.len();
stride = 2*APPROX_DIM + n_f;                        // TWO ranges (main) + de-aggregated families (ℓ_agg)
gammas = fs_scalars(dom_gamma, t_a, t_b, [], ell * stride);

// h_i: main's 2-range weave (g_approx + g_slice + families), run over ell = ell_agg() rows.
h = (0..ell).map(|i| { let base = i*stride;                                  // disjoint per-row block
       g_approx = gammas[base .. base + APPROX_DIM];                          // Y range coords
       g_slice  = gammas[base + APPROX_DIM .. base + 2*APPROX_DIM];           // W range coords (offset!)
       hi = g[i] + <Y-range terms with g_approx,R,z3> + <W-range terms with g_slice,R_slice,z3_norm>
                 + Σ_f family_f.eval_ring(s1) · gammas[base + 2*APPROX_DIM + f]; hi }).collect();

// FOLD (ℓ_agg): ell_agg() μ-copies of SumRelation{SepRelation::new_indexed(j), sep_scalar_form(mus⁽ʲ⁾)}
//              proven SIMULTANEOUSLY by prove_agg_vec (ell_agg garbage pairs), NOT prove_agg.
agg = prove_agg_vec(params, t_a, combined_copies, s1, s2, m_hat, SEP_MASK_SIGMA, context, rng)?;
return ShowAggProof { agg /* AggVecProof */, h, z3, z3_norm };
```

Only three things change from `main`'s prove: (a) `ell` is now `ell_agg()` and pinned; (b) `families`
comes from `sep_show_families` (de-aggregated) so the fold's per-row `τ0(h_i)=0` amplification bites; (c)
the relation is built as `ell_agg` independent μ-copies and proven by `prove_agg_vec`. The entire
2·APPROX_DIM range block — sampling, FS-with-aborts, the `g_approx`/`g_slice` `h_i` terms, `z3`/`z3_norm`
— is `main`'s HYP-375 code unchanged.

## The merged verify

Mirror: `stride = 2*APPROX_DIM + SHOW_FAMILIES_deagg + extra.len()`, rebuild the `ell_agg` `h_i` from
`z3`/`z3_norm`/`R`/`R_slice` + the de-aggregated families, check `τ0(h_i)=0 ∀ i∈[ell_agg]`, check
`‖z3‖,‖z3_norm‖` in bound, and call `verify_agg_vec` (ell_agg μ-copies) — not `verify_agg`.

## Params

`IssuanceParams` / the SEP-show `AbdlopParams` set **`ell = 2·Y3_BLOCKS + ell_agg()`** (was `2·Y3_BLOCKS +
1` on `main`; was `Y3_BLOCKS + ell_agg()` on the SPRING branch). Production dims (`PROD_AJTAI_RANK=20`,
`PROD_ABDLOP_M2=74`, HYP-352 item-3) are `main`'s and unchanged — the SPRING branch's inline toy `3/6`
is superseded (it predates item-3). Codec: `AggVecProof` encode/decode (ℓ_agg) + the `z3_norm` field
(HYP-375) coexist — the merged `ShowAggProof` = `{ agg: AggVecProof, h, z3, z3_norm }`.

## Soundness

Both properties are preserved because the mechanisms are orthogonal (disjoint gamma coordinates, additive
`h_i` terms):

1. **Range binding (both Y and W) — unchanged from HYP-375.** The `R = H(t_A, t_B)` post-commitment
   projection + FS-with-aborts is byte-identical to `main`; it is independent of `ell`, the μ-copies, and
   the family set. Adding rows only re-indexes `g_approx`/`g_slice`; the per-range binding argument
   (`APPROX_RANGE_FS_FIX_DESIGN` §1/§3) is untouched. The adaptive-mask forgery stays closed.
2. **Composite-`q̂` family soundness — unchanged from ℓ_agg.** The `ELL_AMP = ell_agg()` `h_i` rows +
   `ell_agg()` μ-copies via `prove_agg_vec` give `(1/p_min)^{ell_agg}` on a violated SEP/binariness family
   (`AGGREGATION_SOUNDNESS_COMPOSITE_MODULUS.md` §10 A/B/C). The added W-slice range contributes an
   independent additive `h_i` term over its own `g_slice` coordinates; it neither shares a garbage
   coordinate with a family nor enters the μ-copy relation, so it cannot cancel or grind the family
   amplification.

**Adversary (the strongest attack, named + beaten):** can a prover exploit the *cross-terms* — pick a
witness that violates a family (or a range) but is masked by the *other* mechanism's freedom? No: in each
`h_i`, the family term `Σ_f γ_{i,f}·family_f(s1)` and the range terms use **disjoint** gamma coordinates
(`stride` partitions `[g_approx | g_slice | family γ]`), and `fs_scalars` samples all `ell*stride` gammas
from one transcript-bound XOF, so the adversary cannot choose one block's γ to cancel another's — every
γ is fixed by `H(t_a, t_b, …)` after the witness is committed. A family violation must be zeroed in ALL
`ell_agg` rows (each with independent γ), *and* survive all `ell_agg` μ-copies of the SEP relation
(independent `mu_vector_indexed(j)`); a range violation makes `z3`/`z3_norm` fall out of bound
independently of the fold. The two failure channels are separate and each retains its own bound.

## Build map (the 22 + 2 conflict hunks)

- `IssuanceParams`/`with_dims`/`new`: `ell = 2·Y3_BLOCKS + ell_agg()`; keep `main`'s production dims +
  `with_dims` refactor (item-3), drop the SPRING toy `3/6` inline.
- `prove_show_agg_with_extra` + issuance prove: keep `main`'s 2-range FS-abort block verbatim; swap
  `families` → `sep_show_families`, `ell 1 → ell_agg()` (+pin), `prove_agg → prove_agg_vec`, μ-copies.
- `verify_show_agg_with_extra` + issuance verify: `stride = 2*APPROX_DIM + …`, `verify_agg → verify_agg_vec`.
- `pq_vouch.rs` (2 hunks): the `ell` wiring (`Y3_BLOCKS + ell_agg()` → `2*Y3_BLOCKS + ell_agg()`) + the
  de-aggregated `issuance_binariness_subs` already on `main` from HYP-375's item-3 line — reconcile to the
  merged `ell`.
- codec (`50c3730a`): `AggVecProof` put/read (ℓ_agg) alongside `z3_norm` (HYP-375, already on `main`);
  bump the versions (already v5 on `main`).

Every changed constant/relation traces here or to the two parent docs. Build = resolve the hunks to this
design; then integration + smoke (a full SEP-credential + blind-issuance round-trip that trait-verifies)
and the cross-vendor gate (crypto-critical: encoding · state · spec · concurrency + a Claude soundness
refute leg on the orthogonality claim).
