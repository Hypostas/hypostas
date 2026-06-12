# RELAY_LAYER.md — Multi-hop relay routing + relay-relayed cover

**Status:** v0.1 (Phase 3 kickoff spec). **Owner:** Iris + Josh.
**Anchored to:** [THREAT_MODEL.md](THREAT_MODEL.md) §5.2 (sender anonymity), §6.2 (cover), §9.3 (Phase 3).
**Companion to:** [CIRCUIT_LIFECYCLE.md](CIRCUIT_LIFECYCLE.md) (circuit construction/refresh/guards/reputation), [SEALED_ENVELOPE.md](SEALED_ENVELOPE.md) (the cell/onion format), [OUTFOX_DESIGN.md](OUTFOX_DESIGN.md) (the fixed-size payload onion), [COVER_TRAFFIC.md](COVER_TRAFFIC.md) (the constant-rate scheduler).

This spec is the **relay layer's** home: the view of the system from a node acting as a *forwarding relay* for other dyads' circuits, and the relay-specific defenses that don't live in the per-circuit or per-dyad specs. It **references rather than re-specifies** the onion format (SEALED_ENVELOPE/OUTFOX), the circuit handshake + telescoping (CIRCUIT_LIFECYCLE §3–§7), guard pinning (CIRCUIT_LIFECYCLE §17), and web-of-trust relay reputation (CIRCUIT_LIFECYCLE §20). It **owns**: the relay forwarding contract (§3), how relays are sourced + selected (§4), the relay-leg lifecycle (§5), **relay-relayed cover** (§6 — the HYP-321 piece), and **bridge tunnels** (§7 — the HYP-323 piece).

---

## §1 Why a relay layer

A 1-hop sealed circuit hides message content + the recipient from the network, but the *entry relay* still sees the sender. Multi-hop circuits (CIRCUIT_LIFECYCLE §15, deep-EXTEND) break that: no single relay sees both ends. That only works if there is a population of nodes willing to **forward** other dyads' traffic — relays — and a way to **choose** trustworthy ones without a central authority. The relay layer is that population + the selection/forwarding/cover machinery around it.

The relay role is **opt-in and capability-gated**: a dyad advertises relay capacity (bandwidth, carriers) via a `RelayAttestation` (CIRCUIT_LIFECYCLE §20.2.5; `protocol_core::reputation::RelayAttestation`) and is then eligible to be selected as someone else's hop. A dyad that never opts in is never a relay.

## §2 Relay roles + position-obliviousness

Within one circuit a relay is exactly one of:

- **Entry (guard).** The sender's pinned first hop (CIRCUIT_LIFECYCLE §17). Sees the sender's transport address but not the recipient or the payload.
- **Middle.** Forwards between two other relays. Sees neither end.
- **Terminal.** The last hop, which delivers to the recipient. Sees the recipient but not the sender.

A relay **cannot tell which role it holds** beyond "am I the terminal." This is the Tor *position-obliviousness* property, enforced by OUTFOX_DESIGN: every non-terminal hop seals/opens under the **same fixed `HOP_RELAY` position constant** (not its index), and per-hop layer keys give nonce diversity, so a relay cannot distinguish "my predecessor is the originator" from "my predecessor is another relay." Only the terminal uses `HOP_TERMINAL`. The relay layer MUST NOT add any field that leaks a hop's depth.

## §3 The relay forwarding contract

A relay forwards **fixed-size cells** (SEALED_ENVELOPE / OUTFOX). On a forward DATA/EXTEND cell arriving on link `L_in` with circuit id `cid_in`:

