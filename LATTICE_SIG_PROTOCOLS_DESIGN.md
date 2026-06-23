# Lattice Signature-with-Efficient-Protocols — PQ Anonymous-Credential Show Proof

**Status:** DESIGN (design-first; Codex DESIGN-review pending)
**Issue:** HYP-352 item 1 (C) — the ZK-possession / show proof for the C3 lattice half
**Author:** Iris · 2026-06-15
**Depends on:** the shipped, gate-clean `vouch-crypto` lattice stack (`ring`, `gadget`, `gaussian`,
`trapdoor`, `ring_trapdoor`, `module_sis`, `sis_pok`) and the EC half (`bbs`, `presentation`,
`bridge`, `bind`, `nullifier`). All lattice code is behind `experimental-unaudited`.

---

## 0. One-paragraph summary

The C3 BlindedVouch is `BBS-show AND lattice-show`, both bound to the shared Pedersen anchor
`C_r = w·g + r·h` over BLS12-381. The BBS half (everlasting anonymity) is done. The lattice half
must prove, in **statistical zero-knowledge** and with **PQ soundness**, that the prover holds an
**issuer's signature on the same `w`** committed in `C_r`. We have built the issuer side (the GPV /
MP12 trapdoor + an issuer-signed credential). What remains is the **show proof**: proving knowledge
of a signature without revealing it. This document selects the construction (a **tag-based
commitment-compatible lattice signature** shown with an **LNS-style exact/product ZK proof**),
fixes the interface and security properties, and scopes the faithful transcription of the two
reference frameworks. It exists because the naive paths (GPV-on-`H(w)`, Merkle accumulator) cannot
bind to `C_r` without proving a hash in ZK, and because a *direct* Lyubashevsky proof of the
Gaussian-width preimage is structurally impossible at our modulus.

---

## 1. The problem, precisely

### 1.1 What the lattice half must prove

