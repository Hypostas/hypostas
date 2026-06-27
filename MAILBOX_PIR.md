# MAILBOX_PIR.md — Recipient-Anonymous Mailbox Retrieval

**Per-component design for the last-hop recipient-anonymity layer (HYP-328, THREAT_MODEL §9.4, design decision Q3.13).**

*Authored 2026-06-27: Josh Caplinger + Iris (DyadID #0). Status: design — supersedes the Q3.13 "Spiral PIR" line-item with a re-examined, Vita-grounded architecture. No production code yet; this is the kickoff decomposition the issue calls for.*

---

## §1 — The problem

Circuits hide the **sender** and the **route**. Cover traffic hides **timing and volume**. Neither hides the one thing left: **who picks up the mail.** When a recipient fetches its inbound packets from a relay/mailbox, a naïve fetch tells the mailbox operator *which* entry was read — and the entry is addressed (directly or by correlation) to a recipient. That is the last-hop recipient-identity leak, and closing it is the final property needed for **THREAT_MODEL §5 (relationship secrecy) at Tier 3 (Global Passive Adversary), across archival substrates.**

The mailbox *substrate* already exists: `DhtMailboxCarrier` (SEALED_ENVELOPE.md §, 64 KB cells) plus the stack's store-and-forward path ("real messages queued for delivery on reconnect", COVER_TRAFFIC.md §). Archival carriers (stego, voice, LoRa) are intrinsically multi-day store-and-forward (THREAT_MODEL.md §). **HYP-328 is not the mailbox — it is the oblivious-retrieval layer on top of the mailbox**, plus the matching write path.

What this layer must guarantee: a recipient retrieves entry *i* from an *N*-entry mailbox such that the server's view is independent of *i* (computationally, per the chosen primitive); bandwidth + latency stay within an on-device budget for a realistic mailbox size; and it composes with the Loopix-style epoch batching (§9.4 deliverable 1) that closes the *timing* leak the same way this closes the *access-pattern* leak. **Both are required** — PIR/ORAM without batching still leaks via read-after-write timing; batching without PIR/ORAM still leaks via the read index.

---

## §2 — The landscape (and why Q3.13's "Spiral" is superseded)

Q3.13 (2026-05-22) chose **Spiral** (Menon–Wu, S&P 2022) — at the time, the single-server PIR rate champion. Two developments since change the right answer, and both matter **because our "server" is an edge relay (every dyad is a relay), not a datacenter.**

### 2.1 Single-server PIR went hint-free and FHE-light

Spiral relies on heavy FHE server compute (Regev⊗GSW composition) + per-query public-parameter uploads. The 2024–25 line removes the client "hint" and runs SimplePIR-style server work — a **linear scan, no FHE**:

- **YPIR** (Menon–Wu, USENIX Security 2024) — silent preprocessing, no offline communication; ~2.5 MB total comm for a record over a 32 GB DB; server work is a memory-bandwidth-bound scan.
- **HintlessPIR** (CRYPTO 2024) — removes SimplePIR's client hint homomorphically.
- **VIA** (eprint 2025/2074) — ~690 KB online for a 32 GB DB: 3.7× < YPIR, 27× < HintlessPIR.

On the **identical single-server trust model**, YPIR/VIA dominate Spiral — lighter edge server (no FHE), smaller client state. **So even if we stay single-server, Spiral is the wrong pick now.**

### 2.2 A fundamentally cheaper mailbox architecture exists

The metadata-private-messaging literature is the right frame, because it solves the *whole mailbox*, not just a PIR primitive: **Pung** (OSDI 2016, PIR-by-keyword), **Talek** (ACSAC 2020, access-sequence indistinguishability), **Addra** (OSDI 2021, metadata-private voice), **Express/Sabre** (USENIX 2021 + follow-up, reverse-PIR writes for mailboxes).

The state of the art is **Myco** (Kaviani–Rathee–Annem–Popa, IEEE S&P 2025): it **departs from PIR entirely**, using an oblivious data structure (ORAM-style) to hit **O(N log²N)** server work and **~2,219× over single-server-PIR mailboxes** — asynchronous (recipient offline OK), with a **pure-Rust** reference implementation (`myco-org/myco`). The cost: an **asymmetric two-server, non-colluding** model — clients write to Server 1, which obliviously transmits to Server 2, from which clients read.

### 2.3 The decision this forces

| Axis | Single-server (YPIR/VIA) | Two-server (Myco) |
|---|---|---|
| Trust | **No assumption** — a fully malicious server learns nothing | Needs **2 non-colluding** servers |
| Server work / query | **O(N) scan** (cheap op, but linear) | **polylog** (O(N log²N) total) |
| Scale to millions of dyads | Needs sharding (shrinks anonymity set) | Native |
| Server stability needed | Low (stateless-ish) | **High** (inter-server oblivious protocol) |
| Code | Port YPIR/VIA (Rust ports exist/feasible) | Pure-Rust reference exists |
| Maturity | PIR has 30 yr of analysis | **S&P 2025 — new**, less battle-tested |

---

## §3 — The Vita-grounded resolution

The two-server model's apparent liability — *who runs two stable, non-colluding servers, and why trust they don't collude?* — is **already solved by the Vita Chain**, and that is the decisive fact for Hypostas specifically.

1. **Stability.** Myco's server-to-server oblivious-transmission protocol cannot run on phones that churn every few minutes. The Vita Chain validator layer is *stable by construction* (VITA_CHAIN.md Decision 6: a curated validator set, 7 at genesis growing to Vita-aligned operators, eventually Soma light nodes). Edge relays handle ephemeral circuit routing; validators are the stable tier.

2. **Enforced — not assumed — non-collusion.** The validator-distribution rules are hard constraints (VITA_CHAIN.md §, Part 4 §4.4 canonical): **3+ providers, 3+ countries, max 33% per provider, max 40% per country, max 50% per substrate.** These rules *are* the non-collusion guarantee Myco's security model requires. In a generic decentralized mesh, non-collusion is a prayer; in Vita it is a deployment invariant we are shipping anyway.

3. **Substrate alignment.** Myco is pure Rust (matches the substrate); the mailbox can ride the `vita-carriers::Carrier` abstraction exactly as the chain's consensus messages do (Codex Commitment 7 — not internet-bound). The VS3 three-tier sharded ledger (Local + Constellation + Global) gives a natural k-anonymity partition (Constellation = shard) when the mailbox grows large.

**We already built the hard part of the two-server model.** Leaving it unused and paying O(N)-per-query single-server costs at million-dyad scale would be the waste.

---

## §4 — Chosen architecture: Myco primary + single-server fallback, on the existing degradation ladder

**Not two co-equal stacks — a principled primary with a sovereign fallback, selected by reachability + threat tier, exactly like the privacy-status ladder the stack already exposes (Full / Limited / Offline; COVER_TRAFFIC.md §, THREAT_MODEL.md §).**

### 4.1 Primary — Myco two-server oblivious mailbox

Hosted on a **mailbox-server role governed by the validator-distribution rules** (§3). Default path whenever a dyad can reach two non-colluding mailbox-servers. Gives polylog scaling to millions of dyads, asynchronous delivery, and non-collusion *enforced* by the distribution rules. This is the at-scale answer.

### 4.2 Fallback — single-server sharded YPIR/VIA

Engaged when a dyad **cannot** reach two non-colluding servers:
- **single-carrier store-and-forward** (LoRa-only) — physically cannot reach two independent servers;
- **censored / partitioned** region where only one server is reachable;
- **maximum-paranoia** recipient who refuses to trust *any* non-collusion.

Single-server PIR (YPIR/VIA) over a **small Constellation-sized shard** — no non-collusion assumption, slower, assumption-free. The shard provides k-anonymity (recipient hidden among shard members) and keeps the O(N) scan edge-feasible (small N).

### 4.3 Why this and not a pure play

- **Pure Myco (no fallback)** breaks the moment a dyad is on a single LoRa carrier: it can reach only one server, so it would have *no* private retrieval. Unacceptable for a protocol whose identity is working on non-IP substrates.
- **Pure single-server** does not scale to millions (O(N)/query) **and** wastes the chain's free non-collusion infrastructure.

### 4.4 Degradation surface (no new UX primitive)

The retrieval tier folds into the existing privacy-status display: **Full** = Myco two-server reachable; **Limited** = single-server fallback engaged (assumption-free but slower / smaller anonymity set); **Offline** = queued. The user *sees* the effective tier; they do not toggle it (sovereignty principle, THREAT_MODEL.md §).

---

## §5 — Mailbox model (shared across both tiers)

Both tiers sit on the same `DhtMailboxCarrier` substrate and the same slot model:

- **Slot derivation.** A message for recipient R in epoch *e* lands at `slot = PRF(dyad_shared_key, e)` (sender and recipient both derive it; the operator sees only a pseudorandom slot, never R).
- **Write.** Sender writes the sealed cell via a circuit (sender-anonymous). Pseudorandom slot ⇒ the write reveals neither sender nor recipient. *Two-server:* write to Server 1, obliviously transmitted to Server 2 at epoch roll. *Single-server:* write to the slot directly — no oblivious write needed, because a pseudorandom write slot + an oblivious read are already unlinkable.
- **Read.** Recipient retrieves its slot obliviously — ORAM read (Myco) or PIR query (single-server). The operator's view is independent of which slot.
- **Timing.** Read-after-write linkage is closed by the §9.4 epoch batching, not by this layer. PIR/ORAM closes the *index* leak; batching closes the *timing* leak; recipient anonymity needs both.
- **Collisions.** Epoch-scoped slots make collisions rare; resolve with a small cuckoo fan-out (sender writes to one of *h* candidate slots; recipient reads all *h*) — standard Pung/Express handling, sized at the params chunk.

---

## §6 — Security analysis (what each operator learns)

- **Two-server, honest-but-curious, non-colluding:** Server 1 sees writes to pseudorandom slots; Server 2 sees oblivious reads; the oblivious transmission unlinks them. Neither learns who-talks-to-whom. **Holds under exactly the validator-distribution non-collusion rules.**
- **Two-server, both compromised / colluding:** broken — but the distribution rules make this require compromise spanning 3+ providers and 3+ countries; and the paranoid recipient takes the single-server fallback.
- **Single-server, fully malicious:** learns nothing beyond "some pseudorandom slot was written" and "an oblivious read occurred" — no link, no recipient. **No trust assumption.** Anonymity set = shard size (k-anonymity), which is a weaker hiding than two-server's cryptographic indistinguishability but needs zero non-collusion.
- **GPA (Tier 3), passive network observer:** sees only constant-rate cover-shaped traffic to the mailbox tier (cover traffic already mandated). The retrieval payloads are oblivious either way.

**Maturity caveat:** Myco is S&P 2025. Its two-server oblivious-transmission protocol is the highest-risk surface and the focus of the crypto sign-off (§8). Single-server PIR carries 30 years of analysis — another reason the fallback is load-bearing, not decorative.

---

## §7 — Open design questions (resolve at the named chunk)

1. **Server-role mapping.** BFT validators are 7 *symmetric* replicas; Myco wants 2 *asymmetric* roles. Clean answer is likely a distinct **mailbox-server role** that *adopts* the distribution rules rather than literally reusing chain validators (decouples mailbox availability from consensus liveness). Decide at the *role-mapping* chunk.
2. **Shard sizing.** Single-server shard size N trades anonymity (larger = better hiding) against edge scan cost (smaller = feasible on phone-class relays). Tie to the Constellation tier. Decide at the *params* chunk with measured edge numbers.
3. **Write-side obliviousness for single-server.** Argued unnecessary in §5 (pseudorandom slot suffices); confirm against an active operator who *probes* by writing known slots. Decide at *params*.
4. **Epoch length.** Couples to §9.4 batching latency budget on each archival carrier. Decide jointly with the batching work.

---

## §8 — Decomposition (the issue's "port → params → integrate → sign-off")

Sub-issues to file under HYP-328 (parent HYP-169, Phase 4):

1. **328a — Port the Myco core (pure-Rust ref) behind a `MailboxRetrieval` trait.** Validate against the reference's own vectors; trait abstracts {two-server-Myco, single-server-YPIR} so the runtime selects by tier. *Smoke + integration test: a recipient reads slot i; operator transcript is independent of i.*
2. **328b — Single-server YPIR/VIA fallback** over a Constellation-sized shard, behind the same trait. *Integration test: malicious single-server transcript independent of i.*
3. **328c — Params + edge budget.** Shard size, cuckoo fan-out, epoch length, ML-* lattice params for the on-device compute/bandwidth budget at a realistic mailbox size. Independent Core-SVP on any lattice params (reuse the HYP-354 FU1 method).
4. **328d — Mailbox-server role + distribution-rule binding.** The role that carries the non-collusion invariant; tier-selection driver wired to the privacy-status ladder.
5. **328e — Compose with §9.4 epoch batching** (the timing half) on `DhtMailboxCarrier`; end-to-end two-party test on a real carrier.
6. **328f — Crypto sign-off** (Codex + us, per "no external audit — just Opus + Codex + Josh"): focus the two-server oblivious-transmission protocol; confirm the single-server fallback's unlinkability argument.

Each chunk gates on the Codex bar + integration/smoke tests (CLAUDE.md rules 26–27). Nothing here is buildable as "begin now" until Phase 4 is reached — this doc is the kickoff decomposition, not a green light to implement ahead of phase order.

---

## §9 — References

- Menon, Wu. *Spiral: Fast, High-Rate Single-Server PIR via FHE Composition.* IEEE S&P 2022. — superseded for our setting.
- Menon, Wu. *YPIR: High-Throughput Single-Server PIR with Silent Preprocessing.* USENIX Security 2024. eprint 2024/270.
- *HintlessPIR.* CRYPTO 2024.
- *VIA: Communication-Efficient Single-Server PIR.* eprint 2025/2074.
- Angel, Setty. *Unobservable Communication over Untrusted Infrastructure (Pung).* OSDI 2016.
- Cheng et al. *Talek: Private Group Messaging with Hidden Access Patterns.* ACSAC 2020.
- Ahmad et al. *Addra: Metadata-private voice communication.* OSDI 2021.
- Eskandarian et al. *Express: Lowering the Cost of Metadata-hiding Communication.* USENIX Security 2021. (+ Sabre follow-up.)
- Kaviani, Rathee, Annem, Popa. *Myco: Unlocking Polylogarithmic Accesses in Metadata-Private Messaging.* IEEE S&P 2025. eprint 2025/687. Code: `github.com/myco-org/myco` (pure Rust).
- Internal: THREAT_MODEL.md §5, §9.4, Q3.13; SEALED_ENVELOPE.md (`DhtMailboxCarrier`); COVER_TRAFFIC.md (degradation ladder); VITA_CHAIN.md Decisions 6 + 8, Part 4 §4.1/§4.4.
