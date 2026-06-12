# SESAME_SESSION_DESIGN.md — HYP-159b multi-device session orchestration

**Status:** DESIGN (rule #9 contract — write before code). Pending a Codex DESIGN-review before chunk 1.
**Scope:** the `SesameSession` orchestration that ties HYP-159a's per-device primitives into live dyad↔dyad
multi-device messaging — resolving DOUBLE_RATCHET.md **§16.1** ("concrete protocol detailing" of the
Sesame × CIRCUIT_LIFECYCLE interaction), which was explicitly deferred until the circuit layer existed.
**Unblock:** §16.1 deferred because "the N×M ratchet-handshake rides the circuit layer, which is HYP-160 (not
yet built)." HYP-160 + the full circuit/Outfox/deep-EXTEND stack are **now built + merged** (2026-06-12) — so
§16.1 is resolvable.
**Spec:** DOUBLE_RATCHET.md §11 (§11.3 sub-chains, §11.5 concurrent-send, §11.6 sync). **Companion:** the
circuit layer (`vita-carriers::circuit_manager` / `CircuitTransport`), `protocol-core::sesame` (159a).

---

## 1. What 159a already owns (the FS-critical primitives — DONE)

- **§11.2 device identity:** `DeviceClass` / `DeviceInfo` / `DyadDeviceBundle` (register, max 8, offboard).
- **§11.4 sender-key distribution:** `SenderKeyState` (advancing KDF chain → per-message FS within an epoch),
  `SenderKeyReceiveState` (bounded out-of-order window + replay/rollback rejection), `SenderKeyDistribution`
  (hybrid-signed, rotated 100 msgs / 24h).
- **offboarding:** revocation via `pairing::RevokeDeviceRecord` (forward-only membership gate; historical sigs
  still verify).

HYP-159b builds the SESSION that USES these — it adds no new FS primitive, only orchestration.

## 2. The §16.1 crux — how multi-device messages ride the circuit layer (THE design question)

A circuit/private-channel is **dyad↔dyad** (`A_dyad → B_dyad`), authenticated by the dyad's identity. But a
dyad is a FLEET of device-nodes (each a separate `dyados-runtime` with its own keys). The unresolved question:
**when A1 sends to dyad B {B1,B2,B3}, how does the message reach all of B's devices over a dyad↔dyad circuit?**

This must be answered against the REAL device×circuit model before chunk 1. The candidate resolutions to put
to the Codex DESIGN-review (read `dyados-runtime`'s device handling + `circuit_manager`'s identity model first):

- **(R-a) One circuit per dyad-pair + intra-dyad fan-out via §11.6 sync.** The circuit terminates at ONE B
  device (whichever holds the live channel); that device fans the decrypted message to B2/B3 over the §11.6
  local sync (Continuity/BT/mDNS). Simplest wire model (1 circuit, 1× message for Option B), but couples
  delivery to §11.6 (which is platform-env-blocked) and to one device being online.
- **(R-b) One circuit per device-pair (the literal N×M).** A1↔B1, A1↔B2, A1↔B3 are separate circuits; the
  message is delivered per-device. Matches "N×M sub-circuits" literally; no §11.6 dependency for delivery; but
  N× circuits + the cover-traffic/budget implications, and the per-device-pair ratchet IS the circuit.
- **(R-c) Hybrid: sender-key distribution per-device (N×M, at first-use/rotation) over the device-pair
  circuits, the actual message 1× over the dyad circuit.** Option B's amortization: the N×M cost is only the
  sender-key DISTRIBUTION (rare); steady-state messages are 1×. The per-device-pair ratchet is the channel for
  the SenderKeyDistribution only.

**Leaning (R-c) for Option B (chat) + per-device delivery for Option A (Critical)** — it matches §11.3's
"sender_key distributed via per-device-pair channels at first-use, then reused" exactly. But the device↔circuit
binding (does a device-pair have its own circuit identity, or is the circuit dyad-level with a device selector
in the inner payload?) is the precise sub-question for the review. **Do NOT start chunk 1 until this is pinned.**

