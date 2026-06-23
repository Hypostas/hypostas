# [LNP22] ZK Show Proof — Sub-Design (the C3 lattice-credential long pole)

**Status:** DESIGN (design-first; Codex DESIGN-review pending)
**Issue:** HYP-352 item 1 (C) chunk 5 — the anonymous ZK *show* of the SEP credential
**Author:** Iris · 2026-06-15
**Parent:** `LATTICE_SIG_PROTOCOLS_DESIGN.md` (§9). **Reference:** `refs/jeudy_thesis_2024.pdf` §7.4
(= ePrint 2024/131) + LNP22 (Lyubashevsky–Nguyen–Plançon, CRYPTO 2022, ePrint 2022/284).

---

## 0. Summary

The SEP lattice credential SIGNATURE is shipped + gate-clean (`sep_ring`/`sep_tag`/`sep_gadget`/
`sep_trapdoor`/`sep_sig`): `keygen → sign → verify`, `A_t·v = u + Dm`, `A_t = [A | tG − B]`. This
sub-design covers the **show** — a statistical-ZK, PQ-sound argument of knowledge of a credential
`(t, v, s, m)` *without revealing it*, bound to the EC anchor `C_r`. It is the construction's **long
pole**: the [LNP22] framework has **no public implementation**, so this is a faithful transcription
from thesis §7.4 (which details LNP22 for exactly this circuit) + ePrint 2022/284. Multi-session.

---

## 1. The statement to prove (from SEP.Verify + registration)

Per thesis §7.1.1 / §7.3, each user has a key pair `(upk = D_s·s, usk = s)` with `s ∈ T₁^{2d}`
(uniform binary — high-entropy). `s` is a SIGNED attribute, so the effective message is `[s | m]`
under commitment matrix `[D_s | D]`. The show is a Fiat–Shamir argument of knowledge of
`(t, v, s, m)` such that:

1. **Signature** (SEP.Verify, §6.2): `[A | tG − B]·v = u + D_s·s + D·m (mod p)`.
   - ⚠️ This is **NOT linear** in the witness: `tG·v₂` is a **product** of two committed witnesses
     `t` and `v₂` → a **quadratic relation** (thesis §7.4 line "quadratic relation because of tGv₂").
2. **Short `v`** (ℓ₂): `‖v₁‖₂ ≤ B1`, `‖v₂‖₂ ≤ B2` — **exact-ℓ₂-norm** proofs (LNP22's quadratic
   machinery proves exact ℓ₂ bounds; the extracted witness is a genuine short solution).
3. **Tag** `t ∈ Tw`: binary, fixed Hamming weight `w` — a membership/structure constraint (binary
   coeffs = quadratic `t∘t = t`; weight = a linear sum).
4. **Binary message** `m, s ∈ T₁`: `m∘m = m`, `s∘s = s` (quadratic binary constraints).
5. **Registration**: knowledge of `s` with `D_s·s = upk` (linear).
6. **Issuer-hiding** (R2 P1d, parent §3.4.6): the proof is under the **epoch attested-introducer
   anchor**, not a named `ipk` — HYP-324 verifier-side anonymity layer, shared with the BBS half.