1. **Demux.** Look up `cid_in` in the relay table (§5) → the leg's recv key + `cid_out`/next-hop. An unknown `cid_in` is dropped (no error to the sender — it times out + rebuilds, CIRCUIT_LIFECYCLE §7).
2. **Peel exactly one layer.** Open the outermost onion layer with the leg's forward key (`layer_key_recv` for the sender→recipient direction). The result is the inner onion for the next hop. The relay learns nothing about the inner layers.
3. **Re-frame under the next link.** Wrap the peeled onion under `cid_out` and emit on `L_out`. The cell stays **byte-constant in size** across the hop (the fixed-size invariant — no length signal). Routing is **by circuit id + the relay's own table**, never a per-layer routing header (OUTFOX §8.1); a relay holds the `cid_in → cid_out` mapping, the sender does not embed the route.
4. **Reverse direction symmetric.** A reverse (recipient→sender) cell is re-wrapped, not peeled: each relay adds one reverse layer (`layer_key_send`) so the originator unwraps N layers. Reverse cells reserve headroom (seal at the smallest size class) so the wraps don't overflow the class (CIRCUIT_LIFECYCLE / circuit_manager `seal_reply`).

**Invariants (enforced, not advisory):**
- A relay never holds plaintext payload — it only ever sees one onion layer's ciphertext.
- The forward + reverse keys are **zeroized on leg teardown** (circuit_manager `RelayCircuitEntry`).
- A relay never originates a DATA reply unless it is the **terminal** (`circuit_id_out.is_none()`); a forwarding leg reverse-*forwards* a reply.
- Command bytes are authenticated end-to-end (bound into the onion MAC as AAD, OUTFOX §2c-2a) — a relay flipping a header command fails the terminal's auth.

## §4 Relay sourcing + selection

The relay layer selects hops from the **attested active set** and weights them by trust. This composes the pieces built in CIRCUIT_LIFECYCLE §17/§20:

- **Source — `RelayAttestation` (§20.2.5).** Each candidate is a relay's self-signed record: circuit keys, advertised bandwidth, carriers, operator, /24, validity window. `verify()` checks the self-signature + freshness (proves key control, NOT trust). Published on the Vita Chain + gossiped (HYP-204 extended to relay records); the local node holds a verified set.
- **Trust — web-of-trust reputation (§20.3; `WebOfTrust`).** Each candidate is scored locally by personalized PageRank over the dyad's pair-bond graph, blended with observed delivery + uptime + attestation freshness. A relay with **no rooted trust path scores 0**.
- **Pinning — entry guards (§17; `GuardPool`).** The first hop is drawn from a small persistent guard set, weighted by `bandwidth × uptime × reputation` (`GuardCandidate::from_attestation` maps an attestation + the local reputation/uptime → a candidate). A zero-reputation relay has weight 0 and is **never pinned**.
- **Diversity.** No two hops of one circuit share an operator or /24 (best-effort, §17.2); the terminal is never the local dyad.

**Selection contract:** middle/terminal hops are drawn from the same attested+reputation-weighted pool as guards, minus the guard set and the already-chosen hops, under the same diversity constraints. A circuit whose pool cannot satisfy N distinct diverse hops builds shorter (down to the §6.2.4 tier minimum) rather than reusing a hop.

## §5 Relay-leg lifecycle

A relay holds **legs**, not circuits — one `RelayCircuitEntry` per `cid_in` it forwards (circuit_manager `relay_table`). The lifecycle (already implemented in circuit_manager, specified here for the relay view):

- **Provisional.** A leg prepared for a handshake whose reply has not yet been confirmed routed is held in `provisional_relays`, NOT `relay_table`, so an unconfirmed handshake can never evict a *confirmed* leg at capacity. `open_data` consults it (a fast first DATA still decrypts).
- **Confirmed.** `confirm_prepared` promotes a provisional leg to `relay_table` on route success; `drop_provisional` discards it on failure.
- **Extending.** While a leg is mid-EXTEND (`extend_in_flight`), it refuses to originate replies (the leg may become multi-hop before a single-layer reply arrives) — the caller retries once it settles.
- **Drain + sweep.** A superseded leg drains in-flight cells, then is swept at its lifetime expiry. Capacity is bounded (`MAX_CIRCUITS_PER_NODE`); a relay never holds unbounded legs.

