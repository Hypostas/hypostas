# RELAY_IDENTITY_PREMISE.md — the premise, under test

**Status:** PREMISE UNDER GATE. **Not canon. Not a design.** Nothing may be built against this
document until it survives a cross-vendor gate.
**Context:** `RELAY_LAYER.md` §15 — six confirmed P1s over two gate rounds resolved to one claim:
"there is no anonymous-but-accountable relay identity." This document asserts that claim is **false**
and states exactly why, as falsifiable propositions, so the gate can attack the *premise* rather than
a design built on top of it.

**Why this document exists.** All six P1s lived in premises, not in designs — "SPRING proves
uniqueness," "the nullifier stays spent," "vouching attracts adversaries." Each was a plausible
belief that no one attacked before a design was built on it. This is the mechanism from
`project_ntimes_spend_semantics`: **a design pass implementing an enforcement property must first
quote the code/spec line establishing that property.** Here the quotes come first and the design
comes later.

---

## §0 The premise in one line

> `vouch-crypto`'s `nullifier_lwr` is not (only) a nullifier. Its `epoch` parameter is an **opaque
> byte string**, making `N = round_Δ(H(scope, i) · w)` a **[DAA](https://eprint.iacr.org/2004/205.pdf)
> basename-scoped pseudonym** — deterministic in `(w, scope, i)`, unlinkable across scopes,
> identity-hiding against a quantum adversary. Keyed by `scope = "relay/slot-{i}"` with **no time
> component**, it is a stable relay identity, and the live directory (bounded by `MAX_RELAYS`) is its
> own dedup set — so no growing seen-set and therefore no `E_RETAIN` conflict.

**How to refute the whole document in one shot:** show that a single dyad can obtain two *distinct*
accepted relay pseudonyms for the same `scope`. That is PR-4/PR-5 below, and it is the Sybil bound
the entire design rests on.

---

## §1 Propositions (attack these)

Verification status is **mine, stated honestly** — `VERIFIED` means I read the code this session;
`ASSERTED` means I reasoned it and did not verify; `SUSPECT` means I actively doubt it.

### PR-1 — Scope opacity · **VERIFIED**
`epoch_base_indexed(epoch: &[u8], show_index: u32)` (`vouch-crypto/src/nullifier_lwr.rs:67`) hashes a
**length-prefixed opaque byte string** through an XOF with a fixed domain tag. It carries no time
semantics and no epoch validation. Its own doc: *"a v2 domain + a length-delimited `epoch` + a
fixed-width `i`, so no `(epoch, i)` byte-slot aliasing is possible even for a variable-length
`epoch`."*
⇒ `scope = b"relay/slot-3"` is a well-defined, non-aliasing input.
**Refute by:** finding any caller, verifier, or consensus rule that constrains this argument to a
real epoch, or any aliasing between a relay scope and an introduction epoch label.

### PR-2 — Determinism and stability · **VERIFIED**
`nullifier(a, w)` (`:99`) computes `n[i] = y / NULLIFIER_DELTA` coefficient-wise over
`prod = a.mul(w)`. No randomness, no state, no time. `Δ` is an exact divisor of `q̂`, so the rounding
is unique with no wrap (`:29-32`).
⇒ same `(w, scope, i)` ⇒ same tag, forever ⇒ reputation can accrue to it.
**Refute by:** any path where the same inputs yield different tags, or where uniqueness of rounding
fails at the parameter edges.

### PR-3 — Cross-scope unlinkability · **ASSERTED (module claim, argument not verified by me)**
The module states: *"`a_epoch` differs per epoch ⇒ the `N`s are unlinkable"*, resting on ring-LWR
search hardness.
⚠️ **My own concern, surfaced rather than hidden:** using scopes is the **multi-sample** LWR setting
— every additional scope publishes another sample under the *same secret* `w`. The module itself
prices this: *"each show adds `NHAT` more ring-LWR samples per introducer, so `N_MAX` is the
security-EXPENSIVE knob."*
**Refute by:** showing the sample count implied by (introduction shows + relay slots) exceeds what
`Δ`/HYP-330 supports; or that a *long-lived* published sample is weaker than a rotating one under the
relevant attack model (unbounded attacker time against a never-rotating tag).

### PR-4 — Uniqueness per scope · **SUSPECT — THE CRUX**
Claim: one credential cannot produce two distinct *accepted* tags for the same `(scope, i)`, because
`w` is uniquely determined by the credential and the R5 constraint
(`pq_vouch.rs:424 r5_nullifier_constraints`) binds the published `N` to the committed `w` in-circuit.
❗ **I have NOT verified that `w` is prover-*determined* rather than prover-*chosen*.** If a prover can
present a valid credential under two different `w` values, this document is dead — this is exactly
the shape of the SPRING failure (a proof of membership that failed to bind *which* member).
**Refute by:** exhibiting freedom in `w` at issuance or at show time.

### PR-5 — One credential per dyad · **SUSPECT**
Even granting PR-4, the Sybil bound is `slots = credentials × N_RELAY_MAX`. So it holds only if a dyad
cannot hold multiple credentials.
❗ **I believe this is UNENFORCED.** The n-times cap bounds *introductions per credential per epoch*
(THREAT_MODEL §5.7) — it does **not** obviously bound *credentials per dyad*. If a dyad can accumulate
credentials over time (one per introduction received, or by re-issuance), the relay bound scales with
credentials held and §14's "relay-Sybil cost = dyad-Sybil cost" is false again, for a new reason.
**Refute by:** naming the mechanism that bounds credentials per dyad — or confirming none exists.

### PR-6 — Bounded dedup · **ASSERTED**
Keying the directory at `relay/entry/{pseudonym}` makes the map its own dedup set: a duplicate
registration collides on an existing key. State is bounded by `MAX_RELAYS`, not by time, so
`x/nullifier`'s `E_RETAIN = 2` retention limit never applies.
**Refute by:** showing a registration path that must consult *history* rather than the live set — e.g.
if retired slots must stay unusable (see PR-7).

### PR-7 — Revocation by slot burn · **ASSERTED**
The pseudonym is the handle: evict `relay/entry/{pseudonym}` without ever learning the dyad. To stop
re-registration of a revoked slot, a burned-slot set is needed; it is bounded by
`|dyads| × N_RELAY_MAX` — a **population** bound, not a time bound, unlike a nullifier seen-set.
**Refute by:** showing the burned set grows with *events* rather than population (credential rotation
would do this — see PR-9), which would reintroduce the unbounded-state problem PR-6 claims to solve.

### PR-8 — Capability as a runtime signal · **ASSERTED**
Capability gates (uptime, always-on, reachability) cannot be checked at registration against an
anonymous registrant, but *can* accrue to a stable pseudonym as observations. So they move from
precondition to reputation input.
⚠️ This leans on observations alone establishing standing — and `reputation/mod.rs:266-274` documents
the opposite as load-bearing: *"observations only REFINE a trusted relay's score — they cannot
manufacture reputation for an untrusted/disconnected node (else a Sybil could fake delivery/uptime
to earn up to `REP_W_DELIVERY + REP_W_UPTIME` with no trust path, breaking §20.4)."*
**Refute by:** showing that with PR-4/PR-5 holding, the bounded-slot property does *not* substitute
for the trust-path requirement that comment protects.

### PR-9 — Credential lifetime · **SUSPECT, and possibly fatal**
Every property above is keyed on `w`. If credentials rotate or are re-issued, `w` changes, so **all**
relay pseudonyms change: reputation resets to zero *and* the slot bound resets (the dyad may register
a fresh full set). A relay identity must outlive credential rotation, or PR-2 and PR-4 are both void
in practice.
**Refute by:** establishing that the C3 vouch credential does rotate — or that it does not, and saying
what happens on re-issuance after key compromise.

### PR-10 — Affordability · **ASSERTED, uncalibrated**
`N_MAX_SHOWS_PER_EPOCH = 8` (`:52`) bounds the accepted index range and is documented as the
security-expensive knob, with HYP-330 recalibration required to cover `N_MAX × NHAT` samples. The
documented cheap alternative — *"get more total introductions by rotating epochs more often"* — is
**unavailable here**, because rotation is precisely what a stable relay identity forbids.
**Refute by:** showing `N_RELAY_MAX` slots at usable relay counts is not affordable at the λ target.

---

## §2 What is NOT claimed

To keep the gate on the premise and off strawmen:

1. **Not claimed:** that the relay directory design is correct. `RELAY_LAYER.md` §10–§12 stay
   REFUTED. This document only claims the *primitive* exists.
2. **Not claimed:** that this closes the directory-size problem. That needs
   [Walking Onions](https://spec.torproject.org/proposals/300-walking-onions.html) (SNIP + ENDIVE)
   and remains genuinely unbuilt research, with Tor's own open problems (family enforcement — our
   diversity constraint — and exit policies) still open.
3. **Not claimed:** that `Δ` is calibrated. It is PROVISIONAL and the module is behind
   `experimental-unaudited`.
4. **Not claimed:** unconditional unlinkability. The module is explicit that PQ-*computational*
   hiding is the ceiling: *"a deterministic `w`-keyed value can never be unconditionally unlinkable
   (brute force over a finite-entropy `w`)."*

## §3 Verdict conditions

- **PR-4 or PR-5 broken** ⇒ the premise is dead; the primitive does not bound Sybils and
  `RELAY_LAYER.md` §15 stands as written.
- **PR-9 broken** ⇒ the premise survives cryptographically but is useless operationally (identity
  cannot outlive its credential).
- **PR-3 or PR-10 broken** ⇒ the premise holds but is unaffordable; the slot count must shrink,
  possibly below usefulness.
- **PR-6/PR-7/PR-8 broken** ⇒ repairable; these are consequences, not foundations.
- **All hold** ⇒ the design pass may begin, scoped to re-keying the existing primitive rather than
  inventing one.
