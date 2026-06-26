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
3. **SEP M-SIS bit-security check + Gaussian width/bounds** — the δ₀→b→0.2924b ≥165 calc at
   (n=256, p=425837, d=4, β❶), shown step-by-step; then `s`, `B1`, `B2`, `B3` to the §6.4 closed forms +
   the OblSign `+‖ru‖` bump. **This is the next concrete step — now unblocked (no modulus surgery).**
4. **Composition instances** (§3, in the listed order), each with its δ₀→b→0.2924b ≥165 calc *in the doc
   comment* so Codex + a future reader can check the arithmetic.
5. **Drop `experimental-unaudited`** once every instance is ≥ target and the analysis is Codex-reviewed —
   this is the flag that flips the C3 vouch from "classically sound, PQ-provisional" to "PQ-sound (us+Codex)".

Until (1)–(5) land, the lattice half stays gated; the BBS half remains real BLS12-381. HYP-343 (trait
reshape, retire `StubVouchScheme`) unblocks at the end of (5) — it was only ever gated on "real params."

---
*Calibration anchors are exact thesis transcriptions (lines cited). The composition derivations (§3) are the
by-hand core-SVP calcs to perform per the §1 model — the security-critical numeric work, to be shown step-by-
step in each commit so the arithmetic is auditable by Opus + Codex (the only reviewers).*
