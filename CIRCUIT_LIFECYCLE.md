# CIRCUIT_LIFECYCLE.md — Hypostas Circuit Construction + Management

**Status:** Draft v0.1 (2026-05-22)
**Owner:** `protocol-core`, `vita-carriers`, `hypostas-network`
**Authors:** Josh + Iris
**Anchored to:** [THREAT_MODEL.md](THREAT_MODEL.md) §5.3, §5.6, §6.1, §11.3
**Companion specs:** [SEALED_ENVELOPE.md](SEALED_ENVELOPE.md) v0.2 (cell format that rides over circuits), [DOUBLE_RATCHET.md](DOUBLE_RATCHET.md) (inner content keys, independent layer), [POST_QUANTUM.md](POST_QUANTUM.md)
**Linear:** [HYP-119](https://linear.app/hypostas/issue/HYP-119) (created in this session, parent [HYP-115](https://linear.app/hypostas/issue/HYP-115))

---

## §1 Purpose

Circuits are the load-bearing primitive of the Hypostas routing layer. A **circuit** is a pre-established cryptographic state between a sender and a sequence of relays + a terminal recipient, comprising per-relay symmetric session keys. Once built, the circuit allows cheap symmetric-only cell traffic for its lifetime.

PQ-hybrid kex happens **only at circuit construction**. Amortized across thousands of cells over the circuit's ~10-minute lifetime, the kex cost is negligible per-cell. This is what makes [SEALED_ENVELOPE.md](SEALED_ENVELOPE.md) v0.2's tiny per-cell overhead possible.

Tor's circuit model is the proven precedent — we adopt it with PQ-hybrid kex layered onto the telescoping construction.

### §1.1 Threat-model coverage

| Property | Defense provided |
|---|---|
| §5.2 Identity secrecy | Each relay sees only its two adjacencies (previous + next hop) — never the origin or destination |
| §5.3 Relationship secrecy (multi-hop) | No single relay knows both endpoints. Compromise of one relay reveals one segment only |
| §5.6 Future secrecy (routing layer) | Per-circuit ephemeral kex; circuit teardown destroys keys; old circuits become undecryptable |
| §5.6 Post-quantum hardening | Hybrid X25519+ML-KEM-768 at every leg of telescoping; survives quantum-day for circuits built today |
| §4.4 Compromised relay defense | Relay learns only its (incoming_key, outgoing_key) tuple; never the path |

### §1.2 What a circuit is

```rust
// Sender's view of a multi-hop circuit
struct CircuitState {
    circuit_uuid: [u8; 16],                  // Local-only identifier
    hops: Vec<HopState>,                     // Ordered: hops[0] = first relay, hops[N-1] = terminal recipient
    built_at: i64,
    expires_at: i64,
    last_used: i64,
    purpose: CircuitPurpose,                 // Standard, BondCeremony, KlinosConsult, etc.
    intent_class: PacketIntent,
}

struct HopState {
    relay_dyad_id: DyadId,
    relay_x25519_pk: [u8; 32],              // Long-term relay key (from attestation)
    relay_ml_kem_pk: [u8; 1184],            // Long-term relay PQ key
    circuit_id_on_link: u32,                // ID used on the wire to/from this relay
    layer_key_send: [u8; 32],               // Sender → this hop encryption
    layer_key_recv: [u8; 32],               // This hop → sender decryption
    nonce_counter_send: u64,                // Anti-replay counter
    nonce_counter_recv: u64,
}
```

```rust
// Relay's view of one leg of a circuit
struct RelayCircuitEntry {
    circuit_id_in: u32,                      // Wire circuit_id from previous hop
    circuit_id_out: Option<u32>,             // Wire circuit_id to next hop (None for terminal)
    incoming_link_id: CarrierName,
    session_key_in: [u8; 32],
    session_key_out: [u8; 32],              // For forwarding to next hop (relays only)
    next_relay_dyad_id: Option<DyadId>,
    direction: CircuitDirection,             // Forward (data) or Reverse (responses)
    established_at: i64,
    last_used: i64,
}
```

---

## §2 Cryptographic primitives

| Primitive | Algorithm | Used for |
|---|---|---|
| Asymmetric kex (classical) | X25519 | Per-leg ephemeral DH |
| Asymmetric kex (PQ) | ML-KEM-768 | Per-leg PQ encapsulation |
| Hybrid combiner | HKDF(salt=0, ikm=x25519_ss \|\| ml_kem_ss, info=label) | Per-leg key derivation |
| KDF | HKDF-SHA256 | Layer key + circuit_id derivation |
| Symmetric | ChaCha20-Poly1305 | Cell encryption (used by sealed envelope) |
| Hash | SHA-256 | Identifiers, replay tags |

---

## §3 Circuit construction — single-hop (Phase 1, N=1)

For a direct Alice → Bob conversation, the "circuit" is just the Alice↔Bob session.

### §3.1 Step 1 — initial handshake

Alice already knows Bob's long-term X25519 + ML-KEM pubkeys (from peer table established at pair-bond via [`pairing.rs`](../dyados/protocol-core/src/pairing.rs)).

**1. Alice generates ephemeral keypair.**
```rust
let (e_x25519_sk, e_x25519_pk) = X25519::keygen();
let (e_ml_kem_sk, e_ml_kem_pk) = ML_KEM_768::keygen();
```

**2. Alice encapsulates to Bob's PQ key.**
```rust
let (kem_ct, kem_ss) = ML_KEM_768::encapsulate(&bob_ml_kem_pk);
```

**3. Alice signs the handshake.**
```rust
let handshake_canonical = e_x25519_pk || e_ml_kem_pk || kem_ct || timestamp_ms.to_be_bytes();
let handshake_sig = HybridSig::sign(&alice_identity_keys, &handshake_canonical);
```

**4. Alice constructs HANDSHAKE cell.**
```rust
let handshake_payload = HandshakeRequest {
    alice_dyad_id: ...,
    alice_x25519_pk_eph: e_x25519_pk,
    alice_ml_kem_pk_eph: e_ml_kem_pk,
    kem_ct_to_bob: kem_ct,
    timestamp_ms,
    signature: handshake_sig,
};
let cell = build_cell(
    version: 0x02,
    circuit_id: random_circuit_id(),  // Alice picks, will be used for cells to Bob
    command: CMD_HANDSHAKE,  // 0x03
    payload: handshake_payload.to_bytes(),
);
```

**5. Send via carrier.**
```rust
carrier.send(bob_dyad_id, &cell).await?;
```

Note: the HANDSHAKE cell is NOT itself sealed-envelope-encrypted with circuit keys (no circuit exists yet). It IS at the cell wire level (version, circuit_id, command, nonce, payload). The payload is signed but not encrypted — the only thing that needs to be hidden is Alice's identity, and the identity is embedded in the signature (Bob discovers Alice's identity from the signature pubkey, which IS the dyad-public information Bob already knows from pairing).