7. **Cross-domain bind + nullifier** (HYP-345). ⚠️ DESIGN-review R3 P1b: the nullifier key is the
   **EC scalar `w`**, NOT the lattice registration secret `s`. Distinguish them:
   - `w ∈ F_r` (BLS12-381 scalar) — the **member identity**, committed in `C_r = w·g + r·h` (EC) AND
     encoded as its **binary digits** in the lattice message `m` (`m = bits(w)`, `T₁`). The
     cross-domain bind (HYP-345: digit decomposition + shared challenge) proves *the same `w`* is in
     `C_r` and is `m`'s digit-encoding — `w`'s digits are literally the lattice message, so there is
     **no `s→F_r` map and no hash/compression** (the very risk R3 P1b flags). The nullifier is
     `N = w·H_G1(epoch)` over the EC `w` (the shipped `nullifier.rs` Schnorr-AND proves the `N`-`w`
     equals the `C_r`-`w`; the show additionally proves that `w` equals `m`'s digits via the bind).
   - `s ∈ T₁^{2d}` (binary, lattice-only) — the **thesis registration secret** (impersonation
     prevention, `upk = D_s·s`). It is signed + proven-known, but it is **not** the nullifier key and
     is never mapped to `F_r`.
   Identity-hiding + unlinkability hold because (a) `w` is full-entropy (the bind uses FULL `DIGITS`,
   not the toy 32 — resolves the R2 P1e/§nullifier brute-force gap), and (b) blind issuance
   (`OblSign`) hides `m = bits(w)` from the issuer, so it cannot recompute `N`.

So the show is a single LNP22 proof over: **linear** parts (the `A`,`D_s`,`D` terms, registration,
tag weight) + **quadratic** parts (`tG·v₂`, binary `t∘t=t`/`m∘m=m`/`s∘s=s`) + **exact-ℓ₂-norm**
(`‖v₁‖,‖v₂‖`), all over committed witnesses, made non-interactive by Fiat–Shamir.

---

## 2. LNP22 building blocks (to transcribe — thesis §7.4 / ePrint 2022/284)

The framework proves, for committed `s₁` (short) and `m` (arbitrary), statements combining:
- **(a) ABDLOP commitment** — the LNP22 commitment: an **A**jtai part (Module-SIS-binding, for the
  short witness `s₁`) fused with a **BDLOP** part (for the unbounded part `m`). Our shipped `bdlop`
  is the BDLOP half; chunk 5.1 extends it to **ABDLOP**. (Thesis §7.4 / LNP22 §2.)
- **(b) Challenge space** (§7.4.1) — challenges `c` from `C = {c ∈ R : ‖c‖∞ ≤ ρ, ‖c‖₁-like ≤ η}`
  (thesis Ch8: `ρ=8`, `η=93`), with invertible differences (the modulus `q̂` splitting governs this).
  `|C| ≥ 2^λ`; soundness amplified `ℓ=7` times (`q̂min^{-ℓ} ≤ 2^-λ`).
- **(c) Linear-relation proof** — prove public linear relations over the committed witness (Dilithium-
  style masked opening + rejection sampling; our `module_sis` is this shape).
- **(d) Quadratic-relation proof** — prove `f(witness) = 0` for quadratic `f` (the `tG·v₂` product,
  the binary constraints). Uses LNP22's automorphism/NTT-slot "garbage term" technique. **The hardest
  component.**
- **(e) Exact-ℓ₂-norm proof** — prove `‖x‖₂² ≤ β²` exactly via a quadratic relation (a squared-norm
  evaluation), so the extracted witness norm is tight (no gadget blow-up). (Thesis §6.4 / §7.4.)
- **(f) Fiat–Shamir** — non-interactive in the ROM; repeats until a non-aborting transcript (rejection
  sampling). Yields a signature-of-knowledge (binds the message/epoch/C_r).

The proof modulus is `q̂ = q·q1` (thesis Ch8: `q=425837` the SEP modulus, `q1≈2^19=524269`,
`q̂≈2^37.7`); proof-system ring degree `n̂=64`, subring embedding `k̂=4`, Ajtai rank `d̂≈20`; mask
widths `σ1,σ2,σ3`; transcript ≈ 80 KB. All PROVISIONAL (HYP-330).

---

## 3. Interface (Rust, behind `experimental-unaudited`)

```text
// New module(s): vouch-crypto::lnp22  (+ extend bdlop → abdlop)

pub struct AbdlopParams { /* Ajtai block (binding) + BDLOP block (hiding) */ }
// ⚠️ R2 P1: challenges live in the PROOF ring R_q̂ (degree n̂=64, modulus q̂=q·q1), NOT the SEP ring
// R_p — the LNP22 challenge distribution + invertible-difference property are defined there. A
// dedicated proof-ring element type is a build prerequisite (chunk 5.0).
pub struct ProofRingElem { /* Z_q̂[X]/(X^{n̂}+1), n̂=64, q̂=q·q1 */ }
pub struct Challenge { c: ProofRingElem }          // ‖c‖∞≤ρ, ‖c‖1-like≤η, from C ⊂ R_q̂
pub fn sample_challenge(transcript_hash) -> Challenge

// The LNP22 sub-proofs over an ABDLOP commitment to the witness:
pub struct LinearProof   { ... }                  // (c) public linear relations
pub struct QuadraticProof{ ... }                  // (d) quadratic relations (tGv₂, binary)
pub struct NormProof     { ... }                  // (e) exact ℓ₂ bounds

// The composed credential show. ⚠️ R2 P2b: the verifier input is ONLY the epoch
// introducer-set anchor — NOT a named SepVerifyKey. The individual issuer key ipk* is a HIDDEN
// witness proven ∈ the anchor (issuer-hiding, §1.6). The PROVER holds ipk* (+ its own credential).
pub struct ShowProof { commit, linear, quadratic, norm, bind, issuer_hiding, nullifier: Nullifier }
pub fn show(ipk_star: &SepVerifyKey, epoch_anchor: &EpochIntroducerAnchor,
            sig: &SepSignature, s, m_bits_w, w, r_i, c_r_i, epoch, rng) -> ShowProof
pub fn verify_show(epoch_anchor: &EpochIntroducerAnchor, c_r_i, epoch, proof)
    -> Result<Nullifier, Error>
```

`show` proves §1's statement in ZK (the prover knows `ipk*` + its credential); `verify_show` takes
ONLY the `epoch_anchor` (no named issuer key — issuer-hiding, R2 P2b), checks the ABDLOP opening +
linear + quadratic + norm + bind + nullifier + the `ipk* ∈ anchor` membership, and returns the EC
`N`. Then `vouch.rs` AND-verifies it with the BBS half over the shared `C_r^(i)`/epoch (HYP-343).

---

## 4. Build plan (chunk-by-chunk, each: tests + Codex gate)

0. **5.0 Proof ring `R_q̂`** (R2 P1) — a new ring instance `Z_q̂[X]/(X^{n̂}+1)`, `n̂=64`, `q̂=q·q1`
   (`q1≈2^19`), with the lift `R_p → R_q̂` (thesis: "lift the equation to `R_q̂`"). Distinct from
   `sep_ring`; challenges + the LNP22 proof live here. Arithmetic + inversion (for the
   invertible-difference challenge property). Tests: arithmetic, lift correctness, inversion.
1. **5.1 ABDLOP commitment** — extend `bdlop` to the Ajtai+BDLOP fused commitment (binding for the
   short block, hiding for the message block) over `R_q̂`. Tests: opening, binding, hiding, homomorphism.
2. **5.2 Challenge space** (§7.4.1) — sample `c ∈ C ⊂ R_q̂` (`ρ,η` bounds); invertible-differences
   property; `|C| ≥ 2^λ`. Tests: bounds, difference-invertibility.
3. **5.3 Linear-relation proof** — masked opening + rejection sampling over ABDLOP; soundness/ZK.
4. **5.4 Quadratic-relation proof** — the garbage-term/automorphism technique for `f(witness)=0`
   (the `tGv₂` product + binary constraints). **The long pole within the long pole.** Threshold tests.
5. **5.5 Exact-ℓ₂-norm proof** — squared-norm-as-quadratic; tight extraction. Tests at the bound.
6. **5.6 Compose `show`/`verify_show`** — assemble §1's statement; Fiat–Shamir; statistical-ZK +
   soundness + completeness tests (honest credential shows verify; forgeries/tampering rejected).
7. **5.7 Cross-domain bind + `w`-keyed nullifier** — generalize `bind.rs` to prove the lattice
   message `m = bits(w)` is the digit-encoding of the EC `C_r`'s scalar `w` (HYP-345), and emit
   `N = w·H_G1(epoch)` over that same `w` (shipped `nullifier.rs` Schnorr-AND). FULL `DIGITS` (not the
   toy 32) so `w` is full-entropy (resolves R2 P1e). `s` is separately proven-known, not the key.
8. **5.8 Blind issuance** (`OblSign`, Alg 7.1) — user commits `c = A·ru + D_s·s + D·m` + proves the
   opening (5.3); signer `EllipticSampler`s; user unblinds. (Reuses 5.1–5.3.)
9. **5.9 Wire into `vouch.rs`** — AND-verify the lattice show with the BBS half (HYP-343, retire
   `StubVouchScheme`); end-to-end vouch test.

Realistic: 5.4 (quadratic) + 5.5 (norm) are the research-grade core; expect multiple careful gated
sub-chunks each. No public LNP22 impl ⇒ faithful transcription throughout (thesis §7.4 is the source).

---

## 5. Open questions for the DESIGN-review

- **Q1 — proof ring vs SEP ring.** The proof works over a degree-`n̂=64` subring with modulus
  `q̂ = q·q1`; the SEP signature is over degree-256 `R_p`. Confirm the embedding (`k̂=4`,
  `n = n̂·k̂ = 256`) and that the show lifts the SEP relation into `R_{q̂}` correctly (thesis: "lift
  the equation to `R_{q̂}`").
- **Q2 — statistical vs computational ZK.** LNP22 is honest-verifier ZK with rejection sampling;
  confirm the everlasting-anonymity requirement (parent §3.6 D6) is met (the show hides the witness
  statistically) — or flag the exact guarantee.
- **Q3 — quadratic-proof variant.** Which LNP22 quadratic technique (automorphism vs NTT-slot
  garbage) to transcribe — proof size vs pure-Rust implementability (no NTT yet for `q̂`; may need a
  partial NTT or schoolbook at the proof modulus).
- **Q4 — nullifier key.** RESOLVED in §1.7 (DESIGN-review R3 P1b): the key is the EC scalar `w` (not
  the lattice secret `s`); `m = bits(w)` is the lattice digit-encoding, cross-domain-bound to `C_r`'s
  `w` (no `s→F_r` map). Remaining to confirm at build: the FULL `DIGITS` width for `w` (so the bind
  covers a full `F_r` element) + its proof cost.
- **Q5 — params.** Lock the provisional Ch8 params (`n̂,k̂,d̂,q1,ρ,η,σ_j,ℓ`) + the resulting
  bit-security (M-SIS/M-ISIS/M-LWE) and proof size (HYP-330).

---

## 6. Grounding — what's already shipped this lands on

Gate-clean: `sep_ring` (+inversion), `sep_tag`, `sep_gadget`, `sep_trapdoor` (incl. the
Schur-complement perturbation), `sep_sig` (sign/verify + public `SepVerifyKey`), `bdlop` (the BDLOP
half of ABDLOP), `module_sis` (the Dilithium-style masked-opening shape 5.3 reuses), `bind`/
`nullifier`/`bbs` (the EC half + cross-domain + AND-verify). The show is the last major component
before the C3 dual-hybrid `BlindedVouch` is end-to-end.

---

## 7. DESIGN-review log

### Round 1 (Codex gpt-5.5/high, 2026-06-15) — 2×P1, both RESOLVED

- **P1a — obsolete shipped-modulus construction.** `LATTICE_SIG_PROTOCOLS_DESIGN.md` §3 still
  described the construction over the shipped `q=8380417` ring, contradicting §9.4 (which requires the
  separate `p=425837` SEP ring for tag unforgeability). **Resolution:** §3 (and its §4 interface) now
  carry a ⚠️ SUPERSEDED-by-§9 banner; the authoritative construction is §9 + this doc.
- **P1b — undefined vector→`F_r` nullifier binding.** The draft keyed the nullifier on the lattice
  binary vector `s`, but `N = k·H_G1` needs an `F_r` scalar. **Resolution:** §1.7 now keys the
  nullifier on the EC scalar `w` (the member identity, in `C_r`), with `m = bits(w)` the lattice
  digit-encoding cross-domain-bound to `C_r` — no `s→F_r` map, no hash/compression. `s` is kept as the
  separate lattice registration secret (proven-known, never the key). Q4 updated.

### Round 2 (Codex gpt-5.5/high, 2026-06-15) — 1×P1, 2×P2, all RESOLVED

- **P1 — challenges in the proof ring.** `Challenge` was `SepRingElem` (degree-256 SEP ring), but
  LNP22 challenges live in `R_q̂` (degree `n̂=64`, `q̂=q·q1`) — using the SEP ring breaks the challenge
  distribution + invertible-difference soundness. **Resolution:** §3 introduces `ProofRingElem` over
  `R_q̂`; build chunk **5.0** adds the proof ring + the `R_p → R_q̂` lift before everything else.
- **P2a — parent nullifier inconsistency.** Parent §1.1 still said signature on `(w,k)` + `N=k·H_G1`.
  **Resolution:** parent §1.1 updated to the EC-scalar `w` key + `m = bits(w)` (matching §1.7); the
  separate `k` is dropped (full-entropy `w` via full-`DIGITS` bind + blind issuance does the job).
- **P2b — verifier issuer-anonymity.** `verify_show` took a named `SepVerifyKey`, revealing the
  introducer. **Resolution:** §3 — `verify_show` takes ONLY the `EpochIntroducerAnchor`; the issuer
  key `ipk*` is a hidden witness the prover proves `∈ anchor` (the prover holds `ipk*`).
