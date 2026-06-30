# ANCHOR_RANGE_COMPACT_DESIGN.md — shrink the κ anchor openings by un-replicating non-EC witness

**Status:** design-first (no code), **needs Codex DESIGN-review** (the §3 reframing of `ANCHOR_COMPACTION_DESIGN`
option D is soundness-subtle — the bind took **13 design-review iterations** to settle, `ANCHOR_BIND_DESIGN`;
that is the design-process count, NOT the κ≈128 binary soundness rounds — so do not assume an obvious win). Goal:
shrink the C3 anchor openings ~2–3.5× by removing witness the cross-domain EC binding does NOT need from the
per-round opening path.

Refs: `ANCHOR_COMPACTION_DESIGN.md` (the size investigation + options A/B/D/E), `ANCHOR_BIND_DESIGN.md` (the
κ-round bind, 13 rounds), `ANCHOR_FOLD_DESIGN.md` (option B), `proof_anchor_bind.rs`, `proof_ltconst.rs`,
`pq_vouch.rs` (the unified `s1` layout).

## 0. Why this — option B (folding) is now CONFIRMED a base case

`ANCHOR_COMPACTION_DESIGN §5` chose **B (LaBRADOR-style recursive folding of the κ rounds)** as the real path.
HYP-358 built a complete, completeness-proven sovereign LaBRADOR fold — and then MEASURED it on the real anchor
relation (`proof_anchor_bind::measure_real_anchor_opening_size` + `fold_feasibility::compaction_at_real_anchor_
shape`, 2026-06-30): **r=κ=128, n≈769, β²≈8.4e14 ⇒ depth=1, ratio=1.0× across q∈{2^58..2^80}**. The recursive
fold is a **base case** — 114k-element, β²=8.4e14 relations are below LaBRADOR's useful threshold; the per-round
fold overhead exceeds the witness. **B does not compact this relation.** (The fold stays a reusable primitive
under `labrador_fold/`.) So §5's recommendation is superseded; Josh (2026-06-30): "shrink openings at the
source."

## 1. The real cost (pq_vouch.rs:13)

The unified anchor/show witness opened κ times is:

```
s1 = [ <show witness> | w_bits[255] | w_ring | e_null | ltc_diff[255] | ltc_borrow[255] | e_bits[2k≈38] ]
```

The anchor binds `w_bits` (lattice, in `t_A`) ↔ `w` (EC, in `C_r`) via κ binary rounds, opening `z1_j = y1_j +
c_j·s1` (the FULL `s1`) each round. But the **EC reconstruction** `A_j = Σ_i τ0(z1_j[bit_idx_i])·g_i + …`
reads ONLY `w_bits`. Everything else in `s1` rides along κ times for nothing the EC side checks:

- **Range-proof witness** (`ltc_diff[255] + ltc_borrow[255] + e_bits[38] ≈ 548`): proves the STATIC facts
  `w < r` (`proof_ltconst` borrow circuit) and the nullifier range. Not in any EC equation.
- **Show witness** (`<show witness>`, `w_ring`, `e_null`): the LNP22 show + nullifier values. Not in the EC
  equation either — but `w_bits` is *committed inside the show's `t_A`*, which is the §3 obstacle.

## 2. Construction X (conservative, clearly sound): move the range witness to a one-time commitment

Commit the range-proof coordinates in their OWN ABDLOP `t_R`, OUT of the per-round-opened `t_A`:

- `t_A` = `ABDLOP([show | w_bits | w_ring | e_null])` — the per-round-opened part (the anchor + EC binding
  read `w_bits` from here, unchanged).
- `t_R` = `ABDLOP([ltc_diff | ltc_borrow | e_bits])` — opened ONCE.
- **One range proof** (`proof_ltconst`/`proof_range` borrow + binariness relations, the existing single
  aggregated `proof_relation` garbage proof) over the JOINT `(w_bits ∈ t_A, ltc_diff‖ltc_borrow ∈ t_R)` +
  `(e_null ∈ t_A, e_bits ∈ t_R)`. The borrow relation `d_k = MAX_k − V_k − c_{k−1} + 2c_k` is affine given
  `V_k` (t_A) and `d_k,c_k` (t_R); `proof_relation` already spans a multi-commitment witness.

Per-round opening: `891 → ~343` (≈**2.6×**). `t_R` (548) + its proof sent once. **This is NOT option D** —
`w_bits` stays in the show's `t_A` (the §3 binding is untouched); only the non-load-bearing range witness moves.

