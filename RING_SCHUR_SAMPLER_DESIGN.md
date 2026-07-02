# Ring-structured Schur sampler — design (HYP-356)

**Status:** DESIGN (design-first, pre-impl for chunks 2–4). Chunk 1 (the negacyclic FFT foundation,
`vouch-crypto/src/sep_fft.rs`) is built + Codex-gate-clean on branch `iris/hyp-356-ring-schur-fft-foundation`.
**Issue:** HYP-356 (FU2-deep of HYP-354). **Reference:** Jeudy ePrint 2024/131 (`covariance.c` `compute_covariance`,
`poly_q_sampling.c` `poly_q_vec_2d_dk_sample_perturb`) — C code NOT local; this derives from the paper +
the shipped flat implementation (`sep_trapdoor.rs::build_sigma1`), which is the ground truth.

## 1. Goal & the soundness trap

Replace the FLAT `m1·N × m1·N` Cholesky factor `L1` (~8.4 MB `f32`, `SepTrapdoorKey::l1`) with the reference's
per-frequency eval-domain factorization (~128 KB). **The trap (why design-first):** the sampler produces
`p1 = round(L1·𝒩 + mean)`; a subtly-wrong covariance still yields short pre-images that PASS the exact
syndrome test `A_t·x = target` AND `sep_sig`'s B1/B2/B3 norm bounds — the *distributional* error is invisible
to every functional test. It is caught ONLY by (a) an **operator-equivalence** check against the flat matrix
(chunk 2) and (b) a **statistical** check that the empirical sample covariance ≈ `Σ1` (chunk 4).

## 2. The flat covariance (ground truth — `build_sigma1`)

`m1 = 2d` (top block), `d = 4`, `N = 256`. With `rr_{ij} := Σ_k R[i][k]·adjoint(R[j][k]) ∈ R` (`R[i]` the
`i`-th trapdoor row over the `dk` gadget columns; `adjoint` = negacyclic conjugate, `r*[0]=r[0]`,
`r*[t]=−r[N−t]`), the flat covariance is

```
Σ1[i·N+a][j·N+b] = ( S1_SQ·[i=j][a=b] + SGINVSQ_S2INVSQ · M_{rr_ij}[a][b] ) / (2π)
```

where `M_p` is the **negacyclic matrix** of poly `p`: `M_p[a][b] = center(p[a−b])` for `a≥b`, `−center(p[a+N−b])`
for `a<b` (the `X^N=−1` skew-circulant). Constants (`sep_params.rs`): `S1_SQ = 34270592.82`,
`SGINVSQ_S2INVSQ = −4623.49` (already-negated `−(s_G⁻²−s2⁻²)⁻¹`), `TWO_PI` (width²→variance). PSD is
guaranteed by keygen's exact `R_MAX` gate (`‖R‖₂² ≤ 7390 < 7413`).

## 3. Eval-domain diagonalization (chunk 2)

`M_p` is skew-circulant ⇒ **diagonalized by the negacyclic transform** (`sep_fft`): its eigenvalues are the
`N` evaluations `p̂(ω_ℓ)`, `ω_ℓ = ζ·e^{2πiℓ/N}` (`ζ=e^{iπ/N}`), the odd-`2N`-th roots. Applying the transform
to each of the `m1` blocks block-diagonalizes `Σ1` across frequency: at each `ω_ℓ` it becomes an **`m1×m1`
Hermitian** matrix

```
Σ̂1(ω_ℓ)[i][j] = ( S1_SQ·[i=j] + SGINVSQ_S2INVSQ · r̂r_{ij}(ω_ℓ) ) / (2π)
```

where `r̂r_{ij}(ω_ℓ) = negacyclic_fft(rr_{ij})[ℓ]` — computed by FFT'ing the SAME `rr_{ij}` poly `build_sigma1`
already forms (NOT by combining `R(ω)·conj(R(ω))` — reusing the exact ground-truth poly removes an adjoint-
convention pitfall). Hermitian because `rr_{ij} = adjoint(rr_{ji})` ⇒ `r̂r_{ij}(ω_ℓ) = conj(r̂r_{ji}(ω_ℓ))`
(verify this in a test). Store the per-frequency **lower-triangular Cholesky** `L̂(ω_ℓ)` (`Σ̂1(ω_ℓ) = L̂ L̂ᴴ`),
an `m1×m1` complex matrix: `N · m1(m1+1)/2` complex `f64` ≈ `256·36·16 B ≈ 147 KB` (vs 8.4 MB).

**Chunk-2 validation (operator equivalence — the correctness gate before any Cholesky):** for random real
block-vectors `x ∈ ℝ^{m1·N}`, the flat matrix–vector product `Σ1·x` must equal the eval-domain application
`ifft_blocks( Σ̂1(ω) · fft_blocks(x) )`, where `fft_blocks` FFTs each of the `m1` length-`N` sub-vectors and
`Σ̂1(ω)·` is the per-frequency `m1×m1` multiply. Assert max-abs agreement `< 1e-6·‖Σ1‖`. This certifies the
per-frequency matrices represent the SAME operator — independent of the sampler.

## 4. Eval-domain R_MAX certificate (chunk 3)

The flat keygen gate Choleskys `R_MAX·I − R·R*` (PD ⟺ `‖R‖₂² ≤ R_MAX`). Eval-domain equivalent: at each `ω_ℓ`,
the `m1×m1` Hermitian `R_MAX·I_{m1} − R̂R*(ω_ℓ)` must be PD (attempt its Cholesky; fail ⇒ reject `R`). Here
`R̂R*(ω_ℓ)[i][j] = r̂r_{ij}(ω_ℓ)` (the same evals). `λ_max(R·R*) = max_ℓ λ_max(R̂R*(ω_ℓ))`, so the per-frequency
PD checks are collectively EXACT — same guarantee as the flat gate, `O(N·m1³)` not `O((m1·N)³)`.

