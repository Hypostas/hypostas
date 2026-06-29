# VOUCH_TRAIT_RESHAPE_DESIGN.md — HYP-343: wire the real C3 vouch behind the protocol-core trait

**Status:** design-first (no code yet). Gate: Codex `review --base` gpt-5.5/high before any build chunk.
**Refs:** `ISSUER_HIDING_DESIGN.md` chunk 3 (this is its detailed home); `LNP22_SHOW_DESIGN.md` §1.6
(live path = wrapped only); `INTRODUCTION_RECORD_CRYPTO_DESIGN` §4 (the four properties).
**Crates:** `protocol-core/src/introduction_record/mod.rs` (the shell traits) ← `vouch-crypto` (the crypto).

---

## 0. The spine

The C3 crypto is **done + gate-clean**: `vouch-crypto::pq_vouch` has the full dual-hybrid
`PqBlindedVouch` (BBS bound presentation + LNP22 SEP-credential show + cross-domain anchor + PQ LWR
nullifier, AND-verified under one shared `C_r`) and the issuer-hidden live entry
`verify_issuer_hidden(params, &EpochIntroducerAnchor, vouch)`; `blind_issuance` has request/issue/finalize
→ `DualCredential`; `codec` has `PqBlindedVouch::to_bytes` (v3). What is missing is **the seam**: the
protocol shell (`introduction_record`) still runs on `StubVouchScheme` (non-crypto). HYP-343 replaces the
stub with a real scheme backed by `vouch-crypto`, retiring the placeholder for the live path.

**This is mostly integration wiring — with ONE real soundness gap to close** (§4): the shell binds a vouch
to `(introduced, RecordContext)`; `pq_vouch` today binds only to `(w_introducer, epoch)`. That gap is
closed by FS-context binding, a small change to a soundness-bearing transcript — hence design-first.

---

## 1. What exists vs. what HYP-343 adds

| Layer | Exists (gate-clean) | HYP-343 adds |
|---|---|---|
| Crypto compose | `pq_vouch::{prove, verify, verify_issuer_hidden}`, `PqBlindedVouch` | FS-context binding to `(introduced,ctx)` (§4) |
| Issuance | `blind_issuance::{request, issue, finalize}`, `DualCredential`, `UpkLedger` | map onto `VouchIssuer` 3-step |
| Anchor | `EpochIntroducerAnchor::SharedKey{epoch,sep_key,bbs_pk}` | ↔ shell `EpochAnchor{epoch,bytes}` codec |
| Serialize | `PqBlindedVouch::to_bytes`, `BlindRequest/BlindResponse::to_bytes` | `EpochIntroducerAnchor` (de)serialize |
| Shell | `VouchVerifier`/`VouchIssuer` traits, `StubVouchScheme`, `EpochAnchor`, `RecordContext` | `PqVouchScheme` impl |
| Dep | — | `protocol-core → vouch-crypto` (feature-gated) |

---

## 2. The trait reshape — `PqVouchScheme`

A new `PqVouchScheme` (in `protocol-core`, behind a `pq-vouch` feature that pulls in `vouch-crypto`)
implementing BOTH `VouchVerifier` and `VouchIssuer`. The shell traits stay **byte-opaque** (the §1.6
"shell treats the vouch as opaque bytes" requirement is preserved); `PqVouchScheme` is the interpreter.

- `BlindedVouch(Vec<u8>)` = `PqBlindedVouch::to_bytes()` (codec v3). `verify_vouch` deserializes (size-cap
  first per `INTRO_MAX_VOUCH_LEN`, then `from_bytes`), rebuilds the `EpochIntroducerAnchor` from
  `EpochAnchor.bytes`, derives the FS context from `(introduced, ctx, epoch)`, and calls
  `pq_vouch::verify_issuer_hidden`. **Live path uses ONLY `verify_issuer_hidden`** (never the named-key
  `verify`) — the §1.6 issuer-hiding requirement made mechanical.
- `EpochAnchor.bytes` = serialized `EpochIntroducerAnchor` (epoch + `SepVerifyKey` + `bbs_pk` G2). The
  shell's `epoch` field MUST equal the embedded anchor's epoch (cross-check, fail closed) — mirrors the
  existing `verify_issuer_hidden` params↔anchor consistency check, lifted to the wire boundary.

---

## 3. Modeling decision — where the credential→show step sits

`pq_vouch` is an **anonymous credential** (issue once → show, unlinkably). The shell's `VouchIssuer` is
`blind_request → blind_sign → unblind → BlindedVouch`. The natural map:

