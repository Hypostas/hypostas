# SEALED_ENVELOPE.md — Hypostas Outer Envelope (Circuit-Based)

**Status:** Draft v0.2 (2026-05-22) — supersedes v0.1 per-envelope-KEM design
**Owner:** `protocol-core`, `vita-carriers`, `hypostas-network`
**Authors:** Josh + Iris
**Anchored to:** [THREAT_MODEL.md](THREAT_MODEL.md) §5.2, §5.3, §5.5, §6.1, §11.1, §11.3, §11.4
**Companion specs:** [CIRCUIT_LIFECYCLE.md](CIRCUIT_LIFECYCLE.md) (circuit construction + per-relay session keys), [DOUBLE_RATCHET.md](DOUBLE_RATCHET.md) (inner content keys), [COVER_TRAFFIC.md](COVER_TRAFFIC.md) (scheduler), [POST_QUANTUM.md](POST_QUANTUM.md)
**Linear:** [HYP-116](https://linear.app/hypostas/issue/HYP-116) (parent [HYP-115](https://linear.app/hypostas/issue/HYP-115))

---

## §0 What changed from v0.1

v0.1 used per-envelope PQ kex: each envelope carried a fixed 8.7 KB stack of ML-KEM ciphertexts (one per potential hop). Smallest cell was 11.3 KB. That was wrong — it ignored circuit-based amortization (Tor's foundational insight).

**v0.2 design:** circuits. PQ-hybrid kex happens **once per circuit** (~10 min lifetime), establishing per-relay symmetric session keys via telescoping handshake. Per-envelope crypto is **only symmetric** — ChaCha20-Poly1305 keyed by the circuit's session keys. Cost moves from per-envelope to per-circuit, amortized across thousands of cells.

**Size reduction:**
- Smallest cell: 11.3 KB → 512 B (22× smaller)
- Medium cell: 14.9 KB → 4 KB
- Large cell: 27.2 KB → 16 KB
- XLarge cell: 76.3 KB → 64 KB

PQ security is identical — the circuit-construction handshake IS hybrid X25519+ML-KEM-768, just amortized. Per-envelope cost = pure symmetric crypto + ~5 bytes routing header.

The Sphinx onion structure is **preserved** for header routing. Per-hop keys come from circuit state instead of per-envelope kex.

---

## §1 Purpose

The Sealed Envelope is the wire format every carrier sees in the Hypostas substrate — Tor-style **cell** format with PQ-hardened circuits. Single-hop sealed-sender (Phase 1, N=1) and multi-hop relay routing (Phase 2+, N≥3) share one canonical cell format. Cells ride over pre-established circuits with per-relay symmetric session keys.

This spec defines what bytes go on the wire. Circuit construction (how the symmetric session keys are established + refreshed + torn down) is in [CIRCUIT_LIFECYCLE.md](CIRCUIT_LIFECYCLE.md). Inner content encryption (dyad-pair Double Ratchet) is in [DOUBLE_RATCHET.md](DOUBLE_RATCHET.md). The carrier that transports cells is in [VITA_CARRIERS.md](../vita/components/VITA_CARRIERS.md).

### §1.1 Threat-model coverage

| Property | Defense provided by this spec | Where else |
|---|---|---|
| §5.1 Content secrecy | Outer AEAD over inner ciphertext | Inner [DOUBLE_RATCHET.md](DOUBLE_RATCHET.md) for dyad-pair keys + FS |
| §5.2 Identity secrecy | No `DyadId`, trust tier, conversation ref on the wire — only opaque circuit_id | — |
| §5.3 Relationship secrecy | Multi-hop circuit (Phase 2+) — no single relay knows both endpoints. Phase 1 N=1 = partial via [COVER_TRAFFIC.md](COVER_TRAFFIC.md) + multi-carrier fanout | Vita Chain blinded intros (Phase 3) |
| §5.4 Timing secrecy | — | [COVER_TRAFFIC.md](COVER_TRAFFIC.md) constant-rate cover |
| §5.5 Volume secrecy | Fixed-size cells (4 buckets: 512B/4KB/16KB/64KB) | — |
| §5.6 Future secrecy | Per-circuit ephemeral kex provides FS at routing layer; PQ-hybrid kex (X25519+ML-KEM-768) at circuit-build | Inner [DOUBLE_RATCHET.md](DOUBLE_RATCHET.md) for content-layer FS + PCS |

### §1.2 Adversary coverage

| Adversary | Defended? | How |
|---|---|---|
| §4.1 Passive observer | ✅ full | AEAD + sealed identity + fixed-size cells |
| §4.2 Active network | ✅ full | + bounded decoders + replay tags + Poly1305 tag |
| §4.3 Global passive | Partial Phase 1, full Phase 2 | + multi-hop circuits + cover scale |
| §4.4 Compromised relay | ✅ structural | Per-circuit session keys; each relay learns only its incoming + outgoing circuit binding, never the full path |

---

## §2 Format at a glance

```
Cell wire bytes (fixed 512B / 4KB / 16KB / 64KB total):
  ┌─────────────────────────────────────────┐
  │ version (1 byte) = 0x02                 │
  ├─────────────────────────────────────────┤
  │ circuit_id (4 bytes, per-link opaque)   │
  ├─────────────────────────────────────────┤
  │ command (1 byte)                        │
  │   0x01 = data                           │
  │   0x02 = circuit_destroy                │
  │   0x03 = circuit_handshake              │
  │   0x04 = relay_extend                   │
  │   0x05 = relay_extended                 │
  │   0x06 = relay_data                     │
  ├─────────────────────────────────────────┤
  │ nonce (12 bytes)                        │
  ├─────────────────────────────────────────┤
  │ payload (size_class - 34 bytes,         │
  │          AEAD-encrypted with circuit's  │
  │          incoming session key)          │
  ├─────────────────────────────────────────┤
  │ tag (Poly1305, 16 bytes)                │
  └─────────────────────────────────────────┘

Fixed cell overhead = 1 + 4 + 1 + 12 + 16 = 34 bytes
Payload capacity per cell:
  S (512 total):    478 bytes
  M (4096 total):   4062 bytes
  L (16384 total):  16350 bytes
  XL (65536 total): 65502 bytes
```

A carrier observing the wire sees only one of these four exact byte lengths and an opaque circuit_id. Size class is implicit by total byte count — never serialized into the cell.

---

## §3 Cryptographic primitives

The wire format uses **only symmetric crypto**. PQ-hybrid kex happens at circuit construction (see [CIRCUIT_LIFECYCLE.md](CIRCUIT_LIFECYCLE.md)).

| Primitive | Algorithm | Notes |
|---|---|---|
| Symmetric AEAD | ChaCha20-Poly1305 | RFC 8439; per-cell encryption + auth |
| KDF | HKDF-SHA256 | Per-cell nonce derivation if needed |
| Hash | SHA-256 | Replay tags, circuit fingerprints |

Per-circuit session keys (incoming + outgoing per direction per relay) come from the circuit-construction handshake. The wire never carries these keys; they live in each relay's circuit table.

---

## §4 Wire format (exact bytes)

All multi-byte integers big-endian.

### §4.1 Cell header (18 bytes)

| Offset | Length | Field | Type | Description |
|---|---|---|---|---|
| 0 | 1 | `version` | u8 | `0x02` = v0.2 (this spec). v0.1 (per-envelope KEM) deprecated |
| 1 | 4 | `circuit_id` | u32 | Per-link opaque ID. Receiving relay uses `(incoming_link, circuit_id)` to look up its circuit-table entry |
| 5 | 1 | `command` | u8 | Cell command — see §4.2 |
| 6 | 12 | `nonce` | bytes | Per-cell AEAD nonce. Combined with circuit key |

### §4.2 Cell commands

| Code | Name | Meaning | Payload structure |
|---|---|---|---|
| `0x01` | `data` | Carry encrypted inner payload from sender to terminal hop | Onion-layered for multi-hop; single-layer for N=1 |
| `0x02` | `destroy` | Tear down circuit | Reason code (u8) + padding |
| `0x03` | `handshake` | Circuit-construction message (see [CIRCUIT_LIFECYCLE.md](CIRCUIT_LIFECYCLE.md)) | Handshake-specific structure |
| `0x04` | `extend` | Telescoping extend request (relay→next-relay during build) | Next-hop info + KEM material |
| `0x05` | `extended` | Telescoping extend response | KEM response material |
| `0x06` | `relay_data` | Inner relay command (after onion-strip) | Sub-command + payload |

For Phase 1 with N=1, only `0x01` (data), `0x02` (destroy), `0x03` (handshake) are used. Multi-hop variants `0x04`, `0x05`, `0x06` activate in Phase 2.

### §4.3 Payload encryption

For `command = 0x01` (data):
- `payload_plaintext = onion_layered_data(inner_dyad_packet_bytes, hops)` (see §5)
- `nonce_full = SHA-256(circuit_id || nonce || hop_position)[..12]` — binds nonce to circuit + hop, prevents cross-circuit confusion
- `payload_ciphertext, tag = ChaCha20Poly1305::encrypt(key=session_key_in, nonce=nonce_full, ad=cell_header, plaintext=payload_plaintext)`

Each relay decrypts one layer with its `session_key_in` (incoming direction's key, established at circuit build). For multi-hop, the relay then re-encrypts with `session_key_out` (outgoing direction's key for the next hop) before forwarding.

### §4.4 Single-hop simplification (Phase 1, N=1)

When N=1 (sender→terminal recipient directly via libp2p or other carrier):
- No relays in between
- One circuit segment: sender ↔ recipient
- Sender encrypts payload with `session_key_in_recipient` (Alice→Bob direction)
- Recipient receives, decrypts, processes
- No re-encryption, no onion-stripping

Same wire format. Same cell. Just N=1 in the circuit structure.

---

## §5 Construction (sender)

### §5.1 Pre-condition: circuit exists

The sender has already built a circuit per [CIRCUIT_LIFECYCLE.md](CIRCUIT_LIFECYCLE.md). The circuit comprises:
- A sequence of hops: `[R_1, R_2, ..., R_{N-1}, Bob]` (Phase 1: just `[Bob]`)
- Per-hop incoming + outgoing session keys (Alice's view: she knows the FIRST-hop's key only; subsequent hops are reached via telescoping)
- A per-hop **layer-key set** — these are the symmetric keys Alice uses to encrypt each layer of the onion:
  - `layer_key_i` for `i ∈ {1..N}` — derived from circuit state during construction (see CIRCUIT_LIFECYCLE.md §6)
- An `incoming_circuit_id` for the wire address (the ID R_1 uses to look up this circuit in its table)

### §5.2 Step-by-step (Phase 1, N=1, the common case)

For a single-hop conversation Alice → Bob:

**1. Get circuit state.** Alice has a circuit to Bob (via her routing carriers). She holds:
- `circuit_id_out_to_bob: u32` — the ID Bob expects on incoming cells from Alice
- `session_key_send_to_bob: [u8; 32]` — symmetric key for cells Alice → Bob

**2. Serialize inner.** `inner_bytes = bincode::serialize(&dyad_packet_with_double_ratchet_aead)?`
- This INCLUDES the [DOUBLE_RATCHET.md](DOUBLE_RATCHET.md) AEAD output (MessageHeader || ciphertext || tag)
- So inner_bytes is already content-encrypted by the dyad-pair layer

**3. Pad to cell payload size.**
```rust
let size_class = select_size_class(4 + inner_bytes.len());
let payload_capacity = size_class.payload_capacity();  // 478, 4062, 16350, 65502
let mut payload_plaintext = Vec::with_capacity(payload_capacity);
payload_plaintext.extend_from_slice(&(inner_bytes.len() as u32).to_be_bytes());
payload_plaintext.extend_from_slice(&inner_bytes);
payload_plaintext.resize(payload_capacity, 0); // zero padding
```

**4. Generate nonce.**
```rust
let mut nonce = [0u8; 12];
rand::thread_rng().fill(&mut nonce);
```

**5. Build cell header.**
```rust
let cell_header = CellHeader {
    version: 0x02,
    circuit_id: circuit_id_out_to_bob,
    command: 0x01,  // data
    nonce,
};
```

**6. AEAD-encrypt payload.**
```rust
let nonce_full = sha256(&[
    &circuit_id_out_to_bob.to_be_bytes()[..],
    &nonce[..],
    &[0u8],  // hop_position = 0 (terminal in N=1)
].concat())[..12].to_vec();

let (ciphertext, tag) = chacha20poly1305::encrypt(
    key: &session_key_send_to_bob,
    nonce: &nonce_full,
    ad: &cell_header.to_bytes(),
    plaintext: &payload_plaintext,
)?;
```

**7. Assemble wire bytes.**
```rust
let wire = [
    &[cell_header.version],
    &cell_header.circuit_id.to_be_bytes()[..],
    &[cell_header.command],
    &cell_header.nonce[..],
    &ciphertext[..],
    &tag[..],
].concat();
debug_assert_eq!(wire.len(), size_class.total_bytes());
```

**8. Hand off to carrier.**
```rust
carrier.send(dest: bob_dyad_id, packet_bytes: &wire).await?;
```

### §5.3 Multi-hop construction (Phase 2+, N≥2)

For a multi-hop path Alice → R_1 → R_2 → Bob:

**1. Get circuit state.** Alice holds per-hop `layer_key_i` for each of the N hops (derived from telescoping handshake — see CIRCUIT_LIFECYCLE.md).

**2. Build innermost layer (terminal hop, Bob).**
```rust
let inner_payload = serialize(inner_dyad_packet);
let inner_plaintext = [
    &(inner_payload.len() as u32).to_be_bytes()[..],
    &inner_payload[..],
    &zeros(payload_capacity - 4 - inner_payload.len())[..],
].concat();
let (l_N_ciphertext, l_N_tag) = aead_encrypt(layer_key_N, nonce_N_full, l_N_plaintext);
```

**3. Build each routing layer from innermost out.**
For `i ∈ {N-1, N-2, ..., 1}`:
```rust
let l_i_plaintext = RelayHeader {
    next_circuit_id: circuit_id_at_hop_i_plus_1,
    next_hop_position: i+1,
    replay_tag: sha256(circuit_id_at_hop_i || hop_pos_i)[..16],
}.to_bytes() ++ l_{i+1}_ciphertext ++ l_{i+1}_tag;
// Pad to payload_capacity
let (l_i_ciphertext, l_i_tag) = aead_encrypt(layer_key_i, nonce_i_full, l_i_plaintext);
```

**4. Final wire cell.**
```rust
let wire = CellHeader { version, circuit_id: circuit_id_to_R1, command: 0x01, nonce: nonce_1 }
        ++ l_1_ciphertext ++ l_1_tag;
```

The Sphinx-style onion structure is preserved; the kex is amortized into circuit construction.

### §5.4 Size-class selection

```rust
fn select_size_class(needed_payload_bytes: usize) -> SizeClass {
    if needed_payload_bytes <= 478 { SizeClass::S }
    else if needed_payload_bytes <= 4062 { SizeClass::M }
    else if needed_payload_bytes <= 16350 { SizeClass::L }
    else if needed_payload_bytes <= 65502 { SizeClass::XL }
    else { return Err(EnvelopeError::PayloadTooLarge) }
}
```

Payloads exceeding XL require higher-layer chunking ([`chunking.rs`](../dyados/vita-carriers/src/chunking.rs)).

---

## §6 Processing (recipient/relay)

Every node receiving a cell follows this algorithm:

### §6.1 Step-by-step

**1. Length sanity.** Reject if `wire.len() not in {512, 4096, 16384, 65536}`. → `BadSizeClass`

**2. Parse cell header.** Extract `version`, `circuit_id`, `command`, `nonce`. Reject if `version != 0x02`. → `BadVersion`

**3. Circuit lookup.** Look up `(incoming_link, circuit_id)` in this node's circuit table → get `(direction, session_key_in, next_hop_info)`. If not found → `UnknownCircuit`, drop.

**4. Branch on command.**

**4a. `command = 0x01` (data):**
- Compute `nonce_full = sha256(circuit_id || nonce || hop_position)[..12]`
- Decrypt: `payload_plaintext = chacha20poly1305::decrypt(session_key_in, nonce_full, ad: cell_header, ciphertext, tag)?` → reject on auth failure → `BadTag`
- Check replay: `replay_tag` derived from `(circuit_id, hop_position, this_node_pubkey)[..16]`; check bloom filter → reject if seen → `Replay`
- Add to bloom filter

**4b. Terminal hop** (`next_hop_info == None`):
- Parse `inner_len` from first 4 bytes of decrypted payload; reject if too large → `BadInnerLen`
- Extract `inner_bytes = payload_plaintext[4..4+inner_len]`
- Verify padding bytes after inner_bytes are zero → `NonZeroPadding`
- Deserialize bounded: `let dyad_packet = bincode::decode_with_limit::<MAX_INNER_LEN>(&inner_bytes)?` → `InnerDecodeFail`
- Pass `dyad_packet` to runtime's inbound handler (which will then unwrap the inner DOUBLE_RATCHET layer)

**4c. Relay hop** (`next_hop_info != None`):
- Parse the relay header from `payload_plaintext[0..relay_header_size]` to get `(next_circuit_id, next_hop_position, replay_tag)`
- The remainder `payload_plaintext[relay_header_size..]` is the next layer's ciphertext+tag, BUT — that ciphertext was constructed by the sender with the NEXT layer's key. We don't decrypt it; we just forward it.
- Build new cell:
  ```rust
  let new_nonce = random();
  let new_cell_header = CellHeader {
      version: 0x02,
      circuit_id: next_circuit_id,
      command: 0x01,
      nonce: new_nonce,
  };
  // Re-encrypt the forwarded payload with the NEXT hop's session key (this relay's outgoing)
  let new_nonce_full = sha256(next_circuit_id || new_nonce || next_hop_position)[..12];
  let (new_ciphertext, new_tag) = aead_encrypt(
      key: next_hop_info.session_key_out,
      nonce: new_nonce_full,
      ad: new_cell_header.to_bytes(),
      plaintext: forwarded_payload_with_remaining_layers,
  );
  let new_wire = new_cell_header.to_bytes() ++ new_ciphertext ++ new_tag;
  ```
- Forward: `carrier.send(dest: next_hop_info.next_relay_dyad_id, packet_bytes: new_wire)`

**4d. `command = 0x02` (destroy):**
- Decrypt payload to verify circuit ownership
- Remove circuit from this node's circuit table
- If this is a relay (not terminal): forward destroy to the next hop in the circuit using the same pattern as data forwarding

**4e. `command = 0x03/0x04/0x05` (handshake / extend / extended):**
- See [CIRCUIT_LIFECYCLE.md](CIRCUIT_LIFECYCLE.md) §5 for handshake processing

### §6.2 Why relays can't see the full path

Each relay maintains a circuit table:

```rust
struct CircuitEntry {
    incoming_link: CarrierName,
    circuit_id_in: u32,
    direction: CircuitDirection,    // Forward or Reverse
    session_key_in: [u8; 32],       // Decrypt cells from previous hop
    session_key_out: [u8; 32],      // Re-encrypt cells for next hop
    next_relay_dyad_id: Option<DyadId>,  // None for terminal
    next_circuit_id: Option<u32>,
    established_at: i64,
    last_used: i64,
}
```

The relay's table contains ONLY two adjacencies: the previous hop and the next hop. The relay does NOT know:
- The origin of the circuit (who Alice is)
- The destination of the circuit (who Bob is)
- The full path (who the other relays are)
- The cells' actual content (encrypted with keys the relay doesn't have)

Even compromising one relay reveals only its two adjacencies. This is the Sphinx anonymity guarantee, preserved with circuit amortization.

---

## §7 Size classes + padding

| Class | Total wire | Payload capacity | Use case |
|---|---|---|---|
| `S` | 512 B | 478 B | Heartbeat, cover, short chat |
| `M` | 4096 B | 4062 B | Standard chat, signal packets, biosensor sample |
| `L` | 16384 B | 16350 B | Memory writes, biosensor batches, photo thumbs |
| `XL` | 65536 B | 65502 B | Large attachments, large memory blobs |

The 34-byte fixed overhead is now genuinely small relative to body. Smallest cell at 512 B = 93% payload, 7% overhead. (Compare v0.1: 11.3KB total = 4.5% payload, 95.5% overhead.)

Padding is always zero bytes after the actual content. Receivers reject non-zero padding to defeat steganographic abuse of the channel.

---

## §8 Hop budget + replay protection

### §8.1 Implicit hop budget via circuit structure

In circuit-based routing, the hop count is bound at circuit construction (see CIRCUIT_LIFECYCLE.md §5). The wire format doesn't need an explicit hop budget — the circuit table at each relay tells it "this is your role" (terminal or relay).

If a relay receives a cell on a circuit it's terminal for: terminal path.
If a relay receives a cell on a circuit it's intermediate for: forward path.
If a relay receives a cell on an unknown circuit_id: drop.

No hop-budget tampering possible because the budget IS the circuit table structure, established cryptographically at build.

### §8.2 Replay protection

Each cell carries a `replay_tag` in the **decrypted payload's relay header** (for relay hops) or implicit via `(circuit_id, nonce)` uniqueness (for terminal hops).

```
replay_tag = SHA-256(circuit_id || nonce || hop_position)[..16]
```

Each relay maintains a bloom filter of seen replay_tags. TTL aligned with circuit lifetime (~10 min default, capped at 24h per [THREAT_MODEL §11.4](THREAT_MODEL.md)).

**Bloom filter sizing:** 65536 bits with 3 hash functions. At 1 packet/sec per circuit, ~600 packets per 10-min circuit lifetime per circuit. False positive rate negligible.

**Why this works for circuits:** within a circuit's lifetime (~10 min), unique nonces ensure no collisions. After circuit teardown, the session keys are gone (forward secrecy at routing layer) — replay is harmless.

### §8.3 Resistance to active attacks

| Attack | Defense |
|---|---|
| Replay cell to different relay | replay_tag binds to specific relay (`hop_position` in derivation); other relays compute different expected tag → drop |
| Modify cell bytes | Poly1305 tag fails → drop |
| Forge cells without circuit knowledge | No session key → AEAD fails → drop |
| Replay across circuit-rebuild | New circuit has new keys; old replay_tag's session key is gone |

---

## §9 Failure modes

Every rejected cell is dropped silently (no error response to network). Local structured logs record reasons.

| Error | Cause | Action |
|---|---|---|
| `BadSizeClass` | Wire length not in {512, 4096, 16384, 65536} | Drop, log WARN |
| `BadVersion` | `version != 0x02` | Drop, log WARN |
| `UnknownCircuit` | `(incoming_link, circuit_id)` not in circuit table | Drop, log INFO (likely stale circuit, replay attempt, or scan) |
| `BadTag` | Poly1305 AEAD mismatch | Drop, log INFO (likely tampering, wrong key, or different circuit attempt) |
| `Replay` | Bloom filter hit on `replay_tag` | Drop, log INFO |
| `BadInnerLen` | Decrypted `inner_len > payload_capacity - 4` | Drop, log WARN |
| `NonZeroPadding` | Decrypted padding non-zero | Drop, log WARN (covert channel attempt) |
| `InnerDecodeFail` | Bincode bounded decode fails or exceeds limit | Drop, log WARN |
| `RelayForwardFailed` | Cell decrypted + needs forward, but next-hop carrier unavailable | Drop, log INFO; consider notifying circuit owner for re-route |
| `UnknownCommand` | `command` not in valid set | Drop, log WARN |

---

## §10 Bounded decoders

Per CLAUDE.md systemic-class issue ([HYP-14/21/47/49/72/73/75/98/100](https://linear.app/hypostas/issue/HYP-49)): every wire decoder is size-bounded.

### §10.1 Cell-level
- Reject before parsing if `wire.len() != one of {512, 4096, 16384, 65536}`
- All offsets fixed; no length-prefixed allocations

### §10.2 Inner DyadPacket decoder
- `MAX_INNER_LEN = payload_capacity - 4` (478, 4062, 16350, 65502 per size class)
- bincode config with explicit limit:
  ```rust
  let config = bincode::config::standard().with_limit::<MAX_INNER_LEN>();
  let packet: DyadPacket<P> = bincode::decode_from_slice_with_config(&inner_bytes, config)?.0;
  ```

### §10.3 Circuit table
- Each node's circuit table bounded at `MAX_CIRCUITS_PER_NODE = 256` (one node can be a member of at most 256 concurrent circuits)
- LRU eviction with refresh-on-use
- Memory per circuit entry ~200 bytes → ~50KB per node total

### §10.4 Bloom filter
- 65536 bits × 2 buckets (active + draining) = 16KB per node

---

## §11 Carrier-trait integration

The sealed cell rides over the existing [`Carrier`](../dyados/vita-carriers/src/carrier.rs) trait. No changes to the trait surface.

### §11.1 Carrier MTU constraints

| Carrier | MTU | S (512B) | M (4KB) | L (16KB) | XL (64KB) |
|---|---|---|---|---|---|
| LibP2pCarrier | 16 MiB | ✅ direct | ✅ direct | ✅ direct | ✅ direct |
| DhtMailboxCarrier | 64 KB | ✅ direct | ✅ direct | ✅ direct | ✅ direct |
| ThreadCarrier | 1280 B | ✅ direct | ⚠️ chunked | ⚠️ chunked | ⚠️ chunked |
| LoRaCarrier | 250 B | ⚠️ chunked | ⚠️ chunked | ⚠️ chunked | ⚠️ chunked |
| SteganographicCarrier | ~100 KB | ✅ direct | ✅ direct | ✅ direct | ✅ direct |
| VoiceCallCarrier | variable | ⚠️ chunked | ⚠️ chunked | ⚠️ chunked | ⚠️ chunked |

**Much better than v0.1.** S cells now fit through ThreadCarrier directly (1280 byte MTU vs 512 byte cell).

Chunking handled at carrier layer per [`chunking.rs`](../dyados/vita-carriers/src/chunking.rs). Chunks are NOT sealed cells — they're transport-layer fragments of an opaque byte stream. Reassembly precedes cell processing.

### §11.2 PrivacyClass update

[`PrivacyClass`](../dyados/vita-carriers/src/properties.rs:156) with Phase 1:
- Default for every carrier: `PayloadEncryptedPlusOnion` (single-hop = degenerate onion)
- `PayloadEncryptedToRecipient` deprecated, removed
- `PayloadInClear` remains forbidden

### §11.3 Sealed cell is mandatory

Phase 1 commits: **every** DyadPacket on the wire MUST be wrapped in a sealed cell. The single-hop sealed-sender pattern is the floor — no carrier may transport unsealed DyadPacket bytes. This closes the §5.2 identity-secrecy gap at [`packet.rs:148-165`](../dyados/protocol-core/src/packet.rs:148).

The Phase 0 HTTP wire format is sealed by [HYP-109](https://linear.app/hypostas/issue/HYP-109) migration to native DyadPacket over UDS. After HYP-109 PR F, the only "unsealed" packet format is the UDS local IPC surface — local-only, not network-observable, doesn't need sealing.

---

## §12 Forward compatibility

The wire format is identical for N=1 (Phase 1) and N≥3 (Phase 2+). The differences are entirely in:
- How many relay hops the circuit has at construction time
- Each relay's circuit-table entry (single-hop circuit has no `next_hop_info`; multi-hop does)

A Phase 1 N=1 cell and a Phase 2 N=3 cell **look identical to any observer** — same byte length, same wire format. The hop count is bound to circuit state (private to relays) not envelope (public on wire).

### §12.1 Version evolution

- `0x00` — reserved, never used
- `0x01` — v0.1 per-envelope KEM (deprecated, never deployed)
- `0x02` — this spec (v0.2 circuit-based), Phase 1+2+3+4
- `0x03..0xFF` — reserved for future breaking changes

If a future PQ primitive replaces ML-KEM-768 (e.g., FIPS 206 if standardized), version byte gates and we run dual-version concurrent for migration.

---

## §13 Test plan

Per CLAUDE.md rule #27.

### §13.1 Unit tests
- Round-trip cell construct → parse at each size class
- Single-hop construction + decryption with mock circuit state
- Multi-hop (N=2, N=3) construction + per-hop processing (mock relays)
- Replay-tag determinism (same circuit_id+nonce produces same tag)
- Size-class selection at boundaries (477, 478, 479 → S/S/M)
- AEAD failure modes: wrong key, modified ciphertext, modified AAD

### §13.2 Integration tests (with circuit + carrier)
- LibP2pCarrier single-hop round-trip: Alice→Bob with established circuit
- LoRaCarrier round-trip with chunking: cell split+reassembled, processes correctly
- Multi-hop A→R1→R2→B with three real dyads_runtime instances + pre-built circuits
- Replay rejection across multiple deliveries to same relay
- Circuit teardown (command=0x02) removes circuit table entry

### §13.3 Adversarial tests
- Random-byte injection at every offset → all rejected with correct error
- Modify circuit_id → UnknownCircuit
- Truncate cell by 1 byte → BadSizeClass
- Send cell with valid format but circuit not built → UnknownCircuit
- Replay same cell twice → second rejected as Replay
- Replay across circuit-rebuild → second rejected (new circuit has new keys)

### §13.4 Property tests (proptest)
- For any valid DyadPacket P, established circuit C, `decrypt(C, encrypt(C, P)) == P`
- For any random byte string of correct size, decrypt either succeeds or rejects cleanly (no panic, no UB)
- Multi-hop forwarding preserves payload through all hops

---

## §14 Constants

```rust
// Wire format
pub const CELL_VERSION: u8 = 0x02;
pub const CIRCUIT_ID_LEN: usize = 4;
pub const CELL_COMMAND_LEN: usize = 1;
pub const CELL_NONCE_LEN: usize = 12;
pub const CELL_HEADER_LEN: usize = 1 + 4 + 1 + 12;  // 18 bytes
pub const CELL_TAG_LEN: usize = 16;
pub const CELL_FIXED_OVERHEAD: usize = CELL_HEADER_LEN + CELL_TAG_LEN;  // 34 bytes

// Size classes (total wire)
pub const CELL_TOTAL_S: usize = 512;
pub const CELL_TOTAL_M: usize = 4096;
pub const CELL_TOTAL_L: usize = 16384;
pub const CELL_TOTAL_XL: usize = 65536;

// Payload capacities (derived)
pub const CELL_PAYLOAD_S: usize = CELL_TOTAL_S - CELL_FIXED_OVERHEAD;   // 478
pub const CELL_PAYLOAD_M: usize = CELL_TOTAL_M - CELL_FIXED_OVERHEAD;   // 4062
pub const CELL_PAYLOAD_L: usize = CELL_TOTAL_L - CELL_FIXED_OVERHEAD;   // 16350
pub const CELL_PAYLOAD_XL: usize = CELL_TOTAL_XL - CELL_FIXED_OVERHEAD; // 65502

// Cell commands
pub const CMD_DATA: u8 = 0x01;
pub const CMD_DESTROY: u8 = 0x02;
pub const CMD_HANDSHAKE: u8 = 0x03;
pub const CMD_EXTEND: u8 = 0x04;
pub const CMD_EXTENDED: u8 = 0x05;
pub const CMD_RELAY_DATA: u8 = 0x06;

// Circuit table
pub const MAX_CIRCUITS_PER_NODE: usize = 256;

// Replay protection (THREAT_MODEL §11.4)
pub const REPLAY_BLOOM_BITS: usize = 65536;
pub const REPLAY_BLOOM_HASHES: usize = 3;
pub const REPLAY_TTL_HOURS: u64 = 24;

// HKDF labels (versioned)
pub const HKDF_INFO_CELL_NONCE: &[u8] = b"hypostas-cell-nonce-v2";
pub const HKDF_INFO_REPLAY_TAG: &[u8] = b"hypostas-replay-tag-v2";
```

---

## §15 Resolved questions

1. ✅ **Per-hop kex primitive.** Moved to circuit construction (see [CIRCUIT_LIFECYCLE.md](CIRCUIT_LIFECYCLE.md)). Per-cell is symmetric only.
2. ✅ **Replay protection structure.** SHA-256-derived replay_tags + per-relay bloom filter + circuit-aligned TTL.
3. ✅ **Size class signaling.** Implicit by total byte count.
4. ✅ **Carrier-specific variants.** Single cell format + chunking adapter.
5. ✅ **Next-hop hint encoding.** Implicit via circuit_id + circuit-table lookup. Wire carries only the opaque ID.

## §16 Deferred to v0.3 / future

1. **PQ-Sphinx blinding.** If a PQ-blinded primitive emerges that lets a single ML-KEM ciphertext extend across multiple hops via key blinding, circuit construction could compress. Active research; not deployed. Revisit if Nym or IETF land standards.
2. **Circuit-bundling.** Multiple short-lived sub-conversations within one circuit (e.g., Anima signal + biosensor stream simultaneously). Trade-off: traffic mixing on a single circuit increases anonymity-set but couples failure modes. Defer.
3. **Padding-cell injection by relays.** Relays could inject their own padding cells onto circuits as additional cover. Tradeoff: stronger cover, more bandwidth. Defer to Phase 2 review.

---

## §16.4 Outfox absorption (per Q2.7 walkthrough)

We absorb three patterns from [Outfox: A Postquantum Packet Format for Layered Mixnets](https://arxiv.org/html/2412.19937) (Nym, WPES '25, Oct 2025) at the **wire-format** layer; the corresponding circuit-construction adoptions are spec'd in [CIRCUIT_LIFECYCLE.md §21](CIRCUIT_LIFECYCLE.md).

### §16.4.1 Adopted at the wire layer

- **Constant-length-route principle.** Every cell carries the same payload structure regardless of actual hop count. With max-hops = 5 in `CIRCUIT_LIFECYCLE.md §13`, decoy hop layers pad shorter routes. An observer cannot distinguish a 1-hop cell from a 5-hop cell.
- **UC security proof framework.** Wire-format claims are framed in UC notation for the eventual external review deliverable. The cell, header, body, and AEAD construction are described as ideal functionalities + concrete realizations per the Camera UC framework.

### §16.4.2 Not adopted

- **Stateless-per-packet routing** (Outfox's primary optimization). We use circuits (§5 above) for amortization; stateless routing is incompatible with circuit-based design.
- **Pure ML-KEM kex** (Outfox's primitive choice). We keep hybrid X25519+ML-KEM at circuit construction for defense-in-depth per POST_QUANTUM.md.
- **Batch mixing delays** (Outfox's latency model). We use constant-rate cover traffic instead (THREAT_MODEL §6.2.1).

### §16.4.3 Cross-references

- CIRCUIT_LIFECYCLE.md §21 — full Outfox-absorption discussion including compact per-hop header for EXTEND/EXTENDED cells
- THREAT_MODEL.md §12 — sovereignty principle that informs the rejection of ML-KEM-only

## §17 Implementation skeleton

Suggested module layout for `protocol-core::sealed_envelope`:

```
protocol-core/src/sealed_envelope/
  mod.rs          — public API (encrypt_cell, decrypt_cell, parse)
  cell.rs         — wire format constants + parse/serialize
  onion.rs        — multi-hop layered construction (Phase 2)
  replay.rs       — bloom filter + replay-tag derivation
  errors.rs       — EnvelopeError enum
  tests.rs        — unit + property tests
```

Module docs reference `// Ref: SEALED_ENVELOPE.md §X.Y` for every constant + invariant.

---

## §18 Revision history

| Date | Author | Change |
|---|---|---|
| 2026-05-22 (initial) | Iris | v0.1 per-envelope PQ kex design (8.7KB+ overhead per cell) |
| 2026-05-22 (circuit pivot) | Iris + Josh | **v0.2 PIVOT: circuit-based architecture.** Tor-style telescoping handshake at circuit-build amortizes PQ across thousands of cells. Per-cell crypto is pure symmetric. ~22x size reduction (11.3KB → 512B smallest cell). Companion CIRCUIT_LIFECYCLE.md spec required. Cell command structure adopted from Tor (0x01 data, 0x02 destroy, 0x03 handshake, 0x04/05 extend, 0x06 relay_data). |
| 2026-05-22 (walkthrough) | Iris + Josh | v0.2.1: §16.4 Outfox absorption — constant-length-route principle + UC proof framework at wire layer. Cross-references CIRCUIT_LIFECYCLE.md §21 for circuit-layer Outfox adoptions. |

---

*v0.2 is a structural improvement over v0.1. Per CLAUDE.md rule #1: draft, not self-certified complete. The circuit-based design depends on [CIRCUIT_LIFECYCLE.md](CIRCUIT_LIFECYCLE.md) being correct + implementable; the two specs must be co-reviewed.*
