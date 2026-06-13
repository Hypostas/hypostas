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
fixed `body_size = size_class.total() − OUTFOX_HEADER_LEN`). A request sealed at a fixed class is
byte-constant across hop count, to `MAX_HOPS = 5`, with no depth cap. The `ExtendRequest` wire is ≈ one
hop's kex material (X25519 pk + ML-KEM ct + the next-hop key hash + signature) — a few KB — which fits
comfortably in `CELL_PAYLOAD_L = 16350` (or `Xl`). The forward Outfox machinery already peels + forwards at
every intermediate relay (`process_relay_cell_outfox` → `OutfoxRelayOutcome::Forward`).

> **⚠️ Codex DESIGN-review correction (2026-06-13).** A first draft proposed distinguishing the EXTEND cell by
> the Outfox cell's **command** field (`seal_outfox_cell(entry_id, command=CMD_EXTEND, …)`). That is WRONG: the
> Outfox cell command is a **clear header byte**, so `CMD_EXTEND` would let every intermediate relay + any
> passive observer distinguish construction cells from data — a §6.x privacy leak, and it violates D4′
> (uniform cell shape). It would also break dispatch (a `CMD_DATA`-only router never reaches `on_data_outfox`
> for the EXTEND cell). **The fix mirrors the reverse path's KIND (DEEP_EXTEND_DESIGN D2) symmetrically:** the
> outer Outfox command STAYS `CMD_DATA`; DATA vs EXTEND is a **1-byte KIND prefix on the innermost (encrypted)
> payload**, opened ONLY at the terminal. Relays + observers see a uniform stream of `CMD_DATA` Outfox cells.

## 2. Decision

**Move the forward EXTEND request onto the Outfox length-preserving forward path, sealed exactly like forward
DATA (outer command `CMD_DATA`) but tagged with a 1-byte ENCRYPTED INNER `FWD_KIND` prefix; the terminal
opens the innermost layer, reads `FWD_KIND`, and brokers an EXTEND via the EXISTING `process_extend`.** The
reverse EXTENDED reply is unchanged (already Outfox, DEEP_EXTEND_DESIGN D2/D3).

This is the *symmetric* counterpart of the reverse-path decision (which used a reverse `KIND` byte on the
inner payload), and it reuses substantially more existing machinery than the reverse build did. Sub-decisions:

### D1′ — Seal the EXTEND request via the forward Outfox onion, `CMD_DATA` + inner `FWD_KIND_EXTEND`, fixed `SizeClass::L`