> **[RESOLVED 2026-06-12 — see §7.](#7-codex-design-review-outcome-2026-06-12--the-2-crux-resolved)** Verdict:
> **NOT R-b** (circuits are dyad-level — no device-pair circuit identity exists). **R-c confirmed**, with one
> load-bearing correction: R-c's "1× over the dyad circuit reaches all B devices" is **WRONG** — a dyad circuit
> reaches ONE endpoint; multi-device *delivery* is a separate, currently-unsolved transport concern. **Sesame is
> protocol-core orchestration that produces device-addressed ciphertexts; it does NOT own delivery.**

## 3. Orchestration the design CAN fix now (independent of the §2 crux)

- **Send-path tier split (§11.3):** `SesameSession::seal(plaintext, trust_tier, peer_bundle)` → **Option B**
  (sender-key, 1× ciphertext) for chat-class; **Option A** (per-device `double_ratchet` encrypt, N× ciphertext)
  for Critical-tier (Bond/dissolution). The tier comes from the existing `PacketIntent`/trust mapping.
- **Sender-key lifecycle:** first send to a (dyad, peer-dyad) with no live sender-key → generate (159a) +
  distribute a `SenderKeyDistribution` to each peer device → encrypt once. Subsequent sends reuse until the
  159a rotation (100/24h) fires.
- **Receive demux (§11.5):** inbound is keyed by `(sender_device_id, sender_key_id)` (Option B) or the
  per-device-pair ratchet (Option A); concurrent A1/A2 sends disambiguate on `device_id + n_send` — independent
  receive chains, no central ordering. The 159a `SenderKeyReceiveState` bounded window + replay rejection apply.
- **Carrier choice (§16.1 item 2 — RESOLVED):** SenderKeyDistribution + messages ride the SAME live private
  channel / circuit (no separate carrier). Resolved by the circuit layer existing.
- **Partial-device-loss (§16.1 item 3 — RESOLVED):** a lost/offboarded peer device → A rotates the sender-key
  + redistributes to the REMAINING devices (159a rotation + the offboard membership gate); a transient miss is
  absorbed by the bounded out-of-order window. No new mechanism — composition of 159a primitives.

## 4. Invariants (Codex-verify each)

- **FS preserved:** the session adds no key-lifetime change — per-message FS is the 159a chain; the per-
  device-pair ratchets are standard `double_ratchet` sessions.
- **Trust-tier gate is real:** Critical-tier MUST use Option A (per-device encrypt) — a chat-class fast-path
  must never carry a Bond/dissolution payload. Test the tier→option mapping at the boundary.
- **Max devices:** `SESAME_MAX_DEVICES_PER_DYAD = 8` enforced at registration (159a) AND at send fan-out.
- **Revoked device excluded:** a revoked device receives no sender-key + can't originate a valid message
  (159a offboarding); the session must consult the live membership set on every distribution.
- **No N×M blow-up in steady state:** Option B sends 1× after distribution; only distribution is N×M, only at
  first-use/rotation.

## 5. Chunk decomposition (each its own PR + Codex gate + rule-#27 test)

- **Chunk 0 — resolve §2 (the device×circuit binding) + Codex DESIGN-review.** No code; pin R-a/R-b/R-c against
  the real `dyados-runtime` device model + `circuit_manager` identity model. This doc + the review ARE chunk 0.
- **Chunk 1 — `SesameSession` skeleton + the per-device-pair ratchet map** (`HashMap<(DeviceId,DeviceId),
  RatchetSession>`), independent of delivery. Unit: per-device sub-chain independence (§11.5).
- **Chunk 2 — Option B send/receive** (sender-key generate→distribute→encrypt-once; receive demux by
  `(sender_device_id, sender_key_id)`). Integration: 2 dyads × 2 devices, the 4-device-pair message matrix all
  decrypt; a device added mid-conversation receives sender-keys.
- **Chunk 3 — Option A (Critical-tier) per-device encrypt** + the tier→option gate. Adversarial: a revoked
  device can't generate a valid message; replay of a sender-key message rejected.
- **Chunk 4 — concurrent-send resolution (§11.5)** end-to-end: concurrent A1/A2 → 3 receiver devices decrypt
  with correct ordering.
- **§11.6 local cross-device sync (Continuity/BT/mDNS)** → platform-env-blocked, like the iOS work (HYP-296):
  the Rust seam + an `#[ignore]` contract test; the native shim is the signed-app's job. Tracked separately.

## 6. Open question for the Codex DESIGN-review (before chunk 1) — ✅ ANSWERED (§7)

Pin §2: is the per-device-pair ratchet bound to its OWN circuit identity (R-b, literal N×M circuits), or is the
circuit dyad-level with a device selector in the inner payload + sender-key fan-out (R-c)? This determines the
chunk-1 data model. Read the `dyados-runtime` device/identity model + `circuit_manager`'s `LocalIdentity` /
`PeerDirectory` before answering — the answer must match how a dyad's devices actually hold circuit identity
today, not an idealized model.

**Answered by §7:** dyad-level circuit (R-c), device identity in the inner payload. Delivery to every device is a
separate seam (§7.2). Chunk 1 is cleared to start on the reframed basis.

---

## 7. Codex DESIGN-review outcome (2026-06-12) — the §2 crux RESOLVED

Reviewer: Codex `gpt-5.5` / reasoning=high, standalone (run `bz09ewwwn`), reading the REAL device×circuit model
(`circuit_manager/mod.rs`, `circuit_transport.rs`, `circuit_identity_store.rs`, `dyad_ledger/key_bundle.rs`,
`ratchet_manager.rs`, `sesame/`, `server.rs`, `private_channel_inbound.rs`, `pairing.rs`). Verdict: **NOT R-b.
R-c — with a delivery correction that reshapes the chunk plan.** This section is authoritative where it diverges
from §2–§5 (rule "specs are intent, code is truth"); the earlier sections are preserved as the audit trail of
how the crux was framed before it was pinned to code.

### 7.1 Crux verdict — circuits are dyad-level, not device-level

The per-device-pair ratchet is **NOT** bound to its own circuit identity. Circuits are dyad↔dyad, full stop.
Code-anchored evidence:

- `CircuitPeer { dyad_id, x25519_pk, ml_kem_ek }` — no device selector (`circuit_manager/mod.rs:614`).
- Sender circuits keyed by terminal DyadId: `circuits: HashMap<DyadId, CircuitState>` (`mod.rs:810`).
- Handshake identity is `initiator_dyad_id`; responder legs attribute DATA to the dyad, not a device
  (`mod.rs:373`, `mod.rs:624`).
- `PeerDirectory::lookup(&DyadId)`; `LocalIdentity` = one `dyad_id` + one `ResponderKeypair`
  (`circuit_transport.rs:164`, `:200`).
- Runtime persists exactly ONE circuit identity per dyad: `circuit_identity.sealed` (`circuit_identity_store.rs:4`).
- `DyadKeyBundle` publishes ONE circuit keypair per DyadId (`dyad_ledger/key_bundle.rs:45`).

**R-b is therefore impossible without a new device-aware circuit-identity layer that does not exist.** The only
model compatible with circuit identity as built is **R-c**: dyad-level circuit, device identity carried INSIDE
the encrypted Sesame payload.

### 7.2 Delivery correction — R-c's "1× reaches all devices" was WRONG (load-bearing)

§2's lean claimed R-c delivers "the actual message 1× over the dyad circuit," implying one ciphertext reaches
all of B's devices. **Refuted.** A dyad-level circuit reaches the ONE B endpoint selected by the current
bundle/routing — not all of B's devices. The 1× ciphertext is correct *cryptographically* (one sender-key
ciphertext), but **delivery to every B device is a separate, currently-unsolved transport concern.** It requires
either:

