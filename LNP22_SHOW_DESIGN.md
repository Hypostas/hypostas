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
   - ⚠️ DESIGN-review R3 P1: this relation holds **mod `p`**, but the LNP22 proof runs **mod `q̂ =
     p·q1`**. `R_p → R_q̂` is NOT a homomorphic embedding (only the reduction `R_q̂ → R_p` is natural).
     So the proven relation is `[A | tG − B]·v − (u + D_s·s + D·m) = p·z (mod q̂)` for an additional
     **committed, bounded quotient witness `z`** — the LNP22 lift must carry + prove `z` (and its
     bound), or honest signatures are rejected mod `q̂`. `z` joins the witness/commitment.
2. **Short `v`** (ℓ₂): `‖v₁‖₂ ≤ B1`, `‖v₂‖₂ ≤ B2` — **exact-ℓ₂-norm** proofs (LNP22's quadratic
   machinery proves exact ℓ₂ bounds; the extracted witness is a genuine short solution).
3. **Tag** `t ∈ Tw`: binary, fixed Hamming weight `w` — a membership/structure constraint (binary
   coeffs = quadratic `t∘t = t`; weight = a linear sum).
4. **Binary message** `m, s ∈ T₁`: `m∘m = m`, `s∘s = s` (quadratic binary constraints).
5. **`s` is a hidden SIGNED attribute** (not re-checked against `upk` here). ⚠️ DESIGN-review R7 P2a:
   registration (`D_s·s = upk`, proving the user knows their secret) is an **ISSUANCE-time** check
   (`OblSign`/`UKeyGen`, where `upk` IS public to the issuer) — NOT a show input. Putting `upk` in the
   show would de-anonymize the user, and without it the relation is vacuous; so the show proves only
   that the signed `s` is the same `s` bound under the credential (via the signature relation), with
   `s` hidden. Impersonation-prevention is enforced at issuance (§1.7 / chunk 5.8), not at show.
6. **Issuer-hiding** — ⚠️ DESIGN-review R5 P1: this is a LAYERED concern, deferred to **HYP-324**
   (shared with the BBS half), NOT resolved in this sub-design. The **core show** (chunks 5.0–5.7)
   proves §1.1–5 + bind + nullifier under a **PUBLIC issuer/epoch verification key** — so the SEP
   matrices `A,B,u,D_s,D` are public constants and the relation above is tractable. Issuer-hiding
   (hiding *which* introducer) is then the HYP-324 wrapper, with two known shapes:
   - **(a) shared/aggregate epoch key** (HYP-324 candidate a): all attested introducers verify under
     ONE public epoch key, so the matrices stay **public constants** and this sub-design's relation is
     UNCHANGED; anonymity comes from the sharing/aggregation (a PQ aggregatable/threshold sig or
     group-sig-with-blind-issuance — the research-heaviest path). **Preferred — keeps LNP22 tractable.**
   - **(b) committed-key + accumulator membership**: the issuer key is a hidden witness proven `∈` an
     accumulator of attested keys; then `A·v₁, B·v₂, D·m` become **witness×witness quadratics** — a
     materially heavier LNP22 relation (extra quadratic terms + the membership proof).
   Until HYP-324 locks (a) or (b), the buildable target is the core show under a public key (the first
   cut may use a named `ipk`, non-anonymous; (a) then swaps in the epoch key with no relation change).
