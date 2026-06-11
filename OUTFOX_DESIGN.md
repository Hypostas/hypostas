# OUTFOX_DESIGN.md — Fixed-Size Constant-Length-Route Onion (HYP-318)

**Status:** DESIGN (v0.1, 2026-06-11). Implementation-detail design for the Outfox absorption that
`CIRCUIT_LIFECYCLE.md §21` and `SEALED_ENVELOPE.md §16.4` spec only at the design-level principle. This is the
contract-before-code artifact (rule #9) for HYP-318. Authored after the bidirectional multi-hop DATA plane
(HYP-315 forward + reverse, chunks 1/2/3a) landed and concretely exposed the two limits Outfox removes.

**Crypto sign-off authority:** Fable 5 + Codex gpt-5.5/high are the gate (no human cryptographer; external
audit reserved for HYP-330). Every implementation chunk is Codex-gated. This design doc is itself a
gate-able artifact — review it against the Outfox paper + the threat model before the first code chunk.

---

## §1 Why — the two limits Outfox removes

The current cell format (`SEALED_ENVELOPE §7`) has **four quantized size classes** (S=512 / M=4096 / L=16384 /
XL=65536 B) and an onion where **each layer is `smallest_fitting(header + inner)`** — so an onion GROWS one
size class per layer (`seal_onion`), and a reverse reply GROWS one class per relay wrap. Two consequences,
both measured during HYP-315:

1. **Forward depth ceiling ~4 hops.** A DATA payload sealed at S becomes M→L→XL across 3 relay layers; a 4th
   layer would exceed XL → `PayloadTooLarge`. So circuits deeper than ~4 hops can't carry a non-trivial
   payload, and the spec's `MAX_HOPS_PER_CIRCUIT = 5` (CIRCUIT_LIFECYCLE §13) is unreachable.
2. **Reverse-reply size cap (S, ~478 B).** Each relay reverse-wrap bumps a size class, so the terminal must
   seal a reply at S to survive ≤3 wraps — capping replies at 478 B regardless of circuit depth (HYP-315
   chunk 3a P1). Larger replies / 5-hop reverse are impossible.

Both are the SAME root cause: **per-layer size growth from quantization.** Outfox's fixed-size
constant-length design removes it at the root — every cell is ONE fixed size end-to-end, peeled-and-padded
Sphinx-style, with the hop count padded to a constant 5 by decoy layers.

Also fixed: **hop-count leakage.** Today a relay (and a passive observer correlating cell sizes) can infer a
cell's depth from how the size class shrinks along the path. A fixed-size 5-layer cell makes 1-hop and 5-hop
DATA indistinguishable — including to a compromised relay (THREAT_MODEL §4 hop-count privacy).

---

## §2 Core design — fixed-size, always-5-layer, peel-and-pad

**Invariant: a DATA cell is a single fixed wire size for the whole journey.** No `smallest_fitting`, no
per-layer growth, no per-hop class. A cell = a fixed **header region** (constant-length route info, always
`MAX_HOPS = 5` hops) + a fixed **payload region** (the body, one size for the channel — see §6 on whether we
keep S/M/L/XL for the *body* while the *route* is constant).

**Always 5 onion layers.** The initiator builds exactly `MAX_HOPS` layers regardless of the real hop count:
`real_hops` real layers (one per relay + terminal) followed by `MAX_HOPS - real_hops` **decoy layers**. An
observer or any single relay sees a 5-layer cell and cannot tell the real depth.

**Peel-and-pad (Sphinx).** Each relay PEELS its one layer (decrypt with its circuit key) and **appends fresh
pseudorandom padding** so the cell stays exactly the fixed size. The bytes a relay reveals by peeling are
replaced by indistinguishable padding it cannot have predicted — so the cell's size and high-entropy
appearance are constant at every hop. This is the crux that the current `peel_relay_layer` (which SHRINKS
`forward_inner`) must be replaced by.

**Terminal discards decoys.** The terminal peels its real layer to the payload; the trailing decoy layers are
structurally present but carry no deliverable content (they decrypt to padding the terminal drops). The
terminal knows it is terminal from the circuit table (`SEALED_ENVELOPE §8.1`), not from the layer count.

**Reverse is symmetric.** The reverse onion is ALSO fixed-size + always-5-layer: the terminal seals a reply
into a fixed-size cell with `MAX_HOPS` reverse layers (real reverse hops + decoys); each relay re-encrypts
ONE reverse layer in place WITHOUT growing the cell (the inverse of forward peel-and-pad); the initiator
decrypts all `MAX_HOPS` reverse layers. This removes the reverse-reply size cap (the reply can fill the fixed
payload region, independent of depth).

---

## §3 What this replaces (the concrete deltas vs the merged code)

| Component (today) | Outfox change |
|---|---|
| `SizeClass` (S/M/L/XL) chosen per layer via `smallest_fitting` | ONE fixed route size; body size decided once at seal, never per-layer |
| `seal_onion` — nests N layers, each `smallest_fitting(header+inner)`, grows outward | `seal_onion_fixed` — builds exactly `MAX_HOPS` layers (real + decoy) into a fixed-size cell |
| `peel_relay_layer` — returns `forward_inner` SHORTER than input | `peel_and_pad` — returns the SAME-size cell (one layer removed, padding appended) |
| `open_data_multihop` — peels `hops.len()` reverse layers, variable size | peels exactly `MAX_HOPS` layers, discards decoy tail |
| reverse wrap (`try_reverse_forward`) — `smallest_fitting(wire.len())`, grows | in-place fixed-size reverse re-encryption |
| `seal_reply` — caps at S to survive wraps | fills the fixed payload region; no cap |
| EXTEND/EXTENDED per-hop header (~250 B/layer) | compact per-hop header (~80 B/layer) — §21.1.1 |

The forward + reverse DATA-plane *transport wiring* (HYP-315 dispatch, the learn-on-forward reverse demux,
the relay tables, the replay bloom) stays — it routes by `circuit_id` + circuit-table role, which is
format-agnostic. Outfox is a **cell-format / onion-construction** redesign, not a routing redesign. That is
what makes it tractable to land under the existing transport.

---

## §4 The decoy-hop construction (the subtle part)

Decoy layers must be **indistinguishable from real layers** to every relay AND undetectable as "the route
ended here." Open design decisions (resolve before the seal/peel chunk, with Codex review):

1. **Decoy key derivation.** A real layer's key comes from the circuit's per-hop `layer_key_send`. A decoy
   layer has no relay, so its "key" must be derived by the INITIATOR from a circuit secret (so the initiator
   can build the decoy AND the terminal/initiator can recognize+discard it) WITHOUT any relay being able to
   distinguish decoy from real. Candidate: `HKDF(circuit_secret, "outfox-decoy" ‖ layer_index)`.
2. **Where decoys sit.** Sphinx places decoys AFTER the terminal (trailing). For us: layers
   `[R1 … R_{k-1}, terminal, decoy_{k+1} … decoy_5]`. The terminal peels its layer, then must NOT forward
   (circuit table says terminal) — the decoy tail is never processed by a relay, only padded-over by the
   peel chain up to the terminal. **Verify:** does any relay before the terminal ever "see" a decoy layer?
   (It should not — each relay peels exactly one real layer; decoys are inside the still-encrypted core that
   only the terminal would reach, and the terminal stops.) This is the property to prove in the design review.
3. **Per-layer MAC / integrity.** Sphinx chains a per-hop MAC so a relay rejects a tampered header. Define
   the MAC chain over the fixed header region; a decoy layer's MAC is initiator-derived. Must not let a relay
   distinguish "MAC verifies as a real next-hop" from "MAC is a decoy terminator."

### §4.4 Construction finding (2026-06-11 — why this is the full Sphinx mix-header, not a shortcut)

Working the seal/peel concretely surfaced that the two "obvious" length strategies BOTH fail, which is what
forces the real Sphinx construction:

- **Naive AEAD layering grows.** `AEAD(K_i, inner)` appends a 16-byte tag per layer, so an N-layer onion is
  `body + N·16` and each peel SHRINKS by 16 — the current `seal_onion`. Padding the shrink back leaks depth
  (the pad accumulates per hop, and a relay that knows the real-vs-pad boundary knows its depth).
- **Naive XOR-onion is length-preserving but can't carry decoys.** `payload ⊕= KS(K_i)` per layer keeps the
  size constant (good), but a **decoy** layer's keystream is held by NO hop — nobody unwraps it, so it never
  cancels and corrupts the terminal's plaintext. Decoys only work if the path's own processing
  *deterministically regenerates* the padding that fills the vacated tail.

That regeneration IS the Sphinx **filler**: the initiator pre-computes, from the real hops' keystreams, the
exact bytes each relay's transform will deposit in the tail as it shifts the header forward, so after `k` real
hops the layout is byte-identical to a fresh `MAX_HOPS`-hop packet. Concretely the cell is:

```
[ clear: version(1) ‖ circuit_id(4) ‖ command(1) ]
[ header: MAX_HOPS fixed slots — each {per-hop MAC(16) ‖ blinded routing/control} ]   ← shifted + filler-padded per hop
[ payload: fixed-length block, one length-preserving transform per hop ]              ← end-to-end integrity at the terminal
```

Each relay: (1) recompute its hop key from the circuit table, (2) verify its header MAC over (header‖payload)
— tamper-reject, (3) length-preservingly transform the payload, (4) shift the header up one slot and append
the deterministic filler. A decoy slot is initiator-MAC'd with a key derived per §4.1 so it verifies exactly
like a real slot but routes nowhere; the terminal stops by circuit-table role (§2), never reaching the decoy
tail. **Decision:** specify the filler + the per-hop transform precisely (candidate transform: a wide-block
PRP, or ChaCha20 keystream with the per-hop MAC supplying the integrity Sphinx needs) and pin it with a
KAT-backed test vector BEFORE the seal chunk — this is the part to get a Codex design-review pass on, and the
part most worth an eventual external-audit reference (HYP-330).

**Threat to defeat:** a compromised relay must not learn (a) its position/depth, (b) the total hop count,
(c) whether the next layer is real or decoy. The fixed size + uniform transform + filler-regenerated padding +
indistinguishable decoy MAC slots are what deliver (a)-(c) — and the filler is the load-bearing piece, so it
is where the indistinguishability proof lives.

---

## §5 PQ-hybrid integration

Outfox's paper uses pure ML-KEM; we REJECT that (CIRCUIT_LIFECYCLE §21.2) and keep hybrid X25519+ML-KEM at
construction (POST_QUANTUM.md). So Outfox here is **the packet/onion FORMAT, not the kex.** The per-hop
layer keys still come from the existing hybrid circuit handshake (`circuit_kex`); Outfox only changes how the
DATA/reverse cell is structured + padded around those keys. No change to `begin_extend`/`finalize_extend`
key derivation — only the EXTEND/EXTENDED *wire header* gets the compact form (§3 last row), and DATA cells
get the fixed-size onion. This keeps the crypto-review surface bounded: the kex is unchanged + already gated.

---

## §6 Open decision — body size classes vs one universal size

Two sub-options for the PAYLOAD region (the route/header region is unconditionally fixed at 5 hops):

- **(A) One universal body size.** Every DATA cell is the same total (e.g. a single fixed size ≈ current L
  or XL). Maximum uniformity (even body size is invisible); maximum overhead for small messages (a heartbeat
  pays full size). Pairs naturally with constant-rate cover (cover already pays a fixed slot).
- **(B) Keep S/M/L/XL for the BODY, fix only the ROUTE.** A cell's hop count is invisible (fixed 5-layer
  header region) but its body class (S/M/L/XL) is visible — as today, used by the cover scheduler's
  size-tiered slots. Less uniform (body size leaks message-size class) but far less overhead + reuses the
  cover size tiers.

