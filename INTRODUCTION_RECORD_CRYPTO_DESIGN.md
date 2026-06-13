# INTRODUCTION_RECORD — Dual-Hybrid Crypto Construction (HYP-338 design proposal)

**Status:** DESIGN PROPOSAL for the Fable 5 + Codex crypto sign-off. This is the construction we propose to build; it is **not** a security certification. The sign-off (and the [HYP-330] external audit before mainnet) remain the gates. Per rule #1, every claim carries a confidence flag and anything unverified is marked ⚠️.

**Author:** Iris, 2026-06-13. Co-designed with Josh via decision walk-through (this session).

**Anchors:** [INTRODUCTION_RECORD.md](INTRODUCTION_RECORD.md) §1–6 · [INTRODUCTION_RECORD_CRYPTO_BRIEF.md](INTRODUCTION_RECORD_CRYPTO_BRIEF.md) (the literature grounding) · [THREAT_MODEL.md](THREAT_MODEL.md) §5.3 · [POST_QUANTUM.md](POST_QUANTUM.md) · the `protocol_core::introduction_record` shell (HYP-337).

---

## 0. The construction in one paragraph

A `BlindedVouch` is a **dual credential**: a **classical BBS half** that carries *which-introducer* anonymity **unconditionally** (information-theoretic / everlasting — no adversary, quantum or otherwise, can ever strip it), and a **sovereign pure-Rust lattice half** that carries **post-quantum soundness** via a *shared per-epoch issuing key that encodes no individual-introducer identity*. A verifier checks **both** (`AND`). The result: **anonymity is unconditional** (the BBS half is the sole, unbreakable carrier; the lattice half is built so even a total break of it reveals "an attested party" but never *which*), and **soundness holds if *either* half is unforgeable** (forging a vouch requires forging both the q-SDH BBS credential *and* the lattice signature — so a quantum break of BBS *or* a bug in our young lattice port is each individually survived). This was **composition C2** of the three we evaluated — but the Codex DESIGN-review (P1) showed C2's shared-epoch-key realization has a soundness hole under a *compromised introducer*, which reopens the C2-vs-C3 choice (§4.4–§4.5). The dual-hybrid *shape* (BBS = unconditional anonymity, lattice = PQ soundness, AND-verify) stands; the precise lattice realization (C2-threshold vs C3) is now the central sign-off decision.

---

## 1. Decisions locked (this session) + the reframe that drove them

| Decision | Value | Where |
|---|---|---|
| Construction family | (c) anonymous credential, **dual-credential hybrid** = lattice AC + classical BBS | locked (HYP-322 sign-off prep) |
| Who verifies | validators verify; **public verification also available** (§3.4) — no secret verifier key strictly required | locked + upgraded by 2026 work |
| Implementation | **sovereign pure-Rust** — NOT FFI to LaZer's C/AVX-512 core | locked |
| Anonymity carrier | **BBS, unconditionally** — the lattice half must not be the anonymity carrier | locked (this session) |
| Lattice realization | **C2-threshold vs C3** — REOPENED by Codex P1 (§4.5); shared-key C2 eliminated | open (sign-off) |
| Build order | **both halves at once** — PQ-complete at first ship; the `StubVouchScheme` stays live until the full construction lands | locked (this session) |

**The reframe (the spine of the whole design).** The two halves are not "future-proof lattice + throwaway classical." They are **complementary opposites**:

| Property | Classical BBS | Lattice half |
|---|---|---|
| **Anonymity** (introducer hidden) | **everlasting / statistical** — unbreakable by *any* adversary, forever | computational (LWE/SIS) — strong but assumption-based |
| **Unforgeability** (no fake vouch) | classical (Gap q-SDH) — **quantum-broken** | **post-quantum** |

Read the diagonals: each half is strong on exactly the axis the other is weak. For a *privacy* system, BBS's **unconditional anonymity is the single strongest guarantee in the construction** — stronger than anything the lattice half offers — which is why we keep it and let it *own* anonymity, while the lattice half owns post-quantum soundness.

