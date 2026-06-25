# PQ_VOUCH_WIRING_DESIGN — wiring the LNP22 credential show into the C3 BlindedVouch

**Status:** design-first proposal (HYP-352 item 1, the PQ-soundness *wiring*). To be driven through
Codex DESIGN-review until clean **before** any code, per the convention loop and the repeated lesson
that the cross-domain binding is the arc's highest-risk component (ANCHOR_BIND_DESIGN, bind.rs:
"subtle bug = silent deanonymization, invisible to functional tests AND the gate").

**Scope.** This turns the *classically*-sound foundation `BlindedVouch` (which uses a commitment-
opening `bind`, PQ-forgeable) into a *post-quantum*-sound vouch by making it consume the already-built
LNP22 credential show (`proof_show::prove_show_agg` / `verify_show_agg`) — a ZK proof of possession of
an issuer-signed SEP credential — in place of `bind`. It does NOT cover blind issuance (Fig 7.1,
separate), HYP-343 trait reshape, or σ-calibration (HYP-330). It DOES specify the cross-representation
binding that ties the show, the anchor bind, and the PQ nullifier to one member identity `w`.

---

## 1. What exists (the inputs — all built + gate-clean on `iris/hyp-342-bbs-half`)

| Piece | Entry | Proves | `w`-representation it touches |
|---|---|---|---|
| BBS bound presentation | `bridge::present_bound`/`verify_bound` | a BBS credential certifies the `w` in `C_r = w·g + r·h` | EC scalar `w` (in `C_r`) |
| LNP22 credential show | `proof_show::prove_show_agg`/`verify_show_agg` | possession of a SEP signature on a binary message `m` (+ exact ℓ₂ norms + tag/message binariness), as ONE masked quadratic over a committed `s1` | SEP message `m` = `M_MSG=2` binary `SepRingElem` (bits in coeffs) |
| Anchor bind | `proof_anchor_bind::prove`/`verify` (+ `prove_full`) | the `ANCHOR_DIGITS=255` bits committed at `s1[bit_idx]` (each `τ0` = a bit) equal `C_r`'s `w`; κ binary-challenge rounds, cross-ring | 255 bit-coordinates in `s1` ↔ EC `C_r` |
| PQ nullifier | `nullifier_lwr::prove_nullifier`/`verify_nullifier` | `N = round_Δ(a_epoch · w)` for the `w` committed at `s1[w_blk]`, `e = a_epoch·w − N·Δ ∈ [0,Δ)` in-circuit | one ring element `s1[w_blk]` (value `w`) |

**Key observation.** The anchor bind and the nullifier were *built to share the show's commitment* —
both take an `AbdlopParams` + `t_a` + `s1` + `s2` and an index into `s1` (`bit_idx` / `w_blk`,
`e_blk`). So the composition is "prove all four over ONE ABDLOP commitment of one `s1`," not "glue
four independent proofs." What is missing is the **representation reconciliation**: the show signs `m`
(dense bits), the anchor reads 255 `τ0`-coordinates, the nullifier reads one ring element. These are
three different encodings of the same `w` and nothing yet forces them equal.

---

## 2. The unified witness `s1`

One ABDLOP commitment over a single packed `s1`. Existing show layout is
`[θ(v1) | θ(v2) | θ(m) | θ(tag) | z(carry) | slack1 | slack2]`
(`proof_show::pack_show_witness`). We **append** three canonical-`w` blocks:

```
s1 = [ θ(v1) | θ(v2) | θ(m) | θ(tag) | z | slack1 | slack2 |   ← unchanged show witness
       w_bits[0..255] | w_val | e_null ]                       ← appended (this design)
```

- **`w_bits[0..255]`** — 255 proof-ring coordinates, each the *constant* poly `bit_i` (so
  `τ0(w_bits[i]) = bit_i ∈ {0,1}`, all other coeffs 0). This is exactly the form
  `proof_anchor_bind` consumes (`bit_idx = [w_bits_off .. w_bits_off+255]`).
- **`w_val`** — one proof-ring coordinate holding the value `w = Σ_i 2^i·bit_i` (canonical `< r`),
  the form `nullifier_lwr` consumes (`w_blk = w_val_off`).
- **`e_null`** — the nullifier remainder `e = a_epoch·w − N·Δ` (`e_blk = e_null_off`), already part of
  the nullifier sub-proof's witness.

