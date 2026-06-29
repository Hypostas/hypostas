# ANCHOR_COMPACTION_DESIGN.md — shrinking the C3 vouch (HYP-343 size investigation)

**Status:** investigation + options (no code). Triggered by the chunk-3 finding that the production C3
vouch is ~tens of MiB, incompatible with the gossip transport. Josh (2026-06-29) asked to investigate a
compact anchor bind before finishing the issuer wiring. Refs: `proof_anchor_bind.rs`, `bind.rs`,
`ANCHOR_BIND_DESIGN.md` (the κ-round construction, 13 design rounds), `LNP22_SHOW_DESIGN.md`.

---

## 1. The measurement (the size is the anchor bind)

Empirically, for the dual-hybrid `PqBlindedVouch` at **κ=8, d=1**: total **4,144,653 B (~4 MiB)**, of which
the **cross-domain anchor bind (`AnchorBindProof.z1`/`z2`) is ~88%** (7,176 proof-ring elements). The driver:

- **Each of the κ rounds opens the FULL `s1`** — `Z1_j = y_j + c_j·s1` with **m1 ≈ 891 ring-elements**
  (`s1` is the whole unified witness: `v1|v2|m|tag|z|slacks|w_bits|…`), plus `Z2_j` (m2=6).
- So the anchor is `κ × (m1+m2) × NHAT×8 B`. At **κ=128** (production) that is **~57 MB** for the anchor
  alone; with d=4 scaling the show, the whole vouch is **~60 MB**. The show/BBS/commitment are ~12% (~460 KB
  at d=1; a few MB at d=4) — NOT the driver. **The anchor's `κ × full-opening` is the whole problem.**

## 2. Why κ full openings — the soundness constraint (not incidental)

`ANCHOR_BIND_DESIGN §2–§3.1`: the bind is **cross-domain** (lattice `w_bits` in `t_A` ↔ EC `w` in
`C_r = w·g + r·h`), and the two challenge spaces are mismatched:

- The **EC side** needs a full-`Fr` (~256-bit) challenge to bind soundly.
- The **lattice side** challenge is `ρ`-bounded; worse, the EC binding can only read the challenge through
  `τ0(·)` (the **constant coefficient** of the proof-ring responses), which lies in `[−8, 8]`. A single
  shot therefore has soundness error ~`1/17` — useless.

`bind.rs`'s resolution: **κ binary-challenge rounds** (`c_j ∈ {0,1}`, `2^−κ` soundness). Per round the SAME
small integer `τ0(Z1_j[bit_idx_i])` is the digit response in BOTH the EC equation and the lattice opening,
and **the FULL `Z1_j` is mandatory** so the verifier can reconstruct the ABDLOP announcement
`w_c_j = A1·Z1_j + A2·Z2_j − c_j·t_A` and confirm the digit responses are projections of a *genuine* opening
of `t_A` (DESIGN R12 P2 — projecting an unverified opening is forgeable). So the `κ × full-opening` is
**load-bearing for this construction**, not slack. Shrinking it requires a *different* cross-domain bind.

## 3. Compaction options (all research-grade — each reopens the bind soundness)

| # | Idea | Size win | Soundness risk | Notes |
|---|---|---|---|---|
| **A** | **Multi-coefficient extraction** — bind via many coefficients `τ0,τ1,…,τ_{127}` of ONE opening's responses instead of `τ0` over κ rounds, so a single opening yields ~128 bits of binding. | **~κ× (→ ~450 KB)** | HIGH — needs a new soundness proof that 128 coefficient-projections of one challenge give `2^−128` cross-domain binding (the constant-coeff `[−8,8]` limit is exactly what this must overcome). | The highest-impact direction; the hardest to prove. |
| **B** | **Fold the κ rounds** (Bulletproofs/sumcheck-style) into `log κ` openings. | **~κ/log κ (→ ~3 MB at κ=128)** | MED — folding over the κ binary-round lattice+EC structure is non-standard; needs a recursion argument. | Less aggressive, more mechanical; preserves the per-round structure under a fold. |
| **C** | **Lower κ** if the anchor binding doesn't need `2^−128` (e.g. `2^−80` ⇒ κ=80). | ~1.6× only | LOW (just a parameter) but a real security reduction — needs a threat-model justification that a `2^−80` member-binding forgery is acceptable. | A cheap partial win; Josh/threat-model call, not a redesign. |
| **D** | **Separate, smaller anchor commitment** (commit just `w_bits`, not the full `s1`). | n/a | — | **REJECTED**: binding `w_bits` to the show's `t_A` *requires* opening `t_A`, which is the full `s1`. Circular. |
| **E** | **Out-of-band transport** (don't shrink; gossip a small digest, fetch the big vouch on request). | 0 (transport, not size) | none (orthogonal) | Always available as the deployment answer regardless of compaction; the size just makes it mandatory. |

## 4. Recommendation

1. **Ship E (out-of-band transport) as the deployment path regardless** — a ~tens-of-MiB single-publish
   record fetched on demand is acceptable (INTRODUCTION_RECORD §5), and it unblocks finishing HYP-343
   (chunks 4–5) without waiting on a crypto redesign. This is a sync-layer (HYP-313) follow-up.
2. **Pursue A (multi-coefficient extraction) as the real compaction** — it is the only option that gets to
   the ~hundreds-of-KB range, and it attacks the actual culprit (the `τ0`-only, `[−8,8]` extraction). It is
   genuine research: design-first → Codex DESIGN-review (this construction took 13 rounds; a replacement
   will take as many) → build → gate. **Q for Josh:** pursue A now (delays the rest of HYP-343), or finish
   HYP-343 on E and schedule A as a dedicated optimization issue?
3. **B is the fallback** if A's soundness proof doesn't close; **C only with a threat-model sign-off.**

**The crypto built in chunks 1–3 is correct and reusable under any of these** — A/B change the anchor proof
shape only; the SEP credential, the LNP22 show, the FS record-binding, and the verifier seam stand.