- **§11.6 intra-dyad sync** — the terminating device fans the decrypted message to its siblings over local
  Continuity/BT/mDNS (platform-env-blocked), OR
- **a future device-aware routing layer** — relates to **HYP-313** (own-device send reroute); the runtime today
  explicitly states own-device/intra-dyad traffic does NOT ride the inter-dyad circuit (`private_channel_inbound.rs:41`).

**Consequence — the scope line of HYP-159b:** Sesame is **protocol-core orchestration that produces correctly-
keyed, device-addressed ciphertexts.** It does NOT own multi-device delivery. The live-delivery test is an
explicit `#[ignore]` seam (like §11.6 / the HYP-296 iOS block), blocked on the device-aware routing layer —
tracked, never faked.

### 7.3 Reframe — Sesame is orchestration; integration tests are protocol-core-level

The 5 chunks hold **only when reframed as protocol-core Sesame orchestration**, not live multi-device transport
delivery:

- `SesameSession` produces: **Option A** → N per-device ciphertexts (device-selector-addressed); **Option B** → 1
  sender-key ciphertext + the N×M `SenderKeyDistribution`s at first-use / rotation.
- Chunk 1–4 integration tests assert the **protocol-core matrix** (the device-pair ciphertext matrix decrypts;
  receive-demux keys correctly; concurrent ordering) — NOT a live `CircuitTransport` multi-device delivery, which
  CANNOT exist today without faking fan-out: the directory is `HashMap<DyadId, DyadKeyBundle>`, so two devices of
  one dyad **overwrite**, they don't coexist as addressable circuit endpoints.

### 7.4 Prerequisite gap (must precede chunk 1) — the local-device registry

There is NO source in runtime state for: local `DeviceId`, local device **signing** identity, local Sesame PKE
keys, or the cached peer `DyadDeviceBundle`. `server.rs` state holds `dyad_id`, `ratchet`, `local_prekeys`,
`circuit_identity`, bundle caches — but no Sesame local-device registry (`server.rs:38`). **Chunk 1 must FIRST
establish this registry** (effectively a chunk 0.5). Note the `RatchetManager` is itself dyad-keyed
(`HashMap<DyadId, RatchetState>`, `ratchet_manager.rs:397`); the device-pair ratchet map is NEW *inner* Sesame
state — explicitly NOT circuit state and NOT the existing ratchet manager.

