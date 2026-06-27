# PARAM_CALIBRATION.md — de-provisionalizing the C3 lattice parameters (HYP-352 item 3 / HYP-330)

**Status:** calibration ANALYSIS locked (this doc). Security-critical, by-hand from the audited reference
(Jeudy thesis ePrint 2024/131 = `refs/jeudy_thesis_2024.{pdf,txt}`). "No external audit — Opus + Codex."
Constant-flipping + the modulus resolution follow from this analysis; nothing here is free-handed — every
number traces to a thesis line.

> ⚠️ Why this is its own careful pass and not a code-chunk: the params **are** the security. Wrong dims/
> bounds = a real M-SIS/M-LWE break, NOT a backstopped soundness bug. And the Codex gate validates
> soundness *logic* (it caught every P1/P2 this session) but **cannot recompute lattice bit-security from a
> diff** — so the analysis below is the actual safety net and must be checkable line-by-line.

## 1. Target + cost model (thesis §6.4 + §9)

- **Target: ~165-bit M-SIS core-SVP** (classical). Thesis §6.4 line 13944: *"we need to aim for around 165
  bits of M-SIS core-SVP hardness instead of 213"* — the rejection-based proof (Lemma 1.31) drops the loss
  so 165 core-SVP nets the intended ~128-bit security. M-LWE side calibrated to **λ=128** (thesis Table 3.2).
- **Cost model (thesis §9, lines 19958–19983):** root-Hermite factor δ₀ ↔ BKZ blocksize `b` via Chen's
  formula (Heuristics 9.1 GSA + 9.2); **classical sieving cost 2^(0.2924·b)** [BDGL16], **quantum
  2^(0.2570·b)** [CL21]. So bit-security = 0.2924·b (classical) / 0.2570·b (quantum); core-SVP = the
  conservative one-SVP-call lower bound.
- **Method per instance:** from (lattice rank `m·n`, modulus `q`, target norm `β`) compute the δ₀ that a
  BKZ-`b` basis needs to find a vector ≤ β (standard `β ≈ δ₀^(rank)·q^(d·n/rank)` GSA condition), invert to
  `b`, require 0.2924·b ≥ 165 (M-SIS) / ≥ the 128-bit M-LWE blocksize.

## 2. The SEP credential = the thesis SEP⋆ (Ch6.4, "optimized signature with efficient protocols")

Our `sep_sig` IS SEP⋆. Confirmed line-by-line: line 13970 `At = [A|tG−AR|A3]v = u+Dm`; **our OblSign is the
thesis's own privacy-protocol variant** — line 13957-13964: *"hide his message by adding Aru to the
commitment Dm... ‖v1‖₂ ≤ B1 + ‖ru‖₂... ru composed of binary polynomials, ⇒ only a √(2n) additive term in
the verification bound."* That is exactly `oblivious_commit`/`oblivious_unblind` (`v = v' − [ru;0]`,
binary `ru`, bound `B1 + ‖ru‖`). So we transcribe SEP⋆'s param set directly — no re-derivation of the base.

### Calibrated SEP⋆ 128-bit set (thesis line 14218 + Thm 6.3/6.4)
| Param | Thesis value | Source | Our constant |
|---|---|---|---|
| `n` (ring degree) | **256** | §6.4 / Table 3.2 | `sep_ring::N = 256` ✅ already correct |
| `d` (module rank) | **4** | line 14218 (λ=128, n=256, d=4, k=5, Q=2³²) | `SepSigKey::keygen(d, …)` — **prod = 4** (tests use 1 for speed) |
| `k` (gadget dim) | **5** | line 14218 | `keygen(_, k)` — **prod = 5**; `KG`/gadget base `b` set so `k=⌈log_b q⌉=5` |
| `Q` (signing-query bound) | **2³²** | line 14218 | issuance/issuer lifetime budget (doc-level; informs the tag-space `|Tw|`) |
| `ε` (reduction leakage) | **2⁻⁴⁰** | line 14220 (δ′≈1) | the rejection-sampling tolerance; informs the Gaussian width margin |
| Gaussian width `s` | `s ≈ ω(log₂n)·n·η·√(2d)` | line 5652 | `sep_sig::COMMIT_SIGMA_FACTOR·gadget_sigma` + `s2` — **set to the §6.4 closed form, not `=1.0`** |
| M-SIS forgery bound | `β❶ = (B1+ndB2)² + B3² + nm + 1` | Thm 6.3 (line 14195) | drives the `b`→165-core-SVP check; `B1,B2` from Lemma 1.26, `B3` the tag part |
| OblSign bound bump | `‖v1‖₂ ≤ B1 + ‖ru‖₂`, `‖ru‖ ≤ √(2n)` (binary) | line 13959-13964 | `sep_sig` `b1_sq` for the issuance path = `(√B1 + √(2n))²` ✅ matches our `v=v'−[ru;0]` algebra |

