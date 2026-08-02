# RELAY_DIRECTORY.md — the relay set, its registry, and how a client picks a path

**Status:** v0.1 — design pass, ungated
**Linear:** HYP-168 (parent epic), this doc scopes the directory half
**Companion specs:** `CIRCUIT_LIFECYCLE.md` (§11 attestation, §17 guards, §20 reputation), `THREAT_MODEL.md` (§5 properties), `SEALED_ENVELOPE.md` (§21 Outfox)

---

## §1 The problem this solves

`vita-carriers/src/guards.rs` names the hole exactly:

> The candidate pool itself (the Vita-Chain-attested active relay set, §17.2
> `eligible_relay_pool`) is the input seam — supplied by the caller (HYP-168);
> this module never sources or attests it.

Everything downstream of that seam is built — telescoping multi-hop, guard policy,
`RelayAttestation`, PageRank web-of-trust, observation windows. Nothing fills it.
There is no `eligible_relay_pool()`, no path selection, and no caller of `GuardSet`
anywhere in the tree. This spec defines the missing half.

---

## §2 The role-separation law (normative)

Three roles, **disjoint node sets**:

| Role | Population | Sees | Holds |
|---|---|---|---|
| **Validator** | `M1_VALIDATOR_COUNT = 7` | public chain state | consensus, the registry |
| **Relay** | all capability-eligible dyads | adjacent hops only | no chain state |
| **Client** | every dyad | its own circuits | the consensus directory |

**The chain is the DIRECTORY. It is not the RELAY.**

