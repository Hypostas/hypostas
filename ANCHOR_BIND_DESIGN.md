# §5.7-c — Cross-Domain Anchor Bind (lattice nullifier `w` ↔ EC Pedersen `C_r`)

**Status:** DESIGN (pre-build). HYP-352 item 1 (C), LNP22 build §5.7-c.
**Risk class:** ⚠️⚠️ HIGHEST — same class as `bind.rs` (HYP-345). A subtle bug here is a *silent*
anonymity/soundness failure. Build is gated by this crate's own rigor + the Codex gate; HYP-330
external audit is the pre-mainnet backstop, not a substitute.

---

## 1. What must be proven

The **member/prover scalar** `w` — the credential holder's committed secret, encoded as `m = bits(w)`
and used as the **nullifier key** `N = round_p(a_epoch·w)` (terminology per `LNP22_SHOW_DESIGN §1`; the
*introducer* is the epoch anchor `a_epoch`/`ipk*`, NOT `w` — tying the bind to `w` ties it to the
credential holder, which is what one-show requires) — is committed in two domains that must attest the
*same* `w`:

- **EC Pedersen anchor** `C_r = w·g + r·h` (`bridge.rs`, BLS12-381 G1) — the value the BBS half and the
  whole vouch hang off.
- **Lattice show** — `w` is the SEP-credential message, committed inside the LNP22 ABDLOP witness
  `s1` over the **proof ring** `R̂_q̂` (`q̂ = PHAT_P·PHAT_Q1 ≈ 2^37.7`, flips to `≈2^57.7` at HYP-330).
  The nullifier `N = round_p(a_epoch·w)` (`nullifier_lwr.rs`) is derived from this same `w`.

§5.7-c proves: **the `w` inside `C_r` equals the `w` inside the lattice show/nullifier.** Without it,
a prover could show a valid credential for `w` but anchor the vouch (and the nullifier) to a *different*
`w'` — breaking one-introducer-per-onboarding and the dual-hybrid AND-binding.

This is the cross-*ring* analogue of `bind.rs`, which binds `C_r` to a **SIS-ring** (`ring.rs`, `Q =
8380417`) statement `t = A·s`. Here the lattice side is the **proof-ring** ABDLOP commitment, not SIS.

## 2. Why the naive single-challenge bind is UNSOUND (finding, 2026-06-15)

The tempting construction — one shared Fiat–Shamir challenge `c`, prove per digit `z_i^ec == τ0(z_i^lat)`
(EC response equals the const-coeff of the lattice response) — **does not bind soundly**:

- The lattice proof challenge (`proof_challenge`, `CHALLENGE_RHO = 8`) has coefficients in `[−8, 8]`,
  so `τ0(c) ∈ [−8, 8]`. A single-shot EC Schnorr with a `±8` challenge has soundness error `~1/17`
  **per digit** — useless.
- The EC side needs a full-`Fr` (≈256-bit) challenge for binding; the lattice side is `ρ`-bounded by
  construction (short challenges are what make the lattice extractor work). **They cannot share one
  scalar challenge.**

`bind.rs` resolves exactly this mismatch with **κ binary-challenge rounds** (`c_j ∈ {0,1}`, `2^−κ`
soundness), sharing *per round* the coefficient masks `y_i`, the binary challenge `c_j`, and the
responses `z_i = y_i + c_j·a_i` across the EC digit bases `{g_i = 2^i·g, h}` and the lattice opening.
"κ binary rounds ⇒ `2^−κ` soundness; one Fiat–Shamir challenge binds every commitment."

**§5.7-c must reproduce that ROUNDS structure, cross-ring.** No shortcut.

## 3. Construction

Reuse, don't reinvent:

- **Lattice digit decomposition = `proof_range`'s committed bits.** `proof_range` already commits the
  bit-blocks `b_0..b_{L-1}` of `w` in `s1` and proves `w = Σ 2^i·b_i` + binariness over the proof ring.
  Those bits ARE the digit decomposition the bind needs on the lattice side. (`L = range_bits(2^L)`;
  for `w` we bind the full `w`, not the nullifier remainder `e`.)
- **EC digit bases** `g_i = 2^i·g` (mirror `bind.rs::BindParams::g_pow`).

### 3.1 Per-round binary-challenge protocol (κ rounds, Fiat–Shamir)

