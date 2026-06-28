# MYCO_INTEGRATION.md — Wiring the Myco tier live

**Status:** design, 2026-06-27. Companion to `MAILBOX_PIR.md` (the tier-choice design) and the
completed Myco port (`mailbox-pir/src/myco/`, HYP-328a). Resolves *how* the built-but-isolated Myco
2-server ORAM becomes a live, runtime-selectable mailbox tier — the work spanning HYP-328d/328e.

This doc exists because a finding during 328a closeout changes the integration shape: **the
`MailboxRetrieval` trait does not fit Myco**, and the live transport needs infrastructure that does
not yet exist. Settle the architecture here before building it.

---

## §1 — The finding: `MailboxRetrieval` is PIR-shaped; Myco is ORAM

`mailbox-pir/src/lib.rs::MailboxRetrieval` is a **stateless PIR** contract:

```
query(db_len, index, rng) -> (Vec<Query>, ClientState)
answer(query, db: &MailboxDb) -> Answer          // over a flat, replicated N-cell DB
reconstruct(state, answers) -> Option<Cell>
```

`xor_pir::TwoServerXorPir` fits it exactly (query = bitvector, answer = XOR of selected cells,
reconstruct = XOR). It is the right shape for the **single-server / IT-PIR tiers**, where the server
holds a flat replicated `MailboxDb` and the client hides *which index* it reads.

Myco is **not** that. Myco is a stateful 2-server tree ORAM: per-dyad `setup` keys, a `write` path
(client → S1 `queue_write` → batch eviction → oblivious transmission → S2), a `read` path
(notifications → path read → double-decrypt → bucket-signature verify), epochs, a sliding PRF-key
window, and a notification ring. There is no flat `MailboxDb` the two servers replicate, and no
`query/answer/reconstruct` round. Forcing Myco behind `MailboxRetrieval` would be a leaky abstraction
(CLAUDE.md "no bad abstractions") — the `db: &MailboxDb` argument is meaningless for Myco.

**`MailboxRetrieval` stays the read mechanism of the PIR-family tiers (xor_pir, YPIR/328b). It is not
the cross-tier seam.** The 328a issue text ("port behind a `MailboxRetrieval` trait so the runtime
selects by tier") is honored at a *higher* layer — see §2.

## §2 — The real seam: the §5 mailbox model as a `Mailbox` trait

`MAILBOX_PIR.md` §5 already names the shared contract — both tiers sit on the **same slot model**:
*write a sealed cell to a pseudorandom slot; retrieve your slot obliviously.* That is the seam, one
level above the retrieval mechanism:

```rust
/// A recipient-anonymous mailbox tier. The runtime selects an impl by privacy tier
/// (Full = two-server Myco; Limited = single-server PIR) without call sites caring which.
pub trait Mailbox {
    /// Sender-side: deposit a sealed cell for `recipient` in the current epoch. Sender anonymity is
    /// already provided by the circuit this runs over; this call only places the cell at its slot.
    fn deposit(&mut self, recipient: &str, sealed_cell: &[u8]) -> Result<(), MailboxError>;

    /// Recipient-side: obliviously retrieve this dyad's cells for the last `delta` epochs. The
    /// operator transcript MUST be independent of which slot(s) actually held mail.
    fn retrieve(&mut self, delta: usize) -> Result<Vec<Cell>, MailboxError>;

    /// The effective privacy tier this impl provides right now (drives the §4.4 status ladder).
    fn tier(&self) -> MailboxTier; // Full(TwoServer) | Limited(SingleServer)
}
```

**Sync, not async (decision 2026-06-27).** The Myco protocol is synchronous (the port is sync), so
`Mailbox` is a sync trait. Async lives only at the two real boundaries: the RPC-`Server*Access`
internals `block_on` the `Carrier` (§3), and the async runtime invokes `Mailbox` via
`tokio::task::spawn_blocking` (mailbox retrieval *is* a blocking multi-round-trip). No `Send` bound on
the trait — the in-process local impl is `!Send` (single-thread tests); the RPC impl is `Send` and is
the one the runtime `spawn_blocking`s. The recipient is the per-tier id (the Myco contact id; the
runtime maps `DyadId → contact-id` above this layer).

- **`MycoMailbox`** implements `Mailbox` over the ported `myco::client::Client` + the server-access
  traits. `deposit` = `Client::write`; `retrieve` = `Client::read` (the epoch/notification machinery
  is internal). The per-dyad key `setup` is established once at channel creation.
- **`PirMailbox`** implements `Mailbox` over `MailboxRetrieval` + `slot::derive_slot`: `deposit` =
  write the cell to `derive_slot(key, epoch)`; `retrieve` = `query/answer/reconstruct` at that slot.

The runtime holds a **`Box<dyn Mailbox + Send>`** chosen by reachability (two non-colluding
mailbox-servers → `MycoMailbox`; else `PirMailbox`), exactly the §4.4 degradation surface. The `+
Send` is required, not incidental (DESIGN-review P2): the runtime drives `deposit`/`retrieve` via
`tokio::task::spawn_blocking`, whose closure must be `Send + 'static`, and `Send` is erased from a bare
`dyn Mailbox` trait object even when the concrete `MycoMailbox`/`PirMailbox` is `Send` — so the marker
must be on the object type. The trait itself stays `Send`-bound-free (so the `!Send` single-thread
`local` test object remains a valid `Box<dyn Mailbox>`); only the runtime-spawned path widens to `+
Send`, which both production impls satisfy. `MycoMailbox`'s `Arc<dyn Carrier>` field is `Send + Sync`
**because the `Carrier` trait is declared `pub trait Carrier: Send + Sync`** — the supertrait bound
rides on the `dyn Carrier` object, so no `+ Send + Sync` is needed at the field's use site (this is the
opposite of the `dyn Mailbox` case above, where the trait is deliberately bound-free and the marker
must be added at the *object* type); `PirMailbox`'s `MailboxRetrieval`/`MailboxDb` fields are likewise
`Send`. **This is the trait 328a's intent points at** — it just lives above `MailboxRetrieval`, not as
it.

