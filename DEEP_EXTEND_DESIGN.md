# DEEP_EXTEND_DESIGN.md — live ≥3-hop circuit construction (HYP-209)

**Status:** DESIGN (rule #9 contract — write before code). Pending a Codex DESIGN-review before chunk 1.
**Scope:** lift `MultiHopExtendUnsupported` (vita-carriers `circuit_transport.rs`) so a node builds ≥3-hop
circuits live, by routing the deep `CMD_EXTENDED` reply back to the initiator over the **Outfox
length-preserving reverse path**. Spec: CIRCUIT_LIFECYCLE §4 (telescoping) + OUTFOX_DESIGN §reverse.
**Companion:** OUTFOX_DESIGN.md (the data plane this reuses), CIRCUIT_LIFECYCLE §4.2 (the construction steps).

---

## 1. The problem

Telescoping construction (HYP-315) works to **2 hops**. `initiate_extend` onion-seals a `CMD_EXTEND` to the
current terminal; the terminal (`process_extend`) brokers a handshake to the next relay on the initiator's
behalf; the relay wraps the next relay's `HandshakeResponse` as an `ExtendedResponse` (`try_forwarded_extend`)
sealed with its leg's reverse key, and routes it to its predecessor. For a **1-hop** circuit the predecessor
IS the initiator, who opens it single-layer (`open_extended` at the terminal hop's `layer_key_recv`) and
`finalize_extend`s the new hop.

For a **≥2-hop** circuit the predecessor is an INTERMEDIATE relay, which must **reverse-forward** the
`CMD_EXTENDED` back toward the initiator — each intermediate adding its own reverse layer — and the initiator
must **peel the reverse onion** before `finalize_extend`. That reverse-forward + multi-layer peel does not
exist for `CMD_EXTENDED` today, so the 1-hop-only guard (`MultiHopExtendUnsupported`,
`circuit_transport.rs`) refuses any extend of a circuit already ≥2 hops.

### 1.1 Why not the existing (old-onion) reverse path

The HYP-315 old-onion reverse path (`seal_reply` / `try_reverse_forward` / `open_data_multihop`) is
**length-GROWING** (each reverse wrap adds an AEAD tag → bumps a size class) and therefore caps a reply at the
**S** class so it survives ≤4 wraps (`seal_reply` rejects `inner > S.max_inner_len()`). An `ExtendedResponse`
carries a full PQ `HandshakeResponse`:

| field | bytes (approx) |
|---|---|
| x25519 pk | 32 |
| ML-KEM-768 ciphertext | 1088 |
| hybrid signature (Ed25519 64 + ML-DSA-65 3309) | 3373 |
| circuit_id + timestamps + framing | ~32 |
| **total ExtendedResponse** | **~4.5 KB** |

~4.5 KB ≫ S. The old-onion reverse path **cannot carry an EXTENDED reply**. This is the exact limitation
OUTFOX_DESIGN solved for DATA.

### 1.2 Why the Outfox reverse path fits

The Outfox reverse path (`seal_reply_outfox` / `try_reverse_forward_outfox` / `open_reply_outfox`,
HYP-318 chunk 2c-2d) is **length-PRESERVING** (LIONESS wide-block PRP): a reverse cell is byte-constant across
every wrap, at a fixed size class chosen ONCE at the source. A `~4.5 KB` ExtendedResponse rides an **L or XL**
Outfox reverse cell with no per-hop growth and no depth cap (to MAX_HOPS=5). It is already live + Codex-clean.

---

## 2. Decision

**Route the deep `CMD_EXTENDED` reply over the Outfox length-preserving reverse path, kind-tagged so it shares
the merged reverse-DATA machinery, demuxed at the initiator.** Three sub-decisions:

### D1 — Forward EXTEND stays old-onion; only the REVERSE EXTENDED moves to Outfox (asymmetric, justified)

Forward and reverse are independent directions. The forward `CMD_EXTEND` is small (an `ExtendRequest` = one
ephemeral kex + the next relay's key hashes, ~200 B) and the existing `seal_extend`
(`seal_onion_with_command`) already routes it correctly to the terminal broker. There is no size pressure on
the forward leg, so it stays old-onion — **no change to `initiate_extend` / `seal_extend` / `process_extend`
/ the relay EXTEND broker on the forward side.** Only the reverse reply (the large one) moves to Outfox. This
minimizes the blast radius: the heavily-gated forward telescoping construction (HYP-315, 14 Codex rounds) is
untouched.

### D2 — A KIND discriminator distinguishes a reverse EXTENDED from a reverse DATA reply

Both ride `CMD_DATA` Outfox reverse cells (so intermediate relays reverse-wrap them identically + blindly —
`try_reverse_forward_outfox` is unchanged). The initiator demuxes by a **1-byte KIND prefix on the inner
reverse payload** (NOT a new command, NOT an Outfox-primitive change — the byte lives in the circuit_manager's
inner payload, opaque to the Outfox layer and to every relay):

```
reverse inner payload = [ KIND(1) ‖ body ]
  KIND_DATA     = 0x00 → body is the DyadPacket reply (today's behavior)
  KIND_EXTENDED = 0x01 → body is the ExtendedResponse wire
```

The initiator's reverse-Outfox receive peels the onion (`open_reply_outfox`), reads KIND, and routes:
`KIND_DATA` → deliver as today; `KIND_EXTENDED` → `finalize_extend`. A relay never sees KIND (it's inside the
innermost layer, sealed by the terminal broker under the terminal leg's reverse key). **This is the only new
wire element.** Versioned: the reverse-Outfox cell already carries `OUTFOX_CELL_VERSION` 0x03; KIND is a new
inner field, so old/new are distinguished by the existing version gate + the kind byte.

### D3 — The 1-hop extend ALSO moves to the Outfox reverse path (uniformity, with a migration guard)

Today a 1-hop extend's EXTENDED replies via the OLD path (`try_forwarded_extend` → `seal_cell(CMD_EXTENDED)` →
`open_extended`). To avoid TWO reverse-EXTENDED paths (old for 1-hop, Outfox for deep), the 1-hop case ALSO
moves to Outfox reverse. This is a migration of a WORKING path → it must be cut over carefully (see §5
chunk 3) with the existing `alice_telescopes_1hop_to_2hop` test as the regression guard, and the old
`open_extended` / the `CMD_EXTENDED` arm of `on_extended` retired only once the Outfox path passes that test.

---

## 3. The mechanism, end to end (2→3 example: init → R1 → R2, extend R2→R3)

1. **Initiator** `initiate_extend(from_terminal=R2, next_relay=R3)`: onion-seal `CMD_EXTEND(ExtendRequest)` to
   R2 (old onion, **unchanged**), route to the entry hop R1.
2. **R1** forwards the cell to R2 (forward onion peel, **unchanged**).
3. **R2** (broker) `process_extend` → handshake to R3 → R3 returns its `HandshakeResponse` (carrying R3's
   signed `circuit_id`, HYP-318 provisioning). **NEW:** instead of `seal_cell(CMD_EXTENDED)`, R2 seals the
   `ExtendedResponse` as the **innermost Outfox reverse layer**: `inner = [KIND_EXTENDED ‖ extended_wire]`,
   `seal_reply_outfox(R2's terminal leg, inner)` → an Outfox reverse cell at the smallest class that fits
   ~4.5 KB (L/XL), routed to R2's predecessor (`initiator_dyad_id` of R2's leg = R1).
   - R2 still provisions `learn_next_hop_circuit_id` for R3 on the FORWARD path exactly as today (DATA to R3
     will need it). The reverse EXTENDED routing is independent.
4. **R1** receives an Outfox `CMD_DATA` reverse cell. `try_reverse_forward_outfox` (UNCHANGED) demuxes it to
   R1's forwarding leg by `next_hop_circuit_id`, adds R1's reverse layer (`add_payload_layer` under R1's
   `session_key_out`), re-frames under `circuit_id_in`, routes to R1's predecessor = the initiator.
5. **Initiator** receives the Outfox reverse cell on its sender circuit. `open_reply_outfox` peels every hop's
   reverse layer (R1 then R2 via each hop's `layer_key_recv`-derived Outfox key) → recovers
   `[KIND_EXTENDED ‖ extended_wire]`. **NEW:** read KIND → `KIND_EXTENDED` → parse `ExtendedResponse` →
   `finalize_extend(pending, extended, R3_pubkey, now)` → the hop appends, the circuit is now init→R1→R2→R3.
6. **Guard lift:** `initiate_extend` no longer refuses a ≥2-hop circuit; it allows up to `MAX_HOPS_PER_CIRCUIT`
   (5). The pending-extend lifecycle (reserve/finalize/restore under the manager lock, TTL sweep) is
   UNCHANGED — only the reply's transport changes.

The 1-hop case (§D3) is step 3→5 with R2=the directly-reachable terminal and no intermediate (R1 absent):
the initiator's `open_reply_outfox` peels ONE reverse layer and finalizes. Same code path, depth-agnostic.

---

## 4. Invariants preserved (must hold; Codex-verify each)

- **Position-obliviousness:** every reverse wrap is uniform (HOP_TERMINAL, `CMD_DATA`, Outfox length-preserving)
  — a relay reverse-forwarding an EXTENDED is byte-indistinguishable from one reverse-forwarding a DATA reply.
  KIND is inside the terminal-sealed innermost layer; no relay sees it.
- **No new leak:** the EXTENDED already traversed these hops as an old-onion reply for the 1-hop case; moving
  to Outfox changes only size-class behavior (length-preserving), not who-learns-what.
- **finalize_extend unchanged:** the signature/fingerprint/circuit_id-provisioning checks (HYP-318) all run
  on the recovered `ExtendedResponse` exactly as today. A lying responder still fails `CircuitIdMismatch` /
  `HandshakeBadSignature` before the hop installs.
- **Replay/freshness:** the reverse-Outfox cell carries the terminal-nonce replay tag
  (`open_reply_outfox`'s `outfox_nonce_replay_tag`) — the initiator replay-checks the EXTENDED reply like any
  reverse cell. A replayed EXTENDED is dropped before `finalize_extend`.
- **MAX_HOPS:** `initiate_extend` enforces `hops.len() < MAX_HOPS_PER_CIRCUIT` (5) before sealing — an
  over-deep extend is refused at the source (mirrors the forward `seal_onion_with_command` TooManyHops guard).
- **Extend-in-flight:** at most one pending extend per circuit, reserved under the manager lock (UNCHANGED).
- **No reply/extend serialization:** per the HYP-315 chunk-3a hard lesson — extends are NEVER blocked; a DATA
  reply invalidated by a concurrent deepening extend is an accepted best-effort loss (the app resends). A
  reverse EXTENDED invalidated similarly is the same accepted loss; the pending TTL sweep bounds it.

## 5. Chunk decomposition (each its own PR + Codex gate; rule #27 integration test each)

- **Chunk 1 — KIND-framed reverse payload (circuit_manager).** Add `KIND_DATA`/`KIND_EXTENDED` to the inner
  reverse payload. `seal_reply_outfox` gains a kind arg (or a sibling `seal_reply_extended_outfox`);
  `open_reply_outfox` returns `(kind, body, peer, replay_tag)`. The existing reverse-DATA path passes
  `KIND_DATA` (regression: the live reverse-DATA tests stay green). Unit + the existing reverse round-trip
  tests, plus a new `reverse_outfox_carries_an_extended_kind` round-trip. **No transport change yet.**
- **Chunk 2 — broker seals EXTENDED over Outfox reverse (circuit_transport `try_forwarded_extend`).** Replace
  the `seal_cell(CMD_EXTENDED)` with `seal_reply_outfox(KIND_EXTENDED ‖ extended_wire)` routed to the
  predecessor. Integration: a relay brokering an extend emits an Outfox reverse cell to its predecessor (assert
  on the sink wire). The forward EXTEND broker + provisioning stay unchanged.
- **Chunk 3 — initiator demux + finalize (circuit_transport reverse-Outfox receive).** `on_data_outfox`'s
  initiator-deliver branch reads KIND: `KIND_EXTENDED` → match the pending initiator-extend by the sender
  circuit + `finalize_extend`; `KIND_DATA` → deliver as today. Cut the 1-hop path over (§D3) and retire
  `open_extended` / the `CMD_EXTENDED` `on_extended` arm once `alice_telescopes_1hop_to_2hop` passes via
  Outfox. Integration: the existing 1→2 test, re-pathed.
- **Chunk 4 — lift the guard + deep e2e (rule #27 capstone).** Remove `MultiHopExtendUnsupported`; allow extend
  to `MAX_HOPS`. Integration: `telescope_to_5_hops_then_bidirectional_data` — Alice builds init→R1→R2→R3→R4
  via 3 sequential deep extends over REAL transports, then sends DATA + gets a reply both ways (reuses the
  Outfox 5-hop DATA proof). This is the headline AC.

## 6. Out of scope (tracked elsewhere)

- **Tor-style guard nodes (§17, GUARD_NODE_POOL_SIZE=3)** → HYP-316.
- **SPRING ring-signature anonymity (§18, K=1000)** → HYP-317.
- **Live two-runtime integration over a real LibP2pCarrier (§12.2)** → env-blocked; the `#[ignore]` stub
  `integration_two_runtime_circuit_over_carrier` is its un-ignore target.

## 7. Open question for the Codex DESIGN-review (before chunk 1)

Is migrating the 1-hop EXTENDED to the Outfox reverse path (§D3) worth retiring `open_extended` + the
`CMD_EXTENDED` `on_extended` arm, vs keeping the old 1-hop path and only adding Outfox for ≥2-hop? Leaning
**migrate** (one reverse-EXTENDED path is simpler + the old path's S-cap is a latent footgun if a 1-hop
response ever grows), but the migration touches a working, heavily-gated path — confirm the cutover guard
(the 1→2 regression test) is sufficient before retiring the old code.
