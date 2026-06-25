# PQ_VOUCH_WIRING_DESIGN — wiring the LNP22 credential show into the C3 BlindedVouch

**Status:** design-first proposal (HYP-352 item 1, the PQ-soundness *wiring*). **Revision 2** —
addresses the 4 P1 + 1 P2 from Codex DESIGN-review R1 (and a concurrent self-audit): the nullifier
`w` is a coefficient-wise-rounded *ring element* (not a single 255-bit coordinate), so the
recomposition is per-coefficient limbs; R3 needs an explicit conjugate-coefficient selector + padding
pins; only true algebraic fold-in preserves the leak-free invariant; the binding web needs the full
checklist. To be re-reviewed clean before any code, per the convention loop and the lesson that this
cross-domain binding is the arc's highest-risk component (ANCHOR_BIND_DESIGN took 13 rounds).

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

One ABDLOP commitment over a single packed `s1`. The show layout
`[θ(v1) | θ(v2) | θ(m) | θ(tag) | z(carry) | slack1 | slack2]` (`proof_show::pack_show_witness`) is
**appended** with the canonical-`w` blocks:

```
s1 = [ θ(v1) | θ(v2) | θ(m) | θ(tag) | z | slack1 | slack2 |   ← unchanged show witness
       w_bits[0..255] | w_ring | e_null[0..NHAT] ]            ← appended (this design)
```

- **`w_bits[0..255]`** — the **canonical source of truth**: 255 coordinates, each a *constant* poly
  whose `τ0 = bit_i ∈ {0,1}` (all other coeffs pinned 0 by R1). Exactly what `proof_anchor_bind`
  consumes (`bit_idx = w_bits_off .. +255`). LSB-first; `w = Σ_i 2^i·bit_i`.
- **`w_ring`** — the nullifier's identity ring element. Its coefficients hold `w` as `L = ⌈255/B⌉`
  **B-bit limbs in the low positions, zero above** (`B = 50` ⇒ each limb `< 2^50 < q̂`, ample no-wrap
  headroom; `L = 6`): `w_ring.coeff[k] = Σ_{j<B} 2^j·bit_{Bk+j}` for `k<L`, `w_ring.coeff[k] = 0` for
  `k ≥ L`. (`Bk+j ≥ 255` ⇒ the bit is 0, so the top limb is partial — fine.) This is the form
  `nullifier_lwr` consumes (`w_blk = w_ring_off`); the nullifier rounds it coefficient-wise.
- **`e_null[0..NHAT]`** — the nullifier remainder ring element `e` (`e_blk = e_null_off`), part of the
  nullifier sub-proof's witness; `0 ≤ e.coeff[i] < Δ` (range-proven, `proof_range`, already built).

All appended blocks are committed in the SAME `t_A` as the show witness, so every sub-proof's linear
opening binds them under one M-SIS commitment.

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

**(R2) `w_ring` = limb-pack(`w_bits`) — per-coefficient, no wrap.** For each `k < L`:
`coeff_k(w_ring) − Σ_{j<B} 2^j·τ0(w_bits[Bk+j]) = 0`, a const-coeff relation
`const_coeff(conj(X^k)·w_ring − Σ_j 2^j·w_bits[Bk+j]) = 0`. Each limb sum `< 2^B = 2^50 < q̂` so the
equality is over the integers, **not** mod q̂ (the P1/Q3 fix — limbs are bounded, no huge `2^254`
weight ever appears). For each `k ≥ L`: `coeff_k(w_ring) = 0` (padding pin), AND `coeff_j(w_ring)=0`
for the non-LSB coefficient positions of each used limb slot if any (here each limb occupies one
coefficient, so just the `k≥L` pins). Together: `w_ring` is exactly the limb-packing of `w_bits`,
fully pinned. (`B=50, L=6` ⇒ 6 limb relations + `NHAT−6 = 58` zero pins.)

**(R3) `m = repack(w_bits)` — explicit selector + padding (the P1/Q4 fix).** `m`'s `M_MSG=2`
`SepRingElem` are `θ`-embedded; `θ` (`proof_subring::embed`) is decimation: `coeff_v(θ(m_b)[i]) =
coeff_{k̂·v + i}(m_b)`, and `m_b`'s coefficients are the message bits. For each `w`-bit `i<255` at SEP
position `(b, c) = (i / 256, i % 256)` mapping (via decimation `i' = c`, `i'' = k̂·v+i_sub`) to
`s1` element `θ(m_b)[i_sub]` coefficient `v`: the relation
`const_coeff(conj(X^v)·θ(m_b)[i_sub]) − τ0(w_bits[i]) = 0`. **Plus padding:** every SEP message
coefficient NOT carrying a `w`-bit (the `M_MSG·256·k̂ − 255` unused slots) is pinned `= 0`
(`const_coeff(conj(X^v)·θ(m_b)[i_sub]) = 0`). The exact `pos(i)` map is `proof_subring::embed`'s
decimation — to be transcribed into a table + an off-by-one/wrong-position regression test (a permuted
map must reject). This is what makes "the credential signed *this* `w`."

