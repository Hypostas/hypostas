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
