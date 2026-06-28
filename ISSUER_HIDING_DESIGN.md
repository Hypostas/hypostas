# ISSUER_HIDING_DESIGN.md — the HYP-324 issuer-hiding wrapper (candidate (a): shared epoch key)

**Issue:** HYP-324 — the release gate that flips the C3 vouch's lattice show from TEST-ONLY (verifies
against a *named* introducer key, leaking which introducer signed) to live (verifies against a
per-epoch *shared* anchor, hiding which introducer signed in a multi-introducer epoch). Without it,
`experimental-unaudited` MUST NOT drop — a live vouch under a named `vk` is an anonymity break
(LNP22_SHOW §1.6, PQ_VOUCH_WIRING §9, THREAT_MODEL §5.3 relationship-secrecy).

**Refs (our construction — no external transcription; Codex DESIGN-review is the gate):**
`LNP22_SHOW_DESIGN.md` §1.6 + chunk 5.9; `LATTICE_SIG_PROTOCOLS_DESIGN.md` (`EpochIntroducerAnchor`);
`PQ_VOUCH_WIRING_DESIGN.md` §9; the live code `sep_sig::SepVerifyKey` (`b = B = A·R`) +
`pq_vouch::{PqVouchParams.sep_vk, verify}`.

**Process:** design-first → Codex DESIGN-review gate → build chunks (each gated, rule 27). Nothing
here is built yet. **Candidate DECIDED = (a) shared epoch key** (Iris, autonomous under the standing
goal; the minimal-surface, relation-unchanged, sovereign path — (b) committed-key + accumulator
membership is retained in §7 as the documented upgrade and is the one that would need explicit buy-in
for a new ZK subsystem). The one genuine sub-fork — how the shared key is *established* sovereignly —
is isolated in §5 and surfaced as the §8 Q1 (Josh), and the buildable core (§4) does **not** depend on
its resolution.

---

## 0. The one-paragraph mechanism (the spine)

Today the SEP credential's public params split into **global constants** `(A, u, D_s, D)` — identical
for every introducer — and the **issuer-identifying** key `B = A·R`, where `R` is the issuer's secret
trapdoor (`sep_sig::SepVerifyKey.b`). The show proves, in ZK, that the holder owns a credential `σ`
that verifies under a *specific* `B` — so a verifier that knows `B` learns *which* introducer signed.
Candidate (a) makes `B` a **per-epoch shared key `B_epoch`**: every introducer authorised for an epoch
signs credentials that verify under the one `B_epoch` (they hold a trapdoor `R_epoch` with
`A·R_epoch = B_epoch`). The verifier checks the show against `B_epoch` and learns only "signed by *an*
authorised introducer of this epoch" — the anonymity set is the whole epoch introducer-set. **The §1
show relation is unchanged**: `B_epoch` is a `SepVerifyKey` like any other; only the *provenance* of
`B`'s value changes. The wrapper is therefore a thin type (`EpochIntroducerAnchor`) + a plumbing swap,
not new ZK.

---

## 1. The leak this closes (LNP22_SHOW §1.6)

`verify_show(vk_pub, …)` is **TEST-ONLY**: a named `vk_pub` reveals the introducer. A live vouch is
shown to a relay / peer (Tier-4, a *compromised mailbox/relay operator* in scope per THREAT_MODEL
§4.4). Relationship-secrecy (§5.3) requires that operator learn nothing about *who introduced whom*.
In a single-introducer epoch the introducer identity is trivially the epoch's one key, so issuer-hiding
is only meaningful when an epoch has **>1 introducer** — then the named-key verifier would partition
vouches by introducer. Candidate (a) collapses every epoch introducer onto one `B_epoch`, so the
verify transcript is **independent of which introducer signed**.

---

## 2. Construction (candidate (a))

Public, per epoch `e`: the global `(A, u, D_s, D)` (unchanged constants) + the epoch issuer key
`B_epoch^{(e)} ∈ R_p^{d×dk}`. Secret, held by **each** introducer authorised for epoch `e`: a trapdoor
`R_epoch^{(e)}` with `A·R_epoch^{(e)} = B_epoch^{(e)}` (so each can `apply_tagged_with` / `OblSign`).