`w_bits`, `w_val`, `e_null` are committed in the SAME `t_A` as the show witness, so every sub-proof's
linear opening (`z1 = y1 + c·s1`) binds them under the one M-SIS commitment. `mask_sigma` for the
appended blocks is the SEP-scale σ already used by the show (they ride the same opening).

---

## 3. The reconciliation proofs (the new code)

Four constraints force the three encodings to be one `w`. All are **linear or binariness constraints
over the single committed `s1`**, providable with the existing machinery (`proof_linrel` for linear
ring relations, `proof_constraint::aggregated_binariness` for `∈{0,1}`, folded into the aggregated
show's `FQuadForm` exactly like the existing norm/binariness families — so they cost **no new garbage
commitment**, they extend `agg_show_relation`'s `families`).

**(R1) `w_bits` are binary.** `aggregated_binariness` over `w_bits[0..255]` (reuse). Forces each
`τ0(w_bits[i]) ∈ {0,1}` and the non-const coeffs to 0 (the family already pins all coeffs).

**(R2) `w_val = Σ_i 2^i·w_bits[i]` (recomposition).** One linear ring relation:
`w_val − Σ_i 2^i·w_bits[i] = 0`. ⚠️ **Multi-limb caveat (ANCHOR_BIND R3 self-catch):** `2^254`
overflows a single `q̂≈2^57.7` coefficient, so this is NOT one coefficient relation. Recompose in
`L = ⌈255/B⌉` limbs (`B = ⌊log₂ q̂⌋ − slack ≈ 50`): `w_val = Σ_ℓ 2^{ℓB}·limb_ℓ`,
`limb_ℓ = Σ_{j<B} 2^j·w_bits[ℓB+j]`, with a carry chain so each partial sum stays `< q̂`. The limbs
are intermediate `s1` coordinates (committed) or FS-public reductions. **This is the single most
delicate new piece — it is where R2 must be proven without a modular wrap, and it gates the build.**
The EC recomposition (the anchor's `ec_digit_comb`) is over the group order `≈2^255` and needs no
limbs; the lattice-side `w_val` recomposition does. Resolve the exact limb/carry construction in
DESIGN-review before coding (mirror `nullifier_lwr`'s wrap-guard discipline).

**(R3) `m = repack(w_bits)` (the show message encodes the same bits).** The SEP message `m` is 2
`SepRingElem` whose coefficients are `bits(w)` (LSB-first: `w_bits[i]` ↔ `m[i / 256].coeff[i % 256]`).
After `θ`-embedding, `θ(m)` lives at known `s1` coordinates with the bits in known coefficient
positions. R3 is the linear set: for every `i < 255`, `coeff_{pos(i)}(θ(m)) − τ0(w_bits[i]) = 0`. The
`θ` coefficient map is public and fixed (`proof_subring::embed`), so each equation is a linear ring
relation over `s1` (a `proof_linrel` row, FS-μ-aggregated like the SEP rows). **This is the binding
that makes "the credential signed *this* `w`" — without it a prover could show a credential on one
`m` and bind an unrelated `w` to `C_r`.**

**(R4) `w` canonical (`< Fr::MODULUS`).** Reuse `proof_ltconst` (the `< Fr::MODULUS` bit-gadget,
already built for the anchor) over `w_bits` — prevents the non-canonical-encoding malleability
(LNP22_SHOW R8 P1: two bit-strings ≡ same `Fr` ⇒ nullifier/credential collision).

R1+R4 are families folded into the aggregated show (no new commitment). R2+R3 are linear relations:
either folded as `FQuadForm` linear terms (preferred — keeps ONE garbage commitment) or proven by
`proof_linrel` sharing the same `(t_A, s2)` (must reuse the show's `s2`/garbage to avoid the §C-iv
cross-proof leak — **DESIGN-review must confirm the leak-free path**, see §6).

---

## 4. The composed PQ vouch

```rust
pub struct PqBlindedVouch {
    pub bbs:    BoundPresentation,   // BBS cred on w, opens C_r           (unchanged)
    pub show:   ShowAggProof,        // SEP cred possession on m            (replaces `bind`)
    pub anchor: AnchorBindProof,     // w_bits[0..255] ↔ C_r                (new in the vouch)
    pub null:   nullifier_lwr::NullifierProof, // N = round(a_epoch·w_val)  (replaces EC nullifier)
    pub commitment: AbdlopCommitment,// the shared (t_A, t_B)
    // R1–R4 live INSIDE `show.agg` (folded families/linear terms) — no separate proof objects.
}
```

**`prove`** (member side): pack the unified `s1` (§2) from the member's SEP signature + `w`; one
`commit_witness`; `present_bound` (BBS, draws `r`, forms `C_r`); `prove_show_agg` with R1–R4 folded;
`prove`(anchor) over `bit_idx = w_bits range`, same `(t_A,s1,s2,C_r,r)`; `prove_nullifier` over
`w_blk = w_val, e_blk = e_null`. All share `t_A`, `s2`, `C_r`.

**`verify`** (AND-verify): `verify_bound` ∧ `verify_show_agg` (incl. R1–R4) ∧ `verify`(anchor, same
`t_A` + `C_r`) ∧ `verify_nullifier` (same `t_A`); **and** the shared-state checks — all four reference
the SAME `t_A` (the `commitment.t_A`) and the SAME `C_r` (`bbs.c_r == anchor.c_r`, and the anchor's
`C_r` is the one the BBS half opened). Returns the nullifier `N`.

The shared `t_A` is the lattice analogue of the foundation vouch's shared-`C_r` check: it is what
fuses the show (`m`), the anchor (`w_bits`), and the nullifier (`w_val`) into a statement about one
committed `s1` — and R2/R3 make that one `s1` carry one consistent `w`.

---

## 5. Security argument (sketch — to harden in review)

A `PqBlindedVouch` that verifies implies, under M-SIS (binding of `t_A`) + the SEP credential's
unforgeability (M-SIS) + the BBS credential (q-SDH, classical) + DL (Pedersen `C_r`):

- **PQ membership unforgeability.** `verify_show_agg` ⇒ the prover knows a SEP signature `(t,v)` on the
  committed `m` under `vk` (M-SIS-hard to forge — this is what the commitment-opening `bind` lacked).
  R3 ⇒ that `m` encodes `w_bits`; R2 ⇒ `w_bits` recompose to `w_val`; the anchor ⇒ `w_bits` = `C_r`'s
  `w`. So a forged vouch needs a forged SEP credential on the bits of *some* `w` it can also open in
  `C_r` — PQ-hard. (BBS adds classical unforgeability; either half holding ⇒ unforgeable, per C3.)
- **One-show / rate-limit.** `verify_nullifier` ⇒ `N = round_Δ(a_epoch·w_val)` with the in-circuit
  `e∈[0,Δ)` + `N<q1` ranges (unique `N` per `(w,epoch)`); R2 ties `w_val` to the same `w`; the ledger
  rejects a repeated `N`. PQ-hiding (ring-LWR), per Q6=(ii).
- **Anonymity (unchanged from the show's guarantees).** The show is statistical-ZK (one garbage
  commitment, §C-iv fix); the anchor + nullifier + R1–R4 reuse the same garbage so they add no leak
  (⚠️ §6). `w`, `m`, `t`, `v` never revealed. Issuer-hiding is the HYP-324 epoch-key layer (§9, out
  of scope here — the core verifies under a public `vk` until that wrapper gates it).

---

## 6. The leak risk (why this is design-first, not a glue job)

The §C-iv lesson: separate masked sub-proofs that share `(s2, garbage_b)` but commit *separate*
garbage leak `s1`'s covariance through `t1_i − t1_j`. The aggregated show fixed this by folding
EVERYTHING into ONE masked quadratic with ONE `(t0,t1)`. **R1–R4, the anchor, and the nullifier must
not reintroduce the leak.** Two admissible structures, to choose in review:

- **(A) Fold-in (preferred).** R1–R4 become additional `families`/linear terms inside
  `agg_show_relation` (one garbage commitment covers them — like the existing norm/binariness
  families). The anchor + nullifier remain separate Σ-protocols but their *garbage* (`e0/e1`) must be
  masked by the SAME BDLOP `t_B` slot the show uses, OR proven to carry no `s1`-covariance. This needs
  the anchor/nullifier garbage to be re-expressed as families of the show's quadratic — a real
  refactor of `proof_anchor_bind`/`nullifier_lwr` to emit fold-in terms rather than standalone proofs.
- **(B) Standalone-but-masked.** Keep anchor/nullifier as separate proofs but give each its own
  τ0=0-masked garbage committed via the show's `s2` (no shared raw garbage across proofs). Lighter
  refactor, heavier proof, and the cross-proof-independence argument must be made explicitly.

**DESIGN-review question Q1:** which structure, and prove it is leak-free (a statistical-ZK test on
the composed transcript, since functional tests + the Codex gate are blind to a ZK leak —
LNP22_SHOW §C-iv note). Default lean: (A), because it preserves the one-garbage-commitment invariant
the aggregated show already proves leak-free.

---

## 7. Open questions for DESIGN-review (gate before any code)

- **Q1** (§6) leak-free composition structure — (A) fold-in vs (B) standalone-masked.
- **Q2** (§3 R2) the exact multi-limb recomposition + carry chain proving `w_val = Σ2ⁱ·w_bits` with no
  `q̂` wrap. This is the make-or-break linear relation; specify limb width `B`, carry coordinates, and
  the per-limb range, mirroring `nullifier_lwr`'s wrap guard.
- **Q3** (§3 R3) confirm the `θ`-coefficient position map `pos(i)` (`proof_subring::embed`) so R3's
  linear rows are exact; a wrong `pos(i)` silently binds the wrong bits.
- **Q4** `s1` grows by 255+2 coordinates — confirm the ABDLOP dimensions (`m1`, M-SIS hardness) still
  hold at the show modulus, and the larger `s1` does not break `norm_bounds_provable` (the `B²<q̂`
  guard). May need the show modulus headroom (HYP-330).
- **Q5** σ for the appended blocks vs the SEP-scale show σ — one bound, or per-block (the `w_bits`
  are tiny, `w_val` small, `e_null` `<Δ`).
- **Q6** does R3 obviate the show's existing message-binariness family (m is now pinned via w_bits), or
  are both needed? (Likely keep both; m must be binary for the SEP relation regardless.)

---

## 8. Build order (after DESIGN-review clean)

0. **Resolve Q1–Q6** in review; pin the leak-free structure + the limb recomposition.
1. **`w_bits`/`w_val`/`e_null` packing** — extend `pack_show_witness` → `pack_pq_vouch_witness`;
   `w→bits→w_val` encoder (canonical, LSB-first); offsets + length checks (Codex P2 discipline).
2. **R2 recomposition** (the delicate one) — limb/carry linear relation + its range; standalone test
   first (a known `w` recomposes; a wrong `w_val` rejects; no wrap at `w=r−1`).
3. **R3 repack** — the `θ`-coefficient linear rows; test `m`↔`w_bits` (honest binds; mismatched `m`
   rejects).
4. **Fold R1–R4 into `agg_show_relation`** (or the chosen structure) — extend `families`; ℓ₂/wrap-safe.
5. **Compose `PqBlindedVouch::{prove,verify}`** + shared-`t_A`/`C_r` checks; replace `bind` in a new
   `pq_vouch.rs` (keep `vouch.rs` as the classical foundation until HYP-343 retires it).
6. **Tests (rule 27):** integration — real SEP credential + real BBS credential, full
   prove→encode(codec v2)→decode→verify, on one `w`; adversarial — wrong `w` in `C_r` vs `m` rejects
   (R3), tampered `w_val` rejects (R2), non-canonical `w` rejects (R4), double-show same `N`, replay;
   **statistical-ZK test** on the composed transcript (Q1). Each chunk: Codex gpt-5.5/high gate.
7. **Codec v2** — append `show`/`anchor`/`null`/`commitment` to the `BlindedVouch` codec under a
   bumped `VOUCH_CODEC_VERSION` (the v1 envelope was built for exactly this).

σ/B/c_256 stay PROVISIONAL → HYP-330 external audit. The vouch stays behind `experimental-unaudited`
until params land + HYP-343 wires it into `protocol_core::{VouchIssuer,VouchVerifier}`.

---

## 9. Out of scope (tracked separately, the remaining HYP-352 sections)

- **Blind issuance** (Fig 7.1 `OblSign`) — the member obtains the SEP credential on `m=bits(w)`
  without the issuing coalition learning `w`. Its own design-first pass; PQ blind signatures are
  research-adjacent (`reference_pq_blind_sig_landscape`). The show here assumes an already-issued
  credential.
- **HYP-343** trait reshape — wire `PqBlindedVouch` behind `protocol_core::{VouchIssuer,
  VouchVerifier}`, retire `StubVouchScheme`. Gated on this wiring + blind issuance + params.
- **HYP-330** — external audit calibrates `SHOW_SIGMA3`/σ/`c_256`/`B256` and the de-provisionalized
  M-SIS dimensions; the `experimental-unaudited` gate drops only after.
