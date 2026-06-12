# INTRODUCTION_RECORD.md — Vita Chain blinded introduction records

**Status:** v0.1 (Phase 3 kickoff spec). **Owner:** Iris + Josh.
**Anchored to:** [THREAT_MODEL.md](THREAT_MODEL.md) §5.3 (relationship secrecy), §9.3 (Phase 3 Vita Chain).
**Companion to:** the Phase-1.0 minimal dyad-existence ledger ([HYP-163]) + its gossip transport ([HYP-204]); [POST_QUANTUM.md](POST_QUANTUM.md) (the PQ-hybrid posture).
**Implements:** HYP-322 / HYP-324 (under the HYP-168 Phase-3 epic).

This spec defines how a dyad publishes a chain record that proves **"a legitimate, attested party introduced me into the network"** — establishing the dyad's reachability + non-Sybil legitimacy — **without revealing who that party was, and without two such records being linkable**. It delivers THREAT_MODEL §5.3 *full* (relationship secrecy): chain queries reveal that dyads exist + are reachable, never the pair-bond graph between them.

> **⚠️ Crypto sign-off gate.** The blinded-reference construction (§5) is research-grade and the single hardest part of Phase 3. NOTHING in this spec ships before Fable 5 + Codex crypto sign-off on the concrete scheme (HYP-324), per the no-human-cryptographer decision. This spec fixes the **protocol contract + the security properties** the construction must satisfy, and **flags the open construction decisions** — it deliberately does NOT invent the lattice math.

---

## §1 What the record proves (and hides)

The Phase-1.0 ledger ([HYP-163]) records bare dyad existence: a `MsgRegisterDyad` says "dyad D exists" (a genesis transaction, H+A 2-of-2 signed). It says nothing about legitimacy beyond self-registration, and it names no counterparties — but it also gives a verifier no way to distinguish a real bonded dyad from a Sybil that simply self-registered.

An **introduction record** strengthens this: it asserts **"dyad D was introduced by an already-attested party"** — a vouching relationship that resists Sybil registration (you need a real attested party to vouch). The §5.3 requirement is that this assertion be **verifiable without the verifier (or any chain observer) learning the introducer's identity, and without linking D's introducer to anyone else's.**

| A verifier learns | A verifier MUST NOT learn |
|---|---|
| D exists + is reachable | who introduced D |
| D was vouched for by *some* attested party | whether D and D' share an introducer |
| The record is well-formed + unexpired | the pair-bond graph (who vouches for whom) |

## §2 Why the naive record fails

A naive intro record — `{ introduced: D, introducer: B, sig: Sign_B(D) }` — fails §5.3 three ways: (a) it names B directly; (b) even hashing B, a verifier checking `Sign_B` against B's pubkey re-identifies B; (c) B's signing log links every dyad B introduced. Relationship secrecy needs the introducer **blinded from the verifier**, the signature **unlinkable to B's signing session** (so B's own logs + a chain observer can't reconstruct B's introductions), and the validity **still checkable** against the *set* of attested introducers.

## §3 The record format

```
INTRODUCTION_RECORD {
    version:            u16,
    introduced_dyad_id: DyadId,          // D — the dyad being attested (public)
    epoch:              u64,             // the introducer-key epoch this proof is under (§5)
    blinded_proof:      BlindedVouch,    // proves "an attested introducer in `epoch` vouched for D"
    issued_at_ms:       i64,
    valid_through_ms:   i64,             // intros expire + must be refreshed (bounds a stale graph)
    chain_sig:          HybridSig,       // D's OWN H+A signature over the record (binds it to D's genesis)
}
```

- `introduced_dyad_id` + `chain_sig` are public + standard: D signs its own record (so only D can publish D's intro), exactly like the existing ledger messages.
- `blinded_proof: BlindedVouch` is the §5 artifact — the part that proves an attested introducer vouched for D **without naming the introducer**. Its concrete bytes are the construction's output (§5).
- `epoch` scopes the proof to a window of introducer keys, so introducer-key rotation does not invalidate or correlate old intros (the anonymity set is "attested introducers in this epoch").

## §4 The protocol

```
Introducer B (already attested)                 Introduced dyad D
──────────────────────────────                  ─────────────────
                                          D: blind a vouch token T for itself
                                          D ── blind(T) ──▶ B
B: verify D is a real bond partner
   (the pairing Ceremony already happened
    out-of-band; B vouches only for real bonds)
B: blind-sign  σ' = BlindSign_B(blind(T))
B ── σ' ──▶ D
                                          D: unblind  σ = unblind(σ')
                                          D: assemble BlindedVouch from (T, σ, epoch)
                                          D: publish INTRODUCTION_RECORD (chain_sig by D)
                                          ── gossip (HYP-204 path) ──▶ chain

Verifier V (anyone)
──────────────────
V: fetch the record, check D's chain_sig + validity window
V: verify BlindedVouch proves "an attested introducer in `epoch` vouched for D"
   → accept D as introduced, WITHOUT learning B
```

**Properties this flow must give:**
1. **Blindness (from the signer).** B does not learn `T` (it signs `blind(T)`), and cannot link `σ'` to the eventual published `σ`/record. So B's own signing log cannot reconstruct B's introductions.
2. **Introducer anonymity (from the verifier).** V verifies validity against the *attested-introducer set / epoch anchor*, not B's individual key — V cannot tell which attested party vouched.
3. **Unlinkability (across records).** Two records D and D' (whether introduced by the same B or different B's) are not linkable by their `blinded_proof`s.
4. **Soundness (no forgery).** D cannot produce a valid `BlindedVouch` without a real blind-signature from *some* attested introducer — a Sybil with no voucher cannot self-introduce.