For round `j ∈ [0, κ)` (one shared FS challenge yields all `c_j` and binds every announcement):

1. **Prover masks.** Per digit `i`: a lattice mask `y_{j,i}` (a *small* proof-ring element — bits are
   `0/1`, so a `MASK_SIGMA`-class mask keeps `τ0(y)` from wrapping mod `q̂`) and the matching EC
   announcement `A_{j,i} = τ0(y_{j,i})·g_i + s_{j,i}·h` (the EC mask `a_{j,i} = τ0(y_{j,i})` — the
   const-coeff of the lattice mask, the cross-domain glue). Plus an EC randomness mask for the link.
2. **Challenge.** `c_j ∈ {0,1}` from the FS hash of (`C_r`, `t_A`, **the per-round lattice
   announcement `w_c_j = A1·y1_j + A2·y2_j`**, all EC announcements `A_{j,i}`, the link announcement,
   `g_i`, `h`, the public statement). ⚠️ **`w_c_j` MUST be in the transcript (P1, DESIGN-review round 5
   2026-06-15):** omitting it lets the prover pick `c_j` first then set `w_c_j = A1·Z1 + A2·Z2 − c_j·t_A`
   to pass the lattice opening for arbitrary digit projections — the leg would no longer bind the
   projections to the committed `s1`. `bind.rs::fs_challenge` hashes `w_lat` alongside `t_ec` for exactly
   this reason; mirror it.