**Recommendation: (B)** — fix the ROUTE (the Outfox goal: hop-count invisibility) while keeping body size
classes, because (i) the cover-traffic scheduler is already built around size-tiered slots (COVER_TRAFFIC),
(ii) (A)'s overhead (every heartbeat at L/XL) fights the constant-rate budget, (iii) the threat Outfox
targets is hop-count / route-length leakage, not message-size class (which size-tiered cover already shapes).
Decision to confirm with Josh + Codex before the format chunk. If (B): the reverse-reply cap is removed for
each body class independently (a reply fills its class's body region across all 5 fixed layers).

---

## §7 Migration + versioning

This is a **wire-breaking** change to the DATA/reverse cell + EXTEND/EXTENDED header. Per CLAUDE.md
"version everything that crosses a boundary":

- Bump `CELL_VERSION` (or add an Outfox cell variant) so a pre-Outfox peer rejects cleanly rather than
  misparsing. The `PrivacyClass` / wire-version machinery (HYP-164, merged) is the precedent.
- Phase 1 has NO deployed dyads yet (the network is pre-launch), so there is no backward-compat burden —
  Outfox can be a clean cutover, not a dual-stack. Confirm before building (if any devnet peers exist they
  re-handshake).
- The circuit *handshake* (hybrid kex) is unchanged, so existing circuit-construction tests + the merged
  EXTEND handler stay valid; only the DATA/reverse onion + the EXTEND/EXTENDED header bytes change.

---

## §8 Proposed chunk decomposition (each Codex-gated, rule #27)

1. **Constants + fixed-size cell primitive.** `MAX_HOPS` everywhere; the fixed cell layout (header region +
   body region); `seal_cell_fixed` / `open_cell_fixed` round-trip at one fixed size. Unit + adversarial
   (wrong-size rejection, non-zero-padding rejection). No onion yet.
2. **Forward fixed-size onion — seal.** `seal_onion_fixed`: build exactly `MAX_HOPS` layers (real + decoy)
   into a fixed-size cell; the decoy construction (§4) + the initiator-derived decoy keys. Test: a k<5 route
   produces a 5-layer fixed-size cell; the layer bytes are uniform.
3. **Forward fixed-size onion — peel-and-pad.** Replace the relay peel with `peel_and_pad` (same-size out,
   fresh padding). Test: cell size constant across all 5 peels; a relay can't tell its depth (peel output is
   byte-uniform regardless of position); terminal recovers the payload + discards decoys.
