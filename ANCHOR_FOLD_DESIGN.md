# ANCHOR_FOLD_DESIGN.md — LaBRADOR-folding the κ anchor openings (HYP-343 B / compaction)

**Status:** design-first (no code). Goal: cut the C3 vouch from ~57 MB (κ=128) to ~a few MB by folding the
cross-domain anchor bind's κ lattice openings, **without changing the binding it proves or its 2⁻ᵏ
soundness**. Refs: `ANCHOR_COMPACTION_DESIGN.md` (§1 measurement, §5 shortness wall, §6–7 the leading
resolution), `ANCHOR_BIND_DESIGN.md` (the κ-round bind), `proof_anchor_bind.rs` (the code), `refs/labrador`
(the port source), LaBRADOR (Beullens–Seiler CRYPTO'23). Process: design → Codex DESIGN-review → port.

---

## 1. What we keep, what we fold (the spine)

The bind proves `w_bits` (in `t_A`, lattice) `=` `w` (in `C_r = w·g+r·h`, EC) via κ binary-challenge rounds
(2⁻ᵏ). Per round `j`: announcement `w_{c,j} = A1·y1_j + A2·y2_j`; FS bit `c_j`; **lattice response**
`Z1_j = y1_j + c_j·s1` (FULL `s1`, m1≈891) + `Z2_j`; **EC**: `z_{r,j}=ρ_{r,j}+c_j·r` and the digit responses
`τ0(Z1_j[bit_idx_i])`. Measured: the `Z1_j` are **88%** of the vouch; everything else (announcements, EC
scalars, digit responses) is KB.

**Keep unchanged (small):** the κ announcements `w_{c,j}` (d ring elems each), the EC equations
`A_j := Σ_i τ0(Z1_j[bit_idx_i])·g_i + z_{r,j}·h ?= c_j·C_r`, and the revealed digit responses
`τ0(Z1_j[bit_idx_i])`. These carry the cross-domain binding + its 2⁻ᵏ soundness, and they're tiny.

**Fold (the 88%):** the κ pairs `(Z1_j, Z2_j)`. They are κ SHORT vectors satisfying, for known
`(c_j, w_{c,j}, t_A)`, the **linear** relations
`R_j: A1·Z1_j + A2·Z2_j − c_j·t_A = w_{c,j}` and the **pins** `P_{j,i}: const_coeff(Z1_j[bit_idx_i]) =
ρ_{j,i}` (the revealed digit value). Both are linear in the witness ⇒ a LaBRADOR relation.

**Un-compress the FS (the one structural change).** Today bind.rs is FS-COMPRESSED: it does NOT send
`w_{c,j}`; the verifier reconstructs it from `Z1_j`. That is incompatible with folding (the verifier no
longer has `Z1_j`). So **send the κ announcements `w_{c,j}`** (κ·d ring elems ≈ 64 KB at d=1) and derive the
FS bits `c_j` from the SENT announcements. Now `c_j` is checkable without the responses, and the responses
are free to be folded. (This trades ~64 KB of announcements for the ~54 MB the fold removes.)

---

## 2. The fold (LaBRADOR principal step, applied)

Treat the witness as the κ short vectors `s^{(j)} := (Z1_j ‖ Z2_j)` with norm bound `Σ_j‖s^{(j)}‖² ≤ B²`
(each `‖Z1_j‖, ‖Z2_j‖` already rejection-bounded in bind.rs — sum the squares). The verifier already holds
the Ajtai-style commitment to them implicitly via `R_j` (a public-linear image of `s^{(j)}` equals
`w_{c,j}+c_j·t_A`). LaBRADOR step:

1. **Amortize:** verifier sends ring challenges `γ_1..γ_κ` (norm-bounded, pairwise-invertible diffs); prover
   sends ONE `z = Σ_j γ_j·s^{(j)}` + garbage `g_{jk} = ⟨s^{(j)}, s^{(k)}⟩`, `h`-terms for the linear parts.
2. **Verify (folded):** `Σ_j γ_j·(A1·Z1_j+A2·Z2_j−c_j·t_A) = Σ_j γ_j·w_{c,j}` reduces to ONE linear check on
   `z`; the pins fold to `Σ_j γ_j·const_coeff(Z1_j[bit_idx_i]) = Σ_j γ_j·ρ_{j,i}` — also ONE check on `z`
   (const_coeff is linear over the RING-element `z` here because we are checking a *linear image*, not
   reading τ0 of a product — the τ0-nonlinearity that blocked §6 was about the EC fold, which we DON'T do).
3. **Stay short:** base-`b` decompose `z = z^{(0)}+b·z^{(1)}+…` (each `‖z^{(t)}‖<b`), commit, **recurse** on
   the smaller witness `(z^{(t)}, g, h)`. `O(log κ)` levels; each level's commitment is `O(1)` (M-SIS).

Result: the κ openings (κ·m≈114k ring elems) → `O(log κ)` openings + the garbage (`O(κ²)` SCALARS `g_{jk}`,
but scalars are cheap vs ring elements — and LaBRADOR's recursion amortizes the garbage too). Net target:
**~57 MB → ~3 MB.**

---

## 3. Soundness (the part the gate must scrutinize)

Claim: the folded bind has the SAME `2⁻ᵏ` cross-domain binding as bind.rs. Argument sketch:

- **The fold is a PoK (LaBRADOR soundness):** its extractor yields κ short `(Z1_j, Z2_j)` satisfying every
  `R_j` and every pin `P_{j,i}`. So the revealed digit values `ρ_{j,i}` ARE `const_coeff(Z1_j[bit_idx_i])`
  of genuine openings of `t_A` under the FS-fixed `c_j` — exactly bind.rs's R12-P2 requirement, now
  enforced by the fold's extractor instead of by sending each `Z1_j`.
- **The EC + κ-round binding is UNCHANGED:** the EC eqs use `ρ_{j,i}` and the announcements' FS `c_j`,
  identical to bind.rs. Given the extracted genuine openings, a `w_bits ≠ w_{EC}` cheat survives a random
  `c_j` w.p. ≤ ½ ⇒ `2⁻ᵏ` over κ rounds. The fold changed only HOW the openings are conveyed, not the
  binding test.
- **Knowledge soundness composition:** anchor-soundness = (LaBRADOR extractor succeeds) ∧ (κ-round binding).
  Standard AND of two PoKs over a shared FS transcript.

**Open soundness obligations (must close in the design/gate, NOT hand-waved):**
(a) LaBRADOR extractor validity over κ openings of ONE commitment `t_A` (not r independent commitments) —
confirm the `5e`-class invertibility of `γ_j` diffs over the composite `q̂`. (b) The norm bound `B²`
propagation through the base-`b` recursion (LaBRADOR's NormCheck / JL projection at our `q̂`, NHAT=64).
(c) The pins are genuinely LaBRADOR dot-product-expressible (a `const_coeff(·)` projection is a fixed
linear functional ⇒ a `φ_i` inner-product term — yes, but write it explicitly). (d) ZK: the fold must not
leak `s1` beyond what bind.rs already does (LaBRADOR is HVZK; compose with the existing rejection masks).

---

## 4. Size + the honest residual

`~O(log κ)·m` for the folded responses + `κ·d` announcements + `κ`·(EC scalar + digit responses). At
κ=128, d=1: ~3 MB (vs ~57 MB). At production d=4: ~larger but the κ-scaling — the dominant term — is gone.
**Still pair with out-of-band transport (E):** a few-MB single-publish record is borderline for gossip, so
the introduction record gossips a digest + the vouch is fetched on request regardless. Folding turns
"undeployable" into "comfortably out-of-band."

---

## 5. Build order (each chunk: tests + Codex gpt-5.5/high gate)

0. **Gate THIS design** — esp. §3(a)–(d). Resolve before code.
1. **Un-compress the FS** in `proof_anchor_bind.rs`: send `w_{c,j}`, derive `c_j` from them. (Pure
   refactor; the existing tests must still pass — same soundness, just announcements on the wire.)
2. **Port the LaBRADOR core** from `refs/labrador` into a new `vouch-crypto/src/labrador_fold.rs` over our
   proof ring `R_q̂` (NHAT=64, composite q̂): amortized opening + garbage + base-`b` decomposition + the
   recursion + NormCheck. Gate against transcribed reference vectors (the `refs/labrador` tests).
3. **Express the anchor relation** (`R_j` + pins) as LaBRADOR constraints; wire the fold to replace sending
   `Z1_j`/`Z2_j`. Regression: a folded bind verifies; a tampered revealed `ρ_{j,i}` / wrong `c_j` rejects;
   the byte size drops ~`κ/log κ`×.
4. **Re-compose** into `pq_vouch` (the show + the folded anchor + the EC eqs + the nullifier), update the
   codec, re-measure the vouch size, full-suite + Codex gate.

Genuine multi-session lattice-folding port; faithful transcription from `refs/labrador`; gate every chunk.
