# ISSUER_HIDING_DESIGN.md — HYP-324 issuer-hiding for the C3 dual-hybrid vouch

**Status:** v0.1 — written 2026-08-02 to close a dangling citation (HYP-488). `issuer_hiding.rs` has
cited this document 5× since 2026-06-28; it was **never committed anywhere**, so the intent layer for
this mechanism has been missing while the code shipped.
**Owner:** Iris + Josh · **Linear:** HYP-324 (mechanism), HYP-488 (why this doc exists)
**Implements:** `vouch-crypto/src/issuer_hiding.rs`, `pq_vouch::verify_issuer_hidden`
**Companion:** `INTRODUCTION_RECORD_CRYPTO_DESIGN.md` (the C3 construction), `THREAT_MODEL.md` §5.3
(relationship secrecy), `RUNTIME_REQUIREMENTS.md` (establishment contract)

> ⚠️ **This document is written after the code, not before it.** It records intent as reconstructed
> from the implementation plus the decisions in HYP-324, and it marks every place where the code and
> the intended design **currently diverge** (§6, §9). Those divergences are work items, not
> descriptions. Where doc and code disagree, **code is truth** — but a divergence recorded here is a
> defect to close, not a licence to leave it.

---

## §1 The property, and the release gate

Without issuer-hiding, a C3 vouch verifies against a **named** introducer key, so the verify
transcript leaks *which* introducer signed. That is a relationship-secrecy leak
(THREAT_MODEL §5.3): a verifier learns an edge of the introduction graph it has no need to know.

**The property:** a verifier learns only *"this vouch was signed by **an** introducer authorised for
epoch E"* — never which one.

This is the release gate that flips the C3 lattice show from **TEST-ONLY** (named key) to **live**
(shared per-epoch anchor). `verify` is the internal/test entry; **`verify_issuer_hidden` is the entry
the live path MUST use.**

## §2 The anonymity set

The anonymity set is exactly **the epoch's authorised introducer-set**.

Two consequences, both intended:

1. **A single-introducer epoch hides nothing** — correctly, because there is only one possible signer.
   Issuer-hiding is meaningful only for `|introducers(E)| > 1`.
2. **The set is a security parameter.** A deployment that authorises two introducers per epoch has a
   2-anonymity set. This is the same class of quantity as a mixnet's relay count, and it should be
   monitored, not assumed. See §8 Q4.

## §3 Construction — candidate (a), shared epoch key

Every introducer authorised for epoch `E` signs credentials that verify under **one shared key
`B_epoch`**. Each holds a trapdoor `R_epoch` with `A · R_epoch = B_epoch` (`A` is the public `pp`
matrix, shared across epochs).

**The §1 show relation is unchanged.** `B_epoch` is a `SepVerifyKey` like any other; only the
*provenance* of `B`'s value changes — shared rather than personal. No proof-system change was
required, which is why this shipped as a small module rather than a redesign.

### §3.1 Both halves must be anchored — the dual-hybrid requirement

The C3 vouch AND-verifies a **SEP (lattice)** half and a **BBS** half. Anchoring only the SEP key
would still leak the introducer through a **named BBS issuer key**.

> Caught as a **Codex gate P1, 2026-06-28.** Recorded here because it is the single most
> load-bearing constraint in this design and the one most likely to be reintroduced by a future
> refactor that "simplifies" the anchor.

So `EpochIntroducerAnchor::SharedKey` carries **both** `sep_key` (`B_epoch`) and `bbs_pk`
(`bbs_pk_epoch`), and `verify_issuer_hidden` takes **no caller-supplied issuer key** for either half.

## §4 What the verifier enforces

`verify_issuer_hidden` (`pq_vouch.rs:978`) enforces three bindings. All three are required; dropping
any one silently restores the leak:

| Binding | Mechanism | What it stops |
|---|---|---|
| **BBS half anchored** | issuer key is `anchor.bbs_pk()`, never a caller argument | §3.1 leak via a named BBS key |
| **Epoch single-sourced** | `anchor.epoch_bytes()` drives *both* the nullifier base and the show's epoch scope; no separate `epoch` argument exists on this path | a verifier steered to check a vouch under a different epoch than the anchor names |
| **Params↔anchor consistency** | re-checks `params.sep_vk == *anchor.verify_key()`, **fail-closed** | a caller mixing a named introducer key into the hidden path, which would verify under the wrong provenance |

