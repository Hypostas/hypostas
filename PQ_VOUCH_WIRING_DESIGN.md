# PQ_VOUCH_WIRING_DESIGN — wiring the LNP22 credential show into the C3 BlindedVouch

**Status:** design-first proposal (HYP-352 item 1, the PQ-soundness *wiring*). **Revision 3.**
R2 addressed the 4 P1 + 1 P2 from Codex DESIGN-review R1 (nullifier `w` is a coefficient-wise-rounded
*ring element*, not a 255-bit coordinate, so recomposition is per-coefficient limbs; R3 needs an
explicit conjugate-coefficient selector + padding pins; leak-free composition; the full binding web).
**Revision 3 resolves the two carried-open points:** Q1′ — the anchor is cross-group, so it is a
*separate* Schnorr proof (not a fold-in), leak-free in composition by independent masking, **NOT** a
§C-iv shared-garbage case (§6); and Q-θ — the exact `proof_subring::embed` decimation map for R3,
verified against the code. **Revision 4** addresses 3 P1 from the inline `codex exec review` gate: the
R4 `< Fr::MODULUS` borrow auxiliaries (`ltc_borrow`) and the nullifier `e`-range bits (`e_bits`) are
now committed in `s1` (they had nowhere to live), and the standalone `NullifierProof` is removed — the
nullifier (rounding + `e`-range) folds into the show as R5. To be re-reviewed clean before any code,
per the lesson that this cross-domain binding is the arc's highest-risk component (ANCHOR_BIND_DESIGN
took 13 rounds).

**Scope.** Turn the *classically*-sound foundation `BlindedVouch` (commitment-opening `bind`,
PQ-forgeable) into a *post-quantum*-sound vouch by consuming the built LNP22 credential show
(`proof_show::prove_show_agg`/`verify_show_agg`) — ZK proof of possession of an issuer-signed SEP
credential — in place of `bind`. Excludes blind issuance (Fig 7.1), HYP-343 trait reshape, σ-calibration
(HYP-330). Includes the cross-representation binding tying the show, anchor, and PQ nullifier to one `w`.

---

## 1. What exists (the inputs — all built + gate-clean on `iris/hyp-342-bbs-half`)

| Piece | Entry | Proves | `w`-form it reads |
|---|---|---|---|
| BBS bound presentation | `bridge::present_bound`/`verify_bound` | a BBS credential certifies the `w` in `C_r = w·g + r·h` | EC scalar `w` (in `C_r`) |
| LNP22 credential show | `proof_show::prove_show_agg`/`verify_show_agg` | possession of a SEP signature on a binary message `m` (+ exact ℓ₂ norms + tag/message binariness), as ONE masked quadratic over a committed `s1`, ONE garbage commitment `(t0,t1)` | SEP message `m` = `M_MSG=2` binary `SepRingElem`, `θ`-embedded into `s1` |
| Anchor bind | `proof_anchor_bind::prove`/`verify` | the `ANCHOR_DIGITS=255` bits committed at `s1[bit_idx]` (each `τ0` = a bit) equal `C_r`'s `w`; κ binary-challenge rounds; EC recomposition over the group order (no limbs needed EC-side) | 255 bit-coordinates in `s1` ↔ EC `C_r` |
| PQ nullifier | `nullifier_lwr::prove_nullifier`/`verify_nullifier` | `N = round_Δ(a_epoch · w)` **coefficient-wise** (`n[i]=⌊prod.coeff[i]/Δ⌋`, `Δ=p`), with `e[i]=prod.coeff[i]−n[i]·Δ ∈ [0,Δ)` and `n[i]∈[0,q1)` in-circuit, for the `w` committed at `s1[w_blk]` | one ring element `w_ring` = `s1[w_blk]`, **64 coeffs each `< q̂`** |