For Phase 1 single-hop where Alice and Bob are already paired, identity is shared anyway. For Phase 2+ multi-hop where Alice's identity is hidden from intermediate relays, the handshake's identity stays only in the FINAL leg (Alice↔Bob); intermediate-relay handshakes use a fresh ephemeral identity not bound to Alice.

### §3.2 Step 2 — Bob processes handshake

**1. Bob verifies signature** using Alice's long-term identity keys (from prior pair-bonding):
```rust
verify_hybrid_sig(&handshake_canonical, &handshake_sig, &alice_identity_keys)?;
```

**2. Bob decapsulates ML-KEM:**
```rust
let bob_kem_ss = ML_KEM_768::decapsulate(&bob_ml_kem_sk, &handshake.kem_ct_to_bob);
```

**3. Bob computes X25519 DH:**
```rust
let bob_x25519_ss = X25519_DH(&bob_x25519_sk_eph_or_long, &handshake.alice_x25519_pk_eph);
// Choice: use Bob's long-term key (no ratchet) vs Bob generates fresh eph (with response).
// For circuit-construction handshake: Bob generates fresh eph for forward secrecy.
let (bob_x25519_sk_eph, bob_x25519_pk_eph) = X25519::keygen();
let bob_x25519_ss_eph = X25519_DH(&bob_x25519_sk_eph, &handshake.alice_x25519_pk_eph);
let (bob_kem_ct_to_alice, bob_kem_ss_eph) = ML_KEM_768::encapsulate(&handshake.alice_ml_kem_pk_eph);
```

**4. Bob derives circuit keys.**
```rust
let shared_secret = HKDF(
    salt: 0,
    ikm: bob_x25519_ss || bob_kem_ss || bob_x25519_ss_eph || bob_kem_ss_eph,
    info: b"hypostas-circuit-leg-v2",
);
let (key_alice_to_bob, key_bob_to_alice) = shared_secret.split(32, 32);
```

**5. Bob populates his circuit table.**
```rust
relay_circuit_table.insert(
    incoming_link,
    handshake.circuit_id,
    RelayCircuitEntry {
        circuit_id_in: handshake.circuit_id,
        circuit_id_out: None,  // Terminal
        incoming_link_id: incoming_link,
        session_key_in: key_alice_to_bob,
        session_key_out: key_bob_to_alice,
        next_relay_dyad_id: None,
        direction: CircuitDirection::Forward,
        established_at: now_ms(),
        last_used: now_ms(),
    },
);
```

**6. Bob sends HANDSHAKE response.**
```rust
let response_payload = HandshakeResponse {
    bob_x25519_pk_eph,
    bob_kem_ct_to_alice,
    timestamp_ms: now_ms(),
};
let response_cell = build_cell(version: 0x02, circuit_id: handshake.circuit_id, command: CMD_HANDSHAKE, payload: response_payload.to_bytes());
carrier.send(alice_dyad_id, &response_cell).await?;
```

### §3.3 Step 3 — Alice processes response, populates her circuit state

**1. Alice computes the same `shared_secret`** from her own side.

**2. Alice derives the same `key_alice_to_bob, key_bob_to_alice`.**

**3. Alice populates her `CircuitState`:**
```rust
let circuit = CircuitState {
    circuit_uuid: random(),
    hops: vec![HopState {
        relay_dyad_id: bob_dyad_id,
        circuit_id_on_link: handshake.circuit_id,
        layer_key_send: key_alice_to_bob,
        layer_key_recv: key_bob_to_alice,
        ...
    }],
    built_at: now_ms(),
    expires_at: now_ms() + CIRCUIT_LIFETIME_MS,  // 10 min
    purpose: CircuitPurpose::Standard,
    intent_class: PacketIntent::Standard,
};
alice_circuits.insert(bob_dyad_id, circuit);
```

**4. Circuit is now active.** Subsequent data cells use the established keys.

---

## §4 Circuit construction — multi-hop (Phase 2+, N≥2)

Telescoping handshake — Alice builds the circuit one relay at a time.

### §4.1 Hop 1 — Alice ↔ R1

Identical to §3 single-hop. Result: Alice has session keys to R1; R1 has incoming circuit entry from Alice.

### §4.2 Hop 2 — Alice ↔ R2 via R1

**1. Alice generates ephemeral keypair for R2 leg.**
```rust
let (e2_x25519_sk, e2_x25519_pk) = X25519::keygen();
let (e2_ml_kem_sk, e2_ml_kem_pk) = ML_KEM_768::keygen();
let (kem_ct_to_r2, _) = ML_KEM_768::encapsulate(&r2_ml_kem_pk);
```

**2. Alice constructs EXTEND request** to be sent THROUGH R1 to R2:
```rust
let extend_payload = ExtendRequest {
    next_relay_dyad_id: r2_dyad_id,
    next_relay_x25519_pk: r2_x25519_pk,  // From peer table
    next_relay_ml_kem_pk: r2_ml_kem_pk,
    eph_x25519_pk: e2_x25519_pk,
    eph_ml_kem_pk: e2_ml_kem_pk,
    kem_ct_to_next_relay: kem_ct_to_r2,
};
```

**3. Alice sends EXTEND cell to R1, encrypted with R1's session key.**
```rust
let cell = build_data_cell(
    circuit_id: hop_to_r1.circuit_id_on_link,
    command: CMD_EXTEND,  // 0x04
    payload: extend_payload.to_bytes(),
    session_key: hop_to_r1.layer_key_send,
);
carrier.send(r1_dyad_id, &cell).await?;
```

