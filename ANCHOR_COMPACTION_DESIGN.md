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

---

## 5. Feasibility analysis of A — the SHORTNESS WALL (2026-06-29, after Josh chose A)

Designing A revealed a fundamental obstacle that **reverses §3/§4's ranking**: A's `~κ×` single-shot
ambition is blocked, and **B (folding) is the realistic compaction**, not the fallback.

**The shortness wall.** Every lattice opening `Z = y + c·s` must be SHORT (`‖Z‖` bounded) — that shortness
IS the binding (the SIS extractor needs a short witness). So the challenge `c` MUST be small (ρ-bounded);
a large `c` makes `c·s` long and the opening unsound. This is why amplification needs *parallel
repetition* (κ small-challenge rounds), not one big-challenge round. Consequently:

- **"One large scalar challenge" (the obvious A) is unsound** — `c ∈ [0,2^128)` ⇒ `c·s` not short.
- **"Multi-coefficient extraction" doesn't rescue it** — the EC side commits to a SCALAR `w` (in
  `C_r = w·g + r·h`), so there is nothing to check the lattice responses' higher coefficients `τ1,τ2,…`
  *against*. Using them would require restructuring `C_r` into a vector/per-coefficient commitment — which
  breaks the BBS half's binding to the SAME `C_r` and is a far larger redesign than the anchor itself.
- **Even the binary→ρ-bounded tweak** (use `c_j ∈ [−8,8]` ⇒ ~4 bits/round ⇒ ~32 rounds, a 4× win) is the
  most A can plausibly offer, and only if the cross-domain extraction stays clean with non-binary `c_j`
  (the design chose binary deliberately for a clean `2^−κ`). A 4× win, not κ×.

**B (folding) is feasible and is the real path.** The κ openings are *parallel* SIS relations; fold them
with SMALL random coefficients (so the folded opening stays short) recursively — exactly LaBRADOR
(Beullens–Seiler, CRYPTO 2023) / lattice-Bulletproofs. That gives `~O(log κ)`-size (or `~√` for a single
fold layer): **~57 MB → a few MB** at κ=128. It preserves the existing per-round structure under a
recursion argument; it does not touch `C_r` or the BBS half.

**Revised recommendation:** the compaction is **B (LaBRADOR-style recursive folding of the κ anchor
rounds)**, optionally stacked with the ρ-bounded-challenge 4× tweak. A's `κ×` ideal is infeasible without
reshaping `C_r` (which cascades into the BBS half). **This is genuine, soundness-critical lattice-folding
research (LaBRADOR-class) — design-first → Codex DESIGN-review → build, with fresh focus, not rushed.**

---

## 6. LaBRADOR pulled (2026-06-29) — construction + the anchor-folding sketch

**Refs pulled:** paper = LaBRADOR (Beullens–Seiler, CRYPTO'23, eprint 2022/1341 — eprint is Cloudflare-
walled to curl/WebFetch; construction obtained from the zksecurity explainer
`blog.zksecurity.xyz/posts/labrador/`). **Reference Rust impl cloned to `refs/labrador`** (lattirust,
~2.5k LoC: `prover.rs`/`verifier.rs` + `r1cs/` + `binary_r1cs/`). Other impls: condor-rs (Nethermind),
Lazarus, LaZeR.

**The LaBRADOR principal relation:** prove knowledge of `r` SHORT vectors `s_i` with `Σ‖s_i‖² ≤ β²`
satisfying dot-product constraints `f(s) = Σ_{ij} a_{ij}⟨s_i,s_j⟩ + Σ_i⟨φ_i,s_i⟩ − b = 0`.

**The fold (one reduction step):** verifier sends `r` challenges `c_i` (pairwise-invertible differences,
norm-bounded by rejection); prover sends ONE `z = Σ_i c_i·s_i` + the garbage `g_{ij}=⟨s_i,s_j⟩`,
`h_{ij}`. Verifier checks `A·z = Σ c_i·t_i` (Ajtai/M-SIS commitment), `⟨z,z⟩ = Σ g_{ij}c_ic_j`,
`Σ a_{ij}g_{ij}+Σ h_{ii}−b=0`. **Shortness kept by base-`b` decomposing `z = z^(0)+b·z^(1)+…` before
recursing** (so `‖z^(k)‖ < b`, no norm blow-up). The checks are themselves dot-products ⇒ **recurse**;
dim shrinks `r^{(i+1)}=O(|s^{(i)}|^{1/3})` ⇒ **O(log n) proof**. Binding = M-SIS on the Ajtai commitment.

**The anchor map (the sketch):** our κ rounds are κ openings `Z1_j = y_j + c_j·s1` of the SAME `t_A` — i.e.
κ short vectors with the ABDLOP relation as a (linear) dot-product constraint. **Fold them: `Z = Σ_j γ_j·
Z1_j`, garbage `g_{jk}=⟨Z1_j,Z1_k⟩`, base-`b` decompose, recurse → `log κ` openings instead of κ.** That
collapses the 88% (κ×891 → ~log κ×891).

**★ THE OPEN DESIGN PROBLEM (cross-domain ∩ folding):** the κ EC equations `A_j = Σ_i τ0(Z1_j[bit_idx_i])·
g_i + z_{r,j}·h ?= c_j·C_r` must fold TOO. They CAN, because **`τ0(Σ_j γ_j·Z1_j[bit_idx]) = Σ_j γ_j·
τ0(Z1_j[bit_idx])` when `γ_j` are SCALARS** ⇒ the amortized EC eq reads the FOLDED `Z`'s bit responses
`τ0(Z[bit_idx])`. **But LaBRADOR's `c_i` are RING elements** (needed for invertible differences/soundness),
and `τ0` is NOT linear over ring multiplication — so the lattice fold (ring challenges) and the EC-binding
fold (scalar challenges) want DIFFERENT challenge types. Resolution candidates to design + gate: (i) two
coordinated folds — scalar `γ_j` for the EC leg, ring `c_i` for the lattice leg, tied by a shared FS
transcript; (ii) restrict the lattice fold to scalar challenges + prove the ABDLOP fold still extracts
(scalar diffs invertible mod q̂ w.h.p. — the `5e`-class modulus check applies); (iii) move the EC digit
check into the lattice relation as a dot-product so ONE fold covers both. **This is the crux of the
B design — next step: design-first doc (ANCHOR_FOLD_DESIGN) → Codex DESIGN-review → port from
`refs/labrador`. Soundness-critical; fresh focus.**