**The reconciliation problem (the crux).** `w` appears in FOUR forms — EC scalar (`C_r`), 255 anchor
bit-coordinates, the SEP message `m`, and the nullifier ring element `w_ring`. Nothing yet forces them
equal, and (R1 self-audit) they are *structurally* different: `w_ring`'s coefficients are each `< q̂ ≈
2^57.7`, so `w` cannot be one 255-bit coordinate. **Design: one canonical source — `w_bits[0..255]` —
and every other form is a *derived, in-circuit-proven function* of it.**

---

## 2. The unified witness `s1` and the canonical `w_bits`

One ABDLOP commitment over a single packed `s1`. ⚠️ **The box below is ILLUSTRATIVE** — the actual show
witness order is whatever the **current** `proof_show::pack_show_witness` / aggregated show emits (per
AGGREGATED_SHOW_DESIGN that is `(v1'', v2'', v3'', t', m'_sm)` with per-witness slack folded into those
blocks, NOT the loose `[…|slack1|slack2]` order drawn here). **All offsets — existing AND appended —
MUST be derived from the live `pack_show_witness` layout, never hardcoded from this box; in particular
R3's `m`/`tag` coordinate map (§3) comes from the real packed `m`/`m'_sm` position, else honest proofs
reject or the signed message isn't the one `w_bits` constrains (gate P2).** The canonical-`w` blocks
are appended after whatever that layout is:

```
s1 = [ θ(v1) | θ(v2) | θ(m) | θ(tag) | z | slack1 | slack2 |       ← unchanged show witness
       w_bits[0..255] | w_ring | e_null |                         ← canonical w + nullifier value + remainder (1 ring coord each)
       ltc_borrow[0..255] |                                       ← R4: < Fr::MODULUS borrow-chain auxiliaries
       e_bits[0..NHAT · 2·ceil_log2(Δ)] ]                         ← nullifier: per-coeff e-range bit-decomposition
```

- **`w_bits[0..255]`** — the **canonical source of truth**: 255 coordinates, each a *constant* poly
  whose `τ0 = bit_i ∈ {0,1}` (all other coeffs pinned 0 by R1). Exactly what `proof_anchor_bind`
  consumes (`bit_idx = w_bits_off .. +255`). LSB-first; `w = Σ_i 2^i·bit_i`.
- **`w_ring`** — the nullifier's identity ring element. Its coefficients hold `w` as **small `B=4`-bit
  limbs, one per coefficient across all `L = ⌈255/4⌉ = 64 = NHAT` coefficients**. `B` MUST be small so
  each limb `≤ 2^4−1 = 15` and `w_ring` stays a *short* M-SIS witness: a 50-bit limb would give
  coeff² ≈ `2^100 ≫ q̂` and blow the `B²<q̂` exact-ℓ2 norm / no-wrap guard (gate P1).
  `w_ring.coeff[k] = Σ_{j : 4k+j < 255} 2^j·bit_{4k+j}` for `k < 64` (the **top limb `k=63` is partial**
  — bits 252..254, `j<3`; never index `w_bits` past 254). `‖w_ring‖² ≤ 64·15² ≈ 2^13.8`, negligible vs
  `q̂`. This is the form `nullifier_lwr` consumes; rounds coeff-wise.
- **`e_null`** — **ONE** ring coordinate: the nullifier remainder ring element `e`
  (`a_epoch·w_ring = N·Δ + e`), whose `NHAT` coefficients are the per-coefficient remainders. `e_bits`
  (below) range-decomposes each of those `NHAT` coefficients; R5's recomposition ties them back to this
  same `e`. (Not `NHAT` separate coordinates — one ring element with `NHAT` coeffs.)