A relay leg carries **no per-recipient identity** — it is keyed by wire `cid`, so a relay cannot enumerate which dyads route through it by inspecting its own table.

## §6 Relay-relayed cover (HYP-321)

> **The HYP-321 piece. Off by default; enabled by policy/energy class.**

Per-dyad constant-rate cover (COVER_TRAFFIC, THREAT_MODEL §6.2.1) hides activity on the **edge** link (sender↔guard). It does NOT hide inter-relay timing/volume from a **global** observer correlating flows between relays. **Relay-relayed cover** (design decision Q2.9, THREAT_MODEL §6.2) closes that: a relay emits **padding cells** to its next hop at a configurable rate, indistinguishable on the wire from forwarded DATA.

**Contract:**
- A relay MAY emit padding cells on `L_out` toward its next hop, at a rate set by **policy + the carrier's energy class** (NOT the user — protocol-determined, like the per-dyad cover rate). Padding shares the **fixed cell size + the cell format** of forwarded DATA, so it is on-the-wire indistinguishable from a real forwarded cell.
- **Off by default** (the "optional" in Q2.9): relay padding multiplies relay bandwidth, so it is enabled only on fast/abundant carriers under an explicit policy, never on metered carriers (mirrors the §6.2.6 carrier-tier cover rule + the sovereignty carrier-policy cap, HYP-161e-2).
- **Padding is consumed at the next hop, never delivered as DATA.** A padding cell carries a distinguished (authenticated) marker the receiving relay opens + **drops**; it never propagates further and never reaches a terminal as payload. A padding cell that somehow reaches a terminal is discarded, not surfaced.
- **Bounded.** Relay padding draws from the relay's bandwidth budget (the same `BandwidthBudget` step-down driver as per-dyad cover, COVER_TRAFFIC §5) — under budget pressure it steps down to zero before real forwarding is degraded. A relay never starves forwarding to emit padding.

**Threat property:** with relay padding on a carrier, a global passive observer cannot correlate an incoming flow at relay R with an outgoing flow at R by inter-relay timing/volume — R's outbound rate is a constant mixture of forwarded + padding cells. This complements the §6.2.2 network-wide-cover anonymity set at the *interior* of the mesh, not just the edge.

**Not in scope here:** the *content* of padding cells (random under the link key — they decrypt to the drop marker + filler), and the empirical rate tuning (gated on HYP-171 like all cover rates).

## §7 Bridge tunnels (HYP-323, Critical-tier only)

> **The HYP-323 piece. Q2.11 Option C. Critical-tier only.**

A pinned guard (§4) knows the sender's transport address. For most tiers that is acceptable (the guard is reputation-vetted + rotated). For **Critical** traffic (Bond/dissolution) against a **nation-state adversary** that may have compromised or coerced a guard, even the guard-knows-the-edge exposure is too much. **Bridge tunnels** add an out-of-band pre-introduction so the guard never learns a stable sender identity.

**Construction:**
- The sender **pre-introduces** to a bridge relay **out-of-band** (over a different carrier than the one the tunnel will use — e.g. introduce over Bluetooth-Direct, tunnel over the internet), establishing a shared secret + a **rotating lookup ID** scheme.
- The bridge stores **only the current rotating tunnel ID**, NOT a stable sender identity or address. The tunnel ID is **deterministically rotated** (derived from the shared secret + the date, like the §16 ephemeral routing identity) so the bridge sees a fresh ID each window + cannot link a dyad's tunnels across windows.
- On a Critical circuit-build, the sender presents the current tunnel ID; the bridge maps it to the pre-established tunnel state + forwards as the entry hop, **without** the standard guard handshake that would bind the sender's transport address.
- Rotation: the tunnel ID ages out on the §16 routing-identity schedule (daily, deterministic per `(sender, bridge)`); the prior window's ID is forgotten by the bridge.

