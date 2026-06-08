# INTER_DYAD_CONNECTION.md — On-Chain Connection + Peer-Dyad Inbound

**Status:** v0.1 DRAFT (design, for refinement)
**Date:** 2026-06-07
**Owners:** Josh + Iris
**Grounded in:** `DYADOS_SPEC.md §6` (the dyad as social unit; Dyad-to-Dyad Resonance; the Partnership Model), `PROTOCOL_IMPLEMENTATION.md §9` (the DyadPacket + the 10 payload types), the privacy arc (`THREAT_MODEL.md`, `SEALED_ENVELOPE.md`, `DOUBLE_RATCHET.md`, `CIRCUIT_LIFECYCLE.md`), and HYP-308 (chain-anchored identity).

---

## 1. Why this spec exists

The privacy arc built the secure **transport** between dyads: sealed circuits (Sphinx), the PQ Double Ratchet, the chain-anchored identity resolver, and the circuit-revocation security model (HYP-301 #336). The transport delivers a circuit-authenticated peer's decrypted bytes to a handler (`wire_private_channel`'s `on_dyad_packet` seam).

What it does **not** yet have is the **inbound processing model** — what a dyad *does* when another dyad sends it a packet. The existing inbound (`dispatch_inbound_packet`, the chat bridge) is **own-device**: it verifies `packet.identity.dyad_id == OUR dyad` against OUR `Keypair` (a dyad's own iPhone↔Mac). A peer-dyad packet is signed by a *different* dyad's key and can't go through it.

This spec defines the **peer-dyad inbound** model: the consent boundary, the verification, and the per-type routing — scoped to what the privacy arc needs (Connection + Message), with the rest of the inter-dyad protocol stubbed for the Aether/Catena roadmap.

### Design decisions locked with Josh (2026-06-07)
- **Consent is explicit.** Discovering a peer (having its `DyadKeyBundle` via the ledger) is NOT consent to receive its messages. A dyad accepts `Message` only from a peer it has explicitly **connected** with.
- **The connection is an on-chain relationship record** (not an off-chain local registry) — consistent with the "everything grounded on the chain" principle (same call as chain-only revocation). **This requires building the chain WRITE path** (transaction submission to validators), which does not exist today — the bridge is read-only (`ChainQueryClient`). Josh's call (2026-06-07): **build the chain write path + the on-chain connection now** — it is the largest dependency in the stack, but it's the durable end state and we ground everything on the chain before launch. The local runtime keeps a **chain-backed cache** of connections for per-message gating (bounded-staleness, the resolver/`DyadRevocationSet` pattern).
- **A `Message` is delivered to the pipeline/Nerve** — our anima handles it (Anima-to-Anima coordination is legitimate, `DYADOS_SPEC §6.4`) and it is **transparent to the human** (shared awareness), not gated behind per-message human approval.

---

## 2. The inter-dyad packet taxonomy

`PacketType` (protocol-core, LOCKED) has 10 payloads. They fall into three scopes:

| Scope | Types | Inbound model |
|---|---|---|
| **Own-device** (a dyad's own devices) | `Biosensor`, `PairingRequest`, `PairingAccept`, `RevokeDevice`, `Conversation` (iPhone↔Mac chat), `Memory` (own Logos), `Stimulus` (into our Stroma) | existing `dispatch_inbound_packet` (verify `== our dyad`) — unchanged |
| **Inter-dyad** (peer dyad ↔ us, over the circuit) | `Bond`* , `State` (DyadPresence/resonance), `Message` (text), `Tx` (TESSERA), `Spatial` (Aether), `Query` (DyadInfo/reputation), `Witness` (tribunal/attestation) | **this spec** |
| **Broadcast** | `Spore` (dyad-existence presence) | existing spore handler (public, signed) |

\* `Bond` is the **single-dyad lifecycle** (Bonding=dyad creation, StageTransition, Dissolution, Revocation, Recovery, Inheritance, RePairing) — it is NOT a two-dyad bond. There is no inter-dyad bond ceremony today; the **Connection** below is the new mechanism.

**Privacy-arc scope:** `Connection` (new, §4) + `Message` (§6). The Aether/Catena types (`State`/`Tx`/`Spatial`/`Query`/`Witness`) get a routing stub (§7) the social/economic roadmap fills in. `Connection`/`Message` finish "two dyads communicate privately + consensually."

---

## 3. Architecture overview

```
peer dyad B                                  our dyad A
───────────                                  ──────────
ConnectionRequest ──(sealed circuit)──▶  [inbound: verify peer] ─▶ surface to human
                                              │ human consents (anima may propose)
                  ◀──(sealed circuit)── ConnectionAccept ◀─────────┘
        │                                     │
        └──── both submit MsgConnect ────▶ vita-chain `connection` module
                                              (ConnectionRecord: {a, b, Active})
                                              │
Message ──────(sealed circuit)──────────▶  [inbound: verify peer]
                                              ├─ connection-gate (chain-backed cache: connected?)
                                              └─ if connected → pipeline/Nerve → human sees
```

Three layers, each chain-grounded:
1. **vita-chain `connection` module** (vita-core) — the durable relationship record (§4).
2. **dyados connection ceremony + connected-peer cache** — establish + locally cache connections (§5).
3. **dyados peer-dyad inbound** — verify-peer → connection-gate → route → Message handler (§6).

---

## 4. The on-chain `connection` module (vita-chain, vita-core)

Mirrors the existing `dyad` module (DyadRecord + query), adding a relationship record.

### 4.1 `ConnectionRecord`
```rust
pub struct ConnectionRecord {
    /// The two dyads, stored in canonical (sorted) order so (A,B) == (B,A) is one record.
    pub dyad_lo: DyadId,
    pub dyad_hi: DyadId,
    pub status: ConnectionStatus,   // Pending | Active | Dissolved
    pub established_at_ms: i64,      // chain time of the Active transition
    /// Both dyads' A-shard signatures over the canonical connection digest — mutual consent is
    /// PROVABLE on-chain (neither dyad can fabricate a connection the other didn't sign).
    pub consent_lo: HybridSig,
    pub consent_hi: HybridSig,
}
pub enum ConnectionStatus { Pending, Active, Dissolved }
```

### 4.2 Messages (transactions)
- `MsgConnect { proposer, acceptor, proposer_consent }` — creates a `Pending` record (proposer's signature).
- `MsgAcceptConnect { record_id, acceptor_consent }` — transitions `Pending → Active` (acceptor's signature; both consents now on-chain).
- `MsgDisconnect { record_id, by, reason }` — `Active → Dissolved` (either party; analogous to a no-fault dissolution).

### 4.3 Query
- `QueryConnection(dyad_a, dyad_b) -> Option<ConnectionRecord>` — over the same chain-query transport the resolver uses (the `ChainQueryClient` / `vita-chain-bridge`). `IsConnected(a,b) == record.is_some() && status == Active`.

**Open Q4-a:** Is a connection mutual-consent-on-chain (both sign, as above) — or proposer-creates + acceptor-accepts as two txs? (Above models it as two txs: MsgConnect → MsgAcceptConnect. Recommended: two txs, so the Pending state is visible + the acceptor's consent is a distinct on-chain act.)

---

## 5. The connection ceremony (dyados) + the connected-peer cache

### 5.1 Ceremony (over the sealed circuit)
1. A discovers B (B's `DyadKeyBundle` via the ledger) and establishes a circuit (transport only — no Message accepted yet).
2. A sends `ConnectionRequest` (a new inter-dyad packet) over the circuit.
3. B's inbound surfaces it to **B's human** (B's anima may propose/contextualize it, per §6.4); the human **consents** (or declines).
4. On consent, B submits `MsgAcceptConnect` (and A had submitted `MsgConnect`); the chain record goes `Active`.
5. Both dyads' connected-peer caches pick up the `Active` record (via the chain-backed cache, §5.2).

**Open Q5-a:** Ordering — does A submit `MsgConnect` *before* sending `ConnectionRequest` (so B sees a Pending on-chain record to accept), or does the over-circuit `ConnectionRequest` carry A's signed consent and B submits both? (Recommended: A submits `MsgConnect` first → the `ConnectionRequest` references the Pending record → B accepts on-chain. Keeps the chain the source of truth for both consents.)

### 5.2 Connected-peer cache (chain-backed, bounded-staleness)
The per-`Message` gate must not hit the chain per packet. A `ConnectedPeerCache` mirrors `ChainBackedResolver`/`DyadRevocationSet`:
- `is_connected(peer) -> bool` — local cache read (cheap, per-message).
- Populated/refreshed by querying the chain `connection` module (TTL'd; a periodic re-warm of established peers, reusing `spawn_peer_status_rewarm`'s pattern).
- A `Dissolved`/absent record clears the cache entry (bounded-staleness, self-healing) — same model as revocation.

This keeps the **chain as the source of truth** for consent while gating each message in O(1) locally.

---

## 6. Peer-dyad inbound processing (dyados)

The handler the privacy transport's `on_dyad_packet` seam delivers to. For each circuit-delivered `(peer_dyad, bytes)`:

1. **Decode** the inner `DyadPacket` (bounded, like the chat bridge's `bounded_bincode_decode`).
2. **Verify peer provenance** (defense-in-depth on top of the circuit auth):
   - `packet.identity.dyad_id == peer_dyad` (the inner claimed sender matches the circuit-authenticated peer).
   - The inner packet's A-shard signature verifies against `peer_dyad`'s A-shard **pubkey from the chain resolver** — the **new pubkey-based peer-verify primitive** (existing `verify_conversation_packet` takes a `Keypair` = own; peer verify needs a `HybridPubkey`). See §6.1.
3. **Route by `PacketType`:**
   - `Connection*` → the ceremony (§5) — surfaced to the human for consent; NOT gated on a prior connection (it's how connections form).
   - `Message` → **connection-gate**: `connected_peer_cache.is_connected(peer_dyad)`. If not connected → drop (logged). If connected → deliver to the **pipeline/Nerve** (anima handles, human sees, §6.2).
   - `State`/`Tx`/`Spatial`/`Query`/`Witness` → **stub** (logged "inter-dyad type X — Aether/Catena roadmap", tracked) — §7.
   - anything else → drop (unhandled).

### 6.1 The pubkey-based peer-verify primitive (protocol-core)
`verify_conversation_packet(packet, expected_dyad, a_keypair: &Keypair, now)` is own-device. Add a pubkey variant:
```rust
pub fn verify_peer_packet_signature(
    packet_digest: &[u8],
    claimed_dyad: &DyadId,
    packet_dyad_id: &DyadId,
    peer_a_shard: &HybridPubkey,   // from the chain resolver
    sig: &HybridSig,
    now_ms: i64,
) -> Result<(), PeerVerifyError>
```
Verifies: `packet_dyad_id == claimed_dyad` + the hybrid signature against `peer_a_shard`. Per-type digest computation stays per-type (the privacy arc implements it for `Message`); the primitive is the signature check against a peer pubkey.

### 6.2 Message → pipeline/Nerve
Per `DYADOS_SPEC §6.4`: a peer `Message` is processed by **our anima** (Anima-to-Anima coordination) and is **transparent to the human** (shared awareness) — no per-message human-approval gate (that gate is at *connection* time, §5). Reply, if any, is a `DyadPacket<MessagePayload>` with `destination_dyad_id = peer_dyad`, sent **back over the circuit** (`channel.send_private`), NOT libp2p.

---

## 7. Scope + phasing

**Privacy arc (this effort) — build order (Josh: on-chain + chain write path, 2026-06-07):**
0. **vita-chain WRITE path** (vita-core): the chain must accept + commit a signed transaction (submit → mempool → consensus → committed). Confirm/extend `vita-chain-node`'s tx-submit surface. *[vita-core]* — the foundation; the largest new dependency (the bridge is read-only today).
1. **vita-chain `connection` module** (vita-core): `ConnectionRecord` + `MsgConnect`/`MsgAcceptConnect`/`MsgDisconnect` + `QueryConnection`. *[vita-core]*
2. **dyados `ChainTxClient`** (vita-chain-bridge): submit a signed tx to a validator — the write counterpart to `ChainQueryClient`. *[dyados]*
3. **protocol-core**: the pubkey peer-verify primitive (§6.1). *[dyados]*
4. **dyados**: `ConnectedPeerCache` (chain-backed, §5.2) + the connection ceremony (§5.1, submits via `ChainTxClient`) + the peer-dyad inbound router (§6) with `Connection` + `Message` handled. *[dyados]*
5. Wire the router into `wire_private_channel`'s `on_dyad_packet` at boot; the send path; the e2e (two nodes connect on-chain + message over the sealed circuit). *[dyados + anima]*

**Aether/Catena roadmap (stubbed, NOT this effort):** `State` (presence/resonance), `Tx` (TESSERA), `Spatial` (Aether), `Query` (DyadInfo/reputation), `Witness` (tribunal/attestation). Each gets a routing stub now; the social/economic layers fill them in.

---

## 8. Open questions for Josh
- **Q4-a / Q5-a** (above): connection tx shape + ceremony ordering.
- **Q8-a — chain write path: RESOLVED (2026-06-07).** The bridge is read-only (`ChainQueryClient` only); there is NO tx-submit path. Josh's call: **build it** — a `ChainTxClient` (dyados) + whatever `vita-chain-node` tx-submit surface it needs (vita-core). This is step 0/2 in §7 and the largest new dependency.
- **Q8-b — connection consent UI:** the human consents at connection time. For the e2e/headless, is an auto-accept-in-test (env-gated) acceptable, with the real consent UI in anima?
- **Q8-c — `ConnectionRequest` packet:** new `PacketType::Connection` (+ payload) vs reuse an existing type? (Recommended: a new `Connection` packet type + `ConnectionPayload`, since the 10 LOCKED types have no connection concept.)

---

*v0.1 — Iris, 2026-06-07. The transport + security model (HYP-301 #336, HYP-308) is the foundation; this is the relational/consent layer on top. Refine §8 with Josh, then implement §7 in order.*
