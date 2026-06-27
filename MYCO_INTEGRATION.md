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
#[async_trait]
pub trait Mailbox {
    /// Sender-side: deposit a sealed cell for `recipient` in the current epoch. Sender anonymity is
    /// already provided by the circuit this runs over; this call only places the cell at its slot.
    async fn deposit(&self, recipient: &DyadId, sealed_cell: &[u8]) -> Result<(), MailboxError>;

    /// Recipient-side: obliviously retrieve this dyad's cells for the last `delta` epochs. The
    /// operator transcript MUST be independent of which slot(s) actually held mail.
    async fn retrieve(&self, delta: usize) -> Result<Vec<Cell>, MailboxError>;

    /// The effective privacy tier this impl provides right now (drives the §4.4 status ladder).
    fn tier(&self) -> MailboxTier; // Full(TwoServer) | Limited(SingleServer)
}
```

- **`MycoMailbox`** implements `Mailbox` over the ported `myco::client::Client` + the server-access
  traits. `deposit` = `Client::write`; `retrieve` = `Client::read` (the epoch/notification machinery
  is internal). The per-dyad key `setup` is established once at channel creation.
- **`PirMailbox`** implements `Mailbox` over `MailboxRetrieval` + `slot::derive_slot`: `deposit` =
  write the cell to `derive_slot(key, epoch)`; `retrieve` = `query/answer/reconstruct` at that slot.

The runtime holds a `Box<dyn Mailbox>` chosen by reachability (two non-colluding mailbox-servers →
`MycoMailbox`; else `PirMailbox`), exactly the §4.4 degradation surface. **This is the trait 328a's
intent points at** — it just lives above `MailboxRetrieval`, not as it.

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
boundary from the cover-traffic/epoch clock on `DhtMailboxCarrier`, and prove it with the **end-to-end
two-party test on a real carrier** (the §8.5 acceptance test): a recipient reads slot *i*; the
operator transcript is independent of *i* AND of write-to-read timing.

## §5 — Build order (each a gated chunk; integration + smoke tests per rule #27)

1. **`Mailbox` trait + `MycoMailbox` over the local bridge.** The seam (§2) + the in-process impl
   reusing `local::LocalServer*Access`. Smoke: `deposit`→`retrieve` round-trips (lift the existing
   `local` e2e behind the new API). *Buildable now — no new infra.*
2. **`PirMailbox` over `xor_pir` + `DhtMailboxCarrier`.** The single-server tier on the real DHT
   store. Smoke: malicious-single-server transcript independent of *i*. *Buildable now.*
3. **`MycoRpc` framing + `RpcServer{1,2}Access`.** The request/response layer over `Carrier` (§3).
   Integration: a `MycoMailbox` whose server access is RPC-over an in-memory `Carrier` pair.
4. **Mailbox-server role (HYP-328d).** Host `Server1`/`Server2` as services with an epoch timer;
   tier-selection driver wired to the §4.4 privacy-status ladder.
5. **328e — epoch-batching composition + two-party test on a real carrier.** The timing half (§4).

Chunk 1 is the natural next concrete step and needs nothing new. Chunks 3–5 are the live-network
infrastructure and depend on the mailbox-server role.

## §6 — Open question for Josh

Two viable depths for "wire it up":

- **Library-live (chunks 1–2):** Myco + PIR usable behind one `Mailbox` API in-process, e2e-tested.
  Makes the port a usable component the runtime can call; defers the network role/RPC.
- **Network-live (chunks 1–5):** the full mailbox-server role + RPC-over-carrier + batching. This is
  multi-issue infra (328d + 328e + the RPC binding) — a sprint, not a chunk.

Recommendation: **chunk 1 now** (the `Mailbox` seam + `MycoMailbox`) — it is unambiguously correct,
buildable without new infra, and is the foundation every later chunk plugs into. Decide the network
depth (328d/328e) as its own track once the seam is real.
