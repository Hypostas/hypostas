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

A verifier, given the **per-show** anchor `C_r^(i)` and the **epoch attested-introducer anchor**
(NOT a single issuer key), accepts iff the prover knows `(w, s, r_i, σ, ipk*)` — where the SEP
signature is over the attributes `[s | m = bits(w)]`, `s` the hidden registration secret
(impersonation-prevention) and `m` the canonical digit-encoding of the EC scalar `w` — such that:

1. `C_r^(i) = w·g + r_i·h` with **fresh per-show** `r_i` (the prover opens the EC anchor — shared
   with the BBS half; re-randomized each show so issuance cannot match a show — §1.1 R2 P1c), AND
2. `σ` is a valid issuer signature on `w` (lattice-encoded as `m = bits(w)`, cross-domain-bound to
   `C_r`) under some `ipk*` in the epoch introducer set (PQ-unforgeable membership; `ipk*` hidden —
   introducer anonymity, R2 P1d), AND
3. the emitted one-show nullifier `N = F^lat_w(epoch)` — a **PQ keyed lattice PRF** (Q6 DECIDED = (ii),
   2026-06-15), NOT the EC `w·H_G1` — uses the **same `w`** that is in `C_r` and signed (key = the EC
   scalar `w`; `w ← U(F_r)` uniform via `UKeyGen`, R10 P2; hidden from the issuer by blind issuance;
   the show proves in-circuit that `N` is `F^lat` of the bound `w` — `LNP22_SHOW_DESIGN.md` §1.7), AND