## 3. Construction Y (bigger, reframes option D — GATE THIS): small `w_bits` commitment + one-time equality

`ANCHOR_COMPACTION_DESIGN §3` REJECTED option D ("commit just `w_bits`, not the full `s1`") as *circular*:
"binding `w_bits` to the show's `t_A` requires opening `t_A`." **The reframing:** that opening is needed
ONCE (a cross-commitment equality), not per round.

- `t_W = ABDLOP(w_bits[255])` — a SMALL anchor-only commitment, opened κ times (the EC binding + the
  per-round SIS relation `A1·z1_j + A2·z2_j = w_{c,j} + c_j·t_W`).
- **One equality proof** `t_W.w_bits == t_A.w_bits` (a linear relation over the joint `(t_W, t_A)` witness;
  one `proof_relation`, opening `t_A` ONCE) ties the small anchor commitment to the show's `t_A`.
- The show's `t_A` (891) is then opened only by the show + this one equality — NOT by the κ anchor rounds.

Per-round opening: `891 → 255` (≈**3.5×**). The cross-domain chain `C_r ↔ t_W ↔ t_A.w_bits` holds: the
anchor's 2⁻ᵏ binds `t_W`; the one-time equality binds `t_W` to the show's `t_A`. **Open soundness question
for the gate:** does the one-time equality fully preserve what the per-round `t_A` opening proved? The original
rejection implies opening `t_A` per round was load-bearing — verify the equality is not (i.e., the SIS binding
of `t_W` + one equality = the SIS binding of `t_A`'s `w_bits` per round). If the gate finds the per-round
`t_A` opening IS load-bearing beyond `w_bits`, Y collapses to X.

## 4. Size (d=1, κ=128)

| | per-round opening | one-time | κ-openings (ring elems) | vs current |
|---|---|---|---|---|
| current | 891 + |s2| | — | ≈ 98k | 1× |
| **X** (move range witness) | ~343 + |s2| | t_R 548 + range proof | ≈ 44k + 548 | ≈ 2.6× |
| **Y** (small t_W + equality) | 255 + |s2| | t_A once + equality | ≈ 33k + 891 | ≈ 3.5× |

Composes with the orthogonal natural-bit-width serialization (~3.7×, independent) toward the few-MB target the
fold could not reach. (`w_bits × κ` is the EC binding's irreducible cost without reshaping `C_r` — option A,
shown infeasible in §5's shortness-wall analysis.)

## 5. Plan (design-first; gate Y's soundness BEFORE building)

1. **Codex DESIGN-review of Y** (`--base` this commit) — the equality-reframes-D claim is the crux. If it
   holds, build Y; if not, build X (clearly sound, still ≈2.6×).
2. **Cross-commitment relation proof (the real foundation, not just an API tweak).** AUDIT (2026-06-30):
   `proof_relation` proves an affine-quadratic relation over a SINGLE ABDLOP `t_A = A1·s1 + A2·s2` — it does
   NOT span two commitments. So both X (borrow relation over `w_bits∈t_A` + `range∈t_R`) and Y (equality
   `t_W.w_bits == t_A.w_bits`) need a relation/opening that binds TWO commitments with DIFFERENT opening
   schedules (`t_A` per-round, `t_R`/`t_W` once). **Precedent: `bind.rs`** already proves a CROSS-domain
   same-value binding (lattice `W_j` ↔ EC `T_EC_j` commit the same `w`) — its same-value technique is the
   template for Y's lattice↔lattice equality (`t_W ↔ t_A.w_bits`, likely simpler since both are proof-ring).
   X's cross-commitment AFFINE borrow relation is the harder variant. This is the soundness-critical core of
   the build — design-first + DESIGN-review it (do not treat as a mechanical split). Keep the single-commitment
   `proof_relation` path for the LNP22 show.
3. **`proof_anchor_bind` + `pq_vouch` restructure** — the chosen construction; update `prove_full`/`verify_full`
   + `AnchorBindProof`/`…Full` (drop the moved coords from `z1`); the equality proof for Y.
4. **Integration** — `live_full_width_anchor_bind` at the new layout + a `measure_*` re-run confirming the
   reduction; rule #27 smoke (the real 255-bit `w<r`) + tamper/forgery rejections.
5. **Wire natural-bit-width serialization** (orthogonal ~3.7×) for the final vouch-size number.
