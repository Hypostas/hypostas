# Aggregated Masked Show — LNP22 Figure 7.2 (HYP-352 item 1 (C), §C-iv aggregation)

**Status:** ✅ DESIGN COMPLETE — approved to build. Codex DESIGN-review rounds 0–2: R0 (3 P1s + 5 P2s) →
R1 (P1.1 tail-constants + P1.3 four-square×3 RESOLVED) → R2 (**P1.2 Eq 7.11 transcription RESOLVED; no
remaining/new P1; "sound and faithful enough to begin the chunked build C1→C5"**). The build transcribes
Eq 7.11 verbatim from the PDF; `D'_sm` stored pre-negated; tail constants `c_{n̂m1}/c_{n̂m2}/c_256` (not the
challenge). Proceed C1→C5 per §5.
**Supersedes:** the separate-masked-proof rollout (commits aa3a36a + 3a7087f) for `proof_show`.
**Ref:** thesis ePrint 2024/131 (`refs/jeudy_thesis_2024.pdf`) §7.4.3, Figure 7.2, Eq 7.9–7.12, Lemmas 7.5–7.7, Table 7.1.

---

## 0. Why — the ZK gap this closes

The §C-iv rollout migrated the show's three sub-proofs (2 norms + binariness) to **separate** masked
proofs (`proof_relation_zk`), each committing its `c¹` garbage as `t1 = b·s2 + e1`. All three share the
**same `s2`** (the show's one commitment randomness) and the **same NUMS row `b`** (fixed seed). Therefore

```
t1_i − t1_j = e1_i − e1_j        (the b·s2 cancels — ALGEBRAICALLY EXACT)
```

and `e1 = cross(y,s1)+lin(y)−B·y2` has an `s1`-dependent covariance, so the cross-proof `t1` differences
leak `s1`'s statistics. A *single* masked proof is ZK (`b·s2` hides `e1` via M-LWE); only the **difference**
across proofs sharing `(s2,b)` leaks. `proof_relation_zk`'s own doc already says it is the *single-relation*
form and the multi-relation show must **aggregate** (Eq 7.9), not separate-proof. The SEP relation is also
still unmasked (reveals `e0/e1` raw) — it is full-ring, needing full-ring garbage commitment.

**The fix (this design):** the thesis's faithful construction — **one** garbage commitment `(t0,t1)` for the
**whole** aggregated relation `ŝ^T F ŝ + f^T ŝ + f = 0`. No per-relation garbage ⇒ no cross-proof differences
exist ⇒ the leak is structurally impossible, and the SEP relation is masked as one block of `F`.

---

## 1. The relation being proven (thesis p.190)

Witness `(v1, v2, v3, t, m_sm)` (all-concealed base case: no revealed attributes `m_I`, so `u' = q1·u`):

```
q1·( A·v1 − B·v2 + A3·v3 + G(t·v2) − D_sm·m'_sm ) = q1·u   (mod q̂R)   [the SEP signature eq, d rows]
‖v1‖₂ ≤ B1',  ‖v2‖₂ ≤ B2,  ‖v3‖₂ ≤ B3                                 [exact-ℓ2 norms]
‖t‖₂ = √w,  t, m_sm ∈ T1                                              [tag fixed-weight + binariness]
```

**Four-square slack (P1.3 — all three norm witnesses):** `v1, v2, v3` are three separate witnesses, each
with its own bound (`B1', B2, B3`). For EACH `j∈{1,2,3}`, decompose `Bj² − ‖vj'‖₂² = a_{j,0}² + a_{j,1}² +
a_{j,2}² + a_{j,3}²` (Lagrange four-square), pack `a_j = a_{j,0}+a_{j,1}x+a_{j,2}x²+a_{j,3}x³`, set
`vj'' = [vj'^T | a_j]^T` so `‖vj''‖₂² = Bj²` **exactly**. The exact-norm equations 3.2b–3.4b then become
the three `F''` norm blocks. (Our current single `norm_slack` is replaced by this four-square form for all
three — **D1** below.) Note `v3` is itself a signature-component witness, NOT a slack carrier.

Everything is lifted via the subring embedding `θ` (our `embed`/`SUBRING_K`): `v'_j = θ(v_j)`,
`t' = θ(t)`, `m'_sm = θ(m_sm)`, `A'' = [Â|0]` etc. The quadratic term `G·θ(t·v2)` is linearised into
`t'·G''·v2''` via the `G'_i` permutation construction (thesis p.190) — **this is our `sep_bilinear`**.

---

## 2. The protocol (Figure 7.2) — five rounds

Notation: `ŝ = [s1^T | s1*^T | m̂^T | m̂*^T]^T`, `m̂ = [y3^T | g^T]^T` (BDLOP message = approx-range mask +
garbage masks). `*` = the conjugate automorphism `σ_{-1}` (our `conjugate()`).

### First round → `msg1 = (t_A, t_B, w)`
1. `s2 ← χ` (CSPRNG ternary). `t_A = A1·s1 + A2·s2` (Ajtai — our `params.commit`).
2. `y1 ← D_{σ1}`, `y2 ← D_{σ2}`. `w = A1·y1 + A2·y2` (mask commitment).
3. `y3 ← D_{256,σ3}` (approx-range mask, 256 ints). `g ← U({x∈R̂ : τ0(x)=0}^ℓ)` (ℓ garbage masks, τ0=0).
4. `m̂ = [y3 | g]`. `t_B = B_{y,g}·s2 + m̂` (BDLOP — `B_{y,g} ∈ crs`).
5. `chal1 = H(1,…,msg1) = (R0,R1) ∈ {0,1}^{256×m1·n̂}` (binary challenge for the approx-range proof).

### Second round → `msg2 = z3^Z ∈ Z^256`
6. `R = R0 − R1`. `z3 = τ(y3) + R·τ(s1) ∈ Z^256`. **Reject** via `Rej1(z3, R·τ(s1), σ3, M3)`.
7. `chal2 = (γ_{i,j}) ∈ Z_q̂^{ℓ×262}` (per-`h_i` aggregation weights for the 7 equation families).

### Third round → `msg3 = (h1,…,hℓ) ∈ R̂^ℓ`
8. The seven equation families over `Z_q̂` (3.1b–3.7b):
   - (3.1b) `τ(y3) + R·τ(s1) = z3` — approx-range / witness shortness.
   - (3.2b–3.4b) `⟨τ(v_j''),τ(v_j'')⟩ = B_j²` for `j∈{1,2,3}` — exact norms (our `squared_norm`).
   - (3.5b) `⟨τ(t'),τ(t')⟩ = w` — tag fixed-weight.
   - (3.6b) `⟨τ(t'),τ(t')−1⟩ = 0` — tag binariness.
   - (3.7b) `⟨τ(m'_sm),τ(m'_sm)−1⟩ = 0` — message binariness.
9. Combined into ℓ garbage polys via automorphisms + `γ` (**Eq 7.9**):
   ```
   h_i = g_i + Σ_j γ_{i,j}(e_j*·y3 + r_j*·s1 − z3,j)            [approx-range, 256 terms]
            + γ_{i,257}(v1''*·v1'' − B1'²) + γ_{i,258}(v2''*·v2'' − B2²) + γ_{i,259}(v3''*·v3'' − B3²)
            + γ_{i,260}(t'*·t' − w) + γ_{i,261}(t'*(t' − 1)) + γ_{i,262}(m'_sm*(m'_sm − 1))
   ```
   `g_i` (τ0=0) masks every non-`τ0` coefficient; the truth is `τ0(h_i)` (= 0 iff all families hold).
10. `chal3 = (μ_i) ∈ R̂^{ℓ+d̂k}` (final aggregation: ℓ for the `h_i`, `d̂k` for the SEP rows).

### Fourth round → `msg4 = (t0, t1)`
11. Combine the `h_i` well-formedness AND the main SEP relation (`A''v1'' − B''v2'' + A3''v3'' −
    D'_sm·m'_sm + t'·G''·v2'' = u'`, `d̂k` rows) via `μ` into **Eq 7.10**: `0 = Σμ_i(h_i…) + Σμ_{ℓ+i}(SEP_i)`.
12. Recast as `ŝ^T F ŝ + f^T ŝ + f = 0 (mod q̂R)` — **the build transcribes Eq 7.11 VERBATIM from the PDF**;
    the map below fixes the layout (P1.2). `ŝ = [s1 | s1* | m̂ | m̂*]`, `s1 = (v1'',v2'',v3'',t',m'_sm)`,
    `m̂ = [y3 | g]`. **Packing dims (thesis p.190):** `|v1''|=2d̂k̂+1`, `|v2''|=kd̂k̂+1`, `|v3''|=kk̂+1`,
    `|t'|=k̂`, `|m'_sm|=k̂·m_sm` (each `vj''` carries its OWN four-square slack +1; **v3'' uses `kk̂+1`,
    NOT the v2'' dim** — P1.2a).
    - **`F''` (scalar-family quadratic, the `(s1, s1*)` cross-block, diag over `γ`):**
      `Σ_i μ_i · diag( γ_{i,257}·I_{2d̂k̂+1}, γ_{i,258}·I_{kd̂k̂+1}, γ_{i,259}·I_{kk̂+1},
      (γ_{i,260}+γ_{i,261})·I_{k̂}, γ_{i,262}·I_{k̂·m_sm} )` — norms 3.2b–3.4b, tag (3.5b `w`+3.6b),
      message (3.7b). Note the tag block carries `γ260+γ261` (norm + binariness on the same `t'`).
    - **`F'` (SEP quadratic `t'·G''·v2''`):** `Σ_{i∈d̂k̂} μ_{ℓ+i}·G''_i` at the `(t', v2'')` cross-position
      (zeros elsewhere) — `sep_bilinear`'s `G''_i`.
    - **`f` (linear) — EXACT block order over `ŝ` (P1.2b):**
      | block | value |
      |---|---|
      | `v1''` | `Σ_iΣ_j μ_iγ_{i,j} r₁,j* + Σ_{i∈d̂k̂} μ_{ℓ+i} A''ᵀe_R̂` |
      | `v2''` | `Σ_iΣ_j μ_iγ_{i,j} r₂,j* − Σ_{i∈d̂k̂} μ_{ℓ+i} B''ᵀe_R̂` |
      | `v3''` | `Σ_iΣ_j μ_iγ_{i,j} r₃,j* + Σ_{i∈d̂k̂} μ_{ℓ+i} A₃''ᵀe_R̂` |
      | `t'` | `Σ_iΣ_j μ_iγ_{i,j} r_t,j*` |
      | `m'_sm` | `Σ_iΣ_j μ_iγ_{i,j} r_sm,j* + Σ_{i∈d̂k̂} μ_{ℓ+i} D'_smᵀe_R̂` (`D'_sm` stored pre-negated — P1.2c) |
      | `v1''*`,`v2''*`,`v3''*` | **0** |
      | `t'*` | `−Σ_i μ_iγ_{i,261}·1_{R̂k̂}` (tag binariness 3.6b — on the **conjugate**, not `y3`) |
      | `m'_sm*` | `−Σ_i μ_iγ_{i,262}·1_{R̂k̂m_sm}` (msg binariness 3.7b — on the **conjugate**) |
      | `y3` (in `m̂`) | `Σ_i μ_i Σ_j γ_{i,j} e_j*` (approx-range coupling 3.1b) |
      | `g` (in `m̂`) | `[μ_1 \| … \| μ_ℓ]ᵀ` |
      | `m̂*` (= `y3*`,`g*`) | **0** |
    - **`D'_sm` sign (P1.2c):** Eq 7.10's SEP relation is `… − D'_sm·m'_sm − u' = 0`, but the extracted
      Eq 7.11 `m'_sm`-block shows `+D'_smᵀe_R̂`. CONVENTION: **store the SEP `D'_sm` block pre-negated**
      (so `sep_linear` already yields `−D'_sm·m'_sm`), and the `f`-block uses `+D'_smᵀe_R̂` consistently —
      verified by a smoke test that the honest witness gives `ŝ^TFŝ+f^Tŝ+f = 0`. Do NOT leave implicit.
    - **scalar `f`:** `−Σ_i μ_i( Σ_j γ_{i,j} z3,j + γ_{i,257}B1'² + γ_{i,258}B2² + γ_{i,259}B3² +
      γ_{i,260}w + h_i ) − Σ_{i∈d̂k̂} μ_{ℓ+i} u'_i`.
    The `r_{·,j}` split `r_j*·s1 = r₁,j*·v1'' + r₂,j*·v2'' + r₃,j*·v3'' + r_t,j*·t' + r_sm,j*·m'_sm`
    (Eq 7.10, the approx-range `R`-row lifted + split across the witness blocks).
13. Garbage with `y = [y1 | y1* | −B_{y,g}y2 | −(B_{y,g}y2)*]` (**Eq 7.12**):
    `e0 = y^T F y`, `e1 = ŝ^T F y + y^T F ŝ + f^T y`. Commit `t0 = b^T y2 + e0`, `t1 = b^T s2 + e1`
    (`b ∈ crs`, ONE row — the SINGLE garbage commitment for everything).
14. `chal4 = c ∈ C` (the main challenge).

### Fifth round → `msg5 = (z1, z2)`
15. `z1 = y1 + c·s1`, `z2 = y2 + c·s2`. **Reject** via `Rej1` on both. `π = (t_A,t_B,z3,h1..hℓ,t1,c,z1,z2)`.

### Verification (Figure 7.2, right)
- `w = A1·z1 + A2·z2 − c·t_A`; recompute `chal1..3`; `μ` from `chal3`.
- `z = [z1 | z1* | c·t_B − B_{y,g}·z2 | (c·t_B − B_{y,g}·z2)*]` — the masked opening
  (`c·t_B − B·z2 = c·m̂ − B·y2`, the garbage opened **without revealing `m̂`**).
- **Reconstruct** `t0 := z^T F z + c·f^T z + c²·f − (c·t1 − b^T z2)` (NOT a transmitted field — `t0 ∉ π`;
  the verifier rebuilds it, forms `msg4 = (t0, t1)`, and the soundness comes from `b5` below).
- `b1: ‖z1‖₂ ≤ c_{n̂m1}·σ1·√(n̂m1)`,  `b2: ‖z2‖₂ ≤ c_{n̂m2}·σ2·√(n̂m2)`,  `b3: ‖z3^Z‖₂ ≤ c_256·σ3·√256`
  — the `c_N` are **Gaussian-tail constants** (P1.1; NOT the Fiat–Shamir challenge `c`), the standard
  `‖D_σ^N‖₂ ≤ c_N·σ·√N` bound from the rejection analysis; the soundness β (Lemma 7.6) uses these same
  `c_{n̂m1}, c_{n̂m2}`.
- `b4: ∀i, τ0(h_i) = 0` — the relation-truth predicate, sound **only together with** the F reconstruction
  (P2.2: `b4` proves each randomized scalar relation; the `t0` check proves the published `h_i` are
  well-formed — both are required).
- `b5: chal4 = H(4, crs, x, msg1, msg2, msg3, msg4) = c` — binds the reconstructed `t0` (Figure 7.2).

---

## 3. Soundness / ZK (Lemmas 7.5–7.7)

- **Soundness** `ε = 2/|C| + q_min^{−n̂/κ} + q_min^{−ℓ} + 2^{−128} + ε_{M-SIS}` (Lemma 7.6, β =
  `8η√((c_{n̂m1}·σ1·√(n̂m1))² + (c_{n̂m2}·σ2·√(n̂m2))²)` — the Gaussian-tail constants `c_{n̂m1}/c_{n̂m2}`,
  NOT the challenge). The `q̂ > max(B², 82/√26·n̂m1·B256, 2B256²/13 − B256)` bound is our
  HYP-330 calibration (`q̂≈2^57.7` clears it; this is the SAME bound `proof_params::zk_bound` encodes).
- **ZK** (Lemma 7.7, simulator on p.189): one garbage set, `g_i` masks the `h_i`, `t_B` hides `m̂` via
  knapsack-M-LWE, `t0/t1` hide `e0/e1`. **No cross-proof difference exists** (single proof) ⇒ the §0 gap
  cannot occur. The simulator samples `c, t_A, z1, z2, t_B, R, z3, γ, h_i, μ, t1` and DERIVES `w, t0` —
  proving nothing about `(t,v,m)` leaks.

---

## 4. Code map — reuse vs new

**Reuse (already gate-clean):**
- ring `R̂_q̂` (`proof_ring`, q̂≈2^57.7 HYP-330), conjugate `σ_{-1}`, challenge space `C` (`proof_challenge`).
- subring embed `θ` (`embed`, `SUBRING_K`, `block`), `sep_bilinear` (= `G''_i` quad term), `sep_linear`
  (= `A''v1''−B''v2''+A3''v3''−D'_sm·m'_sm`), `neg_u_rows` (= `u'`), `aggregate_rows`, `mu_vector`.
- `squared_norm` / `norm_constraints` (3.2b–3.4b), `aggregated_binariness` (3.6b/3.7b + tag-weight 3.5b).
- garbage helpers `garbage_b`, `b_dot`, `sample_garbage` (τ0=0), `commit_garbage` (`proof_garbage`/`_zk`).
- rejection `Rej1` (`gaussian`/`proof_linear`), Gaussian `sample_z`, `D_{σ}`.

**New (this build):**
- **C1 — approx-range proof (3.1b):** `y3 ← D_{256,σ3}`, the binary challenge `R=R0−R1`, `z3=τ(y3)+Rτ(s1)`,
  `Rej1`. The `e_j*·y3 + r_j*·s1 − z3,j` terms of Eq 7.9. (NEW machinery; the witness-shortness leg the
  current code lacks.)
- **C2 — the `h_i` assembly (Eq 7.9):** combine the 7 families with `γ` + the conjugate automorphism into ℓ
  garbage polys; `g_i` mask; `τ0(h_i)` truth.
- **C3 — the F-block (Eq 7.11):** assemble `F = [[F'|F''],[0|0]]` over `ŝ=[s1|s1*|m̂|m̂*]`, the linear `f`,
  the scalar `f`. The intricate core — `F''` diag blocks + `F'` SEP-`G''` block.
- **C4 — single garbage + masked opening (Eq 7.12):** `y`, `e0=y^TFy`, `e1=ŝ^TFy+y^TFŝ+f^Ty`,
  `t0=b^Ty2+e0`, `t1=b^Ts2+e1`; verify `z=[z1|z1*|c·t_B−B·z2|·*]`, the one quadratic check.
- **C5 — the protocol driver + Fiat–Shamir** (`prove_show`/`verify_show` REPLACEMENT, 5 rounds) + the
  `#[ignore]` full-width capstone.

**Removed:** `prove_sep_relation`/`verify_sep_relation` (subsumed into F), the separate
`prove_signature_norms`/`binariness` masked calls (subsumed). `SepRelationProof` struct → `AggShowProof`.

---

## 5. Build order (chunks, each gated)

1. **C0 (this doc)** — design + Codex DESIGN-review.
2. **C1** — approx-range proof (`y3`, binary-challenge `z3`, `Rej1`) as a standalone, tested module.
3. **C3a** — `ŝ` assembly + the `F''` (diag γ) block + `e0/e1` for the norm/tag/binariness families ONLY
   (no SEP yet); verify the one quadratic check on that sub-F. Smoke + integration.
4. **C3b** — add the `F'` SEP-`G''` block (the `Σμ_{ℓ+i}G''_i` rows) + `f`/scalar-`f`; full F.
5. **C2** — wire the `h_i` (Eq 7.9) + `b4: τ0(h_i)=0` + the `γ` challenge.
6. **C4/C5** — the single `(t0,t1)` + masked opening `z` + the 5-round driver + FS + bounds `b1..b3` + `b5`.
7. **Capstone** — `#[ignore]` honest full-width show verifies; tampered-each-family rejects; the **ZK
   leakage test** (the §0 difference no longer exists — assert there is exactly one `t1`).
8. **Migrate** — repoint vouch composition; delete the subsumed separate proofs; reconcile
   `LNP22_SHOW_DESIGN.md`.

---

## 6. Open decisions (for Codex DESIGN-review)

- **D1 — norm slack (RESOLVED, P1.3):** four-square `a_{j,0..3}` for **ALL THREE** `v1,v2,v3` (thesis
  p.190: "perform the same decomposition" for a2,a3), making `‖vj''‖₂²=Bj²` exact via Lagrange. Replaces
  the single `norm_slack`. (C3a.)
- **D2 — `ℓ` (garbage count):** thesis Table 7.1 `ℓ=7`. Soundness `q_min^{−ℓ}`; ZK needs `ℓ` masks. Use 7.
- **D3 — params (RESOLVED, pin Table 7.1 SHOW):** `n̂=64, k̂=4, d̂=23, q1=549755813869, q̂≈2^57.7,
  m1=211, m2=74, ρ=8, η=93, γj=48.64, Mj=2, σ1=582380223, σ2=311305, σ3=114957847, ℓ=7`. `q̂` is the
  HYP-330 flip (live); `proof_params::zk_bound` encodes the Lemma 7.6 bound. σ/B256 PROVISIONAL until the
  HYP-330 external audit. The `b1..b3` tail constants `c_{n̂m1}, c_{n̂m2}, c_256` are the rejection tail
  (≈ from the thesis §8.3 53-bit-precision samplers), NOT the challenge.
- **D4 — revealed attributes `m_I`:** base case all-concealed (`u'=q1u`, `I=∅`). The `D_I·m_I` split is a
  later extension (selective disclosure / HYP-324) — out of scope here; note the seam.
- **D5 — approx-range vs exact-norm overlap (RESOLVED):** the thesis proves BOTH and both are required —
  3.1b (approx-range `z3`) = witness `s1` **shortness** for M-SIS soundness; 3.2b–3.4b (exact `⟨v,v⟩=B²`)
  = signature-component **validity**. Keep both.
- **D6 — z3 sign convention (RESOLVED, P2.3):** lock to **Eq 7.9** (the safer source): `z3^Z = τ(y3) +
  R·τ(s1)` and the `h_i` term `e_j*·y3 + r_j*·s1 − z3,j`. Define `r_j` (the `R`-rows lifted to R̂) so
  `r_j*·s1` splits across the witness blocks as in step-12's `r_{·,j}`. (Figure 7.2's prover line shows the
  same up to sign; Eq 7.9 governs.)

---

*Faithful transcription of thesis Figure 7.2 / Eq 7.9–7.12. No rolled crypto. Behind
`experimental-unaudited`. HYP-330 external audit re-checks σ/B256 pre-mainnet.*
