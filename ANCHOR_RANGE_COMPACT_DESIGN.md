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
   schedules (`t_A` per-round, `t_R`/`t_W` once). **The right primitive is a SINGLE-ROUND `proof_relation`
   generalized to a stacked two-commitment witness** (block `[A1 0; 0 A1_W]`, one ring challenge `c`, the
   garbage-technique degree-2 identity) — see §6 obligation 1. **`bind.rs` is the WRONG template** (it is
   κ-round binary because its EC side is `τ0`-limited; a κ-round equality would re-open `t_A` κ times and
   defeat Y). X's cross-commitment AFFINE borrow relation is the same two-commitment `proof_relation`, just a
   bigger constraint set (the borrow chain over `w_bits∈t_A`, `diff/borrow∈t_R`). This generalized
   `proof_relation` is the soundness-critical core of the build — design-first + DESIGN-review it. Keep the
   single-commitment `proof_relation` path for the LNP22 show.
3. **`proof_anchor_bind` + `pq_vouch` restructure** — the chosen construction; update `prove_full`/`verify_full`
   + `AnchorBindProof`/`…Full` (drop the moved coords from `z1`); the equality proof for Y.
4. **Integration** — `live_full_width_anchor_bind` at the new layout + a `measure_*` re-run confirming the
   reduction; rule #27 smoke (the real 255-bit `w<r`) + tamper/forgery rejections.
5. **Wire natural-bit-width serialization** (orthogonal ~3.7×) for the final vouch-size number.

## 6. Y soundness analysis — does the one-time equality overcome option D? (2026-06-30, for DESIGN-review)

Grounded in the ACTUAL bind (`proof_anchor_bind.rs::prove`/`verify`). Per round `j`, with binary `c_j`:
the prover sends `z1_j = y1_j + c_j·s1`, `z2_j = y2_j + c_j·s2`, `z_{r,j}`; the verifier reconstructs and
FS-checks BOTH

- **(lattice)** `A1·z1_j + A2·z2_j − c_j·t_A = w_{c,j}` — binds `z1_j` (hence `s1`) to `t_A`, and
- **(EC)** `ec_digit_comb(τ0(z1_j[bit_idx])) + z_{r,j}·h − c_j·C_r = A_j` — binds `τ0(z1_j[bit_idx])` to `C_r`.

The **same `z1_j`** sits in both, so `t_A`'s value bits = `C_r`'s `w` (`2^−κ` over the κ binary rounds). That
simultaneity — NOT the full-`s1` opening per se — is the cross-domain binding.

**Construction Y replays the simultaneity on `t_W`:** `z1_j = y1_j + c_j·w_bits` (the `t_W` witness, 255);
verifier checks (lattice) `A1'·z1_j + A2'·z2_j − c_j·t_W = w_{c,j}` and the SAME (EC) check. The same `z1_j`
binds `t_W`'s `w_bits` to `C_r` (`2^−κ`). A one-time equality `t_W.w_bits == t_A.w_bits` then gives:

```
   (κ-round bind on t_W)   t_W.w_bits = C_r.w
   (one-time equality)     t_W.w_bits = t_A.w_bits          ⟹   t_A.w_bits = C_r.w.
```

— the SAME end binding as the current scheme, with the per-round opening on the small `t_W` (255) not the
unified `t_A` (891).

**Why option D's "circular" rejection does not bite.** D ("commit just `w_bits`") was rejected because
"binding `w_bits` to the show's `t_A` requires opening `t_A` (the full `s1`)." True — but that opening is the
ONE-TIME equality, not a per-round cost: (i) the equality opens `t_A` once; (ii) the show ALREADY opens `t_A`
for its own relations, so `t_A`'s per-round-in-the-anchor opening was *redundant* with the show; (iii) the
anchor needs only `w_bits` (the EC reads `bit_idx` alone) — the rest of `s1` is the show's obligation, proven
by the show, untouched by Y. So the per-round `t_A` opening is not load-bearing for the anchor beyond `w_bits`;
moving it to `t_W` + a one-time equality loses nothing the anchor proved.