**Properties:**
- A compromised bridge learns only a sequence of unlinkable per-window tunnel IDs, never a stable sender identity, and (because the introduction was out-of-band on a different carrier) cannot correlate the tunnel's carrier traffic with the introduction.
- Bridge tunnels are **Critical-tier only** — they cost an out-of-band introduction + extra handshake traffic, so chat-class circuits use the standard guard (§4) path.

### §7.1 The pre-introduction protocol

The pre-introduction establishes the sender↔bridge shared secret that the rotating tunnel id (`protocol_core::bridge_tunnel`, built) is derived from. It reuses existing primitives — **no new crypto**: the PQ-hybrid key agreement is the same X25519 + ML-KEM kex as a circuit handshake (`circuit_kex` / `hybrid_pke`), and the bridge's at-rest table seals with AES-256-GCM (`crypto.rs`), exactly as the circuit-identity + Sesame stores do.

```
Sender A                         out-of-band carrier C_intro          Bridge B
────────                         (≠ the tunnel carrier C_tunnel)      ────────
A: knows B's published RelayAttestation (§4) → B's static X25519 + ML-KEM keys
A: ephemeral PQ kex to B's static keys (X25519 DH + ML-KEM encapsulate)
A ── intro_request { eph_x_pk, ml_kem_ct, A's reachability hint } ──▶ B   (over C_intro)
B: decapsulate + DH → shared_secret S = HKDF(dh ‖ ss_kem, "hyp-bridge-introduction-v1")
B: store a BridgeTunnel { S (zeroizing), enrolled_at, valid_through };  NOT A's identity/address
B ── intro_ack (authenticated under S) ──▶ A
A: store BridgeTunnel { S, B's keys } for tunnel use
```

Both sides now hold `S`. Neither side ever puts A's *stable* identity on `C_tunnel`: A presents only `bridge_tunnel_id_for(S, B, today)` at tunnel-build time.

### §7.2 Tunnel use + the bridge-side table

