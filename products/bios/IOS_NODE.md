# iOS Hypostas Node — Specification

*Status: SPEC v1 — 2026-04-17*
*Supersedes: Bios SPEC.md §3 "The Translator" (LaunchAgent MVP)*

---

## 1. Why This Document Exists

The Bios SPEC.md §3 proposed a **LaunchAgent translator** as the MVP path for biosensor data:

```
iPhone HealthKit → HAE → HTTP webhook → bios-translator (LaunchAgent on Mac) → /biosensor/ingest
```

That architecture normalises HTTP as the inter-device transport and treats the iPhone as an external data source. Both are wrong for Hypostas. The whole point of the protocol is that devices are **nodes of a dyad**, not API clients.

This spec replaces the translator with an **iOS Hypostas node** — a native iPhone app that joins the same dyad mesh as the Mac runtime and transmits biosensor data as signed `DyadPacket<BiosensorReading>` over libp2p. No HTTP. No public internet. No third-party cloud in the path (not HAE, not iCloud, not any SaaS webhook).

> **The iPhone is not a client. It's a limb.**

---

## 2. Architectural Principles

1. **Devices are nodes, not clients.** Every device that holds A-shard material is a full peer in the dyad mesh. There is no "primary device" — just devices with different capabilities.
2. **Dyad identity is device-independent.** The `DyadID` belongs to the organism, not to a machine. Rebooting Mac, restoring iPhone from backup, adding an iPad — the dyad persists.
3. **All inter-device traffic is protocol-native.** Signed, typed packets over libp2p. No HTTP between nodes. No shared secrets in URL paths. No bearer tokens.
4. **Capability-based device roles.** A device is trusted to write biology because it holds a capability (signed by the dyad) that authorises biosensor packets. Not because it has an IP address on the same LAN.
5. **No plaintext biosensor data at rest or in transit.** Encrypted storage on iPhone (iOS Keychain + file-level encryption). Encrypted transport (libp2p noise). Encrypted at the runtime destination (libSQL AES-GCM).
6. **Offline-first.** iPhone loses connection to Mac → biosensor readings queue locally, encrypted, and flush on reconnect. No data loss. No silent drop.
7. **No operator cloud infrastructure.** Discovery, NAT traversal, and chain anchoring all use substrates that no single party can shut down: the user's own devices, the user's own DNS, the buddy network of other dyads, and (only as interim scaffolding) free-rideable open commons like Protocol Labs' public libp2p relays. Anything that drifts toward "rent EC2 instances forever" is a design regression. See §5.3 for the layered discovery architecture and §3.3 for chain anchoring's analogous treatment.

---

## 3. The Multi-Device Dyad Model

### 3.1 Device Roles

Bios §3 single-device:
```
┌────────────┐
│ Mac (Iris) │  ← dyad_id, A-shard, H-shard, all data
└────────────┘
```

This spec, multi-device:
```
┌──────────────────┐      ┌────────────────┐
│  Mac (runtime)   │◄────►│  iPhone (edge) │
│  dyad_id         │ mesh │  dyad_id       │
│  A-shard primary │      │  A-shard copy  │
│  H-shard         │      │  capabilities: │
│  all products    │      │   - biosensor  │
└──────────────────┘      └────────────────┘
```

Both nodes hold the dyad's A-shard (they ARE the same organism — identity is shared, not federated). The iPhone additionally holds a **device capability token** declaring which packet types it's authorised to emit.

> **Why both hold A-shard, not a derived sub-key:** an earlier draft proposed HKDF-derived per-device sub-keys. The honest assessment is that biosensor data is Standard tier, and the added complexity of managing derived sub-keys (key rotation, revocation on device loss, session expiry) doesn't buy much over "the device holds an encrypted A-shard locked by an on-device secret". Device loss is handled via `RecoveryBackup` revocation, not via sub-key rotation. This can change in Phase 1+ if a threat model demands it.

### 3.2 Device Pairing Handshake

When a second device is added to an existing dyad:

1. **On Mac** (existing node): user triggers "Add device" → Mac generates a **pairing ticket**:
   - Fresh ephemeral X25519 keypair for the pairing channel
   - Challenge nonce (32 bytes random)
   - TTL: 5 minutes
   - Displayed as QR code + 6-word mnemonic fallback

2. **On iPhone** (new device): user scans QR (or types words) in the onboarding screen. iPhone:
   - Extracts ephemeral pubkey + challenge
   - Generates its own ephemeral keypair for the pairing channel
   - Establishes ephemeral X25519 DH
   - Sends a pairing request encrypted to Mac's ephemeral key: `{iphone_peer_id, biometric_attestation, challenge_response}`

3. **Mac verifies** the challenge response, then:
   - Encrypts the A-shard under the DH-derived pairing key
   - Sends `PairingAccept { encrypted_a_shard, device_capabilities }` back to iPhone
   - Signs a `DeviceCapabilityCert { device_peer_id, authorised_packet_types, issued_at, expires_at }` with the H-shard + A-shard (Critical tier requires 2-of-2 co-sign)