7. **Cross-domain bind + nullifier** (HYP-345). ⚠️ DESIGN-review R3 P1b: the nullifier key is the
   **EC scalar `w`**, NOT the lattice registration secret `s`. Distinguish them:
   - `w ∈ F_r` (BLS12-381 scalar) — the **member identity**, committed in `C_r = w·g + r·h` (EC) AND
     encoded as its **binary digits** in the lattice message `m` (`m = bits(w)`, `T₁`). The
     cross-domain bind (HYP-345: digit decomposition + shared challenge) proves *the same `w`* is in
     `C_r` and is `m`'s digit-encoding — `w`'s digits are literally the lattice message, so there is
     **no `s→F_r` map and no hash/compression** (the very risk R3 P1b flags). The nullifier is
     the nullifier `N = F^lat_w(epoch)` over that same `w` (the **PQ lattice PRF** — see NULLIFIER
     CONSTRUCTION below; the show proves `N` is the PRF of the `w` that equals `m`'s digits via the bind).
     ⚠️ DESIGN-review R8 P1: `bits(w)` MUST encode the **canonical** field representative
     `0 ≤ w < Fr::MODULUS` — the EC side only sees the digit-value mod `r`, so without a canonical
     constraint a non-canonical encoding (e.g. `w + r`, or any value `≥ r`) would be a DIFFERENT
     signed lattice message that maps to the SAME `C_r`/`N` (malleability ⇒ a second valid credential
     for one identity / nullifier collisions). The bind therefore fixes the bit width to
     `⌈log₂ r⌉ = 255` bits AND **range-proves `digit-value < Fr::MODULUS`** (the standard "less-than-a-
     constant" decomposition, done in the LNP22 quadratic layer). Same constraint applies at issuance.
   - `s ∈ T₁^{2d}` (binary, lattice-only) — the **thesis registration secret** (impersonation
     prevention, `upk = D_s·s`). It is signed + proven-known, but it is **not** the nullifier key and
     is never mapped to `F_r`.
   Identity-hiding + unlinkability require: (a) ⚠️ R10 P2 — `w` MUST be **generated uniformly at
   random in `F_r`** (`UKeyGen` samples `w ← U(F_r)`; full *width* ≠ full *entropy*), and (b) blind
   issuance (`OblSign`) hides `m = bits(w)` from the issuer.

   **NULLIFIER CONSTRUCTION — Q6 DECIDED = (ii) PQ lattice PRF** (Josh, 2026-06-15). The nullifier is
   `N = F^{lat}_w(epoch)` — a **post-quantum (lattice) keyed PRF** evaluated on the epoch, keyed by the
   member scalar `w`, NOT the EC `N = w·H_G1(epoch)`. Rationale + the exact guarantee:
   - ⚠️ **Framing correction (was mis-stated R10 P1):** a *deterministic*, `w`-keyed nullifier can
     NEVER be everlasting-(unbounded)-unlinkable — an unbounded adversary brute-forces the finite-
     entropy `w`, recomputes `N=f(w,·)`, and links. So "everlasting nullifier" is impossible by
     construction; the achievable maximum is **PQ-computational** unlinkability. The EC nullifier gives
     only **classical**-computational (a future QC solves the DLP, recovers `w`, links the introduction
     graph across epochs). We choose the lattice PRF to reach **PQ-computational** — consistent with
     the PQ-soundness ambition (a QC must not forge a vouch AND must not de-anonymize the introduction
     graph). Everlasting anonymity remains for the SHOW/membership (statistical ZK); the nullifier is
     PQ-computational (the honest, maximal claim for a deterministic nullifier).
   - **Construction:** a PQ keyed PRF `F^{lat}: (w, epoch) ↦ N`. Candidate = a key-homomorphic /
     rounded Ring-LWE PRF (Banerjee–Peikert–Rosen / BP14), chosen for ZK-friendliness at build (the
     rounding is the cost). The LNP22 show proves, in-circuit, that `N = F^{lat}_w(epoch)` for the
     **same `w`** bound in `C_r`/`m=bits(w)` — so the emitted `N` is consistent + unforgeable, and the
     proof reveals nothing about `w`. One-show holds (deterministic in `(w,epoch)`); cross-epoch
     unlinkability is PQ-computational (PRF pseudorandomness).
   - **Shared with the BBS half:** the vouch carries ONE nullifier `N`; switching it to `F^{lat}` fixes
     both halves at once. The shipped EC `nullifier.rs` is SUPERSEDED for the C3 vouch by the lattice
     PRF nullifier (a new build component — see chunk 5.7). This is the Q6 crypto-sign-off outcome.

So the show is a single LNP22 proof over: **linear** parts (the `A`,`D_s`,`D` terms of the signature
equation + the tag weight; NOT a `upk`-registration check — that is issuance-time, §1.5/R7 P2a) +
**quadratic** parts (`tG·v₂`, binary `t∘t=t`/`m∘m=m`/`s∘s=s`, and the canonical-range constraint on
`m=bits(w)`, R8 P1) + **exact-ℓ₂-norm** (`‖v₁‖,‖v₂‖`), all over committed witnesses, made
non-interactive by Fiat–Shamir.

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

The proof modulus is `q̂ = q·q1` (thesis Ch8: `q=425837` the SEP modulus). ⚠️ **The SHOW needs a
HYP-330-calibrated `q̂` of the ~2^57.7 magnitude class** (NOT the illustrative `q1=549755813869`, which
FAILS the ZK bound — see the bounds section) (Table 7.1 / §5.6 — the mask widths `σ1,σ2,σ3` and ZK norm
bounds are sized for this). The current build is bootstrapped over the **issuance** modulus
`q1=524269≈2^19` (`q̂≈2^37.7`) **as scaffolding only** (caps provable dims via
`proof_show::norm_bounds_provable`'s `B²<q̂` guard); the flip to the show modulus is **HYP-330**,
pre-mainnet. Proof-system ring degree `n̂=64`, subring embedding `k̂=4`, Ajtai rank `d̂≈20`; transcript
≈ 80 KB. All PROVISIONAL (HYP-330).

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

// The composed credential show. ⚠️ R5 P1: the CORE show verifies under a PUBLIC issuer/epoch verify
// key `vk_pub` (so the SEP matrices A,B,u,D_s,D are public constants and the §1.1 relation is
// tractable). Issuer-hiding (which introducer) is the HYP-324 wrapper (§1.6): under candidate (a)
// `vk_pub` IS the shared epoch key (anonymous, relation unchanged); under (b) the key is committed +
// proven ∈ an accumulator, adding quadratic terms. The first buildable cut uses a named public key.
// Q6=(ii): the nullifier is a PQ LATTICE-PRF output `N = F^lat_w(epoch)` (a canonical digest), NOT an
// EC G1 point — and the show proves `N` is that PRF of the bound `w` (a relation in the LNP22 proof).
pub struct LatticeNullifier { /* canonical bytes of F^lat_w(epoch) */ }
pub struct ShowProof { commit, linear, quadratic /* incl. p·z carry + PRF-eval relation */, norm,
                       bind, nullifier: LatticeNullifier }
pub fn show(vk_pub: &SepVerifyKey, sig: &SepSignature, s, m_bits_w, w, r_i, c_r_i, epoch, rng) -> ShowProof
pub fn verify_show(vk_pub: &SepVerifyKey, c_r_i, epoch, proof) -> Result<LatticeNullifier, Error>
// HYP-324 wrapper (later): swap vk_pub → EpochIntroducerAnchor; add the issuer-key-membership proof.
```

`show` proves §1's statement in ZK under the public `vk_pub` (incl. `N = F^lat_w(epoch)` for the bound
`w`); `verify_show` checks the ABDLOP opening + linear + quadratic (incl. the `p·z` carry + the PRF
eval) + norm + bind + nullifier, and returns the PQ lattice nullifier `N`. The
**issuer-hiding wrapper is HYP-324** (§1.6), layered on top without changing this core relation under
candidate (a). ⚠️ `verify_show(vk_pub, …)` is **TEST-ONLY** (named key ⇒ reveals the introducer). The
**live `vouch.rs` path consumes ONLY the HYP-324-wrapped, issuer-hidden proof** (epoch anchor) and
AND-verifies it with the BBS half over the shared `C_r^(i)`/epoch — never the public-key core (chunk
5.9 gates 5.10; see §4).

---

## 4. Build plan (chunk-by-chunk, each: tests + Codex gate)

0. **5.0 Proof ring `R_q̂`** (R2 P1) — a new ring instance `Z_q̂[X]/(X^{n̂}+1)`, `n̂=64`, `q̂=p·q1`.
   ⚠️ **MODULUS (P1, DESIGN-review 2026-06-15):** the SHOW needs a HYP-330-calibrated ~2^57.7-class `q̂`
   (NOT the illustrative `549755813869`, which FAILS the ZK bound — see the bounds section)
   (the show params in §5.6 / Table 7.1 — the mask widths + ZK norm bounds are sized
   for this `q̂`). The build is bootstrapped over the **issuance** modulus `q1=PHAT_Q1=524269≈2^19`
   (`q̂≈2^37.7`) **PROVISIONALLY** so the arithmetic/CRT/proof scaffolding lands first; this caps the
   provable signature-norm dims (see `proof_show::norm_bounds_provable`, the `B²<q̂` guard). **The flip
   to the show modulus is HYP-330** and MUST happen before mainnet — until then, params are toy and
   honest large-dim shows are (correctly) rejected, not silently mis-secured. Do NOT read "q1≈2^19" as
   the target. Distinct from `sep_ring`; challenges + the LNP22 proof live here. Arithmetic +
   inversion (for the invertible-difference challenge property). ⚠️ R3 P1: the `R_p → R_q̂` lift is
   NOT homomorphic (`q̂=p·q1`); a mod-`p` SEP relation becomes a mod-`q̂` relation **with a `p·z`
   carry**, so the lift produces a bounded quotient witness `z` that the proof commits + bounds. Tests:
   arithmetic, inversion, and the carry-lift round-trip (a mod-`p` equation lifts to `= p·z` mod `q̂`
   with the recovered `z` bounded).
1. **5.1 ABDLOP commitment** — extend `bdlop` to the Ajtai+BDLOP fused commitment (binding for the
   short block, hiding for the message block) over `R_q̂`. Tests: opening, binding, hiding, homomorphism.
2. **5.2 Challenge space** (§7.4.1) — sample `c ∈ C ⊂ R_q̂` (`ρ,η` bounds); invertible-differences
   property; `|C| ≥ 2^λ`. Tests: bounds, difference-invertibility.
3. **5.3 Linear-relation proof** — masked opening + rejection sampling over ABDLOP; soundness/ZK.
4. **5.4 Quadratic-relation proof** — the garbage-term/automorphism technique for `f(witness)=0`
   (the `tGv₂` product + binary constraints). **The long pole within the long pole.** Threshold tests.
5. **5.5 Exact-ℓ₂-norm proof** — squared-norm-as-quadratic; tight extraction. Tests at the bound.
6. **5.6 Compose the SIGNATURE-CORE show** (⚠️ R12 P2b — NOT the full §1 statement yet) — assemble
   ONLY the credential-possession core (sig relation §1.1 + tag §1.3 + binary §1.4 + norms §1.2 +
   carry), Fiat–Shamir; soundness/ZK tests. Does NOT yet prove `m=bits(w)`-binds-`C_r` or emit `N` —
   so it is test-only and incomplete on its own.
7. **5.7 Cross-domain bind + PQ lattice-PRF nullifier (Q6=(ii)) + FULL show assembly** — extend 5.6
   into the complete §1 statement: generalize `bind.rs` to prove the
   lattice message `m = bits(w)` is the digit-encoding of the EC `C_r`'s scalar `w` (HYP-345). The
   nullifier is `N = F^lat_w(epoch)` — a **PQ keyed lattice PRF** (BPR/BP14 candidate, ZK-friendly
   variant chosen at build), and the show proves **in-circuit** that `N` is that PRF of the bound `w`
   (a new ZK relation — the PRF rounding is the cost, done in the quadratic/norm layer). This SUPERSEDES
   the EC `nullifier.rs` for the C3 vouch (new build component, shared with the BBS half). `255 = ⌈log₂
   r⌉` bits
   (full-entropy `w`, resolves R2 P1e) AND a **canonical-range proof `digit-value < Fr::MODULUS`** (R8
   P1 — else a non-canonical `bits` maps to the same `C_r`/`N` as a different signed message). `s` is
   separately proven-known, not the key.
8. **5.8 Blind issuance** (`OblSign`, Alg 7.1) — user commits `c = A·ru + D_s·s + D·m` and proves the
   opening (5.3) **AND the full message well-formedness** (R9 P2): `m, s` binary (`m∘m=m`, `s∘s=s`,
   via 5.4), `m = bits(w)` canonical (`< Fr::MODULUS`, range-proof via 5.4/5.7), and the
   registration `D_s·s = upk` (here `upk` IS known to the issuer). Only then does the signer
   `EllipticSampler`; user unblinds. ⚠️ Without these, the issuer signs out-of-space / non-canonical
   `m`/`s` that later collide mod `Fr` — issuance must enforce the SAME constraints as the show, not
   just opening correctness. (Reuses 5.1–5.4, 5.7.)
9. **5.9 Issuer-hiding wrapper** (HYP-324, shared with BBS) — replace the public `vk_pub` with the
   `EpochIntroducerAnchor`: candidate (a) shared/aggregate epoch key (matrices stay public, relation
   unchanged) or (b) committed-key + accumulator-membership (adds quadratic terms). This is the gate
   for entering the live vouch path. ⚠️ R6 P1: until this lands, the public-`vk_pub` core (5.6) is
   **TEST-ONLY** — it must NOT be wired into `vouch.rs`, because verifying against a named key reveals
   the introducer (violating §1.6 when an epoch has >1 introducer).
10. **5.10 Wire into `vouch.rs`** — ONLY after 5.9: AND-verify the issuer-hidden lattice show with the
   BBS half (HYP-343, retire `StubVouchScheme`); end-to-end vouch test. Depends on 5.9 (no live
   wiring of the public-key core).

Realistic: 5.4 (quadratic) + 5.5 (norm) are the research-grade core; 5.9 (issuer-hiding) is the
HYP-324 crypto-sign-off decision. Expect multiple careful gated sub-chunks each. No public LNP22 impl
⇒ faithful transcription throughout (thesis §7.4 is the source). The public-key core (≤5.8) is
test-only until 5.9 gates it into the vouch path.

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
- **Q6 — nullifier construction. ✅ DECIDED = (ii)** (Josh, 2026-06-15): a **PQ keyed lattice PRF**
  `N = F^lat_w(epoch)`, proven in-circuit consistent with the bound `w`, SUPERSEDING the EC
  `nullifier.rs` for the C3 vouch (shared with the BBS half — one nullifier, fixed once). Framing
  corrected: a deterministic `w`-keyed nullifier can't be everlasting-(unbounded)-unlinkable
  (brute-force `w`); the achievable max is **PQ-computational**, which the lattice PRF reaches and the
  EC nullifier (classical-computational) does not — consistent with the PQ-soundness ambition. See
  §1.7 + chunk 5.7. (Cost: the PRF-eval ZK relation, accepted.)
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

### Round 3 (Codex gpt-5.5/high, 2026-06-15) — 1×P1, 1×P2, both RESOLVED

- **P1 — `q̂` lift carry term.** `q̂ = p·q1`, so `R_p → R_q̂` is not a homomorphic embedding; a mod-`p`
  SEP relation lifts to a mod-`q̂` relation with a `p·z` carry, which the proof must carry+bound or
  honest sigs are rejected. **Resolution:** §1.1 + chunk 5.0 now prove `…·v − (u+…) = p·z (mod q̂)`
  with a committed, bounded quotient witness `z`.
- **P2 — stale `k` in the parent build plan.** Parent §5 (the early LNS build plan) still bound a
  separate `k` and emitted `N=k·H_G1`. **Resolution:** the parent §3 supersede banner now explicitly
  covers §4 AND the §5 build plan (LNS/`k` references there are non-normative; authoritative build
  order = this doc §4, nullifier keyed by `w`).

### Round 4 (Codex gpt-5.5/high, 2026-06-15) — 1×P2, RESOLVED

- **P2 — §2 still named LNS20/21 as the show framework.** **Resolution:** §2 item 2 locked to
  **[LNP22]**; LNS20/21 are conceptual ancestors only; authoritative = this doc.

### Round 5 (Codex gpt-5.5/high, 2026-06-15) — 1×P1, RESOLVED

- **P1 — hidden issuer key vs the public-matrix SEP relation.** If `verify_show` takes only the epoch
  anchor and `ipk*` is hidden, the SEP matrices `A,B,u,D_s,D` are no longer public constants, so
  `A·v₁, B·v₂, D·m` become witness×witness quadratics — the proof would have to commit the issuer key
  + prove membership + handle those products, or it loses anonymity / soundness. **Resolution:**
  issuer-hiding is now correctly scoped as the **HYP-324 layer** (§1.6), NOT invented here: the CORE
  show (this doc) verifies under a **public** issuer/epoch key (matrices public ⇒ §1.1 tractable);
  HYP-324 candidate (a) shared/aggregate epoch key keeps the matrices public (relation unchanged,
  preferred), while (b) committed-key+accumulator adds the quadratic terms (heavier, flagged). §3
  `verify_show` takes a public `vk_pub`; the HYP-324 wrapper swaps in the anchor + membership proof.

### Round 6 (Codex gpt-5.5/high, 2026-06-15) — 1×P1, RESOLVED

- **P1 — vouch wiring must gate on issuer-hiding.** The build plan let the public-`vk_pub` core be
  wired into `vouch.rs` before the HYP-324 wrapper, producing a BlindedVouch that verifies against a
  named key (revealing the introducer when an epoch has >1). **Resolution:** build plan split — **5.9
  issuer-hiding wrapper (HYP-324)** is the gate; the public-key core (≤5.8 + the 5.6 compose) is
  **TEST-ONLY** and MUST NOT be wired live; **5.10 wire into `vouch.rs`** depends on 5.9.

### Round 7 (Codex gpt-5.5/high, 2026-06-15) — 2×P2, RESOLVED

- **P2a — registration `upk` binding.** `D_s·s=upk` had no public `upk` in the show ⇒ vacuous (and a
  public `upk` de-anonymizes). **Resolution:** §1 item 5 — registration is ISSUANCE-time
  (`OblSign`/`UKeyGen`); the show keeps `s` hidden as a signed attribute. Parent §9.3 updated.
- **P2b — parent transcription order didn't gate wiring.** **Resolution:** parent §9.3 now gates
  vouch-wiring on the issuer-hiding wrapper (public core test-only until then).

### Round 8 (Codex gpt-5.5/high, 2026-06-15) — 1×P1, 1×P2, RESOLVED

- **P1 — canonical `F_r` range for `bits(w)`.** Raw bits are malleable: a non-canonical encoding
  (value `≥ r`) maps to the same `C_r`/`N` as `w` but is a different signed message ⇒ a second
  credential / nullifier collision. **Resolution:** §1.7 + chunk 5.7 require `bits(w)` = the canonical
  representative (`255` bits AND a range-proof `digit-value < Fr::MODULUS`), at show AND issuance.
- **P2 — residual `registration` in the show summary.** **Resolution:** §1's summary now states the
  linear parts are the `A,D_s,D` signature terms + tag weight (NOT a `upk`-registration check).

### Round 9 (Codex gpt-5.5/high, 2026-06-15) — 1×P2, RESOLVED

- **P2 — blind issuance well-formedness.** Chunk 5.8 only proved the commitment opening, but issuance
  must enforce the SAME message constraints as the show (binary `m,s`; canonical `m=bits(w) <
  Fr::MODULUS`) or the issuer signs out-of-space / non-canonical messages that collide mod `Fr`.
  **Resolution:** chunk 5.8 now requires the full well-formedness proof (binary via 5.4, canonical
  range via 5.4/5.7, registration `D_s·s=upk`) before signing — not just opening correctness.

### Round 10 (Codex gpt-5.5/high, 2026-06-15) — 1×P1, 1×P2, RESOLVED (P1 ⇒ DECISION Q6)

- **P1 — EC nullifier vs everlasting hiding.** `N=w·H_G1(epoch)` is public + only computationally
  hiding; a future EC-DL break recovers `w` and links epochs, contradicting everlasting anonymity.
  **Resolution:** §1.7 + parent §1.1 now SCOPE the claim (everlasting = the show; the EC nullifier is
  a documented computational caveat) and flag the fix as **Q6** — a PQ/statistically-hiding nullifier
  is a crypto-sign-off DECISION shared with the BBS half (the C3 PQ lattice-PRF `nullifier_lwr.rs`; the
  EC `nullifier.rs` is superseded for C3, Q6). Not overclaimed.
- **P2 — `w` must be full-entropy, not full-width.** §1.7 + parent §1.1 now require `w ← U(F_r)`
  generated uniformly by `UKeyGen` (else the public `N` is brute-forceable over a low-entropy `w`).

---

# §5.4c–5.6: FULL ZK SHOW — faithful spec from thesis Figure 7.2 + Eq 7.9–7.12 + Table 7.1

*Captured 2026-06-15 by reading the thesis PDF directly (the .txt OCR garbled the F-matrix). This is
the COMPLETE construction the remaining build transcribes. `n̂=64`, `k̂=4`, `ℓ=7` (soundness-amp dim),
`d̂` = Ajtai module rank, `q̂ = q·q1`. Source: cjeudy.github.io manuscript Ch7 §7.4.3, Fig 7.2.*

## Table 7.1 — exact parameters (SHOW column; issuance differs)
| sym | issuance | **show** |
|-----|----------|----------|
| λ | 128 | 128 |
| n̂ (ring degree) | 64 | 64 |
| k̂ (subring embed) | 4 | 4 |
| d̂ (Ajtai rank) | 20 | **23** |
| q1 (modulus factor) | 524269 ≈2^19 | **~2^39 class — HYP-330-calibrated** (549755813869 illustrative, fails ZK) |
| q_min | 425837 ≈2^18.7 | 425837 |
| q̂ = q·q1 | ≈2^37.7 | **≈2^57.7** |
| ℓ (soundness amp) | 7 | 7 |
| m1 (witness dim) | 104 | **211** |
| m2 (commit rand dim) | 58 | **74** |
| χ (commit rand distn) | B1 (ternary) | B1 |
| ρ (ℓ∞ chal norm) | 8 | 8 |
| η (ℓ1-like chal norm) | 93 | 93 |
| γ_j (rej slack, j∈[3]) | 48.64 | 48.64 |
| M_j (rej rate) | 2 | 2 |
| σ1 (1st mask width) | 369051 | **582380223** |
| σ2 (2nd mask width) | 275603 | **311305** |
| σ3 (3rd mask width) | 72848 | **114957847** |
| ‖π‖ proof size | 35.99 KB | **79.58 KB** |
| λ*_anon / λ*_unf | — | 129 / 124 |

**MODULUS FINDING (build impact):** my shipped `proof_ring.rs` uses `PHAT_Q1=524269` (=issuance). The
SHOW needs a LARGER `q̂` (~2^57.7 class). ⚠️ **`q1=549755813869 ≈2^39` is ILLUSTRATIVE ONLY and is NOT
a valid target — it FAILS the ZK bound** (the bounds section: `2B256²/13−B256 ≈5.2e17 > q̂≈2.34e17`). It
shows the right magnitude class + the structural constraints any candidate must meet (i64 coeffs fit
2^57.7<2^63; i128 products fit 2^115.4<2^127; `mod 8 = 5` ✓ for SEP + invertible-diff). The REAL show
modulus is a HYP-330 deliverable: solve the ZK bound jointly (`q̂`, `σ1-3`, `c_256`) → pick a `q1` with
`q≡5 mod 8` that SATISFIES all three `max` terms, THEN flip `PHAT_Q1`. Do NOT flip to `549755813869`.
The ring/CRT MECHANISM is modulus-agnostic; only the value is provisional.

## Figure 7.2 — the non-interactive ZK show (5 rounds, Fiat-Shamir)

**Witness:** `s1` (the committed witness incl. SEP sig `v`, tag `t`, message `m`, hidden attrs `m_sm`);
ABDLOP commit randomness `s2 ← χ^{m2}`.

**Prove (reject-loop until all `keep`):**
```
s2 ← χ^{m2};  t_A ← A1 s1 + A2 s2                       # ABDLOP Ajtai commit
y_i ← D_{σ_i}^{m_i}, i∈{1,2};  w ← A1 y1 + A2 y2        # masks + mask commit
y3 ← D_{σ3}^{256/n̂};  g ← U({x∈R̂_q̂^ℓ : τ0(x)=0})       # 3rd mask + ZERO-CONST-COEFF garbage
m̂ ← [y3^T | g^T]^T;  t_B ← B_{y,g} s2 + m̂              # BDLOP commit of (y3,g)
msg1 = (t_A, t_B, w);  (R0,R1) ← H(1,crs,x,msg1) ∈ ({0,1}^{256×m1 n̂})²
R ← R0 − R1;  z3 ← τ(y3) − R·τ(s1);  keep ← Rej(z3, R·τ(s1), σ3, M3)   # approx-shortness of s1
msg2 = z3;  (γ_{i,j}) ← H(2,…) ∈ Z_q̂^{ℓ×262}           # aggregation challenges
compute h_i  (Eq 7.9);  msg3 = (h1..hℓ)
(μ_i) ← H(3,…) ∈ R̂_q̂^{ℓ+d̂k̂}
compute ŝ, y (Eq 7.12), F, f, f̄ (Eq 7.11)
e0 ← y^T F y;  e1 ← ŝ^T F y + y^T F ŝ + f^T y           # garbage terms
t0 ← b^T y2 + e0;  t1 ← b^T s2 + e1                     # BDLOP-commit the garbage (b∈crs)
msg4 = (t0,t1);  c ← H(4,…) ∈ C                         # self-conjugate challenge
z1 ← y1 + c·s1;  z2 ← y2 + c·s2;  keep1/2 ← Rej1(…)
π = (t_A, t_B, z3, h1..hℓ, t1, c, z1, z2)               # w,t0 recomputed by verifier
```

**Verify (b1∧b2∧b3∧b4∧b5):**
```
w ← A1 z1 + A2 z2 − c·t_A;  msg1=(t_A,t_B,w)
(R0,R1)←H(1,…); msg2=z3; (γ)←H(2,…); msg3=(h_i); (μ)←H(3,…)
compute F,f,f̄ (Eq 7.11)
z ← [z1; z1^{*T}; c·t_B − B_{y,g} z2; (c·t_B − B_{y,g} z2)^{*T}]     # packed response
t0 ← z^T F z + c·f^T z + c²·f̄ − (c·t1 − b^T z2)         # reconstruct garbage commit
msg4=(t0,t1)
b1: ‖z1‖2 ≤ c_{n̂m1}·σ1·√(n̂m1)      b2: ‖z2‖2 ≤ c_{n̂m2}·σ2·√(n̂m2)
b3: ‖z3‖2 ≤ c_{256}·σ3·√256          b4: ∀i∈[ℓ], τ0(h_i)=0          # THE relation check
b5: H(4,crs,x,msg1,msg2,msg3,msg4) = c                  # Fiat-Shamir
```

## Eq 7.9 — the aggregated `h_i` (combine all quadratic eqs via γ, mask via g_i, τ0(h_i)=0 carries the truth)
```
h_i = g_i + Σ_{j∈[256]} γ_{i,j}(e_j*·y3 + r_j*·s1 − z3,j)            # (3.1b) approx-shortness rows
        + γ_{i,257}(v1''*·v1'' − B1'^2)                              # (3.2b) ‖v1''‖²=B1'^2
        + γ_{i,258}(v2''*·v2'' − B2^2) + γ_{i,259}(v3''*·v3'' − B3^2) # (3.3b,3.4b) norm bounds
        + γ_{i,260}(t'*·t' − w_) + γ_{i,261}(t'*·(t' − 1_{R̂k̂}))      # (3.5b,3.6b) tag norm + binariness
        + γ_{i,262}(m_sm'*·(m_sm' − 1_{R̂km_sm}))                     # (3.7b) hidden-attr binariness
```
where `r_j = τ^{-1}(R^T e_j^Z)`. The `v1''/v2''/v3''/t'/m_sm'` are the subring-decomposed witness parts
(the SEP signature `v` split, the tag `t`, hidden attrs). `g_i` (τ0=0) masks all non-const coeffs.

## Eq 7.11 — F, f, f̄ (the public quadratic form; built from μ, γ + SEP matrices A'',B'',A3'',D'_sm,G_i'')
`ŝ = [s1^T | s1^{*T} | m̂^T | m̂^{*T}]^T`. The main linear SEP relation aggregated by μ_{ℓ+i}:
`A''v1'' − B''v2'' + A3''v3'' − D'_sm m_sm + t'G''v2'' = u' + p·ẑ` (this is the SEP VERIFY eq with the
tag-product `t'G''v2''` = the QUADRATIC term; `d̂k̂` equations). ⚠️ **CARRY (P1, DESIGN-review round 3
2026-06-15):** the SEP relation holds mod `p`, but the proof lives mod `q̂ = p·q1` (§1, non-homomorphic
lift), so the lifted equation carries the **committed bounded quotient witness `ẑ`** as `+ p·ẑ` — `ẑ`
is a witness coordinate in `ŝ` that the proof commits AND norm-bounds (so the carry cannot be abused).
Omitting `p·ẑ` would reject honest signatures that satisfy the relation only mod `p`. The
implementation already does this (`proof_show::compute_carry` / `sep_exact_carry_holds` /
`sep_lhs_from_blocks` − `sep_rhs_from_blocks` `= p·z`); these equations must match it. f̄ is the scalar
constant from 7.10.
`F = [[F', F'', 0],[0,0,0]]` block; `F' = Σ_{i∈[d]} μ_{ℓ+i} G_i''` placement; `F'' = Σ_i μ_i·
diag(γ_{i,257}I, γ_{i,258}I, γ_{i,259}I, (γ_{i,260}+γ_{i,261})I, γ_{i,262}I)`. (Full block shapes in
PDF p.192; transcribe verbatim at build.)

## Build order (remaining)
- **5.4c** subring decomposition `τ`/`τ^{-1}` (n→n̂=64, k̂=4 split) + the `R^T` approx-range rows + `g`
  (τ0=0) garbage + BDLOP-commit garbage (t0,t1) + the `b4: τ0(h_i)=0` check. (Unblocks ZK.)
- **5.5** the three exact ℓ2-norm bounds (b1,b2,b3 via the `‖v‖²=B²` rows of h_i).
- **5.6** F/f assembly (Eq 7.11) incl. the SEP tag-product quadratic `t'G''v2''` — the sig-core.
- **5.7** full Figure 7.2 prove/verify compose + bind to C_r + PQ lattice-PRF nullifier.
- **5.8** issuance (Figure 7.1, simpler — no show-relation, commitment-opening + registration).
- **5.9** HYP-324 issuer-hiding gate;  **5.10** wire vouch.rs (HYP-343).

## Completeness/ZK/soundness bounds (Lemmas 7.5–7.7, for HYP-330 calibration)
- `B = √(B1'^2 + B2^2 + B3^2 + w + n·m_sm)` bounds ‖s1‖2;  σ1=γ1·η·B, σ2=γ2·η·√(n̂m2), σ3=γ3·√337·B.
- soundness error `≈ 2/|C| + q_min^{-n̂/κ} + q_min^{-ℓ} + 2^{-128} + ε_{M-SIS}`;
  `β = 8η√((c_{n̂m1}σ1√(n̂m1))² + (c_{n̂m2}σ2√(n̂m2))²)` for M-SIS_{n̂,d̂,m1+m2,q̂,β}.
- ZK: `q̂ > max(B², 82/√26·n̂ m1 B256, 2B256²/13 − B256)`, `B256 = c_256 σ3 √256`.
  ⚠️ **The Table 7.1 / §5.6 modulus values are ILLUSTRATIVE and do NOT yet satisfy this bound (P2,
  DESIGN-review round 7 2026-06-15).** With the listed `q̂ = 425837·549755813869 ≈ 2.34e17` and
  `σ3√256 ≈ 1.84e9`, the dominating `2B256²/13 − B256` term `≈ 5.2e17 > q̂` — so the documented show
  modulus FAILS ZK. This is the HYP-330 joint-calibration target (the *bound* is the canonical
  mechanism from Lemma 7.7; the specific `q̂`/`σ1-3`/`c_256`/`B256` values are PROVISIONAL and must be
  solved together — `q̂` larger and/or `σ3`/`c_256` smaller — so all three `max` terms hold). Do NOT
  treat the listed numbers as a validated parameter set; implement the bound as a runtime/param-gate
  assertion so an uncalibrated set is rejected, not silently shipped.
