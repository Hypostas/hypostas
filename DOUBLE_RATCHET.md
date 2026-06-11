# DOUBLE_RATCHET.md — Hypostas PQ-Hybrid Double Ratchet

**Status:** Draft (2026-05-22, v0.1)
**Owner:** `protocol-core`, `hypostas-network`
**Authors:** Josh + Iris
**Anchored to:** [THREAT_MODEL.md](THREAT_MODEL.md) §5.1, §5.6, §6.1, §11.5
**Companion specs:** [SEALED_ENVELOPE.md](SEALED_ENVELOPE.md) (wire format that carries ratchet output), [POST_QUANTUM.md](POST_QUANTUM.md) (hybrid kex spec), [HYPOSTAS_PROTOCOL.md](HYPOSTAS_PROTOCOL.md) (DyadPacket structure)
**Linear:** [HYP-117](https://linear.app/hypostas/issue/HYP-117) (parent [HYP-115](https://linear.app/hypostas/issue/HYP-115))
**Replaces:** static-key derive at [`hypostas-network/src/encryption.rs:54-69`](../dyados/hypostas-network/src/encryption.rs:54)

---

## §1 Purpose

The Double Ratchet is Hypostas's content-layer key schedule. It provides:
- **Per-message forward secrecy:** compromise of today's key cannot decrypt yesterday's messages
- **Post-compromise security (PCS):** compromise of one device recovers privacy within one ratchet step
- **Post-quantum hybrid:** X25519 + ML-KEM-768 combined keys, survives store-now-decrypt-later attacks
- **Asynchrony tolerance:** out-of-order messages decrypt correctly within a configurable window
- **Independence from transport:** ratchet state is a pure cryptographic state machine; sealed envelopes carry the bytes

The ratchet produces the keys that AEAD-encrypt the *inner* DyadPacket. The sealed envelope ([SEALED_ENVELOPE.md](SEALED_ENVELOPE.md)) provides identity secrecy at the routing layer with its own per-packet ephemeral keys; the ratchet provides content secrecy and FS at the dyad-pair layer with persistent ratchet state shared between Alice and Bob.

**Today's gap:** [`hypostas-network/src/encryption.rs:54-69`](../dyados/hypostas-network/src/encryption.rs:54) derives a static shared key from identity Ed25519 keys via X25519 + HKDF. **Zero forward secrecy.** Compromise of either dyad's H-shard decrypts the entire conversation history. Quantum-day reveals everything. This spec replaces that with Signal-pattern Double Ratchet plus post-quantum hybridization.

### §1.1 Threat-model coverage

| Property | Defense provided by this spec | Where else |
|---|---|---|
| §5.1 Content secrecy | ChaCha20-Poly1305 AEAD with per-message keys derived from ratchet state | — |
| §5.6 Future secrecy / FS | KDF chain advances per message; old keys deleted; DH ratchet refreshes long-term keys; PQ-hybrid X25519+ML-KEM | — |
| §5.6 Post-compromise security | One DH ratchet step after compromise recovers privacy | — |
| §5.2 Identity secrecy | — | [SEALED_ENVELOPE.md](SEALED_ENVELOPE.md) (outer envelope hides identity at routing layer) |

### §1.2 Adversary coverage

| Adversary | Defended? | How |
|---|---|---|
| §4.1 Passive observer | ✅ full | AEAD content secrecy; can't decrypt without ratchet state |
| §4.2 Active adversary | ✅ full | + per-message authenticity, no malleability |
| §4.3 GPA capturing today, breaking tomorrow | ✅ full | PQ hybrid kex; ML-KEM survives quantum |
| §4.4 Compromised relay | ✅ full | Relay sees only sealed envelope; never has ratchet state |
| Endpoint compromise — current keys | Defended at next ratchet step | PCS recovers; one-step exposure |
| Endpoint compromise — past keys | ⚠️ if past chain keys were ever persisted | Mitigated by skipped-message-key encryption + master-key zeroization |

---

## §2 Architecture overview

The Double Ratchet is two ratchets composed:

**Symmetric ratchet (KDF chain):** advances per message. Cheap, fast, per-message FS. Each message advances both sending and receiving chains independently using HKDF.

**DH ratchet:** advances per N messages or T time. More expensive, provides PCS. Each party periodically generates a fresh ephemeral keypair, sends the public key with the next outgoing message, and both parties re-key from the new shared secret.

**Hybrid kex:** every DH ratchet step uses BOTH X25519 and ML-KEM-768. Shared secrets combined via HKDF. An attacker must break both primitives to compromise a ratchet step.

```
                  ┌──────────────────────────────────────────┐
                  │            Root Key (RK)                  │
                  │  (advances on each DH ratchet step)       │
                  └──────────┬───────────────────┬───────────┘
                             │                   │
                  ┌──────────▼──────┐   ┌────────▼──────────┐
                  │ Sending Chain   │   │ Receiving Chain    │
                  │ (advances per   │   │ (advances per      │
                  │  outbound msg)  │   │  inbound msg)      │
                  └─────────────────┘   └────────────────────┘
                       │                       │
                  per-message keys         per-message keys
                  for AEAD encrypt         for AEAD decrypt
```

Each party maintains:
- `RK` — current root key, 32 bytes
- `CK_send` — current sending chain key, 32 bytes
- `CK_recv` — current receiving chain key, 32 bytes
- `dh_self_sk, dh_self_pk` — current ratchet keypair (X25519 + ML-KEM)
- `dh_remote_pk` — remote party's current ratchet pubkey (X25519 + ML-KEM)
- `N_send, N_recv` — message counters in each chain
- `PN` — previous-chain message count (sent with each DH ratchet step for out-of-order recovery)
- `skipped_keys` — map of (dh_remote_pk_hash, N) → message_key for out-of-order receive

---

## §3 Cryptographic primitives

| Primitive | Algorithm | Source |
|---|---|---|
| Asymmetric kex (classical) | X25519 | RFC 7748 |
| Asymmetric kex (PQ) | ML-KEM-768 | FIPS 203 |
| KDF | HKDF-SHA256 | RFC 5869 |
| Symmetric AEAD | ChaCha20-Poly1305 | RFC 8439 |
| Hash | SHA-256 | FIPS 180-4 |
| Hybrid combiner | HKDF(salt=0, ikm=x25519_ss \|\| ml_kem_ss, info=label) | [POST_QUANTUM.md](POST_QUANTUM.md) |
| KDF chain advance | HKDF(salt=CK, ikm=constant, info=label) | Signal Double Ratchet |
| Message key derivation | HKDF(salt=CK, ikm=constant, info="msg-key") | Signal Double Ratchet |

---

## §4 Initial handshake (PQXDH-style)

First-time dyad pair-bond uses a one-time-prekey-based asynchronous handshake. This is invoked once per pair at bond ceremony — subsequent communication runs the ratchet.

### §4.1 Prekey bundle

Each dyad publishes (via Vita Chain or DHT) a prekey bundle:

```rust
PrekeyBundle {
    dyad_id: DyadId,                          // 32 bytes (SHA-256 of identity pubkey)
    identity_pubkey_x25519: [u8; 32],         // Long-term X25519 identity key
    identity_pubkey_ml_kem: [u8; 1184],       // Long-term ML-KEM-768 identity key
    signed_prekey_x25519: [u8; 32],           // Medium-term X25519 (rotated weekly)
    signed_prekey_ml_kem: [u8; 1184],         // Medium-term ML-KEM-768
    signed_prekey_signature: HybridSig,       // Ed25519+ML-DSA-65 sig over the two signed_prekeys
    one_time_prekeys_x25519: Vec<[u8; 32]>,   // One-shot keys (consumed on use; ~100 published at a time)
    one_time_prekeys_ml_kem: Vec<[u8; 1184]>, // Paired one-shot ML-KEM keys
    bundle_version: u8,                       // Format version (0x01 for this spec)
}
```

Bundle is signed by the dyad's identity key and stored either:
- **Phase 1:** in the local peer table at pair-bond time (in-person QR exchange via existing [`pairing.rs`](../dyados/protocol-core/src/pairing.rs))
- **Phase 3:** on Vita Chain via `IntroductionRecord` (deferred per [THREAT_MODEL §10](THREAT_MODEL.md) open question 1)

### §4.2 Handshake — Alice initiates to Bob

Alice fetches Bob's `PrekeyBundle`. Alice generates ephemeral handshake keypair `(EK_x25519, EK_ml_kem)`. Computes:

```
DH1 = X25519_DH(EK_x25519_sk, Bob.identity_pubkey_x25519)
DH2 = X25519_DH(Alice.identity_x25519_sk, Bob.signed_prekey_x25519)
DH3 = X25519_DH(EK_x25519_sk, Bob.signed_prekey_x25519)
DH4 = X25519_DH(EK_x25519_sk, Bob.one_time_prekey_x25519)  // if available

(KEM1_ct, KEM1_ss) = ML_KEM_768::encapsulate(Bob.identity_pubkey_ml_kem)
(KEM2_ct, KEM2_ss) = ML_KEM_768::encapsulate(Bob.signed_prekey_ml_kem)
(KEM3_ct, KEM3_ss) = ML_KEM_768::encapsulate(Bob.one_time_prekey_ml_kem)  // if available

x25519_ss = DH1 || DH2 || DH3 || (DH4 if present)
ml_kem_ss = KEM1_ss || KEM2_ss || (KEM3_ss if present)

SK = HKDF(salt=0, ikm=x25519_ss || ml_kem_ss, info="hypostas-pqxdh-v1")  // 32 bytes
```

`SK` is the initial shared key. Both Alice (computed above) and Bob (computed from his secret keys + the ciphertexts and ephemeral pubkeys Alice sends) derive the same value.

Alice's first message contains a `HandshakeHeader`:

```rust
HandshakeHeader {
    alice_dyad_id: DyadId,
    alice_identity_pubkey_x25519: [u8; 32],
    alice_identity_pubkey_ml_kem: [u8; 1184],
    alice_ephemeral_pubkey_x25519: [u8; 32],
    alice_ephemeral_pubkey_ml_kem: [u8; 1184],
    kem_ct_to_bob_identity: [u8; 1088],
    kem_ct_to_bob_signed_prekey: [u8; 1088],
    kem_ct_to_bob_one_time: Option<[u8; 1088]>,
    bob_one_time_prekey_id: Option<u32>,  // identifies which one-time prekey was used
    signature: HybridSig,                  // Alice's identity-key sig over the above
}
```

This header is part of the inner DyadPacket payload, AEAD-encrypted with `SK`. Bob receives, verifies signature, computes `SK` himself, decrypts the message, and both parties bootstrap into the ratchet state from `SK`.

### §4.3 Ratchet bootstrapping from SK

After handshake:
- `RK = SK`
- Bob immediately generates a fresh ratchet keypair `(B_ratchet_sk, B_ratchet_pk)` (X25519 + ML-KEM-768)
- On Bob's first message back, he includes `B_ratchet_pk` + a fresh ML-KEM ciphertext to Alice's identity ML-KEM key, and Alice does the first DH ratchet step on receive
- After this initial exchange, both parties are in steady-state Double Ratchet

---

## §5 Sending a message (steady-state)

Once handshake is complete, ongoing message send works as follows:

### §5.1 Advance sending chain

```
(CK_send', mk) = HKDF_expand(CK_send, info="hypostas-chain-advance-v1", length=64)
  where CK_send' = first 32 bytes, mk = last 32 bytes
CK_send ← CK_send'
N_send ← N_send + 1
```

`mk` is the message key for this single outgoing message.

### §5.2 Build message header

```rust
MessageHeader {
    dh_self_pubkey_x25519: [u8; 32],   // Alice's current ratchet X25519 pubkey
    dh_self_pubkey_ml_kem: [u8; 1184], // Alice's current ratchet ML-KEM pubkey
    kem_ct_for_next_recv: [u8; 1088],  // ML-KEM ct to Bob's current ratchet ML-KEM key
    pn: u32,                            // Previous-chain message count
    n: u32,                             // This message's counter in the current chain
}
```

The `kem_ct_for_next_recv` is encapsulated against **Bob's current ratchet ML-KEM pubkey**. On every send, Alice includes a fresh ML-KEM ciphertext so Bob can advance the PQ leg of the next DH ratchet without an extra round trip. This is the key design choice that lets ML-KEM ride alongside X25519 in the ratchet without doubling the round-trip cost.

### §5.3 AEAD-encrypt the inner payload

```
nonce = HKDF(salt=0, ikm=mk, info="hypostas-msg-nonce-v1", length=12)
(ciphertext, tag) = ChaCha20Poly1305::encrypt(
    key=mk,
    nonce=nonce,
    ad=serialize(MessageHeader),
    plaintext=DyadPacket_inner_bytes
)
```

### §5.4 Zeroize message key

`mk` is single-use. Immediately after encryption:

```rust
mk.zeroize();
```

(via `zeroize` crate's `Zeroize` derive). Even if the process is then compromised, `mk` is gone.

### §5.5 Assemble the inner payload

The inner DyadPacket payload that goes into the sealed envelope:

```
inner_payload = MessageHeader || ciphertext || tag
```

This becomes the AEAD plaintext for the sealed envelope's outer layer.

---

## §6 Receiving a message (steady-state)

### §6.1 Parse and validate header

Extract `MessageHeader` from the inner payload. Validate field lengths.

### §6.2 Check for DH ratchet step

If `header.dh_self_pubkey_x25519 != self.dh_remote_pk_x25519` (Alice's ratchet key has changed):
- Save the previous chain's remaining keys to `skipped_keys` (see §8)
- Perform DH ratchet step (see §7)

### §6.3 Catch up receiving chain

Advance `CK_recv` from `N_recv` to `header.n`:
```
while N_recv < header.n:
    (CK_recv', mk) = HKDF_expand(CK_recv, info="hypostas-chain-advance-v1", length=64)
    skipped_keys[(dh_remote_pk_hash, N_recv)] = mk
    CK_recv ← CK_recv'
    N_recv ← N_recv + 1
```

Then derive the message key for this specific message:
```
(CK_recv', mk) = HKDF_expand(CK_recv, info="hypostas-chain-advance-v1", length=64)
CK_recv ← CK_recv'
N_recv ← N_recv + 1
```

### §6.4 AEAD-decrypt

```
nonce = HKDF(salt=0, ikm=mk, info="hypostas-msg-nonce-v1", length=12)
plaintext = ChaCha20Poly1305::decrypt(
    key=mk,
    nonce=nonce,
    ad=serialize(MessageHeader),
    ciphertext=ciphertext,
    tag=tag
)?  // Reject on tag mismatch
```

### §6.5 Zeroize key + deserialize

`mk.zeroize()` (single-use). Deserialize plaintext as `DyadPacket`.

---

## §7 DH ratchet step

Triggered when:
- Inbound message has a new `dh_self_pubkey` (peer ratcheted)
- Outbound message after N messages or T time (THREAT_MODEL §11.5: `RATCHET_DH_INTERVAL_MESSAGES = 100`, `RATCHET_DH_INTERVAL_HOURS = 24`)

### §7.1 On inbound ratchet (peer ratcheted)

```
// Save previous receiving chain remaining keys to skipped
save_skipped_keys(self.dh_remote_pk_hash, current_CK_recv, N_recv, header.pn)

// Update remote ratchet pubkey
self.dh_remote_pk_x25519 = header.dh_self_pubkey_x25519
self.dh_remote_pk_ml_kem = header.dh_self_pubkey_ml_kem

// Compute hybrid shared secret using OUR current ratchet keys + peer's new keys
x25519_ss = X25519_DH(self.dh_self_sk_x25519, header.dh_self_pubkey_x25519)
ml_kem_ss = ML_KEM_768::decapsulate(self.dh_self_sk_ml_kem, header.kem_ct_for_next_recv)

// Derive new root key + receiving chain key
RK', CK_recv' = HKDF(salt=RK, ikm=x25519_ss || ml_kem_ss, info="hypostas-ratchet-recv-v1", length=64).split()
RK = RK'
CK_recv = CK_recv'
N_recv = 0

// Generate OUR new ratchet keypair
(self.dh_self_sk_x25519, self.dh_self_pk_x25519) = X25519::keygen()
(self.dh_self_sk_ml_kem, self.dh_self_pk_ml_kem) = ML_KEM_768::keygen()

// Compute NEW sending chain via second hybrid step using our new keys + their pubkeys
x25519_ss_2 = X25519_DH(self.dh_self_sk_x25519, header.dh_self_pubkey_x25519)
(kem_ct_2, ml_kem_ss_2) = ML_KEM_768::encapsulate(header.dh_self_pubkey_ml_kem)
self.pending_kem_ct = kem_ct_2  // Send with next outbound message

RK'', CK_send' = HKDF(salt=RK, ikm=x25519_ss_2 || ml_kem_ss_2, info="hypostas-ratchet-send-v1", length=64).split()
RK = RK''
CK_send = CK_send'
N_send = 0
PN = previous N_send
```

This is the canonical Signal Double Ratchet step, hybridized.

### §7.2 On outbound ratchet (time/count trigger)

We don't initiate a unilateral ratchet step; instead, the next outbound message simply carries `header.dh_self_pubkey` (which already reflects our current keys, possibly from a previous inbound-triggered step). To force a ratchet, we generate a new keypair and send a message — the peer's response will trigger the symmetric inbound step on their side.

For pure-outbound-driven ratchets (idle peer), we send a "ping" inner DyadPacket with empty payload but containing fresh ratchet keys.

---

## §8 Skipped message keys

For out-of-order receive, save message keys for messages that have not yet arrived but whose chain has advanced past them.

### §8.1 Storage structure

```rust
pub struct SkippedKey {
    chain_id: [u8; 32],          // SHA-256 of (dh_remote_pk_x25519 || dh_remote_pk_ml_kem)
    n: u32,                      // Message counter in that chain
    key: [u8; 32],               // The message key (ZeroizeOnDrop)
    inserted_at: i64,            // Unix ms (for TTL)
}

pub struct SkippedKeyStore {
    keys: HashMap<(ChainId, u32), SkippedKey>,
    max_entries: usize,           // 1024 per THREAT_MODEL §11.5
    ttl_ms: i64,                  // 7 days per THREAT_MODEL §11.5
}
```

### §8.2 Bounds

- **Max entries:** 1024 (THREAT_MODEL §11.5 `RATCHET_SKIPPED_MESSAGE_KEYS_MAX`). Eviction policy: oldest-first (LRU by `inserted_at`).
- **TTL:** 7 days. Periodic background sweep removes expired entries.
- **Per-chain limit:** prevent a malicious peer from forcing unlimited skipped keys in one chain — limit to 256 per chain.

### §8.3 Storage strategy

**Decision (deferred open question 3 from HYP-117):** persisted on disk encrypted at rest.

Why persisted: in-memory-only loses keys on app restart. Messages received after restart but sent before would be undecryptable. Acceptable for chat (re-request) but unacceptable for biosensor batches or memory writes.

Why encrypted: the skipped-keys store IS the post-compromise-vulnerable artifact. An attacker getting the disk file but not the master key cannot decrypt anything.

Encryption: AES-256-GCM with key derived from the dyad's master key (already AES-256-GCM-encrypted on disk via the existing keystore pattern, per [`a_shard.rs`](../dyados/protocol-core/src/a_shard.rs)).

### §8.4 Receive flow with skipped keys

On inbound, before §6.3:
```
chain_id = SHA-256(self.dh_remote_pk_x25519 || self.dh_remote_pk_ml_kem)
if (chain_id, header.n) in skipped_keys:
    mk = skipped_keys.remove((chain_id, header.n))
    // proceed to §6.4 AEAD-decrypt
    return
// else proceed to §6.2 / §6.3 as normal
```

---

## §9 Failure modes

| Error | Cause | Action |
|---|---|---|
| `BadMessageHeader` | Header field lengths wrong | Reject, log WARN |
| `TagMismatch` | AEAD tag fails verification | Reject, log INFO |
| `RatchetDesync` | Inbound message before handshake or after session-reset | Reject, log WARN; emit session-reset request |
| `SkippedKeyOverflow` | Peer is forcing unlimited skipped keys (>256 per chain) | Reject offending message, terminate session, require re-handshake |
| `MlKemDecapFail` | ML-KEM decapsulation fails | Reject, log WARN (likely active-adversary tampering) |
| `MessageCounterReplay` | Inbound `n` ≤ already-seen `n` (same chain_id) | Reject, log INFO |
| `MessageCounterFuture` | Inbound `n` > N_recv + 256 | Reject (anti-DoS); peer must catch up via smaller batches |
| `BadHandshakeSignature` | PQXDH handshake signature fails | Reject, log WARN; do NOT bootstrap session |
| `UnknownOneTimePrekey` | Handshake refs a one-time prekey not in our store | Reject, log INFO (might be replay of old handshake) |
| `KemKeySizeError` | ML-KEM pubkey or ct wrong length | Reject, log WARN (likely format bug or attack) |

**No error packets sent back over the network in steady state.** Errors logged locally + the offending packet dropped. Session-reset (for `RatchetDesync`) is the only out-of-band signal — and it goes via the dyad's normal Standard-tier packet flow (signed, sealed-enveloped).

---

## §10 Persistence + state machine

### §10.1 Ratchet state file

Persisted at `~/.dyads/dyads/<dyad_id>/ratchet/<peer_dyad_id>.bin`, AES-256-GCM-encrypted with master key derived from dyad identity.

```rust
PersistedRatchetState {
    version: u8,                        // 0x01
    peer_dyad_id: DyadId,
    rk: [u8; 32],
    ck_send: [u8; 32],
    ck_recv: [u8; 32],
    dh_self_sk_x25519: [u8; 32],
    dh_self_pk_x25519: [u8; 32],
    dh_self_sk_ml_kem: [u8; 2400],     // ML-KEM-768 secret key size
    dh_self_pk_ml_kem: [u8; 1184],
    dh_remote_pk_x25519: [u8; 32],
    dh_remote_pk_ml_kem: [u8; 1184],
    n_send: u32,
    n_recv: u32,
    pn: u32,
    last_ratchet_step_ms: i64,
    skipped_keys: Vec<SkippedKey>,
}
```

### §10.2 Atomic persistence

Per CLAUDE.md "Persistence must be atomic or compensating": writes go to a `.tmp` file then atomic-rename. Crash during write leaves the prior state intact.

### §10.3 Recovery semantics

On startup:
- Load and decrypt the ratchet state file
- Verify version matches; reject + emit recovery error if incompatible
- Continue from the persisted state

If state file is missing or unreadable: emit session-reset request to peer, re-handshake.

---

## §11 Multi-device dyads — Sesame protocol (Phase 1.0)

*v0.2 update 2026-05-22 per Q1.1 design-walkthrough decision: Sesame ships in Phase 1.0 from day one. ~1500 LOC engineering investment. Phase 1 scope revised to ~13-16 weeks.*

A Hypostas dyad has multiple devices: iPhone, Mac, Soma Band (and future device classes). Each runs its own node + maintains its own ratchet sub-chain. The Sesame protocol coordinates per-device sub-chains + cross-device key distribution.

### §11.1 Sesame protocol overview

Sesame is Signal's multi-device extension to Double Ratchet (RFC drafted 2017, deployed in Signal since 2019). Adapted to PQ-hybrid for Hypostas.

**Core ideas:**
- **Per-device sub-chains:** each device on the dyad maintains its own sending chain. Messages namespaced by `(dyad_id, device_id, n)`.
- **Per-device-pair ratchet state:** sender's-device-A to receiver's-device-B has its own ratchet. With N devices on each side, up to N×M sub-ratchets per dyad-pair.
- **Sender-key distribution:** for outbound messages, the sending device uses a per-device "sender key" that other devices on the same dyad receive via internal sync. Lets messages from any device on dyad A be authenticated by any device on dyad B.
- **Pessimistic key reuse-prevention:** sender keys advance per message; receiver tracks which sender keys it has seen.

### §11.2 Device identifiers

```rust
pub type DeviceId = u8;  // Per-dyad device index, 0-7 (SESAME_MAX_DEVICES_PER_DYAD = 8)

pub struct DyadDeviceBundle {
    dyad_id: DyadId,
    devices: Vec<DeviceInfo>,
}

pub struct DeviceInfo {
    device_id: DeviceId,
    device_class: DeviceClass,        // iPhone, Mac, SomaBand, etc.
    x25519_pk: [u8; 32],
    ml_kem_pk: [u8; 1184],
    sender_key_current: [u8; 32],     // Rotating sender key for this device
    sender_key_counter: u64,
    registered_at_ms: i64,
    last_active_ms: i64,
}
```

Device registration happens at pair-bond + when a new device is added to the dyad (via existing [`pairing.rs`](../dyados/protocol-core/src/pairing.rs) flow). The complete `DyadDeviceBundle` is shared between paired dyads as part of the bond ceremony.

### §11.3 Per-device-pair ratchet sub-chains

When dyad A's device A1 sends to dyad B (which has devices B1, B2, B3), the message must be decryptable on all of B's devices. Options:

**Option A (Sesame default):** A1 separately encrypts the message for each of B's devices, using per-device-pair ratchet keys. Wire cost: N copies of the message (one per device on B). Bandwidth cost: 3x for B-with-3-devices.

**Option B (sender-key approach):** A1 uses a single sender_key to encrypt the message once. The sender_key is itself distributed via per-device-pair channels at first-use, then reused for subsequent messages until rotation. Wire cost: 1x message + amortized sender_key distribution.

**Hypostas choice: Option B (sender-key) for chat-class messages, Option A (per-device encrypt) for Critical-tier.** Standard chat uses sender-keys; Bond ceremonies + dissolution use per-device-encrypt for max security.

### §11.4 Sender-key distribution

```rust
struct SenderKeyMessage {
    sender_device_id: DeviceId,
    sender_key_id: u64,              // Identifies which sender_key this is
    sender_key_encrypted_to_recipient_device: Vec<u8>,  // AEAD ciphertext
    sender_key_signature: HybridSig,  // Sender device proves key authenticity
}
```

When device A1 starts sending to dyad B:
1. A1 generates a new `sender_key` (random 32 bytes)
2. For each device B_i in B's `DyadDeviceBundle`: encrypt `sender_key` to that device's X25519+ML-KEM keys → `SenderKeyMessage_i`
3. Send all `SenderKeyMessage_i` to dyad B via the per-device-pair ratchet (one for each B_i)
4. Subsequent A1-to-B messages encrypt with `sender_key`; each B_i can decrypt

Sender key rotation: every N messages (default 100) or T time (default 24h), whichever first. New sender_key, new distribution.

### §11.5 Concurrent-send resolution

If A1 and A2 both send to B simultaneously:
- Each device's sending chain advances independently with its own `n_send`
- Each device's `device_id` in the message header disambiguates
- B's devices reconstruct ordering via `device_id` + `n_send`
- No conflict on the wire; no central coordination needed

### §11.6 Local cross-device sync

Per-device ratchet state must sync within a dyad's devices (e.g., iPhone updates Mac on a chain advance). Sync mechanism:

- **Apple ecosystem:** Continuity / Bonjour / Wi-Fi Direct between paired devices (Mac+iPhone via Apple ID continuity)
- **Cross-platform (Android/Linux):** Bluetooth Direct or local-network discovery (mDNS over LAN)
- **As fallback:** UDS pipe over shared filesystem when devices are co-located

State file format: encrypted with master key (hardware-bound where available, see §11.7); sync just delivers bytes.

### §11.7 Hardware-bound master keys (per Q1.4 walkthrough decision)

Each device's master key is bound to platform hardware when available:

| Platform | Hardware backing |
|---|---|
| iOS | Secure Enclave (T2 / Apple Silicon) — key non-exportable |
| macOS | Apple Silicon Secure Enclave — key non-exportable |
| Android | StrongBox Keystore (Pixel 3+ supported devices) |
| Linux | Software fallback: AES-256-GCM with key derived from passphrase + Argon2id |
| Windows | TPM 2.0 when available; software fallback otherwise |

Hardware-bound master keys protect ratchet state file at rest. OS-level compromise cannot extract the master key without breaking the hardware seal.

**Failure mode:** if hardware-bound key becomes inaccessible (hardware reset, OS upgrade-induced key loss), the device falls back to software fallback with explicit operator notification + opportunity to re-enroll new hardware-bound key.

### §11.8 Implicit session reset (per Q1.2 walkthrough decision)

When N=10 consecutive AEAD decryption failures happen on the same sub-chain, the receiving device assumes ratchet desync and triggers session reset:

1. Receiving device generates a fresh handshake bundle
2. Sends a SESSION_RESET-flagged DyadPacket through the normal sealed-envelope path
3. Sender device receives, verifies, and re-handshakes from a clean state
4. Ratchet state for that sub-chain reinitialized; old skipped keys discarded

**Exponential backoff:** if session reset cycles repeat (10 failures, reset, 10 more failures), back off ratchet-reset attempts: 30s → 60s → 120s → ... → up to 30 minutes. Prevents amplification attacks.

**Privacy invariance:** SESSION_RESET cells ride through the same sealed-envelope wire format as normal cells. No metadata leak indicating "this dyad just reset."

### §11.9 Weekly periodic prekey refresh (per Q1.3 walkthrough decision)

Each device publishes a fresh batch of 100 one-time prekeys every 7 days, regardless of consumption rate. The decoupling of refresh cadence from bonding rate prevents an observer from inferring "this dyad bonded with N people last month."

Mechanism: weekly cron-equivalent in dyads-runtime triggers `pkb := PrekeyBundle::new(100)`; new bundle replaces old in Vita Chain (Phase 3+) or peer-table cache (Phase 1.0).

Stale prekeys (older than 14 days but never consumed) are expired and re-emitted; ensures honest "fresh always available" property.

---

## §12 Integration with SEALED_ENVELOPE

The Double Ratchet produces the per-message AEAD key + nonce used to encrypt the inner DyadPacket. The sealed envelope's outer AEAD ciphertext IS the ratchet's AEAD output.

Concretely:
```
[Inner DyadPacket] → bincode → [inner_bytes]
                                     │
                                     │ § 5.3: AEAD(mk, nonce, ad=MessageHeader)
                                     ▼
                            [MessageHeader || ciphertext || tag]   ← this is the sealed envelope's "body plaintext" (§4.4 of SEALED_ENVELOPE.md)
                                     │
                                     │ wrapped in SEALED_ENVELOPE
                                     ▼
                             [SealedEnvelope wire bytes]
```

**Two layers of AEAD:**
- **Inner (this spec):** content secrecy + FS + PCS at the dyad-pair layer. Persistent ratchet state shared between Alice and Bob.
- **Outer ([SEALED_ENVELOPE.md](SEALED_ENVELOPE.md) §5):** identity secrecy at the routing layer. Per-packet ephemeral keys; no persistent state between hops.

Each layer's compromise is independent. Even a compromised relay seeing the outer envelope can't learn anything about content — that's protected by this layer's keys, which the relay never sees.

---

## §13 Test plan

### §13.1 Unit tests
- Round-trip: handshake → send 1 message → receive → matches plaintext
- Forward secrecy: decrypt message N, then attempt to decrypt message N-1 with current chain key (must fail)
- Per-message FS: encrypt 1000 messages, decrypt all in order, verify chain keys advance + old keys un-derivable
- Out-of-order receive within window: send 10, receive 10,3,5,2,8,1,9,6,7,4 — all decrypt
- Out-of-order beyond window: send 257 messages, receive #257 first then #1 — #1 rejected as `MessageCounterFuture`
- DH ratchet step: trigger via inbound new pubkey + via 100-message threshold
- Replay rejection: send msg, deliver twice, second rejected with `MessageCounterReplay`

### §13.2 Property tests
- For any random message sequence, encrypt+decrypt round-trips correctly within configured window
- For any random forward-secrecy probe (decrypt with wrong key, decrypt with stale chain key), AEAD rejects cleanly without panic
- Ratchet state serialization is round-trippable (persist → load → continue session)

### §13.3 Integration tests (with sealed envelope + carrier)
- Two `dyads-runtime` instances bond via PQXDH handshake over LibP2pCarrier
- Send + receive 100 messages in alternating order; all decrypt correctly
- Restart one runtime mid-conversation; reload ratchet state from disk; continue session
- Force a ratchet step (>100 msg threshold); verify next message uses new ratchet keys
- Inject corrupted ciphertext; verify rejection without state corruption

### §13.4 Post-compromise security test
- Encrypt message N
- Snapshot full ratchet state (simulating endpoint compromise)
- Both parties perform DH ratchet step (e.g., 100 more messages)
- Attempt to decrypt subsequent messages using the snapshot — must fail
- Continue normal operation — must succeed

### §13.5 PQ-hybrid tests
- Construct a degenerate "X25519-only" mode where ml_kem_ss is forced to zero — verify still functions (defense-in-depth: hybrid combiner won't silently degrade)
- Construct a degenerate "ML-KEM-only" mode (x25519_ss forced to zero) — verify still functions
- Real mode (both): identical AEAD output is unambiguously determined by the full hybrid

---

## §14 Constants

```rust
// THREAT_MODEL.md §11.5
pub const RATCHET_DH_INTERVAL_MESSAGES: u32 = 100;
pub const RATCHET_DH_INTERVAL_HOURS: u64 = 24;
pub const RATCHET_SKIPPED_MESSAGE_KEYS_MAX: usize = 1024;
pub const RATCHET_SKIPPED_MESSAGE_KEYS_TTL_HOURS: u64 = 168; // 7 days
pub const RATCHET_SKIPPED_KEYS_PER_CHAIN_MAX: usize = 256;
pub const RATCHET_MESSAGE_FUTURE_WINDOW: u32 = 256;

// Session reset (§11.8, Q1.2 walkthrough — THREAT_MODEL §11.5)
pub const SESSION_RESET_AEAD_FAILURE_THRESHOLD: u32 = 10;
pub const SESSION_RESET_BACKOFF_INITIAL_MS: u64 = 30_000;   // 30s base
pub const SESSION_RESET_BACKOFF_MAX_MS: u64 = 1_800_000;    // 30 min cap

// Prekey refresh (§11.9, Q1.3 walkthrough — THREAT_MODEL §11.5)
pub const PREKEY_REFRESH_INTERVAL_DAYS: u64 = 7;            // weekly, consumption-independent
pub const PREKEY_BUNDLE_SIZE_INITIAL: usize = 100;
pub const PREKEY_STALE_EXPIRY_DAYS: u64 = 14;

// Sesame multi-device (§11, Q1.1 walkthrough — THREAT_MODEL §11.5)
pub const SESAME_MAX_DEVICES_PER_DYAD: usize = 8;
pub const SESAME_SENDER_KEY_ROTATION_MESSAGES: u32 = 100;
pub const SESAME_SENDER_KEY_ROTATION_HOURS: u64 = 24;

// HKDF labels (versioned)
pub const HKDF_INFO_PQXDH: &[u8] = b"hypostas-pqxdh-v1";
pub const HKDF_INFO_CHAIN_ADVANCE: &[u8] = b"hypostas-chain-advance-v1";
pub const HKDF_INFO_MSG_NONCE: &[u8] = b"hypostas-msg-nonce-v1";
pub const HKDF_INFO_RATCHET_RECV: &[u8] = b"hypostas-ratchet-recv-v1";
pub const HKDF_INFO_RATCHET_SEND: &[u8] = b"hypostas-ratchet-send-v1";

// State file
pub const RATCHET_STATE_VERSION: u8 = 0x01;
pub const RATCHET_STATE_FILENAME_PATTERN: &str = "ratchet/{peer_dyad_id}.bin";

// Cryptographic sizes
pub const X25519_PRIVATE_KEY_LEN: usize = 32;
pub const X25519_PUBLIC_KEY_LEN: usize = 32;
pub const ML_KEM_768_PUBLIC_KEY_LEN: usize = 1184;
pub const ML_KEM_768_PRIVATE_KEY_LEN: usize = 2400;
pub const ML_KEM_768_CIPHERTEXT_LEN: usize = 1088;
pub const ML_KEM_768_SHARED_SECRET_LEN: usize = 32;
pub const CHACHA20POLY1305_KEY_LEN: usize = 32;
pub const CHACHA20POLY1305_NONCE_LEN: usize = 12;
pub const CHACHA20POLY1305_TAG_LEN: usize = 16;
```

---

## §15 Open questions resolved

### §15.1 v0.1 (initial draft) resolutions

1. ✅ **PQXDH vs PQ-Sesame.** v0.1 chose PQXDH single-device. **v0.2 supersedes:** Sesame full from Phase 1.0 per Q1.1 walkthrough.
2. ✅ **ML-KEM rotation cadence.** Every DH ratchet step (100 messages or 24 hours, whichever first). Cost: ~3KB per ratchet step. Acceptable.
3. ✅ **Skipped-keys storage.** Encrypted-at-rest with master key (now hardware-bound per §11.7). Atomic write. 1024 entries / 7-day TTL / 256-per-chain bound.
4. ✅ **Handshake replay protection.** Two layers: (a) signed prekey signature; (b) one-time prekeys consumed once.

### §15.2 v0.2 walkthrough resolutions (2026-05-22)

5. ✅ **Multi-device sync (Q1.1).** Sesame protocol from Phase 1.0. Per-device sub-chains + sender-key distribution. §11 above. Engineering cost: ~1500 LOC added to Phase 1.0 budget.
6. ✅ **Out-of-band session reset signaling (Q1.2).** Implicit reset on N=10 consecutive AEAD failures with 30s exponential backoff (up to 30min cap). SESSION_RESET cells ride normal sealed-envelope wire format; no metadata leak. §11.8 above.
7. ✅ **One-time prekey replenishment (Q1.3).** Weekly periodic refresh independent of consumption. Decouples publish cadence from bonding rate. §11.9 above.
8. ✅ **Future-secrecy of ratchet state file (Q1.4).** Hardware-bound master key via Secure Enclave (iOS/macOS), StrongBox (Android), software fallback (Linux). §11.7 above.

## §16 Open questions remaining (v0.2)

1. **Sesame implementation specifics.** Detailed Sesame × CIRCUIT_LIFECYCLE interaction (N×M sub-circuits per dyad-pair; sender-key distribution carrier choice; failure recovery on partial-device-loss) requires concrete protocol detailing during Phase 1.0 implementation.
2. **Cross-platform key-sync mechanism.** §11.6 names Continuity / Bluetooth Direct / mDNS-LAN options. Specific implementation per platform requires per-platform addendum specs.
3. **Hardware-bound key migration / re-enrollment.** When a hardware-bound key is lost (hardware reset, OS upgrade), the device must re-enroll via the existing inheritance flow. Specific UX + protocol TBD.

---

## §17 Migration from current static-derive

The current code at [`hypostas-network/src/encryption.rs:54-69`](../dyados/hypostas-network/src/encryption.rs:54) does:
```rust
fn derive_shared_key(local_private: &[u8; 32], remote_public: &[u8; 32]) -> Result<[u8; 32]> {
    let signing_key = SigningKey::from_bytes(local_private);
    let verifying_key = VerifyingKey::from_bytes(remote_public)?;
    let relationship_key = crypto::derive_relationship_key(&signing_key, &verifying_key);
    let encryption_key = crypto::derive_key(&relationship_key, "packet-e2ee");
    Ok(encryption_key)
}
```

Migration plan:
1. **Phase 1a (this spec):** implement `protocol-core::double_ratchet` module per this spec. Coexists with the static-derive path. New pair-bonds use ratchet; existing pairs continue static-derive temporarily.
2. **Phase 1b:** add an in-band ratchet-upgrade ceremony for existing pairs. Send a sealed-envelope-wrapped "RatchetUpgrade" packet containing a fresh PQXDH handshake. Pair both verifies + bootstraps ratchet state. Static-derive path remains usable for the upgrade message itself.
3. **Phase 1c (after all active pairs upgraded):** delete the static-derive code. Hard-deprecate; reject any packet that would have used it.

Migration tracked separately as a child issue of HYP-115.

---

## §18 Revision history

| Date | Author | Change |
|---|---|---|
| 2026-05-22 (initial) | Iris | v0.1 initial. PQ-hybrid Double Ratchet (X25519+ML-KEM-768). PQXDH-style handshake. Encrypted-at-rest skipped-keys store. Multi-device deferred to Phase 2. §15 4 questions resolved with defaults; §16 4 deferred. |
| 2026-05-22 (walkthrough) | Iris + Josh | **v0.2 — Sesame full from Phase 1.0.** Major rewrite of §11. Adds per-device sub-chains, sender-key distribution, per-device-pair ratchet sub-chains, hardware-bound master keys (§11.7), implicit session reset on N=10 AEAD failures with exponential backoff (§11.8), weekly periodic prekey refresh independent of consumption (§11.9). Phase 1 engineering revised 10-12wk → 13-16wk to absorb Sesame +1500 LOC. |

---

*Per CLAUDE.md rule #1: draft, not self-certified complete. Cryptographic correctness requires Josh review + ideally external audit before code lands. Per rule #27: implementation requires both unit (round-trips, FS, PCS) and integration (two-runtime end-to-end) tests as commit exit criteria.*