## §3 — The transport: Myco servers are *services*, not a carrier

The ported `client::Server1Access` / `client::Server2Access` / `server1::Server2WriteAccess` are RPC
seams. `local::LocalServer{1,2}Access` (the shipped in-process bridge) satisfies them for one-process
tests. Live, the two Myco servers are **stateful services** on the **mailbox-server role** (§7.1,
HYP-328d) — they hold the tree and run eviction; the client issues RPCs.

The existing `vita_carriers::Carrier` (`send(dest, bytes)` / `poll(my_dyad)`) is **packet delivery**,
not a server-RPC surface. `DhtMailboxCarrier` is a slot-keyed DHT store (`key_for(recipient, window)`
→ put/poll) — that is precisely the **single-server** substrate (`PirMailbox`'s `deposit`/`retrieve`
ride it directly). Myco's server RPCs (`queue_write`, `batch_write`, `read`, `read_notifs`,
`get_prf_keys`) need a **request/response layer over a Carrier**:

```
RpcServer{1,2}Access (client side): serialize the call → Carrier::send to the mailbox-server's
  DyadId → await the response packet (Carrier::poll / a reply slot) → deserialize.
Mailbox-server role (server side): poll inbound RPC packets → dispatch to a live Server1/Server2 →
  send the response. S1's batch eviction runs on the server's epoch timer.
```

This RPC binding is new code but small and mechanical: a versioned `MycoRpc` enum (one variant per
server method), `serde`/bincode framing, and the two `RpcServer*Access` impls. It is the only glue
between the (done) Myco protocol and the (done) Carrier substrate.

## §4 — 328e proper: compose with §9.4 epoch batching (the timing half)

PIR/ORAM closes the *index* leak; it does **not** close read-after-write *timing* linkage. §9.4 epoch
batching is the timing half: deposits accumulate and S1's `batch_write` fires on a fixed epoch
boundary (not per-message), so a write and the matching read are unlinkable in time. Myco's batch
model already *is* epoch-structured (`batch_init` → deposits → `batch_write`); 328e = drive that
boundary from the cover-traffic/epoch clock (COVER_TRAFFIC §2) over Myco's **queued point-to-point
carrier** (§7.1 — *not* `DhtMailboxCarrier`, which is the single-server `PirMailbox` substrate), and
prove it with the **end-to-end two-party test on a real carrier** (the §8.5 acceptance test): a
recipient reads slot *i*; the operator transcript is independent of *i* AND of write-to-read timing.

## §5 — Build order (each a gated chunk; integration + smoke tests per rule #27)