4. the proof reveals nothing about `w`, `r_i`, `σ`, or `ipk*` beyond their existence —
   **statistically** (so AND-composition preserves the BBS half's everlasting anonymity). ⚠️ Nullifier
   scope (Q6=(ii)): everlasting anonymity covers the SHOW/membership; the nullifier is **PQ-computational**
   unlinkable (a deterministic `w`-keyed nullifier cannot be everlasting — unbounded brute-force of `w`;
   PQ-computational is the max, reached by the lattice PRF, NOT by the EC `w·H_G1` a QC would break).
   The PQ lattice-PRF nullifier (`nullifier_lwr.rs`, `N=round_p(a_epoch·w)`) anchors to the SAME `w`
   as the BBS half; the classical EC `nullifier.rs` is SUPERSEDED for C3 (Q6). See
   `LNP22_SHOW_DESIGN.md` §1.7 / Q6.

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

1. **Signature scheme:** ⚠️ PRIMARY reference updated 2026-06-15 — **"Practical Post-Quantum
   Signatures for Privacy" (CCS 2024, ePrint 2024/131)**, which **supersedes** Jeudy–Roux-Langlois–
   Sanders *"Lattice Signature with Efficient Protocols, Application to Anonymous Credentials"*
   (CRYPTO 2023, ePrint 2022/509) with a more efficient construction by overlapping authors. Use
   2024/131 as the construction to transcribe; 2022/509 as the conceptual/cross-check reference (its
   tag-based, commitment-compatible, GPV/MP12-underlain signature is the family). Also newer:
   "Lattice-based Proof-Friendly Signatures from Vanishing-SIS" (ePrint 2025/356) — evaluate at
   build time. Fallback: del Pino–Katsumata round-optimal blind-signature framework.
   *Retrieval note: eprint.iacr.org 403s automated fetch (WebFetch + curl both blocked by anti-bot);
   the PDFs must be pulled via an authenticated/manual path before transcription — the references are
   identified, not yet in hand.*
2. **Show proof (the deep ZK core):** ⚠️ LOCKED to **[LNP22]** (Lyubashevsky–Nguyen–Plançon, CRYPTO
   2022, ePrint 2022/284) — the LNS20/LNS21 "integer relations"/"one-time commitments" guess here was
   SUPERSEDED once the reference (thesis §7.4) confirmed the anon-cred show uses LNP22's quadratic +
   exact-ℓ₂-norm framework over an ABDLOP commitment. The authoritative show design is
   **`LNP22_SHOW_DESIGN.md`** (incl. the proof ring `R_q̂` and the `q̂=p·q1` carry-lift). LNS20/21
   remain only conceptual ancestors. Provides: ABDLOP commitment, linear + **quadratic** + exact-ℓ₂
   proofs, Fiat–Shamir.
3. **Cross-domain same-value bind:** our shipped `bind.rs` (HYP-345, Asiacrypt-2014 digit
   decomposition + shared challenge), generalized to bind `m` (lattice digits of `w`) to `C_r`.
4. **Composition:** our shipped `presentation.rs` / `vouch.rs` AND-verify, with the PQ lattice-PRF
   `nullifier_lwr.rs` for C3 (the EC `nullifier.rs` is the BBS-half/classical reference only, Q6).

⚠️ **Sovereignty note:** there is no audited *pure-Rust, C-free* implementation of LNS to depend
on (reference code is research-grade, often x86/AVX). This is a faithful-transcription build, the
deepest in the privacy stack. The design-first step exists to commit to it with eyes open.

---

## 3. The construction (early sketch — ⚠️ SUPERSEDED by §9)

> **⚠️ NORMATIVE NOTE (DESIGN-review R3 P1a):** This section is the EARLY abstract sketch and is
> **superseded by §9** (and `LNP22_SHOW_DESIGN.md`). It is kept only for the reasoning trail. Do NOT
> implement from it: it describes the construction over the *shipped* `q = 8380417` ring +
> `RingTrapdoorKey`, but §9.4 establishes that this modulus splits fully and **breaks SEP tag
> unforgeability** — the credential MUST use the separate SEP-compatible ring `R_p`, `p = 425837`
> (`sep_ring`), with the tag-based signature of §9.1 (shipped as `sep_*`). The authoritative
> construction + interface + build plan are **§9 here** and **`LNP22_SHOW_DESIGN.md`**. The §4
> interface AND the §5 build plan below are likewise early sketches (LNS-based, with a now-dropped
> separate nullifier secret `k`); the shipped/authoritative API is `sep_sig::SepSigKey`/`SepVerifyKey`
> + the planned `lnp22` module, and the authoritative build order is `LNP22_SHOW_DESIGN.md` §4. The
> nullifier is keyed by the EC scalar `w`, NOT a separate `k` (§1.1, R3 P1b). Ignore the `k`/LNS
> references in §§3–5 below.

Notation (early sketch): ring `R_q = Z_q/(X^256+1)`, `q = 8380417`. Module rank `n`, gadget `K=23`.
`ipk` = issuer public key, `isk` = the MP12 trapdoor. *(See §9 for the real `R_p`/`p=425837` setting.)*

### 3.1 Keys

- `isk`: `RingTrapdoorKey` (trapdoor for `A ∈ R_q^{n×m}`).
- `ipk`: `A` (public), a message matrix `D ∈ R_q^{n×ℓ}` (NUMS-derived), a public syndrome
  `u ∈ R_q^n`, and the tag parameters (an invertible-difference tag set `T ⊂ R_q`).

### 3.2 Message encoding of `(w, k)`

The signed message is **both** the member identity `w` AND the member nullifier secret `k` (R2 P1e:
`k` MUST be signed, else a holder picks a fresh `k` per show to forge distinct nullifiers and bypass
one-show detection). `w` is the BLS12-381 scalar committed in the show anchor; `k` is the
member-chosen, blind-committed nullifier key. Encode `(w, k)` as a small-norm digit vector
`m ∈ R_q^ℓ`, `‖m‖_∞ ≤ B_m` (base-`β_m` digits packed into ring coefficients), with public linear
maps `Φ_w, Φ_k` such that `Φ_w(m) = w` and `Φ_k(m) = k` in both domains. `Φ_w` is what the
cross-domain bind (HYP-345) proves consistent with the show anchor; `Φ_k` is what ties the emitted
nullifier to the signed `k` (§3.4.5). (Exact packing: design sub-decision §3.6 D2.)

### 3.3 Issue — **BLIND** (DESIGN-review R1 P1a: must be blind)

⚠️ **Issuance MUST be blind**: the issuer learns neither `w` nor the member's nullifier secret. If
the issuer (= introducer) learned `w`, then since the show emits a nullifier deterministic in the
member's secret + epoch, the issuer could recompute every epoch's nullifier and **link every show to
the issuance** — breaking unlinkability even though the ZK show hides `w`. The introducer's
authorization ("I vouch for *this person*") happens at the **protocol layer** (the introducer
chooses to run the issuance protocol with an out-of-band-authenticated person), NOT by learning the
person's cryptographic secret. This is the standard reconciliation of "known issuer admits known
person" with "issuer cannot track." Blind GPV/preimage issuance is the JRS23 protocol — transcribe it.

Blind issuance protocol (2-move, JRS23-style):

1. **Member → Issuer:** a hiding commitment `Cm` to `(w, k)` (`k` = member-chosen nullifier secret,
   never revealed to anyone), plus a ZK proof that `Cm` is well-formed (each of `w, k` a valid
   small-norm encoding). ⚠️ R2 P1c: the issuance proof does **NOT** reference the show anchor `C_r`
   — if it did, the issuer could store `C_r` and match it to the eventual published show, defeating
   blindness even without learning `w, k`. `Cm` uses **fresh issuance-only randomness**, unlinkable
   to any show anchor. The show anchor is re-randomized **per show** (fresh `r`, fresh
   `C_r^(i) = w·g + r_i·h` — standard BBS-style presentation unlinkability), so the issuer never sees
   any value reused at show time. The member's claim "this is the right person" is established
   **out-of-band** at the protocol layer, not by linking `Cm` to a long-term on-chain anchor.
2. **Issuer:** picks a fresh tag `τ ∈ T` (invertible-difference set → unforgeability), and using
   `isk` blind-signs the committed message: samples a short `x` with `A_τ·x = u − D·m_Cm` where
   `m_Cm` is the committed small-norm encoding — **without** learning `(w, k)`. Uses
   `RingTrapdoorKey::sample_pre` on `A_τ`'s extended structure (reuses the shipped sampler).
3. **Member:** unblinds to obtain `σ = (τ, x)` on its own `(w, k)`; `‖x‖_∞ ≤ β_sig` (the shipped
   `CRED_RING_INF_NORM_BOUND` regime).

Unforgeability (EUF-CMA, even under blind queries): Module-SIS over `A` + the tag structure (no two
signatures share `A_τ`, so linearity attacks fail). **Transcribe the exact blind-issuance reduction
+ tag set + the well-formedness proof from JRS23.**

### 3.4 Show (prover — the deep ZK core)

Prove knowledge of `(τ, x, m, w, k, r)` such that `A_τ·x = u − D·m` under **some** attested
introducer key (R2 P1d — see §3.4.6), `‖x‖,‖m‖` small, `C_r^(i) = w·g+r_i·h` (fresh per-show
anchor), `Φ_w(m)=w`, `Φ_k(m)=k`, `N = k·H_G1(epoch)` — in statistical ZK. Structure:

1. **Decompose** `x`, `m`, and the hidden tag `τ` into bits (or base-`β` digits) `b`, all
   coefficients in a small set. `τ` is committed (NOT revealed — revealing a per-signature tag would
   itself link the show to its issuance), so it joins the witness.
2. **LNS commit** to `b` (Ajtai/BDLOP commitment, small-norm).
3. **Linear-relation proof** for the *linear* part of the signature equation. ⚠️ DESIGN-review R1
   P1b: for the DM-style `A_τ = [A | A·R + τ·G]` with hidden `τ`, the equation
   `A_τ·x = A·x₁ + A·R·x₂ + τ·(G·x₂) = u − D·m` is **NOT linear in the committed bits** — it carries
   the witness **product** `τ·(G·x₂)`. The linear proof covers only `A·x₁ + A·R·x₂ + D·m`; the
   product term is discharged in step 4.
4. **Product proof** — TWO obligations (both via the LNS product/quadratic machinery):
   - (a) `b·(b−1)=0` (exact binary), so the decomposition extraction is tight → extracted `x*` is a
     genuine short Module-SIS-valid signature (`< q`, no `2^k` gadget blowup).
   - (b) the **tag–signature product** `τ·(G·x₂)` (P1b): prove the committed `τ` times the committed
     `G·x₂` equals the committed cross-term, so the full `A_τ·x = u − D·m` is sound with `τ` hidden.
     (Alternative considered + rejected: a tag **set-membership** proof + revealing a re-randomized
     tag — rejected because revealing a unique per-signature tag links to issuance.)
   **This product proof is the hardest component and the long pole — it makes (C) both sound AND
   unlinkable. Transcribe from LNS (and the JRS23 show proof, which already includes the tag term).**
5. **Cross-domain bind + nullifier**: tie `b` (digits of `m`) to the show anchor via the shipped
   `bind.rs` shared-challenge same-value proof:
   - `Φ_w(m) = w` consistent with the per-show anchor `C_r^(i)` (membership of the *same* `w`), AND
   - the one-show **nullifier** `N = k·H_G1(epoch)` in the EC domain, where the show's ZK relation
     proves this `k` is the **SAME `k` signed into `m`** via `Φ_k` (R2 P1e). Because `k` is part of
     the signed message, a holder CANNOT pick a fresh `k` at show time to forge distinct nullifiers —
     one credential yields exactly one `N` per epoch. `k` is the blind-committed secret from §3.3, so
     the issuer never learns it and cannot recompute `N` (R1 P1a). For C3 this is the PQ lattice-PRF
     `nullifier_lwr.rs` (`N=round_p(a_epoch·w)`, Q6); the shipped EC `nullifier.rs` / `Nullifier` type
     (R2 P2) is the classical/BBS-half reference, superseded for the C3 PQ path.
6. **Issuer-hiding** (R2 P1d): the show must prove the signature verifies under **some** attested
   introducer key in the `epoch` anchor — NOT a specific `ipk`, or every verifier learns which
   introducer vouched (violating INTRODUCTION_RECORD §4.2 introducer anonymity). This MIRRORS the
   BBS half's verifier-side anonymity layer (the HYP-324 decision: epoch group/aggregate key, or ZK
   set-membership over the attested-introducer set). The lattice show adopts the SAME mechanism the
   BBS half adopts — not a separate one — so AND-verify hides the introducer in both halves. Concretely,
   the verified statement becomes "`σ` is valid under `ipk*` AND `ipk* ∈ EpochIntroducerSet`" with
   `ipk*` hidden, via the chosen anonymity layer. **Construction = HYP-324 (shared with BBS); this
   doc adopts its output.**