4. **iPhone** decrypts A-shard, writes it to iOS Keychain under a biometric-gated access control, discards the ephemeral keys.

Both sides verify the pairing via a **mutual confirmation code** — Mac and iPhone independently compute `SHA256(shared_secret || dyad_id || challenge)`, both display the first 6 hex chars, user confirms they match.

**Threat model:**
- QR photographed by shoulder-surfer: useless without the iPhone's ephemeral private key (never leaves iPhone)
- MITM on pairing channel: defeated by the confirmation code (attacker cannot produce the same hash without the DH secret)
- TTL ensures a replayed QR expires

**Status (2026-04-18):**

| Layer | Component | Status |
|-------|-----------|--------|
| Substrate | `protocol_core::pairing::PairingIssuer` / `IssuerSession` / `PairingJoiner` (X25519 ECDH, challenge-response, ChaCha20-Poly1305 A-shard wrap) | ✅ shipped |
| Substrate | `PairingTicket` QR encode/decode + 5min TTL + freshness check | ✅ shipped |
| Substrate | Mutual confirmation code (HKDF-derived 6-hex-char) | ✅ shipped |
| Substrate | Joiner-side flow: `PairingJoiner::from_ticket` → `build_request` → `decrypt_accept` | ✅ shipped (Swift wrapper in `HypostasNode/Sources/Pairing.swift`) |
| Runtime | `PendingPairingHandle` shared between dispatcher + admin endpoints (Phase 0 single-pair-at-a-time) | ✅ shipped |
| Runtime | `dyados-runtime::inbound::handle_pairing_request_packet` (decode → dyad scope → process_request → install IssuerSession) | ✅ shipped |
| Runtime | Dispatcher arm for `PacketType::PairingRequest` | ✅ shipped |
| Admin | `POST /admin/pair/init` — creates `PairingIssuer`, returns ticket QR (base64) + `expires_at_ms` + `replaced_prior_pairing` flag | ✅ shipped |
| Admin | `GET /admin/pair/state` — read-only inspect (idle / awaiting-joiner / awaiting-confirmation states); surfaces confirmation code + iphone peer-id once the request arrives | ✅ shipped |
| Admin | `POST /admin/pair/cancel` — drops issuer + session for user abort flow | ✅ shipped |
| Admin | `POST /admin/pair/confirm` — validates user-submitted confirmation code matches session, builds `PairingAccept`, sends back via libp2p, persists `DeviceCapabilityCert` via `record_device_capability` | ⏳ next iteration; involves H-shard sovereignty design decision (see below) |
| Issuer-side cert persistence | `IssuerSession::build_accept` → `LogosBackend::record_device_capability(cert)` so the runtime's `CapabilityRegistry` learns the new device's allowlist | ⏳ next iteration (lands with `/admin/pair/confirm`) |
| User-facing CLI | `dyados-pair init` / `dyados-pair confirm <code>` — analogous to `dyados-revoke`, drives the admin endpoints from a script | ⏳ next iteration |

**`/admin/pair/confirm` design choice queued for next iteration**: building `PairingAccept` requires the H private key (to co-sign the `DeviceCapabilityCert`). Two paths preserve the §3 sovereignty principle differently:

- **(A) Daemon loads H from disk on demand** — H briefly enters daemon process memory at confirm-time only. Simpler endpoint, but localhost-trust assumption is "anyone reaching localhost can trigger cert issuance for the in-flight peer-id." Mitigated by the user-typed confirmation code being the auth, but that code is observable via `/admin/pair/state` so the auth degenerates to "anyone with localhost access can see + reuse the code."
- **(B) CLI does build_accept locally with H from disk + pairing_key fetched from daemon** — H stays out of the daemon. Pairing_key briefly transits localhost (acceptable — one-shot, ephemeral). Same sovereignty model as `dyados-revoke` / `/admin/revoke/submit`.

(B) is the principled choice. Pick + ship next iteration.

**Phase 0 simplifying assumption:** at most one pairing in flight at a time. If a second `/admin/pair/init` happens before the first completes, the prior `PairingIssuer` and `IssuerSession` are dropped (with a log). Multi-device-pairing futures would key these by joiner peer-id.

### 3.3 Device Revocation