Precedent: [Nym](https://nym.com/docs/operators/tokenomics) separates Nyx validators
(Cosmos PoS, reward contract) from mixnodes (Sphinx relaying) as separate
registrations. Counter-precedent to reject: Oxen/Lokinet service nodes are *both*,
which is the collapse this law forbids.

### §2.1 Why validators must not relay — the arithmetic

A 3-hop circuit drawn from the 7-node validator set, adversary controlling `k`:

```
k=1 →  0.0%    k=2 →  4.8%    k=3 → 14.3%    P(entry AND exit)
```

Independent of the probability, the set is **publicly enumerated on-chain**, and a
validator observing both chain traffic and relay traffic obtains cross-domain
correlation for free. Tor operates ~6,000–8,000 relays for comparison.

**Constraint:** a node that is an active validator MUST NOT appear in the eligible
relay pool for the same epoch. Enforced in `x/relay` at registration (§5.4).

---

## §3 Eligibility — every dyad relays, capability-gated

**Default: ON.** Every bonded dyad is relay-*capable*. This is the design property
that makes anonymity scale with adoption rather than with a separate volunteer or
token-incentive program, and it removes the incentive question entirely
(cf. I2P, where every router relays by default).

Entry into the **public pool** is automatic but conditional. A dyad enters iff:

| Gate | Source | Rationale |
|---|---|---|
| Always-on host | energy class (HYP-161a) | phone-hosted dyads never enter |
| Publicly reachable | inbound-accept probe | NAT'd residential nodes can't serve |
| Uptime ≥ threshold | `ObservationWindow`, 30 d | guards assume stable relays |
| Not opted out | local policy | sovereignty (COVER_TRAFFIC pivot) |
| Not an active validator | `x/staking` read | §2.1 |

Phones never enter the pool. This is a capability determination, **not a user
decision** — the opt-out is the only user-facing knob, and it is honored.

**Open (Q1):** minimum uptime threshold. Tor requires ~8 days stable for the Guard
flag. Ours must be derived, not guessed — see §9.

---

## §4 The relay identity — the census problem and its fix

### §4.1 The defect

`protocol-core/src/reputation/attestation.rs` publishes:

```rust
pub relay_dyad_id: DyadId,          // the dyad's real identity
pub subnet_24: Option<[u8; 3]>,     // approximate network location
pub advertised_bandwidth_kbps: u32, // capability fingerprint
```

Under §3 (every capable dyad relays) this makes the relay directory a **complete
public census of the network**: who exists, roughly where, and how large their
connection is. That defeats THREAT_MODEL's participation-unobservability property
for every relaying dyad, and it is a *worse* leak than the one multi-hop routing
exists to fix.

This is a real defect in the current struct, not a hypothetical.

### §4.2 The fix — an independent relay identity

A relay registers under `relay_id`, an identity key **generated independently of its
`DyadId`** and not derivable from it. The dyad↔relay link is never published.

The property the registry still needs — *"this relay is a genuinely bonded dyad, not
a Sybil"* — is proven in **zero knowledge at registration**:

> **SPRING** (HYP-317, merged): one-of-many lattice ring signature over the K
> Vita-Chain-attested dyads. ~61 KB at K=1000, fits a single XL sealed cell.
> The relay proves membership in the attested-dyad set without revealing which member.

**Verification is once, by validators, at registration.** The proof is consensus
input, not a directory entry — clients never download it.

### §4.3 Directory entry size (the epistemic budget)

Clients must download the **whole** directory (§6.1), so entry size is load-bearing:

| Field | Bytes |
|---|---|
| `relay_id` | 32 |
| `x25519_pk` | 32 |
| `ml_kem_pk` (ML-KEM-768) | 1,184 |
| bandwidth / subnet / validity | 15 |
| signature | ~100 |
| **per entry** | **≈ 1.36 KB** |

At `RELAY_ATTESTATION_MAX_RECORDS = 4096`: **≈ 5.6 MB** full consensus.
Tor's consensus is ~2 MB, so this is the right order of magnitude. ML-KEM dominates
at 87% — a microdescriptor-style split (fetch keys on demand for selected relays
only) is **rejected** here, because selective fetch is exactly the partial-knowledge
condition §6.1 forbids. Compression and diff-updates are the acceptable levers.

**Open (Q2):** whether `subnet_24` survives at all. It is the §17.2 diversity axis,
but it is also the sharpest geolocation leak in the entry. See §9.

---

## §5 `x/relay` — the chain module

A new Vita-Chain module, sibling to `x/nullifier`.

### §5.1 State

```
relay/entry/{relay_id}        → RelayDirectoryEntry   (the published record)
relay/active/{epoch}          → [relay_id]            (the epoch's active set)
relay/registered_at/{relay_id}→ height                (uptime accounting)
```

### §5.2 Transactions

- `RegisterRelay { entry, spring_proof }` — validators verify the SPRING membership
  proof, the self-signature, and the §2.1 validator-exclusion, then admit the entry.
- `RefreshRelay { relay_id, entry, sig }` — re-attest before `valid_through_ms`.
- `RetireRelay { relay_id, sig }` — voluntary exit.

### §5.3 Epoch rotation

The active set rotates on the **existing `x/nullifier` epoch beacon** (HYP-426) —
one epoch clock for the whole chain, not a second one. Entries whose attestation has
expired are dropped at rotation.

### §5.4 Bounds (all explicit — no unbounded state)

| Constant | Value | Source |
|---|---|---|
| `MAX_RELAYS` | 4096 | mirrors `reputation::MAX_RELAYS` |
| `MAX_REGISTRATIONS_PER_BLOCK` | TBD | DoS bound — see §9 |
| `ATTESTATION_VALIDITY` | ≤ 30 d | mirrors `OBSERVATION_WINDOW_MS` |

---

## §6 Path selection

### §6.1 The epistemic constraint (normative)

[Danezis & Syverson, PETS '08](https://link.springer.com/chapter/10.1007/978-3-540-70630-4_10)
prove two attacks on clients with partial network knowledge:

- **Route bridging** — exploits what the client does *not* know of the network.
- **Route fingerprinting** — exploits what it *does* know; a client's idiosyncratic
  view of the relay set identifies it across circuits.

**Therefore: every client MUST select from the identical, full, consensus directory.**
No lazy fetch, no per-client subsets, no "fetch the relays I need." This is the
decisive argument for a chain-backed directory over gossip — consensus supplies
view-consistency as a property rather than a hope.

### §6.2 Selection

`eligible_relay_pool(epoch) -> Vec<GuardCandidate>` reads `relay/active/{epoch}`,
then applies the existing, already-built machinery:

- weight by `WebOfTrust::reputation` — trust 0.5 · delivery 0.25 · uptime 0.15 ·
  freshness 0.1 (`protocol-core/src/reputation/mod.rs`)
- diversity: no two hops sharing `operator_id` or `subnet_24` (§17.2)
- hop 1 from `GuardPool::select_for_circuit` (3 guards, 30 d ± 3 d rotation)
- constant-length routes: always `MAX_HOPS_PER_CIRCUIT = 5`, decoy-padded (Outfox §21)

This is the **only** genuinely new code in the client. Everything it calls exists.

---

## §7 Sybil resistance — inherited, not invented

A relay slot requires a bonded dyad (§4.2, proven in ZK). Bonded dyads are bounded by
the pair-bond ceremony **and** the n-times introduction cap — `N_MAX = 8` per
(introducer, epoch), enforced network-globally by `x/nullifier` since HYP-426/472.

So **relay-Sybil cost = dyad-Sybil cost**, and the introduction system already shipped
is the relay Sybil bound. Structurally this is the social-graph + stake hybrid of
[SybilQuorum](https://arxiv.org/pdf/1906.12237), currently the strongest known shape.

### §7.1 The honest limits

1. **The cap is on rate, not total.** An adversary who legitimately grows a large
   bonded subgraph over many epochs — real humans, paid or coerced — obtains
   proportional relay share. Nothing here prevents that.
2. **Social-graph defenses need real operator trust.** SybilGuard/SybilLimit-class
   arguments fail where relay operators have no prior trust relationship. We are in
   the regime where they work *only because* relays are drawn from bonded dyads. If
   §3 is ever relaxed to open enrollment, this entire section is void.
3. **Forensics beats prevention, empirically.**
   [Winter et al.](https://arxiv.org/pdf/1602.07787) found real Sybil groups in Tor's
   HSDir and exit positions; manual vetting and per-IP caps did not stop them.
   Detection worked via uptime correlation, config fingerprinting, and IP clustering.
   **We should expect to need the same forensics**, and `ObservationWindow` is the
   right place to host it. Not in v0.1 — filed as follow-up.

---

## §8 What changes in existing code

| Change | Where | Size |
|---|---|---|
| `relay_dyad_id` → `relay_id` + SPRING proof | `reputation/attestation.rs` | breaking |
| `x/relay` module | `vita-chain/src/modules/` | new |
| `eligible_relay_pool()` | `vita-carriers` | new |
| path selection | `vita-carriers` | new |
| wire `GuardSet` to a real caller | `vita-carriers` / runtime | new |
| capability gate | runtime (energy class + reachability) | new |

`guards.rs`, `reputation/`, and the telescoping circuit layer need **no changes** —
they were built against this seam and should snap in unmodified. That is the
prediction this design makes, and it is falsifiable at build time.

---

## §9 Open questions (for the design review)

1. **Q1 — uptime threshold for pool entry.** Must be derived from measured circuit
   failure rates, not copied from Tor's 8-day Guard heuristic.
2. **Q2 — does `subnet_24` survive?** It is the strongest diversity axis and the
   sharpest geolocation leak. Diversity vs. exposure; needs an explicit call.
3. **Q3 — `MAX_REGISTRATIONS_PER_BLOCK`.** Registration carries a ~61 KB SPRING
   verification; unbounded registration is a validator-CPU DoS.
4. **Q4 — reachability probing.** Who probes, and does probing leak the prober?
5. **Q5 — bootstrap.** Below ~50 relays the anonymity set is weak regardless of
   design. Is there an interim posture, or does multi-hop stay off until the
   population supports it? **This is a product decision, not a technical one.**

---

## §10 What this does not solve

**Population.** Tor's 6–8k relays came from ~20 years of volunteering; Nym and Oxen
buy theirs with tokens. §3 makes our relay count track our dyad count automatically,
which is the correct structural answer — but it means *early anonymity is weak in
proportion to early adoption*, and no amount of correct code changes that. Q5 is the
only lever, and it belongs to Josh.