### 3.5 Verify + compose

`verify_lattice_show` checks the LNS proof (commitment opening, linear, product **incl. tag term**),
the bind to the per-show anchor `C_r^(i)`, the nullifier `N`, and **issuer-hiding** (validity under
the `epoch` introducer-set anchor, not a named `ipk` — R2 P1d). The full vouch verifier (shipped
`vouch.rs`) checks **BBS-show AND lattice-show**, both over the same per-show `C_r^(i)` and the same
`epoch` anchor, and returns the EC `N`. Everlasting anonymity: BBS statistical + LNS statistical ZK,
introducer hidden in both halves. PQ soundness: JRS23 EUF-CMA (Module-SIS).

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
// New module: vouch-crypto::lattice_cred  (built on ring_trapdoor + module_sis + bind + nullifier)

pub struct IssuerPublicKey { a: ..., d: ..., u: ..., tags: ... }   // ipk
pub struct IssuerSecretKey { trapdoor: RingTrapdoorKey }           // isk (wraps the shipped trapdoor)
pub struct LatticeSig { tag: RingElem, x: Vec<RingElem> }          // σ = (τ, x) — held by member only

// BLIND issuance (P1a): two moves. The issuer never learns (w, k) and never sees a show anchor (P1c).
pub fn keygen(n, m_bar, rng) -> (IssuerPublicKey, IssuerSecretKey)
pub struct IssueRequest { commitment, wellformed_proof }    // member → issuer; commits (w,k), NO C_r
pub struct BlindSignature { tag: RingElem, blinded_x: Vec<RingElem> }
pub fn request_issue(ipk, w: &Fr, k: &Fr, rng) -> (IssueRequest, BlindState)       // member (no C_r! P1c)
pub fn blind_sign(isk, req: &IssueRequest, rng) -> Result<BlindSignature, Error>   // issuer (no w,k)
pub fn unblind(st: BlindState, bsig: BlindSignature) -> LatticeSig                 // member; m signs (w,k)