- **`ltc_borrow[0..255]`** — **(P1 fix #1)** the auxiliary borrow/prefix bits of the `proof_ltconst`
  `< Fr::MODULUS` gadget (one per `w`-bit; borrow-subtraction `MODULUS−1 − w` chain). R4 is otherwise
  *inexpressible* folded — its constraints reference these committed auxiliaries, so canonicality stays
  bound to the same `t_A` as `w_bits`. Boolean (R4 pins them ∈{0,1}).
- **`e_bits[0..NHAT·2·ceil_log2(Δ)]`** — **(P1 fix #2)** the per-coefficient range decomposition of
  `e`. `e∈[0,Δ)` is NOT a linear relation: for each of the `NHAT` coefficients, the two-range
  bit-decomposition (`e[i] = Σ2^j b_{i,j}` AND `(Δ−1)−e[i] = Σ2^j b'_{i,j}`, `Δ=p≈2^18.7` ⇒ ~19 bits
  each ⇒ ~38·NHAT bits) is committed here, with binariness + recomposition as folded families. Without
  these a prover picks `e = prod − N·Δ mod q̂` outside `[0,Δ)` and a wrong `N` passes (gate P1).

All appended blocks are committed in the SAME `t_A` as the show witness, so every sub-proof's linear
opening binds them under one M-SIS commitment. ⚠️ `s1` now grows by `255 + 1 + 1 + 255 + 38·NHAT ≈
255+1+1+255+2432 ≈ 2944` proof-ring coords — the norm/headroom check (Q4′, §7) is now load-bearing,
not a formality; the M-SIS dimensions + `B²<q̂` guard must be re-validated at this size (HYP-330).

---

## 3. The reconciliation proofs (the new code) — every form derived from `w_bits`

All four are **const-coefficient / linear constraints over the one committed `s1`**, expressed as
`AffineConstraint` families and **folded into the aggregated show's one masked quadratic** exactly like
the existing norm/binariness/approx-range families (`agg_show_relation`) — **no new garbage
commitment** (this is the §6 fold-in requirement made concrete). The selector primitive is the
conjugate const-coeff extraction the show already uses: `const_coeff(conj(X^j)·x) = x.coeff[j]`
(`proof_quadratic`/`proof_constraint`).

**(R1) `w_bits` binary + pure-constant.** `aggregated_binariness` over `w_bits[0..255]`: each
`τ0(w_bits[i]) ∈ {0,1}` AND every non-const coefficient = 0 (the family pins all coeffs; the "pure
constant" part matters so `bit_i` is exactly `τ0`, not smuggled into higher coeffs). Reused primitive.

**(R2) `w_ring` = limb-pack(`w_bits`) — per-coefficient, no wrap, SHORT.** For each `k < 64`:
`coeff_k(w_ring) − Σ_{j : 4k+j < 255} 2^j·τ0(w_bits[4k+j]) = 0` (`B=4`-bit limbs; the top limb `k=63`
sums only `j<3`, so `w_bits` is never indexed past 254), a const-coeff relation
`const_coeff(conj(X^k)·w_ring − Σ_j 2^j·w_bits[4k+j]) = 0`. Each limb sum `≤ 15 < q̂`, so the equality
is over the integers, **not** mod q̂ (the Q3 fix), AND `w_ring` stays short (the gate-P1 fix — a 50-bit
limb would blow `B²<q̂`). All `64 = NHAT` coefficients carry a limb (no padding coefficients).
Together: `w_ring` is exactly the 4-bit limb-packing of `w_bits`, fully pinned (64 limb relations, no
zero pins needed).

**(R3) `m = repack(w_bits)` — explicit selector + padding (the P1/Q4 fix; map verified, Q-θ).** `m`'s
`M_MSG=2` `SepRingElem` (256 coeffs each = 512 bit-slots) are `θ`-embedded; `θ`
(`proof_subring::embed`, read + verified) is decimation `θ(m_b)[i].coeff[j] = m_b.coeff[k̂·j + i]` with
`k̂ = 4`, and the centering step is a **no-op for binary `m`** (bits 0/1 < p/2), so
`coeff_j(θ(m_b)[i])` equals the bit directly. Inverting the decimation: SEP coefficient position `c` of
message element `b` lives at `s1` element `θ(m_b)[c mod 4]`, coefficient `c div 4`. So for each `w`-bit
`i < 255` at `(b, c) = (i / 256, i % 256)`:
`const_coeff(conj(X^{c div 4})·θ(m_b)[c mod 4]) − τ0(w_bits[i]) = 0`. **Padding:** the `512 − 255 =
257` SEP message slots not carrying a `w`-bit are pinned `= 0` (same const-coeff form), so `m` is
*exactly* `bits(w)`-then-zeros — no malleable message coefficient. A permuted `pos` map must reject
(off-by-one regression test). This is what makes "the credential signed *this* `w`."

**(R4) `w` canonical (`< Fr::MODULUS`) — with committed auxiliaries (P1 fix #1).** The `proof_ltconst`
borrow-subtraction gadget proves `w < Fr::MODULUS` via the `MODULUS−1 − w` chain with per-bit borrow
auxiliaries `ltc_borrow[0..255]` — **now committed in `s1` (§2)**, so the gadget is expressible folded
and stays bound to the same `t_A` as `w_bits` (was the P1: nowhere to put them). R4 folds as: binariness
on `ltc_borrow` + the per-bit borrow recurrence (const-coeff relations) + the final-borrow `= 0` pin.
Closes the non-canonical malleability (LNP22_SHOW R8 P1: two bit-strings ≡ same `Fr` ⇒ collision).

**(R5) nullifier `N = round_Δ(a_epoch·w_ring)` — folded, with committed e-range (P1 fixes #2/#3).** Two
parts, both folded into the one masked quadratic — **NO standalone `NullifierProof`, NO own garbage**:
- the per-coefficient rounding relation `a_epoch·w_ring − e − N·Δ = 0` (linear over `s1`; `N` is public,
  FS-bound), and
- the per-coefficient `e∈[0,Δ)` range — `e∈[0,Δ)` is NOT linear, so it uses the committed `e_bits`
  (§2): binariness on `e_bits` + the two recompositions `e[i] = Σ2^j b_{i,j}` and `(Δ−1)−e[i] =
  Σ2^j b'_{i,j}` (const-coeff families). The `N[i]∈[0,q1)` range is a plaintext check on public `N`.
`nullifier_lwr` is refactored to EMIT these families rather than commit its own `g0` (the §6 fold-in).

**Consistency web:** `w_bits` —R1→ binary; —R4→ canonical; —anchor→ `C_r` (EC, group order, no
limbs); —R3→ `m` (SEP credential's signed message); —R2→ `w_ring` (nullifier). The BBS half opens the
same `C_r`. So one `w_bits` ⇒ one `w` across all four forms.

---

## 4. The composed PQ vouch

```rust
pub struct PqBlindedVouch {
    pub bbs:    BoundPresentation,    // BBS cred on w, opens C_r                          (unchanged)
    pub show:   ShowAggProof,         // SEP possession on m + R1–R5 (incl. nullifier) folded in
    pub anchor: AnchorBindProof,      // w_bits[0..255] ↔ C_r   (separate cross-group Schnorr proof)
    pub n:      ProofRingElem,        // the posted nullifier N (PUBLIC; verified via R5 inside `show`)
    pub commitment: AbdlopCommitment, // the shared (t_A, t_B)
}
```

R1–**R5** — including the **nullifier** (rounding relation + `e`-range) — live **inside `show.agg`**
(folded families / linear terms over the one garbage commitment; no separate proof object, no own
garbage; P1 fix #3). The **anchor is the one separate proof** (cross-group; §6). There is no
`NullifierProof` type in the vouch — `N` is a public field, FS-bound into the show's transcript and
checked by R5.

**`prove`** (member): pack the unified `s1` (§2) from the SEP signature + `w` (incl. `ltc_borrow` +
`e_bits` auxiliaries); one `commit_witness`; `present_bound` (BBS, draws `r`, forms `C_r`);
`prove_show_agg` with **R1–R5** folded (the refactored `nullifier_lwr` emits its families here);
`prove`(anchor) over `bit_idx = w_bits` range, same `(t_A,s1,s2,C_r,r)`. All share `t_A`, `t_B`, `s2`,
`C_r`. `N` is computed from `(a_epoch, w_ring)` and posted.

**`verify`** — AND-verify + the FULL binding web (the P2/Q5 fix). All must hold:
1. `verify_bound` (BBS) ∧ `verify_show_agg` (incl. R1–**R5** — the nullifier rounding + `e`-range
   folded) ∧ `verify`(anchor). The public `N` is FS-bound into the show transcript and checked by R5;
   the ledger rejects a repeated `N`. (No separate `verify_nullifier`.)
2. **Same commitment object:** every sub-proof references the SAME `commitment.t_A` AND `t_B` (not just
   equal `t_A` — the same `(t_A,t_B)` pair; the show's garbage rides `t_B`).
3. **Same anchor:** `bbs.c_r == anchor.c_r`, and the BBS-opened `C_r` is the anchor's `C_r`.
4. **Same ABDLOP params** (`seed`, `d,m1,m2,ℓ`) across all sub-proofs; **same fixed layout offsets** —
   `w_bits_off`, `w_ring_off`, `e_null_off`, **`ltc_borrow_off`, `e_bits_off`** (the R4/R5 auxiliaries),
   and the show blocks — all public constants derived from `vk`, re-checked, never trusted from the
   proof. (Omitting the auxiliary offsets would let R4/R5 reference wrong coordinates, reopening the
   non-canonical-`w` / wrong-`N` cases.)
5. **Same context:** issuer `vk`, `epoch` ⇒ `a_epoch = epoch_base(epoch)`, the posted nullifier `N`,
   and the FS transcript domain separators are identical inputs to every sub-proof. ⚠️ **The public-`vk`
   verification path is TEST-ONLY** — a public `vk` reveals *which* introducer signed when an epoch has
   >1 introducer. Production wiring MUST go through the HYP-324 issuer-hidden wrapper (shared epoch key
   / committed-key + accumulator), exactly as the LNP22 show design gates it; the core here verifies
   under public `vk` only for tests, never for a live vouch.
6. **Codec version** matches (§8.7).

Returns `N` on success.

---

## 5. Security argument (sketch — harden in review)

Under M-SIS (binding of `t_A`/`t_B`) + SEP unforgeability (M-SIS) + BBS (q-SDH, classical) + DL
(Pedersen `C_r`):

- **PQ membership unforgeability.** `verify_show_agg` ⇒ knowledge of a SEP signature on the committed
  `m` (M-SIS-hard to forge — what `bind` lacked). R3 ⇒ `m` encodes `w_bits`; R2 ⇒ `w_ring` is the same
  bits; R1/R4 ⇒ canonical binary; the anchor ⇒ `w_bits` = `C_r`'s `w`. A forged vouch needs a forged
  SEP credential on the bits of some `w` it can also open in `C_r` — PQ-hard. BBS adds the classical
  leg (C3: either-half-unforgeable ⇒ unforgeable).
- **One-show.** `verify_nullifier` ⇒ `N = round_Δ(a_epoch·w_ring)` with the per-coefficient `e∈[0,Δ)`
  + `n∈[0,q1)` ranges (unique `N` per `(w,epoch)`); R2 ties `w_ring` to the canonical `w`. PQ-hiding
  (ring-LWR), Q6=(ii).
- **Anonymity.** The show is statistical-ZK with ONE garbage commitment (§C-iv fix). R1–R4 + the
  nullifier fold into that one masked relation (no additional garbage revealed). The anchor is a
  separate cross-group Schnorr proof composed leak-free by independent masking (§6), checked by the
  composed-transcript statistical-ZK test. So `w, w_bits, m, t, v, r` are never revealed. Issuer-hiding
  is the HYP-324 epoch-key layer (out of scope; core verifies under public `vk`).

---

## 6. The leak-free composition — resolved (the P1/Q2 fix + Q1′)

The §C-iv hazard is *specific*: separate masked sub-proofs that **each BDLOP-commit their own garbage
into the shared `t_B`/`s2`** leak `s1`'s covariance through the garbage difference (`t1_i − t1_j =
e1_i − e1_j` — the shared `b·s2` cancels, exposing `e1_i − e1_j` which correlates with `s1`). The fix
was ONE garbage commitment. The composition here splits cleanly into two classes, only one of which
touches `t_B`:

**(a) Ring-relation proofs → fold into the ONE masked quadratic.** R1, R2, R3, R4 **and the nullifier
relation** (`a_epoch·w − e − N·Δ = 0` + the `e∈[0,Δ)` range) are all proof-ring relations expressible
as `FQuadForm` families — **a mix of linear** (the rounding equation, the limb / borrow / bit
recompositions) **AND quadratic** (the `b²−b=0` binariness on `w_bits` / `ltc_borrow` / `e_bits`, which
the `e∈[0,Δ)` range and canonicality *depend on* — emitting only linear/affine families would let a
prover put `e` outside `[0,Δ)` and pass a wrong `N`). They fold as terms of the SINGLE aggregated
masked quadratic (`agg_show_relation`), verified through the ONE garbage commitment `(t0,t1)` — the
existing norm / binariness / approx-range mechanism, already proven leak-free (with one garbage
commitment, no inter-proof garbage difference exists). Build cost: extend `agg_show_relation` with the
R1–R4 + nullifier families; refactor `nullifier_lwr` to EMIT its relation as a family rather than
commit its own `g0`.

**(b) The anchor → a separate cross-GROUP Schnorr proof, leak-free by independent masking.** The
anchor's binding `Σ_i 2^i·bit_i·g = C_r`'s `w` is an equation in the BLS12-381 group **G1** — it
cannot be a proof-ring quadratic (different algebraic domain), so it is *irreducibly* a separate
proof. **But it is NOT a §C-iv hazard:** `proof_anchor_bind` is a Schnorr-style Σ-protocol with
**fresh independent masks each round** (`y1_j, y2_j, ρ_r_j`) and **no BDLOP garbage commitment** — it
never touches `t_B`. Composition with the show is HVZK by the standard hybrid/simulation argument:
`s1` is opened by the show once (`z = y + c·s1`) and by the anchor κ times (`z1_j = y1_j + c_j·s1`),
all with independent, rejection-bounded masks; the κ+1 openings are jointly simulatable (FS-fix the
challenges, sample each `z / z1_j` from its mask distribution, solve the announcements from the
verification equations) and statistically `s1`-independent — the masks are unknowns of dimension `m1`,
so the linear system in `s1` is underdetermined. **The §C-iv leak required a shared garbage commitment
with per-sub-proof garbage differences; the anchor has neither.**

**Q1′ resolves favorably:** no exotic joint-simulation re-derivation is needed — standard Σ-protocol
HVZK + the hybrid composition argument suffice, PROVIDED (i) the anchor's masks are fully independent
of the show's and rejection-bounded (current `proof_anchor_bind` does this), and (ii) the anchor
commits no garbage into `t_B` (it does not). The remaining obligation is a **statistical-ZK regression
test on the composed (show + anchor) transcript** — functional tests + the Codex gate are blind to a
ZK leak, so that test is the §6 build gate.

---

## 7. DESIGN-review status

**Resolved in R2 (this revision):**
- ~~Q3~~ R2 no-wrap: per-coefficient small `B=4`-bit limbs (keep `w_ring` short; gate-P1), integer (not mod-q̂) equalities; no
  `2^254` weight. No public limb reductions (all committed) ⇒ no `w` leak.
- ~~Q4~~ R3 selector: explicit conjugate const-coeff extraction over the `θ`-decimation map + padding
  pins on all unused message coeffs + a wrong-position regression test.
- ~~Q1~~ one-`w`: w_bits canonical source; all forms proven-derived; padding/unused coeffs pinned
  (R2 `k≥L` zeros, R3 unused-slot zeros).
- ~~Q2~~ fold-in only; standalone-masked rejected (§6).
- ~~Q5~~ binding web: full verify checklist (§4: same `t_A`+`t_B`, params, offsets, `vk`, `a_epoch`,
  `N`, codec version) + the headroom note below.

**Resolved (R3, this revision):**
- ~~Q1′~~ anchor composition (§6): cross-group ⇒ a SEPARATE Schnorr proof (independent masks, no `t_B`
  garbage) → leak-free by the standard hybrid argument, NOT a §C-iv shared-garbage case. Build
  obligation: the composed-transcript statistical-ZK test.
- ~~Q-θ~~ the `embed` map: decimation `θ(m_b)[i].coeff[j] = m_b.coeff[k̂·j+i]`, `k̂=4`, centering a
  no-op for binary `m` ⇒ bit `c` of message `b` sits at `s1` elem `θ(m_b)[c mod 4]` coeff `c div 4`
  (folded into §3 R3 + the `pos(i)` table).

**Resolved (R4 / v4 — inline `codex exec review` gate):**
- ~~P1 #1~~ R4 canonicality auxiliaries (`ltc_borrow[255]`) now committed in `s1` (§2) — the borrow
  gadget is expressible folded + bound to `t_A`.
- ~~P1 #2~~ nullifier `e`-range: the per-coefficient `e∈[0,Δ)` bit-decomposition (`e_bits`, ~38·NHAT)
  is committed in `s1` + folded as binariness + recomposition families (R5) — not modeled as linear.
- ~~P1 #3~~ standalone `NullifierProof` removed; the nullifier folds into `show` (R5); `N` is a public
  field FS-bound + checked there (no separate proof object, no own garbage).

**Still open (build-time check, not a design gap):**
- **Q4′ (now load-bearing):** `s1` grows by ~`2944` coords (`255 w_bits + 1 w_ring + 1 e_null + 255
  ltc_borrow + 38·NHAT e_bits`). Confirm M-SIS binding + the `B²<q̂` `norm_bounds_provable` guard hold
  at this size + the show modulus — likely needs the de-provisionalized M-SIS dimensions (HYP-330).
  The build surfaces it concretely as a `norm_bounds_provable` assertion; if it fails, the nullifier
  coefficient count / `e`-range packing is the first dial to turn.

---

## 8. Build order (after re-review clean)

0. **Build-time only:** the Q4′ headroom check (§7) + derive the live `pos(i)` table from
   `pack_show_witness` (§2). Q1′/Q-θ are resolved (§6/§7): the anchor stays a **separate** Schnorr
   proof (no fold-in) — the only anchor obligation is the composed-transcript ZK regression gate.
1. **Packing** — `pack_pq_vouch_witness` (append `w_bits` / `w_ring` / `e_null` / `ltc_borrow` /
   `e_bits` — ALL the R4/R5 auxiliaries, else canonicality + the `e`-range have nothing to bind to);
   canonical LSB-first `w→bits→limbs` encoder + the borrow chain + the per-coeff `e`-range
   bit-decomposition; offsets + length guards (Codex P2 discipline).
2. **R2** (the delicate one) — per-coefficient 4-bit-limb const-coeff family (all 64 coeffs, no padding
   coords); standalone test (known `w` recomposes; wrong `w_ring` rejects; no overflow at `w=r−1`; top
   limb `k=63` uses only `j<3`).
3. **R3** — conjugate-selector family over the `θ` table + padding pins; test (`m`↔`w_bits` honest
   binds; mismatched `m` rejects; permuted `pos` rejects).
4. **Fold R1–R4 + the nullifier relation into `agg_show_relation`** (ring relations — extend `families`; refactor `nullifier_lwr` to emit a family, not its own `g0`). Keep the anchor as the separate `proof_anchor_bind` Schnorr proof (independent masks, no `t_B`); add the composed-transcript **statistical-ZK test** (§6) as the leak-freeness gate.
5. **Compose `PqBlindedVouch::{prove,verify}`** + the §4 binding web; new `pq_vouch.rs` (keep
   `vouch.rs` as the classical foundation until HYP-343 retires it).
6. **Tests (rule 27):** integration — real SEP + real BBS credential, full
   prove→encode(codec v2)→decode→verify on one `w`; adversarial — wrong `w` in `C_r` vs `m` (R3),
   tampered `w_ring` (R2), non-canonical `w` (R4), padding violation, double-show same `N`, replay;
   **statistical-ZK test** on the composed transcript (§6). Each chunk: Codex gpt-5.5/high gate.
7. **Codec v2** — append `show`/`anchor`/`null`/`commitment` under a bumped `VOUCH_CODEC_VERSION`.

σ/B/c_256 stay PROVISIONAL → HYP-330 (calibration manifest filed there). The vouch stays behind
`experimental-unaudited` until **ALL THREE** land: (i) HYP-330 params, (ii) HYP-343 trait wiring, AND
(iii) the **HYP-324 issuer-hidden wrapper** — without which a live public-`vk` vouch leaks *which*
introducer signed in a multi-introducer epoch. Dropping the gate before HYP-324 is a release error
(an anonymity break), not a params question — the public-`vk` core is test-only until then.

---

## 9. Out of scope (the remaining HYP-352 sections, tracked separately)

- **Blind issuance** (Fig 7.1 `OblSign`) — member obtains the SEP credential on `m=bits(w)` without
  the coalition learning `w`. Own design-first pass; PQ blind sigs research-adjacent
  (`reference_pq_blind_sig_landscape`). The show here assumes an already-issued credential.
- **HYP-324 issuer-hidden wrapper** — **a release gate, not just out-of-scope.** The public-`vk`
  verification core here is TEST-ONLY; a live vouch under a named `vk` leaks which introducer signed in
  a multi-introducer epoch. The HYP-324 wrapper (shared epoch key / committed-key + accumulator) must
  gate the core before any live wiring. `experimental-unaudited` MUST NOT drop without it.
- **HYP-343** trait reshape — `PqBlindedVouch` behind `protocol_core::{VouchIssuer,VouchVerifier}`,
  retire `StubVouchScheme`. Gated on this wiring + issuance + params.
- **HYP-330** — external audit calibrates the provisional constants (manifest filed on HYP-330). The
  `experimental-unaudited` gate drops only after **all of**: HYP-330 (params) ∧ HYP-324 (issuer hiding)
  ∧ HYP-343 (trait wiring). Missing any one is a release error.