A verifier, given the public anchor `C_r` (and the issuer's public key `ipk`), accepts iff the
prover knows `(w, r, σ)` such that:

1. `C_r = w·g + r·h` (the prover opens the EC anchor — shared with the BBS half), AND
2. `σ` is a valid issuer signature on `w` under `ipk` (PQ-unforgeable membership), AND
3. the proof reveals nothing about `w`, `r`, or `σ` beyond their existence — **statistically**
   (so the AND-composition preserves the BBS half's everlasting anonymity).

Property (2) is the part that needs PQ cryptography: a quantum adversary that breaks BBS (q-SDH)
must still be unable to forge the lattice half, so a vouch for a non-member remains infeasible.

### 1.2 Why the obvious approaches fail (recap of the fork)

| Path | Membership object | Why it fails for C3 |
|---|---|---|
| GPV credential on `H(w)` | short `x`, `A·x = H(w)` | unforgeable, but binding "the `w` in `H(w)` = the `w` in `C_r`" requires **proving the hash in ZK** — expensive, and defeats the linear cross-domain bind (HYP-345). |
| Lattice Merkle accumulator | leaf = `Hash(w)`, ZK path | same ZK-hashing binding problem; also discards the trapdoor. |
| **Keep commitment-opening PoK only** | `t = Com(w)` opening | **insufficient** — proves consistency of `w`, NOT membership; a PQ forger commits any `w`. This is the pre-item-1 state we are fixing. |
| Direct Lyubashevsky PoK of GPV `x` | Gaussian `x`, `A·x=…` | **structurally impossible**: mask `γ ~ d·τ·β ≈ 6400·39·8192 ≈ 2·10⁹ ≫ q/2` for rejection to accept. |

### 1.3 Why (C) is the answer

A **signature with efficient protocols** is engineered so that the *show* witnesses are small-norm
and the message binds **linearly** to a commitment. Two design choices do this:

- **Tag-based unforgeability** (Ducas–Micciancio / Boyen): a fresh per-signature tag `τ` shifts the
  signing matrix, so signatures are *not* combinable by linearity — the message can therefore be
  encoded **linearly** (no hash) without the `x_{w₁}+x_{w₂}` forgery.
- **Small-norm message encoding**: `w` enters via a small-norm digit vector `m` and a public matrix
  `D` (`D·m` encodes `w`), so the same-value bind to `C_r` is the **linear** HYP-345 cross-domain
  technique — `m` is exactly `w`'s digits.

The deep ZK core (proving the short signature + small message in statistical ZK with a *tight*
extracted bound) is the **LNS exact-proof / product-proof framework**. That core is needed by any
sound construction; (C) wraps it in the signature structure that makes it bind correctly and stay
PQ-unforgeable. The GPV/MP12 trapdoor we already shipped is the **signing primitive** underneath —
not wasted.

---

## 2. Construction selection (references to transcribe — do NOT approximate from memory)

Per the engineering standard (read the reference's actual logic; never roll our own crypto except as
faithful transcription of an audited reference), the build will transcribe from these. The design
fixes *which* and *how they compose*; the exact equations/constants come from the papers at build
time.

1. **Signature scheme:** Jeudy, Roux-Langlois, Sanders — *"Lattice Signature with Efficient
   Protocols, Application to Anonymous Credentials"* (CRYPTO 2023). The tag-based, commitment-
   compatible signature designed for exactly this show proof. Underlying primitive: a GPV/MP12
   trapdoor signature (what we have). Fallback/cross-check reference: del Pino–Katsumata
   "A New Framework for More Efficient Round-Optimal Lattice-Based (Partially) Blind Signatures."
2. **Show proof (the deep ZK core):** Lyubashevsky, Nguyen, Seiler — *"Practical Lattice-Based
   Zero-Knowledge Proofs for Integer Relations"* / *"Shorter Lattice-Based Zero-Knowledge Proofs
   via One-Time Commitments"* (LNS20/LNS21), and Lyubashevsky–Nguyen–Plançon for the product
   (`b∈{0,1}`) proof. Provides: a commitment to the witness, a linear relation proof, and a
   **product/quadratic** proof (the `b·(b−1)=0` constraint) so the bit-decomposition extraction is
   *tight* (no `2^k` gadget blowup → extracted `x*` stays `< q`).
3. **Cross-domain same-value bind:** our shipped `bind.rs` (HYP-345, Asiacrypt-2014 digit
   decomposition + shared challenge), generalized to bind `m` (lattice digits of `w`) to `C_r`.
4. **Composition:** our shipped `presentation.rs` / `vouch.rs` AND-verify and `nullifier.rs`.

⚠️ **Sovereignty note:** there is no audited *pure-Rust, C-free* implementation of LNS to depend
on (reference code is research-grade, often x86/AVX). This is a faithful-transcription build, the
deepest in the privacy stack. The design-first step exists to commit to it with eyes open.

---

## 3. The construction (the level we can fix now)

Notation: ring `R_q = Z_q[X]/(X^256+1)`, `q = 8380417` (shipped). Module rank `n`, gadget width
`K=23`. `ipk` = issuer public key, `isk` = the MP12 trapdoor (shipped `RingTrapdoorKey`).

### 3.1 Keys

- `isk`: `RingTrapdoorKey` (trapdoor for `A ∈ R_q^{n×m}`).
- `ipk`: `A` (public), a message matrix `D ∈ R_q^{n×ℓ}` (NUMS-derived), a public syndrome
  `u ∈ R_q^n`, and the tag parameters (an invertible-difference tag set `T ⊂ R_q`).

### 3.2 Message encoding of `w`

`w` is the BLS12-381 scalar committed in `C_r`. Encode it as a small-norm digit vector
`m ∈ R_q^ℓ`, `‖m‖_∞ ≤ B_m` (e.g. base-`β_m` digits packed into ring coefficients), with a public
linear map `Φ` such that `Φ(m) = w` over the integers / in both domains. `Φ` is what the
cross-domain bind (HYP-345) proves consistent with `C_r`. (Exact packing: design sub-decision §3.6.)

### 3.3 Issue (issuer, knows `w` — non-blind; one-introducer onboarding)

1. Pick a fresh tag `τ ∈ T` (invertible-difference set → unforgeability).
2. Form the tag-shifted matrix `A_τ` (e.g. `A_τ = [A | A·R + τ·G]` per Ducas–Micciancio; exact form
   from JRS23).
3. Using `isk`, sample a short `x` with `A_τ · x = u − D·m` (this is `RingTrapdoorKey::sample_pre`
   on the syndrome `u − D·m`, with `A_τ`'s extended structure — **reuses the shipped sampler**).
4. Signature `σ = (τ, x)`; `‖x‖_∞ ≤ β_sig` (the shipped `CRED_RING_INF_NORM_BOUND` regime).

Unforgeability (EUF-CMA): Module-SIS over `A` + the tag structure (no two signatures share `A_τ`,
so linearity attacks fail). **Transcribe the exact reduction + tag set from JRS23.**

### 3.4 Show (prover — the deep ZK core)

Prove knowledge of `(τ, x, m, w, r)` such that `A_τ·x = u − D·m`, `‖x‖,‖m‖` small, `C_r = w·g+r·h`,
`Φ(m)=w` — in statistical ZK. Structure:

1. **Decompose** `x` and `m` into bits (or base-`β` digits) `b`, all coefficients in a small set.
2. **LNS commit** to `b` (Ajtai/BDLOP commitment, small-norm).
3. **Linear-relation proof**: `A_τ·x = u − D·m` is linear in `b` (with `τ` handled as a committed
   small element or a small set of public tag candidates). Dilithium-style masked response on the
   *small* `b` (γ now fits: witnesses are small, `d·τ·‖b‖_∞ / γ = O(1)` is achievable `< q/2`).
4. **Product proof**: `b·(b−1)=0` (exact binary), so extraction is tight → extracted `x*` is a
   genuine short Module-SIS-valid signature (`< q`). **This is the component that makes (A)/(C)
   sound and is the hardest to transcribe (LNS product proof).**
5. **Cross-domain bind**: tie `b` (digits of `m`, hence `w`) to `C_r` via the shipped `bind.rs`
   shared-challenge same-value proof. Produces the one-show **nullifier** `N = w·H(epoch)`
   (shipped `nullifier.rs`).

### 3.5 Verify + compose

`verify_lattice_show` checks the LNS proof (commitment opening, linear, product), the bind to `C_r`,
and the nullifier. The full vouch verifier (shipped `vouch.rs`) checks **BBS-show AND lattice-show**,
both over the same `C_r`, and returns `N`. Everlasting anonymity: BBS statistical + LNS statistical
ZK. PQ soundness: JRS23 EUF-CMA (Module-SIS).

### 3.6 Design sub-decisions for the Codex DESIGN-review

- **D1 — tag mechanism:** Ducas–Micciancio invertible-difference tags vs JRS23's exact tag handling
  in the show proof (tag committed vs proven-in-set). Affects proof size + soundness reduction.
- **D2 — message packing `Φ`:** how a 255-bit BLS scalar `w` packs into small-norm `m` AND binds to
  the EC scalar via HYP-345 digits, without a separate hash. (The crux of the linear binding.)
- **D3 — commitment scheme:** BDLOP vs Ajtai for the LNS witness commitment; param interplay with
  our `q`, `n`, `K`.
- **D4 — product-proof variant:** the `b∈{0,1}` proof flavor (LNS automorphism/NTT-slot product vs
  the one-time-commitment variant) — proof size vs implementability in pure Rust.
- **D5 — params:** `n`, `ℓ`, `β_sig`, `β_m`, mask `γ`, `τ` (challenge weight), rejection rate, and
  the resulting **bit-security** (Module-SIS + Module-LWE) and proof size. (Provisional per HYP-330;
  the *mechanisms* above are not deferrable, only the calibrated numbers.)
- **D6 — statistical vs computational ZK:** confirm the show proof is *statistical* ZK (required for
  everlasting anonymity under AND-verify); if any step is only computational, flag it as a
  divergence from the C3 everlasting-anonymity claim.

---

## 4. Interface (Rust, behind `experimental-unaudited`)

```text
// New module: vouch-crypto::lattice_cred  (built on ring_trapdoor + module_sis + bind)

pub struct IssuerPublicKey { a: ..., d: ..., u: ..., tags: ... }   // ipk
pub struct IssuerSecretKey { trapdoor: RingTrapdoorKey }           // isk (wraps the shipped trapdoor)
pub struct LatticeSig { tag: RingElem, x: Vec<RingElem> }          // σ = (τ, x)

pub fn keygen(n, m_bar, rng) -> (IssuerPublicKey, IssuerSecretKey)
pub fn issue(isk, w: &Fr, rng) -> LatticeSig                       // non-blind; encodes w→m, signs
pub fn verify_sig(ipk, w: &Fr, sig) -> bool                        // non-ZK issuer/holder check

// The show proof (the deep ZK core):
pub struct LatticeShowProof { commit, linear, product, bind, nullifier }
pub fn show(ipk, sig, w: &Fr, r: &Fr, c_r: &G1Affine, epoch, rng) -> LatticeShowProof
pub fn verify_show(ipk, c_r: &G1Affine, epoch, proof) -> Result<RingElem /*N*/, Error>
```

The full BlindedVouch (`vouch.rs`) gains a lattice-show field and AND-verifies it with the BBS half
over the shared `C_r` (this is where HYP-343's trait reshape lands).

---

## 5. Build plan (phased; each chunk: integration+smoke tests + Codex gate)

Ordered so each chunk is independently gate-clean and the hard core is isolated:

1. **`lattice_cred` skeleton + tag-based signature** — `keygen`/`issue`/`verify_sig` (non-ZK),
   reusing `ring_trapdoor::sample_pre` on the tag-shifted syndrome. Tests: sign→verify, tag
   freshness, EUF-flavor (no-trapdoor forgery fails, linearity-combination fails).
2. **LNS witness commitment** (BDLOP/Ajtai) — commit + open, binding + hiding tests.
3. **LNS linear-relation proof** — prove `A_τ·x = u − D·m` over committed small `b`. The Dilithium-
   style masked proof on small witnesses (γ fits). Soundness/ZK tests.
4. **LNS product proof** (`b∈{0,1}`) — the hardest core; tight extraction. Tests at threshold.
5. **Cross-domain bind** — generalize `bind.rs` to bind `m`-digits to `C_r`; same-value tests.
6. **Compose `show`/`verify_show`** + nullifier; statistical-ZK + soundness + one-show tests.
7. **Wire into `vouch.rs`** (AND-verify) + HYP-343 trait reshape; end-to-end vouch test.

Realistic scope: this is a multi-chunk, research-grade build (the LNS core especially). Each chunk
stays behind `experimental-unaudited`; HYP-330 external audit remains the gate before any mainnet use.

---

## 6. Open questions for Josh / the DESIGN-review

- Confirm **statistical** ZK is required for the lattice half (it is, for everlasting anonymity) —
  or do we accept computational ZK for the lattice half if it dramatically simplifies the build?
  (D6.)
- Proof size tolerance: LNS proofs are tens of KB. Acceptable for a once-per-onboarding vouch?
- Whether to keep the shipped `H(w)`-syndrome credential (`ring_trapdoor::issue`) as a separate
  non-anonymous primitive, or replace it entirely with the `D·m` linear encoding from §3.2.

---

## 7. What is already DONE (so the design is grounded, not greenfield)

- GPV/MP12 ring trapdoor: `keygen`, ring `SampleG` (coeff-wise), efficient ring `SamplePre`
  (Schur-complement perturbation) — **the signing primitive §3.3 needs.** Gate-clean.
- Module-SIS PoK over `R_q` with structured (`SampleInBall`) challenge — **the Dilithium-style
  machinery §3.4.3 reuses.** Gate-clean.
- Cross-domain same-value bind + range proof (`bind.rs`) — **§3.4.5 generalizes this.** Gate-clean.
- BBS half + AND-verify composition + nullifier — **§3.5 plugs into this.** Gate-clean.

The remaining novel work is: the tag-based signature wrapper (§3.3), and the LNS commitment + linear
+ **product** proofs (§3.4.2–4). The product proof is the long pole.