// The show proof (the deep ZK core). Per-show fresh anchor (P1c); epoch introducer-set anchor (P1d);
// signed-k nullifier in the EC domain (P1e, P2).
pub struct EpochIntroducerAnchor { /* HYP-324 anonymity layer: group key OR set-membership root */ }
pub struct LatticeShowProof { commit, linear, product /* b∈{0,1} + tag term */, bind, issuer_hiding,
                              nullifier: Nullifier }
// fresh per show: r_i (anchor randomness) → c_r_i = w·g + r_i·h
pub fn show(sig, w: &Fr, k: &Fr, r_i: &Fr, c_r_i: &G1Affine, epoch_anchor: &EpochIntroducerAnchor,
            epoch: u64, rng) -> LatticeShowProof
pub fn verify_show(epoch_anchor: &EpochIntroducerAnchor, c_r_i: &G1Affine, epoch: u64,
                   proof) -> Result<Nullifier /*EC N=k·H_G1(epoch)*/, Error>
```

Notes: `verify_show` takes the **epoch introducer-set anchor**, not a single `ipk` (P1d). The show
anchor `c_r_i` is **fresh per show** (P1c). The nullifier is the existing EC `Nullifier` (`G1`),
keyed on the **blind, signed** member secret `k`
(not `w`) so the issuer cannot recompute it (P1a + P2). `show` takes `k` as a witness; the bind
proves the same `k` is in the credential and the same `w` is in `C_r`.

The full BlindedVouch (`vouch.rs`) gains a lattice-show field and AND-verifies it with the BBS half
over the shared `C_r` (this is where HYP-343's trait reshape lands).

---

## 5. Build plan (phased; each chunk: integration+smoke tests + Codex gate)

Ordered so each chunk is independently gate-clean and the hard core is isolated:

1. **`lattice_cred` skeleton + tag-based signature (clear-tag first)** — `keygen` + a NON-blind,
   clear-tag `sign`/`verify_sig` (non-ZK) reusing `ring_trapdoor::sample_pre` on the tag-shifted
   syndrome. This is a build-scaffold ONLY (not the real issuance — clear tag + non-blind are both
   insecure per R1); it validates the signature equation + sampler reuse in isolation. Tests:
   sign→verify, tag freshness, EUF-flavor (no-trapdoor forgery fails, linearity-combination fails).
2. **LNS witness commitment** (BDLOP/Ajtai) — commit + open, binding + hiding tests.
3. **LNS linear-relation proof** — the linear part `A·x₁ + A·R·x₂ + D·m` over committed small `b`.
   Dilithium-style masked proof on small witnesses (γ fits). Soundness/ZK tests.
4. **LNS product proof** — the hardest core, BOTH obligations: (a) `b·(b−1)=0` (tight extraction),
   (b) the tag–signature product `τ·(G·x₂)` (R1 P1b). Tests at threshold for each.
5. **Blind issuance** (R1 P1a) — `request_issue`/`blind_sign`/`unblind` so the issuer learns neither
   `w` nor `k`; the commitment well-formedness proof. Tests: correctness (unblinded σ verifies),
   blindness (issuer view independent of `w,k`), EUF under blind queries.
6. **Cross-domain bind + EC nullifier** — generalize `bind.rs` to bind `m`-digits to `C_r` AND tie
   the member secret `k`; emit the EC `Nullifier = k·H_G1(epoch)` (R1 P2). Same-value + one-show tests.
7. **Compose `show`/`verify_show`**; statistical-ZK + soundness + one-show-collision tests.
8. **Wire into `vouch.rs`** (AND-verify) + HYP-343 trait reshape; end-to-end vouch test.

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

---

## 8. DESIGN-review log

### Round 1 (Codex gpt-5.5/high, 2026-06-15) — 2×P1, 1×P2, all RESOLVED in this doc

- **P1a — non-blind issuance + public nullifier links shows to the issuer.** With the issuer =
  introducer learning `w`, and a nullifier deterministic in the member secret + epoch, the issuer
  could recompute every nullifier and link shows to issuance. **Resolution:** issuance is now
  **blind** (§3.3) — the issuer learns neither `w` nor the member nullifier secret `k`; the nullifier
  is keyed on the blind `k`, not `w` (§3.4.5, §4). Introducer authorization moves to the protocol
  layer (out-of-band-authenticated person), not knowledge of the secret.
- **P1b — hidden tag makes `A_τ·x` non-linear (`τ·(Gx₂)` product term).** A plain LNS linear proof
  cannot prove the signature equation when `τ` is hidden. **Resolution:** §3.4.4 now has the product
  proof discharge BOTH `b∈{0,1}` AND the tag–signature product `τ·(Gx₂)`; revealing a re-randomized
  tag was considered and rejected (a unique per-signature tag, if revealed, links to issuance).
- **P2 — nullifier domain mismatch (`RingElem` vs EC).** **Resolution:** §4 returns the shared EC
  `Nullifier` (`G1`), `N = k·H_G1(epoch)`, consistent with the existing vouch/nullifier plumbing.

These three caught pre-code validate the design-first discipline (the bar is us + the gate; missing
soundness/anonymity *mechanisms* are not deferrable — blind issuance and the tag product proof are
now first-class build chunks §5.4–5.5, not footnotes).

### Round 2 (Codex gpt-5.5/high, 2026-06-15) — 3×P1, all RESOLVED

- **P1c — issuance must not expose the show anchor.** Even blind, if issuance references the
  long-term `C_r`, the issuer stores it and matches the eventual show. **Resolution:** §3.3 issuance
  binds `(w,k)` via fresh issuance-only randomness, NOT `C_r`; the show anchor `C_r^(i)` is
  re-randomized per show (§3.2/§4). `request_issue` no longer takes `C_r`.
- **P1d — must not verify against an individual introducer key.** A single `ipk` de-anonymizes the
  introducer (violates INTRODUCTION_RECORD §4.2). **Resolution:** §3.4.6 + §3.5 — the show proves
  validity under the **epoch attested-introducer anchor**, mirroring the BBS half's HYP-324
  verifier-side anonymity layer (group key / set-membership). `verify_show` takes
  `EpochIntroducerAnchor`, not `ipk`. Construction = HYP-324, shared with BBS (not reinvented).
- **P1e — nullifier secret `k` must be bound into the signed relation.** Else a holder picks a fresh
  `k` per show, forging distinct nullifiers and bypassing one-show. **Resolution:** §3.2 — `k` is
  part of the signed message `m` (via `Φ_k`); §3.4.5 — the show proves the emitted `N` uses the
  SAME signed `k`.

Net effect of R1+R2: the construction now satisfies blindness, introducer anonymity, unlinkability,
PQ unforgeability, and one-show — the full INTRODUCTION_RECORD §4 property set — at the design level,
before any code. Six P1s caught pre-implementation.

---

## 9. EXACT construction (LOCKED reference — Jeudy PhD thesis Ch. 6–8 = ePrint 2024/131)

Reference obtained 2026-06-15: `refs/jeudy_thesis_2024.pdf` (+ `.txt`) — Corentin Jeudy's PhD thesis
"Design of Advanced Post-Quantum Signature Schemes", the journal-version superset of JRS23/2024-131.
eprint 403'd automated fetch; the author's GitHub Pages copy (`cjeudy.github.io/assets/pub/
manuscript.pdf`) is unblocked. This section transcribes the EXACT algorithms to implement — no longer
a sketch. **This validates the shipped trapdoor: thesis §6 signs `c = Ar + Dm` via the MP sampler
(Alg 4.1); §6.4 uses the elliptic sampler (Alg 4.5) = our Schur-complement `SamplePre`.**

### 9.1 SEP signature (thesis Alg 6.1–6.4 — the standard-model statistical signature)

Ring `R_q`, cyclotomic conductor `2n`, `n` power of two. Public params:
- `d` (M-SIS rank), `κ` splitting factors, prime `q ≡ 2κ+1 (mod 4κ)`, `k = ⌈log₂ q⌉`.
- Tag space `Tw = { t ∈ T₁ : ‖t‖₂ = √w }` — **binary** polys of fixed Hamming weight `w`, with
  `t ∈ R_q^×` and *differences of distinct tags also units* (the `q` condition guarantees this; this
  is what defeats forgery-by-linearity). `w` chosen so `|Tw| ≥ Q` (#sig queries).
- `m1 = ⌈d·log₃ q + f(λ)⌉` (commitment-randomness dim), `m` (message dim).
- `G = I_d ⊗ [1|2|…|2^{k-1}] ∈ R_q^{d×dk}` (binary gadget, base 2).
- Gaussian widths: `r̄ = η_ε(Z) = 5.4`; `s = r̄·√5·(√(nm1)+√(ndk)+t_slack)+1` (preimage width);
  `s2` (commitment randomness width), `s1 = √(s² + s2²)`.
- `A ← U(R_q^{d×m1})` **random, NO trapdoor on A** (so the commitment stays hiding); `u ← U(R_q^d)`;
  `D ← U(R_q^{d×m})` (message commitment key). All NUMS from a 32-byte seed.

**KeyGen (6.2):** `R ← U(S₁^{m1×dk})` (ternary, `‖R‖₂ ≤ √(nm1)+√(ndk)+t_slack`); `B = A·R mod qR`.
`pk = B`, `sk = R`. (The MP trapdoor is for `[A | tG − B] = [A | tG − AR]`, secret `R`.)

**Sign (6.3)** message `m ∈ T₁^m` (binary), stateful tag:
1. `r ← D_{R^{m1}, s2}`;  2. `c = Ar + Dm mod qR`;  3. `t = F(st) ∈ Tw` (Fisher–Yates from counter, Alg 8.1);
4. `v = MP-Sampler(R; A, u+c, t·I_d, s, r̄√5) − [r; 0_{dk}]`;  5. `st++`.  `sig = (t, v)`.

**Verify (6.4):** `A_t = [A | tG − B] ∈ R_q^{d×(m1+dk)}`; parse `v = [v1; v2]` (`m1`, `dk`);
check `‖v1‖₂ ≤ B1 = s1√(nm1)`, `‖v2‖₂ ≤ B2 = s√(ndk)`, `A_t·v = u + Dm mod qR`, `t ∈ Tw`.

Note vs our shipped `ring_trapdoor` (`[Ā | G − ĀR]`, relation `A·[R;I]=G`): SEP generalizes to
`[A | tG − AR]` (relation `A_t·[R;I] = tG`) — the §5.1 chunk adds the **tag** `t` and the random
shared `A` to the shipped sampler. The norm checks are **ℓ₂** (not ℓ∞) — match this.

### 9.2 Anonymous-credential show + blind issuance (thesis Ch. 7) — uses [LNP22]

- ZK system = **[LNP22]** (Lyubashevsky–Nguyen–Plançon, CRYPTO 2022) — tackles **quadratic relations
  + exact ℓ₂-norm constraints**. This is the §5.4 product-proof framework (replaces the LNS20/21
  guess in §2). The tag-membership `t ∈ Tw` and the signature relation `A_t·v = u+Dm` are proven in it.
- `OblSign` (7.1) + `Issue` (7.5): **blind issuance** — the user commits the hidden message, proves
  well-formedness, the issuer obliviously signs (MP-samples) without learning `m`. Matches §3.3 (P1a).
- `Prove` (7.2): the **show** — a [LNP22] argument of knowledge of `(t, v, m)` with `A_t·v = u+Dm`,
  `v` short (ℓ₂), `t ∈ Tw`, and `m` opening the shown commitment. Matches §3.4; binds to `C_r` via the
  message-commitment slot (our HYP-345 cross-domain layer on top).
- §8 gives concrete params + the Fisher–Yates `F` (Alg 8.1).

### 9.3 Transcription order (refines §5 with thesis algorithm numbers)

1. **§5.1 SEP signature** ← thesis Alg 6.1–6.4 (+ elliptic sampler 4.5 already shipped). Tag space
   `Tw` + Fisher–Yates `F` (Alg 8.1). Tests: sign→verify, tag-difference-is-unit, EUF-flavor.
2. **§5.2 BDLOP commitment** ✅ shipped (the [LNP22] ansatz commitment).
3. **[LNP22] argument** (the deep core) ← thesis §7.4 / ePrint 2022/284: linear + quadratic + exact
   ℓ₂-norm. This is `Prove`/`Verify` (Alg 7.2) and the long pole. Fetch 2022/284 next (same GitHub
   Pages route if eprint blocks).
4. **Blind issuance** ← Alg 7.1/7.5 (incl. issuance-time registration `D_s·s=upk`). 5. **Cross-domain
   bind + `w`-keyed nullifier** ← the NEW PQ lattice-PRF nullifier `nullifier_lwr.rs` (Q6 decision;
   `N=round_p(a_epoch·w)`) + the cross-ring anchor bind (`ANCHOR_BIND_DESIGN.md`, `bind.rs` as the
   template). ⚠️ NOT the classical-only EC `nullifier.rs` — Q6 supersedes it for C3 (it gives no PQ
   one-show soundness); `nullifier.rs` remains only the EC/BBS-half reference.
6. **Issuer-hiding wrapper (HYP-324)** — the gate for live use; the public-`vk_pub` core is TEST-ONLY
   until this lands (else a live vouch verifies against a named key, revealing the introducer). 7.
   **Compose + wire into `vouch.rs`** (HYP-343) — ONLY after the issuer-hiding wrapper. ⚠️ The detailed
   authoritative order is `LNP22_SHOW_DESIGN.md` §4 (chunks 5.0–5.10); this is the summary.

### 9.4 ⚠️ FOUNDATIONAL FINDING — the credential needs its OWN modulus (NOT the shipped ring's)

Verified 2026-06-15: the shipped `ring.rs` uses `q = 8380417 ≡ 1 (mod 2n=512)`, so `X^256+1` splits
**fully** into 256 linear factors. But SEP's unforgeability requires `q ≡ 2κ+1 (mod 4κ)` with **small
κ** (LIMITED splitting), so that binary tags `Tw` AND their pairwise differences are units in `R_q`
(thesis Lemma 1.4 / Remark 1.2 / §6.2.2). Under full splitting a binary poly can be a zero-divisor →
the tag mechanism breaks. **Therefore the lattice credential (`lattice_cred`) is a SEPARATE ring
instance with a SEP-compatible modulus — it does NOT reuse `module_sis`/`ring.rs`'s `q`.** Consequences:
- a new ring module (or a generic ring parameterized by `q`, `n`, `κ`) with the SEP modulus;
- **ring inversion** `t^{-1}` is needed (tag-scaled gadget `tG`: `SampleG_t(v) = SampleG(t^{-1}·v)`);
  with limited splitting this is per-CRT-slot once an NTT exists, or extended-Euclid over `R_q` meanwhile;
- norm bounds are **ℓ₂** (`B1 = s1√(nm1)`, `B2 = s√(ndk)`), not the ℓ∞ our current sampler tests use;
- concrete SEP params (`d, κ, q, w, m1, m`, widths) come from thesis Ch. 8 — transcribe, don't invent.

This means the shipped `ring_trapdoor` (q=8380417) validated the *sampler math* (Schur-complement
elliptic perturbation) but the credential ring is re-instantiated at the SEP modulus. The sampler
algorithm ports; the modulus + tag + inversion + ℓ₂ are the §5.1 deltas.