4. **Wire DATA path onto the fixed onion.** Swap `seal_data_multihop` / `process_relay_cell` / `open_data_*`
   to the fixed onion; lift the variable-size assumptions. Integration: forward DATA across a 5-hop circuit
   (rule #27). Remove the old `seal_onion` once nothing reads it.
5. **Reverse fixed-size onion.** Symmetric reverse (terminal seal_reply → fixed-size reverse layers → relay
   in-place re-encrypt → initiator peel 5). Removes the S-cap. Integration: a full-size reply round-trips a
   5-hop circuit.
6. **Compact per-hop EXTEND/EXTENDED header** (§21.1.1, ~80 B/layer). Independent of the DATA onion; can land
   in parallel. Saves ~500 B per multi-hop EXTEND.
7. **Lift `MAX_HOPS_PER_CIRCUIT` to 5 + remove `MultiHopExtendUnsupported`.** Now that the onion is
   fixed-size 5-layer and EXTENDED reverse-forwards (the HYP-315 deep-EXTENDED follow-on), deep construction
   lands. Integration: build + use a 5-hop circuit bidirectionally end-to-end — the capstone.
8. **UC-framing doc pass** (§21.1.2) — state the UC properties the format claims, for the eventual external
   audit (HYP-330). Doc-only.

Chunks 1-5 are the core (the fixed-size onion). 6 is parallelizable. 7 is the payoff (full 5-hop circuits).
8 is documentation for audit.

---

## §9 Risks / things to get right (for the design review before chunk 1)

- **Decoy indistinguishability (§4).** The single most important property. If a relay can tell a decoy layer
  from a real one, the constant-length-route guarantee collapses. Prove it in the design review; test it
  adversarially (a relay's peel output must be byte-uniform whether the next layer is real or decoy).
- **Peel-and-pad entropy.** The appended padding MUST be indistinguishable from ciphertext (PRF/keystream,
  not zeros — zeros would mark the peeled region). This differs from the current zero-padding (`§7`, which is
  for the BODY tail at the terminal, not for per-hop peel).
- **Replay tag under fixed size.** The replay tag (`derive_replay_tag` over circuit_id+nonce+hop_position)
  must still bind per hop; confirm the fixed-size header still carries a per-hop nonce.
- **Cover compatibility.** A fixed-size DATA cell must still be byte-indistinguishable from a cover cell
  (`cover_cell`) of the same size (COVER_TRAFFIC §4.2). Option (B) keeps the body classes that cover uses.
- **Don't re-derive the kex.** Outfox is format-only; the hybrid handshake is untouched (§5). Resist the
  paper's ML-KEM-only pull.

---

## §10 Cross-references

- `CIRCUIT_LIFECYCLE.md §21` (design-level Outfox absorption), §13 (`MAX_HOPS_PER_CIRCUIT = 5`)
- `SEALED_ENVELOPE.md §16.4` (wire-layer Outfox absorption), §7 (current size classes — replaced here)
- `THREAT_MODEL.md` §4 (hop-count privacy the constant-length route delivers)
- `POST_QUANTUM.md` (the hybrid kex Outfox does NOT change)
- Outfox paper: https://arxiv.org/html/2412.19937 (Nym, WPES '25)
- HYP-315 (the bidirectional DATA plane Outfox re-formats; its transport wiring is reused)

---

*v0.1 — 2026-06-11 — Iris. Design foundation for HYP-318. The implementation (chunks §8) is a fresh
spec-complete build best done with focused context; this doc is its contract. Body-size decision (§6) +
decoy-construction proof (§4) are the two things to settle with Josh + a Codex design-review pass before
chunk 1.*