### The SEP modulus — ALREADY CORRECT (corrected 2026-06-26; the earlier "research-wall" framing was an error)
SEP⋆ needs a modulus with **controlled splitting** for the tag arithmetic (thesis §6.2.2 / Lemma 1.4): a
prime with `p ≡ 5 mod 8` so the 2-Sylow of `Z_p^×` has order 4 — `i = √−1` exists but no primitive 8th
root, so `X²⁵⁶+1 = (X¹²⁸−i)(X¹²⁸+i)` splits into **exactly two** degree-128 irreducibles (κ=2). That makes
every tag AND every difference of distinct tags a **unit** (the unforgeability foundation — no two sigs
share a tag, matrices differ by an invertible).

**The SEP credential ring ALREADY uses this:** `sep_ring::P = 425837` (prime, `425837 ≡ 5 mod 8`, κ=2 —
`sep_ring.rs:21` / line 342), and `sep_tag::tag_differences_are_units` **already verifies** distinct-tag
differences invert. So there is **no modulus flip** and **no NTT-table regen** for the credential — it is
done. (My earlier note conflated two distinct rings: the `q = 8380417` full-split modulus is the SEPARATE
**proof ring** `proof_ring` for the LNP22 NTT arithmetic, where full splitting is *fine* — only the SEP
*credential* needs limited splitting, which `sep_ring` provides.) `p = 425837 ≈ 2^18.7` also sits squarely
in the thesis's calibrated SEP⋆ modulus regime (Table 3.2 q ≈ 2^17.6–20.8), consistent with d=4. The
`reference_ring_perturbation_wall` memo is about the *ring SamplePre perturbation sampler* (Genise–
Micciancio), a separate efficiency item — NOT the modulus.

So the actual remaining SEP-side work is **verifying** the M-SIS core-SVP at (n=256, p=425837, d=4, β❶)
hits ≥165 (the calc below), and pinning the bounds/width to the §6.4 closed forms — no modulus surgery.

## 3. The composition instances (same target, derived not transcribed)

These are OUR composition (not in the base thesis), so they're derived against the §1 cost model at the
same 165/128 target. Each is a separate calc to lock next, in this order (cheapest blocker first):

1. **`abdlop` (commitment) M-LWE hiding + M-SIS binding** — dims `(d, m1, m2, ℓ)` + `ABDLOP_SHORT_BOUND`.
   The commitment randomness `s2` is M-LWE-hidden; binding is M-SIS on the commitment matrix. Set `(d,m2)`
   so both ≥ target at our `q̂` (`proof_ring::QHAT`). Currently provisional (abdlop.rs:13-25).
2. **`bdlop` (garbage commitment)** — `(n,k,ℓ, short bound)`, same method (bdlop.rs:19-30).
3. **Nullifier ring-LWR Δ** (`nullifier_lwr.rs:23`) — Δ must drop enough low bits for ring-LWR hiding at λ;
   `Δ=p≈2^18.7` provisional. Calc the bit-drop vs the λ target.
4. **`bind`/sis_pok `M`, `DIGITS`** (bind.rs:63) — `M=512`, `DIGITS=32` provisional; raise `M` for a
   full-width identity + the commitment-hiding entropy margin.
5. **Approx-range / show σ (`SHOW_SIGMA3`, `SEP_MASK_SIGMA`)** — the rejection-sampling widths; set to the
   thesis Ch7 [LNP22] values once the base `q`/dims are locked (they scale with them).

## 4. Execution order (constant-flips, each its own gate-clean commit)

1. ~~**SEP modulus**~~ — **DONE / no-op.** `sep_ring::P = 425837` (p≡5 mod 8, κ=2) is already the
   splitting-compatible SEP modulus; `tag_differences_are_units` verifies it. No flip, no NTT regen. (§2.)
2. **SEP dims** — ✅ DONE (commit 44b034b): `keygen(d=4, m1=2d=8)` production-size `#[ignore]` smoke proving
   sign→verify + OblSign round-trip hold at the calibrated module rank. (`k` = gadget `KG`, q-derived.)