**(R4) `w` canonical (`< Fr::MODULUS`).** `proof_ltconst` (the `< Fr::MODULUS` borrow-subtraction
bit-gadget, already built for the anchor) over `w_bits` — closes the non-canonical malleability
(LNP22_SHOW R8 P1: two bit-strings ≡ same `Fr` ⇒ nullifier/credential collision).

**Consistency web:** `w_bits` —R1→ binary; —R4→ canonical; —anchor→ `C_r` (EC, group order, no
limbs); —R3→ `m` (SEP credential's signed message); —R2→ `w_ring` (nullifier). The BBS half opens the
same `C_r`. So one `w_bits` ⇒ one `w` across all four forms.

---

## 4. The composed PQ vouch

```rust
pub struct PqBlindedVouch {
    pub bbs:    BoundPresentation,             // BBS cred on w, opens C_r           (unchanged)
    pub show:   ShowAggProof,                  // SEP cred possession on m + R1–R4 folded in
    pub anchor: AnchorBindProof,               // w_bits[0..255] ↔ C_r
    pub null:   nullifier_lwr::NullifierProof, // N = round(a_epoch·w_ring), e in-range
    pub commitment: AbdlopCommitment,          // the shared (t_A, t_B)
}
```

R1–R4 live **inside `show.agg`** (folded families/linear terms — no separate objects, no extra
garbage commitment). The anchor + nullifier are the open items of §6 (must also fold in, or carry an
explicit joint-ZK argument).

**`prove`** (member): pack the unified `s1` (§2) from the SEP signature + `w`; one `commit_witness`;
`present_bound` (BBS, draws `r`, forms `C_r`); `prove_show_agg` with R1–R4 folded; `prove`(anchor) over
`bit_idx = w_bits` range, same `(t_A,s1,s2,C_r,r)`; `prove_nullifier` over `w_blk=w_ring`,
`e_blk=e_null`. All share `t_A`, `t_B`, `s2`, `C_r`.

**`verify`** — AND-verify + the FULL binding web (the P2/Q5 fix). All must hold:
1. `verify_bound` (BBS) ∧ `verify_show_agg` (incl. R1–R4) ∧ `verify`(anchor) ∧ `verify_nullifier`.
2. **Same commitment object:** every sub-proof references the SAME `commitment.t_A` AND `t_B` (not just
   equal `t_A` — the same `(t_A,t_B)` pair; the show's garbage rides `t_B`).
3. **Same anchor:** `bbs.c_r == anchor.c_r`, and the BBS-opened `C_r` is the anchor's `C_r`.
4. **Same ABDLOP params** (`seed`, `d,m1,m2,ℓ`) across all sub-proofs; **same fixed layout offsets**
   (`w_bits_off`, `w_ring_off`, `e_null_off`, the show blocks) — offsets are public constants derived
   from `vk`, re-checked, never trusted from the proof.
5. **Same context:** issuer `vk`, `epoch` ⇒ `a_epoch = epoch_base(epoch)`, the posted nullifier `N`,
   and the FS transcript domain separators are identical inputs to every sub-proof.
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
- **Anonymity.** The show is statistical-ZK with ONE garbage commitment (§C-iv fix). IF R1–R4 + anchor
  + nullifier are all folded into that one masked relation (§6), no additional garbage is revealed ⇒
  no new leak. `w, w_bits, m, t, v, r` never revealed. Issuer-hiding is the HYP-324 epoch-key layer
  (out of scope; core verifies under public `vk`).

---

## 6. The leak-free composition — fold-in ONLY (the P1/Q2 fix)

R1 confirmed the §C-iv hazard precisely: *separate masked Σ-protocols sharing one `t_B`/`s2` but
committing their own garbage leak `s1`'s covariance through the garbage difference.* The **only**
structure that preserves the proven one-garbage-commitment / statistical-ZK property is **true
algebraic fold-in**: R1–R4 **and** the anchor's per-round relations **and** the nullifier's relation
are all expressed as terms of the **single** aggregated masked quadratic (`agg_show_relation`'s
`FQuadForm` families + linear terms), verified through the one `(t0,t1)`.

- **R1–R4:** already const-coeff/linear families — direct fold-in (the existing mechanism). ✔ tractable.
- **Anchor + nullifier:** currently standalone Σ-protocols. They must be **refactored to EMIT fold-in
  terms** (their relation as `FQuadForm` contributions over the shared `s1`) rather than commit their
  own garbage. This is the real build cost of this issue. The anchor's κ binary-challenge structure
  and the nullifier's `a_epoch·z_w − z_e − c·NΔ = g0` relation must be re-cast as families/linear
  terms of the aggregated relation, or — if a clean fold-in is infeasible for the κ-round anchor — a
  separate **explicit joint-simulation ZK proof** (independent masks, no shared raw garbage) with a
  statistical-ZK test. **Standalone-masked sharing `t_B` is rejected.**

**DESIGN-review Q1 (carry-over):** confirm the anchor's κ-round binary-challenge protocol can be
folded into the single masked quadratic (it uses a different challenge structure than the show's
self-conjugate `c`); if not, specify the joint-simulation argument + its statistical-ZK test. This is
the highest-uncertainty remaining point.

---

## 7. DESIGN-review status

**Resolved in R2 (this revision):**
- ~~Q3~~ R2 no-wrap: per-coefficient B-bit limbs (`B=50<log₂q̂`), integer (not mod-q̂) equalities; no
  `2^254` weight. No public limb reductions (all committed) ⇒ no `w` leak.
- ~~Q4~~ R3 selector: explicit conjugate const-coeff extraction over the `θ`-decimation map + padding
  pins on all unused message coeffs + a wrong-position regression test.
- ~~Q1~~ one-`w`: w_bits canonical source; all forms proven-derived; padding/unused coeffs pinned
  (R2 `k≥L` zeros, R3 unused-slot zeros).
- ~~Q2~~ fold-in only; standalone-masked rejected (§6).
- ~~Q5~~ binding web: full verify checklist (§4: same `t_A`+`t_B`, params, offsets, `vk`, `a_epoch`,
  `N`, codec version) + the headroom note below.

**Still open (gate before code):**
- **Q1′ (§6):** can the κ-round anchor fold into the single masked quadratic, or does it need a joint-
  simulation ZK proof? (highest uncertainty.)
- **Q4′:** finalized norm/headroom — `s1` grows by `255 + 1 + NHAT` coords; confirm M-SIS binding +
  the `B²<q̂` `norm_bounds_provable` guard still hold at the show modulus (may need HYP-330 headroom).
- **Q-θ:** verify the exact `proof_subring::embed` decimation indices for the R3 `pos(i)` table
  against the code before coding (a wrong map silently binds the wrong bits).

---

## 8. Build order (after re-review clean)

0. **Resolve Q1′/Q4′/Q-θ** in review; pin the anchor fold-in (or joint-sim) + the `pos(i)` table.
1. **Packing** — `pack_pq_vouch_witness` (append `w_bits`/`w_ring`/`e_null`); canonical LSB-first
   `w→bits→limbs` encoder; offsets + length guards (Codex P2 discipline).
2. **R2** (the delicate one) — per-coefficient limb const-coeff family; standalone test (known `w`
   recomposes; wrong `w_ring` rejects; no wrap at `w=r−1`; padding pin rejects nonzero high coeff).
3. **R3** — conjugate-selector family over the `θ` table + padding pins; test (`m`↔`w_bits` honest
   binds; mismatched `m` rejects; permuted `pos` rejects).
4. **Fold R1–R4 into `agg_show_relation`**; then the anchor/nullifier fold-in (or joint-sim) per Q1′.
5. **Compose `PqBlindedVouch::{prove,verify}`** + the §4 binding web; new `pq_vouch.rs` (keep
   `vouch.rs` as the classical foundation until HYP-343 retires it).
6. **Tests (rule 27):** integration — real SEP + real BBS credential, full
   prove→encode(codec v2)→decode→verify on one `w`; adversarial — wrong `w` in `C_r` vs `m` (R3),
   tampered `w_ring` (R2), non-canonical `w` (R4), padding violation, double-show same `N`, replay;
   **statistical-ZK test** on the composed transcript (§6). Each chunk: Codex gpt-5.5/high gate.
7. **Codec v2** — append `show`/`anchor`/`null`/`commitment` under a bumped `VOUCH_CODEC_VERSION`.

σ/B/c_256 stay PROVISIONAL → HYP-330 (calibration manifest filed there). The vouch stays behind
`experimental-unaudited` until params land + HYP-343 wires it into `protocol_core`.

---

## 9. Out of scope (the remaining HYP-352 sections, tracked separately)

- **Blind issuance** (Fig 7.1 `OblSign`) — member obtains the SEP credential on `m=bits(w)` without
  the coalition learning `w`. Own design-first pass; PQ blind sigs research-adjacent
  (`reference_pq_blind_sig_landscape`). The show here assumes an already-issued credential.
- **HYP-343** trait reshape — `PqBlindedVouch` behind `protocol_core::{VouchIssuer,VouchVerifier}`,
  retire `StubVouchScheme`. Gated on this wiring + issuance + params.
- **HYP-330** — external audit calibrates the provisional constants (manifest filed on HYP-330); the
  `experimental-unaudited` gate drops only after.