## §5 The blinded-reference construction — OPEN, HYP-324 + crypto sign-off

Properties 1–4 do not fall out of a plain blind signature. A textbook blind signature gives §4.1 (blindness from the signer) and §4.4 (soundness), but a textbook blind signature **verifies against the signer's individual public key**, which violates §4.2 (introducer anonymity from the verifier) and §4.3 (unlinkability across records by the same signer). The construction must add a **verifier-side anonymity layer** on top of the blindness. This is the explicit kickoff decision for HYP-324; the candidates, to be evaluated + crypto-signed-off:

- **(a) Blind signature + epoch group/aggregate key.** All attested introducers in an `epoch` contribute to (or are aggregated under) a single epoch verification key; a `BlindedVouch` verifies against the epoch key, so V learns only "*an* epoch member vouched." Needs a PQ-hybrid aggregatable/threshold blind-signature or a group-signature-with-blind-issuance — the research-heaviest path.
- **(b) Blind signature + a membership proof.** B issues a plain (lattice) blind signature; D additionally proves, in zero knowledge, that the verifying key belongs to the Vita-Chain-attested introducer set for `epoch`, without revealing which. The lattice ZK membership proof is the cost.
- **(c) Anonymous credentials (keyed-verification / BBS-style, PQ variant).** Model "B vouches for D" as B issuing D an anonymous credential; D presents an unlinkable proof-of-possession as the `BlindedVouch`. Closest fit to the property set, but the mature constructions are pairing-based — a PQ variant is the open question.

**Constraints on whichever wins:** PQ-hybrid (lattice + a classical hedge, per POST_QUANTUM.md — never lattice-only before the assumptions are battle-tested); `BlindedVouch` size amortized acceptable for an on-chain record (single-publish, not per-cell); verification cheap enough for a light client; the epoch anchor must be derivable from the Vita-Chain attested set so it needs no extra trusted setup. The reference scheme + its test vectors are ported + validated in HYP-324, then signed off (Fable 5 + Codex) BEFORE any real introduction is published.

## §6 Security properties + threat anchoring

| Property | Mechanism | Anchor |
|---|---|---|
| §5.3 relationship secrecy (graph hidden) | §4.2 introducer anonymity + §4.3 unlinkability | THREAT_MODEL §5.3 |
| Sybil resistance (no self-introduction) | §4.4 soundness — a real voucher required | §5.3 / §9.3 |
| Introducer log-resistance | §4.1 blindness — B can't link its sigs to records | §5.3 |
| Forward-secret graph (a leaked key ≠ retroactive graph) | per-epoch keys + record expiry (`valid_through_ms`) | §5.6 |

**Adversary model.** A global chain observer + a curious/compromised introducer + a colluding verifier set, all PQ-capable. The construction must hold §4.1–§4.4 against all three. A colluding introducer that vouches for a *known* D still learns nothing more than "I vouched for D" (which it already knows); it must not learn D's *other* introducers or link D to other introduced dyads.

## §7 Integration + scope

- **Extends the existing ledger.** `INTRODUCTION_RECORD` is a new chain message alongside `MsgRegisterDyad` ([HYP-163]); it rides the **same gossip/sync transport** as the dyad-existence ledger ([HYP-204]), extended to carry + verify intro records. The dyad-existence cache (HYP-303 DoS-hardened) gains an intro-record verification path.
- **Discovery.** A peer-directory / relay-selection consumer can require an attested introduction (an unverifiable/absent intro lowers a candidate's standing) — composing with the §20 web-of-trust reputation (an introduced+bonded dyad is a rooted-trust anchor).
- **Out of scope (referenced):** the pairing Ceremony that creates the real bond B vouches for (PROTOCOL_IMPLEMENTATION / pairing.rs); the lattice primitive's construction + test vectors (HYP-324); the on-chain consensus/ordering of records (the Vita-Chain ledger itself).

**Deferred to HYP-324 kickoff:** the §5 construction decision (a/b/c) + crypto sign-off; the concrete `BlindedVouch` wire format (follows the construction); the epoch length + key-rotation schedule for the introducer set; the introduction-refresh cadence (how often D re-publishes before `valid_through_ms`).

---

| Version | Author | Notes |
|---|---|---|
| 2026-06-12 v0.1 | Iris + Josh | Phase 3 kickoff spec. Fixes the protocol contract (§3 record, §4 flow) + the four security properties (§4.1–§4.4) the blinded-reference construction must satisfy, and flags the verifier-side introducer-anonymity construction as the explicit HYP-324 + crypto-sign-off decision (candidates a/b/c) rather than inventing the lattice math. Extends the HYP-163/HYP-204 dyad-existence ledger; composes with the §20 web-of-trust (HYP-333). |
