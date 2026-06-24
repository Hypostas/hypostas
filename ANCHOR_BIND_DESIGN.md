# §5.7-c — Cross-Domain Anchor Bind (lattice nullifier `w` ↔ EC Pedersen `C_r`)

**Status:** DESIGN (pre-build). HYP-352 item 1 (C), LNP22 build §5.7-c.
**Risk class:** ⚠️⚠️ HIGHEST — same class as `bind.rs` (HYP-345). A subtle bug here is a *silent*
anonymity/soundness failure. Build is gated by this crate's own rigor + the Codex gate; HYP-330
external audit is the pre-mainnet backstop, not a substitute.

---

## 1. What must be proven

The C3 vouch's introducer identity `w` is committed in two domains that must attest the *same* `w`:

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
2. **Challenge.** `c_j ∈ {0,1}` from the FS hash of (`C_r`, `t_A`, all `A_{j,i}`, the link
   announcement, `g_i`, `h`, the public statement).
3. **Responses.** Lattice: `Z_{j,i} = y_{j,i} + c_j·b_i` (proof-ring element). EC: the verifier
   recomputes from `τ0(Z_{j,i})`. The SAME small integer `τ0(Z_{j,i})` plays the digit response in
   BOTH the EC equation and the lattice opening (rejection-bounded so it does not wrap in either
   modulus — the crux, identical to `bind.rs`'s shared-`z_i`).

### 3.2 Verifier checks

- **Lattice opening** (per round): the ABDLOP opening `A1·Z1 + A2·Z2 = w_c + c_j·t_A` holds with the
  reconstructed `Z` (mirror `proof_linear`). This ties `τ0(Z_{j,i})` to the committed bits in `s1`.
- **EC digit equation** (per round): `Σ_i τ0(Z1[bit_idx_i])·g_i + z_{r,j}·h == A_j-aggregate + c_j·C_r`
  where `A_j-aggregate` is the round's combined EC announcement and `τ0(Z1[bit_idx_i])` is the
  **projection of the SAME full lattice opening `Z1`** checked above (NOT a standalone value) — that
  shared projection is precisely what forces `C_r`'s digits to equal the bits committed in `t_A`.
- **Link**: `C_r − Σ_i 2^i·D_i = δ·h` is implicit in the digit-base aggregation (no separate `D_i`
  needed if the EC equation uses `g_i = 2^i·g` directly, as `bind.rs` does).
- **Range/binariness** of `b_i` comes from the reused `proof_range` proof (lattice side), so the
  shared `τ0(Z_{j,i})` are genuinely bit-responses, not arbitrary.

Soundness: `2^−κ` (κ ≈ 128 ⇒ negligible). Both equations forced to agree on every `τ0(Z_{j,i})` ⇒
the committed proof-ring `w` and the `C_r` `w` decompose to the same bits ⇒ same `w` (mod the shared
`2^i` reconstruction). ZK: the masks `y_{j,i}`/`s_{j,i}` are uniform; rejection sampling on `Z`
(deferred to §C-iv's masking pass, consistent with the rest of the show).

## 4. Witness layout & types (build sketch)

- `AnchorBindParams { bridge: BridgeParams, g_pow: Vec<G1Affine>, kappa: usize }` (mirror
  `bind.rs::BindParams` but proof-ring side instead of SIS).
- `AnchorBindProof { c_r: G1Affine, w_c: Vec<ProofRingElem> /*lattice opening announcement A1·y1+A2·y2,
  per round*/, challenge: Vec<bool> /*κ*/, z1: Vec<Vec<ProofRingElem>> /*FULL opening over ALL s1
  coords, per round*/, z2: Vec<Vec<ProofRingElem>> /*opening over s2 randomness, per round*/, z_r:
  Vec<Fr>, range: proof_range::RangeProof }`.
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

1. `AnchorBindParams` + `g_pow` precompute + the EC digit-base aggregation helper (+ test:
   `Σ τ0(b_i)·g_i + r·h == C_r` for honest digits).
2. One round of the binary-challenge protocol (prove/verify a single `c_j`), both legs (lattice
   opening + EC digit equation) sharing `τ0(Z)`.
3. κ-round Fiat–Shamir wrapper + soundness test (tampered digit / swapped `w'` rejected; honest
   verifies).
4. Wire `proof_range` in as the binariness/range sub-proof; full `anchor_bind_verifies` integration
   test binding a real nullifier `w` to its `C_r`.
5. Compose into the vouch (`vouch.rs`, HYP-343/§5.10): the show + nullifier + anchor-bind share one
   `w`, one `C_r`.

## 6. Open params (PROVISIONAL → HYP-330)

`κ` (soundness rounds, target 128), the lattice mask σ for bit-openings, and the `q̂` flip to the
show modulus. Params provisional; the *mechanism* (ROUNDS cross-ring, shared `τ0(Z)`) is the
soundness core and is not deferrable.
