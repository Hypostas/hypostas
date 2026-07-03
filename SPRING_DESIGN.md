# SPRING_DESIGN.md — HYP-317 log-size lattice ring signature (design-first)

Status: **DESIGN — pre-Codex-review.** Target crate: `vouch-crypto` (the lattice proof stack), behind the
`protocol-core::spring::{RingSigner, RingVerifier}` traits. Feature-gated `experimental-unaudited`,
HYP-330-gated (highest-risk crypto, same class as `bind.rs` / `proof_anchor_bind.rs`).

Spec: CIRCUIT_LIFECYCLE §18 (SPRING universal anonymity), THREAT_MODEL §5.2 / §9.2 / Q2.11.

---

## §0 The contract (what the trait promises)

From `protocol-core/src/spring.rs` (the Track-A shell, already merged):

- `RingSigner::sign(message: &[u8], ring: &SpringRing, signer: &RingMemberId) -> SpringSignature`
  — the holder of `signer`'s secret (who MUST be a ring member) signs `message`, **revealing nothing about
  which member** (1-in-K).
- `RingVerifier::verify(message, sig, ring) -> Ok(())` iff sound + 1-in-K anonymous.
- `SpringRing` = a **public**, canonical (sorted + de-duplicated) `Vec<RingMemberId>`; `RingMemberId([u8;32])`
  is (a hash of) a member's routing identity. `K_DEFAULT = 1000`.
- `SpringSignature(Vec<u8>)`, `SPRING_MAX_SIG_LEN = 64 KiB`. Spec §18.1 *target* ~8–10 KB.

**Restated as a crypto statement.** The ring is PUBLIC and both parties hold the full member list. So SPRING is
a **1-out-of-K proof over a public ring that hides the index i**, Fiat–Shamir-bound to `message`:

> ∃ i ∈ [K] and a secret `sk` such that `RingMemberId_i` is the public key bound to `sk`, and the proof is
> bound to `message` and to the ring. The verifier learns "some member signed" but not `i`.

