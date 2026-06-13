# DEEP_EXTEND_FORWARD_DESIGN.md — forward EXTEND request over Outfox (HYP-334)

**Status:** DESIGN (rule #9 contract — write before code). Pending a Codex DESIGN-review before chunk 1.

The companion to [DEEP_EXTEND_DESIGN.md](DEEP_EXTEND_DESIGN.md) (the *reverse* EXTENDED reply). That work
moved only the reverse reply to the Outfox length-preserving path and **explicitly left the forward
EXTEND request on the old growing onion** (its decision **D1**, "Forward EXTEND stays old-onion … it's
small"). This document records that **D1's assumption was falsified by the HYP-209 chunk-4 live
multi-node harness** and specifies the symmetric forward-direction migration. Spec: CIRCUIT_LIFECYCLE §4
(telescoping) + §13 (`MAX_HOPS_PER_CIRCUIT = 5`) + OUTFOX_DESIGN (length-preserving forward onion).

## 1. The problem

`CircuitManager::seal_extend` seals the forward `CMD_EXTEND` request through every existing hop with the
**growing** onion `seal_onion_with_command` (`vita-carriers/src/circuit_manager/mod.rs:1048`). The reverse
work assumed this was fine because "the `ExtendRequest` is small." It is — but the **onion wrapping grows
with depth**, and the live telescope proved it overflows:

```
telescope init→R1→R2→R3→R4→R5, the 5th extend (R4→R5):
  Circuit(DataCell("payload too large: 65541 inner bytes exceed max cell capacity"))
```

`65541 > CELL_PAYLOAD_XL = 65502` — the forward request exceeds even the **largest** cell class at depth 5.
So telescoping CONSTRUCTION caps at ~4 hops; the spec's `MAX_HOPS_PER_CIRCUIT = 5` is **unreachable by the
builder**. (Forward DATA over a 5-hop circuit is fine — it already rides the length-preserving
`seal_data_outfox`; only the *construction* is broken. The harness test `live_telescope_to_max_hops_five`
is `#[ignore]`d on exactly this.)

### 1.1 Why D1 missed it

The reverse-path work was gated against injected circuits + the live **1→2** telescope
(`initiator_extends_a_circuit_live_end_to_end`). The full **≥5-hop live construction** was the `#[ignore]`
capstone — never exercised until the HYP-209 ch4 harness. D1's "forward is small, leave it" was an
**untested assumption**, not a measured fact. The harness is the first thing that drove a real 5th extend.

### 1.2 Why the Outfox forward path fits

`CircuitManager::seal_data_outfox` (`mod.rs:976`) is **length-PRESERVING** (LIONESS wide-block PRP over a
fixed `body_size = size_class.total() − OUTFOX_HEADER_LEN`) and **already carries a 1-byte command**
(`seal_outfox_cell(entry_id, command, &onion)` — today `CMD_DATA`). A request sealed at a fixed class is
byte-constant across hop count, to `MAX_HOPS = 5`, with no depth cap. The `ExtendRequest` wire is ≈ one
hop's kex material (X25519 pk + ML-KEM ct + the next-hop key hash + signature) — a few KB — which fits
comfortably in `CELL_PAYLOAD_L = 16350` (or `Xl`). The forward Outfox machinery already peels + forwards at
every intermediate relay (`process_relay_cell_outfox` → `OutfoxRelayOutcome::Forward`), command-agnostically.

## 2. Decision

**Move the forward `CMD_EXTEND` request onto the Outfox length-preserving forward path, sealed exactly like
forward DATA but with `command = CMD_EXTEND`; the terminal demuxes the command and brokers via the EXISTING
`process_extend`.** The reverse EXTENDED reply is unchanged (already Outfox, DEEP_EXTEND_DESIGN D2/D3).

This is the *symmetric* counterpart of the reverse-path decision, and it reuses substantially more existing
machinery than the reverse build did (which had to add the whole reverse-reply path). Sub-decisions:

### D1′ — Seal the EXTEND request via the forward Outfox onion, fixed `SizeClass::L`

`initiate_extend` stops calling `seal_extend` (the growing onion) and instead seals
`request.to_wire()` via the `seal_data_outfox` construction with `command = CMD_EXTEND` at a **fixed
`SizeClass::L`** (16350-byte body ≫ the `ExtendRequest`; constant across hop count → no size leak, no depth
overflow). Routed to the ENTRY hop (`circuit.hops.first()`), exactly as forward DATA. A new
`CircuitManager::seal_extend_outfox(from_terminal, &request, &nonce) -> (Vec<u8>, DyadId)` mirrors
`seal_data_outfox` with the EXTEND command + a fail-closed size check (`ExtendRequest` wire ≤ `L` body).

### D2′ — Surface the command in the terminal `Delivered` outcome; demux at the terminal

`OutfoxRelayOutcome::Delivered` (`mod.rs:510`) carries `{ nonce, message, peer, replay_tag }` — **no
command**. Add `command: u8` (the innermost peeled command, already known to the peel). `on_data_outfox`'s
`Delivered` branch (`circuit_transport.rs:1683`) then demuxes:

```
CMD_DATA   → deliver to the app (today's behavior)
CMD_EXTEND → BROKER (the new path, D3′)
other      → drop (defensive; an authenticated cell with an unexpected command is impossible)
```

Intermediate relays are UNCHANGED — `OutfoxRelayOutcome::Forward` peels + forwards command-agnostically, so
the EXTEND cell traverses the circuit identically to a DATA cell (no relay learns it is an EXTEND; the
command lives in the innermost layer, opened only at the terminal). **This is the only behavioral change at
a relay's receive path.**

### D3′ — The terminal broker reuses `process_extend` unchanged

At the terminal, on `CMD_EXTEND`: parse `message` as an `ExtendRequest` (`ExtendRequest::from_wire`), then
call the EXISTING `process_extend(&extend, self_dyad, now, sign)` → `(HandshakeRequest, fingerprint)`. The
broker:
1. **provisions the relay leg** for the new hop (so the EXTENDED reply + subsequent DATA can be forwarded) —
   the same `provisional_relays` / `confirm_prepared` path the old-onion broker uses;
2. **forwards the `HandshakeRequest`** to `extend.next_relay_dyad_id` (a fresh handshake cell, sealed to the
   new hop — NOT onion-wrapped; the terminal↔new-hop link is a direct handshake, as today);
3. records the pending so the new hop's `HandshakeResponse` is recognized + wrapped as a reverse
   `KIND_EXTENDED` reply (the existing reverse-Outfox path, DEEP_EXTEND_DESIGN — UNCHANGED).

`process_extend` already returns exactly `(HandshakeRequest, fingerprint)` and is independent of HOW the
`ExtendRequest` arrived — so the broker logic is **reused verbatim**; only its *trigger* moves from the
old-onion `CMD_EXTEND` inbound to the Outfox `Delivered{CMD_EXTEND}` path.

### D4′ — Retire `seal_extend` (the growing onion) once the Outfox path lands

After D1′–D3′, `seal_extend` / `seal_onion_with_command`'s `CMD_EXTEND` use has no caller. Retire it (or keep
`seal_onion_with_command` only if another command still needs the growing onion — audit at chunk time). The
old-onion forward EXTEND broker (the `handle_inbound` `CMD_EXTEND` seal-cell path, if distinct from the
Outfox path) is removed in the same chunk so there is ONE forward-EXTEND path (no dead second path, rule #6).

## 3. Chunk breakdown

1. **`seal_extend_outfox` + the `Delivered.command` surface (protocol-core/circuit_manager).** Add
   `seal_extend_outfox` (fixed-`L` Outfox seal of the `ExtendRequest` with `CMD_EXTEND`); add `command` to
   `OutfoxRelayOutcome::Delivered` + populate it in `process_relay_cell_outfox`. Unit tests: the cell is
   byte-constant across a 1/3/5-hop circuit; `Delivered.command == CMD_EXTEND`; size fail-closed if a request
   ever exceeds the `L` body. NO behavior change yet (the transport still ignores the new command).
2. **Terminal broker on `Delivered{CMD_EXTEND}` (circuit_transport).** Demux the command in `on_data_outfox`;
   on `CMD_EXTEND` parse the `ExtendRequest`, `process_extend`, provision the leg, forward the
   `HandshakeRequest`. Unit test (injected circuit): an Outfox `CMD_EXTEND` at the terminal forwards a
   handshake to the new hop + provisions the leg.
3. **Rewire `initiate_extend` + retire `seal_extend` (D4′).** `initiate_extend` seals via
   `seal_extend_outfox`; remove the old-onion forward-EXTEND seal + broker. Verify the reverse EXTENDED reply
   still finalizes (unchanged path).
4. **Un-ignore the harness capstone.** `live_telescope_to_max_hops_five` (vita-carriers
   `circuit_transport/tests.rs`) goes live: init→R1→R2→R3→R4→R5 + bidirectional DATA, end to end. This is the
   acceptance test for HYP-334.

Each chunk Codex `gate`d (gpt-5.5/high). Chunk 1 is the design's protocol-core core; chunks 2–3 are the
transport wiring; chunk 4 is the acceptance proof the harness already stages.

## 4. Risks + open questions for the DESIGN-review

- **R1 — `process_extend` provisioning parity.** The old-onion broker provisions the relay leg + records the
  pending in a specific order under the manager lock. The Outfox broker must reproduce that order EXACTLY
  (provision before forward, so a fast EXTENDED reply finds the leg). Resolve by reading the old-onion broker
  (`handle_inbound` `CMD_EXTEND` path) side-by-side at chunk 2.
- **R2 — replay/nonce accounting.** The forward Outfox DATA `Delivered` path replay-checks on
  `(circuit_id, nonce)` and `record_relay_used`. The EXTEND `Delivered` must use the SAME accounting (an
  EXTEND is a forward cell like DATA) — confirm a brokered EXTEND advances the leg's recv accounting once,
  not twice.
- **R3 — size class choice.** `L` (16350) fits today's `ExtendRequest`; confirm the wire size with a
  fail-closed assertion so a future larger kex (e.g. a bigger PQ pubkey) trips a loud error, not a silent
  overflow. `Xl` is the fallback if `ExtendRequest` ever approaches `L`.
- **R4 — uniform cell shape.** A `CMD_EXTEND` Outfox cell must be byte-indistinguishable from a `CMD_DATA`
  cell to every intermediate relay (the command is inside the innermost layer). Confirm `seal_extend_outfox`
  produces a cell of the SAME outer shape as a `CMD_DATA` cell at the same class (no observable EXTEND
  marker on the wire) — this is a privacy property, not just correctness.

---

| Date | Author | Change |
|------|--------|--------|
| 2026-06-13 | Iris | DESIGN. Forward EXTEND → Outfox (HYP-334). Records that DEEP_EXTEND_DESIGN D1's "forward stays old-onion" assumption was falsified by the HYP-209 ch4 live harness (65541 > CELL_PAYLOAD_XL at depth 5), and specifies the symmetric forward migration reusing `seal_data_outfox` + `process_extend`. Pending Codex DESIGN-review before chunk 1. |
