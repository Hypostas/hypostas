# RELAY_LAYER.md — Multi-hop relay routing + relay-relayed cover

**Status:** v0.1 (Phase 3 kickoff spec). **Owner:** Iris + Josh.
**Anchored to:** [THREAT_MODEL.md](THREAT_MODEL.md) §5.2 (sender anonymity), §6.2 (cover), §9.3 (Phase 3).
**Companion to:** [CIRCUIT_LIFECYCLE.md](CIRCUIT_LIFECYCLE.md) (circuit construction/refresh/guards/reputation), [SEALED_ENVELOPE.md](SEALED_ENVELOPE.md) (the cell/onion format), [OUTFOX_DESIGN.md](OUTFOX_DESIGN.md) (the fixed-size payload onion), [COVER_TRAFFIC.md](COVER_TRAFFIC.md) (the constant-rate scheduler).

This spec is the **relay layer's** home: the view of the system from a node acting as a *forwarding relay* for other dyads' circuits, and the relay-specific defenses that don't live in the per-circuit or per-dyad specs. It **references rather than re-specifies** the onion format (SEALED_ENVELOPE/OUTFOX), the circuit handshake + telescoping (CIRCUIT_LIFECYCLE §3–§7), guard pinning (CIRCUIT_LIFECYCLE §17), and web-of-trust relay reputation (CIRCUIT_LIFECYCLE §20). It **owns**: the relay forwarding contract (§3), how relays are sourced + selected (§4), the relay-leg lifecycle (§5), **relay-relayed cover** (§6 — the HYP-321 piece), and **bridge tunnels** (§7 — the HYP-323 piece).

---

## §1 Why a relay layer

A 1-hop sealed circuit hides message content + the recipient from the network, but the *entry relay* still sees the sender. Multi-hop circuits (CIRCUIT_LIFECYCLE §15, deep-EXTEND) break that: no single relay sees both ends. That only works if there is a population of nodes willing to **forward** other dyads' traffic — relays — and a way to **choose** trustworthy ones without a central authority. The relay layer is that population + the selection/forwarding/cover machinery around it.

The relay role is **default-ON and capability-gated** (Josh, 2026-08-01; supersedes the v0.1 opt-in default — see §9.2 for the rationale and §13 Q3 for what the reversal costs). Every bonded dyad that *can* relay does, so the anonymity set tracks adoption rather than a separate volunteer or token-incentive program, and the "why would anyone run a relay" question does not arise. Capability is determined by the node, not chosen by the user: phone-hosted dyads never enter the pool. The single user-facing knob is an **opt-out**, and it is honored (the COVER_TRAFFIC sovereignty principle).

A dyad advertises relay capacity (bandwidth, carriers) via a `RelayAttestation` (CIRCUIT_LIFECYCLE §20.2.5; `protocol_core::reputation::RelayAttestation`) and is then eligible to be selected as someone else's hop — but **under a relay identity, not its `DyadId`** (§10). Publishing the dyad identity of every relaying dyad would turn the directory into a public census of the network; that defect and its fix are §10.

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
- **Trust — web-of-trust reputation (§20.3; `WebOfTrust`).** Each candidate is scored locally by personalized PageRank over the dyad's pair-bond graph, blended with observed delivery + uptime + attestation freshness. ⚠️ **The v0.1 rule "a relay with no rooted trust path scores 0" is REPEALED by §11.** Under §10 a relay's identity is unlinkable to its `DyadId`, so it has no pair-bond edges by construction and would score 0 — meaning `GuardPool` would select *nothing* and no circuit would ever build (confirmed against `reputation/mod.rs:301` + `guards.rs:357`). §11 replaces the rule with a two-tier prior.
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

### §6.1 Implementation dependency — the relay↔relay link key (OPEN, blocks HYP-321)