3. **SEP M-SIS bit-security** — ✅ **VERIFIED BY TRANSCRIPTION (no re-derivation).** Our credential params
   `(n=256, p=425837, d=4)` ARE the thesis's calibrated SEP⋆ set: `p=425837 ≈ 2^18.7` is the thesis's own
   modulus (thesis L15529 / L18551 — its smallest modulus factor, κ=2); `d=4` is L14218; the target is
   ~165-bit M-SIS core-SVP (L13944), and the thesis reports its achieved hardness as **181 classical / 165
   quantum** core-SVP (L12287). The thesis *did* the δ₀→b core-SVP calc for this exact set — so transcribing
   its params transcribes its security. This is rule-compliant (faithful transcription of the audited
   reference) and avoids an error-prone hand re-derivation. **Residual on the SEP side:** pin `B1`/`B2`/`B3`/
   `s` to the §6.4 closed forms (Lemma 1.26 + the §6.4.1 width) so the *bounds* match the thesis's β❶ that
   the 181/165 assumes (the current bounds are provisional; honest issuance always verifies because sign
   reject-resamples, but they must equal the thesis values for the 181/165 to apply). This is a closed-form
   transcription, not a re-derivation.
4. **Composition instances** (§3) — these ARE our own composition (abdlop/bdlop garbage commitments, the
   nullifier ring-LWR), NOT in the base thesis, so they DO need the δ₀→b→0.2924b ≥165 calc per instance,
   shown step-by-step in the doc comment so Opus + Codex can check the arithmetic. They live over the PROOF
   ring (`proof_ring`, the multi-factor modulus whose smallest factor is 425837 — thesis Ch7 [LNP22]); the
   thesis's Ch7 proof-system param table (L18540+: qmin/qb/ℓ=7 soundness dim) is the transcription anchor
   for the show side, leaving only the abdlop/bdlop/nullifier composition widths as genuine new calcs.
5. **Drop `experimental-unaudited`** once (3)'s bounds are pinned and (4)'s instances are ≥ target +
   Codex-reviewed — the flag that flips the C3 vouch from "classically sound, PQ-provisional" to
   "PQ-sound (us+Codex)". HYP-343 (retire `StubVouchScheme`) unblocks here.

## 5. The calibration crux — LOCATED (2026-06-26): the sampler width, not a bound

The provisional-bound trail bottoms out at **one security-limiting line**, now identified by reading the
code + the thesis side by side:

**`sep_trapdoor.rs:252` — `let s = alpha * (r_fro_sq.sqrt() + 2.0);`** — the elliptic-sampler preimage
width uses the **Frobenius** norm `‖R‖_Fro` of the trapdoor. The thesis's Alg 4.5 sampler is parameterised
by the **spectral** norm `s₁(M_τ(R))`, bounded by **Heuristic 1.1** (thesis p.53):
`s₁(M_τ(R)) ≤ √(nk) + √(nd) + t`, with `t` s.t. `2n·e^(−πt²) ≤ 2^(−λ)`. For λ=128, n=256:
`2·256·e^(−πt²) ≤ 2^(−128)` ⇒ `e^(−πt²) ≤ 2^(−137)` ⇒ `t² ≥ 137·ln2/π ≈ 30.2` ⇒ **t ≈ 5.5**.

The gap, at (m1=8, dk=76, N=256): Frobenius `√(m1·dk·N) ≈ 394` worst-case (`~322` typical) vs spectral
`√(N·m1)+√(N·dk)+t ≈ 45.25 + 139.48 + 5.5 ≈ 190`. **The sampler runs ≈1.7–2× wider than the thesis's
Alg 4.5**, so the credential is ≈2× larger and the realised M-SIS β is ≈2× the thesis's → the security sits
**below** the 181/165 the credential params (n=256, p=425837, d=4) are entitled to. The verification bounds
(`sep_sig.rs:195-199`, `s_pre = α·(Frobenius+2)`, `L2_TAIL = 1.2`) inherit this width and add a loose tail
(Lemma 1.26 gives the smallest valid `c ≈ 0.49` for these dims at λ=128, not 1.2).