> Status (2026-06-28): the network-live Myco implementation is **complete + gate-clean**. Chunks 1, 3,
> and 4 are built (mailbox-pir + hypostas-network), and chunk 5's two named deliverables (epoch-batching
> composition + the two-party-on-a-real-carrier test) landed with chunk 4. The only remaining item is
> chunk 5's *full* §4 privacy assertion, which is gated on the HYP-328c notification-cardinality
> threat-model decision (below). Chunk 2 (the single-server `PirMailbox` tier) is independent + still open.

1. ✅ **`Mailbox` trait + `MycoMailbox` over the local bridge.** The seam (§2) + the in-process impl
   reusing `local::LocalServer*Access`. *Done — `mailbox-pir/src/mailbox.rs`, gate-clean.*
2. **`PirMailbox` over `xor_pir` + `DhtMailboxCarrier`.** The single-server tier on the real DHT
   store. Smoke: malicious-single-server transcript independent of *i*. *Buildable now (independent).*
3. ✅ **`MycoRpc` framing + the dispatch core.** The wire types, version+bincode framing, correlation-id
   framing, chunked S1→S2 transmission with exactly-once `BatchAccept`, and `role::dispatch_s1`/
   `dispatch_s2`/`dispatch_s2_read` (the sync server-side handlers). *Done — `mailbox-pir/src/myco/{rpc,
   role}.rs`, gate-clean.*
4. ✅ **Mailbox-server role — live carrier binding (HYP-328d).** The kind-tagged `CarrierMsg` envelope,
   the sync↔async client bridge (`carrier_client_access` over `RpcEndpoint`), the unified S2 role
   (`run_server2`: client reads + the authenticated dedicated-S1↔S2 batch stream) and the S1 role
   (`run_server1_blocking`: client writes + the epoch timer driving `batch_write` over `CarrierS1ToS2`),
   per **§7**. *Done — `hypostas-network/src/myco_transport.rs`, gate-clean; smoke + 3-party deposit→
   retrieve + timeout integration tests pass.* The tier-selection driver wired to the §4.4 ladder
   remains a small runtime follow-up.
5. **328e — epoch-batching composition + two-party test on a real carrier.** ✅ *Both named deliverables
   done with chunk 4:* the epoch-batching composition is `run_server1_blocking`'s epoch timer (deposits
   accrue, `batch_write` fires on the fixed boundary), and the two-party-on-a-real-carrier test is
   `e2e_deposit_and_retrieve_over_carrier`. **Remaining:** the full §4 assertion — *operator transcript
   independent of i AND of write-to-read timing*. The **message** read path is fixed-width by
   construction (`Client::read` reads one path + `fake_read` fills, regardless of mail), and epoch
   batching unlinks write-from-read timing. The one open leg is **notification-read cardinality**: the
   `read_notifs` count is not yet padded (a documented `client.rs` note) — that is the **HYP-328c**
   threat-model decision (§6 below), not an implementation gap. The §8.5 transcript-invariance
   regression test should be written once 328c fixes the notification-read width.

The §7 design was the implementation plan for chunk 4 (and the carrier half of chunk 5); it is now built.

### §5.1 — Gating item for the full §4 assertion: HYP-328c (notification cardinality)

`Client::read`'s **message**-path read is fixed-width (oblivious), but its **notification** read
(`read_notifs`) issues a per-epoch location count that today tracks the recipient's actual notification
count rather than a fixed width — so a malicious operator could in principle infer notification
cardinality. Padding it to a fixed width (e.g. per-client capacity `Q`, with re-randomized notification
slots) closes the leak but costs bandwidth; the right width is a **threat-model decision (HYP-328c)** —
Josh's call (like the other threat-model decisions). Until it is decided + implemented, the §8.5
"transcript independent of i" regression test cannot be honestly asserted in full, so it is **tracked**,
not written against the current (knowingly-partial) read width. This is the one place the live Myco tier
is not yet fully oblivious; everything else in chunks 1–5 is done.

## §6 — Depth decision (resolved 2026-06-27)

The original fork was library-live (chunks 1–2) vs network-live (chunks 1–5). **Decision: network-live**
— the full mailbox-server role + RPC-over-carrier + batching (328d + 328e). Execution since: chunks 1
and 3 + chunk 4's sync dispatch core are built + gate-clean (§5 status); chunk 4's live carrier binding
is designed in §7 and is the next code. The library-live milestone (a usable in-process `Mailbox`) was
passed at chunk 1.