- **Issue (OblSign, §BLIND_ISSUANCE):** unchanged except the introducer uses `R_epoch` (not a personal
  `R`). The credential `σ = (t, v)` verifies under `B_epoch`.
- **Show (`proof_show`/`pq_vouch`):** unchanged relation — `vk_pub := the epoch anchor's B_epoch`.
- **Verify (`pq_vouch::verify`):** takes an `EpochIntroducerAnchor` (which, under (a), *is* the epoch
  `SepVerifyKey`) instead of a named introducer key; everything downstream is identical.

**Anonymity (introducer-hiding).** Two credentials issued by introducers `i ≠ j` of the same epoch
verify under the **same** `B_epoch` and (post-show) are computationally indistinguishable: the show is
statistical-ZK over the relation, and the relation's only issuer-dependent input is `B_epoch`, which is
shared. So the verify transcript is identical in distribution regardless of `i` — perfect hiding within
the epoch introducer-set, *given* both hold `R_epoch`. The anonymity set size = |epoch introducers|;
a single-introducer epoch hides nothing (correctly — §1).

**PQ soundness (unforgeability) is preserved.** Forging a credential under `B_epoch` without a valid
`R_epoch` is exactly SEP EUF-CMA under the key `B_epoch = A·R_epoch` — the same M-SIS hardness as any
SEP key (JRS23). Sharing the trapdoor across the epoch introducer-set does **not** weaken soundness
against *users / outsiders*; it only means epoch introducers can sign *for each other* (§3 trust).

**Nullifier / Sybil unaffected.** `N` is keyed on the *user's* bound secret (`w`/`k`, HYP-346), and the
`upk` rate-limit is user-side (BLIND_ISSUANCE §2). Sharing the *introducer* trapdoor changes neither —
one-introducer-per-onboarding and per-user issuance quotas are orthogonal to which introducer key
signed.

---

## 3. The trust this assumes (stated honestly)

Under (a), every introducer of epoch `e` holds `R_epoch^{(e)}` ⇒ **any epoch introducer can issue a
credential attributable only to the epoch, not to itself** — mutual issuance power within the
authorised set. This is the deliberate trade of (a): **per-epoch accountability, not per-introducer**.
It is acceptable because the epoch introducer-set is precisely the set the protocol has *authorised to
introduce* in that epoch; a member misusing the shared key cannot exceed what the set is collectively
trusted to do, and the misuse is bounded to one epoch (rotation, §5/§6). Per-introducer accountability
+ revocation is the property candidate (b) buys with a ZK accumulator-membership proof (§7); (a)
forgoes it by design. **Revocation granularity under (a): per epoch** — a revoked introducer is simply
excluded from the next epoch's `R_epoch` distribution; the current epoch's `B_epoch` is not retroac­
tively unsignable (bounded-harm, documented).

---

## 4. The buildable core (relation unchanged) — decoupled from §5

This is what lands now; it does **not** depend on the §5 setup fork (the core consumes a `B_epoch`
*whatever* produced it).

- **`EpochIntroducerAnchor` (new type, `vouch-crypto`).** Under (a):
  ```rust
  /// HYP-324 issuer-hiding anchor. Candidate (a): the per-epoch SHARED issuer verify key. The vouch
  /// verifies against this, not a named introducer key, so the verify transcript hides WHICH epoch
  /// introducer signed (anonymity set = the epoch introducer-set). `epoch` binds the anchor to its
  /// validity window; `B_epoch` is the shared `SepVerifyKey`. (Candidate (b) would replace `key`
  /// with a commitment + membership root — see ISSUER_HIDING_DESIGN §7; the enum leaves room.)
  pub enum EpochIntroducerAnchor {
      /// (a) shared epoch key — the live default.
      SharedKey { epoch: u64, key: SepVerifyKey },
      // (b) Committed { epoch: u64, root: AccumulatorRoot }  // §7, not built
  }
  ```