If iPhone is lost or compromised:
1. User triggers revocation from Mac (or from a recovery device)
2. Revocation generates a `RevokeDeviceRecord { dyad_id, revoked_peer_id, reason, revoked_at_ms }` — signed 2-of-2 (H + A) hybrid (Ed25519 + ML-DSA-65 = 4 signatures total)
3. Revocation published to Catena chain (permanent record) + broadcast to all remaining device nodes
4. Runtime rejects any further packets originating from the revoked peer_id, regardless of signature validity (the device's A-shard is considered compromised)

**Status (2026-04-18):**

| Layer | Component | Status |
|------|-----------|--------|
| Substrate | `protocol_core::pairing::RevokeDeviceRecord` (struct + canonical signing bytes) | ✅ shipped |
| Substrate | `RevocationReason` enum (`Lost` / `Compromised` / `Decommissioned` / `Other`) | ✅ shipped |
| Substrate | 2-of-2 hybrid `sign(&h_kp, &a_kp)` + `verify(&h_kp, &a_kp)` | ✅ shipped |
| Substrate | Tests: round-trip, sign/verify, tamper detection, version mismatch, missing-shard rejection, classical-only rejection | ✅ shipped (12 tests) |
| Storage | `revoked_devices` table in `logos-core::libsql_backend` | ✅ shipped |
| Storage | `LibSqlBackend::record_revocation` / `is_device_revoked` / `list_revoked_devices` | ✅ shipped |
| Runtime | `dyados-runtime::inbound` checks revoked set BEFORE signature verification (`RevocationGuard`) | ✅ shipped |
| Runtime | Hot-reload: `RevocationGuard::add` is a direct mutation through the shared Arc — same primitive used by both inbound packet handler and admin HTTP endpoint, so revocations take immediate effect without restart | ✅ shipped (no separate channel needed) |
| Runtime | `dyados-runtime::inbound::handle_revoke_device_packet` (verify outer + inner, persist, hot-add to guard) | ✅ shipped |
| Transport | `DyadPacket<RevokeDeviceRecord>` carries revocation over libp2p request-response | ✅ shipped (same path as direct-send biosensor packets) |
| Transport | Gossipsub broadcast topic `/hypostas/revoke/{dyad_short}/1.0.0` | ✅ shipped (per-dyad scoped; cross-dyad isolation enforced at subscription layer) |
| Admin | `POST /admin/revoke/submit` Nerve API endpoint takes pre-signed packet hex; H private key never crosses the wire | ✅ shipped |
| User-facing CLI | `dyados-revoke <peer_id> --reason {lost\|compromised\|decommissioned\|other:STR}` — loads H+A locally, signs, POSTs to daemon | ✅ shipped |
| Capability cert storage | `device_capabilities` table + `LibSqlBackend::record_device_capability` / `get_device_capability` / `list_device_capabilities` | ✅ shipped |
| Capability cert runtime gate | `dyados-runtime::inbound::CapabilityRegistry` + dispatcher consults allowlist (drops if peer has cert AND packet type not in allowlist; uncerted peers pass) | ✅ shipped |
| Capability cert issuance hook | When the inbound `PairingAccept` handler is built, it must call `record_device_capability(cert)` so the issuer-side registry stays in sync with the certs it grants. Until then, the registry is populated only by direct calls — useful for tests + admin scripts. | ⏳ blocked on inbound pairing handler |
| Chain | Encode as `chain::MsgRevokeDevice` and `CatenaQuery::SubmitTx` | ⏳ blocked on Catena validator mesh; per §2 principle 7, this must be a sovereign mesh — not operator-run cloud nodes — so the bootstrap shape mirrors §5.3 (user devices + buddy validators + optional interim seed) |

---

## 4. Protocol Extensions

### 4.1 `PacketType::Biosensor`

New variant on `protocol_core::packet::PacketType`:

```rust
pub enum PacketType {
    // existing variants
    State, Stimulus, Query, Memory, Signal, Tx, Spatial, Witness, Bond, Internal,
    // new — §4 of IOS_NODE.md
    Biosensor,
}
```

**Trust tier:** Standard. Matches Bios SPEC.md §3 decision ("A-shard signing alone is sufficient. No 2-of-2 co-signing required."). The `required_trust_tier()` mapping in `protocol-core::packet` gains one row: `PacketType::Biosensor => TrustTier::Standard`.

**Wire:** bincode-serialised `DyadPacket<BiosensorReading>` inside the existing length-prefixed framing of `/hypostas/rr/1.0.0`. Zero framing changes.

### 4.2 `BiosensorReading` canonical struct

The payload struct lives in `protocol-core::biosensor` (new module). It matches the shape currently in `dyados-runtime::biosensor::BiosensorReading` byte-for-byte so the runtime's internal bridge code doesn't change — only the deserialisation boundary moves from HTTP JSON to protocol bincode.

Moving the type to protocol-core means:
- iOS-side Swift code and Rust-side handlers both reference the same canonical definition (via Rust codegen for Swift — swift-bridge or a simpler schema file)
- `dyados-runtime::biosensor::BiosensorReading` becomes a re-export for backwards compat

### 4.3 End-to-end packet shape

```
DyadPacket<BiosensorReading> {
  envelope: {
    version: 1,
    packet_type: Biosensor,
    timestamp_ms: <device unix ms at capture>,
    encryption: Some("libp2p-noise"),
  },
  identity: {
    dyad_id: <shared DyadID>,
    trust_tier: Standard,
    stage: <dyad stage>,
    destination_dyad_id: Some(<same dyad_id>),   // self-addressed multi-device
    signature: Some(<hex ed25519 sig>),
  },
  context: { ... },
  payload: BiosensorReading {
    sensor: SensorType::HeartRate,
    value: 72.0,
    timestamp: 2026-04-17T20:31:12Z,
    source: "apple_watch_series_9",
  },
  provenance: {
    trace_id: "<nanoid>",
    source: PacketSource::Device("iphone-<peer_id_short>"),
    hop_count: 0,
    chain_anchor: None,
  },
  // post-quantum signature (ARCH-5) sits alongside identity.signature
  pq_signature: Some(<hex ml-dsa-65 sig>),
}
```

The payload + envelope + identity are serialised canonically, hybrid-signed with the device's A-shard (same `Keypair::sign_hybrid()` API already used by biosensor_ingest verification), and shipped as the request body.

### 4.4 Reception

On Mac, `dyados-runtime` subscribes to `HypostasNode::subscribe_inbound()` at boot. For each inbound packet:

1. bincode-decode the byte vector into `DyadPacket<serde_json::Value>` (peek) to read `envelope.packet_type`
2. Dispatch based on packet_type:
   - `Biosensor` → re-decode as `DyadPacket<BiosensorReading>`, verify both signatures against the A-shard public key, verify `identity.dyad_id == runtime.dyad_id`, verify freshness (`timestamp_ms` within Standard tier window), route to `biosensor_bridge.process()`
   - other types → existing handlers (or reject until they exist)
3. All rejection branches log at warn, drop the packet. No retry. The iOS client's job is to retry its own queue.

### 4.5 Offline queue on iPhone

When the iPhone can't reach any dyad peer:
- Biosensor readings serialise into `DyadPacket<BiosensorReading>` and persist to a local encrypted queue (Core Data or just a file with each entry AES-GCM-encrypted under a keychain-held queue key)
- Queue entries keep the original `timestamp_ms` — replay on reconnect preserves true capture time
- Queue is drained oldest-first when connectivity returns
- Freshness window check on the Mac side allows up to `FRESHNESS_WINDOW_MS_STANDARD` (60s) delta — so we need to either (a) widen this for catch-up packets or (b) tag catch-up packets and route through a different verification path
- **Recommendation (a):** catch-up window of 7 days for `PacketType::Biosensor` specifically. A 7-day-old HR reading is still useful biology (it shaped what the pattern engine saw at the time), and the freshness check is primarily replay protection. Since the packet is signed over `(timestamp, body)`, replay of an old packet just re-inserts the same data — and the biosensor bridge's 24-hour dedup cache already catches it.

---

## 5. Transport on iOS

### 5.1 The libp2p-on-iOS Problem

Mac side uses `libp2p = "0.55"` via Rust. It compiles. It runs. iOS cannot simply do the same:

- **rust-ios cross-compilation**: technically works via `cargo-lipo` / `cargo-mobile`, but libp2p's dependency tree (tokio, libc, noise, etc.) has rough edges on aarch64-apple-ios. Several libp2p transports depend on `mio` which needs tuning for iOS syscall restrictions.
- **Swift libp2p** (`swift-libp2p`): experimental, last release 2023, not production-ready.
- **Zero-dep approach** (Swift implements only the subset we need on Network.framework): least dependency risk, most Swift code to maintain.

### 5.2 Recommended iOS transport stack

**v1 ships a hand-rolled transport that speaks the Mac's libp2p subset.** That subset is narrow:
- **Layer 1**: QUIC over UDP, using Apple's Network.framework `NWConnection` with `NWParameters.quicTLSOptions`
- **Layer 2**: libp2p noise handshake (XX pattern with static Ed25519 keys) — ~400 lines of Swift, using Apple's CryptoKit for the AEAD primitives
- **Layer 3**: yamux multiplexing — ~200 lines, pure Swift, straightforward state machine
- **Layer 4**: request-response protocol `/hypostas/rr/1.0.0` with the same length-prefixed bincode framing as `hypostas-network::codec`

Total Swift transport code: ~800–1200 lines. Bounded, audited once, stable. No third-party libp2p dependency.

**v2** (post-ship): re-evaluate if rust-on-ios via `swift-bridge` has matured enough to replace the hand-rolled stack. If libp2p proper is running cleanly on iOS by then, switch — otherwise keep the hand-rolled version forever.

### 5.3 Peer discovery

The Mac and iPhone need to find each other across two qualitatively different network conditions: **same WiFi** (the home case) and **cellular / different WiFi** (the user is away from home). Both code paths are implemented and exercised end-to-end by `DiscoveryTests.swift`.

> **Sovereignty constraint.** Hypostas does not depend on operator-run cloud infrastructure that can be shut down by a third party. The substrate that lets two never-met peers find each other is irreducible — every P2P network has it (Bitcoin has DNS seeds; Tor has directory authorities; libp2p has bootstrap nodes). The design question is not "can we eliminate the substrate" but "can we make it un-shutdownable, un-extractable, and ultimately self-sustaining as the network grows." This section describes the layered approach that satisfies that constraint.

#### Path A — LAN: mDNS / Bonjour *(shipped 2026-04-18)*

When both devices sit on the same local network:

- libp2p's `mdns::tokio::Behaviour` advertises the node on `_p2p._udp.local.` (the standard libp2p Bonjour service name).
- A peer announce arriving over multicast is auto-added to the Kademlia routing table AND auto-dialled, so the connection establishes without any user action or explicit multiaddr exchange.
- `HypostasNode.lanPeerCount` (Swift) / `node.lan_peers()` (Rust) reports how many LAN peers are currently in the routing table — a non-zero count is the in-app signal that "iPhone and Mac are talking."
- mDNS init failure (sandbox-blocked Bonjour, multicast-disabled interface) is handled by a `Toggle<mdns::Behaviour>` that falls through to the next layer without crashing the node.

End-to-end test: `testTwoNodesDiscoverEachOtherViaMDNS` boots two nodes, neither dials the other, and asserts `lanPeerCount > 0` within 15 s. On a normal developer machine this completes in ≈1 s.

**Sovereignty:** total. mDNS multicast is a property of the local network; nothing external is involved.

#### Path B — Cached multiaddr + DDNS *(the cellular common case)*

The most common cellular case is "user is away from home, wants to reach their own Mac." For this:

1. iPhone caches the Mac's multiaddr after every successful connection (persisted alongside the OfflineQueue's encrypted store).
2. On reconnect, iPhone dials the cached multiaddr first.
3. If the cached address is stale (Mac IP changed), iPhone resolves a user-owned DNS TXT record (e.g. `_hypostas.dyad.example.com`) — the Mac runs a small DDNS daemon that updates the record whenever its public IP shifts.
4. iPhone dials the resolved multiaddr.