---

## §7 — Carrier transport architecture (chunk 4 design; HYP-328d)

> Status: chunks 1, 3a/3b/3c (the `Mailbox` seam, the `MycoRpc` wire types, framing, correlation-id
> framing, chunked S1→S2 transmission with exactly-once `BatchAccept`, and the sync **dispatch core**
> `role::dispatch_s1`/`dispatch_s2`) are built + gate-clean in `mailbox-pir`. §7 specifies the *live*
> binding — the async `Carrier` poll loops + the sync↔async boundary — that chunk 4 builds in
> `hypostas-network`. The hard part is not the RPC; it is the **concurrency model** (a sync
> mailbox-pir Client/Server over an async, pull-based `Carrier`). This section locks that model before
> code, because the analogous *sync* hardening (the dispatch core) took nine gate rounds — the async
> version is strictly harder and must not be discovered by trial.

### §7.1 Topology + addressing

Three roles, each a `DyadId`:

- **Client** (a dyad) — issues `queue_write` to S1 and `get_prf_keys`/`read_notifs`/`read` to S2.
- **S1** (write server, a service `DyadId`) — accepts `QueueWrite`; on its epoch timer runs
  `batch_init`/`batch_write`, transmitting the evicted batch to S2.
- **S2** (read/storage server, a service `DyadId`) — accepts the client read legs + S1's
  `TransmitBatchChunk` stream.

S1/S2 service `DyadId`s are configuration (the validator-distribution + non-collusion rules of the
threat model govern *who* runs them — out of scope here; this is the wire binding only).

**Substrate requirement (DESIGN-review P1a — `DhtMailboxCarrier` is NOT Myco's carrier).** Myco RPC is
**multi-message-per-epoch**: several client↔S2 reads, and an S1→S2 *stream* of `TransmitBatchChunk`s,
all to the same service `DyadId` within one window. `DhtMailboxCarrier` keys storage by
`(recipient, window)` only — a single overwriting slot — so concurrent frames to one dyad would clobber
each other and the advancing poll cursor would miss them. Myco therefore requires a **reliable,
per-message (queued / point-to-point) carrier** (libp2p-class: each `send` is an independent delivery,
in-order within a link). The slot-overwriting `DhtMailboxCarrier` is precisely the **single-server
`PirMailbox`** substrate (its `deposit`/`retrieve` *is* the slot model) — not Myco's. The in-memory
**shared-bus** test carrier (§7.6) models the queued semantics (a per-`DyadId` FIFO), not the slot
semantics, so tests exercise the real contract.

### §7.2 The sync↔async boundary (the crux)

`mailbox-pir` is **sync** (the port is sync; `Mailbox`, `Server*Access`, `Server2WriteAccess` are
sync traits). `Carrier` is **async** (`async fn send`/`poll`). Three impedance sites, each made safe
**without a mutex held across an `.await`** (each stateful object is owned by exactly one execution
context):

| Site | Sync caller | Async need | Bridge | Why safe |
|---|---|---|---|---|
| Client RPC | `Server1Access`/`Server2Access` | `send` + poll-for-reply | the whole sync `Client` runs in `spawn_blocking`; its `*Access` use a captured `Handle` + `block_on` | a `spawn_blocking` thread is **not** a runtime worker, so `Handle::block_on` is legal |
| S1→S2 xmit | `Server2WriteAccess::write` (inside `Server1::batch_write`) | `send` chunks + await Ack | the epoch driver runs `batch_write` under `tokio::task::block_in_place` | `block_in_place` + `block_on` is the sanctioned multi-thread-runtime pattern for sync-in-async |
| Dispatch | `dispatch_s1`/`dispatch_s2` | *none* — pure state read/write | called inline in the async loop | no carrier I/O inside dispatch itself (only the response `send`, which is `await`ed in the loop) |

**Ownership, not locking.** S2 is owned by its task; S1 is owned by its task; the client by its
blocking thread. No `Arc<Mutex<Server*>>` shared across the run loop and the epoch timer — they are
the same single-threaded `select!` loop (§7.4), so S1 state is touched by one context at a time. This
is the dropped-`Mutex`-across-`await` rule (CLAUDE.md) honored by construction.

### §7.3 The request envelope: correlation id + explicit reply address

`Carrier` is fire-and-forget + pull (`poll` returns *all* pending packets) and its `InboundPacket.from`
is **`Option<DyadId>`** — `None` for carriers that don't carry substrate sender identity. So the server
**cannot** rely on `from` to address its reply (DESIGN-review P1b). A node's inbound stream also mixes
two packet *shapes* — requests it must serve, and replies to requests it itself sent (S1 is both a
server for clients **and** a client of S2, so its stream carries both). The bridge therefore frames
every carrier packet as a **kind-tagged** `CarrierMsg`, so a node demuxes on shape before decoding
(DESIGN-review): a stale/late reply is never mis-decoded as a request, and vice-versa.

```
enum CarrierMsg {
    Request(RpcEnvelope { reply_to: DyadId, frame: Vec<u8> }), // frame = frame_correlated(id, encode(req))
    Response(Vec<u8>),                                         // bare correlated frame_correlated(id, encode(resp))
}
```

`reply_to` is the requester's pickup `DyadId` (a routing address, not a trust assertion — request
authenticity is the sealed-envelope/circuit layer's job); a reply needs no `reply_to` (the requester
matches it by `id`). `CarrierMsg`/`RpcEnvelope` live in the **hypostas-network bridge** (they need
`protocol_core::DyadId`); `mailbox-pir` stays carrier-agnostic (`frame_correlated` is just `id ++
payload`). **Poll-loop demux (every node):** decode `CarrierMsg`; `Request` → server-dispatch + reply
`Response` to `reply_to`; `Response` → match `id` to a pending waiter (the client wait loop, or S1's
S1→S2 Ack wait), else **drop** (a stale reply after a timeout/retry — dropped, never decoded as a
request).