**Why the fix is test-checked, not free-handed (the key realisation):** the Schur-complement elliptic
sampler (Alg 4.5) produces the correct `D_{Λ,s}` for **any** `s` whose perturbation
`Σ₁ = s²·I − α²·[R;I][R;I]ᵀ` stays PSD (`cholesky(Σ₁)` succeeds — `sep_trapdoor.rs:306`), with the gadget
smoothing handled separately by `α` (`SIGMA_FACTOR=5.0`, unchanged). Heuristic 1.1 guarantees
`s₁ ≤ spectral` w.h.p., so tightening `s` to `α·spectral` keeps Σ₁ PSD. **Cholesky-success ⇒ correct
distribution; Cholesky-failure ⇒ a caught panic — there is no silent wrong-distribution path.** Plus the
d=4 smoke (`production_size_…`) re-verifies honest sigs against the tightened bounds. So this is a
test-validated change, not the uncatchable-insecurity class.

### 5a. LANDED (commit 26e9c3d, Codex-clean): the sampler-width swap

`sep_trapdoor.rs` + `sep_sig.rs` now use `s₁_bound = √(N·m1)+√(N·dk)+T_SPECTRAL` (T=5.5) for both the
sampler width and the matching acceptance bound, replacing the Frobenius norm. **Validated:** 48 fast sep
tests (Cholesky PSD + honest-verify at d=1), the d=4 production smoke (52s), full 373-test suite, clippy
clean. **Codex gate independently confirmed it** by computing the actual `s₁(M_τ(R))` over 200 random d=4
keys: max 161.1 vs bound 190.2, **0/200 over-bound** (+ 0 fails across four other shapes) — the Heuristic
1.1 bound holds empirically with margin. This is the dominant ≈2× gain; the credential now runs at the
thesis's Alg 4.5 width.

