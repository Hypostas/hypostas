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
  is a member's routing identity hash. `K_DEFAULT = 1000`.
- `SpringSignature(Vec<u8>)`, `SPRING_MAX_SIG_LEN = 64 KiB`. Spec §18.1 *target* ~8–10 KB.

**`RingMemberId` is an INDEX into an authenticated directory, not the crypto input** (Codex DESIGN-review P1).
The 32-byte id is a hash — the verifier cannot recover the member's lattice SPRING pubkey `t_i ∈ R_q̂^d` from it,
and proving a SHA-256 pre-image in-ZK is lattice-hostile. Both the signer and the verifier already hold the
attested active set that §18.3's `sample_ring` draws the ring from (the ring is "identical at sender + verifier
given Vita-Chain state"), so the real scheme holds a **member directory** `RingMemberId → t_i` and *resolves*
every ring member to its SPRING pubkey before touching the accumulator. This resolution is public + authenticated
(the attestation binds `RingMemberId ↔ t_i`, §2), OUTSIDE the ZK. The `RingSigner`/`RingVerifier` trait
signatures are unchanged — the directory is `&self` state on the concrete `LatticeRingScheme` (§7), exactly like
a verifier holding its CRS.

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
| proof ring R_q̂ = Z_q̂[X]/(X^{n̂}+1), n̂ = 64, q̂ ≈ 2⁵⁷·⁷ (credential ring R_q: X²⁵⁶+1, q = 425801) | `proof_ring`, `sep_ring` | the proof ring the accumulator + proof live in |
| ABDLOP commitment + linear opening | `abdlop`, `proof_linear` | commit the witness |
| Aggregated masked quadratic (one garbage commitment, §C-iv leak-free) | `proof_agg_show` | fold ALL constraints into one proof |
| Exact-ℓ₂ norm families, binariness, `Σ = w` fixed-weight | `proof_constraint`, `proof_show` | short-preimage + selector-bit constraints |
| Matrix–vector relation `M·x = y` over R_q̂ | `proof_linear`, `proof_linrel` | the Ajtai/SIS hash rounds |
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
- **Port SPRING-2025 / a LaBRADOR-native ring sig wholesale.** Rejected (duplicate stack). Note LaBRADOR is
  NOT even a size-optimization route here: HYP-358 built + proved the fold and found relations at this scale are
  base cases (it compacts MB–GB proofs, not a 20–45 KB one) — see §6.

---

## §2 Why routing keys can't be the ring key — SPRING gets its own attested SIS key

`RoutingIdentity` (`protocol-core/src/routing_identity/`) keys are **X25519 + ML-KEM-768 + Ed25519 + ML-DSA-65**;
`routing_id = SHA-256(x25519_pk ‖ ml_kem_ek)`. ML-DSA-65 lives in a DIFFERENT ring (q = 8380417, degree 256,
NTT-friendly) than our proof ring `R_q̂` (n̂ = 64, q̂ ≈ 2⁵⁷·⁷, §3.0). Proving an ML-DSA secret relation *inside*
our proof system is a modulus-mismatch that would dwarf the rest of the design. So:

**Each dyad mints a SPRING key in OUR ring, attested alongside its identity.**

- `spring_sk = s ∈ T₁^{η}` — a short/binary secret (mirrors the SEP user key `s ∈ T₁^{2d}`, `sep_sig::ukeygen`).
- `spring_pk = t = A_s · s ∈ R_q̂^{d}` — an M-SIS commitment under a public matrix `A_s` (CRS, §5). Binding to a
  binary `s` is exactly the `upk = D_s·s` relation we already prove (`proof_show` binariness + linear).