- `blind_request` (D) ↔ `blind_issuance::request` → `(VouchRequest, UnblindState)` carrying the
  serialized `BlindRequest` + `BlindState`.
- `blind_sign` (B) ↔ `blind_issuance::issue` → `BlindResponse`.
- `unblind` (D) ↔ `blind_issuance::finalize` → **`DualCredential`**, *then* `pq_vouch::prove` (the SHOW)
  → `PqBlindedVouch` → `BlindedVouch` bytes.

**The fork (Q1 for the gate):** does `unblind` return the credential *and* a first show (fold show into
unblind), or does the trait gain a separate `present(credential, introduced, ctx) → BlindedVouch`?

- **Recommendation: fold the show into `unblind`** for HYP-343. The introduction-record use case publishes
  **one** record → **one** show per credential; issue-once-show-many unlinkability is not exercised by the
  intro-record path. Folding keeps the existing 3-method trait surface intact (no new method, smaller
  blast radius). BUT `unblind` then needs `(introduced, ctx)` to scope the show — they must ride in
  `UnblindState` (D produced them in `blind_request`, so this is free + keeps them D-side-secret).
- The `present`-as-its-own-method variant is the documented upgrade if a credential is ever shown to >1
  record (kept as a note, not built).

---

## 4. THE soundness gap — binding the vouch to `(introduced, RecordContext)` (Q2, the gate's focus)

**Contract** (`verify_vouch`): `Ok(())` **iff** an attested introducer in `epoch` vouched **for
`introduced`**, **bound to `ctx`** (§4.2 anti-replay). **Today `pq_vouch` binds neither `introduced` nor
`ctx`** — it binds `w_introducer` (BBS+SEP credential, nullifier `N=round(a_epoch·w)`) + `epoch` (anchor
epoch + nullifier base). So as-is, an introducer's published vouch could be **lifted to a different
`introduced` or a different record** (extended `valid_through`, etc.).

**Why not fold `(introduced,ctx)` into the nullifier base `a_epoch`?** That makes `N` per-record, so the
same introducer producing two records gets two different `N` → the k=1 per-epoch rate-limit (HYP-346,
one-introducer-per-onboarding) **silently breaks**. The nullifier base MUST stay epoch-only.

**Proposed mechanism — FS-context binding (the standard "proof is a signature over a message").** Thread a
`context: &[u8]` into the show's Fiat-Shamir so the challenge `c = fs_agg(t_a,t_b,w,t0,t1, context)`
depends on it. The protocol-core sets `context = H("hyp343-vouch-ctx/v1" ‖ introduced ‖ ctx.0 ‖
epoch_bytes)`. Any change to `(introduced,ctx,epoch)` ⇒ different `c` ⇒ the proof fails to verify. The
nullifier base is untouched ⇒ rate-limit preserved. Cost: a `&[u8]` argument threaded through
`fs_agg` + `prove_agg`/`verify_agg` + `pq_vouch::{prove, verify, verify_issuer_hidden}` (+ a new domain
tag). Small, mechanical, but it edits a soundness-bearing transcript ⇒ **gate it**.

**Open gate questions (Q2a–c):**
- **Q2a — which sub-proofs must absorb `context`?** The show (`fs_agg`) binds the SEP possession + norms +
  nullifier (the nullifier rides the show's extra-families). The **anchor** is bound to the show via the
  shared `t_A`; the **BBS half** is bound via the shared `C_r`. CLAIM: absorbing `context` into the
  show's `fs_agg` binds the whole vouch (the other halves are non-malleably tied to it through `t_A`/`C_r`).
  The gate must confirm this — OR require the BBS half's Schnorr FS to also absorb `context` (defense in
  depth against a BBS-half swap that keeps `C_r`).
- **Q2b — is `introduced` a member-`w`-style commitment, or pure FS context?** Pure FS context is simplest
  and sufficient for "this proof is *about* this introduced+record". A stronger in-circuit binding
  (commit `introduced` in `t_A`) is heavier and only needed if `introduced` must be *extractable* — it is
  not (the record names `introduced` in the clear). Recommend pure FS context.
- **Q2c — `RecordContext` redundancy audit.** With `w`-binding (introducer), the epoch nullifier
  (one-per-epoch), and the anchor-epoch check already present, exactly what residual replay does the `ctx`
  digest stop? (Hypothesis: same-introducer, same-epoch, *tampered `valid_through`/`issued_at`* — within
  the epoch window. The FS context covers it.) Document the precise residual threat so the binding is
  justified, not cargo-culted.

---

## 5. Dependency