- **Client wait loop** (sync, under `block_on`): `send(Request{me, frame})`, then loop `{ for p in
  carrier.poll(me): match CarrierMsg: Response(f) if split_correlation(f)==my_id → decode + return;
  else buffer/ignore; if Instant::now() > deadline → Timeout; sleep(poll_interval) }`. A bounded buffer
  holds any non-matching packet; the mailbox client is **sequential** (one RPC at a time) so it is
  normally empty — it exists only so a shared inbound stream is never silently dropped.
- **Demux caveat (documented, not built in chunk 4):** in the live runtime the carrier inbound is
  shared with *all* (non-Myco) traffic too. A single demux (the `NetworkManager` poll loop) must route
  each polled packet to the right subsystem by `(kind, correlation_id)`. Chunk 4 builds + tests the
  bridge against a carrier whose poll stream is **Myco-only** (the shared-bus test carrier's
  per-`DyadId` FIFO); the shared-runtime demux is the chunk-4→runtime integration seam. Its acceptance
  criteria are the §7.3 `(kind, correlation_id)` routing contract above; a HYP follow-up issue is filed
  when chunk 4 lands and the runtime wiring begins (this §7.3 caveat is the spec-of-record until then).

### §7.4 The server roles

Both demux `CarrierMsg` by kind (§7.3), dispatch `Request`s, and reply to the envelope's `reply_to`
(never `from`):

- **S2 role** — a pure async loop, no `block_on`: `loop { for p in carrier.poll(s2): match CarrierMsg:
  Request(env) → { (id,frame)=split_correlation(env.frame); resp=dispatch_s2(decode(frame),&mut s2,
  &mut reassembler); carrier.send(env.reply_to, Response(frame_correlated(id, encode(resp)))) };
  Response(_) → ignore (S2 issues no requests, so any reply is stray) ; sleep }`. `dispatch_s2` already
  absorbs the chunked `TransmitBatchChunk` stream + the exactly-once `BatchAccept` logic. S2 never
  awaits mid-dispatch, so the single loop has no internal race.
