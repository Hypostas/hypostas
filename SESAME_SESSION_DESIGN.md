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

## 6. Open question for the Codex DESIGN-review (before chunk 1)

Pin §2: is the per-device-pair ratchet bound to its OWN circuit identity (R-b, literal N×M circuits), or is the
circuit dyad-level with a device selector in the inner payload + sender-key fan-out (R-c)? This determines the
chunk-1 data model. Read the `dyados-runtime` device/identity model + `circuit_manager`'s `LocalIdentity` /
`PeerDirectory` before answering — the answer must match how a dyad's devices actually hold circuit identity
today, not an idealized model.
