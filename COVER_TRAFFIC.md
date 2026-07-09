# COVER_TRAFFIC.md — Constant-Rate Cover Traffic Scheduler

**Status:** Draft (2026-05-22, v0.1)
**Owner:** `vita-carriers`, `protocol-core`
**Authors:** Josh + Iris
**Anchored to:** [THREAT_MODEL.md](THREAT_MODEL.md) §5.4, §6.2.1, §6.2.2, §6.2.4, §11.2
**Companion specs:** [SEALED_ENVELOPE.md](SEALED_ENVELOPE.md) (wire format cover packets use), [DOUBLE_RATCHET.md](DOUBLE_RATCHET.md) (cover packet inner content uses same keys as real traffic)
**Linear:** [HYP-118](https://linear.app/hypostas/issue/HYP-118) (parent [HYP-115](https://linear.app/hypostas/issue/HYP-115))

---

## §1 Purpose

Cover traffic is the **creative-engineering answer to the mixnet-latency problem** stated in [THREAT_MODEL.md §6.2](THREAT_MODEL.md). Classical mixnet designs (Mixminion, Loopix, Nym) achieve §5.4 timing-secrecy + §6.3 GPA defense via per-hop batching delays — paying latency for unlinkability. Anima's <300ms latency budget can't absorb that cost.

This spec defines the alternative: **constant-rate outbound traffic per dyad per carrier**. Real messages ride on the next available scheduled slot. Cover packets fill the gaps when no real message is queued. The outbound stream looks identical to any observer regardless of whether the dyad is actively conversing — timing decorrelation comes from uniformity, not delay.

**Cost trade:** bandwidth, not latency. A dyad maintaining 1 packet/sec cover on libp2p pays ~14 KB/sec = ~1.2 GB/day per active carrier. Mitigated by:
- Carrier-tier policy (no cover on cellular by default)
- Energy-class tiering (idle dyad uses Ambient 5s rate, ~240 MB/day)
- Per-carrier budget caps with graceful rate-step-down

This is the spec where Josh's 2026-05-22 "creative engineering to fix latency" mandate gets concrete.

### §1.1 Threat-model coverage

| Property | Defense provided |
|---|---|
| §5.4 Timing secrecy | Constant-rate outbound → packet timing invariant of conversation activity |
| §5.3 Relationship secrecy (partial Phase 1) | Combined with multi-carrier fanout — a passive observer of one substrate cannot correlate with another |
| §5.3 Relationship secrecy (Phase 2+) | Network-wide cover means **anonymity set = entire active network** — any dyad's real packet is indistinguishable from any other dyad's cover packet at the wire layer |

### §1.2 The Loopix insight, adapted

Loopix's foundational observation: if every node sends at a constant rate, an adversary can't tell *which* nodes are actively communicating. Real messages embed within the cover stream. The defense is statistical: even a GPA seeing every link can only determine that the network is active, not which pairs are correlated.

Hypostas variant: instead of Loopix's per-hop Poisson delays (latency), we use per-dyad constant rate (bandwidth). The math works the same way at the network observation layer; the cost is paid in a different dimension.

---

## §2 Energy classes + rates

Per [THREAT_MODEL §11.2](THREAT_MODEL.md), four energy classes:

| Class | Rate | Use case | Latency budget for real msg |
|---|---|---|---|
| `Ambient` | 5000ms (5s) | Idle dyad, low-energy mode, background-only | Up to 5s |
| `Standard` | 1000ms (1s) | Active Anima conversation | Up to 1s |
| `Elevated` | 500ms | Klinos consultation, Bios real-time biosensor stream | Up to 500ms |
| `Critical` | 200ms | Bond ceremony, dissolution, succession anchor | Up to 200ms |

### §2.1 Class transitions

Energy class is computed from PacketIntent + dyad activity signal + carrier properties. Transitions are debounced to avoid leaking activity onset:

```rust
struct EnergyClassPolicy {
    current: EnergyClass,
    pending: Option<EnergyClass>,
    pending_since_ms: i64,
    debounce_ms: u64,  // 30000 ms / 30s
}

fn maybe_transition(&mut self, requested: EnergyClass, now_ms: i64) {
    if requested == self.current {
        self.pending = None;
        return;
    }
    match self.pending {
        Some(p) if p == requested && now_ms - self.pending_since_ms > self.debounce_ms => {
            self.current = p;
            self.pending = None;
        }
        Some(p) if p == requested => { /* still debouncing */ }
        _ => {
            self.pending = Some(requested);
            self.pending_since_ms = now_ms;
        }
    }
}
```

**Why 30s debounce:** transitions reveal information. If the class jumps from Ambient to Standard the instant the user opens Anima, an observer correlating wall-clock app-launch (visible side-channel: phone unlock screen detected via accelerometer-derived patterns, etc.) with on-network traffic class shift learns the user is active. 30s smears the transition across enough Standard-rate packets that the onset isn't observable from outside.

**The cost of debouncing:** during the 30s window, real Anima messages route at the previous class's rate. If you go from Ambient (5s) to Standard (1s) and a message arrives during the 30s debounce window, the message may wait up to 5s. Acceptable for the privacy gain.

### §2.2 Class selection at packet send time

```rust
fn select_energy_class(intent: PacketIntent, dyad_active: bool, carrier: &CarrierProperties) -> EnergyClass {
    let base = match intent {
        PacketIntent::Critical => EnergyClass::Critical,
        PacketIntent::Elevated => EnergyClass::Elevated,
        PacketIntent::Standard if dyad_active => EnergyClass::Standard,
        PacketIntent::Standard => EnergyClass::Ambient,
        PacketIntent::Ambient => EnergyClass::Ambient,
    };
    // Cap based on carrier policy
    apply_carrier_policy(base, carrier)
}
```

`dyad_active = true` when there's been Anima/Klinos activity within the last 5 minutes (per `intent.write_pending` Stroma signal or explicit activity tag).

### §2.3 Carrier-policy table (protocol-determined, NOT user-configurable)

**Per THREAT_MODEL §12 sovereignty principle:** privacy is a structural property of the protocol. Users do NOT toggle these. The protocol determines cover behavior given connectivity sensing + device state.

| Connectivity state | Cover behavior | Effective privacy |
|---|---|---|
| LAN/WiFi, any battery | Full cover at energy class rate | Full ▮▮▮▮▮ |
| Cellular, battery > 50% | Opportunistic cover at adjusted rate (matched to data-plan headroom + battery state) | Strong ▮▮▮▮▯ |
| Cellular, battery 20-50% | Cover suspended; real messages only | Limited ▮▮▯▯▯ |
| Cellular, battery < 20% | Real messages queued for next WiFi | Limited (degraded) ▮▮▯▯▯ |
| Offline | Real messages queued for delivery on reconnect | Offline ▯▯▯▯▯ |

Per-carrier max-class (also protocol-determined, not user-configurable):

| Carrier | Default max energy class | When effective rate is below max |
|---|---|---|
| LibP2p over LAN/WiFi | Critical | Battery-aware throttling |
| LibP2p over cellular | Standard (when battery+data permit) | Battery + cellular-cost thresholds |
| Bluetooth Mesh | Standard | Range + nearby-peers availability |
| LoRa | Ambient | Hardware-budget-aware |
| Stego carriers | Ambient | Channel-availability-driven |
| Voice carriers | Disabled (latency cost) | Activated only when carrier-substrate requires |
| Cover sink (Local UDS IPC) | N/A | Not network-observable |

**Cellular cover IS enabled by default when conditions permit** (battery > 50%, data plan headroom available). The "no cellular cover" default is replaced by "opportunistic cellular cover sensitive to constraints." User does not opt-in; protocol opportunistically takes available bandwidth + battery within thresholds in §11.7 (in THREAT_MODEL.md §11.7).

---

## §3 Scheduler architecture

### §3.1 Per-carrier-per-dyad scheduler

Each dyad runs one `CoverTrafficScheduler` instance per active carrier. Schedulers are independent — different carriers can be at different energy classes simultaneously.

```rust
pub struct CoverTrafficScheduler {
    dyad_id: DyadId,
    carrier: Arc<dyn Carrier>,
    energy_class: EnergyClassPolicy,
    last_send_ms: AtomicI64,
    outbound_queue: Arc<Mutex<VecDeque<OutboundPacket>>>,  // Bounded to 1024 per THREAT_MODEL
    budget_tracker: Arc<Mutex<BandwidthBudget>>,
    cover_keymat: Arc<CoverKeyMaterial>,
    stop_signal: AtomicBool,
}

pub struct OutboundPacket {
    intent: PacketIntent,
    sealed_envelope_bytes: Vec<u8>,
    destination: DyadId,
    enqueued_at_ms: i64,
}
```

### §3.2 Main scheduler loop

```rust
async fn scheduler_loop(self: Arc<Self>) {
    let mut interval = tokio::time::interval(Duration::from_millis(self.energy_class.current.rate_ms()));
    interval.set_missed_tick_behavior(MissedTickBehavior::Skip);
    loop {
        interval.tick().await;
        if self.stop_signal.load(Ordering::Acquire) { break; }
        
        // Re-evaluate energy class
        self.energy_class.tick(now_ms());
        if interval_changed(&self.energy_class) {
            interval = tokio::time::interval(Duration::from_millis(self.energy_class.current.rate_ms()));
        }
        
        // Dequeue real message if available, otherwise generate cover
        let packet = match self.outbound_queue.lock().pop_front() {
            Some(real) => real,
            None => self.generate_cover_packet().await,
        };
        
        // Send via carrier
        match self.carrier.send(packet.destination, &packet.sealed_envelope_bytes).await {
            Ok(()) => {
                self.budget_tracker.lock().record_send(packet.sealed_envelope_bytes.len());
                self.last_send_ms.store(now_ms(), Ordering::Release);
            }
            Err(CarrierError::CostBudgetExceeded) => {
                // Step down to next-lower energy class
                self.energy_class.step_down();
                if let Some(real) = packet.intent_was_real() {
                    self.outbound_queue.lock().push_front(real); // Requeue
                }
            }
            Err(e) => {
                tracing::warn!(?e, "scheduler send failed");
                // Drop packet, continue scheduling
            }
        }
    }
}
```

### §3.3 Real message enqueueing

When the runtime wants to send a real packet:

```rust
pub async fn send(&self, dest: DyadId, inner_packet: DyadPacket, intent: PacketIntent) -> Result<()> {
    // Build sealed envelope per SEALED_ENVELOPE.md
    let sealed_bytes = sealed_envelope::encrypt(inner_packet, dest, intent).await?;
    
    // Enqueue for the appropriate carrier's scheduler
    let scheduler = self.select_scheduler(dest, intent);
    let outbound = OutboundPacket {
        intent,
        sealed_envelope_bytes: sealed_bytes,
        destination: dest,
        enqueued_at_ms: now_ms(),
    };
    scheduler.outbound_queue.lock().push_back(outbound);
    
    // Update energy class if needed
    let target_class = select_energy_class(intent, true, scheduler.carrier.properties());
    scheduler.energy_class.maybe_transition(target_class, now_ms());
    
    Ok(())
}
```

**Real messages NEVER bypass the scheduler.** Even Critical messages wait for the next 200ms slot. This is structural: bypassing the scheduler would leak that a real message just happened (timing burst, missed cover slot).

### §3.4 Queue bounds

Queue capacity 1024 packets per scheduler per carrier. If full:
- For `PacketIntent::Critical`: evict oldest non-critical, push critical at front
- For others: return `Err(SchedulerError::QueueFull)` to caller

A queue stuck at full means real messages are arriving faster than the energy class allows — caller should escalate intent class or accept the rejection.

---

## §4 Cover packet content generation

Cover packets MUST be indistinguishable from real packets on the wire. Per [SEALED_ENVELOPE.md §4](SEALED_ENVELOPE.md), envelopes are uniformly-sized AEAD-encrypted blobs with fixed-size routing headers and PQ-hybrid ciphertext stacks. Cover packets follow the same format.

### §4.1 Design choice

**Cover packets are FULL sealed cells addressed to randomly-selected known dyad IDs**, indistinguishable from real traffic on the wire. This is the Loopix pattern — cover traffic traverses the network like any other packet; the destination's local state determines "drop or deliver."

Updated for SEALED_ENVELOPE.md v0.2 (circuit-based): cover cells use the sender's existing circuits, same wire format as real cells. The cover destination is the terminal recipient of one of the sender's active circuits — selected randomly from the dyad's peer table.

```rust
async fn generate_cover_packet(&self) -> OutboundPacket {
    // Pick a random size class weighted toward S (most common)
    let size = sample_size_class(&[(SIZE_S, 0.7), (SIZE_M, 0.2), (SIZE_L, 0.08), (SIZE_XL, 0.02)]);
    
    // Pick a random destination from this dyad's peer table
    // (the dyad's own pair-partner is NOT excluded — cover to partner is fine; partner drops via AEAD mismatch
    //  since cover keymat is not the active ratchet key)
    let destination = self.sample_random_known_dyad();
    
    // Get or build a circuit to the destination
    let circuit = self.circuit_manager.get_or_build(destination, PacketIntent::Standard).await?;
    
    // Generate cover inner content: random bytes shaped like Double Ratchet AEAD output
    let cover_inner = self.cover_keymat.generate_cover_inner(size).await;
    
    // Seal in cell using the circuit's session keys
    let cell = sealed_envelope::encrypt_cell(
        circuit: &circuit,
        inner_bytes: &cover_inner,
        size_class: size,
    ).await?;
    
    OutboundPacket {
        intent: PacketIntent::Standard,
        sealed_envelope_bytes: cell,
        destination,
        enqueued_at_ms: now_ms(),
    }
}
```

**Why full sealed cells:** any other shape (just-random-bytes, or a sentinel "this is cover" packet) is distinguishable from real packets by an observer with partial key compromise. Structural indistinguishability requires identical format.

### §4.2 Cover destination — random known dyad (Loopix pattern)

Each cover packet is addressed to a randomly-sampled dyad from the sender's peer table. The receiver attempts to decrypt the cell using their normal circuit + ratchet state. Three outcomes:

1. **No matching circuit** (most common for cover targeting a stranger-dyad): cell drops at the relay layer as `UnknownCircuit` ([SEALED_ENVELOPE §9](SEALED_ENVELOPE.md)).
2. **Matching circuit, AEAD fails** (cover packet shaped like real but content is random): cell drops at the AEAD verification step as `BadTag`.
3. **Matching circuit, AEAD succeeds** (impossible — would require cover keymat to coincidentally equal the circuit's session key, which has negligible probability against a 256-bit symmetric key): cell would deliver. **Cover packet generation MUST never produce a coincidental valid cell.**

To guarantee outcome 3 cannot occur, cover keymat derivation is designed such that the generated AEAD output is provably distinct from any session-key output:

```rust
impl CoverKeyMaterial {
    fn generate_cover_inner(&self, size_class: SizeClass) -> Vec<u8> {
        // The cover seed is per-dyad and CANNOT collide with any session key (which are derived
        // from circuit handshake shared secrets). We can prove non-collision by using a different
        // HKDF info label from any real key derivation.
        let pkey: [u8; 32] = HKDF::expand(&self.seed_key, b"hypostas-cover-packet-content-v2", 32);
        // Generate pseudo-random AEAD output shape
        chacha20_prg_output(&pkey, size_class.payload_capacity())
    }
}
```

The `b"hypostas-cover-packet-content-v2"` label is reserved — any other system using a key derived with this label would itself be a cover-content generator. Code review enforces no other use.

### §4.3 Statistical indistinguishability

A passive network observer sees:
- Every dyad emits cells at its configured rate
- Cells go to a variety of destinations (each dyad's own pair-partner plus random others)
- All cells are uniformly-sized, AEAD-encrypted

There is no global "cover sink" to filter by. No "this dyad is doing cover traffic" signal. The cover blends entirely into the network's normal traffic pattern.

**Anonymity set property (Phase 2+):** as the network grows, this Loopix-style cover means any cell observed on any link could be any sender's real message to any receiver, or any sender's cover to any random destination. The anonymity set is the entire active network.

### §4.4 Receiver-side cost

Receivers process each inbound cell, attempt AEAD verification, drop on failure. Per cell cost:
- ~1 SHA-256 (replay tag check) — fast
- ~1 ChaCha20-Poly1305 AEAD attempt — ~microsecond
- Drop on AEAD fail — no state change

Aggregate: at 1 cell/sec from each of N peers, a node processes N cells/sec. For a dyad with 100 known peers all sending Standard-rate cover: 100 cells/sec → ~100 microseconds of CPU per second = 0.01% CPU. Negligible.

### §4.5 Per-recipient circuit reuse

The cover destination is sampled from the dyad's existing peer table. Each cover packet uses an existing circuit (if one exists) or triggers circuit construction. To avoid making circuit-build events themselves a fingerprint, cover-driven circuit construction is rate-limited (max 1 new circuit per 60s; if budget exceeded, the cover packet picks a different destination from peers with existing circuits).

### §4.3 Cover inner content generation

```rust
struct CoverKeyMaterial {
    seed_key: [u8; 32],  // Per-dyad cover seed, rotated daily
    rotation_at_ms: i64,
}

impl CoverKeyMaterial {
    async fn generate_cover_inner(&self, size_class: SizeClass) -> Vec<u8> {
        // Derive a per-packet pseudo-random key from the seed + counter
        let counter = self.next_counter();
        let pkey: [u8; 32] = HKDF(salt=0, ikm=self.seed_key, info=counter.to_be_bytes()).expand(32);
        
        // Generate plausible-shaped inner DyadPacket bytes
        // (random length within size class, random structure inside)
        let target_len = sample_inner_length(size_class);
        let mut inner = vec![0u8; target_len];
        rand::thread_rng().fill(&mut inner[..]);
        
        // Wrap as a fake MessageHeader || ciphertext || tag (matching DOUBLE_RATCHET output shape)
        wrap_as_pseudo_double_ratchet_output(inner, pkey)
    }
}
```

Cover content's internal byte distribution must statistically match real Double Ratchet output. Real outputs are: deterministic MessageHeader (varies in pubkey bits — uniform random over X25519+ML-KEM key space) + AEAD ciphertext (uniform random) + AEAD tag (uniform random). Cover content is the same shape with random "pubkey" bytes (which a network observer can't distinguish from real ephemeral pubkeys).

### §4.4 Receiver-side cover detection (defense in depth)

If a node mistakenly receives a cover packet addressed to itself (routing error, malicious relay, etc.):
- AEAD verification fails (cover key material is not the real ratchet key)
- Packet drops at the standard envelope-failure path ([SEALED_ENVELOPE.md §9](SEALED_ENVELOPE.md) `BadTag`)
- No state corruption; logged as INFO

This means receivers cannot tell their own cover packets from genuine bit-error decryption failures. Acceptable — both are "drop and continue."

---

## §5 Bandwidth budget enforcement

### §5.1 Budget tracking

```rust
pub struct BandwidthBudget {
    carrier_class: CarrierClass,
    daily_cap_bytes: u64,
    consumed_bytes: u64,
    reset_at_ms: i64,
    over_budget_count: u32,
}

impl BandwidthBudget {
    pub fn for_carrier(carrier: &CarrierProperties) -> Self {
        let daily_cap = match (carrier.cost, carrier.class) {
            (CostClass::Bandwidth, _) => 100 * 1024 * 1024,  // 100 MB/day on cellular
            (CostClass::Free, CarrierClass::Network) => u64::MAX,  // libp2p LAN: unlimited
            (CostClass::HardwareUpfront, _) => 50 * 1024 * 1024,  // LoRa: practical limit
            _ => 500 * 1024 * 1024,  // 500 MB default
        };
        Self { /* ... */ }
    }
}
```

### §5.2 Step-down policy on budget exceed

When carrier returns `CostBudgetExceeded` or local budget is approaching:

```
Critical → Elevated → Standard → Ambient → OFF
```

Each step happens with 30s debounce (same as energy-class transitions). Step-down is sticky for 1 hour before allowing re-escalation. This prevents:
- Oscillation (frantic up-down leaks budget-pressure to observers)
- Attacker-induced step-down (sustained traffic forces budget exhaustion → forces step-down → observer learns budget hit)

### §5.3 Budget reset

Budgets reset at local midnight in the dyad's configured timezone. Step-down decisions also reset on budget rollover.

### §5.4 Graceful degradation, not hard cap

When budget is fully exhausted (after all step-downs), the scheduler still serves **real messages** at their intent's rate but suspends cover traffic. This means:
- Real-message latency stays bounded (good for UX)
- Cover-traffic privacy property degrades (bad, but visible: a network observer sees the dyad's outbound rate drop to "only when conversing")
- Logged as WARN; surface to user via Anima as "Cover traffic paused — budget exhausted"

**Tradeoff acknowledged:** under sustained budget pressure, a dyad becomes more observable. The hard alternative (drop real messages too) breaks the product worse. Future work: predictive budget management that prevents budget exhaustion before it happens, vs. reactive step-down.

---

## §6 Mobile platform considerations

### §6.1 iOS Background Tasks

iOS limits background CPU + network. The constant-rate scheduler must survive:

- **Backgrounding:** app goes to background → iOS suspends timers after ~3 minutes by default
- **BGAppRefreshTask:** opportunistic wake at iOS's discretion (~15-30 min)
- **BGProcessingTask:** opportunistic wake for heavier work (~30-60 min, when charging/WiFi)
- **App restart:** scheduler state must persist + resume

**Strategy:**
1. **Foreground:** scheduler runs natively; full constant-rate behavior
2. **Background within 3 min:** scheduler continues briefly; one packet per remaining wake
3. **Background beyond suspension:** scheduler suspended. **No cover traffic emitted.** This leaks "phone is in background" — accepted tradeoff (the alternative is a battery-killing always-awake mode)
4. **Background wake (BGAppRefreshTask):** scheduler emits one cover packet on wake, then suspends until next wake. From observer's view: dyad emits packets at iOS's wake cadence, not constant rate. Privacy degraded but better than nothing.
5. **Foreground resume:** scheduler immediately re-enters constant-rate mode; state restored from persistence

### §6.2 Surfacing the privacy degradation

Anima UI must show the current effective privacy class:
- ✅ "Full privacy" — foreground, constant-rate active
- ⚠️ "Reduced privacy — backgrounded" — only background-wake cover
- ❌ "Real-message-only" — no cover (budget exhausted or carrier-OFF policy)

Per THREAT_MODEL §12: **users do not configure privacy.** The protocol determines effective privacy from connectivity sensing + device state. Anima displays current Privacy Status (per §12.3 of THREAT_MODEL.md) but does not expose toggles. Users adjust their *environment* (move to WiFi, charge their device) — not the protocol behavior.

### §6.3 Android (future)

Android has more flexible background work (WorkManager, foreground services with notifications). Spec for Android cover-traffic scheduling deferred to a per-platform addendum. Same logical model; different OS hooks.

---

## §7 Network-wide cover bootstrap (Phase 2 hook)

[THREAT_MODEL §6.2.2](THREAT_MODEL.md) commits to **network-wide cover = anonymity set spans entire active network** by Phase 2. The mechanism:

- Every active dyad runs cover traffic at its energy-class rate (per this spec, Phase 1).
- Cover packets address the cover-sink DyadId AND fan out across multiple carriers (multi-carrier fanout per [THREAT_MODEL §6.2.4](THREAT_MODEL.md)).
- An observer of any link sees uniformly-distributed packets from many sources. Real conversations are statistically buried in cover traffic.

### §7.1 Bootstrap problem

Anonymity-set defense scales with active dyad count. With N=2 (Klinos founding pair), anonymity set is 2. With N=10,000, the math becomes meaningful.

**Phase 1 baseline (this spec):** each dyad's own cover defends against same-link observation (Tier 1). Anonymity set effectively 1, but Tier 1 is defeated via timing-invariance.

**Phase 2 transition:** as the network grows, the same cover-traffic mechanism scales naturally. No re-engineering. The math just gets better.

### §7.2 Future enhancement: cover-relayed cover

In Phase 3+, dyads acting as relays will forward cover packets along with real packets. A relay's outbound stream is a mix of: own cover, real-message-forwards, cover-from-other-dyads. This further compounds the anonymity set at relay vantage points. Specified in `RELAY_LAYER.md` (deferred to Phase 3).

---

## §8 Failure modes

| Error | Cause | Action |
|---|---|---|
| `QueueFull` | Outbound queue at 1024 capacity | Drop oldest non-Critical or return error to caller |
| `BudgetExhausted` | Carrier daily budget fully consumed | Step down energy class → eventually disable cover; real messages still sent |
| `CarrierUnavailable` | Carrier substrate is down | Pause scheduler for this carrier; resume on `CarrierStatusChange::Available` event |
| `CoverGenerationFailed` | Cover keymat unavailable or RNG failure | Skip this slot; emit no packet; log at ERROR |
| `SchedulerStalled` | Last successful send >2× interval ago | Restart scheduler task; persist error state |
| `EnergyClassOscillation` | Class transitioning >3 times in 60s | Lock to lowest-requested class for 5 min; log at WARN |
| `RealMessageTimeout` | Real message enqueued >10s past energy-class rate | Escalate intent class one step (Standard→Elevated etc.) for next packet only; log at INFO |

---

## §9 Persistence + state machine

### §9.1 Scheduler state file

Persisted per-carrier-per-dyad at `~/.dyads/dyads/<dyad_id>/scheduler/<carrier_name>.bin`, AES-256-GCM-encrypted with master key.

```rust
PersistedSchedulerState {
    version: u8,                    // 0x01
    carrier_name: String,
    energy_class: EnergyClass,
    pending_class: Option<EnergyClass>,
    pending_since_ms: i64,
    last_send_ms: i64,
    budget_consumed_today: u64,
    budget_reset_at_ms: i64,
    over_budget_count: u32,
    queued_packets: Vec<OutboundPacket>,  // For survival across restart
    cover_seed_key: [u8; 32],
    cover_seed_rotation_at_ms: i64,
}
```

### §9.2 Cover seed key rotation

The cover seed key is rotated every 24 hours. This prevents an attacker who somehow recovers one cover packet's pseudo-random structure from predicting future cover packets across days. Rotation handled at scheduler tick: if `now_ms > cover_seed_rotation_at_ms`, generate new seed via OS CSPRNG, update `cover_seed_rotation_at_ms = now_ms + 86400000`.

### §9.3 Recovery

On startup:
- Load + decrypt scheduler state
- Re-enqueue persisted `queued_packets`
- Resume scheduler at the energy class from state
- Verify cover seed not expired; rotate if needed
- **Resume the constant-rate cadence on the deterministic grid (HYP-40x).** The slot grid is
  `epoch·DITHER_EPOCH_MS + phase + k·rate`, where `phase = HKDF-Expand(cover_seed, "cover-cadence-phase" ‖ epoch ‖ rate) mod rate`.
  Because the phase is a **pure function** of the persisted cover seed, the wall-clock dither epoch, and the
  current rate, a restarted dyad reconstructs the **identical** grid a never-crashed dyad is on — with **no
  persisted cadence anchor**. The momentary down-span state that shaped the rate while the process was down
  (device cap §2.3, §6 suspension, §5.2 escalation lock, queue depth) is irrelevant to reconstruction: it only
  ever moved the *rate*, which both the restarted and the never-crashed dyad recompute identically at `now`.
  Recovery therefore resumes **exactly** on the live cadence — no restart-visible early or late slot — rather
  than off a `last_send`-relative anchor, which drifts ≤1 period across a rate-changing dither (§2.4) boundary.
  The phase rotates per 30s epoch, so it is **not** a stable per-dyad cadence fingerprint. `last_send_ms` is
  retained as a persisted status / §8 stall-detection timestamp, **not** the cadence anchor.

---

## §10 Integration with carrier selector

The scheduler sits **above** the [`CarrierSelector`](../dyados/vita-carriers/src/selector.rs). Flow:

```
                              ┌─────────────────────────────┐
                              │ Runtime/Anima/Klinos        │
                              │ wants to send DyadPacket    │
                              └──────────────┬──────────────┘
                                             │
                       1. Wrap inner DyadPacket as bytes (bincode)
                       2. Build SealedEnvelope (per SEALED_ENVELOPE.md)
                                             │
                                             ▼
                              ┌─────────────────────────────┐
                              │ For each active carrier:    │
                              │ CoverTrafficScheduler       │
                              │  - Has outbound_queue       │
                              │  - Has current energy_class │
                              └──────────────┬──────────────┘
                                             │ scheduler tick
                                             ▼
                              ┌─────────────────────────────┐
                              │ Carrier (libp2p/lora/...)   │
                              │ Carrier::send(...)          │
                              └─────────────────────────────┘
```

The CarrierSelector still decides **which carrier(s)** to use for a given packet (multi-carrier fanout for Critical, etc.). The scheduler runs **per-carrier**, handling rate-limiting + cover-filling for that carrier.

### §10.1 Selector handoff

```rust
impl DyadRuntime {
    pub async fn send(&self, dest: DyadId, inner: DyadPacket, intent: PacketIntent) -> Result<()> {
        let sealed = sealed_envelope::encrypt(inner, dest, intent).await?;
        
        let carriers = self.selector.select_carriers(dest, intent).await?;
        for carrier in carriers {
            let scheduler = self.schedulers.get(carrier.name()).ok_or(...)?;
            scheduler.enqueue(OutboundPacket {
                intent,
                sealed_envelope_bytes: sealed.clone(),
                destination: dest,
                enqueued_at_ms: now_ms(),
            }).await?;
        }
        Ok(())
    }
}
```

`select_carriers` returns 1 carrier for Ambient/Standard, 2+ for Elevated, all-available for Critical (existing selector behavior per [VITA_CARRIERS.md §1.3](../vita/components/VITA_CARRIERS.md)).

---

## §11 Test plan

### §11.1 Unit tests
- Scheduler emits at configured rate (±50ms jitter tolerance) over a 60s window
- Energy class transition fires after debounce window (30s)
- Energy class transition does NOT fire before debounce
- Budget step-down: simulate budget exceeded → class drops one step
- Step-up sticky: after step-down, ignore step-up attempts for 1 hour
- Cover packet generation produces correct-size envelopes
- Cover packets statistically indistinguishable from random (chi-square test on inner byte distribution)
- Queue full: enqueue at capacity → returns QueueFull for non-Critical
- Queue full: enqueue Critical at capacity → evicts oldest non-Critical
- Real message rides next slot: enqueue real → next tick sends real (not cover)
- Real message at empty queue: scheduler ticks → emits cover, not real

### §11.2 Property tests
- Over any random sequence of {enqueue real, enqueue cover-trigger, advance time}, observed outbound rate is within tolerance of energy-class rate
- Over any random transition pattern, scheduler never sends two packets within (rate_ms / 2) of each other
- Real messages always emerge in FIFO order within an energy class (except Critical front-jumping)

### §11.3 Integration tests (with sealed envelope + carrier)
- Run scheduler against `LibP2pCarrier` for 5 minutes at Standard class — measure actual outbound rate (should be ~300 packets ±10%)
- Two dyads_runtime instances: one sends 10 real messages, other receives + verifies; observer-on-link sees 300 packets total, only 10 are real → real-message indistinguishability verified
- Mid-conversation energy escalation: start Ambient, send 5 messages, transition to Standard, send 5 more, verify rate ramp + 30s debounce
- Carrier budget exhaustion: configure budget=1KB; send 100 packets; verify step-down sequence

### §11.4 Mobile-specific tests
- iOS simulator: scheduler survives BGAppRefreshTask scheduling
- iOS simulator: scheduler suspends correctly on background; resumes on foreground
- State persistence across simulated app restart: enqueue 50 packets, kill process, restart, verify all 50 in queue

### §11.5 Adversarial tests
- Burst-real-messages attack: enqueue 100 real messages rapidly at Standard — verify scheduler doesn't burst out (rate-limited)
- Energy-class oscillation attack: send messages at rates that trigger up/down classification — verify lock-to-lowest after 3 oscillations in 60s
- Cover-key extraction attack: capture 1000 cover packets, attempt to predict next cover packet's bytes — verify HKDF chain prevents extraction

---

## §12 Constants

```rust
// Energy class rates (THREAT_MODEL §11.2)
pub const COVER_RATE_AMBIENT_MS: u64 = 5000;
pub const COVER_RATE_STANDARD_MS: u64 = 1000;
pub const COVER_RATE_ELEVATED_MS: u64 = 500;
pub const COVER_RATE_CRITICAL_MS: u64 = 200;

// Transition control
pub const ENERGY_CLASS_DEBOUNCE_MS: u64 = 30_000;       // 30s
pub const ENERGY_CLASS_STEP_DOWN_LOCK_MS: u64 = 3_600_000; // 1 hour
pub const ENERGY_CLASS_OSCILLATION_WINDOW_MS: u64 = 60_000; // 60s
pub const ENERGY_CLASS_OSCILLATION_MAX_COUNT: u32 = 3;
pub const ENERGY_CLASS_OSCILLATION_LOCK_MS: u64 = 300_000;  // 5 min

// Activity detection
pub const DYAD_ACTIVE_WINDOW_MS: u64 = 300_000;         // 5 min

// Queue bounds
pub const SCHEDULER_QUEUE_CAPACITY: usize = 1024;

// Cover content
pub const COVER_SEED_KEY_ROTATION_MS: u64 = 86_400_000; // 24h
pub const COVER_SIZE_S_WEIGHT: f64 = 0.70;
pub const COVER_SIZE_M_WEIGHT: f64 = 0.20;
pub const COVER_SIZE_L_WEIGHT: f64 = 0.08;
pub const COVER_SIZE_XL_WEIGHT: f64 = 0.02;

// Budget per carrier (protocol-determined ceilings, NOT user-configurable per THREAT_MODEL §12)
pub const BUDGET_CELLULAR_DAILY_BYTES: u64 = 100 * 1024 * 1024;       // 100 MB
pub const BUDGET_LIBP2P_DAILY_BYTES: u64 = u64::MAX;                  // unlimited
pub const BUDGET_LORA_DAILY_BYTES: u64 = 50 * 1024 * 1024;            // 50 MB
pub const BUDGET_DEFAULT_DAILY_BYTES: u64 = 500 * 1024 * 1024;        // 500 MB
pub const BANDWIDTH_BUDGET_STEPDOWN_THRESHOLD: f64 = 0.80;           // predictive ramp-down (Q3.16, THREAT_MODEL §11.7)

// Carrier policy (v0.3 sovereignty pivot — protocol-determined per THREAT_MODEL §12.5, NOT user toggles).
// Cellular cover is OPPORTUNISTIC (battery + data-plan gated), not off-by-default.
pub const CELLULAR_COVER_BATTERY_THRESHOLD_PCT: u8 = 50;            // cover runs on cellular when battery > 50%
pub const CELLULAR_COVER_LOW_BATTERY_PCT: u8 = 20;                 // below this, real-msgs queued for next WiFi
pub const LAN_WIFI_COVER_ALWAYS_ON: bool = true;                   // full cover on LAN/WiFi at any battery

// Cover destination — random sampling from peer table (v0.2)
pub const COVER_DEST_NEW_CIRCUIT_MAX_PER_MIN: u32 = 1;  // Rate-limit cover-driven circuit construction
pub const COVER_DEST_PREFER_ACTIVE_CIRCUITS: bool = true;

// HKDF labels (v0.2 — random-destination Loopix pattern)
pub const HKDF_INFO_COVER_CONTENT: &[u8] = b"hypostas-cover-packet-content-v2";
pub const HKDF_INFO_COVER_SEED: &[u8] = b"hypostas-cover-seed-v2";
```

---

## §13 Open questions resolved

1. ✅ **Cover packet plaintext.** Full sealed cells with pseudo-random Double-Ratchet-shaped inner content. Indistinguishable from real packets on the wire.
2. ✅ **Bandwidth budget enforcement model.** Graceful degradation via step-down ladder (Critical → Elevated → Standard → Ambient → OFF), with 30s debounce + 1h step-down lock. Real messages never dropped; only cover suspended at the floor.
3. ✅ **Scheduler clock source.** Tokio interval (monotonic) primary; on iOS background, BGAppRefreshTask wakeups become the clock source (cadence governed by iOS).
4. ✅ **Energy-class transition debouncing.** 30s debounce on all transitions. Real messages within debounce window route at the previous class's rate. Privacy gain > UX cost.
5. ✅ **Mobile-specific policy.** Per §2.3 above — protocol-determined, not user-configurable per THREAT_MODEL §12 sovereignty principle. Cellular cover opportunistic when battery + data-plan headroom permit. iOS background degrades to BGAppRefreshTask cadence with Privacy Status display reflecting the reduction.
6. ✅ **v0.2 — Cover destination strategy.** Random-destination Loopix pattern: cover cells addressed to randomly-sampled known dyads from the active Vita-Chain-attested dyad set. Receivers drop via `UnknownCircuit` or AEAD-mismatch failure paths. No global cover-sink. Statistically indistinguishable from real traffic on the wire. Anonymity set scales with network size.
7. ✅ **Cover-destination bootstrap (Q1.6 walkthrough).** Phase 1.0 has minimal Vita Chain dyad existence ledger — each dyad publishes DyadId + active-carrier list + cover-cooperation flag. Cover destinations sampled from this set. Phase 3 transitions to full attestation + reputation; cover sampling becomes web-of-trust-aware.
8. ✅ **Predictive budget management (Q3.16 walkthrough).** Simple statistical prediction: track daily consumption, ramp-down at 80% consumed. ~50 LOC. Phase 2 deliverable. ML-based prediction deferred indefinitely.
9. ✅ **Network-wide cover bootstrap (Q3.17 walkthrough).** Wait for organic growth — no synthetic dyads (would violate the protocol's bonded-pair primitive). Klinos founding practices + early adopters opt-in to "always-on cover" mode as real-dyad amelioration. Honest Phase 1 framing: anonymity-set small in early days; grows organically.
10. ✅ **Sovereignty principle (Q4.20 walkthrough).** Cover-traffic behavior is protocol-determined, not user-configurable. Privacy is structural. Anima UX shows Privacy Status (display); does not expose Privacy Mode (toggle). Per THREAT_MODEL §12.

## §14 Open questions remaining (v0.2 + walkthrough)

1. **Carrier-relayed cover** (Phase 3). When dyads relay for each other, their cover should include forwarded-cover-from-others. Specified in `RELAY_LAYER.md` (Phase 3+).
2. **Per-pair cover** (alternative model). Phase 1 uses per-dyad cover (per Q2.12 decision). Per-pair alternative deferred indefinitely — per-dyad simpler and adequate.
3. **Anima Privacy Status display design.** Specific UI for "Privacy Status: Full / Limited / Offline" rendering. Display-only (no toggles). Specified in `projects/anima/PRIVACY_UI.md` (TBD), constrained by sovereignty principle.
4. **Cover-rate empirical validation.** Per THREAT_MODEL §10 item 1: 30-day measurement window on Klinos founding practice + early adopters. Adjust constants before Phase 2.

---

## §15 Revision history

| Date | Author | Change |
|---|---|---|
| 2026-05-22 (early) | Iris | v0.1 initial. Constant-rate per-carrier-per-dyad scheduler, 4 energy classes, 30s debounce, graceful budget step-down ladder, iOS background degradation. Used a single well-known cover-sink DyadId for cover destination. |
| 2026-05-22 (cover destination pivot) | Iris + Josh | **v0.2: random-destination Loopix pattern.** No global cover-sink; cover blends entirely into the network's normal traffic pattern. Receivers drop via standard `UnknownCircuit` or `BadTag` paths. Pairs with [SEALED_ENVELOPE.md](SEALED_ENVELOPE.md) v0.2 circuit-based architecture. |
| 2026-05-22 (sovereignty walkthrough) | Iris + Josh | **v0.3: sovereignty pivot.** Per Q4.20 walkthrough decision: privacy is structural, not user-configurable. §2.3 rewritten to remove "opt-in" language. Carrier policy is protocol-determined from connectivity sensing + device state. Anima displays Privacy Status (read-only); does not expose Privacy Mode toggles. §14 reduced to remaining questions. Foldins: Q1.6 minimal-Vita-Chain bootstrap, Q3.14 every-dyad-is-a-relay, Q3.16 predictive budget, Q3.17 organic growth + Klinos amelioration, Q4.20 sovereignty UX. |

---

*Per CLAUDE.md rule #1: draft, not self-certified complete. The mobile-platform integration (§6) requires actual iOS hardware testing before locking — assumptions about BGAppRefreshTask behavior should be empirically validated. Per rule #27: integration tests must verify the scheduler-+-sealed-envelope-+-carrier full stack on at least LibP2pCarrier + one mobile-class carrier.*