---

## 2. The contract the construction must satisfy

### 2.1 The trait boundary (HYP-337 shell — already merged)

```rust
trait VouchIssuer  { fn issue_vouch(&self, introduced: &DyadId, epoch: u64, anchor: &EpochAnchor)
                          -> Result<BlindedVouch, VouchError>; }
trait VouchVerifier{ fn verify_vouch(&self, vouch: &BlindedVouch, introduced: &DyadId, epoch: u64,
                          anchor: &EpochAnchor) -> Result<(), VouchError>; }

pub struct BlindedVouch(pub Vec<u8>);          // OPAQUE bytes — the construction owns the wire format
pub struct EpochAnchor { epoch: u64, bytes: Vec<u8> }   // derived from the Vita-Chain attested set
```

`BlindedVouch` being opaque bytes means the construction has **total wire-format freedom** (§3). The real scheme drops in behind these two traits with **zero protocol rewiring** — the shell already drives the full issue → publish → verify path.

### 2.2 The four properties (INTRODUCTION_RECORD §4, verbatim)

1. **Blindness (from the signer).** The introducer B does not learn the vouch token and cannot link its signing session to the published record. (B's own log can't reconstruct B's introductions.)
2. **Introducer anonymity (from the verifier).** V verifies against the *attested-introducer set / epoch anchor*, not B's individual key — V cannot tell *which* attested party vouched.
3. **Unlinkability (across records).** Two records (same or different B) are not linkable by their `blinded_proof`s.
4. **Soundness (no forgery).** D cannot produce a valid `BlindedVouch` without a real signature from *some* attested introducer — a Sybil cannot self-introduce.

### 2.3 The adversary (INTRODUCTION_RECORD §6)

A **global chain observer + a curious/compromised introducer + a colluding verifier set, all PQ-capable.** The construction must hold §4.1–§4.4 against all three. **"All PQ-capable" is why everlasting anonymity matters: a PQ verifier set still cannot break BBS's statistical anonymity.**

---

## 3. Verified crypto facts (the foundation — confidence-flagged)

These were verified against the primary literature this session (sources §10), upgrading the brief's hypotheses to facts:

- **[HIGH — verified] BBS is "proven unforgeable in the ROM under the Gap q-SDH assumption, and *statistically anonymous*."** Statistical anonymity = information-theoretic = holds against an unbounded/quantum adversary. The CFRG draft states the asymmetry explicitly (§6.9): unforgeability is computational and quantum-broken, while the proof's hiding properties remain quantum-resilient. *Mechanism:* a BBS proof re-randomizes the signature into a uniform group element and blinds every witness with uniform randomness in a Fiat–Shamir Schnorr SPK — perfectly/statistically hiding.
- **[HIGH — verified] Issuer-hiding (hiding *which* introducer among the attested set) is achievable with "everlasting issuer-hiding anonymity"** — Katz & Šefránek, eprint [2025/2080] (GGM; verification uses a verifier-held *policy key*).
- **[MEDIUM — verified-but-fresh] Public verification (no secret policy key) for issuer-hiding** is achieved by 2026 randomizable-key constructions — eprint [2026/369] ("via Randomizable Keys") and [2026/555] ("Improved Issuer Hiding," AGM, removes secret policy keys). ⚠️ These are 2026-fresh; whether a *single* construction gives **both** everlasting anonymity **and** public verification is the key BBS-side sign-off item (§9).
- **[HIGH — verified] Issuer-hiding presentations are compact — they do *not* scale with the number of issuers.** Constant-size regardless of attested-set growth.
- **[HIGH] Sizes.** BBS proof over BLS12-381 ≈ a few hundred bytes, sub-1 KB (G1 = 48 B compressed, scalar = 32 B; ~3 points + a handful of scalars for a 1-attribute vouch; issuer-hiding adds a constant). Lattice half ≈ tens of KB (brief §2–3). Combined record: tens of KB, single on-chain publish — within budget (INTRODUCTION_RECORD §5).

---

## 4. The construction

### 4.1 BBS half — the unconditional anonymity carrier

- **Scheme.** BBS (CFRG `draft-irtf-cfrg-bbs-signatures`) anonymous credential + an **issuer-hiding** presentation layer. Baseline: Katz–Šefránek everlasting issuer-hiding ([2025/2080]) with a **validator-held policy key** (fits the locked "validators verify" model). Upgrade-if-it-preserves-everlasting: the 2026 randomizable-key public-verification works ([2026/369], [2026/555]).
- **What "B vouches for D" is.** B issues D a one-attribute BBS credential binding D's `introduced_dyad_id` under the epoch. D presents an **issuer-hiding, unlinkable proof-of-possession** — this is the BBS component of `BlindedVouch`. The presentation proves "*an attested introducer in this epoch* signed a credential on D" and hides which one **unconditionally**.
- **Blindness (§4.1).** BBS issuance + the unlinkable presentation give the signer-blindness / log-unlinkability the spec requires.
- **What it provides:** §4.2 introducer-anonymity (unconditional, issuer-hiding), §4.3 unlinkability (statistical), and classical (q-SDH) individual unforgeability.
- **Crates.** Pairing: `bls12_381` (zkcrypto). BBS: an audited/maintained BBS impl — candidates `pairing_crypto` (DIF/MATTR), `docknetwork/crypto`. ⚠️ The **issuer-hiding randomizable-key layer is 2026 research → not in any audited crate** → we implement it on top of an audited BBS+`bls12_381` base, against the papers' test vectors. (Audit surface flagged for HYP-330.)

### 4.2 Lattice half — post-quantum soundness, no individual identity

- **The key design choice (what makes C2 work).** The lattice half is a **lattice blind signature under a *shared per-epoch issuing key* `K_epoch`** held by the attested introducer set — **not** a per-introducer key and **not** a membership proof over individual keys. Because `K_epoch` is shared, the signature encodes **no individual-introducer index**. So even a *total* break of the lattice half's anonymity/blindness reveals only "a `K_epoch` signature exists" = "an attested party authorized this" — **never which party.** This is precisely the property that lets BBS remain the sole (unconditional) anonymity carrier (§4.3).
- **Scheme (standard-assumption base).** Beullens–Lyubashevsky–Nguyen–Seiler lattice blind signature, CCS 2023 ([2023/077]) — 20 KB, standard Module-SIS/LWE+NTRU, 2-round. The vouch token is **blind-signed** under `K_epoch` so B cannot link its signing to the published record (§4.1) and the published signature is re-randomized.
- **`K_epoch` management — threshold holding is MANDATORY, not optional (Codex DESIGN-review P1).** The §6 adversary explicitly includes a *compromised introducer*. If `K_epoch` were a single shared key any introducer holds in full, that one compromised introducer could mint unlimited lattice halves — and **post-quantum, when BBS unforgeability is already gone, the lattice half is the *sole* soundness mechanism**, so the `if-either` hedge collapses entirely. (My earlier "AND-verify saves it" reasoning was wrong: post-quantum the BBS half is forgeable, so the AND provides no protection.) Therefore `K_epoch` MUST be **threshold-held** with an explicit compromise threshold `t` (no coalition smaller than `t` can wield the epoch issuing power) — lattice threshold construction per Faller–Niot [2025/1566].
- **But mandatory threshold exposes a trilemma (§4.5) that reopens C2-vs-C3.** "Threshold-held `K_epoch`" can mean two different things, and they land on different constructions — this is now the central sign-off decision, not a tuning knob.
- **Sovereign pure-Rust route.** LaZer (the reference lattice-ZK library) is **C / x86 / AVX-512 / Linux-amd64** — unusable on our ARM (Mac/iOS) targets and excluded by the sovereign-Rust lock. The path: **faithful transcription of the chosen scheme to pure Rust against published test vectors** (rule: never invented math), building where possible on the Rust lattice substrates `lattirust` / `Lazarus`. ⚠️ Test-vector availability + exact params at our security level are UNVERIFIED here and are sign-off + implementation items. This is **the highest-risk component in the arc** — a subtle sampling/rejection/constant-time bug = silent failure — which is why it gets the HYP-330 external audit.
- **What it provides:** §4.4 post-quantum soundness; it deliberately provides **no** individual-introducer anonymity (none is needed of it — BBS owns anonymity).

### 4.3 Composition C2 + the property argument

**Issue.** B (an attested introducer) gives D an individual **BBS** issuer-hiding credential on D. The **lattice** half is authorized by the attested set through a **threshold** operation whose exact form is the §4.5 decision — either *C2-threshold* (a `t`-of-`n` coalition co-signs D's lattice token per vouch) or *C3* (the set threshold-**issues** B an individual epoch credential at join, which B later presents alone, cryptographically bound to the BBS half). **The eliminated single-introducer-shared-key flow — one B alone producing a shared-`K_epoch` signature — MUST NOT be implemented (§4.2, §4.5).**

**Present.** `BlindedVouch = encode(version ‖ P_bbs ‖ P_lattice)` — D's unlinkable BBS presentation plus the re-randomized lattice proof (realization per §4.5).

**Verify.** V checks **both** against the `EpochAnchor`: the BBS issuer-hiding presentation (against the epoch attested-key policy) **AND** the lattice proof (against the epoch lattice anchor — §5.2). **Both must pass.**

**Property argument:**

| Property | Argument | Holds against PQ adversary? |
|---|---|---|
| §4.1 Blindness | BBS issuance is blind + presentation unlinkable to issuance; lattice half is a **blind** signature → B links neither half to the record | yes |
| §4.2 Introducer anonymity | **Unconditional** — BBS issuer-hiding is statistical; the lattice half carries **no** individual identity (`K_epoch` shared), so it cannot leak which introducer even if fully broken | **yes — unconditionally** |
| §4.3 Unlinkability | BBS presentations statistically unlinkable; lattice signatures re-randomized per record; the only shared public values are `(D, epoch)`, already public in the record | yes |
| §4.4 Soundness | **AND-verify** → a forged vouch requires forging **both** the q-SDH BBS credential **and** the `K_epoch` lattice signature → soundness holds **if either is unforgeable**. Pre-quantum: both guard (q-SDH + Module-SIS/LWE). Post-quantum: BBS forgeable, lattice holds. Our-lattice-impl-forgery-bug: BBS holds. | **yes** |

**The headline guarantees:** **anonymity is unconditional** (the strongest possible — and it survives a PQ verifier set, harvest-now-decrypt-later, and even a future break of the lattice half); **soundness is hedged if-either** (a quantum break of BBS *or* a bug in our young lattice port is each individually survived).

### 4.4 Why C2, not C1 or C3 (the rejected alternatives)

- **C1 (two per-introducer proofs, side-by-side) — rejected.** If the lattice half is a per-introducer membership proof, its hidden witness *is* "which introducer," and a classical cryptanalysis break or **a bug in our own lattice port** would deanonymize the graph *despite* BBS (side-by-side, record anonymity is capped at the **weaker** half). That is the exact "silent graph deanonymization" failure the issue names — unhedged for anonymity. C2 fixes this by giving the lattice half no individual identity to leak.
- **C3 (cross-scheme binding — split the introducer witness across both halves) — REOPENED by Codex P1 (see §4.5).** *On the anonymity axis alone*, C3 buys nothing over C2: BBS anonymity is unconditional, so "break both" is unachievable and C3's anonymity collapses to the same unconditional ceiling C2 reaches — for the cost of a novel cross-domain ZK proof (proving one hidden value across the elliptic-curve and module-lattice worlds; no off-the-shelf pattern; highest audit risk). **That was the basis for preferring C2 — but it only considered anonymity.** Codex's P1 shows the *soundness-under-compromise* axis distinguishes them: C2's no-individual-identity property forces a *shared/threshold* lattice key, whose only single-introducer-vouch realization (shared key) has the compromise hole, while its safe realization (threshold-per-vouch) changes onboarding to t-of-n. C3 instead uses **individual, threshold-*issued*** credentials — one introducer vouches alone, a single compromise can't forge (issuance is t-of-n), *and* the binding keeps anonymity unconditional. So C3 may resolve the trilemma C2 cannot. The C2-vs-C3 choice is now genuinely open (§4.5).

### 4.5 The per-vouch-authorization trilemma (Codex DESIGN-review P1) — the central open decision

Three properties we want, of which **any construction can cleanly hold at most two**:

- **(i) one-introducer onboarding** — a new dyad is introduced by *one* attested party it actually knows (the intimate pairing-ceremony model; low join friction).
- **(ii) lattice half carries no recoverable individual identity** — required for *unconditional* (C2) record anonymity; otherwise a break of the lattice half's computational anonymity deanonymizes the graph despite BBS.
- **(iii) single-compromise can't forge** — a single compromised/leaked introducer cannot mint vouches for Sybils (the §6 adversary), *especially* post-quantum when the lattice half is the sole soundness mechanism.

The three candidate resolutions:

| | Lattice half | (i) one-introducer | (ii) unconditional anon | (iii) compromise-safe | Cost |
|---|---|---|---|---|---|
| **C1** | per-introducer key + ZK membership | ✅ | ❌ (computational — break deanonymizes) | ✅ (own key only vouches as self) | lowest crypto risk; weakest anonymity |
| **C2-shared** | one shared `K_epoch` | ✅ | ✅ | ❌ **(Codex P1 — one leak mints all)** | — *eliminated by P1* |
| **C2-threshold** | `t`-of-`n` co-signed per vouch | ❌ (t co-vouchers) | ✅ | ✅ | onboarding friction (t introducers per new dyad) |
| **C3** | individual cred, **threshold-*issued***, bound to the BBS half | ✅ | ✅ (binding ⇒ unconditional via BBS) | ✅ (issuance is t-of-n; a leaked cred only vouches as self) | the novel cross-domain binding proof |

**Updated lean (changed by the review):** with C2-shared eliminated, the real choice is **C2-threshold** (clean crypto, t-of-n onboarding friction) vs **C3** (preserves one-introducer onboarding + unconditional anonymity + compromise-safety, at the cost of the cross-domain binding) vs **C1** (simplest, computational anonymity). If one-introducer onboarding is a hard product requirement, **C3 becomes the principled choice despite its complexity** — which inverts my pre-review recommendation. This is the reserved Fable 5 + Codex construction-choice call (INTRODUCTION_RECORD §5); it should be made with the cryptographer's eye on whether the C3 cross-domain binding is feasible to build soundly in sovereign pure-Rust, or whether C2-threshold's onboarding friction is acceptable.

---

## 5. Wire format + EpochAnchor

### 5.1 `BlindedVouch` bytes

```
BlindedVouch = VOUCH_VERSION (u16)
             ‖ len(P_bbs)     (u32) ‖ P_bbs
             ‖ len(σ_lattice) (u32) ‖ σ_lattice
```

- Length-prefixed, version-tagged, canonical (a frame-cap precedes decode, per the codec-safety rule used in `introduction_record_sync`). Total ≈ tens of KB.
- `VOUCH_VERSION` lets the BBS-only interim (if the build is ever re-phased) and the full dual record be distinguished — though the locked build order is both-at-once, so v1 = dual.

### 5.2 `EpochAnchor` bytes — derivable from the Vita-Chain attested set, **no extra trusted setup**

**Self-delimiting, versioned, tagged encoding (Codex DESIGN-review P2)** — a raw concatenation is not unambiguously parseable (the BBS policy may be a full key-set *or* a root; revocation is optional), so the anchor is framed like `BlindedVouch`: a version, then a tag byte + length prefix per field. Verifiers reject unknown tags / trailing bytes.

The tag set for the lattice field is **conditional on the §4.5 realization** (the anchor does not pre-freeze a C2-only format): C2-threshold publishes the shared epoch verification key (`tag=LATTICE_KEPOCH_PUBLIC`); C3 publishes the epoch issuer key / accumulator for the individual threshold-issued credentials (`tag=LATTICE_EPOCH_ISSUER`). A verifier selects its lattice check by the present tag.

```
EpochAnchor.bytes = ANCHOR_VERSION (u16)
                  ‖ field{ tag=BBS_POLICY_KEYSET | BBS_POLICY_ROOT,            len(u32), bytes }
                  ‖ field{ tag=LATTICE_KEPOCH_PUBLIC | LATTICE_EPOCH_ISSUER,   len(u32), bytes }  // realization per §4.5
                  ‖ field{ tag=REVOCATION_ROOT (OPTIONAL),                     len(u32), bytes }   // absent ⇒ field omitted, not zero-length-ambiguous
```

- **BBS policy** (`tag` distinguishes keyset vs root) = the attested introducer BBS public keys for the epoch, or a Merkle/accumulator root over them; with randomizable-key public verification this is published and verification is public. Derived directly from the chain's attested set → no trusted setup.
- **Lattice anchor** (`tag` distinguishes the §4.5 realization) = C2-threshold's shared epoch verification key, **or** C3's epoch issuer key/accumulator — both **threshold-established** by the attested set at epoch start via DKG (§4.2). Derived from the attested set → no trusted setup. The single-holder shared key is eliminated regardless of tag.
- **Revocation** (⚠️ sign-off): present (a lattice accumulator root, Libert et al. / LaZer-style, over non-revoked introducers) or omitted (epoch-rotation-only) — the tag's presence/absence is unambiguous in the framing above.

### 5.3 Epoch model + churn (⚠️ sign-off — INTRODUCTION_RECORD brief Q5)

- `epoch` scopes both the BBS policy and `K_epoch`. Per-epoch rotation gives the **forward-secret graph** property (§6: a leaked key ≠ retroactive graph) and is the anonymity-set boundary ("attested introducers in this epoch").
- Epoch length trades anonymity-set size (longer = bigger set) against re-keying cost (threshold DKG for `K_epoch` + BBS policy refresh each epoch) and record-refresh frequency (`valid_through_ms`). **Epoch length is a sign-off parameter.**

### 5.4 Public vs validator verification

Verification can be **public** (randomizable-key issuer-hiding, no secret policy key) — so light clients *may* verify, not only validators. The locked "validators verify" stands as the baseline (and is required for the everlasting [2025/2080] policy-key variant if the public-verification variant cannot also be everlasting); public verification is a strict upgrade where available.

---

## 6. Implementation plan (both-at-once) — separate impl issues after sign-off

1. **BBS half** — audited `bls12_381` + BBS base; implement the issuer-hiding presentation layer against the paper test vectors; behind `VouchIssuer`/`VouchVerifier`.
2. **Lattice half** — sovereign pure-Rust transcription of the chosen blind-signature scheme + `K_epoch` (threshold) issuance, against published test vectors; constant-time; behind the same traits.
3. **Composition** — `BlindedVouch` encode/decode (frame-capped) + AND-verify; the `EpochAnchor` derivation from the attested set; replace `StubVouchScheme`.
4. **Integration + smoke (rule #27)** — round-trip issue→present→verify against real BBS + real lattice; gossip-sync ingest (the HYP-337 chunk-3 path) with the real verifier; epoch-rotation + revocation tests at spec thresholds.
5. **[HYP-330] external third-party audit BEFORE any real introduction is published / mainnet.**

Each half is independently testable (rule #27) without the live swarm — the seal/verify round-trips offline against the real primitives, exactly as the inter-dyad path did.

---

## 7. Open sign-off items (what Fable 5 + Codex must resolve) + honest limits (rule #1)

**Sign-off agenda:**
1. **Confirm BBS issuer-hiding is everlasting *for our exact construction*** — and whether a single construction gives **both** everlasting anonymity **and** public verification, or whether we accept validator-held-policy-key verification to keep the everlasting guarantee. (The §4.2 unconditional-anonymity headline rests on this.)
2. **Lattice scheme + parameters at our security level** — confirm the BLNS CCS-2023 base (or a justified alternative), exact params, and **current cryptanalysis status** (lattice blind sigs have a real history of breaks — non-negotiable diligence).
3. **THE central decision — the §4.5 trilemma: C2-threshold vs C3** (vs C1). Shared-key C2 is eliminated (Codex P1). Decide with the cryptographer's eye on (a) whether the C3 cross-domain binding is buildable soundly in sovereign pure-Rust, vs (b) whether C2-threshold's t-of-n onboarding friction is acceptable, vs (c) accepting C1's computational anonymity. Drives the threshold compromise parameter `t`, the DKG, and churn cadence.
4. **Test-vector availability** for the pure-Rust transcription, and the ARM constant-time strategy.
5. **Revocation** — accumulator-in-anchor vs epoch-rotation-only.
6. **Epoch length.**
7. **HYP-330 audit scope** — research-artifact-derived code vs hardened port.

**Honest limits:**
- This proposal **selects a construction and argues its properties; it does not prove them.** The property argument (§4.3) is an engineering argument, not a security proof. The sign-off + HYP-330 audit are the proof gates.
- The §4.2 **unconditional-anonymity** claim is contingent on item (1) above holding for our exact issuer-hiding construction. Marked accordingly.
- Lattice params, test-vector availability, and current-cryptanalysis status are **UNVERIFIED** here.
- The sovereign pure-Rust lattice port is the **highest-risk crypto in the arc**; "design-first" exists precisely because a correctness gate cannot catch a silent anonymity/forgery bug in it.

---

## 8. Sources

- BBS Signature Scheme — IETF CFRG `draft-irtf-cfrg-bbs-signatures` (statistical anonymity; §6.9 quantum asymmetry).
- Katz & Šefránek, *Issuer Hiding for BBS-Based Anonymous Credentials*, eprint **2025/2080** (everlasting issuer-hiding anonymity; GGM; policy-key verification).
- *Improved Issuer Hiding for BBS-based Anonymous Credentials*, eprint **2026/555** (AGM; removes secret policy keys → public verification).
- *Issuer-Hiding for BBS Anonymous Credentials via Randomizable Keys*, eprint **2026/369** (public verification via randomizable keys).
- Beullens, Lyubashevsky, Nguyen, Seiler, *Lattice-Based Blind Signatures: Short, Efficient, and Round-Optimal*, CCS 2023, eprint **2023/077** (20 KB, standard Module-SIS/LWE+NTRU).
- Faller & Niot, *Lattice-Based Threshold Blind Signatures*, eprint **2025/1566**.
- The LaZer Library (lattice ZK), CCS 2024, eprint **2024/1846**; code MIT (C / x86 / AVX-512 — excluded by the sovereign-Rust lock, used only as a reference).
- Libert, Ling, Mouhartem, Nguyen, Wang, *ZK Arguments for Lattice Accumulators*, J. Cryptology 2023 (accumulators / revocation).
- Rust lattice-ZK substrates: `lattirust`, `Lazarus`.

| Version | Author | Notes |
|---|---|---|
| 2026-06-13 v0.1 | Iris | HYP-338 design proposal. Dual-hybrid (BBS = unconditional anonymity; lattice = PQ soundness; AND-verify), build order both-at-once, after a co-design walk-through + primary-literature verification of BBS statistical anonymity. Initially locked composition C2. |
| 2026-06-13 v0.2 | Iris | Folded in the Codex DESIGN-review: **P1** — shared-key C2 has a compromised-introducer soundness hole (post-quantum, the lattice half is the sole soundness mechanism), so threshold holding is mandatory and the §4.5 per-vouch-authorization trilemma **reopens C2-threshold vs C3** as the central sign-off decision (C3's individual-but-threshold-issued credentials may now be the principled choice — inverting the v0.1 lean). **P2** — `EpochAnchor` now uses a self-delimiting versioned+tagged encoding. Pending re-review + Fable 5 + Codex sign-off. |