- **S1 role** — a `select!` over two arms on one task (so S1 state is single-owner, no `Mutex`). S1's
  inbound stream carries **both** kinds (client `Request`s *and* S2's `Response` Acks to S1→S2 sends):
  - inbound: `Request(env)` → `dispatch_s1`(QueueWrite) → reply to `reply_to`; `Response(_)` → a
    **stale** Ack arriving outside an active transmit (its batch already completed) → **drop**.
  - epoch tick (`tokio::time::interval`): `block_in_place(|| { s1.batch_init()?; s1.batch_write() })`,
    where S1's `Server2WriteAccess` is a `CarrierS1ToS2` that `split_batch`es and `block_on`s each
    `TransmitBatchChunk` send to S2, awaiting that chunk's `Response` Ack (retrying per §7.5).
  - **Epoch transmit is an exclusive phase (DESIGN-review P2).** `batch_write` runs under
    `block_in_place`, so the `select!` loop is paused — *nothing* else polls `s1`'s stream during the
    transmit. The Ack-wait inside `CarrierS1ToS2` is the *only* poller then; it matches `Response`
    Acks by correlation id, drops stale `Response`s, and **rejects** any `Request(QueueWrite)` it
    observes with a transient *busy* `Response` (S1 is mid-eviction) — it does **not** queue or buffer
    it (DESIGN-review P1: buffering a write past the client's deadline would let it land *and* be
    re-deposited, duplicating the cell). A rejected write fails fast at the client per the best-effort
    model (§7.5); the next epoch's writes are accepted once `batch_write` returns. This matches Myco's
    own model: an epoch boundary is a write-quiescent eviction phase.

### §7.5 Failure semantics

- **S1→S2 transmission is at-least-once → exactly-once effect.** The `CarrierS1ToS2` retries a
  timed-out/`Error` chunk with backoff; on a mid-batch link drop it retransmits the **whole batch**
  next attempt. Re-delivered chunks are absorbed by the already-built reassembler idempotency
  (same-payload in-flight dup → `Incomplete`; replayed applied `batch_id` → `AlreadyApplied`), so a
  retried/whole-batch-replayed transmission never double-advances S2. This is *why* the dispatch core
  was hardened to exactly-once **first** — the unreliable-link recovery path depends on it.
- **Client reads are idempotent** (`get_prf_keys`/`read_notifs`/`read` are pure S2 reads) → retry-safe
  on timeout.
- **Client writes are best-effort, NOT auto-retried (DESIGN-review P1).** `queue_write` is *not*
  idempotent at S1 — a re-deposit would double-queue the message into the epoch. So Phase-1 must **not**
  blindly re-deposit: a `queue_write` that times out or is rejected *busy* (mid-transmit, §7.4) has an
  **unknown/failed** outcome surfaced to the caller, which does **not** auto-retry. Occasional unsent
  writes are masked by constant-rate cover (COVER_TRAFFIC §2) and recovered, if at all, by an explicit
  higher-layer resend — *not* by the transport. This is internally consistent: nothing both queues a
  late write *and* re-deposits it. **The prerequisite for any retry/re-deposit (and thus for
  reliable, exactly-once writes) is the write-nonce hardening:** a client-supplied per-write nonce +
  per-epoch S1 dedup set makes `queue_write` idempotent, after which a re-deposit is safe (at-least-once
  + dedup = effectively-once) and §7.4 could buffer instead of reject. Deferred from chunk 4 (it adds
  per-epoch nonce state at S1); tracked as the writes-reliability hardening. The gate should confirm
  this trade rather than assume retry-safety.

### §7.6 Test plan (rule #27)

- **Smoke:** instantiate the S2 role on a shared-bus in-memory carrier; one `get_prf_keys` RPC from a
  client bridge returns the key window (proves the poll→dispatch→reply→correlate path end-to-end).
- **Integration (the §8.5 acceptance shape, in-memory carrier):** spawn S1 + S2 roles on a shared-bus
  carrier; a client `deposit`s a message (→S1) , the S1 epoch tick fires (→ chunked transmit → S2),
  the client `retrieve`s (→S2) and recovers the plaintext — the full client↔S1↔S2 round-trip over the
  real async `Carrier` interface, not the in-process `local` bridge.
- **Timeout:** a client read against a silent (never-spawned) S2 returns `Timeout` within the deadline,
  not a hang (mirrors the `feedback_mock_transports` lesson — bound every reply wait).

Chunk 5 (328e) then drives the S1 epoch tick from the real cover/epoch clock (COVER_TRAFFIC §2) — over
the **queued point-to-point carrier** that carries Myco RPC (§7.1), *not* `DhtMailboxCarrier`, which is
the single-server `PirMailbox` substrate — and adds the operator-transcript-independent-of-`i`-and-
timing assertion (§4).