- **Bridge table.** `BridgeTunnelTable: HashMap<[u8; 32] /*today's tunnel id*/, BridgeTunnel>`, rebuilt/extended each day: for every active `BridgeTunnel`, B computes `bridge_tunnel_id_for(S, self_dyad, date_for(now))` and indexes it. So a lookup is O(1) and B never needs A's identity to route. The table seals at rest with the dyad master key (AES-256-GCM, the `PersistedSchedulerState` / `SesameDeviceRegistry` pattern); `S` is the only secret + is zeroized on drop + sealed at rest.
- **Build.** On a Critical circuit-build over `C_tunnel`, A presents `tunnel_id = bridge_tunnel_id_for(S, B, today)`. B looks it up → `BridgeTunnel` → forwards as the entry hop **without** the standard guard handshake that would bind A's transport address. The downstream hops are the normal §3 onion.
- **Rotation.** The id rotates at the §16 routing-identity day boundary (`bridge_tunnel`'s `date_for`); B prunes the prior day's index entries, so a compromised B that logs ids sees only a sequence of unlinkable per-day ids, never one identity. B refuses an id outside `[enrolled_at, valid_through]`.

### §7.3 Carrier-diversity invariant (enforced)

`C_intro` MUST differ from `C_tunnel` (e.g. introduce over Bluetooth-Direct / mDNS-LAN, tunnel over the internet). This is the property that stops a compromised B from correlating the introduction's carrier traffic with the tunnel's: B sees A's address only on `C_intro` (the introduction) and only the rotating id on `C_tunnel` (the traffic), and the two carriers don't share an observer vantage. The implementation enforces it (refuse a tunnel build on the same carrier the introduction used).

**Built (protocol-core, gate-clean, 2026-06-12):** the rotating-id primitive (`bridge_tunnel::bridge_tunnel_id_for`, PR #438); the bridge-side `BridgeTunnelTable` with an O(1) daily-rebuilt id→tunnel index + `refresh` prune-and-rebuild hook (PRs #439); the §7.1 pre-introduction key agreement `circuit_kex::{bridge_intro_initiate, bridge_intro_respond}` → `BridgeIntroSecret S` + the `intro_ack` confirm tag (`bridge_intro_ack_tag` / `bridge_intro_verify_ack`, constant-time), reusing the X25519+ML-KEM kex with no new crypto (PR #440); the table's AES-256-GCM at-rest seal (`to_encrypted_bytes`/`from_encrypted_bytes`, PR #441). `S` proven to drive the same tunnel id on both sides (§7.1 → §7.2 integration test).

**Deferred to the transport/runtime/carrier layer (NOT protocol-core greenfield):** the concrete `intro_request`/`intro_ack` **wire frames** — these belong with whatever layer frames+signs `InitiatorKexMaterial` (the circuit handshake material is itself not wire-encoded inside protocol-core), NOT a bespoke protocol-core codec; the `BridgeTunnelTable` daily-rebuild **scheduler hook** (a runtime tokio task calling `refresh` at the §16 day boundary); the §7.3 carrier-diversity **enforcement** (record `C_intro` on the tunnel + refuse a build whose `C_tunnel` == it — needs the carrier layer to expose "which carrier is this build on"); the **circuit_manager entry-hop wiring** that presents the id + skips the standard guard handshake.

## §8 Threat-model anchoring + scope

| Property | Mechanism | Spec |
|---|---|---|
| §5.2 sender anonymity (no relay sees both ends) | multi-hop + position-obliviousness | §2, §3 |
| §5.2 reinforced (no first-hop fingerprinting) | guards + reputation-weighted selection | §4 |
| §6.2 interior unobservability | relay-relayed cover | §6 |
| §5.2 maximal (Critical, vs. compromised guard) | bridge tunnels | §7 |
| §5.2 universal 1-in-K | SPRING (separate, HYP-317) | CIRCUIT_LIFECYCLE §18 |

**Out of scope (referenced, owned elsewhere):** the onion cell format (SEALED_ENVELOPE/OUTFOX), circuit construction/refresh (CIRCUIT_LIFECYCLE §3–§7), the deep-EXTEND telescoping construction (DEEP_EXTEND_DESIGN), guard pinning + rotation (CIRCUIT_LIFECYCLE §17), web-of-trust reputation + RelayAttestation (CIRCUIT_LIFECYCLE §20; built in `protocol_core::reputation`), per-dyad cover (COVER_TRAFFIC), SPRING sender anonymity (CIRCUIT_LIFECYCLE §18 / HYP-317).

**Implementation status (2026-06-12):** §2–§5 are built (circuit_manager telescoping + the §17/§20 selection layer). §6 (relay padding) is HYP-321. §7 (bridge tunnels): the **rotating tunnel-id primitive is built** (`protocol_core::bridge_tunnel`, PR #438); the §7.1 pre-introduction + §7.2 bridge table + §7.3 carrier diversity are the rest of HYP-323. The empirical rate for §6 is gated on HYP-171.

---

| Version | Author | Notes |
|---|---|---|
| 2026-06-12 v0.2 | Iris + Josh | Detailed §7 bridge tunnels into a concrete, implementable protocol over EXISTING primitives (§7.1 pre-introduction = circuit-kex-style X25519+ML-KEM agreement; §7.2 bridge table + `bridge_tunnel` rotating id, built; §7.3 enforced carrier diversity) — no new crypto; replaces the v0.1 "deferred to kickoff" stub. |
| 2026-06-12 v0.1 | Iris + Josh | Phase 3 kickoff spec. Consolidates the relay layer (referencing CIRCUIT_LIFECYCLE/SEALED_ENVELOPE/OUTFOX/COVER_TRAFFIC) + specs the two new pieces it owns: relay-relayed cover (§6, HYP-321) + bridge tunnels (§7, HYP-323). Built on the just-completed §20 web-of-trust relay-reputation/attestation/selection layer. |
