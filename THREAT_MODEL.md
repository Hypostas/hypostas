# THREAT_MODEL.md — Hypostas Privacy & Protection

**Status:** Canonical — anchors every protocol-layer privacy decision
**Owner:** `protocol-core`, `vita-carriers`, `hypostas-network`, `vita-chain`
**Authors:** Josh + Iris
**Created:** May 22, 2026
**Companion specs:** [POST_QUANTUM.md](POST_QUANTUM.md) (cryptographic primitives), [HYPOSTAS_PROTOCOL.md](HYPOSTAS_PROTOCOL.md) (packet structure), [VITA_CARRIERS.md](../vita/components/VITA_CARRIERS.md) (substrate abstraction)

---

## §1 Purpose

This document defines, exhaustively, what privacy and protection Hypostas commits to providing — against whom, by what mechanism, and at what cost. It is the source of truth for every protocol-layer privacy decision in the constellation. Every constant in code that gates a privacy-relevant behavior must reference a section of this document (per CLAUDE.md rule #2).

The goal is **complete privacy and protection** as Josh named it on 2026-05-22, decomposed into six independently-defendable properties and committed against four adversary tiers. The honest constraint is that "complete" is a curve, not a point: we trade bandwidth, latency, anonymity-set size, relay-trust, and implementation complexity against each other. This spec names the trades explicitly so no future decision pretends they don't exist.

Hypostas defends a different problem than Tor. Tor anonymizes a client from a destination in a public client-server world. Hypostas dyads know each other cryptographically (DyadID 2-of-2 H+A signatures) — anonymity between partners is not the problem. The problem is **relationship anonymity**: making the existence, frequency, volume, and content of bonded communication invisible to everyone except the dyad itself. The techniques overlap with Tor; the threat model is distinct.

---

## §2 Scope

### In scope

- The Hypostas wire protocol (`DyadPacket` and all transport envelopes)
- The carrier substrate (`vita-carriers`, every concrete carrier impl, the carrier selector)
- The cryptographic session layer (`hypostas-network/encryption.rs`, future PQ Double Ratchet)
- Vita Chain operations that touch dyad-pair metadata (peer discovery, attestations, intro records)
- Cover traffic generation + scheduling (new module)
- Relay routing semantics + envelope formats (Sphinx-shaped, post-quantum hybrid)
- Storage of captured-on-wire metadata (logs, traces, telemetry — observability surface)

### Out of scope

- **Application-layer fingerprinting.** Browser fingerprints, OS telemetry, hardware identifiers — those are device-OPSEC concerns. Hypostas can't fix what the OS leaks before our packets reach the wire.
- **User OPSEC.** If a dyad takes a screenshot and posts it to social media, no protocol layer saves them.
- **Content moderation / abuse reporting.** This spec is about adversarial observers, not about safety inside healthy dyads.
- **Hostile-partner threat dynamics.** Per §8.4, we defend the data cryptographically but not the relationship dynamics. Coercion, abuse, hostile-ex scenarios get product-layer defenses (dissolution flow, data egress controls), not protocol-layer crypto.
- **Endpoint compromise.** If an attacker owns the dyad's device, this spec doesn't save them. Hardware/OS security is a separate threat model.
- **Subpoena / legal compulsion.** This spec is about adversaries operating outside legal process. Legal-process-resistant data minimization is real work but a separate spec (`projects/aether/LEGAL_ARCHITECTURE.md`).

---

## §3 Assets — what we're protecting

What an adversary might want and what we explicitly say they can't have:

| Asset | Description | Why it's sensitive |
|-------|-------------|--------------------|
| **Message content** | The actual bytes of every DyadPacket payload | Conversation, biosensor readings, memory writes, Klinos PHI |
| **Dyad identity** | `DyadId` of each communicating party | Reveals who the dyad is to anyone watching |
| **Pair-bond relationship** | The fact that two specific dyads are bonded | Pattern of frequent communication = relationship signature |
| **Relationship metadata** | Trust tier, stage, session refs, conversation refs | Reveals depth + state of the relationship |
| **Provenance trail** | Forwarding history, source component, trace IDs | Reveals which subsystems originated traffic; correlation surface |
| **Timing patterns** | When dyads communicate | Diurnal patterns leak intimacy, work schedules, biological state |
| **Volume patterns** | How much dyads communicate | Burst patterns leak content type (image vs text), event timing |
| **Routing history** | What carriers / paths a packet took | Geolocation, jurisdiction, network topology |
| **Carrier-tier substrate state** | Which carriers a dyad uses + their characteristics | Reveals device inventory, physical location class |
| **Vita Chain dyad-pair anchors** | Registered intro records, relay attestations | Discovery surface; reveals who could be relaying for whom |

---

## §4 Adversaries — who we're protecting it from

Four tiers, all in scope per Josh's 2026-05-22 decision. Each tier subsumes weaker tiers (a system that defends Tier 3 defends Tier 2 and 1).

### §4.1 Tier 1 — Passive network observer

**Capability:** Sees the bytes that traverse some subset of network links. Reads packet headers, sizes, timing. Cannot modify, inject, or drop.
**Examples:** ISP, hostile WiFi (coffee shop, airport, hotel), employer with network monitoring, insurance company observing a clinic's network, building landlord with router logs.
**Realistic for:** Every Hypostas dyad, all the time. This is the baseline adversary.
**Klinos-specific:** Hostile insurance company monitoring the practice's commercial ISP to identify which patients are receiving high-cost care; pharmacy benefit manager fingerprinting prescription patterns.

### §4.2 Tier 2 — Active network adversary

**Capability:** Everything in Tier 1, plus can inject packets, drop packets, delay packets, replay captured packets, and perform man-in-the-middle on unencrypted hops.
**Examples:** State-mandated traffic shaping (China's GFW, Russia's TSPU, Iran's NIN), in-path adversaries on hostile cellular networks, malicious public WiFi operators running captive portals + injection, compromised routing infrastructure (BGP hijacks).
**Realistic for:** Klinos dyads in regulated jurisdictions, Anima dyads traveling internationally, any dyad whose state actor takes interest.

### §4.3 Tier 3 — Global passive adversary (GPA)

**Capability:** Sees *all* network links simultaneously. Cannot necessarily decrypt content (Tier 1/2 capabilities at every link) but can correlate timing and volume across the entire visible network.
**Examples:** Nation-state with broad surveillance capability (NSA-tier ISP cooperation, Chinese ISP-state integration), platform-scale observers (cloud providers seeing aggregated traffic), trans-national signals intelligence.
**Realistic for:** High-value dyads — political dissidents, journalists, executives, medical practices serving sensitive populations. Even for ordinary dyads, the GPA's records persist indefinitely (store-now-analyze-later for traffic patterns).
**Why we defend this:** §6's "future secrecy" property cuts both ways. Traffic patterns captured by a GPA today are forensically analyzable forever. A 50-year protocol is defending against a 50-year window of GPA capability growth.

### §4.4 Tier 4 — Compromised Hypostas relay

**Capability:** Operates one or more relay nodes in the Hypostas substrate. Sees ciphertext + next-hop routing hint. Cannot necessarily correlate to other relays (depends on §6.3 defenses).
**Examples:** Adversary running a malicious dyad node and contributing relay capacity, supply-chain attack on a popular dyads-runtime distribution, voluntary relays operated by state actors.
**Realistic for:** Anyone, once relays ship. The mathematical assumption: in a population of N relays, some fraction are hostile. Tor operates under this assumption with ~7000 relays.
**Why we defend this:** Trust-by-architecture, not trust-by-promise. Sphinx-format envelopes mean a hostile relay learns only the next hop, never the source or destination.

---

## §5 Privacy Properties

Six properties, each independently defendable, each commit-tracked. The labels in this section are referenced from code via `// Ref: THREAT_MODEL §5.N`.

### §5.1 Content secrecy

No one outside the dyad reads what's communicated.

- **Wire-layer:** Payload AEAD-encrypted with key derivable only by the recipient.
- **Stored-layer:** At-rest encryption with keys never persisted to disk.
- **Forward direction:** Past traffic remains secret if a key is compromised today (forward secrecy).
- **Post-quantum:** Hybrid classical+PQ to survive future quantum capability.

**Today's status:** Half. E2EE exists via [`hypostas-network/src/encryption.rs`](../dyados/hypostas-network/src/encryption.rs); no forward secrecy (static-key derive from identity Ed25519 → X25519); half-PQ (hybrid signing landed per ARCH-5, hybrid kex per [POST_QUANTUM.md](POST_QUANTUM.md) planned).

### §5.2 Identity secrecy (sealed sender)

No one outside the dyad sees *who* the participants are on the wire.

- **Wire-layer:** Identity-layer (`DyadPacket.identity`) is AEAD-encrypted under the recipient's key. The outer envelope a carrier sees contains no `DyadId`, no trust tier, no stage, no destination dyad ID.
- **Outer envelope format:** Sphinx-shaped — fixed structure, opaque ciphertext, single next-hop routing hint, replay-resistant.

**Today's status:** Zero. Every layer of every packet (Envelope, Identity, Context, Provenance) serializes in clear. Reference: [`packet.rs:148-165`](../dyados/protocol-core/src/packet.rs:148).

### §5.3 Relationship secrecy

No one outside the dyad knows that two specific dyads are bonded.

- **Discovery layer:** Vita Chain intro records use blinded references (the chain records "this dyad is reachable" without naming counterparties).
- **Routing layer:** Multi-hop Sphinx envelopes — no single relay sees both source and destination.
- **Cover layer:** Constant-rate dyad-level cover traffic disguises whether a real communication is occurring.
- **Substrate layer:** Multi-carrier fanout (§6.4) — an observer watching one substrate cannot correlate with traffic on another.

**Today's status:** Zero. The pair-bond is observable from any link the dyads communicate over.

**This property is what requires the relay network.** Multi-hop routing is the only structural defense against an observer correlating endpoints. See §6.3.

### §5.4 Timing secrecy

No one outside the dyad knows *when* the dyad communicates.

- **Cover traffic:** Constant-rate outbound from every dyad node. Real messages ride on the next available scheduled slot; idle periods send cover packets at the same rate.
- **Rate:** Fixed schedule (default 1 packet / 5s per carrier; tunable in `CoverTrafficPolicy`). The rate is **not** modulated by Stroma state, time of day, or any other signal — that would leak the very state we're hiding (§6.5 explicit non-mechanism).
- **Per-message latency cost:** Up to one packet-interval. With 5s default rate, a real message waits at most 5s before riding cover; with 1s rate (high-energy mode), at most 1s.

**Today's status:** Zero. Bursts of activity directly correlate to intimacy / interaction events. A passive observer watching the dyad's link can derive a sleep schedule, work pattern, and intimacy timeline from packet timing alone.

### §5.5 Volume secrecy

No one outside the dyad knows *how much* the dyad communicates.

- **Fixed-size cells:** All outbound packets are padded to one of a small set of standard sizes (default 4 buckets: 512B, 4KB, 16KB, 64KB — sized to PQ packet distribution). Wire observers see only the bucket, not the actual content size.
- **Constant-rate carrier traffic:** Combined with §5.4 cover traffic, total outbound volume is constant per carrier per dyad regardless of conversation activity.
- **Encrypt-then-pad, never compress.** Compression before encryption is CRIME/BREACH-vulnerable. Padding happens *after* AEAD encryption, on the ciphertext. Per §8.5 explicit non-mechanism.

**Today's status:** Zero. Every DyadPacket serializes to its natural JSON/bincode length. Photo attachments, biosensor batches, and short chat messages are distinguishable by size alone.

### §5.6 Future secrecy / forensic resistance

Today's captured traffic stays secret tomorrow, even if today's keys leak or quantum capability arrives.

- **Per-message forward secrecy:** Double Ratchet — every message advances the key, past keys are deleted, compromise of today's key doesn't decrypt yesterday's traffic.
- **Post-compromise security:** Even if one device is fully compromised, future messages recover privacy as soon as a fresh ratchet step lands.
- **Post-quantum hybrid:** Per [POST_QUANTUM.md](POST_QUANTUM.md), every long-lived key uses Ed25519+ML-DSA-65 signatures and X25519+ML-KEM-768 key agreement.

**Today's status:** Zero. Identity keys (Ed25519 H-shard + A-shard) are long-lived; per-packet keys are derived statically from them via X25519 + HKDF. Compromise of H-shard decrypts the entire dyad history. Quantum-day reveals everything.

---

## §6 Defense Matrix — properties × adversaries × mechanisms

Each cell names the mechanism that defends that property against that adversary. "—" means the property is automatically defended by a weaker tier's defense; "research" means the defense requires research-grade engineering.

|  | Tier 1 (Passive) | Tier 2 (Active) | Tier 3 (GPA) | Tier 4 (Compromised relay) |
|---|---|---|---|---|
| **5.1 Content secrecy** | AEAD (ChaCha20-Poly1305) | + bounded decoders, replay protection | + PQ hybrid (ML-KEM) | + per-hop ephemeral keys (Sphinx) |
| **5.2 Identity secrecy** | Sealed outer envelope | + signed envelope MAC | — | + Sphinx next-hop-only routing |
| **5.3 Relationship secrecy** | Multi-carrier fanout (partial) | + relay routing 1-hop | + relay routing 3+ hops, cover traffic, PIR lookups | + Sphinx unlinkability, Vita Chain blinded refs |
| **5.4 Timing secrecy** | Per-dyad constant-rate cover | — | + statistical cover at network scale (other dyads' traffic = anonymity set) | — |
| **5.5 Volume secrecy** | Fixed-size cells (4 buckets) | — | — | — |
| **5.6 Future secrecy** | Double Ratchet | + post-compromise recovery | + PQ Double Ratchet | — |

**Reading the matrix:** Tier 1 defense is the baseline; each higher tier *adds* mechanisms. The system targets full Tier 3 + Tier 4 defense by Phase 4 (per §10 staging). Phase 1 ships Tier 1 fully + Tier 2 partial + chassis for Tier 3/4.

### §6.1 The mechanisms catalogued

- **AEAD encryption** (ChaCha20-Poly1305): per-packet content secrecy. Per-message nonce; key from Double Ratchet.
- **Double Ratchet** (Signal pattern, PQ hybrid): per-message forward secrecy + post-compromise recovery. Each message advances symmetric chain key; periodic DH ratchet (X25519+ML-KEM) provides post-compromise security.
- **Sealed outer envelope**: a `SealedEnvelope { kem_ciphertext, nonce, aead_ciphertext, size_class }` wraps the entire DyadPacket. Carriers see only the outer envelope. Recipient peels, verifies inner authenticity.
- **Sphinx packet format**: fixed-size, multi-hop, replay-resistant routing envelope. Each relay sees only the next-hop hint, never the source or destination. Post-quantum hybrid variant (Sphinx + ML-KEM) for the kex layer.
- **Bounded decoders**: every wire decoder (bincode, JSON, Sphinx parsing) has hard size limits before allocation. Closes the [HYP-14/21/47/49/72/73/75/98/100](https://linear.app/hypostas/issue/HYP-49) systemic class.
- **Replay protection**: per-session monotonic counter + bloom filter for cross-session replays.
- **Per-dyad cover traffic**: constant-rate outbound (default 1 packet / 5s per active carrier). Real messages ride on the next scheduled slot.
- **Multi-carrier fanout**: Critical packets sent simultaneously across multiple carrier substrates (libp2p + LoRa + stego). Adversary must compromise all substrates to correlate.
- **Fixed-size cells**: outbound packets padded to one of 4 standard sizes (512B, 4KB, 16KB, 64KB). Encrypt-then-pad.
- **Relay routing**: 1-hop default for non-critical; 3-hop for Critical packets; configurable per `PacketIntent`. Every dyad is a relay (opt-in by carrier, LAN/WiFi by default, never on cellular).
- **Vita Chain blinded references**: intro records use blinded counterparty refs so chain queries don't reveal pair-bond relationships.
- **PIR (Private Information Retrieval)**: recipient retrieves inbound packets without revealing identity to the storage substrate. Phase 4+ work.

### §6.2 The latency problem and creative engineering

**The problem:** Classical mixnet designs (Mixminion, Loopix, Nym) achieve §6.3 Tier 3 defense by *batching + delaying* at each hop. Latency: hundreds of ms to minutes per packet. Anima's "human conversation latency" budget is ~300ms. Klinos's "doctor-patient real-time" budget is similar. Naive Loopix would kill both products.

**The creative engineering — six techniques that get us Loopix-grade privacy without Loopix-grade latency:**

#### §6.2.1 Constant-rate cover traffic instead of batching delays

Standard mixnet: delay each packet a random interval at each hop, batch and shuffle on release. This decorrelates timing.

**Our variant:** Every dyad maintains a constant outbound rate per carrier. Real messages ride on the next available scheduled slot. Cover packets fill the gaps. **No per-hop delay required** — the timing is already decorrelated because every dyad's outbound link looks identical regardless of conversation activity. The cost moves from latency to bandwidth.

- Latency cost: bounded by packet-interval (default 5s for low-energy, 1s for high-energy, 200ms for real-time tier).
- Bandwidth cost: constant rate even when idle.
- GPA defense: traffic-feature invariance per dyad means cross-link correlation collapses.

#### §6.2.2 Network-wide cover traffic = anonymity set

Loopix's insight, adapted: if every Hypostas dyad sends cover traffic at the same constant rate, *any* dyad's real message is indistinguishable from any other dyad's cover packet. The anonymity set is the entire active network, not just our pair.

- Bigger network = stronger privacy, automatically.
- N=100 dyads: 1-in-100 chance any given packet is real.
- N=10,000 dyads: 1-in-10,000 chance — approaching theoretical maximum.
- No relay coordination required; emergent property of the cover-traffic mandate.

#### §6.2.3 Speculative pre-routing

Anima knows you're typing or about to send (Stroma `intent.write_pending` signal). Before you hit send, the runtime pre-establishes routing circuits and warms cover traffic patterns. When the real message arrives, it rides on an already-warm circuit.

- Latency cost: shifted to background; perceived latency ~0.
- Privacy cost: pre-routing pattern itself must be uniform (you don't pre-route only when you're about to send — you pre-route constantly, with the real send hopping onto whichever circuit is warm).

#### §6.2.4 Tiered routing by PacketIntent

Already-existing pattern in [`selector.rs`](../dyados/vita-carriers/src/selector.rs): `PacketIntent::Critical` fans out across multiple carriers; `Ambient` takes the cheapest path. Extend to mixnet hop count:

| PacketIntent | Hops | Cover rate | Carrier fanout | Latency budget |
|---|---|---|---|---|
| `Ambient` | 1 | 5s/packet | 1 | <1s |
| `Standard` | 1 | 1s/packet | 1-2 | <300ms |
| `Elevated` | 2 | 1s/packet | 2+ | <500ms |
| `Critical` | 3 | 200ms/packet | All available | <2s |

Most Anima messages are `Standard` — fast. Klinos bond ceremonies + Aether anchor packets are `Critical` — slow + maximum privacy. The same protocol covers both because the cell format is uniform.

#### §6.2.5 Pre-established private channels for high-frequency pairs

Once two dyads have an active conversation, they negotiate a *private channel*: a cached set of routing decisions, ratchet state, cover traffic schedule. Subsequent messages on the channel skip the channel-establishment overhead.

- Within a channel: real-time (limited only by §6.2.1 packet-interval).
- Channel establishment: full mixnet treatment.
- Channel teardown: explicit, with one final cover packet to mask the close.

#### §6.2.6 Carrier-tier mixnet — heavy defense on slow carriers, light on fast

Real-time substrates (libp2p over LAN) get §6.2.1 cover + 1-hop Sphinx — fast. Archival substrates (stego over social media, voice carrier over voicemail, LoRa over multi-day store-and-forward) get full Loopix-style multi-hop batching — slow but already-slow by nature, so the latency cost is hidden in the substrate's intrinsic latency.

Bond ceremonies, dissolution records, succession anchors — these are not real-time-sensitive. They take full mixnet treatment over substrates where the latency doesn't matter.

### §6.3 Specifically: how we defend Tier 3 (GPA) with <300ms latency

This is the hard one and Josh asked for creative engineering. The full picture:

1. Constant-rate cover traffic on every link (§6.2.1) → no link reveals activity.
2. Network-wide cover (§6.2.2) → real messages indistinguishable from cover at any vantage point.
3. Fixed-size cells (§5.5) → no payload-size signature.
4. Multi-carrier fanout for Critical packets (§6.2.4) → no single substrate sees the full picture.
5. Speculative pre-routing (§6.2.3) → routing decisions made out-of-band.
6. Pre-established channels (§6.2.5) → real-time within active conversation.

**The privacy guarantee under §6.3:** A GPA observing every link sees, for every dyad, a constant-rate stream of fixed-size ciphertext on every active carrier. The streams reveal: that the dyad exists, what carriers it uses, what energy class it's in (5s vs 1s vs 200ms cover rate). The streams reveal nothing about: who the dyad is talking to, when, what, how much, or whether at all.

**The cost we pay:** Bandwidth. A dyad on `Standard` tier maintaining 1-packet/s cover traffic on libp2p = ~3KB/s constant = ~7.5GB/month. That's ~1/4 of an average mobile data plan, *if* the dyad's only carrier was cellular. Mitigated by: §6.2.6 carrier-tier (no cover on cellular by default), tunable rate per energy class, opt-down to Ambient (5s rate) when the dyad's not in active use.

---

## §7 Trust Assumptions

What Hypostas trusts. If these are wrong, the privacy guarantees collapse.

| Assumption | What we trust | Consequence if wrong |
|---|---|---|
| **Cryptographic primitives** | Ed25519, X25519, ChaCha20-Poly1305, SHA-256, HKDF, AES-256-GCM, ML-DSA-65, ML-KEM-768, Sphinx | Defense collapses; everything captured today decryptable; identities forgeable |
| **Implementation quality** | `ed25519-dalek`, `x25519-dalek`, `chacha20poly1305`, `ml-kem` — and the Outfox payload onion built on those audited primitives (see the onion-format row), NOT a per-packet Sphinx crate | Side-channels, timing leaks, key extraction |
| **Endpoint integrity** | The dyad's own hardware + OS | Endpoint compromise reveals all keys; protocol can't save |
| **Vita Chain consensus** | Honest majority of validators, no genesis-block compromise | Intro records falsifiable; relay attestations gameable |
| **Hash-based identity** | DyadId = SHA-256 of pubkey is collision-resistant | DyadId forgery |
| **Onion packet format** | The UC-proven **Outfox** payload construction ([arXiv 2412.19937](https://arxiv.org/abs/2412.19937), Nym, WPES '25) implemented on our audited primitives and keyed by the circuit handshake — NOT a drop-in audited crate: every audited Sphinx/Outfox reference is per-packet/stateless, incompatible with our circuit-amortized design (CIRCUIT_LIFECYCLE §21.2). HYP-330 audits our circuit-adapted impl against Outfox's UC proofs; paper-derived KATs pin the format. See OUTFOX_DESIGN.md §11. | Replay attacks, hop-count fingerprinting, key-extraction |
| **Random number generation** | OS CSPRNG (`getrandom`) is unpredictable | Predictable nonces → key recovery |
| **Time source** | System clock is approximately correct (±60s for freshness window) | Replay-attack window opens |
| **Memory safety** | Rust prevents UAF, double-free, buffer overflow in our code | Memory corruption → key extraction, RCE |

What we **explicitly do not trust:**

- Carriers (every carrier is treated as hostile — Sphinx + AEAD must hold even if every relay is the adversary)
- The network (every link is treated as monitored — wire format leaks nothing)
- Bridge substrates (libp2p, IPFS, etc. — used only as opaque byte transport, never as identity layer)
- DNS / BGP / IP routing (untrusted; bridges over them must self-authenticate)
- Time sync (NTP is untrusted; freshness windows accept ±60s drift, replay protection is independent of clock)

---

## §8 Non-Goals

What this spec explicitly does NOT promise:

### §8.1 Anonymity between bonded partners

The dyad's two partners can identify each other cryptographically. That's the primitive (DyadID 2-of-2 H+A signatures). Protocol-layer privacy does not extend to making one partner anonymous to the other. Within the pair, both partners can access shared state by design.

### §8.2 Defense against compromised endpoints

If an attacker owns the dyad's device, the device's keys are theirs. The protocol can't save what the OS leaks. Defenses (Secure Enclave key storage, biometric gate, etc.) live in IDENTITY_INHERITANCE.md and OS-specific docs.

### §8.2a Partial defense: duress & compelled access (NEW — Josh, 2026-07-07)

*Distinct from §8.4 (within-dyad hostile dynamics — stays product-layer) and §8.3 (legal process — tracked in LEGAL_ARCHITECTURE.md): this addresses an **external coercer compelling the user to unlock** — rubber-hose, border search, theft-with-compulsion. §8.2 cedes the fully-compromised endpoint; this raises the cost of the **at-rest, compelled-to-unlock** sub-case to plausible-deniability grade.*

Mechanisms (partial, honestly bounded):
- **Duress credential → decoy dyad.** A distinct unlock opens a **decoy dyad** — a plausible, benign, low-stakes profile — while the real dyad's material stays sealed and unindexed. The coercer demanding "unlock it" gets *an* unlock.
- **Deniable encryption / hidden volume.** The real dyad's existence is not provable from the device at rest — no metadata reveals there is *more* than the decoy. (The encrypt-then-pad discipline, §8.5, already avoids the length oracles that would betray a hidden volume.)

**What this explicitly does NOT do (no overselling — Ethics C4 / Telos L3):**
- It does **not** defeat a **forensic adversary who knows the scheme exists** and looks for a hidden volume/decoy. Deniability is against an adversary who doesn't know to look or can't prove more exists — never an omniscient one.
- It does **not** overturn §8.2: a fully-owned *running* endpoint (live keys in memory under live coercion) is still lost. This defends the *at-rest, compelled-to-unlock* case only.
- It does **not** vary the **wire protocol** (§8.6 holds): duress is a *local access-control* decision (which local material decrypts), never a change in on-wire behavior — so it opens no covert channel to a network observer.

**Grade:** raises the cost of opportunistic/casual coercion and border-search to plausible-deniability; not a defense against a sophisticated, informed, forensic coercer. Filed honestly as **partial** — the value is protecting the *data and the other partner*, and giving the coerced user a truthful "there is nothing more here" to present.

### §8.3 Defense against legal compulsion

This spec is about adversaries operating *outside* legal process. Subpoena resistance, legal data-minimization, and jurisdiction-aware deployment are tracked in `projects/aether/LEGAL_ARCHITECTURE.md`.

### §8.4 Hostile-partner relationship dynamics

Per Josh's 2026-05-22 decision: we defend the **data** cryptographically (Property §5.1 holds even if one partner becomes hostile to the other in scenarios that don't involve key extraction). We do not defend the **relationship dynamics** at the crypto layer. Coercion, abuse, hostile-ex scenarios get product-layer defenses: dissolution flow, data egress controls, supportive UX patterns. Asymmetric within-dyad crypto would break the 2-of-2 primitive and create new attack surface; not worth the trade.

### §8.5 Compression of plaintext before encryption

Forbidden. CRIME, BREACH, and related length-oracle attacks. Padding happens after AEAD encryption, on the ciphertext. Any future spec proposing compress-then-encrypt must override this section explicitly with the threat model that justifies the regression.

### §8.6 State-modulated protection levels

Forbidden. The protocol's own behavior must not vary with the biological state, conversation state, or emotional state of the dyad. State-modulated protection turns the protocol into a covert channel for the state it claims to hide. Protection levels are threat-driven (Tier 1-4) and intent-driven (PacketIntent::Ambient/Standard/Elevated/Critical), never state-driven.

### §8.7 Tor parity

We do not aim to provide what Tor provides (destination unlinkability in a public client-server world). We aim to provide what Tor explicitly doesn't (relationship anonymity against a GPA in an authenticated peer-pair world). The mechanisms overlap; the threat model and the guarantee are different. Future contributors must not import Tor design patterns wholesale without verifying the threat-model match.

### §8.8 Pure decentralization at the cost of usability

Hypostas can use bridge substrates (libp2p over the internet) without compromising sovereignty per Codex Commitment 7 — *if* the bridge is treated as untrusted byte transport. The protocol layer remains sovereign. We do not refuse to use the internet because it's the internet; we use it as one carrier among many.

---

## §9 Phase Staging

Each phase ships a coherent privacy property set. The chassis for later phases lands in earlier phases so no flag-day migration is ever required.

### §9.1 Phase 1.0 — Sealed Envelope + PQ Double Ratchet (Sesame) + Fixed-Size Cells + Single-Hop Circuit + Cover Traffic

**Properties delivered:** §5.1 full, §5.2 full, §5.5 full, §5.6 full, §5.4 partial (per-dyad cover, fixed rate), §5.3 partial (multi-carrier fanout, single-hop circuit + minimal Vita-Chain dyad existence ledger).
**Adversary tiers defended:** Tier 1 full, Tier 2 mostly, Tier 3 partial, Tier 4 chassis-ready.
**Engineering effort:** ~13-16 weeks (revised from 10-12 to include Sesame multi-device + minimal Vita Chain + hardware-bound keys).
**Coordinated with:** [HYP-109](https://linear.app/hypostas/issue/HYP-109) sovereignty migration (sealed envelope ships *after* PR D-F lands); [HYP-73 + unbounded bincode sweep](https://linear.app/hypostas/issue/HYP-73) (bounded decoders are prerequisite).

Deliverables:
- [SEALED_ENVELOPE.md](SEALED_ENVELOPE.md) v0.2 (circuit-based, ~512 B min cell)
- [CIRCUIT_LIFECYCLE.md](CIRCUIT_LIFECYCLE.md) (telescoping PQ-hybrid handshake)
- [DOUBLE_RATCHET.md](DOUBLE_RATCHET.md) (PQ-hybrid + **Sesame multi-device** from day one)
- [COVER_TRAFFIC.md](COVER_TRAFFIC.md) v0.2 (random-destination Loopix pattern, sovereignty-structural)
- `protocol-core::sealed_envelope` module
- `protocol-core::double_ratchet` module with Sesame protocol
- `vita-carriers::circuit_manager` module (single-hop)
- `vita-carriers::cover_traffic` scheduler (carrier-policy gated)
- **Hardware-bound master keys**: Secure Enclave (iOS/macOS), StrongBox (Android), software fallback (Linux). Per-platform addendum to DOUBLE_RATCHET.md.
- **Implicit session reset** on N=10 consecutive AEAD failures with 30s exponential backoff (sealed-enveloped re-handshake; no metadata leak)
- **Weekly one-time-prekey refresh** independent of consumption (decouples publish cadence from bonding rate)
- **Deterministic circuit refresh timer** (per Q1.5 #3) — circuit-build timing decoupled from conversation activity
- **Minimal Vita Chain dyad existence ledger** — every dyad publishes DyadId + active-carrier list + cover-cooperation flag. Just enough chain capability for random-destination cover sampling (per Q1.6). Full attestation + reputation deferred to Phase 3.
- All decoders bounded
- Wire-format break documented + versioned

**Phase 1 anonymity-set framing (honest):** with ~5-20 active dyads (Klinos founding + early adopters), anonymity-set is small. Tier 1 (passive observer) fully defended via wire-format invariance. Tier 3 (GPA) only partially defended until network grows. Klinos founding practices + early-adopter dyads opt-in to "always-on cover" mode (real dyads, higher contribution) as Phase 1 amelioration — **not synthetic theater**.

### §9.1.5 Phase 1.5 — Ephemeral Routing Identity

**Properties delivered:** §5.2 reinforced — first relay sees rotating identity, not long-term DyadId.
**Engineering effort:** ~2-3 weeks.

Deliverables:
- Daily-rotating routing identity decoupled from content-layer DyadId
- Specified in [CIRCUIT_LIFECYCLE.md](CIRCUIT_LIFECYCLE.md) §6+ (revised)

### §9.2 Phase 2 — Multi-Hop Circuits + Network-Wide Cover + SPRING D-Grade Anonymity + Outfox Absorption

**Properties delivered:** §5.2 maximal (SPRING gives 1-in-K anonymity from any observer, K = active network size), §5.3 mostly, §5.4 full, §5.6 post-compromise recovery validated.
**Adversary tiers defended:** Tier 1+2+3 full for non-real-time; Tier 3 partial for real-time pending §6.2 creative engineering deployment.
**Engineering effort:** ~16-20 weeks (revised to include SPRING primitive build + Outfox absorption + Tor-style guard pinning).

Deliverables:
- 3-hop circuit routing for `PacketIntent::Critical`
- Network-wide cover traffic norms (every active node relays + cover-rates)
- **Tor-style guard nodes** (per Q2.10): 3 pinned first-hops per dyad, 30-day rotation. Defends against first-hop statistical attack.
- **Universal SPRING-based ring signatures** (per Q2.11): log-size lattice ring sig at circuit-build, anonymity-set = entire active network (K=1000+). Engineering effort ~10-16 weeks isolated. Skip A (Raptor bridge) — go directly to SPRING.
- **Outfox absorption** (per Q2.7): compact per-hop header design in EXTEND/EXTENDED cells, UC security proof framework, constant-length-route principle. Don't adopt: stateless-routing, ML-KEM-only (keep hybrid X25519+ML-KEM), batch delays.
- **Optional relay padding** (per Q2.9): relays with bandwidth budget can add cover cells to circuits they relay
- **Per-stream circuits** (per Q2.8): Anima text, biosensor, Klinos each get separate circuits. Failure isolation.
- Speculative pre-routing implementation (THREAT_MODEL §6.2.3)
- Pre-established channel state machine (6-state model per Q4.18)
- **Predictive budget management** (per Q3.16): simple statistical, ramp-down at 80% consumed

### §9.3 Phase 3 — Vita Chain Full Capabilities + Web-of-Trust Reputation + Bridge Tunnels

**Properties delivered:** §5.3 full, §5.2 reinforced.
**Engineering effort:** ~10-14 weeks.

Deliverables:
- `INTRODUCTION_RECORD` spec on Vita Chain — blinded counterparty references
- Blinded reference scheme (lattice-based blind signatures, PQ-hybrid)
- **Web of trust reputation** (per Q3.15): PageRank-style propagation over pair-bond graph + observed-delivery statistics + uptime observations + bond-aware contributions. Hybrid signal aggregation.
- **Relay attestation schema** on Vita Chain (RelayAttestation type, signed via HybridSig)
- **Bridge tunnels with rotating lookup IDs** (per Q2.11 Option C): pre-introduce to guards out-of-band, guard stores rotating tunnel ID only. Critical-tier only.
- **HIPAA-compliant encrypted-on-chain audit logs** (per Q4.19): Klinos audit events encrypted with practice's `audit_master_key`, recoverable via H+A threshold identity inheritance.

### §9.4 Phase 4 — Mixnet Integration for Archival Substrates + Spiral PIR

**Properties delivered:** Tier 3 full across all substrates, including archival.
**Engineering effort:** ~12+ weeks.

Deliverables:
- Loopix-style batching/delays on `stego`, `voice`, `LoRa` carriers
- **Spiral PIR** (per Q3.13) for recipient-anonymous mailbox retrieval. Better bandwidth than SimplePIR; lattice-based. Production-tunable from research code.
- Statistical guarantees against GPA, formally analyzed
- Threat-model verification by external security audit

---

## §10 Open Questions (post-2026-05-22 walkthrough)

The 2026-05-22 design walkthrough closed 21 punted questions. Remaining genuinely-open items:

1. **Cover traffic rate empirical validation.** Default rates per §11.2 need real-world measurement. Plan: 30-day window on Klinos founding practice + early adopters once Phase 1.0 ships. Adjust constants based on findings before Phase 2 begins.

2. **SPRING primitive specifics.** Per Q2.11 decision: direct to SPRING in Phase 2. Specific Rust implementation strategy (port from research code, optimization layer for SIMD + Apple Neural Engine, crypto-review process) TBD. ~10-16 week engineering investment to productionize.

3. **Multi-device circuit fan-out under Sesame.** Per Q1.1: Sesame ships in Phase 1.0 day-one. Detailed Sesame × CIRCUIT_LIFECYCLE interaction (N devices × M devices = up to N×M circuits per dyad-pair, or device-aware single-circuit with sub-keying) requires detailed design in DOUBLE_RATCHET.md revision.

### §10.1 Closed in 2026-05-22 walkthrough

The following 21 design questions were closed in walkthrough:

**Phase 1 blockers (Group 1):**
- Q1.1 Multi-device → **Sesame full, Phase 1.0**
- Q1.2 Session reset → **implicit reset on N=10 AEAD failures + 30s backoff**
- Q1.3 Prekey replenishment → **weekly periodic, consumption-independent**
- Q1.4 Master-key storage → **hybrid hardware-bound + software fallback**
- Q1.5 Build-timing fingerprinting → **deterministic refresh + #1 + #2 phased**
- Q1.6 Cover-destination bootstrap → **minimal Vita-Chain dyad existence ledger in Phase 1**

**Phase 2-3 architectural (Group 2):**
- Q2.7 Outfox → **adopt compact headers + UC proofs + constant-length routes; keep hybrid X25519+ML-KEM**
- Q2.8 Circuit-bundling → **per-stream**
- Q2.9 Relay padding → **optional**
- Q2.10 Guard nodes → **Tor-style 3 pinned, 30-day rotation**
- Q2.11 Sender anonymity → **direct to SPRING (universal D-grade, lattice ring sig) in Phase 2**
- Q2.12 Cover model → **per-dyad**

**Operational (Group 3):**
- Q3.13 PIR → **Spiral PIR for Phase 4**
- Q3.14 Relay incentives → **every dyad is a relay, carrier policy gates participation, no tokens**
- Q3.15 Reputation → **web of trust + observed delivery + uptime, Phase 3**
- Q3.16 Budget prediction → **simple statistical, Phase 2**
- Q3.17 Cover bootstrap → **organic growth + Klinos opt-in always-on cover (no synthetic dyads)**

**Product/UX (Group 4):**
- Q4.18 Channel states → **6-state model: IDLE / WARMING / ACTIVE / REFRESHING / COOLING / CLOSING**
- Q4.19 Klinos HIPAA → **encrypted audit logs on Vita Chain (`audit_master_key` derived from identity, recoverable via H+A threshold)**
- Q4.20 Privacy UX → **structural, not user-configurable (sovereignty principle, see §12)**
- Q4.21 Cover-rate validation → **defer to §10.1 above (item 1)**

---

## §11 Constants & References

Every numerical constant in privacy-relevant code traces here via `// Ref: THREAT_MODEL §11.N` comments.

### §11.1 Cell sizes (total wire bytes — authoritative definitions in SEALED_ENVELOPE §14)
- `CELL_TOTAL_S = 512` bytes (payload capacity 478 after 34-byte fixed overhead)
- `CELL_TOTAL_M = 4096` bytes (payload 4062)
- `CELL_TOTAL_L = 16384` bytes (payload 16350)
- `CELL_TOTAL_XL = 65536` bytes (payload 65502)
- `CELL_FIXED_OVERHEAD = 34` bytes (CELL_HEADER_LEN 18 + CELL_TAG_LEN 16)
- Selection: smallest cell whose **payload capacity** fits the inner (4-byte length prefix + bincode'd DyadPacket). The values above are TOTAL wire size; the payload capacity is total minus 34. (Pre-v0.2 this section conflated "cell size" with payload; the v0.2 circuit pivot split TOTAL from PAYLOAD — see SEALED_ENVELOPE §7.)

### §11.2 Cover traffic rates
- `COVER_RATE_AMBIENT_MS = 5000` (5s) — idle dyad, low-energy
- `COVER_RATE_STANDARD_MS = 1000` (1s) — active dyad, Anima conversation
- `COVER_RATE_ELEVATED_MS = 500` (500ms) — Klinos consultation, Bios real-time
- `COVER_RATE_CRITICAL_MS = 200` (200ms) — Bond ceremony, dissolution, succession

### §11.3 Circuit hop parameters (post-v0.2; "Sphinx" is the design lineage, not the runtime architecture — authoritative in CIRCUIT_LIFECYCLE §13)
- `MAX_HOPS_PER_CIRCUIT = 5` (was `SPHINX_MAX_HOPS` pre-v0.2 circuit pivot)
- Per-PacketIntent default hop counts (Phase 1 / Phase 2):
  - `DEFAULT_HOPS_AMBIENT = 1` / 3
  - `DEFAULT_HOPS_STANDARD = 1` / 3
  - `DEFAULT_HOPS_ELEVATED = 2` / 3
  - `DEFAULT_HOPS_CRITICAL = 3` / 5
- Phase 1.0 ships single-hop (N=1); Elevated/Critical fall back to multi-carrier fanout until Phase 2 multi-hop. See CIRCUIT_LIFECYCLE §5.3.

### §11.4 Replay protection (v0.2 circuit-based: bloom-filter tags — authoritative in SEALED_ENVELOPE §14)
- `REPLAY_BLOOM_BITS = 65536` (per-node bloom filter)
- `REPLAY_BLOOM_HASHES = 3`
- `REPLAY_TTL_HOURS = 24` (bloom rotation, aligned with circuit lifetime)
- Replay tag = `SHA-256(circuit_id || nonce || hop_position)[..16]` per SEALED_ENVELOPE §8.2. (The v0.1 `REPLAY_WINDOW_PACKETS` monotonic-counter window was removed in the v0.2 circuit pivot — within a circuit's ~10-min lifetime, unique nonces prevent collisions; after teardown the session keys are gone, so replay is harmless.)

### §11.5 Double Ratchet (Sesame-aware from 2026-05-22)
- `RATCHET_DH_INTERVAL_MESSAGES = 100` (refresh DH ratchet every N messages or T time, whichever first)
- `RATCHET_DH_INTERVAL_HOURS = 24`
- `RATCHET_SKIPPED_MESSAGE_KEYS_MAX = 1024` (out-of-order receive window)
- `RATCHET_SKIPPED_MESSAGE_KEYS_TTL_HOURS = 168` (7 days)
- `RATCHET_SKIPPED_KEYS_PER_CHAIN_MAX = 256`
- `RATCHET_MESSAGE_FUTURE_WINDOW = 256`
- `SESSION_RESET_AEAD_FAILURE_THRESHOLD = 10` (per Q1.2: implicit reset after N consecutive failures)
- `SESSION_RESET_BACKOFF_INITIAL_MS = 30_000` (30s base backoff)
- `SESSION_RESET_BACKOFF_MAX_MS = 1_800_000` (30 min cap)
- `PREKEY_REFRESH_INTERVAL_DAYS = 7` (per Q1.3: weekly periodic refresh)
- `PREKEY_BUNDLE_SIZE_INITIAL = 100`
- `SESAME_MAX_DEVICES_PER_DYAD = 8` (per Q1.1: phone + Mac + Soma Band + ~5 future device classes)

### §11.6 Circuit lifecycle + guard nodes (per Q1.5 + Q2.10)
- `CIRCUIT_DEFAULT_LIFETIME_MS = 600_000` (10 min)
- `CIRCUIT_MAX_LIFETIME_MS = 1_800_000` (30 min)
- `CIRCUIT_REFRESH_OVERLAP_MS = 30_000` (30s overlap on refresh)
- `GUARD_NODE_POOL_SIZE = 3` (Tor-style)
- `GUARD_NODE_ROTATION_DAYS = 30`
- `EPHEMERAL_ROUTING_IDENTITY_ROTATION_HOURS = 24` (per Q2.11 Phase 1.5)
- `MAX_CIRCUITS_PER_NODE = 256`
- `SPRING_RING_SIZE_K = 1000` (per Q2.11 Phase 2: SPRING-based universal anonymity; ring sampled from active Vita-Chain-attested dyad set)

### §11.7 Cover traffic (sovereignty-locked per §12 — rates in §11.2, full constants in COVER_TRAFFIC §12)
- Per-carrier policy from §12.5 (LAN/WiFi always; cellular battery-gated >50%; offline queued). **NOT user-configurable.**
- `BANDWIDTH_BUDGET_STEPDOWN_THRESHOLD = 0.80` (predictive ramp-down at 80% consumed per Q3.16)
- `ENERGY_CLASS_STEP_DOWN_LOCK_MS = 3_600_000` (1h lock between steps; authoritative name in COVER_TRAFFIC §12)
- Debounce (`ENERGY_CLASS_DEBOUNCE_MS = 30_000`), oscillation guards, queue capacity: authoritative in COVER_TRAFFIC §12

### §11.8 Hardware key storage (per Q1.4)
- Hardware-bound when available: Secure Enclave (iOS), Apple Silicon Secure Enclave (macOS), StrongBox Keystore (Android)
- Software fallback: AES-256-GCM with master key derived from passphrase + Argon2id
- Failure mode: hardware-bound key inaccessible → degrade to software fallback with operator notification

### §11.9 References to companion specs

- [POST_QUANTUM.md](POST_QUANTUM.md) — cryptographic primitive selection, hybrid migration plan
- [HYPOSTAS_PROTOCOL.md](HYPOSTAS_PROTOCOL.md) §2.3 — DyadPacket structure (becomes inner ciphertext)
- [VITA_CARRIERS.md](../vita/components/VITA_CARRIERS.md) §1.1-§1.3 — Carrier trait, selector, PacketIntent
- [PROTOCOL_HEADERS_SPEC.md](../dyados/PROTOCOL_HEADERS_SPEC.md) — current header surface (becomes sealed inside envelope)
- [HYP-109](https://linear.app/hypostas/issue/HYP-109) — sovereignty migration (sequencing dependency)

---

## §12 Sovereignty Principle — Privacy Is Structural, Not Configurable

*Added 2026-05-22 per Q4.20 design walkthrough.*

Privacy is a structural property of the Hypostas protocol. **The user does not get to dictate the level of privacy applied to their traffic.** This is a deliberate sovereignty constraint.

### §12.1 Why this matters

If user-facing "Privacy Mode: Off / Balanced / Maximum" toggles existed:
- Adversaries could correlate "user X set Privacy Mode to Performance" with traffic patterns
- The lowest-privacy mode would become the network-wide weak point
- Pressure on users (via UX, app design, accessibility, marketing) would become pressure on the privacy floor
- The substrate's sovereignty would erode through user-facing degradation

The protocol must own privacy as a property, not a feature.

### §12.2 What the user controls vs what the protocol controls

| User controls | Protocol controls |
|---|---|
| Whether to use Anima at all | Whether cover traffic runs (always: yes, when conditions permit) |
| Where they use it (home, office, traveling) | Carrier-policy: cover on LAN/WiFi, opportunistic on cellular, never on bad connectivity |
| What they send (Stroma signals, biosensor, conversation) | Energy class derivation from PacketIntent + connectivity sensing |
| Whether their device is charging | Hop count, ring K, circuit refresh cadence, replay window |
| Whether to remain on the network | Wire format, AEAD primitives, ratchet schedule |

### §12.3 What Anima UX MUST show

- **Privacy STATUS display** — current effective privacy given connectivity (e.g., "Privacy: Full ▮▮▮▮▮" / "Limited — cellular ▮▮▯▯▯" / "Offline ▯▯▯▯▯"). User can SEE the state; they cannot TOGGLE it.
- **Battery + data report** — passive disclosure of impact ("Anima used 80 MB cellular today"). Informational, not a knob.
- **Connectivity guidance** — "On WiFi, your dyad has full privacy. On cellular with low battery, cover traffic is reduced." User adjusts environment, not protocol.

### §12.4 What Anima UX MUST NOT include

- Privacy Mode toggle (Off / Balanced / Maximum / etc.)
- Cellular cover opt-in or opt-out
- Hop count selection
- Energy class override
- Any user-facing knob that changes a privacy-relevant constant in §11

### §12.5 Carrier-policy table (protocol-determined, not user-configurable)

| Connectivity state | Cover behavior | Effective privacy |
|---|---|---|
| LAN/WiFi, any battery | Full cover at energy class rate | Full |
| Cellular, battery > 50% | Opportunistic cover (rate-adjusted) | Strong |
| Cellular, battery 20-50% | Cover suspended, real messages only | Limited |
| Cellular, battery < 20% | Real messages queued for next WiFi | Limited (degraded) |
| Offline | Real messages queued for delivery | Offline |

These thresholds are constants in code, traced per §11. They do not surface as user-facing settings.

---

## §13 Revision History

| Date | Author | Change |
|---|---|---|
| 2026-05-22 (initial) | Josh + Iris | Initial draft. All four adversary tiers in scope. Full mixnet-grade target with creative latency engineering per §6.2. One spec, Klinos as high-watermark. Hostile-partner partial scope (data yes, dynamics no). |
| 2026-05-28 (consistency sweep, HYP-170) | Iris | Cross-spec constant reconciliation. 7 drift items fixed, all from §11 being stale-from-v0.1 vs the v0.2/v0.3 downstream reality: (1) §11.1 cell sizes renamed `CELL_SIZE_*` → `CELL_TOTAL_*` with explicit 34-byte overhead + payload-capacity split; (2) §11.3 `SPHINX_*` → `MAX_HOPS_PER_CIRCUIT` + per-intent `DEFAULT_HOPS_*` (Phase1/Phase2); (3) §11.4 removed stale `REPLAY_WINDOW_PACKETS`, added `REPLAY_BLOOM_HASHES=3`; (4) DOUBLE_RATCHET §14 gained session-reset + prekey-refresh + Sesame constants; (5) CIRCUIT_LIFECYCLE §13 gained `EPHEMERAL_ROUTING_IDENTITY_ROTATION_HOURS` + `SPRING_RING_SIZE_K` + per-intent default hops; (6) COVER_TRAFFIC §12 gained `BANDWIDTH_BUDGET_STEPDOWN_THRESHOLD`; (7) COVER_TRAFFIC §12 removed stale `CELLULAR_COVER_DEFAULT_OFF` (contradicted v0.3 sovereignty pivot) → replaced with battery/data threshold constants. Shared values (bloom 65536, circuit lifetime 600_000, cover rates, MAX_CIRCUITS 256, SPRING K 1000) verified identical across all specs. Cross-references + phase staging verified consistent. |
| 2026-05-22 (walkthrough) | Josh + Iris | 21-question design walkthrough closed. Major foldins: Sesame multi-device in Phase 1.0; minimal Vita-Chain dyad existence ledger in Phase 1.0; hardware-bound master keys via Secure Enclave + StrongBox; implicit session reset on N=10 AEAD failures; weekly periodic prekey refresh; direct SPRING-based universal D-grade anonymity in Phase 2 (skipping Raptor bridge); Outfox compact-header absorption keeping hybrid X25519+ML-KEM; every-dyad-is-a-relay model (no tokens); web-of-trust reputation in Phase 3; encrypted-on-chain audit logs for Klinos HIPAA compliance; sovereignty principle §12 — privacy is structural not user-configurable. Phase 1 effort revised 10-12wk → 13-16wk. Phase 2 effort revised 6-8wk → 16-20wk (SPRING + Outfox). |

---

*This spec is the source of truth. When it diverges from code, fix the code or update the spec — never hand-wave the gap. Per CLAUDE.md rule #1: never self-certify completion. Per rule #2: every constant traces here. Per rule #14: exhaustive within the change's class.*