> **Spec/code divergence surfaced 2026-06-12 (HYP-323 build).** This subsection resolves a hand-wave, per "specs are intent, code is truth — resolve the mismatch explicitly." The §6 text above presumes the receiving relay can *authenticate* a padding cell ("a **distinguished (authenticated)** marker the receiving relay opens + drops"; "random under **the link key**"). **That link key does not exist in the current circuit.** A relay leg (`RelayCircuitEntry`) holds `session_key_in`/`session_key_out` — the **initiator↔this-hop** payload keys — plus `next_hop_dyad` + `next_hop_circuit_id`; a forwarding relay "holds none of the leg's secrets" and shares **no key with its next hop R+1**. The Outfox payload MAC is keyed initiator↔terminal, so a relay R **cannot** forge a payload-onion cell that R+1 will authenticate, and the forward path re-seals with the *same* command under R+1's id (so a naive `CMD_DROP` would *propagate*, not stop). HYP-321 therefore cannot be implemented as a payload-onion cell as written. The decision (and HYP-321's real first step):

- **(a) Unauthenticated cover-drop (no new key, recommended for v1 — IN PROGRESS).** A padding cell is a random Outfox-shaped cell (correct fixed size + clear header) with a **random `circuit_id`** that authenticates *nowhere* at R+1 — it falls through R+1's existing **cover-drop** path (`on_data_outfox`'s final fall-through already silently drops a cell matching no forward/terminal/reverse leg) and is consumed, never delivered. Delivers the §6 **threat property** in full (the observer can't distinguish padding from data; R+1 consumes it). This is exactly the model of the per-dyad EDGE cover cell (`sealed_envelope::cover_cell` — "the random `circuit_id` drops it at the receiver").
  - **The receiver-collision is residual but BENIGN (a key realization, 2026-06-12).** The emitter R **cannot** pick a guaranteed-cover-dropped id: the demux that matters is **R+1's** table, which R cannot see (R checking its OWN tables proves nothing about R+1). With a 2³² id space vs R+1's small live table, a random id collides at R+1 with probability ~2⁻²⁰; on a collision with one of R+1's **forwarding** legs, R+1 peels the random body + re-frames it onward (the forward path authenticates only at the terminal), so the padding traverses the rest of *that* circuit and is dropped at the terminal (`recover_message` fails on the random body) — **never delivered as DATA, never corrupting the real flow, the threat property intact**. So §6.1(a) padding is *best-effort cover*, not a hard guarantee, and accepts the **same** negligible benign collision the edge `cover_cell` already accepts. **A local "collision-free id picker" does NOT help — it filters the wrong (emitter's) tables — and is not needed.** (An attempt to build one was reverted on this finding.)
  - **No protocol change. The whole LOGIC layer is BUILT (gate-clean, dyados PRs #443/#447/#449/#450):** the cell primitive `seal_outfox_padding_cell` (random-id, indistinguishable from a forwarded DATA cell; integration-proven cover-dropped); the cadence core `RelayPaddingScheduler` (off-by-default; enabled iff opt-in AND **unmetered** AND cover-class ≥ Standard; `on_slot(now, &shared_carrier_budget)` one slot per the carrier energy-class rate, yielding to budget pressure first); the `RelayPaddingDriver::tick` + the carrier-**pinned** `RelayPaddingSink` trait (emits one random-id padding cell to EACH forwarding next-hop, metered into the shared budget, fan-out yields at the predictive step-down, `CryptoRng` ids); and the driver's read surface `CircuitManager::forwarding_next_hops()` + `CarrierSelector::preferred_carrier_props()`. All reuse `BandwidthBudget` + `EnergyClass` + `carrier_max_cover_class` — zero new rate/budget model.
  - **Remaining = the runtime WIRING only** (dyados-runtime, mirrors `cover_driver.rs`): the async loop ticking `tick` at `rate_ms`; building the scheduler from `preferred_carrier_props` (`cover_class` + `CostClass::Free`) + the off-by-default opt-in; a `route_pinned`-backed `RelayPaddingSink` impl (pin to the preferred carrier); and the **shared per-carrier `BandwidthBudget`** so padding meters into the same budget as real forwarding + cover (§6 "never starve forwarding"). The shared budget is the one genuine architecture question — cover's budget is encapsulated in `CoverTrafficDriver`; a v1 may use a conservative padding SUB-budget (a small fraction of the carrier cap, can't starve forwarding) with the real-time-shared budget as a refinement. (The carrier-facts surface that earlier blocked this is now built — `preferred_carrier_props` — and is the SAME surface §7.3 carrier-diversity needs.)