**Normative:** any new verify entry point MUST enforce all three, or MUST be marked
`#[doc(hidden)]`/test-only and never reachable from the live path.

## §5 Epoch-key establishment — the contract this crate does NOT satisfy

`issuer_hiding.rs` ships only the **verifier handle**. Establishing and distributing
`(B_epoch, R_epoch)` and the shared BBS keypair is a runtime/ops concern, deferred here and to
`RUNTIME_REQUIREMENTS.md`. This section defines what that contract must provide.

### §5.1 The decision — (a-ii) threshold/DKG

Two ways to give every epoch introducer signing power under one `B_epoch`:

- **(a-i) Dealer.** One party generates `(B_epoch, R_epoch)` and distributes `R_epoch` to each
  authorised introducer. Simple, and **rejected**: the dealer is a single point of total compromise,
  and every introducer holds a full trapdoor — so any one of them can sign for the whole epoch, and a
  single leaked `R_epoch` forges arbitrarily.
- **(a-ii) Threshold / DKG.** No single party ever holds a full `R_epoch`; signing is a threshold
  protocol among authorised introducers. **This is the decision of record (Josh, HYP-324).**

⚠️ **Provenance note:** that decision was taken in session and this document is its first written
record — precisely the gap HYP-488 describes. It should be confirmed against HYP-324 before being
treated as settled.

### §5.2 The cost, stated plainly

**Threshold lattice trapdoor generation and Gaussian sampling are not off-the-shelf.** MP12-style
trapdoors require preimage sampling under a discrete Gaussian; doing that in a threshold setting
without leaking the shared trapdoor is an active research area, not an engineering task. A design
pass that assumes (a-ii) is a library call will fail.

This is the honest reason the establishment contract is still open (HYP-324 ch4, tracked). It is
**not** a detail deferred for convenience.

### §5.3 What the contract must specify

1. **Who is authorised** for epoch `E`, and where that set is published such that a verifier can
   check it. ⚠️ **Currently nowhere** — see §6.3.
2. **How `(B_epoch, R_epoch)` is generated** under (a-ii), and the threshold `t`-of-`n`.
3. **Distribution + rotation cadence**, including what happens to in-flight credentials at an epoch
   boundary.
4. **Compromise response**: what a leaked share permits, and how an epoch is retired early.
5. **The BBS half**: the same questions for `bbs_pk_epoch`, which has the same sharing requirement
   and is easier (pairing-based threshold signing is well-studied) but is not automatically solved.

## §6 Rotation — intent vs. what the code actually does

**Intent:** `B_epoch` is per-epoch. A new epoch means a new shared key, which is what makes the
epoch a meaningful privacy boundary — it gives forward secrecy for the introduction graph (a leaked
epoch key must not retroactively deanonymise earlier epochs).

### §6.1 ⛔ The code does not rotate. Confirmed 2026-08-02.

`EpochIntroducerAnchor::shared_key(epoch, sep_key, bbs_pk)` is a **pure struct constructor**
(`issuer_hiding.rs:67-73`) — `epoch` is a caller-supplied **tag** on a caller-supplied key. Nothing
derives the key from the epoch, and **every `SepSigKey::keygen` call site in the workspace is
`#[cfg(test)]`.** There is no production epoch-key generation at all.

**Consequences, all confirmed by cross-vendor gate:**

- `B_epoch` never rotates ⇒ the epoch is a **label, not a boundary**, and the forward-secrecy property
  §6 claims is not delivered.
- `D_s` lives inside `SepVerifyKey`, so `upk = D_s · s` is a **permanent** pseudonym, not an
  epoch-scoped one. An issuer's `upk` view therefore links a dyad's issuance sessions **across all
  time**.
- A design pass (HYP-486 CP-2) concluded "upk is epoch-scoped" from `ds_matrix` being a *field of*
  the epoch key and was refuted. **A type carrying an `epoch` field is evidence `epoch` was passed
  in — never that the key is derived from it.**

### §6.2 ⛔ Over-issuance is unattributable