Security goals (§18.1, THREAT_MODEL §5.2):
- **Unforgeability** — a non-member (nobody holding any ring member's `sk`) cannot produce an accepting `sig`.
- **Anonymity (1-in-K)** — `sig` is computationally independent of `i` given the ring; no observer (including
  the first-hop guard) can do better than `1/K` at guessing the signer.
- **Message binding** — `sig` for `message₁` does not transfer to `message₂ ≠ message₁` (non-malleable NIZK).
- **Post-quantum** — hardness rests on lattice assumptions (M-SIS / M-LWE), no classical-only step.

Non-goals (deliberate, tracked): linkability / traceability (SPRING is a *plain* ring signature — the
one-introducer-per-onboarding nullifier is a SEPARATE mechanism, `nullifier.rs` / HYP-346); revocation; the
live EXTEND-cell wiring (§18.2, follows the primitive); the §18.4 SIMD/ANE perf stack (a later optimization
pass, not soundness).

---

## §1 Decision: REUSE the [LNP22]/SEP\* stack, do NOT port SPRING-2025

The module name references "SPRING (Sign-then-prove ring signatures from lattices, 2025)". "Sign-then-prove"
is a *paradigm*, not a single wire format: a member holds a lattice key/credential, and the ring signature is
a NIZK proof of possession for one public key in the ring. We already built the entire machinery this paradigm
needs, for C3:

| Primitive we already have | Module | Reused for SPRING as |
|---|---|---|
| R_q = Z_q[X]/(X²⁵⁶+1), q = 425801, sub-ring n̂ = 64, show modulus q̂ ≈ 2⁵⁷·⁷ | `proof_ring`, `sep_ring` | the proof ring |
| ABDLOP commitment + linear opening | `abdlop`, `proof_linear` | commit the witness |
| Aggregated masked quadratic (one garbage commitment, §C-iv leak-free) | `proof_agg_show` | fold ALL constraints into one proof |
| Exact-ℓ₂ norm families, binariness, `Σ = w` fixed-weight | `proof_constraint`, `proof_show` | short-preimage + selector-bit constraints |
| Matrix–vector relation `M·x = y` over R_q | `proof_linear`, `proof_linrel` | the Ajtai/SIS hash rounds |
| Approx-range witness-shortness, carry-lift exactness | `proof_approx_range` | keep the relation exact over q̂ |
| SIS-commit-to-short-secret `t = D_s·s`, `s ∈ T₁` binary | `sep_sig` (`ukeygen`, `upk`) | the SPRING key relation |
| Cross-domain / set-membership-flavoured ZK | `proof_anchor_bind` | pattern for the membership leg |

Refs on disk: **LaBRADOR** (BS23, eprint 2022/1341) and the **SEP paper** (Jeudy, 2024/131). Porting a distinct
SPRING-2025 construction would duplicate a second full proof stack (its own commitment, aggregation, FS,
params, calibration) — a direct violation of "audit existing abstractions before defining new ones"
([[feedback_audit_before_abstractions]]) and of the minimal-crate-footprint standard. **Reuse.** The only new
crate-local modules are the SIS-Merkle accumulator and the SPRING relation/prove/verify that composes the
existing proof legs; no new commitment or aggregation layer.

Rejected alternative constructions (considered):
- **One-out-of-many via a one-hot selector `e ∈ {0,1}^K` (Groth–Kohlweiss / MatRiCT-style).** Log-size needs a
  lattice product-argument we do NOT have; building it is more novel infra than the accumulator path, and the
  naive O(K) one-hot witness is ~1000 committed ring elements (too large). Rejected: more new machinery, worse
  size.
- **Port SPRING-2025 / a LaBRADOR-native ring sig wholesale.** Rejected for v1 (duplicate stack); LaBRADOR is
  retained as the §6 size-optimization route, not the v1 construction.

---

## §2 Why routing keys can't be the ring key — SPRING gets its own attested SIS key

`RoutingIdentity` (`protocol-core/src/routing_identity/`) keys are **X25519 + ML-KEM-768 + Ed25519 + ML-DSA-65**;
`routing_id = SHA-256(x25519_pk ‖ ml_kem_ek)`. ML-DSA-65 lives in a DIFFERENT ring (q = 8380417, degree 256,
NTT-friendly) than our proof ring (q = 425801). Proving an ML-DSA secret relation *inside* a q = 425801 proof
system is a modulus-mismatch that would dwarf the rest of the design. So:

**Each dyad mints a SPRING key in OUR ring, attested alongside its identity.**

- `spring_sk = s ∈ T₁^{η}` — a short/binary secret (mirrors the SEP user key `s ∈ T₁^{2d}`, `sep_sig::ukeygen`).
- `spring_pk = t = A_s · s ∈ R_q^{d}` — an M-SIS commitment under a public matrix `A_s` (CRS, §5). Binding to a
  binary `s` is exactly the `upk = D_s·s` relation we already prove (`proof_show` binariness + linear).
- `RingMemberId = SHA-256(domain ‖ encode(t))` — the shell's 32-byte id becomes the hash of the SPRING pubkey.
  The Vita-Chain attestation (RelayAttestation / routing-identity publication) binds `t` to the dyad so the ring
  sampler (`sample_ring`, already merged) draws honest `RingMemberId`s. **This is the one integration
  requirement** and is recorded in `RUNTIME_REQUIREMENTS.md` (§7): the attested active-set entry must carry the
  SPRING pubkey `t` (or a commitment the verifier can open to `t`), not merely the routing id.

Rotation: the SPRING key MAY rotate on the routing-identity cadence (24 h) or be longer-lived; the ring is per
circuit-build over the currently-attested set, so rotation is transparent to the construction. (Open question
Q3, §8.)

---

## §3 The construction — SIS-Merkle accumulator + [LNP22] path-and-key proof

Blueprint: Libert–Ling–Nguyen–Wang, "Zero-Knowledge Arguments for Lattice-Based Accumulators" (EUROCRYPT 2016),
realized on our [LNP22] proof stack. The ring is public, so the verifier RECOMPUTES the accumulator; the prover
proves a hidden path.

### §3.1 The accumulator (public, both sides compute it)

An Ajtai/SIS hash `H: R_q^{2ℓ} → R_q^{ℓ}` compresses two nodes into one:

```
H(a, b) = A_h · [ g⁻¹(a) ; g⁻¹(b) ]  mod q
```

where `g⁻¹(·)` is the base-b gadget decomposition (`sep_gadget`, base-14, k = KG) mapping a full node in R_q^{ℓ}
to a SHORT vector, and `A_h ∈ R_q^{ℓ × 2ℓk}` is a public CRS matrix. `H` is collision-resistant under M-SIS
(a collision yields a short nonzero kernel element of `A_h`). The Merkle tree over the K leaves
`leaf_i = H_leaf(t_i)` (a domain-separated hash of member i's SPRING pubkey) has root `R = MerkleRoot(ring)`,
depth `δ = ⌈log₂ K⌉ = 10` at K = 1000. The verifier computes `R` from the public ring in the clear (no ZK).

### §3.2 What the prover proves in ZK (the [LNP22] relation)

Witness (all committed in ONE ABDLOP `t_A`, hidden):
- `s` — the signer's SPRING secret (binary, `η` ring elements),
- the leaf `t = A_s·s` and `leaf = H_leaf(t)`,
- the authentication path `{sibling_j}_{j<δ}` and the direction bits `{b_j ∈ {0,1}}_{j<δ}` (which side the
  path node is), δ = 10,
- the intermediate node hashes and their gadget decompositions.

Relation families (each folds into the §C-iv aggregated masked quadratic via a γ-weighted family, exactly like
the SEP show's v1/v2/v3-norm + binariness families):

1. **Key opening** — `A_s · s = t` (linear over R_q) ∧ `s ∈ {0,1}` (binariness). [`proof_linear` + `proof_constraint::binariness`]
2. **Leaf** — `leaf = A_h · g⁻¹(t ‖ pad)` with `g·g⁻¹(t) = t` (gadget-recomposition exactness) ∧ the
   decomposition digits are in `[0,b)`. [`proof_linear` + range/binariness on digits]
3. **Path rounds** j = 0..δ: `node_{j+1} = A_h · [ sel(b_j; node_j, sibling_j) ; sel(¬b_j; node_j, sibling_j) ]`
   with `g·g⁻¹ = id` exactness, digit-range, and `b_j ∈ {0,1}`. The child-order swap `sel` is a
   bit-conditioned selection `left = (1−b_j)·node_j + b_j·sibling_j`, `right = b_j·node_j + (1−b_j)·sibling_j`
   — one multiplication by the selector bit, expressible as a quadratic family (like the tag/message binariness
   cross-terms already handled).
4. **Root equality** — `node_δ = R` (the public root; a linear constraint pinning the last node to the public
   value). This is what ties the hidden path to the ring WITHOUT revealing the leaf index.

The NIZK is Fiat–Shamir: the challenge (all of `proof_agg_show`'s `t_A`/`t_B`/γ/μ derivations) is seeded with
`H(domain ‖ message ‖ R ‖ ring.canonical_bytes())`, so the proof is bound to `message` and the ring
(non-malleable, replay-bound). `SpringSignature.0 = serialize(ShowAggProof + public inputs)`.

### §3.3 Sign / verify

- **sign(message, ring, signer):** reject `SignerNotInRing` if `signer ∉ ring` (O(log K) `contains`). Compute
  `R`, locate the leaf index, assemble the witness (path + key), run `prove` (FS-seed as above), serialize.
- **verify(message, sig, ring):** enforce `SPRING_MAX_SIG_LEN`; recompute `R` from the public ring; re-derive
  the FS seed from `(message, R, ring)`; run `verify_agg`; `Ok(())` iff it accepts. No secret, no index leaks.

---

## §4 Soundness (unforgeability)

An accepting proof, by [LNP22] knowledge-soundness (the extractor we already rely on for the SEP show), yields a
witness satisfying families 1–4. Family 4 pins `node_δ = R`; families 2–3 are a hash-chain from `leaf` to
`node_δ`; family 1 opens `leaf`'s pre-image `t = A_s·s` for a KNOWN binary `s`. Therefore either:
(a) `leaf` is one of the ring's actual leaves and the forger holds that member's `s` (not a forgery — it's a
real member signing), or
(b) the extracted path is a **collision** in `H` (two different pre-images hashing into an on-path node) or a
short kernel element of `A_h`/`A_s` — an M-SIS break.
Unforgeability reduces to M-SIS (accumulator + key binding) ∧ the FS/[LNP22] soundness we already calibrated for
the show (q̂ ≈ 2⁵⁷·⁷, ℓ garbage rows → ~q̂⁻ˡ soundness error). The message is in the FS seed, so a proof does not
transfer across messages.

**Reused invariant (carry into the build):** the norm/relation families must be *provable without wrap* at q̂ —
the same `norm_bounds_provable`-style check that HYP-355 needed. Every SIS-hash round's max committable norm
must be `< q̂`; the accumulator params (§5) are chosen so.

## §5 Anonymity (1-in-K)

The proof is a `proof_agg_show` NIZK: statistically/computationally ZK (the garbage-masked `h_i` reveal only
`τ0(h_i)=0`; the openings `z1,z2` are rejection-sampled Gaussians independent of the witness). The ONLY public
inputs are `message`, the ring, and `R` — all independent of `i`. Hence `sig` is (comp.) independent of the
signer index: 1-in-K holds against any observer, including the guard. Anonymity rests on the same ZK property
that protects the SEP credential show; no new assumption.

Ring-sampling caveat (already handled by the shell): `sample_ring` excludes the first-hop relay and the signer
is always included; a degenerate `len()==1` ring gives no anonymity — the caller checks `ring.len()`.

---

## §6 Parameters + honest size estimate

- CRS: `A_s ∈ R_q^{d×η}`, `A_h ∈ R_q^{ℓ×2ℓk}` — sampled from a public seed at install (§18.4 CRS
  preprocessing), shared by all dyads. Concrete `d, η, ℓ, k` calibrated in `proof_params.rs`
  (`calibration-as-code`, the HYP-352 item-3a pattern) against M-SIS core-SVP ≥ 128.
- Depth δ = 10 (K = 1000). Witness ≈ key-opening (η) + δ·(node + sibling + gadget digits) + selector bits.
- **Size honesty (rule: no silent caps).** The aggregated show is ONE masked quadratic regardless of family
  count, but its `z1` opening scales with the committed witness dimension m₁, which grows ~linearly in δ and the
  per-round gadget width. v1 is expected to land in the **~20–45 KB** range — LARGER than the §18.1 ~8–10 KB
  target, WITHIN the 64 KiB `SPRING_MAX_SIG_LEN`. The doc does not pretend otherwise. Routes to the target
  (deferred, tracked): (i) LaBRADOR (BS23, on disk) recursive folding of the final relation → few-KB proofs;
  (ii) a smaller per-round hash arity; (iii) SIMD/ANE only affects time, not size. The v1 acceptance bar is
  **sound + anonymous + log-size scaling**, with the concrete byte count measured and reported, not the 8–10 KB
  number.

## §7 Implementation plan (behind the traits, in `vouch-crypto`)

Design-first, then build in gate-clean chunks (each: integration + smoke test per rule #27; Codex gate per #15):

- **C1 — `spring_acc.rs`:** the SIS-Merkle accumulator (Ajtai `H`, gadget decomposition, `MerkleRoot(ring)`,
  path extraction). Unit + a collision-resistance sanity test. NO ZK yet.
- **C2 — `spring_relation.rs`:** the families 1–4 as `AffineConstraint`s / linear relations over the packed
  witness; the witness packer; `norm_bounds_provable`-style wrap-safety check.
- **C3 — `spring_prove.rs` / `spring_verify.rs`:** compose C2 into `prove_show_agg`-style prove/verify with the
  `(message, R, ring)` FS seed. Round-trip + adversarial (tampered path, wrong message, non-member) tests.
- **C4 — the trait impl:** a real `RingSigner`/`RingVerifier` in `vouch-crypto` (e.g. `LatticeRingScheme`) that
  `protocol-core` wires behind `spring::{RingSigner, RingVerifier}`, replacing `StubRingScheme`. Serialization
  codec with the `SPRING_MAX_SIG_LEN` + frame cap (the §18.2 note). Smoke test through the trait.
- **C5 — params calibration** (`proof_params.rs`): M-SIS core-SVP ≥ 128 estimator test; measure + record the
  real proof size.
- Each chunk: `cargo test -p vouch-crypto --features experimental-unaudited --lib` + clippy + Codex gate.

## §8 Open questions for Codex DESIGN-review

1. **Accumulator vs. one-out-of-many.** Is the SIS-Merkle accumulator the right log-size vehicle on our stack,
   or is a MatRiCT-style bit/product argument worth the new machinery for a smaller proof? (Design picks
   accumulator; challenge it.)
2. **Hash arity / params.** Ajtai `H` arity (binary tree vs higher) and `A_h` dims to balance depth vs
   per-round width against q̂ wrap-safety and size.
3. **SPRING key lifetime + attestation.** Does the SPRING pubkey `t` rotate with the routing identity (24 h) or
   persist? Where exactly in the Vita-Chain attestation is `t` bound, and does the ring sampler need `t`
   in-line or a commitment it opens? (RUNTIME_REQUIREMENTS integration point.)
4. **FS binding completeness.** Is `H(domain ‖ message ‖ R ‖ ring.canonical_bytes())` sufficient, or must
   individual leaves / the CRS digest also enter the seed to prevent cross-ring/weak-FS attacks?
5. **Size gap.** Is a v1 at ~20–45 KB acceptable behind the 64 KiB cap with LaBRADOR compression tracked, or is
   the 8–10 KB target a hard v1 requirement (→ start from LaBRADOR)?

---

*Author: Iris. Pattern mirrors SEP_V3A3_DESIGN.md / ANCHOR_BIND_DESIGN.md (design-first → Codex DESIGN-review →
chunked build → gate). Highest-risk crypto: a subtle bug is a silent anonymity/soundness failure; HYP-330 is the
pre-mainnet backstop.*