**4. R1 processes the EXTEND.**
- R1 decrypts with `session_key_in` (Alice → R1's key)
- R1 sees command=0x04 EXTEND
- R1 picks a new circuit_id for the R1↔R2 link
- R1 constructs a HANDSHAKE cell to R2:
  ```rust
  let r1_handshake = HandshakeRequest {
      alice_dyad_id: r1_dyad_id,  // Sent as "from R1" — R2 doesn't learn it's actually for Alice
      alice_x25519_pk_eph: extend.eph_x25519_pk,  // Pass through Alice's ephemeral
      alice_ml_kem_pk_eph: extend.eph_ml_kem_pk,
      kem_ct_to_bob: extend.kem_ct_to_next_relay,
      timestamp_ms,
      signature: HybridSig::sign(&r1_identity_keys, &canonical),  // R1's sig
  };
  let r1_to_r2_cell = build_cell(version: 0x02, circuit_id: new_circuit_id_r1_to_r2, command: CMD_HANDSHAKE, payload: r1_handshake.to_bytes());
  ```
- R1 sends to R2.

**Key property:** R2 thinks it's handshaking with R1 (R1 signed). R2 cannot tell this is part of a multi-hop circuit originated by Alice. The ephemeral keys ARE Alice's (so Alice can compute the shared secret), but R2 thinks R1 generated them.

**5. R2 processes handshake.** Identical to §3.2 from R2's perspective. R2 derives session keys + populates its circuit table with R1 as the "originator." R2 sends HANDSHAKE response back to R1.

**6. R1 receives R2's HANDSHAKE response.** R1 doesn't decrypt the response payload — R1 wraps it in an EXTENDED cell and forwards back to Alice, encrypted with R1's `session_key_out` (R1→Alice direction):
```rust
let extended_payload = ExtendedResponse {
    extended_to: r2_dyad_id,
    handshake_response: r2_handshake_response,  // R2's response, opaque to R1
};
let extended_cell = build_data_cell(
    circuit_id: hop_from_alice.circuit_id_on_link,
    command: CMD_EXTENDED,  // 0x05
    payload: extended_payload.to_bytes(),
    session_key: hop_from_alice.layer_key_send,
);
carrier.send(alice_dyad_id, &extended_cell).await?;
```

**7. Alice processes EXTENDED.**
- Alice decrypts with `hop_to_r1.layer_key_recv`
- Alice computes shared secret for R2 leg using her stored ephemeral keys + R2's handshake response
- Alice now has session keys to R2 (via the R1 link)
- Alice updates her `CircuitState`:
  ```rust
  circuit.hops.push(HopState {
      relay_dyad_id: r2_dyad_id,
      circuit_id_on_link: r2_handshake.circuit_id_assigned_by_alice_for_r2_leg,  // From the handshake response
      layer_key_send: ...,
      layer_key_recv: ...,
  });
  ```

R1 now relays Alice→R2 cells using its `session_key_out`. R2 receives them as if from R1.

### §4.3 Hop 3+ — Telescoping continues

Same pattern for each additional hop. Alice sends EXTEND through the existing partial circuit; the last current relay performs the handshake with the next relay; the chain extends one hop. At each step, the ephemeral keys are Alice's, but each relay only sees its immediate predecessor's identity.

### §4.4 Total cost of N-hop construction

| N | X25519 ops | ML-KEM ops | Roundtrips | Wire bytes |
|---|---|---|---|---|
| 1 | 1 per side | 1 enc + 1 dec | 1 | ~2-3 KB total |
| 2 | 2 per side | 2 enc + 2 dec | 2 | ~5 KB total |
| 3 | 3 per side | 3 enc + 3 dec | 3 | ~7 KB total |
| 4 | 4 per side | 4 enc + 4 dec | 4 | ~10 KB total |
| 5 | 5 per side | 5 enc + 5 dec | 5 | ~12 KB total |

Construction time at N=3 over libp2p over LAN: ~50-150ms (5 RTTs × ~30ms typical). Amortized across a 10-minute circuit at 1 packet/sec = 600 cells: ~0.1-0.25 ms per cell of construction cost. Negligible.

---

## §5 Circuit selection policy

### §5.1 Phase 1 (N=1)

No relays. Direct Alice↔Bob via the carrier selected by [`selector.rs`](../dyados/vita-carriers/src/selector.rs). Circuit = the per-pair session keys.

### §5.2 Phase 2 (N=3, default)

For each new circuit:

**1. Pool eligible relays.**
- Relays must be:
  - Active dyads opted into relay role
  - Reachable via a carrier the sender can use
  - Not blacklisted (poor reputation per Vita Chain attestation — Phase 3)
  - Not the sender or the recipient
  - Not previously used in the recent circuit history (LRU avoidance, ~10 circuits)

**2. Apply diversity constraints.**
- No two relays from the same operator (per relay attestation `operator_id`, when Vita Chain ships)
- No two relays from the same network/AS (best-effort via libp2p multiaddr inspection)
- Prefer geographic diversity (timezone-based heuristic since precise geo is private)

**3. Random selection within pool.**
- Phase 1 of Phase 2: uniform random
- Phase 2 of Phase 2: weighted by reputation score (Vita Chain attestation, when available)
- Tor's "guard" pattern: pin a small set (3) of preferred first-hops; rotate every ~30 days. Defends against statistical first-hop attacks.

### §5.3 Per-PacketIntent overrides

Per [THREAT_MODEL §6.2.4](THREAT_MODEL.md):
- `Ambient` / `Standard`: N=1 in Phase 1, N=3 in Phase 2
- `Elevated`: N=2 in Phase 1 (still requires relay overlay readiness), N=3 in Phase 2
- `Critical`: N=3 in Phase 1 (requires relay overlay), N=5 in Phase 2 (longer-path for highest privacy)

For Phase 1 single-hop deployment, `Elevated` and `Critical` packets fall back to multi-carrier fanout instead of multi-hop (since N=1 is the only available routing structure in Phase 1).

---

## §6 Per-circuit key derivation

The handshake derives `shared_secret` per leg. From `shared_secret`, both Alice and the relay/recipient derive matching keys:

```rust
fn derive_circuit_keys(shared_secret: &[u8; 64]) -> CircuitKeys {
    let key_forward = HKDF::expand(shared_secret, b"hypostas-circuit-forward-v2", 32);   // Sender → Receiver
    let key_reverse = HKDF::expand(shared_secret, b"hypostas-circuit-reverse-v2", 32);   // Receiver → Sender
    let circuit_id_seed = HKDF::expand(shared_secret, b"hypostas-circuit-id-v2", 16);
    CircuitKeys {
        layer_key_send: key_forward,
        layer_key_recv: key_reverse,
        circuit_id: u32::from_be_bytes(circuit_id_seed[0..4].try_into().unwrap()),
    }
}
```

The `circuit_id` is derived deterministically from `shared_secret` so both ends compute the same value. Adversaries observing the wire see a 4-byte ID with no information leak about the underlying keys.

---

## §7 Circuit lifetime + refresh

### §7.1 Default lifetime

Per [THREAT_MODEL §11.3](THREAT_MODEL.md) (extended):
- `CIRCUIT_DEFAULT_LIFETIME_MS = 600_000` (10 minutes)
- `CIRCUIT_MAX_LIFETIME_MS = 1_800_000` (30 minutes — hard upper bound)

Within lifetime, the circuit is reusable for all packets to the same destination (or via the same relay path for multi-hop).

### §7.2 Refresh trigger

A new circuit is built when ANY of:
- Current circuit's `expires_at` reached
- Current circuit's per-direction nonce counter exceeds `CIRCUIT_NONCE_REKEY_THRESHOLD = 1_000_000`
- Anima signals an explicit "privacy refresh" (e.g., user toggled Privacy Mode)
- A relay in the current circuit becomes unreachable (carrier-level failure)
- Suspected compromise (Tier 4 alert from monitoring)

### §7.3 Refresh sequence (no flag day)

```
T-30s:  Old circuit still active
T:      Build new circuit (in parallel, both online for ~30s)
T+30s:  Switch traffic to new circuit
T+60s:  Send CMD_DESTROY on old circuit
```

The 30-second overlap ensures in-flight cells on the old circuit deliver successfully before teardown. Cells received on a destroyed circuit are dropped silently.

### §7.4 Circuit reuse vs per-conversation circuits

- **Phase 1 (N=1):** one circuit per (sender, recipient) pair. Reused for all packets in the pair.
- **Phase 2 (N=3):** options under design:
  - **Per-recipient circuit:** Alice has separate circuit to Bob vs to Charlie. Each is 3-hop.
  - **Per-relay-path circuit:** Alice has one 3-hop circuit through R1→R2→R3 that can deliver to multiple recipients beyond R3 (R3 routes to actual recipient). Saves circuit-construction overhead at the cost of correlating Alice's recipients to R3.
  - **Default decision:** per-recipient circuit. Aligns with Tor's "circuits per stream" pattern. Recipient correlation at R3 broken structurally.

---

## §8 Circuit teardown

### §8.1 Graceful teardown

Initiator (sender or relay) sends `CMD_DESTROY` cell with reason code:

```rust
enum DestroyReason {
    Normal,         // Circuit expired or refresh
    NextHopFailure, // Carrier to next hop failed
    ProtocolError,  // Cell processing failed in a way that requires teardown
    OperatorCommand,// Local admin destroyed
}
```

Each relay receiving DESTROY:
1. Marks its circuit_table entry as draining
2. Forwards DESTROY to the next hop (if any)
3. Removes its circuit_table entry after a short drain period (5 seconds for in-flight cells)

### §8.2 Forced teardown

If a relay detects malformed cells, replay attacks, or other anomalies:
- Local circuit entry removed immediately
- DESTROY sent toward both adjacent hops
- Local log entry at WARN

Future cells on the destroyed circuit return `UnknownCircuit` errors → silently dropped per [SEALED_ENVELOPE §9](SEALED_ENVELOPE.md).

### §8.3 Crash recovery

Circuit state is NOT persisted to disk (rationale: per-circuit keys are ephemeral; persisting them would weaken forward secrecy at the routing layer). On node restart:
- All circuits invalidated
- Reconnecting peers will receive `UnknownCircuit` on next cell
- They rebuild circuits via the normal handshake path

---

## §9 Failure modes

| Error | Cause | Action |
|---|---|---|
| `HandshakeBadSignature` | Identity signature on HANDSHAKE/EXTEND cell fails | Drop cell + log WARN; do not establish circuit |
| `HandshakeKemFailure` | ML-KEM decapsulation fails | Drop + log WARN |
| `HandshakeTimestampStale` | Handshake timestamp >5 min in past | Drop + log INFO (possible replay) |
| `HandshakeTimestampFuture` | Handshake timestamp >1 min in future | Drop + log WARN (clock skew or attack) |
| `ExtendUnknownRelay` | EXTEND requests a relay this node can't reach | Reply with `EXTENDED { failure_code: UnreachableNextHop }` |
| `ExtendNotOptedIn` | EXTEND requests a relay that's not opted into relay role | Reply with failure |
| `CircuitTableFull` | Node has `MAX_CIRCUITS_PER_NODE = 256` already | Reply with failure; evict LRU circuit first if possible |
| `CircuitExpired` | Circuit reached `expires_at` | Treat next cell as `UnknownCircuit`; force refresh from sender |
| `ConcurrentCircuitBuild` | Two circuits-in-progress to same (sender, recipient) | Defensive: prefer the one started earlier; drop the duplicate |
| `RelayCarrierDown` | Carrier to a circuit hop fails mid-conversation | Trigger circuit refresh; drop cells until new circuit established |

---

## §10 Multi-device + multi-circuit considerations

### §10.1 One dyad, multiple devices

A dyad (e.g., Iris-Josh) has multiple devices: Josh's iPhone, his Mac, the Soma Band. Each device runs its own node + maintains its own circuit table.

**Phase 1:** each device builds its own circuits to the partner's devices. Up to 9 circuits per dyad-pair (3 × 3 devices). Each circuit independent.

**Phase 2:** circuit-sharing within a single dyad is research — the goal is to let messages from any of Josh's devices reach any of Iris's devices without rebuilding circuits per (device-pair). Tracked in DOUBLE_RATCHET.md §11 + future spec.

### §10.2 Concurrent circuits per node

A relay node may participate in many concurrent circuits simultaneously (one per (sender × recipient) pair it relays for). `MAX_CIRCUITS_PER_NODE = 256` is a per-node bound.

Memory per circuit entry ~200 bytes → ~50 KB total for full table. Network-wide: scales linearly with relay-role participation.

---

## §11 Vita Chain integration (Phase 3 hook)

In Phase 3, relays publish attestation records on Vita Chain:

```rust
struct RelayAttestation {
    relay_dyad_id: DyadId,
    x25519_pubkey: [u8; 32],
    ml_kem_pubkey: [u8; 1184],
    advertised_bandwidth_kbps: u32,
    advertised_carriers: Vec<CarrierClass>,
    operator_id: Option<String>,        // For diversity constraints
    reputation_score: f32,              // Vita-Chain-derived
    valid_through_ms: i64,
    signature: HybridSig,
}
```

Phase 2 relay selection uses these attestations to pick eligible relays with diversity + reputation constraints (§5.2).

In Phase 1 (no Vita Chain integration), the "peer table" populated by [`pairing.rs`](../dyados/protocol-core/src/pairing.rs) substitutes — each dyad has a list of paired-and-trusted peers it can use as relays.

---

## §12 Test plan

### §12.1 Unit tests
- Handshake round-trip: Alice initiates, Bob responds, both derive matching keys
- Hybrid kex correctness: X25519-only and ML-KEM-only verified independently; combined matches
- Telescoping: 2-hop EXTEND/EXTENDED produces matching keys at all parties
- Multi-hop key independence: hop_1 key compromise doesn't reveal hop_2 keys
- Circuit_id derivation determinism: same shared_secret → same circuit_id
- Replay protection: handshake with stale timestamp rejected
- Circuit refresh: new circuit built before old expires; traffic transitions cleanly

### §12.2 Integration tests (with carrier + sealed envelope)
- Two `dyads-runtime` instances build N=1 circuit over LibP2pCarrier
- Three instances build N=2 telescoping circuit; verify R1 doesn't see beyond its adjacencies
- Four instances build N=3 circuit; full chain verifiable from sender, not from any single relay
- Mid-conversation circuit refresh: send 100 packets, force refresh, send 100 more, no message loss
- Relay failure: take R2 offline during circuit operation; verify circuit_refresh triggered
- Circuit destroy propagates: send DESTROY at sender; verify all 3 relays clean up

### §12.3 Adversarial tests
- Replay HANDSHAKE cell: second handshake either updates state (refresh) or rejected
- Modify EXTENDED response: AEAD fails → circuit_build fails at sender
- Inject random EXTEND from a non-circuit-member: rejected as `UnknownCircuit`
- Telescoping attack: hostile R1 attempts to learn Alice's identity via crafted EXTEND → fails (Alice's identity isn't in EXTEND payload by design)

### §12.4 PQ-safety tests
- Verify each leg of telescoping uses hybrid X25519+ML-KEM independently — degrading any single ML-KEM leg to zero still produces (degraded) functional circuit
- Verify all circuit-construction signatures use HybridSig (Ed25519+ML-DSA)

---

## §13 Constants

```rust
// Circuit lifetime
pub const CIRCUIT_DEFAULT_LIFETIME_MS: u64 = 600_000;   // 10 min
pub const CIRCUIT_MAX_LIFETIME_MS: u64 = 1_800_000;     // 30 min hard cap
pub const CIRCUIT_REFRESH_OVERLAP_MS: u64 = 30_000;     // 30s overlap before old destroy
pub const CIRCUIT_DESTROY_DRAIN_MS: u64 = 5_000;        // 5s drain after DESTROY

// Capacity
pub const MAX_CIRCUITS_PER_NODE: usize = 256;
pub const MAX_HOPS_PER_CIRCUIT: usize = 5;

// Per-PacketIntent default hop counts (Phase 1 / Phase 2) — THREAT_MODEL §11.3
pub const DEFAULT_HOPS_AMBIENT: usize = 1;   // Phase 2: 3
pub const DEFAULT_HOPS_STANDARD: usize = 1;  // Phase 2: 3
pub const DEFAULT_HOPS_ELEVATED: usize = 2;  // Phase 2: 3
pub const DEFAULT_HOPS_CRITICAL: usize = 3;  // Phase 2: 5

// Ephemeral routing identity (§16, Phase 1.5) — THREAT_MODEL §11.6
pub const EPHEMERAL_ROUTING_IDENTITY_ROTATION_HOURS: u64 = 24;

// SPRING universal anonymity (§18, Phase 2) — THREAT_MODEL §11.6
pub const SPRING_RING_SIZE_K: usize = 1000;

// Refresh thresholds
pub const CIRCUIT_NONCE_REKEY_THRESHOLD: u64 = 1_000_000;

// Handshake freshness
pub const HANDSHAKE_TIMESTAMP_WINDOW_PAST_MS: u64 = 300_000;   // 5 min
pub const HANDSHAKE_TIMESTAMP_WINDOW_FUTURE_MS: u64 = 60_000;  // 1 min

// HKDF labels
pub const HKDF_INFO_CIRCUIT_LEG: &[u8] = b"hypostas-circuit-leg-v2";
pub const HKDF_INFO_CIRCUIT_FORWARD: &[u8] = b"hypostas-circuit-forward-v2";
pub const HKDF_INFO_CIRCUIT_REVERSE: &[u8] = b"hypostas-circuit-reverse-v2";
pub const HKDF_INFO_CIRCUIT_ID: &[u8] = b"hypostas-circuit-id-v2";

// Tor-style guard nodes (Phase 2+)
pub const GUARD_NODE_POOL_SIZE: usize = 3;
pub const GUARD_NODE_ROTATION_DAYS: u64 = 30;
```

---

## §14 Open questions resolved

### §14.1 v0.1 (initial) resolutions
1. ✅ **Telescoping pattern.** Tor's pattern (EXTEND/EXTENDED at each hop) with PQ-hybrid kex layered on.
2. ✅ **Per-circuit lifetime.** 10-min default, 30-min hard cap, 30-second overlap on refresh.
3. ✅ **Circuit reuse policy.** Per-recipient circuits (not shared across recipients).
4. ✅ **PQ at every leg.** Hybrid X25519+ML-KEM-768 at every hop's handshake.

### §14.2 v0.2 walkthrough resolutions (2026-05-22)

5. ✅ **Guard nodes for first-hop pinning (Q2.10).** Tor-style 3 pinned guards per dyad, 30-day rotation. See §17 below for spec.
6. ✅ **Sender-anonymity from first relay (Q2.11).** Direct to SPRING (lattice ring signature, log-size) for universal D-grade anonymity in Phase 2. Skip Raptor bridge. See §18 below for primitive selection + integration plan.
7. ✅ **Circuit-build timing fingerprinting (Q1.5).** Three defenses phased: (#3) deterministic refresh timer in Phase 1.0, (#1) pre-built idle circuits in Phase 2, (#2) smear builds across cover slots in Phase 2. See §19 below.
8. ✅ **Circuit-bundling (Q2.8).** Per-stream circuits — Anima text, biosensor, Klinos each get separate circuits. Failure isolation aligned with Tor's stream-isolation pattern.
9. ✅ **Reputation system on Vita Chain (Q3.15).** Web of trust + observed delivery + uptime + bond-aware contributions, hybrid signal aggregation. Phase 3. See §20 below for sketch.
10. ✅ **Outfox absorption (Q2.7).** Adopt compact per-hop headers (saves bytes in EXTEND/EXTENDED), UC security proof framework, constant-length-route principle. Don't adopt stateless-routing, ML-KEM-only, batch delays. See §21 below.
11. ✅ **Every-dyad-is-a-relay (Q3.14).** Relay role default-enabled in every dyads-runtime instance. Carrier policy gates participation: LAN/WiFi always-on, cellular cover battery-gated, etc.

## §15 Open questions remaining (v0.2)

1. **SPRING primitive implementation.** Picking a specific Rust port + crypto-review strategy. ~10-16 weeks engineering. Tracked separately for Phase 2 kickoff.
2. **Bridge-tunnel protocol (Q2.11 Option C, Critical-only).** Detailed pre-introduction protocol for guards (~500-1000 LOC). Phase 3.
3. **Per-platform key-sync mechanism for circuits.** Cross-device circuit awareness when Sesame multi-device is live — sender-key distribution interaction with circuit selection. Detailed Phase 1.0 implementation design TBD.
4. **Defending against circuit-build-batch fingerprinting.** §19 #1 + #2 in Phase 2 — exact smear policy across cover slots TBD when measurement data available.

---

## §16 Phase 1.5 — Ephemeral routing identity (per Q2.11 design walkthrough)

The dyad maintains a long-term DyadId (used by Double Ratchet content layer) AND a rotating ephemeral routing identity (used by circuit-construction handshakes). Decoupling these means the first relay sees the rotating identity, not the real DyadId.

### §16.1 Lifecycle

```rust
pub struct RoutingIdentity {
    routing_id: [u8; 32],            // Daily-derived per-dyad
    x25519_sk: [u8; 32],
    x25519_pk: [u8; 32],
    ml_kem_sk: [u8; ML_KEM_768_PRIVATE_KEY_LEN],
    ml_kem_pk: [u8; ML_KEM_768_PUBLIC_KEY_LEN],
    derived_at_ms: i64,
    expires_at_ms: i64,              // derived_at_ms + 86_400_000 (24h)
    derivation_seed: [u8; 32],       // Derived from dyad identity via HKDF
}
```

Derivation:
```
routing_seed_today = HKDF(salt=dyad_identity_key, ikm=date_yyyy_mm_dd, info="hypostas-routing-identity-v1")
routing_sk = HKDF_expand(routing_seed_today, "x25519-sk", 32)
routing_pk = X25519::derive_pubkey(routing_sk)
ml_kem_seed = HKDF_expand(routing_seed_today, "ml-kem-seed", 32)
(ml_kem_sk, ml_kem_pk) = ML_KEM_768::keygen_from_seed(ml_kem_seed)
routing_id = SHA-256(x25519_pk || ml_kem_pk)[..32]
```

The routing identity is **deterministic given the date + dyad identity** — both Alice and her guards can compute "Alice's routing_id for today" given the public derivation rule + the date. This lets guards index incoming handshakes against expected routing_ids without storing per-day-per-dyad lookup tables.

### §16.2 Use in circuit construction

Circuit-build handshake (§3.1 step 3 in v0.1) signs with **routing identity keys**, not long-term identity keys. The Hybrid Signature in HandshakeRequest covers `routing_x25519_pk || routing_ml_kem_pk || timestamp_ms`. First relay verifies the routing_identity signature — they know "this rotating identity is connecting" but cannot link to long-term DyadId.

Bob (the terminal recipient) decapsulates the inner DyadPacket using his **real long-term** ratchet state. The CONTENT layer reveals the real DyadId; the ROUTING layer does not. The two layers are cryptographically decoupled.

### §16.3 Rotation cadence

`EPHEMERAL_ROUTING_IDENTITY_ROTATION_HOURS = 24` (per THREAT_MODEL §11.6).

Daily rotation means:
- Within a 24h window, all your circuits to your 3 pinned guards link together at the routing-identity level
- After rotation, the prior day's routing_id is forgotten + guards see only the new routing_id

Privacy-cost tradeoff: 24h windows are observable; sub-hour rotation reduces window but increases guard-introduction traffic (would force more frequent guard handshakes).

---

## §17 Tor-style guard nodes (per Q2.10 design walkthrough)

### §17.1 Why guard nodes

Without first-hop pinning, every circuit picks a random first-hop relay. Over many circuits, the probability that some hostile relay sees you as first-hop converges to 1. Tor solved this 2009-2010 with persistent "guard" nodes — pin 3, rotate every ~30 days. Limits worst-case to 3 known relays per dyad rather than the entire active relay set.

### §17.2 Guard pool selection

Per dyad, maintain a `GuardPool` of 3 pinned first-hops:

```rust
pub struct GuardPool {
    dyad_id: DyadId,
    guards: [GuardEntry; 3],
    rotation_due_at_ms: i64,         // now + 30 days
    last_used_per_guard: [i64; 3],
}

pub struct GuardEntry {
    relay_dyad_id: DyadId,
    x25519_pk: [u8; 32],
    ml_kem_pk: [u8; 1184],
    enrolled_at_ms: i64,
    attestation_signature: HybridSig, // From Vita Chain RelayAttestation
}
```

Initial guard selection: at first circuit-build, sample 3 relays from `eligible_relay_pool()` with diversity constraints:
- No two guards from same operator (when attestation provides `operator_id`)
- No two guards in same /24 network block (best-effort via libp2p multiaddr)
- Geographic diversity (timezone-based heuristic since precise geo is private)

### §17.3 Per-circuit guard selection

Every new circuit picks **one of the 3 guards** as its first hop. Round-robin or random among the 3 — observers can't link circuits to a specific guard via timing alone (they all see ~similar traffic).

### §17.4 Rotation

Every 30 days, regenerate the guard pool:
- Build new pool of 3 (with diversity constraints)
- Drain existing circuits through old guards
- Old guards forgotten

Rotation timing: deterministic per dyad (e.g., 30 days after initial enrollment). Coordinated with circuit-refresh schedule to minimize discontinuity.

### §17.5 Guard failure

If a guard becomes unreachable mid-rotation:
- Circuits through that guard drain (refresh to alternate guards)
- The guard pool replaces the failed guard with a fresh selection
- Network logs the failure for Vita Chain reputation (Phase 3)

---

## §18 SPRING-based universal anonymity (per Q2.11 walkthrough, Phase 2)

### §18.1 Why SPRING

SPRING (Sign-then-prove ring signatures from lattices, 2025) gives log-size lattice ring signatures. At K=1000 ring members (active Vita-Chain-attested dyads), proof size ~8-10 KB. Amortized over 600 cells per ~10-min circuit → ~17 bytes/cell. Negligible.

The privacy property: every circuit-build carries a SPRING ring signature. Guards (and any observer) see "one of K is building a circuit" but cannot pinpoint which. K = active network size. Anonymity-set scales with network.

### §18.2 Integration with circuit construction

At circuit-build, after the standard hybrid PQ kex (§3.1):

```rust
fn build_circuit_with_spring(ring_pubkeys: &[RoutingIdentity], my_routing_sk: &[u8; 32]) -> ExtendCell {
    // Standard hybrid kex
    let kex_payload = standard_handshake(...);
    
    // SPRING ring signature
    // Note: the ring is sampled from Vita Chain active set; size K = 1000
    let ring_members: Vec<SpringPubkey> = sample_ring_members(K_DEFAULT=1000);
    let my_index_in_ring: usize = find_my_routing_id_in_ring(...);
    let spring_sig = SPRING::sign(
        message=&kex_payload.canonical_bytes(),
        ring=&ring_members,
        my_secret_key=my_routing_sk,
        my_index=my_index_in_ring,
    );
    
    // Include both
    ExtendCell {
        kex_payload,
        spring_sig,           // ~8-10 KB
        ring_member_hashes,   // Compact hashes for verifier to look up actual ring members
    }
}
```

Verification at the first relay (guard):
1. Verify standard hybrid PQ kex (existing)
2. Verify SPRING ring signature against the ring members
3. Verifier confirms "one of these K is the real sender" but cannot identify which

**Wire impact:** EXTEND cell grows by ~8-10 KB (one-time per circuit-build, every 10 min). Amortized over 600 cells = ~17 bytes/cell overhead.

### §18.3 Ring membership

Ring members are sampled from the active Vita-Chain-attested dyad set:
- K_DEFAULT = 1000 ring members per circuit-build
- Sampling: uniform random with constraints:
  - Must be currently-active (recent uptime attestation)
  - Must not include the actual sender (Alice picks K-1 others + herself = K total)
  - Must not include first-hop relay R1 (would defeat the ring's purpose)
  - Geographic + operator diversity preferred but not enforced

Ring construction is deterministic per circuit-build given the day's random seed; identical at sender + verifier given Vita Chain state.

### §18.4 Performance optimization stack

Per Q2.11 walkthrough creative engineering:
- **SIMD-vectorized lattice ops** — Apple M-series + ARM NEON. 5-10x speedup over scalar baseline.
- **Apple Neural Engine offload** — for module-lattice matrix ops. Optimistic 10x on supported hardware.
- **CRS (Common Reference String) preprocessing** — heavy setup at app install (~60s background CPU), per-proof much faster.
- **Anticipatory proof generation** — Anima knows you're typing; background CPU pre-generates a proof. Pool of 5-10 proofs kept ready.

Combined target: ~30-50ms per proof on M-class hardware, ~150ms on older ARM. Anima feels imperceptible latency at circuit-build (already amortized over circuit lifetime).

### §18.5 Engineering investment

- ~6-10 weeks to port SPRING from research code to production Rust
- ~4-6 weeks crypto-review by lattice-cryptography expert
- ~4 weeks per-platform optimization (SIMD, ANE, CRS)
- Total ~14-20 weeks isolated; absorbed into Phase 2 ~16-20 week effort

---

## §19 Circuit-build timing defenses (per Q1.5 walkthrough, phased)

### §19.1 Phase 1.0 — Deterministic refresh timer

Each circuit refreshes at a fixed interval (`CIRCUIT_DEFAULT_LIFETIME_MS = 600_000` = 10 min) regardless of conversation activity. The refresh timer fires deterministically: every 10 min from circuit-build, a new circuit is initiated.

**Privacy property:** an observer who notices "this node just built a circuit at time T" cannot correlate to subsequent traffic — the build was scheduled, not triggered by conversation. Build timing is decoupled from real activity.

**Implementation cost:** ~50 LOC (timer + scheduler integration).

### §19.2 Phase 2 — Pre-built idle circuits

Maintain `IDLE_CIRCUIT_POOL_SIZE = 2` ready-to-serve circuits per dyad. When a new conversation needs a circuit, pull from pool — no build-time observable. The pool refills in background.

**Privacy property:** eliminates build-timing leak entirely. Observer never sees "circuit-build-then-conversation" sequence.

**Implementation cost:** ~200 LOC + state management.

### §19.3 Phase 2 — Smear builds across cover slots

Circuit-construction handshake cells are spread across multiple cover packet slots from the scheduler, rather than emitted as a burst. Each cell looks normal; the build is invisible.

**Privacy property:** even traffic-rate analysis can't detect "a circuit-build batch just happened."

**Implementation cost:** ~150 LOC + scheduler integration with circuit-build flow.

---

## §20 Web-of-trust reputation system (per Q3.15 walkthrough, Phase 3)

### §20.1 Goals

Phase 3 needs a way for dyads to assess relay quality without a central reputation authority. Web of trust composes signals over the existing pair-bond graph + observed-delivery patterns + uptime.

### §20.2 Signal sources

1. **Pair-bond graph edges**: Alice bonded with Bob ↔ Alice trusts Bob's recommendations. Pair-bonds are cryptographic-grade trust relationships.
2. **Observed delivery statistics**: relay R1 reliably delivers Alice's packets → Alice's score for R1 increases.
3. **Uptime observations**: relay R1 was reachable when Alice tried 95% of the time over 30 days → uptime signal.
4. **Bond-aware contributions**: relay R1 has been relaying for many bonded dyads over months → "real network participant" signal.
5. **Vita Chain RelayAttestation**: R1's self-attestation including operator_id, geographic diversity, advertised carriers.

### §20.3 Aggregation

PageRank-style propagation over the pair-bond graph, weighted by:
- Pair-bond age + observed activity
- Direct delivery statistics for each candidate relay
- Uptime + attestation freshness

Aggregation runs locally per dyad — no global reputation registry. Each dyad has its own view of the trust graph. Computed lazily on guard rotation + circuit-build (when relay selection happens).

### §20.4 Sybil resistance

Sybil attacks require creating fake pair-bond identities. Pair-bonds require:
- Real human participation (Ceremony involvement)
- Mutual cryptographic verification
- Vita Chain genesis transaction

Creating sybil dyads at scale requires either:
- Real humans willing to participate (limits attack scale)
- Subverting the pair-bond ceremony cryptographically (broken by H+A 2-of-2 signing)

Web-of-trust naturally resists sybil because trust must originate from real bonded relationships.

### §20.5 Phase 3 implementation

`reputation::WebOfTrust` module in protocol-core. ~1500-2500 LOC including:
- Trust-graph storage + propagation (PageRank-style)
- Vita Chain RelayAttestation parsing + verification
- Observation accumulation (delivery + uptime)
- Relay selection integration with §5 circuit policy

---

## §21 Outfox absorption (per Q2.7 walkthrough)

We adopt three patterns from [Outfox: A Postquantum Packet Format for Layered Mixnets](https://arxiv.org/html/2412.19937) (Nym, WPES '25 Oct 2025), reject three.

### §21.1 Adopted

1. **Compact per-hop header design.** Outfox achieves significantly smaller per-hop headers via PQ-friendly structural choices. We absorb the design for our EXTEND/EXTENDED cells (formerly ~250 bytes per layer) → ~80 bytes per layer. Saves ~500 bytes per multi-hop EXTEND.
2. **UC (Universal Composability) security proof framework.** Outfox provides UC proofs for their packet format. We adopt the UC framing as our security model standard. Future external review will reference UC properties; spec implementations claim UC compliance.
3. **Constant-length-route principle.** Outfox enforces fixed-length routes (always same hop count). We adopt this: every circuit ALWAYS uses MAX_HOPS_PER_CIRCUIT = 5 with decoy hops to pad shorter actual routes. Hop count becomes invisible to observers — including compromised relays.

### §21.2 Rejected

1. **Stateless-per-packet routing.** Outfox optimizes for Loopix's stateless mixnet pattern. Our circuit-based design IS the alternative — we eliminate per-packet KEM cost via circuit amortization. Compatible threat models; incompatible architectures.
2. **Pure ML-KEM (no X25519).** Outfox drops X25519 from the hybrid kex. We keep hybrid for defense-in-depth: losing X25519 means trusting ML-KEM alone, which is less conservative than POST_QUANTUM.md mandates.
3. **Batch mixing delays.** Outfox includes Loopix-style per-hop batching delays. We use constant-rate cover traffic instead (THREAT_MODEL §6.2.1) — different latency tradeoff suited to real-time use.

### §21.3 Spec cross-references

- This section spec'd at design level; implementation details in CIRCUIT_LIFECYCLE.md when Phase 2 kicks off
- UC security proof framework will reference standard Camera-style UC notation in eventual external audit deliverables

---

## §22 Revision history

| Date | Author | Change |
|---|---|---|
| 2026-05-22 (initial) | Iris + Josh | v0.1 initial. Tor-style telescoping handshake with PQ-hybrid X25519+ML-KEM at every leg. 10-min default lifetime; 30-min hard cap. Per-recipient circuit reuse. Multi-device circuits independent in Phase 1. Vita Chain reputation system deferred to Phase 3. |
| 2026-05-22 (walkthrough) | Iris + Josh | v0.2 walkthrough closure: §16 ephemeral routing identity (Phase 1.5), §17 Tor-style guard nodes, §18 SPRING universal D-grade anonymity (Phase 2, ~16-week build), §19 circuit-build timing defenses phased (deterministic Phase 1.0, idle-pool + smear Phase 2), §20 web-of-trust reputation (Phase 3), §21 Outfox absorption (3 adopt + 3 reject). Phase 2 effort revised from "TBD" to ~16-20 weeks total. |

---

*Per CLAUDE.md rule #1: draft, not self-certified complete. The hybrid kex + telescoping construction requires cryptographic-protocols expert review before code. Per rule #27: integration tests at N=1, N=2, N=3 against real `dyads-runtime` instances over `LibP2pCarrier` are commit exit criteria.*