`protocol-core` gains an optional `vouch-crypto` dep behind a `pq-vouch` feature (default-off, mirroring
`experimental-unaudited` — `vouch-crypto` is still params-provisional until HYP-330). `StubVouchScheme`
stays for tests/non-`pq-vouch` builds; `PqVouchScheme` is the live impl when the feature is on. This keeps
the shell buildable without the heavy lattice stack and matches the staged release gate (HYP-324 mechanism
+ HYP-330 params + HYP-343 wiring are the three gates; none flips `experimental-unaudited` alone).

---

## 6. Serialization mapping

- `BlindedVouch.0` = `PqBlindedVouch::to_bytes()` / `from_bytes` (v3, exists). Size-cap before decode.
- `EpochAnchor.bytes` = `EpochIntroducerAnchor` (de)serialize (NEW small codec: epoch u64 + `SepVerifyKey`
  via `CanonicalSerialize` + `bbs_pk` G2 — reuse codec.rs `put_ark`). Bound by `INTRO_MAX_ANCHOR_LEN`.
- `VouchRequest`/`BlindResponse`/`UnblindState` = the `blind_issuance` `BlindRequest`/`BlindResponse`/
  (`BlindState` + `introduced` + `ctx`) `to_bytes` (exist; `BlindState` needs a codec or is opaque-held).

---

## 7. Test plan (rule 27 — integration + smoke, both required)

- **Smoke:** `PqVouchScheme` instantiated via its production constructor; one `verify_vouch` over a
  real `prove`-produced vouch returns `Ok`.
- **Integration (the real assertions):**
  1. **Happy path:** request→sign→unblind→`BlindedVouch`→`verify_vouch` = `Ok` (full ceremony).
  2. **§4.2 anti-replay:** a vouch minted for `ctx_1` (record R1) → `verify_vouch(.., ctx_2)` = `Err`
     (the FS-context binding bites). And a vouch for `introduced_1` → `verify_vouch(introduced_2, ..)` = `Err`.
  3. **Wrong epoch:** `EpochAnchor.epoch ≠ record.epoch` ⇒ `Err` (cross-check + nullifier base mismatch).
  4. **Issuer-hiding:** two vouches by two distinct introducers under one shared `B_epoch` both `verify`,
     and the transcripts are equal-in-distribution (the anonymity assertion; reuse the statistical-ZK
     harness). [Blocked on the two-trapdoors-for-one-`B` helper — `#[ignore]` until §5 establishment.]
  5. **Size DoS:** an over-`INTRO_MAX_VOUCH_LEN` vouch is rejected before decode (no alloc-bomb).
  6. **Malformed bytes:** truncated/trailing/non-canonical vouch ⇒ `Err(Invalid)`, never panic.

---

## 8. Build order (each chunk: tests + Codex gpt-5.5/high gate)

0. **Gate THIS design** (Q1 modeling, Q2a–c soundness). Resolve before any code.
1. **FS-context binding** in `vouch-crypto` (`fs_agg` + `prove_agg`/`verify_agg` + `pq_vouch::{prove,
   verify,verify_issuer_hidden}` take `context: &[u8]`; new domain tag). Regression test: a vouch with
   context A fails verify under context B. **Gate (soundness-bearing).**
2. **`EpochIntroducerAnchor` codec** (to/from bytes) + the `EpochAnchor.epoch == embedded epoch` cross-check.
3. **`PqVouchScheme`** in `protocol-core` (feature `pq-vouch`): `VouchVerifier` (deserialize → context →
   `verify_issuer_hidden`) + `VouchIssuer` (3-step → `blind_issuance` + folded show). The §7 tests.
4. **Retire `StubVouchScheme` from the live path** (keep `#[cfg(any(test, not(feature="pq-vouch")))]`);
   point `introduction_record` + `hypostas-network` sync at `PqVouchScheme` when the feature is on.
5. **PQ_VOUCH_WIRING §8/§9 update** — mark HYP-343 wiring landed; the `experimental-unaudited` flip still
   waits on HYP-330 params (one of the three release gates).

---

## 9. Open questions for the gate + Josh

- **Q1 (modeling):** fold the show into `unblind` (recommended) vs. a separate `present` method?
- **Q2a–c (soundness):** the FS-context binding scope + the `RecordContext` residual-threat audit (§4).
- **Q3 (establishment, already decided):** epoch key = (a-ii) threshold/DKG (Josh, 2026-06-28) — a runtime
  contract (HYP-324 ch4 / `RUNTIME_REQUIREMENTS`), establishment-agnostic to this wiring.