Under candidate (a), every authorised introducer signs under one `B_epoch` and each holds its **own,
process-local** `UpkLedger`. So a member enrolling with introducers A and B gets two quotas, and —
because the verifier cannot tell which introducer signed — the over-issuance **cannot be attributed**.
That is issuer-hiding working as designed, and it is precisely why the issuance cap cannot be
per-introducer. THREAT_MODEL §5.7 names the same hole on the show side.

**This is the structural tension at the heart of the mechanism:** hiding the issuer is what makes a
per-issuer cap unenforceable. Any credential-cap design must assume it.

### §6.3 ⛔ The authorised-introducer set is not on-chain

`vita-chain/src/modules/nullifier.rs:24-29`: *"The chain does NOT verify that `anchor_bytes` is
correctly derived from the attested-introducer set for the epoch (that set is not on-chain yet)."*
So the chain cannot distinguish an authorised introducer from any registered dyad — §5.3(1) is
unsatisfied, and any on-chain enforcement keyed on "is this an introducer" is currently impossible.

## §7 Candidate (b) — committed key + accumulator membership (not built)

The documented upgrade, reserved as `EpochIntroducerAnchor::Committed { epoch, root }`.

Instead of one shared key, each introducer keeps its **own** key, and the anchor commits to an
**accumulator root** over the authorised set. A vouch carries a ZK proof of membership in that
accumulator. The verifier learns "signed by a member of the committed set" without learning which.

**Why it is the upgrade path:**

- **Per-introducer revocation** — remove one introducer from the accumulator without re-keying every
  other introducer, which candidate (a) cannot do (a compromised `R_epoch` invalidates the epoch).
- **No shared trapdoor** — dissolves the §5.2 threshold-sampling problem entirely; each introducer
  signs with its own key.
- **Attributable over-issuance becomes possible in principle**, since per-introducer identity exists
  under the proof even though it is hidden from the verifier.

**Why it is not built:** it costs a membership proof per vouch. Our SIS-Merkle accumulator +
one-of-many machinery exists (SPRING, HYP-317), so this is a composition rather than new
cryptography — but the composition is unproven and would need its own premise gate.

The enum variant is reserved so adopting (b) is **additive**, not a rewrite.

## §8 Open questions

1. **Q1 — the establishment contract.** §5.3, blocked on §5.2's research cost. HYP-324 ch4.
2. **Q2 — publish the authorised-introducer set.** §6.3. Without it, (a) has no verifiable membership
   and (b) has nothing to accumulate over. **This blocks both candidates** and should be sequenced
   first.
3. **Q3 — make rotation real.** §6.1. Until `B_epoch` is actually regenerated per epoch, the epoch
   boundary delivers no privacy property, and `upk` permanence silently undermines any design that
   assumes epoch-scoped handles.
4. **Q4 — minimum anonymity set.** §2. What is the smallest `|introducers(E)|` we will ship? A
   2-introducer epoch is a 2-anonymity set. Needs a floor, and a monitored alarm when a live epoch
   falls below it. Product decision.
5. **Q5 — epoch length.** Referenced across the crypto specs as *"a sign-off parameter"* and defined
   nowhere. It sets the rotation cadence (§6), the nullifier retention window, and the granularity of
   every epoch-scoped rate limit.

## §9 Implementation status

| Piece | Status |
|---|---|
| `EpochIntroducerAnchor::SharedKey` + codec (`ANCHOR_CODEC_VERSION = 1`) | ✅ built |
| `verify_issuer_hidden` three-binding enforcement (§4) | ✅ built, fail-closed |
| Dual-half anchoring (§3.1) | ✅ built |
| Epoch-key **establishment** (§5) | ❌ not built — no production `keygen` call site exists |
| Epoch-key **rotation** (§6) | ❌ not built — `shared_key` is a pure constructor |
| Authorised-introducer set on-chain (§6.3) | ❌ not built |
| Candidate (b) accumulator variant (§7) | ❌ not built — enum room reserved |

**Read that table as the gap between this document and the code.** The verifier side is real and
sound; everything that would make the *epoch* mean something is absent. Any design that relies on
epoch-scoped issuer keys must treat §6.1 as the current state, not §6's intent.