### 7.5 Missed invariants (fold into §4 — each Codex-verified)

1. **Device signing-pubkey source — a real PQ gap.** `SenderKeyDistribution::verify(&HybridPubkey)`
   (`sender_key.rs:405`) needs a full hybrid (Ed25519 **+ ML-DSA**) signing key. But `DeviceInfo` carries only
   `device_peer_id` + `x25519_pk` + `ml_kem_pk` (`sesame/mod.rs:139`) — no signing key — and `DeviceCapabilityCert`
   (`pairing.rs`) is H+A 2-of-2 co-signed but binds only `dyad_id` + `device_peer_id` + authorised packet types,
   carrying no device signing pubkey either. The libp2p `device_peer_id` recovers only the *classical* half; the
   **ML-DSA half has no authenticated home today.** Resolution (chunk-1 prerequisite): add the device's hybrid
   signing pubkey to an authenticated structure — **preferred: extend `DeviceCapabilityCert`** (already the H+A
   2-of-2 device-authority cert) so the signing key inherits the bond's 2-of-2 trust; alternative: add it to
   `DeviceInfo` in the bond-shared `DyadDeviceBundle` (verify the bundle's authentication chain first). Decide +
   implement in chunk 1; do not let chunk 2's Option-B verify run against an unauthenticated key.
2. **Bind recipient + peer-dyad context.** `canonical_bytes` binds only
   `(sender_device_id, sender_key_id, counter, chain_key_ct)` (`sender_key.rs:366`) — NOT the recipient device id
   or peer dyad. A `SenderKeyDistribution` is therefore cross-replayable to a different recipient/dyad. Fix
   (touches the 159a primitive): extend the signed canonical bytes to include `recipient_device_id` +
   `peer_dyad_id`, OR bind both as AAD on the enclosing per-device envelope. Chunk-2 contract item; add a regression
   test that a distribution rejects when replayed cross-recipient.
3. **Revocation forces rotation.** A revoked/offboarded device MUST trigger immediate sender-key rotation BEFORE
   the next Option-B send (159a documents this MUST, `sesame/mod.rs:236`). The session enforces it on the
   membership-change event, not lazily. Chunk-3 adversarial test.
4. **Sesame self-enforces device revocation.** The runtime's existing device revocation / capability gates are
   RAW-transport scoped; circuit packets **bypass** them by design (`inbound.rs:1452`, `:1487`). So Sesame
   membership is the ONLY device-revocation enforcement point on the circuit path — it must consult the live
   membership set on **every send AND every receive**, not just at distribution. Chunk-3.
5. **Receive-state key triple.** Receive demux must key on `(sender_dyad_id, sender_device_id, sender_key_id)` —
   `sender_device_id` alone is per-dyad-scoped (a compact `DeviceId` index, §11.5), not globally unique. Chunk-4.

### 7.6 §11.6 reframed — load-bearing, not optional polish

§11.6 (intra-dyad sync) is NOT merely a platform-env-blocked nicety. Under the dyad-level circuit model, §11.6 OR
an equivalent device-aware routing layer is **REQUIRED** for the "message reaches every device" guarantee
(`private_channel_inbound.rs:41` confirms intra-dyad traffic does not ride the inter-dyad circuit). 159b ships the
orchestration + the `#[ignore]` delivery contract; the delivery layer itself is **HYP-313-adjacent** and tracked
as its own issue (file a follow-up under HYP-301's epic per rule #29).

### 7.7 Resulting chunk plan (supersedes §5 where they differ)

- **Chunk 1** — local-device registry prerequisite (§7.4) + resolve the device-signing-pubkey gap (§7.5.1) +
  `SesameSession` skeleton + the per-device-pair ratchet map as INNER state. Unit: per-device sub-chain
  independence (§11.5).
- **Chunk 2** — Option B at **protocol-core level** (the 4-device-pair ciphertext matrix decrypts; mid-conversation
  device addition gets sender-keys). Bind recipient+peer-dyad (§7.5.2) with the cross-replay regression test.
- **Chunk 3** — Option A + tier gate; revocation-forces-rotation (§7.5.3) + Sesame-self-enforces-revocation
  (§7.5.4) as adversarial tests.
- **Chunk 4** — concurrent-send (§11.5); receive-state keyed per §7.5.5.
- **Delivery seam** — `#[ignore]` live multi-device-delivery contract (§7.2 / §7.6), blocked on the device-aware
  routing layer; documented in `EXTERNAL_INJECTION_POINTS.md` + a HYP-313-linked follow-up issue.

**Chunk 1 is cleared to start** on this reframed basis: inner Sesame orchestration over a dyad-level circuit,
device identity in the payload, multi-device *delivery* explicitly out of 159b's scope.

---

## 8. Sesame fleet device identity (resolves §7.5.1) — the fleet flow does NOT exist yet

**Discovery (2026-06-12, pre-chunk-1 code read):** the entire Sesame *fleet* subsystem is unbuilt and unwired.
`DeviceInfo` / `register_device` / `DyadDeviceBundle::new` have **zero** production constructors (only their own
defs/docs); `sesame::` / `DyadDeviceBundle` / `SenderKeyState` are **not referenced in `dyados-runtime` at all**;
`DeviceCapabilityCert` is issued **only** in the iPhone-biosensor pairing flow (`build_accept`,
`authorised_packet_types: vec![Biosensor]`, `pairing.rs:858`). HYP-159a built the *primitives* (the structs +
sender-key crypto); **nothing constructs, provisions, or wires them.** Therefore §7.5.1 is not "add a field to an
existing flow" — there IS no fleet device-identity flow. 159b must **define it from scratch.** This section pins
the identity model before chunk 1; the original DESIGN-review (§7) explicitly handed this as the open item
("the design must specify where authenticated device signing pubkeys come from").

### 8.1 The device hybrid signing key is necessary — intra-dyad forgery is in scope

A dyad-level circuit/ratchet authenticates "*some* device of dyad A," not *which* device (the X25519+ML-KEM
bundle is per-dyad, §7.1). So a compromised device A2 could forge a `SenderKeyDistribution` claiming
`sender_device_id = A1` over the shared dyad ratchet keys — the AEAD alone can't stop it. The per-device hybrid
signature (`SenderKeyDistribution::verify(&HybridPubkey)`) is precisely what binds the `sender_device_id` claim to
a device-held key, giving **intra-dyad device authentication.** Since devices are individually compromisable AND
revocable (the entire point of §11.2 membership + offboarding), this threat is in scope. **→ each fleet device
MUST hold its own hybrid (Ed25519+ML-DSA) signing keypair.** "Drop the signature / rely on the ratchet AEAD" is
rejected — it would let any dyad-mate device impersonate any other.

### 8.2 The signing pubkey binds to a SIGNED structure (the bundle is unsigned)

`DyadDeviceBundle` / `DeviceInfo` are **unsigned** — `RawDyadDeviceBundle`'s `TryFrom` validates *structure*
(cap, id range, key lengths, uniqueness) but not *authenticity* (`sesame/mod.rs:163,312`); membership-change
authentication is delegated to the caller via the separately-signed `RevokeDeviceRecord` (`mod.rs:228-230`). The
H+A-2-of-2-signed device structures are `DeviceCapabilityCert` + `RevokeDeviceRecord`. **→ the authenticated
device signing pubkey binds into a SIGNED cert, never the bundle.** `DeviceInfo` may carry a convenience copy, but
verification trusts only the cert's copy (or cross-checks the two).

### 8.3 ~~Generalize `DeviceCapabilityCert`~~ — SUPERSEDED by §8.7

> **[SUPERSEDED 2026-06-12 by §8.7.](#87-codex-identity-consult-outcome-2026-06-12-run-b7enk0vl4--fleetdevicecert-not-cert-overload)**
> The Codex identity-consult **rejected** overloading `DeviceCapabilityCert` (it's biosensor/transport-scoped,
> the runtime ignores its version/sig/expiry on the hot path, and adding a required field breaks old certs before
> verify). The resolution is a **separate `FleetDeviceCert`** — see §8.7. The original §8.3 text is retained below
> as the audit trail of the rejected approach.

Rather than a parallel structure, **generalize the existing H+A-co-signed cert**: add
`device_signing_pk: Vec<u8>` (the hybrid pubkey bytes: Ed25519 32B ‖ ML-DSA pk) to its `canonical_signing_bytes`
(`pairing.rs:295`) + bump `version`, and let `authorised_packet_types` carry the full message set for fleet
devices (the field already exists for exactly this — its doc says "future Bios iOS app ships a richer set",
`pairing.rs:274`). One signed device-authority structure, extended.

- **Backwards-compat (rule "version everything crossing a boundary"):** existing biosensor certs (current
  `PAIRING_PROTOCOL_VERSION`, no signing key, biosensor-only) keep their canonical layout + verify unchanged;
  fleet certs use the bumped version and include `device_signing_pk` in the canonical bytes. Verifiers branch on
  `version`: pre-bump certs have no signing key (and are not valid Sesame fleet members — they can't originate
  `SenderKeyDistribution`s); post-bump certs do. **No shipped biosensor cert breaks.**
- The Ed25519 half MAY equal the device's libp2p identity key (recoverable from `device_peer_id`) or be an
  independent signing key carried in full — **carry both halves explicitly** in `device_signing_pk` so verify
  needs no peer-id decoding and the classical/PQ pair is bound as a unit by the H+A signature. (Pin the exact
  `HybridPubkey` byte layout against `crate::signing` in chunk 1a.)

### 8.4 Genesis + join (where the cert comes from)

- **Founding device (genesis):** holds H+A at dyad genesis → **self-issues** its own fleet cert (H+A co-sign,
  reusing the `sign_hybrid` path at `pairing.rs:873-874`) binding its freshly-generated `device_signing_pk`.
- **Subsequent fleet device (join):** generalize `IssuerSession::build_accept` beyond biosensor — the joining
  device generates its hybrid signing keypair locally, sends the **pubkey** in its join request; the device that
  holds H+A co-signs a fleet cert binding it (full packet allowlist + `device_signing_pk`). Reuses the entire
  pairing handshake; the only new surface is the signing-key field + the non-biosensor allowlist. (Secret key
  never leaves the joining device.)

### 8.5 Secret-key custody — the local-device registry (the §7.4 prerequisite)

The device's hybrid signing **secret** key is generated at registration and persisted **sealed**, exactly like
`circuit_identity.sealed` (AES-256-GCM, key derived from DyadID + H-shard per CLAUDE.md "Security"). The registry
(`SesameDeviceRegistry`, new) holds: local `DeviceId`, local hybrid **signing** secret + its cert, local Sesame
**PKE** (X25519 + ML-KEM) secrets (for Option-A per-device decrypt + sender-key receipt), and the cached peer
`DyadDeviceBundle` + peer fleet certs (the authenticated pubkey source for verify). This registry is the chunk-1
prerequisite; nothing in `SesameSession` can run without it.

### 8.6 Revised chunk 1 split (supersedes §7.7's chunk 1)

- **Chunk 1a — fleet device crypto identity (focused crypto PR + Codex gate).** (i) `DeviceCapabilityCert`
  signing-key extension §8.3 (field + canonical bytes + version branch + verify) with the backwards-compat test
  (an old biosensor cert still verifies; a fleet cert round-trips). (ii) device hybrid-signing keypair generation.
  (iii) the sealed `SesameDeviceRegistry` §8.5 + genesis self-issue §8.4. Integration test (rule #27): generate →
  self-issue cert → persist sealed → reload → verify cert + signing-key round-trip.
- **Chunk 1b — `SesameSession` skeleton + per-device-pair ratchet map** (inner state) + peer-cert-pubkey lookup
  wired so a `SenderKeyDistribution` verifies against the §8.2 cert copy. Unit: per-device sub-chain independence.
- **Chunk 1c (if 1a/1b grow) — the join-flow generalization** §8.4 (subsequent fleet devices via the extended
  `build_accept`).

Chunks 2–4 + the delivery seam are unchanged from §7.7. *(Chunk 1a's cert decision is revised by §8.7.)*

### 8.7 Codex identity-consult outcome (2026-06-12, run `b7enk0vl4`) — `FleetDeviceCert`, not cert-overload

Codex gpt-5.5/high read the real cert + ratchet + bootstrap code and ruled on §8's three open calls:

- **Q1 (§8.1 — per-device signing key necessary): CONFIRMED.** No existing binding makes the signature redundant
  — `RatchetManager` + circuit identity are both dyad-level (no device selector); `SenderKeyDistribution::verify`
  binds `sender_device_id` only if the caller supplies that device's authenticated `HybridPubkey`. Without it a
  compromised A2 can claim `sender_device_id = A1`. Use the hybrid device signature in chunk 1a. (A per-device-pair
  MAC is a *later* optimization for strictly-pairwise records; it does NOT remove the cert need — the peer still
  needs an authenticated source for A1's device keys.)

- **Q2 (§8.3 — extend cert vs new record): OVERRIDES §8.3 → a separate `FleetDeviceCert`.** Do NOT overload
  `DeviceCapabilityCert`:
  - It is transport/biosensor-scoped — the runtime collapses it to a peer-id→`PacketType` allowlist and
    **ignores version/signature/expiry on the hot path** (`inbound.rs:523`); the gate is Transport-only and circuit
    packets bypass it (`inbound.rs:1487`). `build_accept` is hardwired to `iphone_peer_id` + `vec![Biosensor]`
    (`pairing.rs:848,858`).
  - Fleet identity needs *different* semantics: compact `DeviceId`, the device signing pubkey, Sesame PKE material,
    membership/revocation — NOT a packet allowlist.
  - **Backcompat trap:** adding a *required* `device_signing_pk` to the existing cert breaks old serialized certs
    **before** `verify` runs; and bumping `PAIRING_PROTOCOL_VERSION` for a cert-schema change is rejected by
    `PairingJoiner::from_ticket` + `decrypt_a_shard` (`pairing.rs:925,986`).
  - **→ Add a purpose-built `FleetDeviceCert`** with its OWN cert-specific version, an H+A 2-of-2 hybrid signature,
    and explicit Sesame fields (`dyad_id`, `DeviceId`, `device_peer_id`, `device_signing_pk`, the device PKE
    pubkeys, `issued_at_ms` + optional expiry, `signature_field`). **Reuse the signing helper logic** (`sign_hybrid`
    + the `DyadSignature` field shape), not the cert type. `DeviceCapabilityCert` stays byte-for-byte untouched.

- **Q3 (§8.4 — genesis self-issue): CONFIRMED, with the timing constraint** already found: issue inside the genesis
  bootstrap window where H+A are both loaded (`create_new_dyad` returns both, `bootstrap.rs:1913/1949`; H drops at
  `:206`). No circularity — the founding device IS the genesis trust root.

**Missed (fold in):**

1. **NEW — sender-key MESSAGE authentication ≠ the distribution signature.** Signing only `SenderKeyDistribution`
   does not authenticate every future Option-B *message*: any recipient that learns the sender chain key can derive
   message keys and forge as the sender (the classic sender-keys receiver-forgery problem). **Each Option-B message
   must also carry a per-message sender authentication** (the sender device signs the message, à la Signal's
   `SenderKeyMessage`) — so the per-device signing key is used for BOTH the distribution AND every Option-B message.
   This shapes the Option-B message format → **chunk-2 contract item.**
2–3. Cert version separate from `PAIRING_PROTOCOL_VERSION` + old-cert *deserialization* tested (not just verify) —
   both satisfied by the separate `FleetDeviceCert` (its own version; the shipped cert's wire shape is unchanged).
4–6. Reaffirm §7.5.2 (recipient+peer-dyad binding), §7.5.5 (receive-state triple), §7.5.4 (Sesame revocation
   independent of the raw-transport `CapabilityRegistry`) — all mandatory, unchanged.

**Revised chunk 1a:** `FleetDeviceCert` (new struct + cert-specific version + canonical bytes + H+A hybrid
sign/verify, reusing `sign_hybrid`) + device `Keypair` generation + the sealed `SesameDeviceRegistry` (§8.5) +
genesis self-issue in the bootstrap window (§8.4). Integration test (rule #27): generate device keypair →
self-issue `FleetDeviceCert` (H+A co-sign) → persist sealed → reload → verify the cert's H+A signature + the
signing-key round-trip; plus a backcompat test that the shipped `DeviceCapabilityCert` wire shape is untouched. The
gate must confirm §8.1 (forgery justification) + the `FleetDeviceCert` isolation from the biosensor cert.

---

## 9. The `SesameSession` orchestration (chunk 1b onward) — pinning the per-device-pair model

**Status (2026-06-12):** the device-identity sub-layer (§8) is COMPLETE + merged (1a-i…1b-1, PRs #409-412).
This §9 pins the *orchestration* — the `SesameSession` that ties the §8 identity + the 159a sender-key primitives
into actual messaging — before chunk 1b code. It resolves the model questions that surfaced when grounding the
real ratchet/prekey API (`RatchetState`, `RatchetManager`, `LocalPrekeys`/`PublishedPrekeys`). Pending a Codex
DESIGN-consult (the §8 pattern) before chunk 1b.

### 9.1 The per-device-pair ratchet map — keyed by the PEER device

§8.6 wrote the map as `HashMap<(DeviceId, DeviceId), RatchetState>` (the conceptual full pair). But from THIS
node's runtime view, *our* device is fixed (this node IS one specific device of dyad A), so the only varying axis
is the peer. And a dyad talks to MANY peer dyads, each a fleet. So the live key is **`(peer_dyad_id,
peer_device_id) → RatchetState`** — one independent Double Ratchet per peer device, across all peer dyads. This
matches §7.5.5's receive-state triple (`sender_dyad_id, sender_device_id, …`). `SesameSession` is therefore a
**per-device-pair `RatchetManager`** (the existing manager is keyed by `DyadId`; this one by the peer-device
tuple), holding `Arc<SesameDeviceRegistry>` for our own identity.

### 9.2 THE CRUX — a peer's *ratchet* prekeys are NOT in its `FleetDeviceCert`

Establishing a per-device-pair ratchet uses the existing PQXDH: `establish_initiator(peer_published_prekeys)` →
`pqxdh_initiate` → `RatchetState::init_initiator`. But `PublishedPrekeys` needs **four** public keys:
`id_x_pk` + `id_kem_ek` (identity) **AND** `ratchet_x_pk` + `ratchet_kem_ek` (the initial ratchet prekey). The
`FleetDeviceCert` attests only the device's **identity** PKE keys (`device_x25519_pk` / `device_ml_kem_pk` =
`id_x_pk` / `id_kem_ek`). It does **not** carry a ratchet prekey. So: **where does a peer device publish its
ratchet prekeys, authenticated?** Candidate resolutions for the consult:

- **(P-a) A signed per-device prekey bundle.** Each device publishes a `DeviceLocalPrekeys`-style bundle
  (identity = its cert keys, + a rotating `initial_ratchet`), **signed by the device's own `FleetDeviceCert`
  signing key** (which §8 already gives every device). Authenticity chains: dyad H+A → fleet cert → device
  signing key → signs the rotating ratchet prekey. This reuses the §8 signing identity for exactly the job the
  per-dyad `LocalPrekeyManager` does today, but per-device. *(Leaning P-a — it's the direct per-device analogue of
  the existing rotating-prekey design, and the cert signing key is purpose-built to authenticate this.)*
- **(P-b) Carry an initial ratchet prekey IN the cert.** Add `ratchet_x_pk`/`ratchet_kem_ek` to `FleetDeviceCert`.
  Rejected-leaning: the cert is long-term (no expiry), but ratchet prekeys ROTATE for forward secrecy — baking a
  static ratchet prekey into a long-term cert defeats prekey rotation.
- **(P-c) Bootstrap the per-device-pair ratchet from a sender-key distribution** instead of PQXDH. Doesn't fit —
  Option A (Critical) needs a real per-device-pair ratchet independent of the group sender-key.

### 9.3 The device's own Sesame prekeys

Symmetrically, THIS device needs its own `LocalPrekeys` to respond: `identity` = the registry's PKE
`ResponderKeypair` (the cert-attested keys), `initial_ratchet` = a fresh per-device rotating ratchet keypair. So
the registry (or a companion per-device prekey manager) must also hold/rotate the device's ratchet prekey. Pin in
chunk 1b whether this extends `SesameDeviceRegistry` or is a sibling `SesameDevicePrekeys` (leaning sibling — keep
the long-term identity registry separate from the rotating prekey, mirroring how `circuit_identity` (long-term) is
separate from `LocalPrekeyManager` (rotating)).

### 9.4 Chunk-1b skeleton scope (after the crux is pinned)

`SesameSession { registry: Arc<SesameDeviceRegistry>, sessions: HashMap<(PeerDyadId, PeerDeviceId), RatchetState> }`
+ `establish_initiator` / `establish_responder` per peer device (reusing PQXDH against the §9.2-resolved peer
prekeys) + `encrypt` / `decrypt` routed by the peer-device key. **Unit (§11.5): per-device sub-chain independence**
— establish two peer-device ratchets, encrypt on one, prove the other's chain is unaffected + no cross-decrypt.
Option A/B + the per-message sender signature (§8.7 missed-#1) + the §11.6 delivery seam are chunks 2-4 (unchanged
from §7.7). The bootstrap genesis call (1b-1) currently establishes + drops the registry; chunk 1b's
runtime-integration step holds it (in `RuntimeState`) + builds the `SesameSession` over it.

### 9.5 Open questions for the Codex DESIGN-consult (before chunk 1b)

1. §9.2 — resolve **P-a vs P-b vs P-c** for the peer ratchet-prekey source, against the real PQXDH/`init_initiator`
   requirements + the FS implications of a long-term cert. Is P-a (cert-signing-key-signed rotating per-device
   prekey bundle) sound, and does anything in the existing `LocalPrekeyManager` / PQXDH preclude a per-device
   instance?
2. §9.1 — confirm the live key is `(peer_dyad_id, peer_device_id)`, and that one `SesameSession` spanning all peer
   dyads (vs. one per peer dyad) is the right granularity.
3. §9.3 — registry-extension vs sibling `SesameDevicePrekeys` for the device's own rotating ratchet prekey.
4. Any missed invariant in modelling `SesameSession` as a per-device-pair `RatchetManager` (e.g. the §8.7
   missed-#1 per-message signature interacting with the ratchet's own authentication).