**CONFIRMED thesis-faithful (not just test-passing):** thesis L12973 gives its sampler width literally as
`s ← s_G·(√(nm1) + √(ndk) + t) + 1` — exactly our new structure `α·(√(N·m1)+√(N·dk)+t)+2` (`s_G`=our `α`;
the `+2` margin is marginally more conservative than the thesis's `+1`). L9587 confirms `‖R‖₂ ≤
√(nm1)+√(ndk)+t` is the thesis's own spectral bound, and L8544 gives `A_T ∈ R_q^{d×(m1+kd)}` (gadget block
width `kd = k·d`). The Frobenius form we replaced was never the thesis's; the spectral form matches it
line-for-line.

### 5b. FINDING (2026-06-26): the L2_TAIL is NOT the bare Lemma 1.26 minimum

Attempted `L2_TAIL 1.2 → the per-dimension Lemma-1.26 minimum c` (≈0.58 at d=1 v1). **The d=1
`sign_verifies` test FAILED** — honest sigs no longer fit. Reason: Lemma 1.26's `c` is the tail of a
*clean* width-`s₁` discrete Gaussian over the full lattice, but the verification checks `‖v1‖`/`‖v2‖`
*separately*, and these sub-vectors are **marginals** of the SamplePre output — they run wider than
`s₁·√dim` predicts (the gadget block `v2` especially). So the bound tail is NOT the bare Lemma 1.26 min;
it's the thesis's **Thm 6.3 SamplePre-output** bound, which is larger. The empirical `1.2` absorbs this and
is correct-and-conservative; the true thesis `c` lies in `(0.58, 1.2)`. **Reverted** to `1.2` (the test
caught the over-tightening — the rule-1 safety net working as designed; the validated 5a change stands).

The L2_TAIL exact-match is therefore a **measure-then-pin** follow-up, not a transcription: instrument the
d=4 smoke to record `max ‖v1‖/(s₁√(m1·N))` and `max ‖v2‖/(s_pre√(dk·N))` over many sigs, then set each
per-part tail just above the observed max with a `2^(−λ)` margin (or pull the exact Thm 6.3 closed form).
Until then `1.2` is conservative ⇒ β slightly above the thesis's ⇒ security slightly *under* the exact
181/165 *from the tail alone* — but the dominant width gain (5a) is landed, so the residual tail gap is
small.

### 5c. FINDING (2026-06-26): the gadget BASE differs (k=19 base-2 vs thesis k=5 base-16) — 181/165 is NOT inherited

Running the β-clears-165 check surfaced a second, more important mismatch. Thesis Thm 6.3 (L14191/L14218)
sets the forgery hardness as `M-SIS_{n,d,2d+k+m+1,q,β❶}` with `β❶ = √((B1+ndB2)² + B3² + nm + 1)`, and the
thesis's SEP⋆ 128-bit set uses **k=5** (L14218: λ=128, n=256, d=4, **k=5**, Q=2³²). Our `sep_gadget`
uses a **base-2** gadget, `KG = ⌈log₂ p⌉ = 19` (`g=(1,2,…,2¹⁸)`); the thesis's `k=5 = ⌈log₁₆ p⌉` is a
**base-16** gadget. The gadget base differs ⇒ the M-SIS *width* (`2d+k+m+1`) and the gadget width `α`
differ ⇒ **our k=19 credential does NOT inherit the thesis's 181/165 core-SVP** — my earlier "params match
⇒ security inherited" (§4 step 3) was over-optimistic: it checked n, p, d but NOT the gadget base.

Base-2 is a deliberate, valid, gate-clean choice (Dilithium uses base-2; smaller per-digit `α`, more digits),
NOT a bug — but its security is a *different point* on the size/security curve and must be **computed at
k=19**, not borrowed. The sampler-width fix (5a) is unaffected (it tightened the width at whatever base);
only the *security-level claim* needs the actual core-SVP at the shipped (n=256, d=4, k=19, q=425837, β❶).

So the honest residual is a genuine **core-SVP computation** (not a transcription): assemble B1/B2/B3 at the
shipped params, form β❶, run the §9 core-SVP estimate (0.2924·b classical / 0.2570·b quantum, δ₀↔b via
Chen), and report the actual bits — then decide if base-2/k=19 clears the target or the gadget rebases to
k=5 to inherit 181/165 cleanly. This is Codex-verifiable arithmetic (Codex re-ran the `s₁` check the same
way), so it is checkable, not free-handed — but it IS the security-critical number, so it gets a careful pass.

**Remaining execution:** (a) compute the actual core-SVP at k=19 (above); (b) the L2_TAIL measure-then-pin;
(c) decide k=19-as-is vs rebase-to-k=5; (d) Codex-gate; (e) drop `experimental-unaudited`.

### 5d. CORRECTION (2026-06-26): the target is ~165 core-SVP, NOT "181/165" (that was Robin-1061)

While reading the thesis tables for the core-SVP anchor I caught a misattribution I'd propagated across
several commits + memory: **"181 classical / 165 quantum" is Robin-1061** (a hash-and-sign signature in the
**Ch5 Table 5.4 scheme comparison** — Mitaka/Eagle/Robin/Phoenix/Falcon, L12255-12289), **NOT the SEP⋆
credential.** The actual SEP⋆ (§6.4) target is **"around 165 bits of M-SIS core-SVP hardness"** (L13944, a
single core-SVP figure; §6.2's earlier variant used 213). So every prior "181/165" in this doc/commits/memory
should read **"~165 bits M-SIS core-SVP (§6.4 target, L13944)."** The 5a sampler-width fix is unaffected (it
was anchored to L12973/L9587, correctly SEP⋆ lines); only the *target figure* citation was wrong.

**Why this matters beyond the typo:** this is the THIRD correction this session that surfaced only by
verifying rather than asserting (modulus-wall illusory → gadget-base k=19≠5 → 181/165=Robin). The latest is
a *misattributed security number*. That is direct evidence that at this depth I am making security-figure
attribution errors — which is precisely why the remaining **core-SVP computation** (estimator + exact β❶ + W
disambiguation, all feeding one security claim) must be done at a state where such errors aren't happening,
and validated against the now-correct ~165 §6.4 anchor + a published M-SIS point. Computing it now would risk
compounding exactly the class of error I just caught. This is evidence-based, not a context excuse: a wrong
core-SVP number is a false security claim, the one outcome worse than "computed next, verified."

### 5e. RED FLAG (2026-06-26): code-extracted β❶ ≫ q — the reduction may be vacuous at p=425837

Extracting the GROUND-TRUTH bounds from the code (`print_d4_msis_beta_for_coresvp`, d=4) gave: `α=11.18`,
`B1=1.17e5`, `B2=3.60e5`, modulus `q=425837`. Two alarms:

- **`B2/q = 0.845`** — the per-signature ℓ₂ verification bound on `v2` is **85% of the modulus**. A
  well-calibrated SIS signature is *short* (`B ≪ q`, typically `B/q ~ 0.01–0.1`); `0.85` is barely-short.
- **`β❶ ≈ B1 + nd·B2 = 3.69e8`, i.e. `β❶/q ≈ 865`** (`nd = n·d = 1024`). The M-SIS *forgery* target is
  865× the modulus ⇒ trivially solvable (`(q,0,…)` is a solution) ⇒ **the unforgeability reduction
  `M-SIS_{…,q,β❶}` is vacuous** at these params.

This is EITHER a real, serious problem — **the credential modulus `p=425837` is too small** (which would
*contradict* §2's "modulus is already correct" note: 425837 is the thesis's *proof-system* `qmin` (L18551),
and I may have wrongly adopted it as the *credential* modulus, which the thesis sets larger so that `β❶<q`)
— OR my forgery-amplification model is wrong (`nd=1024` may overstate it; the tag-difference operator norm
could be `~√(w·n)` not `n·d`; or the forgery M-SIS is over a different/larger modulus). **I cannot
confidently distinguish these right now**, and this session has already produced THREE security-relevant
corrections (modulus-wall, gadget-base, 181/165=Robin), at least one of which (§2) this finding may now
overturn. Reporting a core-SVP "≥165" or "<165" on top of an unresolved `β❶≫q` would be a fabricated
verdict about a *possible real vulnerability*.

**This BLOCKS the security claim — correctly.** The `experimental-unaudited` flag must stay; the credential
is NOT verified secure and may have a too-small modulus. Resolution (careful, rigorous, fresh): (i) pin the
exact `nd` forgery amplification from the thesis Thm 6.3 proof (operator norm of tag-difference mult);
(ii) determine the thesis's actual *credential* modulus vs proof `qmin=425837`; (iii) if the modulus is too
small, raise it (a structural change: new NTT/gadget tables, re-gate the whole stack) — NOT a tail
refinement. Until then no core-SVP number is meaningful. **The 5a sampler-width fix still stands** (it is the
thesis's width formula regardless of modulus); but the security *level* is now openly unresolved, which is
the honest state — better than the false "181/165 inherited" it replaces.

Until (1)–(5) + §5 land, the lattice half stays gated; the BBS half remains real BLS12-381. HYP-343 (trait
reshape, retire `StubVouchScheme`) unblocks at the end of (5) — it was only ever gated on "real params."

---

## §6. RESOLVED via the official reference implementation (2026-06-27) — supersedes §5e's modulus hypothesis

The whole hand-calc chain above (§5a–5e) is **retired** in favour of porting the **official reference
implementation** of the construction — `github.com/Chair-for-Security-Engineering/lattice-anonymous-credentials`
(the C code for ePrint 2024/131, "Practical Post-Quantum Signatures for Privacy", CCS 2024). Reading its
`code/include/params.h` against our code resolves every open question and **withdraws §5e's "modulus may be
too small" hypothesis**:

- **The modulus is FINE.** `q = 425801` is the SEP credential modulus; the *proof* modulus is `q·q1 =
  425801·524201 ≈ 2³⁷·⁷` (ref `PARAM_Q_ISS`/`PARAM_Q1_ISS`). `425837` was never the right value — our
  hand-built ring drifted.
- **The real cause of `β❶ ≫ q` is parameter DRIFT, not a vulnerability.** Our SEP⋆ ran at non-validated
  params end-to-end: `q=425837` (κ=2) vs ref `425801` (κ=4, q≡1 mod 8, factors of degree 64); gadget base-2
  `k=19` vs ref **base-14 `k=5`**; a **spherical** sampler vs the ref **elliptic** one (`s1≈5854` wide /
  `s2≈68.17` narrow); `m=2,w=31` vs ref `m=10,w=5`. The reference `B2 = √4886925 ≈ 2211` is SHORT (~0.5% of
  q); ours was `~0.85q`, because our spherical sampler made `v2` ~130–160× too wide.
- **`nd` is moot.** No hand "core-SVP" calc is needed — security comes from the reference's `scripts/` +
  `lattice-estimator`.

**The fix = a coherent port of the SEP⋆ core to the reference (HYP-354):** `sep_params` ✅ (chunk 1, the
validated constant set, committed `cff50ef`/`f44dc48`) → `sep_ring` (q=425801) → `sep_gadget` (base-14 k=5)
→ `sep_tag` (w=5, κ=4) → `sep_trapdoor` (elliptic sampler — a spherical→elliptic modification of our existing
Schur-complement Cholesky, NOT a from-scratch FFT) → `sep_sig` (B1/B2/B3, m=10), validated against the
reference. The params are coupled, so this is one focused reimplementation, not independently-gateable chunks.
Full state on HYP-354.

---
*Historical note: §1–§5e are the hand-derivation that the reference port replaces. They are kept for the
audit trail of how the red flag was found and why the reference route was chosen; §6 is the operative plan.*