`initiate_extend` stops calling `seal_extend` (the growing onion). Instead it frames the innermost payload as
`[ FWD_KIND(1) ‖ request.to_wire() ]` and seals it through the existing `seal_data_outfox` construction with
the **normal `CMD_DATA` outer command** at a **fixed `SizeClass::L`** (16350-byte body ≫ the framed request;
constant across hop count → no size leak, no depth overflow). Routed to the ENTRY hop, byte-identical on the
wire to a forward DATA cell. `FWD_KIND` lives INSIDE the innermost payload layer (sealed under the terminal
leg's send key), so no relay or observer sees it.

```
forward inner payload = [ FWD_KIND(1) ‖ body ]
  FWD_KIND_DATA   = 0x00 → body is the application message (today's forward DATA — see D2′ migration)
  FWD_KIND_EXTEND = 0x01 → body is the ExtendRequest wire (the construction cell)
```

A new `CircuitManager::seal_extend_outfox(from_terminal, &request, &nonce) -> (Vec<u8>, DyadId)` mirrors
`seal_data_outfox` but prepends `FWD_KIND_EXTEND` + a fail-closed size check (`1 + ExtendRequest` wire ≤ `L`
body). **`FWD_KIND` is the only new wire element**, and like the reverse `KIND` it is opaque to the Outfox
layer + every relay.

### D2′ — Read the inner `FWD_KIND` at the terminal; the outer command stays `CMD_DATA`

The OUTER Outfox command is `CMD_DATA` for both DATA and EXTEND, so intermediate relays
(`OutfoxRelayOutcome::Forward`) peel + forward IDENTICALLY — no relay-receive behavior changes, and the
construction cell is indistinguishable on the wire (D4′ satisfied **by construction**). At the TERMINAL,
`process_relay_cell_outfox` → `OutfoxRelayOutcome::Delivered` recovers the innermost `message`. The
`Delivered` body's FIRST byte is now `FWD_KIND`; `on_data_outfox`'s `Delivered` branch
(`circuit_transport.rs:1683`) strips + demuxes it:

```
FWD_KIND_DATA   → deliver body[1..] to the app
FWD_KIND_EXTEND → BROKER body[1..] as an ExtendRequest (the new path, D3′)
other           → drop (defensive; an authenticated inner byte with an unexpected kind is impossible)
```

The `FWD_KIND` byte is recovered from the (authenticated) innermost payload — NOT from
`OutfoxRelayOutcome::Delivered.command` (the clear cell command, which stays `CMD_DATA`). So `Delivered` does
NOT need a new `command` field; the kind rides the payload, exactly like the reverse path. **The only change
at the terminal is stripping + demuxing the first inner byte.**

> **Forward DATA migration.** Existing forward DATA has NO inner kind byte today. To add `FWD_KIND` without a
> flag day, the forward DATA send (`send_data` → `seal_data_outfox`) must ALSO prepend `FWD_KIND_DATA`, and
> the terminal strip it — a coordinated change in the SAME chunk as `seal_extend_outfox`, versioned by the
> Outfox cell version already on the wire. (Symmetric to how the reverse path added `REVERSE_KIND_DATA` to
> the existing reply path.)

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

1. **`FWD_KIND` framing on the forward Outfox payload (protocol-core/circuit_manager).** Add the
   `FWD_KIND_DATA`/`FWD_KIND_EXTEND` constants; prepend `FWD_KIND_DATA` to the existing `seal_data_outfox`
   inner payload + strip it at the terminal `Delivered`; add `seal_extend_outfox` (`FWD_KIND_EXTEND` +
   `ExtendRequest` wire, fixed-`L`, outer `CMD_DATA`) with a fail-closed `1 + wire ≤ L` size check. Unit
   tests: a DATA round-trip still delivers `body[1..]`; the EXTEND cell is byte-IDENTICAL to a DATA cell at
   the same class (no wire-distinguishable marker — the D4′ privacy property); the cell is byte-constant
   across a 1/3/5-hop circuit. The terminal demux still treats every `FWD_KIND_EXTEND` as a drop for now
   (no broker yet) — NO live extend behavior change.
2. **Terminal broker on `FWD_KIND_EXTEND` (circuit_transport).** In `on_data_outfox`'s `Delivered` branch,
   on `FWD_KIND_EXTEND` parse `body[1..]` as an `ExtendRequest`, `process_extend`, provision the leg, forward
   the `HandshakeRequest` to the new hop. Unit test (injected circuit): an Outfox `FWD_KIND_EXTEND` at the
   terminal forwards a handshake to the new hop + provisions the leg, in the SAME lock order as the old-onion
   broker (R1).
3. **Rewire `initiate_extend` + retire `seal_extend` (D4′).** `initiate_extend` seals via
   `seal_extend_outfox`; remove the old-onion forward-EXTEND seal + its broker path. Verify the reverse
   EXTENDED reply still finalizes (unchanged path).
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
- **R4 — uniform cell shape (RESOLVED by D1′/D2′ revision).** The Codex DESIGN-review caught that an outer
  `CMD_EXTEND` command would be a clear-header privacy leak. The revised design keeps the outer command
  `CMD_DATA` and carries the kind as an encrypted inner `FWD_KIND` byte, so the EXTEND cell is
  byte-indistinguishable from a DATA cell BY CONSTRUCTION. Chunk 1's unit test asserts this (the two cells
  are byte-identical at the same class). Remaining check: that `seal_data_outfox`'s existing callers all go
  through the new `FWD_KIND_DATA`-prefixing path (no un-migrated DATA send bypasses the prefix → terminal
  strip mismatch).

---

| Date | Author | Change |
|------|--------|--------|
| 2026-06-13 | Iris | DESIGN. Forward EXTEND → Outfox (HYP-334). Records that DEEP_EXTEND_DESIGN D1's "forward stays old-onion" assumption was falsified by the HYP-209 ch4 live harness (65541 > CELL_PAYLOAD_XL at depth 5), and specifies the symmetric forward migration reusing `seal_data_outfox` + `process_extend`. Pending Codex DESIGN-review before chunk 1. |