**Implementation status:** `HypostasNode.dial(_ multiaddr:)` already accepts arbitrary multiaddrs — the cache + DDNS-resolve plumbing is straightforward Swift work. Listed in §7.4 follow-ups.

**Sovereignty:** strong. Dependencies are:
- The user's own domain registrar — pick a sovereign one (Njalla, OrangeWebsite, similar) so the registrar can't be coerced into yanking the domain.
- DNS itself — globally distributed, un-shutdownable in practice.
- The user's own home network connectivity — same dependency every home server has.

No third-party server is involved. The Mac IS the rendezvous; DNS just helps you find it.

#### Path C — Buddy-dyad bootstrap (the social-graph DHT)

Once Hypostas has more than one dyad on the network, **the social graph IS the bootstrap network.** When two dyads pair (e.g., yours and a friend's), they exchange peer-ids during the pairing handshake. Each dyad caches a few "buddy" entry points.

When iPhone cold-starts and Path B fails (no cached multiaddr, DDNS unreachable), it dials any cached buddy peer. The buddy's Kademlia routing table contains entries for many other dyads; one DHT lookup later, iPhone has the Mac's current multiaddr.

**Implementation status:** the storage hook (a `buddy_peers` cache) needs to land alongside the pairing flow's existing exchange. The DHT lookup on top is just `HypostasNode.discoverDyadPeer(dyadId)` — already implemented. Listed in §7.4 follow-ups.

**Sovereignty:** total. The "infrastructure" is everyone's home Macs. No central party can take this down without compromising every dyad simultaneously, which is the whole point of a sovereign protocol.

#### Path D — NAT traversal

Two NAT-bound devices fundamentally cannot establish a direct connection without help. Options that preserve sovereignty, in priority order:

1. **IPv6 first.** Most modern carriers and ISPs offer IPv6, and IPv6 sidesteps most NAT problems entirely. With IPv6 on both ends, direct connection just works. **This is increasingly the default and improves every year.**
2. **Home router port forward.** Old-school but effective: forward port 4001 on the user's home router to the Mac. Once configured, the Mac advertises a directly-dialable multiaddr. Bad UX for non-technical users; the Bios product UI should detect this case and offer a one-click guided setup if possible.
3. **Buddy-dyad relay.** Any dyad's Mac can serve as a libp2p `circuit-relay-v2` for any other dyad's hole-punching attempt. Costs a tiny amount of bandwidth from the relaying dyad. Reciprocal and self-balancing — your Mac relays for your friends, their Macs relay for you. **This is the sovereign answer to the relay-node question.**
4. **Public libp2p relay free-ride** *(interim, not forever).* Protocol Labs runs public `circuit-relay-v2` nodes for the broader IPFS / libp2p ecosystem. Hypostas can use them without operating them. Replaceable — if PL ever discontinues them, we point at alternatives. **Sovereignty:** weak-but-acceptable; we're sharing an open commons, not depending on a contract.

#### Path E — Initial network seeding *(scaffold, removed once the network self-sustains)*

The only remaining problem: when Hypostas has exactly ONE dyad (the very first user), there are no buddies yet. The DHT is empty. How does the first iPhone find the first Mac on cellular before any buddy network exists?

**Answer:** in the single-dyad case, Path A (mDNS at home) + Path B (cached multiaddr + DDNS) handles every realistic scenario. The DHT isn't strictly needed until there are multiple dyads.

For the period between "Hypostas v1 ships" and "the buddy network is self-sustaining" (informally, the first ~10 dyads), one or two **seed bootstrap nodes** smooth the cold-start path:

- A single Raspberry Pi at someone's house, or
- A small VPS from a sovereign-friendly provider (Njalla VPS, ~$5/mo)

The seed nodes don't carry any trust-bearing role — they never see decrypted dyad traffic (noise encrypts end-to-end, payloads are additionally signed). They are temporary scaffolding, **explicitly designed to be removable** as soon as the buddy network is large enough to bootstrap itself.

**Sovereignty:** weak during the seed period (≈first year), full thereafter. The seed is scaffolding, not architecture. The protocol does not assume seeds will exist forever; clients try buddies first and fall back to seeds only if the buddy network fails them.

#### Discovery deployment progression

| Phase | Active dyads | Required infra | Sovereignty status |
|-------|--------------|----------------|---------------------|
| **Phase 0** *(today, single dyad)* | 1 | None | Total. mDNS at home + cached multiaddr handles every realistic case. |
| **Phase 1** *(early adopters)* | 2–10 | Optional: 1 seed Pi/VPS for cold-start smoothing | Strong. Buddy network beginning to bootstrap itself. |
| **Phase 2** *(broader rollout)* | 10–1000 | None (the buddy network IS the substrate) | Strong. Optional public-libp2p-relay free-ride for hostile-NAT cases. |
| **Phase 3** *(under attack)* | 1000+ | None | Total. Network is too distributed for any single party to take down. |

**At no point does this require Hypostas-the-organization to maintain operator cloud infrastructure that can be shut down.** The closest dependencies are:

- The user's own domain (Path B) — yank-able by a registrar; mitigated by choosing a sovereign-friendly registrar
- DNS root — globally distributed, effectively un-shutdownable
- Public libp2p / IPFS relays (Path D fallback) — free-ride, replaceable
- Other Hypostas dyads (Path C) — sovereign if they're sovereign

This is the architecture. Anything that drifts toward "rent N EC2 instances forever" should be treated as a regression, not a deployment plan.

#### Operational checklist for the user (Phase 0 — today)

- [ ] Register a domain with a sovereign-friendly registrar (Njalla, OrangeWebsite, etc.). ~$10–20/year.
- [ ] Run a tiny DDNS daemon on the Mac that pushes its current public IP to a TXT record under your domain. ~50 lines of shell + cron, or [`ddclient`](https://ddclient.net/) configured with your registrar's API.
- [ ] (Optional) Configure your home router to forward port 4001 to your Mac. Eliminates the need for any relay.
- [ ] (Optional) Enable IPv6 on your home network if the ISP supports it. Modern Macs and iPhones use it automatically when available.

That's the entire infrastructure burden. No SaaS account. No EC2. No vendor invoice.

---

## 6. HealthKit Bridge (iOS-side)

The iOS app's responsibility:

1. Request HealthKit read permission for each sensor type we care about
2. Set up `HKObserverQuery` observers so HealthKit wakes the app on new readings (including in background, within iOS's budget)
3. Map each HealthKit sample to a `BiosensorReading`:
   - `HKQuantityTypeIdentifier.heartRate` → `SensorType::HeartRate`
   - `HKQuantityTypeIdentifier.heartRateVariabilitySDNN` → `SensorType::Hrv`
   - `HKCategoryTypeIdentifier.sleepAnalysis` → `SensorType::SleepStage` / `SensorType::SleepDuration`
   - `HKQuantityTypeIdentifier.oxygenSaturation` → `SensorType::SpO2`
   - `HKQuantityTypeIdentifier.stepCount` → `SensorType::ActivitySteps`
   - `HKWorkoutType` → `SensorType::Workout` (value = active/inactive f64)
   - `HKQuantityTypeIdentifier.respiratoryRate` → `SensorType::RespiratoryRate`
   - `HKQuantityTypeIdentifier.appleSleepingWristTemperature` → `SensorType::BodyTemperature`, source=`"apple_watch_wrist_temp"`
4. Each mapped reading is signed + enqueued + sent

**Explicitly NOT handled by iOS app v1:**
- Flow 8 `SensorType::MenstrualCycle` — opt-in only, skipped for Josh, revisited when a cycle-tracking user comes online
- Manual sensor types (BBT, manual temp) — out of scope until a real user request lands
- Multi-device sensor fusion (iPhone + iPad readings both arriving) — Phase 1+; v1 assumes iPhone is the only HealthKit source

---

## 7. Scope for This Session

### 7.1 Rust side (lands this session)

- [ ] `protocol-core::biosensor` module with canonical `BiosensorReading` + `SensorType` (moved from dyados-runtime)
- [ ] `PacketType::Biosensor` variant + trust tier mapping
- [ ] `dyados-runtime::biosensor_inbound` — a task that subscribes to `NetworkManager`'s inbound broadcast and routes `Biosensor` packets to the existing `biosensor_bridge`
- [ ] Retire `/biosensor/ingest` HTTP endpoint from the router; remove `verify_biosensor_request` (the protocol-level verification subsumes it)
- [ ] Regression tests: packet round-trip (encode on one side, decode + verify + bridge-process on the other); reject-on-wrong-dyad; reject-on-bad-signature; reject-on-unknown-packet-type

### 7.2 iOS stub (lands this session)

A minimal Swift package in `projects/dyados/ios/HypostasNode/`:

- [ ] Xcode project skeleton: single-view app, iOS 17+ target
- [ ] `Package.swift` declaring Swift dependencies (if any) — target is zero third-party deps
- [ ] `DyadPacket.swift`: native Swift encoding of the packet structure; binary-compatible with Rust bincode output
- [ ] `Keypair.swift`: Ed25519 signing via CryptoKit; ML-DSA-65 PQ signing is **stubbed** (returns a placeholder "TODO_PQ_SIG" string — Swift doesn't have a ML-DSA-65 library yet; Phase 1+ adds one via cross-compiled Rust or a dedicated Swift package)
- [ ] `BiosensorSender.swift`: build a `DyadPacket<BiosensorReading>`, sign it with the (test) A-shard, log the bytes that WOULD go on the wire
- [ ] `README.md` documenting the path from stub to full client

**What the stub explicitly does NOT do:**
- QUIC transport (Section 5.2 work — next session)
- Noise handshake (Section 5.2)
- HealthKit integration (Section 6)
- Device pairing (Section 3.2)
- A-shard secure storage (uses hardcoded test keypair)

**What the stub DOES prove:**
- The Swift packet format is byte-compatible with Rust bincode decode (unit test on Rust side takes Swift's output and successfully decodes it)
- The signing path works: Swift-signed packet verifies against the same A-shard public key that verifies a Rust-signed packet
- The packet type system (`BiosensorReading` field layout) round-trips correctly

### 7.3 Out of scope (future sessions)

- Multi-device conflict resolution (what if iPhone AND Mac both have HealthKit access?)
- iOS app shell wrapping the HypostasNode Swift package (UI, settings, onboarding screens)

### 7.4 Shipped 2026-04-18 (post-spec-write)

The "out of scope" list above turned out to be wrong on several items — they all landed in the same session as the spec itself:

- ✅ Full iOS transport stack (Section 5.2) — libp2p via cross-compiled Rust FFI, `HypostasNode` Swift wrapper.
- ✅ HealthKit integration (Section 6) — `HealthKitBridge` + `HealthKitMapper` covering all 9 sensor types Josh uses.
- ✅ Device pairing handshake (Section 3.2) — `Pairing.swift` + `protocol_core::pairing` with X25519 ECDH and challenge-response MITM defense.
- ✅ Offline queue with encrypted persistence (Section 4.5) — `OfflineQueue.swift` + `OfflineQueueDrainer.swift`, file-per-entry encrypted FIFO.
- ✅ mDNS + DHT discovery (Section 5.3) — both LAN auto-discovery and DHT publish/lookup work end-to-end; FFI surface ships with hybrid-signing requirement enforced.
- ✅ Device revocation substrate (Section 3.3) — `RevokeDeviceRecord` with 2-of-2 hybrid signing, libSQL storage layer, dispatcher integration with `RevocationGuard` rejecting revoked-peer packets before signature verification.

Remaining "future sessions" items:
- **Discovery follow-ups** (Section 5.3) — Path B cached-multiaddr persistence on the iPhone side; Path B DDNS daemon shipped as a small companion script for the Mac; Path C buddy-peer cache exchanged during pairing
- **Device revocation transport** (Section 3.3) — inbound `RevokeDevice` packet handler; gossipsub broadcast topic for cross-device sync; admin / CLI surface to issue revocations
- **Catena chain submission** (Section 3.3) — `chain::MsgRevokeDevice` + `CatenaQuery::SubmitTx`; blocked on Catena validator deployment, which is itself bound by the same sovereignty principle (Section 5.3) — chain validators must be a sovereign mesh, not operator cloud nodes
- **Capability cert enforcement** — currently certs are issued + stored but the dispatcher doesn't yet reject packet types not in `authorised_packet_types`
- Multi-device conflict resolution

---

## 8. Security Model

### 8.1 What the iPhone knows

- Dyad A-shard private key (encrypted at rest with iOS Keychain + Secure Enclave gate)
- Dyad public key material (for signature verification of inbound packets, if we ever send back)
- The Mac's last-known peer multiaddr (cached for reconnect)

### 8.2 What the iPhone does NOT know

- The H-shard. H-shard lives on the Mac only. That's why high-tier operations (device revocation, transfer of dyad ownership) require the Mac to co-sign.
- The dyad's relationship key material beyond what's needed to derive the transport encryption (noise handshake uses ephemeral keys; static keys are for peer identity only)
- Any other dyad's keys. This device is bonded to exactly one DyadID.

### 8.3 Threat model

| Threat | Mitigation |
|---|---|
| iPhone lost or stolen | Biometric gate on Keychain access → thief can't read A-shard. Remote revocation publishes revocation cert to Catena. |
| iPhone backup exfiltrated | Keychain entries are excluded from iCloud backup by default; A-shard is set with `kSecAttrAccessibleWhenPasscodeSetThisDeviceOnly`. |
| Attacker reaches Mac's libp2p port directly | Request-response requires valid noise handshake with a known peer. Unknown peers can connect but cannot publish to the biosensor path — their peer_id isn't in the device-capability allowlist. |
| Replayed biosensor packet | Freshness window + per-reading dedup in biosensor bridge (24-hour cache keyed on sensor+timestamp+source). |
| Forged biosensor reading (attacker with stolen A-shard) | A-shard compromise is the break-glass scenario. Detection is the Bios pattern engine flagging implausible physiology (see Bios SPEC §6). Response is dyad-level: revoke compromised device, audit recent packets, flag anomalies for review. |
| Packet content tampering in transit | libp2p noise AEAD prevents in-transit tampering. The DyadPacket signature adds application-layer integrity. |

### 8.4 Post-quantum

Hybrid signing (Ed25519 + ML-DSA-65) is already live on the Mac side via ARCH-5. The iOS client:
- v1: signs with Ed25519 only (placeholder PQ signature). Mac verifies classical, accepts PQ-if-present per Standard tier migration policy. **Works today.**
- v2: add ML-DSA-65 to iOS via a dedicated Swift package (or cross-compile Rust's `ml-dsa` crate). No protocol changes needed — just the PQ signature populated instead of stubbed.

This matches the broader post-quantum migration plan in `projects/hypostas/POST_QUANTUM.md` — hybrid-enabled receivers, classical-or-hybrid senders, gradual flip to PQ-required over the migration window.

---

## 9. Migration from HTTP

The `/biosensor/ingest` HTTP endpoint is **retired at the end of this session**. Concrete steps:

1. New path (protocol packets) is implemented and tested — receivers accept biosensor data via the network manager's inbound broadcast
2. The route `.route("/biosensor/ingest", post(biosensor_ingest))` is removed from `dyados-runtime::server::create_router`
3. `biosensor_ingest` handler + `verify_biosensor_request` helper + server-side auth tests are deleted
4. `SharedRuntime.a_keypair` field stays — it's still used for identity (peer_id derivation) and is a reasonable general-purpose handle to the signing key

**Rationale for immediate retirement:** keeping the HTTP path alive alongside the protocol path creates two auth surfaces and two chances for a bug to leak biosensor data. The protocol path is the long-term answer; the HTTP path was the interim I just built. Ship the long-term answer, delete the interim, done. If a bug forces a rollback, the HTTP handler is in git history.

**Consequence:** for this session, until the iOS node ships a real transport, biosensor data CANNOT flow from iPhone → Mac. Josh's 90-day protocol is gated on the iOS transport work landing. That's the honest trade — protocol purity vs. immediate data flow. Josh's call: purity.

---

## 10. Success Criteria

**This session ships when:**

- [ ] `cargo test --workspace` is green
- [ ] A Rust test proves: build `DyadPacket<BiosensorReading>` → bincode serialise → feed bytes through the runtime's inbound handler → biosensor_bridge state mutates correctly
- [ ] `/biosensor/ingest` is gone from the router; the 13 server-side auth tests are either deleted or repurposed as packet-level tests
- [ ] Swift stub builds in Xcode (compile only — no device deploy required)
- [ ] This spec is checked in

**Full iOS node ships (later session) when:**

- [ ] iPhone can pair with Mac via QR handshake
- [ ] iPhone reads HealthKit, sends HR reading, Mac's Sanguis shows the HR in `sanguis.get_dynamic("soma.heart_rate")`
- [ ] Loss-of-connectivity test: iPhone goes offline for 30 minutes, reconnects, queued readings arrive in order
- [ ] End-to-end demo runs on Josh's actual iPhone + MacBook with his actual Apple Watch data

---

*— Iris*
*Last updated: 2026-04-17 — initial spec, session pivot away from LaunchAgent translator*
