# VOUCH_TRAIT_WIRING_DESIGN.md — wiring the C3 vouch into `protocol_core::{VouchIssuer, VouchVerifier}` (HYP-343)

**Issue:** HYP-343 — retire `StubVouchScheme` and implement the protocol-core vouch traits with the real
dual-hybrid C3 crypto (`vouch-crypto`), so the live introduction-record path mints + verifies real
PQ-sound, issuer-hidden, everlasting-anonymous vouches. One of the three release gates that drop
`experimental-unaudited` (with HYP-330 params + HYP-324 issuer-hiding, whose *mechanism* is now landed).

**Refs:** `protocol-core/src/introduction_record/mod.rs` (the traits + `StubVouchScheme` + the opaque
types); `vouch-crypto::{pq_vouch, blind_issuance, issuer_hiding, codec}`; `ISSUER_HIDING_DESIGN.md`
(HYP-324, the anchor); `PQ_VOUCH_WIRING_DESIGN.md` (the composed `PqBlindedVouch`); `INTRODUCTION_RECORD.md`
§4.1 (blind issuance), §4.2 (record-context anti-replay), §5.3 (relationship secrecy).

**Process:** design-first → Codex DESIGN-review → build chunks (each gated, rule 27). Nothing here is
built yet. The dependency direction is fixed: **`vouch-crypto` → `protocol-core`** (vouch-crypto impls
protocol-core's traits; protocol-core never depends on vouch-crypto — no cycle). This is the trait-impl
chunk the `vouch-crypto/Cargo.toml` note reserved (blake3→cc re-enters here, accepted).

---

## 0. The mechanism (the spine)

`protocol-core` owns the *abstraction*: opaque `BlindedVouch(Vec<u8>)`, `EpochAnchor { bytes }`,
`RecordContext([u8;32])`, the 3-party `VouchIssuer` (`blind_request`/`blind_sign`/`unblind`), and
`VouchVerifier::verify_vouch`. `vouch-crypto` owns the *construction*: `PqBlindedVouch` (BBS half + LNP22
show + anchor + nullifier, already composed + `to_bytes`), `EpochIntroducerAnchor` (the shared epoch
`(sep_key, bbs_pk)`), and the `blind_issuance` `OblSign` flow. HYP-343 is the **adapter**: a new
`C3VouchScheme` in `vouch-crypto` that impls both protocol traits by (de)serialising across the two type
worlds and **binding the record context into the proof**. The stub's SHA-256 marker is replaced by real
crypto; the trait signatures do NOT change (they were already shaped for blind, dual-hybrid, anchored,
context-bound vouches — `verify_vouch` already takes `introduced`/`epoch`/`anchor`/`ctx`).

---

## 1. THE CENTRAL SOUNDNESS POINT — context binding ≠ epoch scope (the §4.2 vs HYP-346 separation)

`verify_vouch` must enforce **two independent bindings**, and conflating them breaks one:

- **Epoch (the nullifier base, HYP-346 one-introduction-per-epoch).** `N = F_w(epoch)`; the ledger
  rejects a repeated `N`, so a member gets ONE introduction per epoch. The nullifier base MUST be
  `epoch` alone.
- **Record context (the §4.2 anti-replay).** A vouch minted for record `R1 = (introduced1, ctx1)` must
  NOT verify under `R2 = (introduced2, ctx2)`. So `(introduced, ctx)` must bind into the **proof's
  Fiat–Shamir transcript**.

⚠️ **The trap:** the obvious "fold `(introduced, ctx)` into the vouch-crypto `epoch: &[u8]` scope" makes
the nullifier base `= H(epoch‖introduced‖ctx)`, so a member could mint a fresh-`N` introduction per
record (vary `ctx`) — **defeating one-introduction-per-epoch**. So the two bindings CANNOT share the
scope input. The fix: **add a separate `context: &[u8]` input to the vouch-crypto prove/verify** that
binds into the FS challenge (and ONLY there), leaving `epoch` as the sole nullifier base.

**The crypto-layer change (the one real `vouch-crypto` API delta):** `pq_vouch::{prove, verify}` and
`verify_issuer_hidden` gain a `context: &[u8]` parameter that is absorbed into the show's Fiat–Shamir
hash (the same transcript that already binds `epoch`, `t_A`, `c_r`, `N`). `context` does NOT touch
`epoch_base`/`N`. Prover and verifier must absorb identical `context` bytes. (Implementation: thread
`context` into `prove_show_agg_with_extra`'s FS seed / the challenge derivation — a localized addition,
no relation change.) The adapter sets `context = SHA-256("hyp343/ctx/v1" ‖ introduced ‖ ctx.0)`.

**Soundness:** `epoch` ⇒ per-epoch `N` (HYP-346 intact); `context` in FS ⇒ a proof is bound to its
record (§4.2: a different `introduced`/`ctx` ⇒ a different challenge ⇒ the masked-opening responses no
longer verify). The two are orthogonal and both enforced. *This is the DESIGN-review's primary target.*

---

## 2. Type adapter (the (de)serialisation map)

| protocol-core (opaque) | vouch-crypto (concrete) | via |
|---|---|---|
| `BlindedVouch(Vec<u8>)` | `PqBlindedVouch` | `PqBlindedVouch::to_bytes` / `from_bytes` (codec v3); length ≤ `INTRO_MAX_VOUCH_LEN` (256 KiB) checked first |
| `EpochAnchor { bytes }` | `EpochIntroducerAnchor::SharedKey { epoch, sep_key, bbs_pk }` | a new `epoch_anchor` codec: `version ‖ epoch ‖ sep_key ‖ bbs_pk` (the verifier rebuilds `PqVouchParams::from_epoch_anchor` from it); `anchor.epoch` MUST equal the `epoch` arg (caller contract, re-checked) |
| `RecordContext([u8;32])` | `context: &[u8]` (FS) | `SHA-256("hyp343/ctx/v1" ‖ introduced ‖ ctx.0)` — §1 |
| `VouchRequest(Vec<u8>)` | `blind_issuance::BlindRequest` | `BlindRequest::to_bytes` / `from_bytes` (codec v4) |
| `BlindResponse(Vec<u8>)` | `blind_issuance::BlindResponse` | `BlindResponse::to_bytes` / `from_bytes` |
| `UnblindState(Vec<u8>)` | the `D`-side secret (`ru`, `s`, `s_prime`, …) | a new `unblind_state` codec; **never sent** (§4.1) |
| `VouchError` | `MycoError`-style / `Option<_>` | map: bad length → `TooLarge`; decode/verify fail → `Invalid` |

`EpochAnchor.bytes` is bounded + the codec is hardened like the others (length-prefixed, complete-frame,
no alloc-bomb). A malformed anchor ⇒ `VouchError::Invalid`, never a panic.

---

## 3. `VouchVerifier` impl (the immediately-buildable half)

```rust
fn verify_vouch(&self, vouch: &BlindedVouch, introduced: &DyadId, epoch: u64,
                anchor: &EpochAnchor, ctx: &RecordContext) -> Result<(), VouchError> {
    if vouch.0.len() > INTRO_MAX_VOUCH_LEN { return Err(TooLarge { .. }); }     // alloc-bomb guard first
    let anchor = EpochIntroducerAnchor::from_bytes(&anchor.bytes)?;             // rebuild shared (sep,bbs)
    if anchor.epoch() != epoch { return Err(Invalid); }                        // caller-contract recheck
    let params = PqVouchParams::from_epoch_anchor(&anchor, bbs_params(), KAPPA);
    let pq = PqBlindedVouch::from_bytes(&vouch.0)?;
    let context = ctx_bytes(introduced, ctx);                                  // §1 record binding
    if verify_issuer_hidden_ctx(&params, &anchor, &context, &pq) { Ok(()) } else { Err(Invalid) }
}
```
The verifier is self-contained (the vouch already composes both halves); it reuses HYP-324's
`verify_issuer_hidden` extended with `context` (§1). `bbs_params()`/`KAPPA` are protocol constants (the
generators are global; only the *keys* are per-epoch + anchored).

---

## 4. `VouchIssuer` impl (the 3-party blind flow → `OblSign`)

Maps the interactive trait onto `blind_issuance` (Model B `OblSign` + blind-BBS), all already built:
- **`blind_request(introduced, epoch, anchor, ctx)`** → `D` runs `blind_commit` (SEP `c_u` + BBS
  `C_b`, hiding `w`) + the well-formedness `π`; returns `VouchRequest = (c_u, π, C_b, upk)` and keeps
  `UnblindState = (ru, s, s_prime)`. `introduced`/`ctx` are NOT sent (§4.1) — they bind only at show
  time via §1 (issuance and show are separate ceremonies, BLIND_ISSUANCE §4/Q5).
- **`blind_sign(request, epoch, anchor)`** → `B` (holding the epoch `R_epoch`) verifies `π` + the `upk`
  quota, `apply_tagged_with` → `BlindResponse`. `B` learns nothing about `introduced`/`ctx`/`w`.
- **`unblind(response, state)`** → `D` unblinds to a `DualCredential`, then *composes* the
  `PqBlindedVouch` for the record (this is where `prove(... context ...)` runs) → `BlindedVouch`.

⚠️ **Open (§7 Q2):** the trait's `unblind` takes only `(response, state)` — but composing the vouch
needs `introduced`/`ctx`/`anchor` (the show binds them). Either (a) `unblind` is "produce the credential"
and a separate `VouchVerifier`-side `compose_vouch(cred, introduced, epoch, anchor, ctx)` mints the
record-bound vouch, or (b) `UnblindState` carries the record params so `unblind` can finish. (a) is
cleaner (issuance ceremony ≠ record minting) and matches "one credential, many records" — **lean (a)**,
which may need a tiny trait addition (a `VouchMinter::mint`); flag for review.

---

## 5. The dependency + the `C3VouchScheme` home

`vouch-crypto` adds `protocol-core` as a dep (blake3→cc accepted here — the note in
`vouch-crypto/Cargo.toml` reserved this exact chunk). `C3VouchScheme` lives in a new
`vouch-crypto/src/scheme.rs` behind `experimental-unaudited`, holding the protocol constants
(`bbs_params`, `KAPPA`) + (for the issuer role) the member/issuer key material. The runtime swaps
`StubVouchScheme` → `C3VouchScheme` only after all three release gates (HYP-324 ∧ HYP-330 ∧ HYP-343);
until then `StubVouchScheme` stays as the protocol-test driver and `C3VouchScheme` is `experimental`.

---

## 6. Build order (each chunk: tests + Codex gpt-5.5/high gate)

1. **`context` FS-binding in `vouch-crypto`** (§1) — add `context: &[u8]` to `pq_vouch::{prove, verify}`
   + `verify_issuer_hidden`, absorbed into the show FS only. Regression: a vouch proven under `context1`
   fails verify under `context2`; the nullifier `N` is unchanged by `context` (so one-introduction-
   per-epoch holds across different `context`). **This is the soundness-critical chunk.**
2. **Codecs** — `EpochIntroducerAnchor` (`epoch‖sep_key‖bbs_pk`) + `UnblindState` round-trip codecs,
   hardened (bounded, complete-frame). Adversarial: truncated/over-long/garbled frames → `Invalid`.
3. **`C3VouchScheme: VouchVerifier`** (§3) — the dep + the scheme type + verify. Integration (rule 27):
   a real composed vouch round-trips protocol-core `verify_vouch` Ok; a wrong `introduced`/`ctx`/`epoch`/
   foreign anchor each reject (the §4.2 + issuer-hiding + epoch guards, end-to-end through the trait).
4. **`C3VouchScheme: VouchIssuer` (+ mint)** (§4) — the 3-party flow → a record-bound vouch that
   `verify_vouch` accepts; the `upk` quota enforced; `B` never sees `introduced`/`w`. Capstone (rule 27):
   `blind_request → blind_sign → unblind → mint → verify_vouch` end-to-end, issuer-blind.
5. **Retire `StubVouchScheme` from the live path** — gate it `#[cfg(test)]` / keep as the protocol-test
   driver; the runtime's `IntroductionRecord` path takes a `VouchVerifier`/`VouchIssuer` (already does).
   Update `PQ_VOUCH_WIRING_DESIGN.md` §9 (HYP-343 landed). The `experimental-unaudited` drop stays gated
   on HYP-330 (params) + HYP-324 establishment (§5 Q1).

---

## 7. Open questions (Codex DESIGN-review + Josh)

- **Q1 (DESIGN-review, soundness): the §1 `context` FS-binding.** Confirm absorbing `context` into the
  show challenge (and ONLY there) gives §4.2 anti-replay WITHOUT perturbing the nullifier / one-
  introduction-per-epoch. Is FS-absorption sufficient, or must `context` also bind a committed witness
  coordinate? (Lean: FS-absorption suffices — it's the standard statement-binding for a Σ/FS proof.)
- **Q2 (DESIGN-review, API): `unblind` vs `mint`** (§4) — does composing the record-bound vouch belong in
  `unblind` (needs the record params in `UnblindState`) or a new `mint(cred, introduced, epoch, anchor,
  ctx)`? Lean: a separate mint (issuance ≠ record-binding; one credential → many records).
- **Q3 (Josh, ops): `bbs_params()` + `KAPPA` provenance.** The BBS generators + the anchor κ are protocol
  constants. Confirm they live in a shared protocol-constants module (not duplicated) — ties to HYP-330.
- **Q4 (DESIGN-review): codec versioning.** `EpochAnchor`/`UnblindState` get new codec versions; confirm
  they're distinct tags from the existing v1/v3/v4 (`codec.rs`) and round-trip-tested.

---

## 8. DESIGN-review log

*(to be appended by the Codex gpt-5.5/high DESIGN-review before any code)*