- `RingMemberId` stays the shell's routing-identity hash (unchanged), and the Vita-Chain attestation binds the
  SPRING pubkey `t` to that same id, so the **member directory** `RingMemberId → t` is authenticated. Both ends
  build it from the attested active set the ring is drawn from (§18.3). **This is the one integration
  requirement**, to be recorded in the crate's `RUNTIME_REQUIREMENTS` contract file when the primitive is built
  (§7 C4, per rule #4 — no such file exists yet): the attested active-set entry must carry the SPRING pubkey `t`
  alongside the routing id, so every `RingMemberId` in a ring resolves to a `t` at both signer and verifier. A ring member that does NOT resolve (not in the attested set) makes `verify` reject — the
  signature is over an unauthenticated ring (§3.3). The `A_s` matrix and the leaf hash are CRS (§5), so `t = A_s·s`
  is verifier-checkable once `t` is resolved.

Rotation: the SPRING key MAY rotate on the routing-identity cadence (24 h) or be longer-lived; the ring is per
circuit-build over the currently-attested set, so rotation is transparent to the construction. (Open question
Q3, §8.)

---

## §3 The construction — SIS-Merkle accumulator + [LNP22] path-and-key proof

Blueprint: Libert–Ling–Nguyen–Wang, "Zero-Knowledge Arguments for Lattice-Based Accumulators" (EUROCRYPT 2016),
realized on our [LNP22] proof stack. The ring is public, so the verifier RECOMPUTES the accumulator; the prover
proves a hidden path.

### §3.0 Ring choice — PROOF-RING-NATIVE, no carry-lift (decided at C2)

The accumulator lives **natively in the proof ring** `R_q̂ = Z_q̂[X]/(X^{n̂}+1)` (`proof_ring`, n̂ = 64, q̂ ≈
2⁵⁷·⁷) — NOT in the SEP credential ring `R_p` (p = 425801). Rationale (found while grounding C2): SPRING keys
are independent of the SEP credential, so there is no reason to pay the `R_p → proof-ring` **carry-lift + subring
embedding** the SEP show needs — that bridge is the single most error-prone part of the [LNP22] stack (the class
of the HYP-355 P1). Proving over q̂ directly, `proof_linrel` (`Σ C_k·s1[idx_k] = rhs`), `proof_relation_zk`, and
`proof_agg_show` all compose with ZERO bridge and no carry witness.

The one catch — a base-2 gadget over the 58-bit q̂ is ~58 digits/coeff (11× the R_p base-14's 5), which would
blow the size budget — is resolved by a **large-base gadget** `b ≈ 2^ν` (ν≈12) so `⌈log_b q̂⌉ ≈ 5` digits/coeff,
matching R_p's digit count. The honest/verifier decomposition is the canonical `[0, b)` one; the PROVER's
committed digits are constrained only SHORT (the show's approx-range leg), NOT range-proved to `[0,b)` —
per §4/§3.2d that suffices (a per-digit `proof_range` would be size-prohibitive; §4). Net: SAME witness size
as the R_p accumulator, WITHOUT the carry-lift. `b` (and ℓ, the node dim) are
calibrated for M-SIS collision-resistance in C5 — a larger `b` shrinks the witness but weakens CR; the feasible
window is the C5 lever. C1's initial R_p draft is re-based to this at the C2 pivot.

### §3.1 The accumulator (public, both sides compute it after resolving the ring)

**Resolve first (Codex P1).** Both `sign` and `verify` map the ring's `RingMemberId`s → SPRING pubkeys
`{t_i ∈ R_q̂^d}` through the authenticated member directory (§2). If ANY member is unresolvable, the operation
fails (`verify` → reject: the ring is not fully attested). The accumulator is built over the resolved `t_i`'s —
NOT over the 32-byte ids — so no SHA-256 pre-image ever enters the ZK.

An Ajtai/SIS hash `H: R_q̂^{2ℓ} → R_q̂^{ℓ}` over the PROOF ring (§3.0; q̂ ≈ 2⁵⁷·⁷, NOT the credential ring
`R_q`, q = 425801) compresses two nodes into one:

```
H(a, b) = A_h · [ g⁻¹(a) ; g⁻¹(b) ]  mod q̂
```

where `g⁻¹(·)` is the **large-base gadget decomposition over q̂** (§3.0, base `b ≈ 2^ν`, `k = ⌈log_b q̂⌉ ≈ 5`
digits/coeff, canonical digits in `[0, b)`; the PROVER's committed digits are only proven SHORT, not
range-proved — §4) mapping a full node in R_q̂^{ℓ} to a SHORT vector, and `A_h ∈ R_q̂^{ℓ × 2ℓk}`
is a public CRS matrix. `H` is collision-resistant under M-SIS over q̂
(a collision yields a short nonzero kernel element of `A_h`). The leaves are `leaf_i = H_leaf(t_i)` — an Ajtai
hash of the RESOLVED pubkey `t_i` (lattice-friendly, verifier-computable), NOT of the routing-id hash. To fix a
canonical tree shape both sides agree on, leaves are ordered by the ring's canonical `RingMemberId` order (the
`SpringRing` invariant), padded to a power of two with a fixed `⊥` leaf. The Merkle tree over the K leaves has
root `R = MerkleRoot(resolved ring)`, depth `δ = ⌈log₂ K⌉ = 10` at K = 1000. The verifier computes `R` in the
clear (no ZK) after resolution.

### §3.2 What the prover proves in ZK (the [LNP22] relation)

Witness (all committed in ONE ABDLOP `t_A`, hidden):
- `s` — the signer's SPRING secret (binary, `η` ring elements),
- the leaf `t = A_s·s` and `leaf = H_leaf(t)`,
- the authentication path `{sibling_j}_{j<δ}` and the direction bits `{b_j ∈ {0,1}}_{j<δ}` (which side the
  path node is), δ = 10,
- the intermediate node hashes and their gadget decompositions.

Relation families (each folds into the §C-iv aggregated masked quadratic via a γ-weighted family, exactly like
the SEP show's v1/v2/v3-norm + binariness families):

(Digits are proven only SHORT — via the show's approx-range leg — NOT `[0,b)`/canonical: §4/§3.2d show
shortness + M-SIS CR suffice, so the range/canonicality families listed below were DROPPED. The scalar
families that remain are binariness only.)

1. **Key opening** — `A_s · s = t` (linear over R_q̂) ∧ `s ∈ {0,1}` (binariness). [`proof_linrel` + `proof_constraint::binariness`]
2. **Leaf** — `leaf = A_h · g⁻¹(t ‖ pad)` with `g·g⁻¹(t) = t` (gadget-recomposition exactness). [`proof_linrel`;
   digits proven short by the show's approx-range, not per-digit range — §4]
3. **Path rounds** j = 0..δ: `node_{j+1} = A_h · [ sel(b_j; node_j, sibling_j) ; sel(¬b_j; node_j, sibling_j) ]`
   with `g·g⁻¹ = id` exactness and `b_j` a SCALAR bit (§3.2b/§3.2c binariness). The child-order swap `sel` is a
   bit-conditioned selection `left = (1−b_j)·node_j + b_j·sibling_j`, `right = b_j·node_j + (1−b_j)·sibling_j`
   — one multiplication by the selector bit, expressible as a quadratic family (like the tag/message binariness
   cross-terms already handled).
4. **Root equality** — `node_δ = R` (the public root; a linear constraint pinning the last node to the public
   value). This is what ties the hidden path to the ring WITHOUT revealing the leaf index.

The NIZK is Fiat–Shamir: the challenge (all of `proof_agg_show`'s `t_A`/`t_B`/γ/μ derivations) is seeded with
`H(domain ‖ message ‖ R ‖ ring.canonical_bytes())`, so the proof is bound to `message` and the ring
(non-malleable, replay-bound). `SpringSignature.0 = serialize(ShowAggProof + public inputs)`.

### §3.2b The path-selection relation — the full-ring quadratic (C2b-iii design)

The linear families (key opening, leaf, node hash, root) are proven full-ring by `proof_linrel`
(`Σ C_k·s1[idx] = rhs`). The **path bit-selection is the one full-ring QUADRATIC** — a product of the
witnessed direction bit with a witnessed node/sibling difference — which `proof_linrel` cannot express
and `proof_constraint`/`AffineConstraint` prove only at the constant coefficient τ0. It is the SAME shape
as the SEP relation's tag term `A_t = [A | tG−B]` (a witnessed tag × witnessed `v₂`), which is proven
full-ring by `SepRelation : FullRingRelation` inside `proof_agg_show::prove_agg`. So SPRING gets a
`SpringPathRelation : FullRingRelation` mirroring `SepRelation`.

**Key construction move — do NOT commit the ordered children.** Split `A_node = [A_L | A_R]` and define
two LINEAR hashes of the committed (unordered) child digits:
`H_lin := A_L·g⁻¹(node_j) + A_R·g⁻¹(sib_j)` (children in path-order) and its swap
`H_swap := A_L·g⁻¹(sib_j) + A_R·g⁻¹(node_j)`. Then the bit-selected hash is the **linear interpolation**

```text
A_node·[ selected children ]  =  H_lin  +  b_j·(H_swap − H_lin)          (b_j ∈ {0,1})
```

(`b_j=0` ⇒ path-order ⇒ `H_lin`; `b_j=1` ⇒ swapped ⇒ `H_swap`). So the per-level relation is

```text
recompose(g⁻¹(node_{j+1}))  −  H_lin  −  b_j·(H_swap − H_lin)  =  0          (full ring)
```

whose LINEAR part is `Σ bᵢ·node_{j+1}_digits − A_L·node_j_digits − A_R·sib_j_digits` and whose QUADRATIC
part is the single bilinear `−b_j·((A_L − A_R)·(g⁻¹(sib_j) − g⁻¹(node_j)))` — `bit × linear-combo-of-digits`,
exactly `SepRelation`'s `bil(tag, v₂)` shape. This **eliminates the ordered-children witness** (and its
extra selection constraints): only `node_j_digits`, `sib_j_digits`, `b_j`, `node_{j+1}_digits` are
committed per level, and `node_0 = leaf` (from §3.2 family 2), `node_j` for `j>0` is the previous level's
`node_{j+1}` (shared block). `SpringPathRelation` implements `quad_part` (Σμ over the δ levels of the
bilinear), `cross` (its `c¹` masked-proof term), `lin_part`, `cst=0`, μ-aggregated from `t_A` like
`SepRelation`.

**Composition.** The full relation is `SumRelation<SpringLinearRelation, SpringPathRelation>` (the linear
families as a `lin_part`-only `FullRingRelation` + the path quadratic), proven by ONE masked show, no §C-iv
leak. The SCALAR families fold in as the show's `extra` `AffineConstraint` families (the pq-vouch R1–R5
pattern): `s ∈ {0,1}`, each `b_j` BINARY, and each `b_j` a SCALAR bit. Root equality `node_δ = R` is a
linear family with the public `R` as `rhs`.

**No canonicality / `[0,b)` range families (§4/§3.2d).** An earlier draft (Codex §3.2b P1) added a
`recompose < q̂` canonicality family on every committed digit-vector, reasoning that `[0,b)` alone does not
force a unique decomposition (`b^k = 2⁶⁰ > q̂`, so `x` and `x+q̂` are both representable). The §4 reduction
supersedes this: unforgeability needs only digit SHORTNESS (which the show's approx-range leg already
proves) + M-SIS collision-resistance — a non-canonical chain reaching `R` yields a short `A_node`/`A_leaf`
collision, an M-SIS break, without any canonicality constraint. So the canonicality + `[0,b)` families are
**dropped** (they were also ~25× over the size budget). The digits are proven SHORT, not canonical.

**Soundness.** See §4 for the full reduction: `prove_agg` extracts a SHORT witness satisfying the full-ring
families with binary `s` / scalar bits; for a non-member, walking the extracted chain and the verifier's
canonical tree to the first divergence yields a short `A_node`/`A_leaf`/`A_s` collision — an M-SIS break.
No canonical-decomposition constraint is invoked.

### §3.2c The production show — mirror the ℓ-amplified issuance-π (C2b-iv+v)

The C2b-iii-b `prove_quad` was a construction-validation shortcut with two gaps (documented on
`MembershipCoreProof`): (1) no scalar `{0,1}`/range/canonicality families, (2) my OWN μ-row-aggregation +
single garbage gives only `~1/p` soundness over the composite `q̂ = p·q₁`. **Both are closed by building
the production proof as a MIRROR of the blind-issuance well-formedness show `prove_issuance_wf` (§G′)** —
NOT the SEP-specific `prove_show_agg_with_extra`. §G′ is already the generic pattern: a NON-SEP full-ring
relation (`OpeningRelation`) as the `a:` summand, ALL scalar families supplied via `extra`, the
approx-range witness-shortness leg + the `ℓ` garbage rows + the single `(t0,t1)` — identical to the show.

**Why mirror, not reinvent.** `OpeningRelation : FullRingRelation` aggregates its rows with the SAME
`mu_vector` + `aggregate_rows` the SEP relation uses, inside the SAME ℓ-amplified masked show. So a SPRING
relation built the same way inherits the SEP credential's *exact* soundness properties — including how the
[LNP22] machinery treats the composite modulus. The C2b-iii-b `~1/p` weakness was an artifact of my
bespoke `prove_quad` path, not of the show; mirroring §G′ removes it by construction. (The residual
composite-modulus μ question is then identical to the SEP show's and lives under the same HYP-330 audit —
it is NOT a SPRING-specific gap.)

> **⚠️ SUPERSEDED in part (2026-07-03, Codex gate on C2b-v).** The claim above that mirroring §G′ "removes
> the `~1/p` by construction" is WRONG: the `a:` `mu_vector`+`aggregate_rows` aggregation is one-shot in the
> masked quadratic and is NOT ℓ-amplified by the show's `h_i` rows (those amplify only the scalar `extra`
> families). The `~1/p` is real for the `a:` relation — and, exactly as this section says, it is stack-wide
> (identical in SEP's `OpeningRelation`/`SepRelation`), NOT SPRING-specific. It is a grindable soundness gap
> (`~p_min` work), fixed by ℓ-folding the aggregation layer. See **`AGGREGATION_SOUNDNESS_COMPOSITE_MODULUS.md`**
> for the analysis + the stack-wide fix. Until that lands, `prove_spring_show` (and the SEP show) carry the
> one-shot aggregation posture under the `experimental-unaudited` / HYP-330 gate.

**The build:**
1. **`SpringMembershipRelation : FullRingRelation`** (mirrors `OpeningRelation`): `quad_part` =
   `aggregate_rows(bit×(sib−node) bilinears, μ)`, `cross` = its `c¹` term, `lin_part` =
   `aggregate_rows(key/leaf/node/root linear rows, μ)`, `cst` = `aggregate_rows(−R rows, μ)`, μ from
   `mu_vector(t_a, …)`. (This REPLACES C2b-iii-b's pre-aggregated `FQuadForm` + `path_mu`.)
2. **Scalar families as `extra` `AffineConstraint`s:** `s ∈ {0,1}`, each `b_j` BINARY, and each `b_j` a
   SCALAR bit (`Σ_{k≥1} coeff_k = 0`). Aggregated by `mu_vector` + `aggregate`, like `issuance_binariness`.
   (Digit `[0,b)` range + canonicality `< q̂` are NOT included — §4/§3.2d show shortness + M-SIS CR suffice;
   the show's approx-range leg supplies the shortness. This is the whole of C2b-iv, already built.)
3. **`prove_spring_show` / `verify_spring_show`** mirror `prove_issuance_wf` / `verify_issuance_wf`: sample
   `y3/z3` (approx-range), `ℓ` garbage, commit `t_B`, FS-derive `γ/μ`, compute `h_i`, build
   `SumRelation{SpringMembershipRelation, scalar}`, `prove_agg`. **FS seed = `H(domain ‖ message ‖ root ‖
   ring.canonical_bytes())`** (§3.3 binding — distinct FS domain `spring-show/*`).

This is the single largest, highest-risk chunk; it lands design-first → Codex DESIGN-review → chunked build
(relation, then scalar families, then the show wrapper), each `codex exec review`-gated.

### §3.2d Is per-digit canonicality/range actually needed? (soundness-vs-size) — **RESOLVED: NO (see §4)**

**Resolution:** the §4 reduction proves unforgeability from digit SHORTNESS + M-SIS collision-resistance
ALONE (walk the extracted chain and the verifier's canonical tree to the first divergence → a short nonzero
`A_node`/`A_leaf` kernel element). Canonical digits are never invoked, so the per-digit `[0,b)` range and
`recompose < q̂` canonicality families are **dropped**: `m1 ≈ 440`, size stays ~20–45 KB, and C2b-iv is just
the binariness families (already built). The record of the question follows.

Grounding the C2b-iv (2/2) build surfaced a pivotal question that determines both soundness AND whether
SPRING fits the size budget. `proof_range` commits **2·⌈log₂ b⌉ ≈ 24 bit-blocks per ring element**;
range-proving every committed digit (~440 for δ=10) balloons `m1` from ~440 to **~11 000 blocks** → a
multi-MB proof, ~25× over the 64 KiB cap. So the §3.2b canonicality (`recompose < q̂`) + `[0,b)` range
families, as naively specced, are **size-prohibitive**. Before building them, resolve:

**Claim (to be adjudicated): per-digit canonicality/range is NOT needed for unforgeability; the show's
approx-range shortness + Ajtai-hash M-SIS collision-resistance suffice.**
- The masked show ALREADY carries the `proof_approx_range` witness-shortness leg (`Y3_BLOCKS`/`z3`), which
  proves `‖s1‖` (hence every committed digit) is SHORT — for FREE, no per-digit bit-decomposition.
- Ajtai-hash CR holds for ANY short pre-image, canonical or not. So the extractor's short witness gives:
  either `leaf` is a real ring leaf on a valid path (a real member), OR the extracted `leaf → node_δ = R`
  chain merges with the real canonical tree at some node where two DISTINCT short child-sets share a
  parent — an M-SIS collision. Either way unforgeability holds *without* pinning canonical digits.
- This is a DIFFERENT argument from the one Codex's §3.2b P1 refuted ("digits match the verifier's tree"):
  it does not require the prover's digits to equal the verifier's canonical ones — only that reaching the
  public `R` with any short digits costs an M-SIS collision. Anonymity is unaffected (digits are ZK-masked
  either way).

**If the claim holds** (Codex DESIGN-review + the [LNP22] shortness-bound details confirm the approx-range
`B` is tight enough for the accumulator's M-SIS): drop the canonicality + `[0,b)` families entirely, keep
`m1 ≈ 440`, size stays ~20–45 KB, and C2b-iv reduces to just the binariness families (already built).
**If it does NOT hold** (canonicality genuinely required): the naive per-digit range is infeasible and the
construction needs a COMPACT range argument (one aggregated approx-range-style bound over all digits at
once, or a higher-arity tree cutting the digit count) — a design change, not an implementation detail.

This adjudication gates C2b-iv (2/2) and the final size claim. It is the reason the size §6 estimate must
be re-derived after it settles. **Do not build the per-digit range families until this resolves.**

### §3.3 Sign / verify

- **sign(message, ring, signer):** reject `SignerNotInRing` if `signer ∉ ring` (O(log K) `contains`). Resolve
  every member → `t_i` (§3.1); the signer resolves its own `signer → t` and pairs it with the local `s`. Compute
  `R`, locate the leaf index, assemble the witness (path + key), run `prove` (FS-seed as above), serialize.
- **verify(message, sig, ring):** enforce `SPRING_MAX_SIG_LEN`; resolve every member → `t_i` (reject if any is
  unresolvable); recompute `R` from the resolved ring; re-derive the FS seed from `(message, R, ring)`; run
  `verify_agg`; `Ok(())` iff it accepts. No secret, no index leaks.

---

## §4 Soundness (unforgeability)

An accepting proof, by [LNP22] knowledge-soundness (the extractor we rely on for the SEP show), yields a
witness satisfying the full-ring families (key/leaf/path/root) with, from the show's approx-range leg,
**every committed digit SHORT** (`‖·‖_∞ ≤ B_short`) and (binariness families) `s ∈ {0,1}`, each `b_j` a
scalar bit. Write the extracted values: `t = A_s·s`, `leaf = A_leaf·d_t` where `recompose(d_t)=`… (each
`node` a recomposition of its committed SHORT digits), the δ hash rounds `node_{j+1} = A_node·[d_{node_j};
d_{sib_j}]` (bit-ordered), and `node_δ = R`.

**Reduction (no canonicality needed — resolves §3.2d).** Let `T` be the verifier's public tree: the K real
leaves `{H_leaf(t_i)}` hashed up (canonical digits) to the same root `R`. Compare the extracted chain to `T`
top-down from the shared root `R`:
- **Root:** both `A_node·[extracted top children digits]` and `A_node·[canonical top children digits]` equal
  `R`. If the two SHORT digit-vectors DIFFER, that is two distinct short pre-images of `R` under `A_node` — an
  **M-SIS collision** (their difference is a short nonzero kernel element of `A_node`). Done.
- **Else** they are equal ⇒ the extracted node values on this path match `T`'s; recurse into the sub-tree
  holding the extracted leaf.
- **Leaf:** at the bottom, either the extracted `leaf` equals a real `H_leaf(t_i)` with matching short
  pre-image ⇒ (by `leaf = A_leaf·d_t` and `t = A_s·s`, an `A_leaf`/`A_s`-collision unless `t = t_i`) the
  forger holds member `i`'s binary key — a REAL member, not a forgery; or the leaf digits differ from the
  canonical ⇒ an `A_leaf` collision.

So a non-member accepting proof yields a short nonzero kernel element of `A_node` / `A_leaf` / `A_s` — an
**M-SIS break**. The argument uses ONLY digit SHORTNESS (so the divergence is a valid M-SIS instance:
`2·B_short` below the `A_node`/`A_leaf` M-SIS norm bound, §5) and the hash-chain structure — it NEVER invokes
canonical decompositions. **Hence per-digit canonicality (`recompose < q̂`) and `[0,b)` range families are NOT
required for unforgeability, and are DROPPED (§3.2d resolved).**

*Reconciling Codex's §3.2b P1.* That P1 correctly observed `[0,b)` does not force a canonical decomposition
mod q̂, and refuted the WEAKER claim "the prover's digits equal the verifier's canonical tree." This stronger
reduction does not need that claim: it walks the two trees to the first divergence and extracts the collision
from the SHORT (not canonical) child vectors. The large-base gadget's non-unique decomposition is thus
harmless — the binary LLNW accumulator gets canonicality for free (bits are unique) and so its proofs omit it;
the CR argument covers the large-base case identically. The only residual requirement is `B_short` shortness,
which the show's approx-range leg already provides — no per-digit witness.

Unforgeability reduces to M-SIS (`A_node`/`A_leaf`/`A_s`, at `B_short`) ∧ the FS/[LNP22] soundness of the show
(q̂ ≈ 2⁵⁷·⁷, ℓ garbage rows). The message is in the FS seed, so a proof does not transfer across messages.

**Trust-model dependency (from the P1 fix).** Soundness now also rests on the member directory being the
*authenticated* attested set: the reduction's "leaf is a real member's key" step needs the attestation to bind
`RingMemberId ↔ t_i` so a forger cannot inject a `t_i` it controls. This is the §2 integration requirement, not a
new cryptographic assumption — it is the same Vita-Chain attestation the ring sampler already trusts. If the
directory were unauthenticated, a forger could resolve a ring member to its OWN `t`, so `verify` MUST resolve
through the attested set and reject unresolvable members (§3.1).

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

- CRS: `A_s ∈ R_q̂^{d×η}`, `A_h ∈ R_q̂^{ℓ×2ℓk}` — sampled from a public seed at install (§18.4 CRS
  preprocessing), shared by all dyads. Concrete `d, η, ℓ, k` calibrated in `proof_params.rs`
  (`calibration-as-code`, the HYP-352 item-3a pattern) against M-SIS core-SVP ≥ 128.
- Depth δ = 10 (K = 1000). Witness ≈ key-opening (η) + δ·(node + sibling + gadget digits) + selector bits.
- **Size honesty (rule: no silent caps).** The aggregated show is ONE masked quadratic regardless of family
  count, but its `z1` opening scales with the committed witness dimension m₁, which grows ~linearly in δ and the
  per-round gadget width. v1 is expected to land in the **~20–45 KB** range — LARGER than the §18.1 ~8–10 KB
  target, WITHIN the 64 KiB `SPRING_MAX_SIG_LEN`. The doc does not pretend otherwise.
- **LaBRADOR folding is NOT the route (learned the hard way, HYP-358).** The sovereign LaBRADOR fold was built,
  completeness-proven end-to-end (71/71 tests), and its two soundness-critical formulas BS23-paper-confirmed
  (`[[project_labrador_fold]]`). When it was measured against the real C3 anchor relation (~114k elements, β²≈
  8.4e14, ~58-bit modulus) the result was a **base case — ratio ~1.0×**, sometimes an EXPANSION. LaBRADOR only
  compacts *large* relations (~2²⁸–2⁵² elements at q ≳ 2¹²⁸ → 38–65×). A SPRING proof is a SINGLE ~20–45 KB show
  — ~1000× smaller than the anchor's κ=128-replicated ~57 MB, i.e. far below a single fold round's own overhead —
  so folding it would EXPAND, not compact. Josh already pivoted C3 away from folding to source-shrinking for
  exactly this reason. Do not repeat it here.
- **Real routes to the target (deferred, tracked):** (i) **natural-bit-width serialization** — the openings are
  sent at the full q̂ ~58-bit width but `max|coeff|` needs only ~18 bits; packing at true width is a **~3.7×**
  proven win (HYP-358 `measure_real_anchor_opening_size`), which alone brings ~20–45 KB → **~6–12 KB**, at/near
  the §18.1 target with NO new machinery; (ii) **source-shrink** (the anchor bind-shrink philosophy applied to
  the tree): a higher-arity Merkle node to cut δ, or a more compact membership argument, reducing what the proof
  opens. The v1 acceptance bar is **sound + anonymous + log-size scaling**, with the concrete byte count measured
  and reported (then route (i) applied) — not the 8–10 KB number asserted up front.

## §7 Implementation plan (behind the traits, in `vouch-crypto`)

Design-first, then build in gate-clean chunks (each: integration + smoke test per rule #27; Codex gate per #15):

- **C1 — `spring_acc.rs`:** the SIS-Merkle accumulator (Ajtai `H`, gadget decomposition, `MerkleRoot(ring)`,
  path extraction). Unit + a collision-resistance sanity test. NO ZK yet.
- **C2 — `spring_relation.rs`:** the families 1–4 as `AffineConstraint`s / linear relations over the packed
  witness; the witness packer; `norm_bounds_provable`-style wrap-safety check.
- **C3 — `spring_prove.rs` / `spring_verify.rs`:** compose C2 into `prove_show_agg`-style prove/verify with the
  `(message, R, ring)` FS seed. Round-trip + adversarial (tampered path, wrong message, non-member) tests.
- **C4 — the trait impl:** a real `RingSigner`/`RingVerifier` in `vouch-crypto` (e.g. `LatticeRingScheme`) that
  `protocol-core` wires behind `spring::{RingSigner, RingVerifier}`, replacing `StubRingScheme`. The scheme holds
  the CRS (`A_s`, `A_h`) and the **member directory** `RingMemberId → t_i` as `&self` state (the P1 resolution
  seam); `verify` rejects any unresolvable member. Serialization codec with the `SPRING_MAX_SIG_LEN` + frame cap
  (the §18.2 note). Smoke test through the trait, incl. an adversarial unresolvable-member reject.
  > **BUILT 2026-07-03 (`spring_scheme.rs`, gate-clean).** `LatticeRingScheme { acc, directory, secrets }`;
  > `RingMemberId` is an INDEX into the authenticated `directory` (both sign+verify resolve the whole ring →
  > attested leaves; unresolvable ⇒ `UnknownMember`). Codec `SPRING_SIG_CODEC_VERSION` + `encode/decode_spring_
  > show_proof`. Codex P2 fixes: malformed directory entry fails closed (no `hash_leaf` panic); `register_member`
  > drops stale secrets + `sign` guards `pubkey(s)==directory[signer]` (no `Ok(sig)` that won't verify). 8 tests.
  > **v1 SIZE is over cap** — see C5.
- **C5 — params calibration** (`spring_params.rs`): M-SIS core-SVP ≥ 128 estimator test; measure + record the
  real proof size.
  > **BUILT 2026-07-03 (`spring_params.rs`, gate-clean) — two findings.** (1) **M-SIS is SOUND at the provisional
  > dims.** The BKZ core-SVP estimator (root-Hermite δ(b), optimal-sub-dim SIS-norm, classical 0.292·b / quantum
  > 0.265·b) puts all three instances over the CLASSICAL 128 bar: `A_s`≈438 (binary β below the dimension-limited
  > minimum), `A_leaf`≈170, `A_node`≈132. The large SHARED `q̂≈2⁵⁷·⁷` HARDENS the small node (bigger q → the q-ary
  > lattice minimum grows past the fixed β). Quantum: node ≈119.5 — a slim, Dilithium-2-class margin; `min_ell_for_
  > 128` says a strict quantum-128 node is a MODEST bump (ELL 4→5), not a blow-up. (2) **SIZE is the v1 blocker,
  > not hardness.** Full-width v1 sig measured **110629 B at K=8/δ=3, over the 64 KiB cap.** Because the quantum-128
  > node bump inflates the proof, the production calibration is a COUPLED dims+size optimization → §6 routes (i)
  > natural-bit-width packing + (ii) source-shrink, design-first (rule #6). Committed bar = classical-128 (met);
  > `accumulator_meets_128bit_classical_core_svp` passes at the provisional dims. **This is the remaining SPRING
  > work: C5-full = fit `SPRING_MAX_SIG_LEN` (route i/ii) + optionally lift the node to quantum-128, solved jointly.**
- Each chunk: `cargo test -p vouch-crypto --features experimental-unaudited --lib` + clippy + Codex gate.

## §8 Open questions for Codex DESIGN-review

1. **Accumulator vs. one-out-of-many.** Is the SIS-Merkle accumulator the right log-size vehicle on our stack,
   or is a MatRiCT-style bit/product argument worth the new machinery for a smaller proof? (Design picks
   accumulator; challenge it.)
2. **Hash arity / params.** Ajtai `H` arity (binary tree vs higher) and `A_h` dims to balance depth vs
   per-round width against q̂ wrap-safety and size.
3. **SPRING key lifetime + attestation.** Does the SPRING pubkey `t` rotate with the routing identity (24 h) or
   persist? Where exactly in the Vita-Chain attestation is `t` bound? (The P1 fix settled *how* resolution works
   — the scheme holds an authenticated `RingMemberId → t` directory and rejects unresolvable members; this Q is
   now only the attestation *placement* + rotation cadence, the RUNTIME_REQUIREMENTS integration point.)
4. **FS binding completeness.** Is `H(domain ‖ message ‖ R ‖ ring.canonical_bytes())` sufficient, or must
   individual leaves / the CRS digest also enter the seed to prevent cross-ring/weak-FS attacks?
5. **Size gap.** Is a v1 at ~20–45 KB acceptable behind the 64 KiB cap (then natural-bit-width serialization →
   ~6–12 KB, §6 route (i)), or is the 8–10 KB target a hard v1 requirement? LaBRADOR folding is off the table
   (§6, HYP-358 base-case wall); the levers are bit-width packing + source-shrink.

---

## §9 PIVOT (2026-07-05, decided): accumulator → one-out-of-many. Resolves §8 Q1.

**Why (MEASURED, not estimated — `spring_scheme::measure_packed_signature_size`).** The C1–C5 accumulator
build shipped + is gate-clean, but the measurement kills it for `K=1000`: the natural-bit-width-packed sig at
`K=8/δ=3` is **64.3 KB — already AT the 64 KiB cap**, and `lin.z1` (the [LNP22] opening, dimension
`m1 ∝ δ ∝ log K`) is **70%** of it. The measured scaling `m1 ≈ 28 + 48·δ` puts `K=1000 (δ=10)` at **~150 KB
packed, 2.4× over the cap.** Bit-width packing (route i) and a smaller mask are constant factors that help
`K ≤ ~32` but NEVER fit `K=1000` — the opening scales with the ring through `δ`. Higher-arity Merkle is the
WRONG lever (it GROWS the path witness: siblings `= (A−1)·log_A K`, minimized at binary — arity-32 is ~6×
worse). The membership-witness DIMENSION is the driver, so the fix must shrink `m1` structurally. **One-out-of-
many does exactly that: `m1 = O(log K)` with NO path nodes.** Josh chose it over "raise the §18.2 cap" and
"smaller ring" (both preserve/relax at a cost); this is the "do it right" path — full `K=1000` anonymity, fits
the cap. The accumulator (`spring_acc`/`spring_path`) is retired from the SPRING signature (kept in-tree,
`experimental-unaudited`, in case a future accumulator use appears).

**§9.1 Construction — Groth–Kohlweiss / Bootle-et-al one-out-of-many, adapted to [LNP22]/MatRiCT.** Public:
the resolved member pubkeys `t_0,…,t_{N−1} ∈ R_q̂^{D_PK}` (`N=K`, from the directory), `n=⌈log₂N⌉`. Signer knows
index `ℓ` and secret `s` (binary) with `A_s·s = t_ℓ`. Commit (ABDLOP): the index bits `b_0,…,b_{n−1}` of `ℓ`,
the secret `s`, garbage vectors `T_0,…,T_{n−1} ∈ R_q̂^{D_PK}`, response masks `a_j`. FS challenge `x`. Per-bit
linear forms `f_{j,1}(x)=b_j·x + a_j`, `f_{j,0}(x)=x − f_{j,1}(x)`. For index `i` with bits `i_j`:
`P_i(x)=∏_j f_{j,i_j}(x) = δ_{i,ℓ}·x^n + Σ_{k<n} P_{i,k}·x^k` (top coeff `= ∏_j[i_j=b_j] = 1` iff `i=ℓ`). Then
`Σ_i t_i·P_i(x) = t_ℓ·x^n + Σ_{k<n} T_k·x^k = (A_s·s)·x^n + Σ_{k<n} T_k·x^k` with `T_k = Σ_i t_i·P_{i,k}`.

**§9.2 Why it is BUILDABLE on our stack (the key insight).** Reveal the masked bits `z_j = f_{j,1}(x)` in the
response. The verifier then computes `V(x) = Σ_i t_i·∏_j f_{j,i_j}(x)` as a PUBLIC ring vector (`f_{j,1}=z_j`,
`f_{j,0}=x−z_j`; `O(K·(n+D_PK))` ring mults ≈ ms at `K=1000`). The ZK obligations are ALL relations our stack
already proves: (1) each `b_j` is a SCALAR bit — binariness `b_j²=b_j` on the constant coeff PLUS explicit
zero-pins `coeff_k(b_j)=0 ∀k∈[1,NHAT)`. **Plain binariness is INSUFFICIENT** (Codex DESIGN-review P1): it
constrains only `τ0(b_j)∈{0,1}`, so a prover could smuggle arbitrary data into coeffs `1..NHAT−1` while the
constant stays binary — the top coeff of `P_i` would no longer be the Kronecker delta and the Vandermonde
extraction would not yield a real index. This is the SAME scalar-bit lesson as the accumulator's direction
bits (§3.2c C2b-iv): carry the binariness+zero-pin PAIR here. (2) `z_j = b_j·x + a_j` opens the
committed bit — [LNP22] linear opening; (3) the identity `V(x) = (A_s·s)·x^n + Σ_k T_k·x^k`, LINEAR in the
committed `(s, T_k)` given the PUBLIC `V(x)` — `proof_linrel`; (4) `s` binary + `A_s·s` well-formed. No new
proof primitive — the degree-`n` selector becomes a public evaluation (via the revealed masked bits) plus a
linear garbage-coefficient identity. This is why the earlier "we lack the lattice product-arg" worry (memory
`project_hyp317_spring_design`) does NOT block us: the product is made public at `x`, not proven in-ZK.

**§9.3 Size + verify.** `m1 ≈ n + ETA + n·D_PK ≈ 10 + 8 + 40 = 58` ring elements at `K=1000` vs the path's
~500; the garbage `T_k` (`n·D_PK ≈ 40`) dominate. Packed est. **~30 KB at `K=1000`, under the 64 KiB cap**
(vs 150 KB). Verifier does `O(K)` PUBLIC work (the `V(x)` sum) + `O(log K)` proof checks — the standard
one-out-of-many tradeoff (small proof, linear verify), fine at `K=1000`.

**§9.4 Soundness — RESOLVED single-shot (2026-07-05, grounded in `proof_challenge.rs`; still pending Codex
DESIGN-review + the params pass).** The [LNP22] FS challenge is a RING element from the strong set `C`
(`proof_challenge`: self-conjugate, `ρ`-bounded, **pairwise-invertible differences** via `qmin > (2ρ√κ)^κ`,
sized `|C| ≥ 2^λ = 2^128`). That invertible-difference property is EXACTLY the tool that closes the
composite-`q̂` gap I flagged: over `R_q̂` (a non-domain) a nonzero degree-`n` polynomial `f(X)` can have many
roots, BUT if `c_i − c_j` is a unit for all distinct `c_i,c_j ∈ C`, the Vandermonde `V[i][k]=c_i^k` on any
`n+1` challenges is invertible (`det = ∏_{i<j}(c_i−c_j)` = a product of units = a unit) ⇒ `f` cannot vanish on
`n+1` points of `C` ⇒ `f` has **≤ `n` roots in `C`**. So a cheating prover (whose error polynomial
`Σ_i t_i·P_i(X) − (committed)·X^n − Σ_k T_k·X^k` is nonzero) passes only if the FS challenge lands on one of
those `≤ n` roots: probability `≤ n/|C| ≤ 10/2^128 ≈ 2^{−124}` — **SINGLE-SHOT ~128-bit, NO `ℓ_agg`-folding.**
This is UNLIKE the aggregation gap ([[project_aggregation_soundness_gap]]), where the aggregator was a
HASH-DERIVED SCALAR `μ` with no invertible-difference structure (grindable to `0 mod p`); the one-out-of-many
rides the STRUCTURED [LNP22] challenge, whose invertible differences are precisely designed for this
Schwartz–Zippel-over-a-non-domain argument. Special-soundness EXTRACTION uses the same invertible Vandermonde to
recover the coefficients ⇒ the bits `b_j` (scalar-pinned per §9.2 (1)) ⇒ `ℓ`, and `A_s·s = t_ℓ` with `s` binary;
[LNP22] knowledge-soundness for `s, T_k`. Anonymity: masks `a_j` hide `b_j` (`z_j` uniform), [LNP22] ZK hides
`s, T_k` — standard GK zero-knowledge. **Caveats for the params pass:** confirm `|C| ≥ 2^128` at the SPRING
`ρ`/`κ` (the `proof_challenge` doc asserts it, calibrate concretely), and that the degree-`n` bound uses the
FULL selector degree (`n`, not per-bit) — both are calibration items, NOT soundness-structure gaps.

**§9.5 Open questions for Codex DESIGN-review.** (a) ~~Composite-`q̂` soundness of the `n+1`-transcript
extraction~~ **RESOLVED in §9.4 — single-shot via the invertible-difference challenge set, NO `ℓ_agg`**
(Codex DESIGN-review of the argument returned no refutation, only doc-consistency fixes). (b) The garbage-`T_k`
masking + reject-sampling bounds (ZK + shortness). (c) Params: `m1`, the mask widths, and the concrete
`|C| ≥ 2^128` check at the SPRING `ρ`/`κ` (the §9.4 soundness `≤ n/|C|` depends on it). (d) ~~Non-power-of-2
`K`~~ **RESOLVED (Codex gate P1, `oneofmany_relation::pad_members_to_pow2`):** pad the member list to `2^n`
with deterministic NONZERO NUMS dummy pubkeys (domain-separated XOF, no known binary preimage). Without it the
unused indices `K..2^n` are implicit-ZERO pubkeys and a prover forges via an unused index + the all-zero secret
(`A_s·0 = 0`); the nonzero dummies make those slots un-selectable. Both sides pad identically ⇒ part of the
public statement. (e) The member-directory resolution seam is UNCHANGED (still `RingMemberId → t_i`, §7 C4).

**§9.6 Build chunks (design-first FIRST — this §9 is the skeleton, the full soundness/params pass + Codex
DESIGN-review gate BEFORE code, per rule #6).** D1 `oneofmany_relation.rs`: the clear-text selector +
garbage-coefficient identity, pinned. D2: bit-commitment + binariness + response opening. D3: the `V(x)`
public evaluation + the linear garbage identity. D4: compose into the [LNP22] masked show. **Two soundness
mechanisms, do NOT conflate:** the SELECTOR/garbage identity `V(x)=(A_s·s)x^n+Σ T_k x^k` is LINEAR in the
committed `(s,T_k)` given the PUBLIC `V(x)` → it goes through the `proof_linrel` linear opening, **single-shot,
no `ℓ_agg`** (§9.4, the invertible-difference challenge). BUT the τ0 SCALAR EXTRAS (bit binariness + scalar-pin,
`s` binariness) are coefficient constraints checked via the show's `h_i` → they use the **EXISTING `ℓ_agg`-fold
(chunks 1–4)**, since those τ0 families ARE composite-`q̂`-grindable exactly like the SEP/accumulator ones. So
the one-out-of-many needs no ADDITIONAL amplification beyond the show's standing `ℓ_agg` for its scalar extras.
FS-seed `H(domain‖message‖ring.canonical_bytes()‖{t_i}‖x-transcript)` — MUST bind
the ring's canonical member-ID bytes, NOT only the resolved `{t_i}` (Codex DESIGN-review P2): else a proof
replays for a DIFFERENT `SpringRing` whose IDs resolve to the same `{t_i}` (key reused across routing-id
rotation, or two `RingMemberId`s → the same `t_i`), violating the trait contract that binds the sig to the ring
of member IDs. Matches the C4 accumulator seed (which already included `ring.canonical_bytes()`). D5:
`LatticeRingScheme` swaps its
prove/verify from `spring_show` → `oneofmany_show` (the trait + directory + codec are UNCHANGED — only the
membership engine). Params calibration + measured size. Each chunk: test + clippy + Codex gate.

**§9.7 Review status (2026-07-05).** The selector identity (§9.1: `top coeff P_i(x) = δ_{i,ℓ}` and
`Σ_i t_i·P_i(x)` has `x^n` coeff `= t_ℓ`) is NUMERICALLY VALIDATED (a field-arithmetic harness at `n=4`).
Codex DESIGN-review of this §9 returned two P-findings, BOTH folded in above: **P1** — index bits need the
scalar-bit/zero-pin families, not plain binariness (§9.2 (1)); **P2** — the FS seed must bind
`ring.canonical_bytes()`, not only `{t_i}` (§9.6 D4). The composite-`q̂` crux (§9.4) is now **RESOLVED
single-shot** — the [LNP22] challenge's pairwise-invertible differences give the `≤ n` roots-in-`C` bound, so
soundness is `≤ n/|C| ≤ 2^{−124}` with NO `ℓ_agg`-folding (pending Codex DESIGN-review of this argument + the
`|C| ≥ 2^128` params check). **D1 is BUILT** (in the `dyados` repo, `vouch-crypto/src/oneofmany_relation.rs`,
5 tests — the code lives in dyados, this design in hypostas): the clear-text statement +
the selector identity (`top coeff P_i = δ_{i,ℓ}`; `x^n` coeff of `Σ t_i P_i = t_ℓ`, mask-independent) pinned
over the real proof ring. D2 (scalar-pinned bit commitments + response opening) is next.

**§9.8 D4 show-composition — DESIGN MAP + the OPEN subtlety (needs a careful pass BEFORE the build, per rule
#6).** Build status: **D1 done incl. the Codex-P1 non-power-of-2 fix** (`pad_members_to_pow2` /
`aggregate_selector` fill unused slots `≥ K` with nonzero NUMS dummies — release-enforced, re-gated clean).
**D2-a done** (`oneofmany_bits.rs`: scalar-pinned index-bit + `s`-binariness τ0 sub-constraints). The
remaining **D2-b/D3/D4** compose the GK selector into the [LNP22] masked show; the pieces exist
(`proof_linrel::prove` proves `Σ C_k·s1[idx_k] = rhs` on the committed witness — the shape of the selector
identity; the masked-quad show + `h_i`/`ℓ_agg` handle the scalar extras) but the WIRING has a genuine open
subtlety, mapped here honestly:

- **Witness layout `s1`:** index bits `b_j` (`n` SCALAR blocks), secret `s` (`ETA`), garbage `T_k` (`n·D_PK`),
  AND selector masks `a_j` (`n`). `m1 = n + ETA + n·D_PK + n` (≈ 58 at K=1000 — the §9.3 size).
- **One challenge `c ∈ C`** (the [LNP22] strong-set ring challenge, sampled after the commitment `t_a`) serves
  as the GK selector challenge `x` (§9.4 soundness needs exactly this invertible-difference set).
- **THE open subtlety (why this is NOT a trivial spring_show copy):** the GK masks `a_j` and garbage
  `T_k = Σ_i t_i·P_{i,k}(a)` are FUNCTIONS OF `a_j`, so BOTH must be committed in `s1` PRE-challenge — the
  masks CANNOT be the show's own post-challenge Gaussian `y1` (a tempting shortcut that is WRONG: `y1` is
  sampled after `c`, but `T_k` must exist at commit time). So the design commits `a_j` + `T_k` explicitly, the
  response reveals the masked bits `z_j = c·b_j + a_j`, and the verifier (a) computes the PUBLIC
  `V(c) = Σ_i t_i·∏_j f_{j,i_j}(c)` over the padded members from the revealed `z_j`, then (b) checks the
  selector identity `V(c) = (A_s·s)·c^n + Σ_k T_k·c^k` as a LINEAR relation on the committed `(s, T_k)`. The
  **precise mechanism to settle in the pass:** whether `z_j` is verified via the ABDLOP opening or a
  dedicated `c·b_j + a_j = z_j` linrel (rhs is challenge-dependent, so NOT a fixed-rhs linrel — the GK
  polynomial-identity structure); and whether the `V(c)`-identity check is a `proof_linrel` call or a direct
  check on the opening `z1`. Both my first two quick framings were flawed (mask-timing; circular rhs), which
  is the signal this wants a written sub-design + Codex DESIGN-review before code — mirroring how C2b-v was
  designed before built.
- **Scalar extras** (bit binariness + scalar-pin `oneofmany_bits`, `s` binariness) ride the show's `h_i`/
  `ℓ_agg` (§9.6 D4); the selector-linear is single-shot (§9.4). **FS-seed** binds
  `ring.canonical_bytes()` + the padded `{t_i}` (§9.6 P2). Then D5 swaps `LatticeRingScheme`'s engine.

---

*Author: Iris. Pattern mirrors SEP_V3A3_DESIGN.md / ANCHOR_BIND_DESIGN.md (design-first → Codex DESIGN-review →
chunked build → gate). Highest-risk crypto: a subtle bug is a silent anonymity/soundness failure; HYP-330 is the
pre-mainnet backstop.*