**Residual obligations the gate + the build must discharge (this is "faithful-core, not done"):**
1. **The equality MUST be a SINGLE-ROUND `proof_relation` (NOT `bind.rs`'s κ-round technique) — this is the
   crux of why Y beats D.** `bind.rs`'s same-value is κ binary rounds *because* its EC side reads only `τ0`
   (the `[−8,8]` constant coeff): the cross-domain shortness wall forces small (binary) challenges + parallel
   repetition for `2^−κ`. **Y's equality is lattice↔lattice** (`t_W.w_bits == t_A`'s `w_bits` sub-vector, both
   proof-ring) — NO `τ0` bottleneck — so it is the LNP22 affine-relation proof (`proof_relation`: ONE
   norm-bounded ring challenge `c`, soundness `≤2/|C|` via the degree-2-in-`c` identity), generalized to a
   JOINT witness over the two commitments. **If it were built κ-round (the `bind.rs` reflex), it would re-open
   `t_A` κ times and Y would save nothing — option D's exact trap.** Single-round ⇒ `t_A` opened ONCE ⇒ Y wins.
   Foundation: extend `proof_relation` from one ABDLOP commitment to a stacked `(t_A, t_W)` witness (block
   `[A1 0; 0 A1_W]`), affine constraint `w_bits − s1[value_idx] = 0`. FS-bind the joint proof into the record.
5. **ZK COMPOSITION — the equality must be AGGREGATED into the show's ONE garbage proof, not a separate proof
   (Codex gate P1, 2026-06-30).** `AGGREGATED_SHOW_DESIGN` §C-iv: two LNP22 relation proofs that SHARE a
   commitment's `(s2, b)` masking leak via the difference of their garbage commitments. A standalone equality
   `proof_relation` over `t_A` would reintroduce that leak. `proof_ltconst` already aggregates ALL its
   borrow/binariness relations into ONE garbage proof — so the equality (Y) / the cross-commitment borrow
   relation (X) must be ADDED to that single aggregated relation set over the stacked `(t_A, t_W/t_R)` witness,
   masked once. Equivalently: there is ONE garbage proof for the whole vouch spanning all commitments; the
   new cross-commitment constraints are extra rows in it, not a second proof. (If a separate proof is
   unavoidable, it needs a proven independent-masking construction — strictly harder; prefer aggregation.)
   This makes the stacked-witness `proof_relation` (obligation 1) not just a foundation but THE composition
   point: the show + range + equality are one masked relation over the block-diagonal commitment.
2. **`t_W` security parity** — `t_W = ABDLOP(w_bits)` must be Module-SIS-binding at the same λ as `t_A` (size
   its rank/modulus; the openings are SHORTER so this is easier, not harder).
3. **The show still fully binds `s1`** (incl. `w_bits`) in `t_A` — unchanged; Y adds the equality, removes
   nothing from the show.
4. **No FS-malleability** — the anchor's `fs_rounds` hashes `t_A` today; under Y it must hash `t_W` (the
   per-round commitment) AND the equality transcript, so a prover can't swap `t_W`/`t_A` post-hoc.

**Verdict (pending gate):** Y is sound + leak-free under ALL of (1)–(5) — the equality opens `t_A` once
(single-round, obligation 1), so option D's rejection conflated a one-time equality with a per-round opening;
and obligation 5 keeps it leak-free by aggregating into the show's one garbage proof. The build is BLOCKED on
all five; none is optional. If the gate disputes (1) — e.g. the lattice↔lattice same-value needs the κ-round
structure itself, not a single PoK — Y collapses to **X** (≈2.6×, which needs no equality, only the
cross-commitment borrow relation of §5.2, but still under obligation 5's aggregation requirement). Build the chosen one; do not ship either as "done" until its same-value/cross-
commitment proof is itself gate-clean.