- **`PqVouchParams`** gains/derives its `sep_vk` *from* the anchor: `verify` takes
  `&EpochIntroducerAnchor` (+ the claimed `epoch`) and rejects an anchor whose `epoch` ≠ the show's
  bound `epoch` (so a stale-epoch anchor can't be substituted). The internal show verify is byte-for-
  byte the existing path with `vk_pub = anchor.key`.
- **Retire the named-key live path.** `pq_vouch::verify(vk: &SepVerifyKey, …)` stays available **only
  under `#[cfg(test)]`** (or renamed `verify_under_named_key_TEST_ONLY`); the non-test/`vouch.rs`
  entry is `verify(anchor: &EpochIntroducerAnchor, …)`. This is the §1.6 "live path consumes ONLY the
  wrapped proof" requirement made mechanical.
- **No relation change, no new ZK, no new param.** `proof_show`/`pq_vouch`'s masked quadratic, the
  R1–R5 fold, the codec — all unchanged; only the *source* of `vk_pub` moves behind the anchor.

**Tests (rule 27).** Smoke: a `SharedKey` anchor round-trips a `[s|m]` vouch prove→verify. Integration:
two credentials issued under the *same* `B_epoch` by two distinct `R_epoch` holders both verify, and
their verify transcripts are **equal in distribution** (the anonymity assertion — same statistical-ZK
test harness the wiring uses); a credential under a *different* epoch key is rejected; an anchor whose
`epoch` ≠ the show's bound epoch is rejected.

---

## 5. The genuine sub-fork — sovereign establishment of `(B_epoch, R_epoch)` (§8 Q1)

The core (§4) needs a `B_epoch` and the issuers need `R_epoch`. *Producing* a shared lattice trapdoor
sovereignly (CLAUDE.md: no trusted third party) is the one real decision. The core is built against an
**injection point** — the runtime supplies `B_epoch` (public) and provisions `R_epoch` to authorised
issuers — so the build proceeds while this is chosen. Options, with the recommendation:

- **(a-i) Designated epoch key-generator, rotating role + published-verifiable `B_epoch` — RECOMMENDED.**
  One introducer (a per-epoch rotating role) runs the standard MP12 keygen, publishes `B_epoch`, and
  distributes `R_epoch` to the epoch's authorised introducers over their existing secure channels. Each
  recipient **verifies `A·R_epoch = B_epoch`** before use (so a faulty generator is detected, not
  trusted). Trust is *transient + verifiable + epoch-bounded*: the generator can only define *its* one
  epoch's key, the role rotates, and `B_epoch` is publicly checkable. No permanent third party.
  Buildable now (reuses `sep_trapdoor` keygen). **This is a threat-model choice → Josh (§8 Q1).**
- **(a-ii) Threshold / DKG trapdoor.** The epoch introducers jointly generate `(B_epoch, R_epoch)` so
  no single party ever holds `R_epoch` alone. Strongest (removes the transient-trust of a-i), but a
  lattice-trapdoor DKG is research-grade — documented as the future hardening of (a-i), not the first
  build.
- **(a-iii) Single long-lived shared key.** One global issuer keypair, no rotation. Simplest; coarsest
  anonymity (all introducers ever) + coarsest revocation (rotate the one key). Fallback only.

The establishment layer is a **runtime/ops contract**, tracked in `RUNTIME_REQUIREMENTS.md` (the
`B_epoch` publication + `R_epoch` provisioning + the `A·R_epoch = B_epoch` recipient check), not in
`vouch-crypto`. `vouch-crypto` ships the **verifier-side** check that `B_epoch` is a well-formed
`SepVerifyKey` and the anchor's `epoch` matches; it does not generate or distribute keys.

---

## 6. Build order (each chunk: tests + Codex gpt-5.5/high gate)

1. **`EpochIntroducerAnchor` type + `epoch` binding** — the enum (a-variant), `SepVerifyKey`
   well-formedness validation, the `epoch`-match guard. Unit tests: well-formed vs malformed key,
   epoch-mismatch reject.
2. **`pq_vouch::verify` takes the anchor** — thread `vk_pub` from the anchor; gate the named-key entry
   behind `#[cfg(test)]`/`_TEST_ONLY`. Integration: same-`B_epoch`/distinct-`R_epoch` both verify; the
   anonymity statistical-ZK transcript-equality test; wrong-epoch-key reject.
3. **`vouch.rs` live path consumes the anchor** (the §1.6 "live path = wrapped only" requirement) —
   the dual-hybrid `verify` AND-checks BBS + the anchor-verified lattice show. (This is also where
   HYP-343's trait reshape will sit; coordinate so HYP-343 wires `EpochIntroducerAnchor` through
   `VouchVerifier`.)
4. **`RUNTIME_REQUIREMENTS.md` contract** for §5 establishment (the chosen a-i/a-ii) + a
   `#[ignore = "blocked on epoch-key provisioning — RUNTIME_REQUIREMENTS"]` integration stub showing
   the shape of the end-to-end (provision `R_epoch` → issue → show → anchor-verify).
5. **Drop `experimental-unaudited` precondition note** — issuer-hiding is one of the three release
   gates (with HYP-330 params, HYP-343 wiring); update PQ_VOUCH_WIRING §8/§9 to mark HYP-324 mechanism
   landed (the *gate* still needs all three).

---

## 7. Candidate (b) — committed-key + accumulator membership (the documented upgrade, NOT built)

Each introducer keeps its own `(B_i, R_i)`. The epoch anchor is an **accumulator root** over the set
`{commit(B_i)}` of authorised introducers. The show gains a ZK **set-membership** proof: "the `B` I
verified under is committed in the epoch root" — without revealing which. Buys per-introducer
accountability + revocation (accumulator non-membership / updates). Cost: a new ZK accumulator
subsystem (Merkle-in-ZK or an RSA/lattice accumulator), quadratic terms folded into the show, research-
adjacent, a second construction to audit. The `EpochIntroducerAnchor` enum (§4) reserves the
`Committed { root }` variant so (b) is an additive change, not a rewrite. Revisit (b) only if
per-introducer revocation becomes a hard requirement.

---

## 8. Open questions (Codex DESIGN-review + Josh)

- **Q1 (Josh — threat-model): the §5 establishment model.** (a-i) rotating designated generator +
  published-verifiable `B_epoch` is the recommended default and what the build targets via the
  injection point. (a-ii) DKG is the future hardening; (a-iii) single global key is the fallback.
  *The core (§4) is built regardless; this picks how `B_epoch` is born.* Default-proceed = (a-i).
- **Q2 (DESIGN-review): epoch-anchor freshness vs the show's bound `epoch`.** Confirm the
  `epoch`-match guard (§4) + the per-show fresh `c_r_i` (P1c) together prevent an anchor-substitution
  or cross-epoch replay. Is binding `epoch` into the FS transcript of the show (already done for `N`)
  sufficient, or does the anchor need its own FS commitment?
- **Q3 (DESIGN-review): does sharing `R_epoch` interact with the OblSign `(upk, nonce)` deterministic
  preimage** (BLIND_ISSUANCE §2)? The preimage is `H(upk, nonce, c_u)` — issuer-key-independent — so
  two epoch introducers signing the same `(upk, nonce, c_u)` produce the *same* `v'`. Confirm this is
  benign (it is: same credential, one quota unit) and not a cross-introducer linkage.
- **Q4 (DESIGN-review): anonymity-set degeneracy.** A 1-introducer epoch hides nothing; should the
  protocol *refuse* to drop `experimental-unaudited` / mark a vouch "issuer-hidden" when
  |epoch introducers| < k_min? Propose a `k_min` floor as a runtime policy (not a crypto change).

---

## 9. DESIGN-review log

*(to be appended by the Codex gpt-5.5/high DESIGN-review before any code)*