## 5. Eval-domain `sample_perturb` (chunk 4 — the subtle one)

Current `sample_pre`: `p2 ∈ R^{dk}` narrow (`~D` at `√(s2²−s_G²)`), `mean = NEGSGSQ_DIV_S2SQ_SGSQ·(R·p2)`,
`p1 = round(L1·𝒩 + mean)`. New p1 draw, per frequency, respecting **conjugate symmetry** so the inverse
transform is real:

1. `ĉ(ω_ℓ) = fft_blocks(mean)[ℓ]` — the conditional mean in eval domain (`mean = NEGSGSQ·R·p2`, `R·p2` via
   `negacyclic_mul`, chunk 1).
2. Conjugate-pair structure: `conj(ω_ℓ) = ω_{N−1−ℓ}` (since `conj(e^{iπ(2ℓ+1)/N}) = e^{iπ(2(N−1−ℓ)+1)/N}`).
   `N=256` ⇒ **128 pairs** `(ℓ, N−1−ℓ)`, `ℓ=0..127`, **no self-conjugate** (would need `2ℓ=N−1`, odd —
   impossible). So there are exactly `128·m1` complex degrees of freedom (matching the `m1·N` real DOF: `128
   pairs × m1 × 2 reals = m1·N`).
3. For each pair `(ℓ, ℓ' = N−1−ℓ)`: draw a fresh standard complex Gaussian `z ∈ ℂ^{m1}` (each entry
   `(𝒩(0,½)+i𝒩(0,½))`, unit variance per complex coord), set `p̂1(ω_ℓ) = L̂(ω_ℓ)·z + ĉ(ω_ℓ)` and the
   conjugate `p̂1(ω_{ℓ'}) = conj(p̂1(ω_ℓ))` ONLY for the zero-mean part... — **open Q (resolve in impl):**
   the mean `ĉ` is NOT conjugate-symmetric-free in general (it's the FFT of a real vector, so `ĉ(ω_{ℓ'}) =
   conj(ĉ(ω_ℓ))` DOES hold since `mean` is real). So set `p̂1(ω_{ℓ'}) = conj(L̂(ω_ℓ)·z) + ĉ(ω_{ℓ'})` with
   `ĉ(ω_{ℓ'}) = conj(ĉ(ω_ℓ))` — i.e. the noise conjugates, the mean is already conjugate by realness. Net:
   `p̂1(ω_{ℓ'}) = conj(p̂1(ω_ℓ))`. This guarantees `ifft` returns a real vector.
4. `p1 = round( ifft_blocks(p̂1) )` (real part; imaginary is ~1e-12 noise). Then `p = [p1 ; p2]` as today.

Variance bookkeeping: `L̂ L̂ᴴ = Σ̂1(ω_ℓ)` gives `p̂1(ω_ℓ)` covariance `Σ̂1(ω_ℓ)`; the conjugate-pair coupling
reproduces exactly the real covariance `Σ1` after `ifft` (standard real-Gaussian-via-Hermitian-spectrum
construction). **Confirm the `½`-variance-per-complex-coordinate normalization against `Σ1` in the statistical
test — the factor-of-2 between complex and real Gaussians is the classic error here.**

**Chunk-4 validation (statistical — the check the syndrome test can't give):** draw `M ≥ 200,000` samples of
`p1` at a FIXED small test `R` (e.g. `d=1`, `m1=2`, so `Σ1` is `2N×2N`); form the empirical covariance
`(1/M)Σ p1 p1ᵀ`; assert it matches the flat `Σ1` (build_sigma1) within a relative Frobenius tolerance that
shrinks like `1/√M` (`< ~0.03` at `M=2e5`). Zero-mean draw (`p2=0`) isolates the covariance from the mean.
Also keep the existing `sample_pre`/`sign`/production-d4 functional tests green (the syndrome must still hold).

## 6. Swap-in & chunk plan (each Codex-gated, rule #27)

- **2.** `sep_eval_cov.rs`: `Hermitian` `m1×m1` complex type + `cholesky_h` (Hermitian Cholesky) + build the `N`
  per-frequency `Σ̂1(ω_ℓ)` from `rr_{ij}` via `sep_fft`; the operator-equivalence test vs `build_sigma1`.
- **3.** Eval-domain R_MAX cert (per-freq Hermitian PD); wire into keygen alongside / replacing `build_rmax_gate`;
  test it accepts iff the flat gate accepts on random `R`.
- **4.** Eval-domain `sample_perturb` behind the same `sample_pre` signature; the conjugate-pair Hermitian-noise
  draw; the statistical empirical-covariance test; swap `SepTrapdoorKey.l1` (flat `L1`) → the per-freq factors.
- **5.** Drop the flat `L1` storage; re-measure key size (~8.4 MB → ~150 KB); full suite + Codex gate.

## 7. Risk

Soundness-critical (the credential's Gaussian sampler). Mitigations: reuse the EXACT `rr_{ij}` poly the
validated flat path builds (no re-derived adjoint); the operator-equivalence gate (chunk 2) + the statistical
covariance gate (chunk 4) catch the distribution errors the functional tests miss; behind `experimental-unaudited`
throughout; the precise core-SVP re-check remains HYP-330. Open questions flagged inline in §5 (the `½`-variance
normalization + the mean conjugate-symmetry) resolve in impl against the statistical test.