3. **Responses.** Lattice: `Z_{j,i} = y_{j,i} + c_j·b_i` (proof-ring element). EC: the verifier
   recomputes from `τ0(Z_{j,i})`. The SAME small integer `τ0(Z_{j,i})` plays the digit response in
   BOTH the EC equation and the lattice opening (rejection-bounded so it does not wrap in either
   modulus — the crux, identical to `bind.rs`'s shared-`z_i`).

### 3.2 Verifier checks

Realized via FS compression (§4 layout): the verifier **reconstructs** each round's announcements from
the responses, recomputes `c`, and checks `c == proof.challenge` + the response norm bounds. The two
logical equations it thereby enforces are:
- **Lattice opening** (per round): `w_c_j := A1·Z1_j + A2·Z2_j − c_j·t_A` is the reconstructed ABDLOP
  announcement (mirror `proof_linear`); hashing it into `c` ties `τ0(Z1_j[bit_idx_i])` to the committed
  bits in `s1` (a cheating opening changes `c` ⇒ recomputation fails).
- **EC digit equation** (per round): `A_j := Σ_i τ0(Z1_j[bit_idx_i])·g_i + z_{r,j}·h − c_j·C_r` is the
  reconstructed EC announcement, where `τ0(Z1_j[bit_idx_i])` is the **projection of the SAME full
  lattice opening `Z1_j`** (NOT a standalone value) — that shared projection, also hashed into `c`,
  forces `C_r`'s digits to equal the bits committed in `t_A`.
- **Norm bound**: every `Z1_j`/`Z2_j` response coordinate within the rejection box (range comparison,
  not `.abs()`, so a malformed `i64::MIN` can't overflow — `bind.rs` gate-P2).
- **Link**: `C_r − Σ_i 2^i·D_i = δ·h` is implicit in the digit-base aggregation (no separate `D_i`
  needed if the EC equation uses `g_i = 2^i·g` directly, as `bind.rs` does).
- **Binariness only** of `b_i` is reused from `proof_range`'s binariness sub-proof (each `b_i ∈ {0,1}`),
  so the shared `τ0(Z_{j,i})` are genuinely bit-responses. ⚠️ **Do NOT reuse `proof_range`'s
  *recomposition* relation `Σ 2^i·b_i = w` (P2, DESIGN-review round 5):** for `DIGITS ≈ 255` that sum
  exceeds `q̂`, so over `R̂_q̂` it would only prove a residue mod `q̂` (or reject honest identities). The
  full recomposition lives ONLY in the EC digit equation (next bullet); the lattice side contributes
  binariness + the per-bit opening, never the wide sum.
- ⚠️ **`w ← U(F_r)` is FULL 255-bit width + a canonical `< Fr::MODULUS` proof (the SETTLED
  representation; P2, round 5).** `LNP22_SHOW_DESIGN.md` §1 (R8 P1) already fixes `w ← U(F_r)`, `m =
  bits(w)` the canonical 255-bit representative, AND a `digit-value < Fr::MODULUS` range proof at
  show/issuance — chosen deliberately (full width ≠ full entropy; the EC side only sees `w mod r`, so
  without canonicity the same `C_r` binds `w` vs `w−r`, colliding nullifiers). The anchor MUST use the
  SAME `w` (else it cannot bind credentials issued under the show spec — the round-5 cross-doc P2). So:
  `DIGITS = 255`, and canonicity is the **show's existing `< Fr::MODULUS` bit-gadget** (a less-than-
  constant boolean check over the committed bits — NOT `proof_range`'s `i64` two-range trick, NOT
  multi-limb; it is a per-bit comparison, no wide sum). The anchor REUSES that one shared gadget. (My
  earlier "bounded `DIGITS ≤ 254`" detour contradicted the settled show spec — reverted.)
- ✅ **No multi-limb recomposition (CORRECTED — the round-3 "multi-limb" item was MY over-correction,
  not a gate finding).** The recomposition `Σ_i 2^i·b_i = w` happens ENTIRELY on the **EC side**, whose
  group order ≈2^255 holds it natively (mod `r`). The **lattice side never forms the `>q̂` sum** — it
  opens only individual bit coordinates, each `τ0(Z[bit_idx_i])` rejection-bounded to `< q̂/2 ≈ 2^36.7`.
  That per-bit response is the SAME small integer mod `q̂` and mod `r` (unambiguous since `< q̂/2 <
  r/2`), so the cross-ring gap is bridged **per-bit, not per-`w`** — no limbs, no carry chain. This is
  **exactly `bind.rs`'s proven technique**: it binds a `DIGITS`-bit `w` over the `Q ≈ 2^23` SIS modulus
  (also `≪ 2^255`) with no limbs — *"the SAME small integer `z_i` (rejection-bounded, `< p`), matched
  over the integers"* (`bind.rs` §doc). §5.7-c is that construction, cross-ring (proof ring for SIS).

Soundness: `2^−κ` (κ ≈ 128 ⇒ negligible). Both equations forced to agree on every small `τ0(Z_{j,i})`
(matched over the integers) ⇒ the committed proof-ring bits and the `C_r` digits are identical ⇒ same
`w` (made canonical by the shared `< Fr::MODULUS` bit-gadget, removing the `w` vs `w−r` ambiguity). ZK:
the masks `y_{j,i}`/`s_{j,i}` are uniform; rejection sampling on `Z` (deferred to §C-iv's masking pass).

## 4. Witness layout & types (build sketch)

- `AnchorBindParams { bridge: BridgeParams, g_pow: Vec<G1Affine>, kappa: usize }` (mirror
  `bind.rs::BindParams` but proof-ring side instead of SIS).
- `AnchorBindProof { c_r: G1Affine, challenge: Vec<bool> /*κ*/, z1: Vec<Vec<ProofRingElem>> /*FULL
  opening over ALL s1 coords, per round*/, z2: Vec<Vec<ProofRingElem>> /*opening over s2 randomness,
  per round*/, z_r: Vec<Fr>, binariness: ConstraintProof /*b_i∈{0,1}*/, canonical: LtConstProof /*the
  <Fr::MODULUS gadget, chunk 0*/ }`.
  ⚠️ **Fiat–Shamir COMPRESSION — announcements are RECONSTRUCTED, not stored (P2, DESIGN-review round
  11 2026-06-15).** The proof carries NO announcements (neither `w_c_j` nor the EC `A_j`). The verifier
  RECONSTRUCTS them deterministically per round from the responses + the public statement:
  `w_c_j = A1·z1_j + A2·z2_j − c_j·t_A` (lattice) and `A_j = Σ_i τ0(z1_j[bit_idx_i])·g_i + z_r_j·h −
  c_j·C_r` (EC), then recomputes `c = FS(C_r, t_A, {w_c_j}, {A_j}, g_i, h, public stmt)` and checks
  `c == proof.challenge`. This is exactly `bind.rs`'s compressed FS-with-aborts (it stores only
  `{c_r, t, challenge, z, z_r, range}` and reconstructs `w_lat`/`t_ec` in `verify`). The round-5 P1
  ("`w_c` MUST be in the transcript") is satisfied by hashing the RECONSTRUCTED `w_c_j` — binding holds
  because a cheating `w_c_j` would change `c` and fail the recomputation.
  ⚠️ **Do NOT carry `proof_range::RangeProof` (P2, round 6):** it embeds the wide recomposition
  `Σ2^i·b_i=w` which over `R̂_q̂` proves only a residue mod `q̂` (or rejects honest 255-bit `w`). Carry
  the binariness sub-proof + the separate `< Fr::MODULUS` gadget ONLY; the recomposition is the EC
  digit equation's job, never the lattice side's.
  ⚠️ **P1 (DESIGN-review 2026-06-15): carry the FULL ABDLOP opening, not just digit columns.** `t_A`
  commits the *whole* show witness `s1`, so the lattice check `A1·Z1 + A2·Z2 = w_c + c_j·t_A` needs
  `Z1` over ALL `s1` coordinates plus `Z2` over the commitment randomness `s2`. The per-digit responses
  consumed by the EC equation are the **projections** `τ0(Z1[bit_idx_i])` of that same full opening —
  this is what binds the bits to the original committed signature witness. Projecting to digit columns
  *without* the full opening (the rejected shortcut) would leave the bits unbound to `t_A` unless a
  separate bit subcommitment were added (more data, not less) — so the full opening is the right design.
- `prove(params, t_a, w_idx, bit_lo, bit_hi, s1, s2, c_r, w, r, mask_sigma, rng) -> Option<…>`.
- `verify(params, t_a, w_idx, bit_lo, bit_hi, c_r, proof, mask_sigma) -> bool`.

## 5. Build chunks (each: build → test → Codex gate → commit)

0. **SHARED DEPENDENCY (build first, reuse): the `< Fr::MODULUS` canonical bit-gadget.** NOT built yet
   (confirmed: no less-than-`r` gadget in the crate; `proof_range`'s `i64` `B` cannot reach `2^255`).
   It is a less-than-constant **boolean** check over the `DIGITS = 255` committed bits (MSB-walk /
   borrow chain; each step a small per-bit constraint, NO wide ring sum, NOT multi-limb). It is ALSO
   the show/issuance R8 P1 requirement (`LNP22_SHOW_DESIGN §1`), so build it ONCE as a shared module
   (`proof_ltconst.rs` or fold into `proof_range`) and reuse in show + issuance + anchor. Design +
   DESIGN-review this gadget before anchor chunk 1. (This is the only real sub-construction the rounds
   surfaced — small + bounded, unlike the false multi-limb alarm.)
1. `AnchorBindParams` + `g_pow` precompute (`g_i = 2^i·g`, `i < DIGITS = 255`) + the EC digit-base
   aggregation helper (+ test: `Σ b_i·g_i + r·h == C_r` for honest digits). Read `bind.rs` end-to-end
   as the line-by-line template (the audited reference for this exact construction, cross-ring).
2. One round of the binary-challenge protocol (prove/verify a single `c_j`), both legs (lattice ABDLOP
   opening with `w_c_j` IN the FS transcript + EC digit equation) sharing the projected `τ0(Z1)`.
3. κ-round Fiat–Shamir wrapper + soundness test (tampered digit / swapped `w'` rejected; honest
   verifies).
4. Wire `proof_range`'s **binariness** + the chunk-0 `< Fr::MODULUS` gadget as the sub-proofs (NOT
   proof_range's wide recomposition); full `anchor_bind_verifies` integration test binding a real
   nullifier `w` to its `C_r`.
5. Compose into the vouch (`vouch.rs`, HYP-343/§5.10): the show + nullifier + anchor-bind share one
   `w`, one `C_r`.

## 6. Open params (PROVISIONAL → HYP-330)

`κ` (soundness rounds, target 128), `DIGITS = 255` (full canonical `Fr` width, per the settled show
spec; `bind.rs` uses 32 as a toy and notes a real deployment raises the lattice witness dim for full
width), the lattice mask σ for bit-openings, and the `q̂` flip to the show modulus. Params provisional;
the *mechanism*
(ROUNDS cross-ring, shared small `τ0(Z)` matched over the integers, EC-side recomposition) is the
soundness core and is not deferrable.