- **(b) Authenticated link key (protocol addition, deferred).** Establish a real R↔R+1 link secret (a lightweight DH during EXTEND, or ride the carrier transport's existing link security) and seal padding under it with a `CMD_DROP` marker R+1 affirmatively opens + drops + accounts. Cleaner (O(1) recognition, distinct budget accounting, no wasted peel) but adds adjacent-hop handshake state + a new key to the circuit lifecycle — a design change gated on Fable 5 + Codex sign-off, not a v1.

**Recommendation:** ship **(a)** for HYP-321 v1 (the threat property with zero protocol change, accepting the benign residual receiver-collision above), and track **(b)** as a follow-up optimization. **Decided + in progress:** the v1 cell primitive is built (PR #443); the *unauthenticated cover-drop* path needs no link key, so the cell IS a clean protocol-core primitive — it is the **authenticated `CMD_DROP` marker** (option b) that needs the absent link key + would give a *hard* drop guarantee (R+1 affirmatively recognizes padding), not the v1 cell. The remaining v1 driver is just the **random-id** emit loop (rate + budget + gating + sink) — there is no collision-free id step (it can't filter R+1's tables and isn't needed). *(The Linear issue for this finding is pending the MCP connector reconnect — see the build ledger.)*

**The full driver + runtime wiring are BUILT, OFF BY DEFAULT (dyados PRs #449/#450/#452/#453):** `RelayPaddingDriver::tick` over `forwarding_next_hops`, a `route_pinned`-pinned `RelayPaddingSink`, the `spawn_relay_padding_driver` loop, and the bootstrap spawn held in `RuntimeState` (opt-in `false`). **Three activation preconditions MUST land before flipping the opt-in on** (gate-surfaced; tracked, all latent while off):
1. **Size-distribution matching (P1).** v1 emits only `SizeClass::S`, but forwarded DATA is the smallest-FITTING class (a mix of `S`/`M`/`L`/`Xl`); an observer distinguishes the `S`-only padding stream by length. Padding must emit the actual forwarded size distribution per link.
2. **Per-link multi-carrier coverage (P2-coverage).** v1 pins to ONE preferred carrier; a forwarding link reachable only via a fallback carrier is uncovered (never mis-covered — `route_pinned` fails + skips). Full coverage needs a padding stream per `(carrier, next-hop)`.
3. **Shared per-carrier budget for CAPPED carriers (P2-budget/P3).** v1 restricts to truly-unbounded carriers (free Network, cap `u64::MAX`) so the budget is moot; a capped eligible carrier (free Radio) needs the SHARED budget (so padding yields to real forwarding + cover) + a local-midnight reset.

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

## §9 The relay directory (v0.3 — HYP-168)

§4 sources candidates from "the attested active set" and never says who publishes it.
`vita-carriers/src/guards.rs:14` names the same hole from the other side: the pool
"is the input seam — supplied by the caller (HYP-168); this module never sources or
attests it." There is no `eligible_relay_pool()`, no hop-selection function, and no
caller of `GuardPool` anywhere in the tree. §9–§12 close that seam.

### §9.1 The role-separation law (normative)

Three roles, **disjoint node sets**:

| Role | Population | Sees | Holds |
|---|---|---|---|
| **Validator** | `M1_VALIDATOR_COUNT = 7` | public chain state | consensus, the registry |
| **Relay** | all capability-eligible dyads | adjacent hops only | no chain state |
| **Client** | every dyad | its own circuits | the consensus directory |

> **The chain is the DIRECTORY. It is not the RELAY.**

Precedent: [Nym](https://nym.com/docs/operators/tokenomics) registers Nyx validators
(Cosmos PoS + reward contract) and mixnodes separately; validators never carry mixnet
traffic. Counter-precedent rejected: Oxen/Lokinet service nodes are *both*.

**Why validators must not relay.** A 3-hop circuit over the 7-node validator set, with
an adversary holding `k`: `k=1 → 0.0%`, `k=2 → 4.8%`, `k=3 → 14.3%` chance of seeing
both entry and exit — over a set that is *publicly enumerated on-chain*, and where a
node observing chain traffic and relay traffic gets cross-domain correlation free.
Tor operates ~6,000–8,000 relays for scale.

**Enforcement is structural, not a check.** §10's relay identity hides the registrant's
`DyadId`, so `x/relay` *cannot* look up "is this a validator." The exclusion is therefore
built into the membership ring: the anonymity set is `attested_dyads \ active_validators`,
so a validator cannot produce a valid membership proof at all. A registration-time check
would be unimplementable — this is the same class of contradiction as §13 Q2.

### §9.2 Eligibility

Every bonded dyad is relay-*capable* (§1). Entry into the public pool additionally requires
an always-on host, public reachability, uptime above a threshold, no opt-out, and
non-membership in the validator set. **All of these are host properties the chain cannot
verify about an anonymous registrant** — see §13 Q2, which is the largest open problem in
this design and is not solved here.

### §9.3 `x/relay` — the chain module

A Vita-Chain module, sibling to `x/nullifier`.

```
relay/entry/{relay_id}         → RelayDirectoryEntry
relay/active/{epoch}           → [relay_id]
relay/registered_at/{relay_id} → height
```

- `RegisterRelay { entry, membership_proof, relay_nullifier }` — validators verify the
  proof and the nullifier's unseen-ness (§10.2), then admit.
- `RefreshRelay` / `RetireRelay` — re-attest before expiry; voluntary exit.

Rotation rides the **existing `x/nullifier` epoch beacon** (HYP-426) — one chain clock,
not a second. ⚠️ That beacon is advanced by a **single `epoch_authority` key**
(`nullifier.rs:61,130,653`) with `MIN_EPOCH_SPACING_BLOCKS = 1000`. Inheriting it means
one key gates when dead or revoked relays leave the active set. Tracked as §13 Q5;
decoupling is the likely fix.

Bounds: `MAX_RELAYS = 4096` (mirrors `reputation::MAX_RELAYS`); attestation validity
≤ `OBSERVATION_WINDOW_MS` (30 d); `MAX_REGISTRATIONS_PER_BLOCK` is **undetermined** and is
a validator-CPU DoS bound (§13 Q4).

## §10 Relay identity — the census defect and its fix

### §10.1 The defect

`RelayAttestation` publishes `relay_dyad_id`, `subnet_24`, and
`advertised_bandwidth_kbps` (`protocol-core/src/reputation/attestation.rs:57-78`). Under
§1's default-ON rule that makes the directory a **complete public census**: who exists,
roughly where, and how large their connection is.

**Required spec amendment (not a citation).** THREAT_MODEL §5 enumerates seven properties
— content, identity, relationship, timing, volume, future secrecy, and introduction
rate-limiting. **None of them covers this**, and an earlier draft of this design cited a
non-existent "participation-unobservability" property rather than noticing the gap.
Closing it requires *adding* an eighth property to THREAT_MODEL — participation secrecy,
scoped to Tier-1/Tier-2 adversaries — and that amendment is a work item of HYP-168, not a
preamble to it.

### §10.2 The fix — a nullifier-bound relay identity

A relay registers under `relay_id`, an identity key generated independently of its
`DyadId` and not derivable from it. Uniqueness is enforced by a **nullifier**, reusing the
n-times machinery already shipped (HYP-415/426/472):

```
relay_nullifier = PRF_credential("relay", slot_index),  slot_index ∈ [0, N_RELAY_MAX)
```

The registrant proves in ZK that it holds a bonded-dyad credential and that
`relay_nullifier` is correctly derived from it; `x/nullifier` rejects a repeat. One dyad
therefore claims at most `N_RELAY_MAX` relay slots, network-globally.

**Why not SPRING.** An earlier draft proposed proving membership with SPRING (HYP-317).
That is unsound here: SPRING is a plain one-of-many ring signature with **no key image,
tag, or nullifier** (verified — zero hits in `spring_scheme.rs` / `spring_acc.rs`), so two
proofs from the same ring member are indistinguishable *by design*. One dyad could mint
`MAX_RELAYS` identities at the cost of proof computation. SPRING's unlinkability is
exactly the property that makes it wrong for this job; the nullifier's linkable-tag is
exactly the property that makes it right.

### §10.3 `relay_id` is a stable pseudonym, and that is deliberate

`slot_index` carries **no epoch**, so `relay_id` is stable for the relay's lifetime. This
is required — §11 accrues reputation to it, and an identity that rotated per epoch would
reset its reputation to zero every epoch and never become selectable.

The cost, stated plainly: a stable pseudonym is linkable **to itself** across time, so a
relay's behavior can be profiled longitudinally. It never links to a `DyadId`. Tor has the
same property (relay fingerprints are stable) and it is the accepted price of reputation.

Consequence: registration is effectively permanent, so **revocation needs a mechanism of
its own** — retiring a `relay_id` must not free the nullifier for reuse, or the Sybil
bound leaks. `RetireRelay` marks the entry dead; the nullifier stays spent.

## §11 Two-tier reputation (replaces the §4 "scores 0" rule)

Josh's call, 2026-08-01. Two tiers exist, but **tier is not a selection input** — both land
in one pool under one score. The tier affects only how the score is *seeded*:

```
score(R) = ( w_vouch·P_trust(R) + n_obs(R)·B(R) ) / ( w_vouch + n_obs(R) )
```

- **Anonymous tier** — `w_vouch = 0`. Scored purely on observed behavior `B(R)`
  (delivery + uptime + attestation freshness). At `n_obs = 0` the score is a **non-zero
  neutral prior**; it must be non-zero or §4's repealed rule reappears and the tier is
  never selected.
- **Vouched tier** — a dyad *opts in* to publishing its `relay_id ↔ DyadId` link, gaining
  a pair-bond PageRank prior `P_trust(R)` with pseudo-count `w_vouch`.

**The vouch is a cold-start prior, not a permanent multiplier.** As `n_obs → ∞` both tiers
converge to `B(R)`: a vouched and an anonymous relay with identical observed behavior end
at identical scores. This is what prevents the failure mode that kills naive two-tier
designs — if vouched relays scored permanently higher, paths would skew vouched, the
anonymous pool would starve, and choosing privacy would be self-defeating. Here the
advantage decays to zero.

**Honest limits.**
1. While `n_obs < w_vouch` a vouched relay *is* preferred. That window is real; bounding it
   is what makes `w_vouch` load-bearing (§13 Q1).
2. Vouching publishes that dyad's link — a census of the opt-in subset. That is an informed
   sovereign trade, and it is **not revocable in retrospect**: dropping to anonymous stops
   new disclosure but cannot unpublish history.
3. `w_vouch` and the neutral prior are **not yet derived**. They MUST come from the measured
   circuit rate against `OBSERVATION_WINDOW_MS`, not be chosen because they look reasonable
   (rule #2).

## §12 Directory distribution and the epistemic constraint

**Normative:** every client selects from the identical, full, consensus directory. No lazy
fetch, no per-client subsets, no fetching only the relays a client intends to use.

[Danezis & Syverson, PETS '08](https://link.springer.com/chapter/10.1007/978-3-540-70630-4_10)
prove two attacks on clients holding partial network knowledge: **route bridging**
(exploiting what a client does *not* know) and **route fingerprinting** (a client's
idiosyncratic view of the relay set identifies it across circuits). This is the decisive
argument for a chain-backed directory over gossip — consensus supplies view-consistency as
a property rather than a hope.

**⚠️ The size budget does not currently close.** Per-entry, with real constants:

| Field | Bytes |
|---|---|
| `relay_id` · `x25519_pk` | 64 |
| `ml_kem_pk` (ML-KEM-768) | 1,184 |
| `signing_pubkey` (`HybridPubkey`: Ed25519 + ML-DSA-65 vk) | ~1,984 |
| `signature` (`HybridSig`: Ed25519 + ML-DSA-65) | ~3,373 |
| bandwidth · subnet · validity | 15 |
| **per entry** | **≈ 6,620 B** |

At `MAX_RELAYS = 4096` that is **≈ 27 MB** — 13.5× Tor's ~2 MB consensus, and 27% of a
dyad's 100 MB/day cellular `CostClass::Bandwidth` cap. Per COVER_TRAFFIC §5.4, exhausting
that budget **suspends cover traffic**, so a naive directory sync would buy down the very
property the relay layer exists to serve.

The PQ *signature+key* pair is 81% of the entry — ML-KEM is only 18%, so compression aimed
at the KEM key is aimed at the wrong field. Selective fetch is **forbidden** by the
epistemic constraint above, which leaves: diff/delta sync against a held baseline,
aggregate signatures over the entry set rather than per-entry, or a smaller `MAX_RELAYS`.
**Unresolved — §13 Q6, and it gates the whole design.**

## §13 Open questions

1. **Q1 — `w_vouch` and the neutral prior.** Must be derived from measured circuit rate vs.
   `OBSERVATION_WINDOW_MS`. Sets how long the vouched tier keeps its edge.
2. **Q2 — capability gates against an anonymous registrant.** Uptime, always-on, and
   reachability are host properties the chain cannot verify about a `relay_id` it cannot
   identify; a fresh `relay_id` has zero uptime by construction. **The largest open problem
   here.** Candidate direction: prove capability to the *observing* clients over time
   rather than to the chain at registration — i.e. move the gate from §9.2 into §11's `B(R)`.
3. **Q3 — what default-ON costs.** §1's reversal from opt-in was not costed. Chiefly: relay
   forwarding and cover traffic share one `BandwidthBudget`
   (`vita-carriers/src/cover_traffic/relay_padding.rs:12`), so an unauthenticated remote
   adversary can drain a relay's budget and **suspend that dyad's cover traffic**
   (COVER_TRAFFIC §5.4). Default-ON converts a self-limited resource into an
   adversary-controlled one for every capable dyad. §6.1 already flags the shared budget as
   "the one genuine architecture question"; default-ON makes it a security question.
4. **Q4 — `MAX_REGISTRATIONS_PER_BLOCK`.** Each registration carries a ZK verification;
   unbounded registration is a validator-CPU DoS.
5. **Q5 — decouple relay rotation from the single-key `epoch_authority`.**
6. **Q6 — the 27 MB directory.** Gating. Diff sync vs. aggregate signatures vs. smaller
   `MAX_RELAYS`.
7. **Q7 — cross-spec conflict, unresolved.** §4's selection contract says a short pool
   "builds shorter"; CIRCUIT_LIFECYCLE §21.1 mandates constant-length 5-hop routes with
   decoy padding so hop count is invisible. These contradict. Not resolved here — flagged
   rather than silently decided.
8. **Q8 — bootstrap.** Below ~50 relays the anonymity set is weak regardless of design.
   **Population is the unsolved problem**: Tor's 6–8k relays took ~20 years of volunteers;
   Nym and Oxen buy theirs with tokens. §1's default-ON makes relay count track dyad count,
   which is the right structural answer, but early anonymity is weak in proportion to early
   adoption and no amount of correct code changes that. Product decision, Josh's call.

## §14 Sybil resistance

A relay slot requires a bonded-dyad credential (§10.2), and bonded dyads are bounded by the
pair-bond ceremony plus the n-times introduction cap — `N_MAX = 8` per (introducer, epoch),
enforced network-globally by `x/nullifier` since HYP-426/472. With §10.2's nullifier
binding, relay-Sybil cost is genuinely dyad-Sybil cost. Structurally this is the
social-graph + stake hybrid of [SybilQuorum](https://arxiv.org/pdf/1906.12237).

**Limits, stated rather than glossed:**
1. **The cap bounds rate, not total.** An adversary growing a large bonded subgraph over
   many epochs — real humans, paid or coerced — gets proportional relay share.
2. **The argument requires §10.2.** Without the nullifier binding it is false, not weak:
   §10.2 explains why the SPRING variant permitted unbounded identities from one dyad.
3. **Social-graph defenses need real operator trust.** SybilGuard/SybilLimit-class arguments
   fail where operators have no prior trust relationship. This design is in the regime where
   they work *only because* relays are drawn from bonded dyads. Relax §1 to open enrollment
   and this section is void.
4. **Self-attested diversity is not a defense.** `operator_id` and `subnet_24` are
   self-asserted fields of a self-signed record (`attestation.rs:76-78`) and `is_diverse`
   (`guards.rs:386-391`) compares them literally, so one host can fabricate three and own
   all three of a victim's guards. §10.2 bounds *how many* identities, not what they claim.
5. **Forensics beats prevention, empirically.**
   [Winter et al.](https://arxiv.org/pdf/1602.07787) found real Sybil groups in Tor's HSDir
   and exit positions; manual vetting and per-IP caps did not stop them. Detection worked on
   uptime correlation, config fingerprinting, and IP clustering. `ObservationWindow` is the
   right host for the same forensics. Not built — follow-up, not claimed as solved.

---

| Version | Author | Notes |
|---|---|---|
| 2026-08-01 v0.3 | Iris + Josh | **§9–§14 (HYP-168): the relay directory.** Fills the `eligible_relay_pool` seam §4 and `guards.rs:14` both name. §9.1 role-separation law (chain = directory, never relay; validators excluded structurally via the membership ring, since §10 makes a registration-time check unimplementable). §1 flipped opt-in → **default-ON capability-gated** (Josh) so anonymity tracks adoption; §13 Q3 costs the reversal. §10 fixes the census defect — `relay_id` bound by a **nullifier** reusing HYP-415/426/472, *not* SPRING (verified: no key image/tag, so one dyad could mint `MAX_RELAYS` identities). §11 **two-tier reputation** (Josh) repeals §4's "no trust path scores 0", which would have made every anonymous relay unselectable and no circuit buildable; the vouch is a decaying cold-start prior so the anonymous pool cannot starve. §12 Danezis–Syverson forces full-consensus fetch — and surfaces that the directory is **~27 MB, unresolved (Q6, gating)**. §14 states five real limits. Prior v0.3 draft (`RELAY_DIRECTORY.md`, cfdd951e) was cross-vendor refuted — 3 P1 confirmed — and is deleted; its surviving material is folded in here. |
| 2026-06-12 v0.2 | Iris + Josh | Detailed §7 bridge tunnels into a concrete, implementable protocol over EXISTING primitives (§7.1 pre-introduction = circuit-kex-style X25519+ML-KEM agreement; §7.2 bridge table + `bridge_tunnel` rotating id, built; §7.3 enforced carrier diversity) — no new crypto; replaces the v0.1 "deferred to kickoff" stub. |
| 2026-06-12 v0.1 | Iris + Josh | Phase 3 kickoff spec. Consolidates the relay layer (referencing CIRCUIT_LIFECYCLE/SEALED_ENVELOPE/OUTFOX/COVER_TRAFFIC) + specs the two new pieces it owns: relay-relayed cover (§6, HYP-321) + bridge tunnels (§7, HYP-323). Built on the just-completed §20 web-of-trust relay-reputation/attestation/selection layer. |
