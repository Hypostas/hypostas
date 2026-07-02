# SEP* v3/A3 partial-trapdoor leg — design (HYP-355)

**Status:** DESIGN (design-first, pre-impl). Reference fetched + construction locked; awaiting Codex DESIGN-review, then chunked impl.
**Issue:** HYP-355 (child of HYP-352 / HYP-354 follow-up FU4).
**Reference:** Jeudy SEP, ePrint 2024/131 (`refs/jeudy_sep_eprint_2024_131.{pdf,txt}`, gitignored). Key lines: §1 line 251 (`A_T = [A|TG − AR]`), 283 (double-trapdoor intermediate `A_T = [A|TG−AR|G−AR']` of dim `2(d+k)`), **308 (the improvement: add a `d×k` matrix `A3` to `A_T` instead of `d×dk` `AR'`)**, 1700 (the exact Sign with `v3`), 1796 ([JRS23] baseline).

## 1. What & why

The shipped SEP signature (`vouch-crypto/src/sep_sig.rs`) uses the **simplified** tagged relation
`A_t·v = u + D_s·s + D·m` with `A_t = [A | tG − B]`, `v = [v1; v2]`. It is **sound** (β❶ < q holds,
`sep_sig.rs:1141` HYP-354 resolution) but is NOT the full ePrint-2024/131 construction: it omits the
`A3`/`v3` **partial-trapdoor** leg. HYP-355 wires that leg so the credential matches the reference's
security construction (the forgery reduces to M-SIS over the FULL `[A | tG−B | A3]`, β❶ gaining the small
`B3` term the module doc at `sep_sig.rs:24` already anticipates) and picks up the reference's size
optimization (`A3` is `d×k`, not the `d×dk` double-trapdoor `AR'`).

**Not a soundness fix** — a reference-fidelity / completeness upgrade. Priority Medium.

## 2. The construction (from ePrint 2024/131)

Extra public block, per §5 (line 308, 1700):

```
A3 = t_{d+1}·G − A·R_{d+1}        // d×k, a SECOND tagged gadget block using an extra
                                   // trapdoor column R_{d+1} (the "partial trapdoor")
A_T = [ A | tG − B | A3 ]         // was [A | tG − B]; B = A·R as today
v   = [ v1 ; v2 ; v3 ]            // v3 ∈ R^k is the new short component
```

**Sign** (ref line 1700 — `v3` sampled FIRST, syndrome adjusted, then `SamplePre` for `(v1,v2)`):
```
v3 ← D_{R^k, s2}                                   // fresh narrow Gaussian, width S2 (=68.17)
syn = u + D_s·s + D·m − A3·v3   (mod qR)
(v1, v2) ← SamplePre(R, A′, syn, t, s1, s2, sG)    // existing elliptic sampler, unchanged
sig = (tag t, v1, v2, v3)
```

**Verify:**
```
[A | tG − B | A3]·[v1; v2; v3] == u + D_s·s + D·m   (mod p)
‖v1‖₂² ≤ B1_SQ ,  ‖v2‖₂² ≤ B2_SQ ,  ‖v3‖₂² ≤ B3_SQ ,  t ∈ Tw
```

`B3` binds `v3` (narrow, `s2`-Gaussian over `R^k`): `B3 ≈ 1243` (`B3_SQ = 1_544_265`, already in
`sep_params`). `v3` uses the SAME `s2` as `v2` (ref: "for `v2`/`v3`", `sep_params.rs:65`).

## 3. What already exists vs. what to wire

**Already present (task #87 ported the params):** `sep_params::B3_SQ`, `K = 5` (= `k`, so `v3 ∈ R^k`),
`S2` (v3 width). The bound invariant `B1 > B2 ∧ B1 > B3` holds.

**To wire (the leg):**
| Component | Change |
|---|---|
| `sep_trapdoor` | produce the extra trapdoor column `R_{d+1}` (partial trapdoor) at keygen |
| `sep_sig` keygen | derive + store `A3 = t_{d+1}G − A·R_{d+1}` in `SepSigKey`/`SepVerifyKey` |
| `sep_sig::sign` | sample `v3 ← D_{R^k,s2}`; subtract `A3·v3` from the syndrome before `SamplePre`; add `v3` to `SepSignature` |
| `sep_sig::verify` | include `A3·v3` in the relation check; verify `‖v3‖₂² ≤ B3_SQ` |
| `proof_show` (LNP22) | prove the `v3` leg — `v3` becomes part of the committed witness `s1`, with the `A3·v3` term in the opening relation + its `b3`/norm coverage |
| `codec` | serialize `v3` in the SEP-signature bytes; version bump |

## 4. Open questions for impl (resolve against §5 + code/src before/while chunking)

1. **Tag on A3.** Ref uses `t_{d+1}` for the A3 block. Is it the SAME tag `t` as the main block, or a
   distinct component of a vector tag? (Line 1700 writes `t_{d+1} G_i` — the per-block tag index.) Read
   §4/§5 for whether our single-attribute case collapses `t_{d+1} = t`.
2. **Does `A3·v3` enter the SHOW's exact-norm/quadratic legs**, or only the linear opening? (Affects
   `proof_show` witness layout + whether `M_MSG`/`v3` widen the approx-range dim.)
3. **`R_{d+1}` distribution** — same `χ` (`sep_trapdoor`) as the base `R` columns? Confirm dims (`d×k`).
4. **β❶ recomputation** — add the `B3` leg to the forgery M-SIS norm in `sep_sig.rs:1141` and re-assert
   β❶ < q (it currently omits `B3`; the doc says B3 is "small", verify numerically).

## 5. Chunk plan (each Codex-gate-clean, rule #27 smoke+integration)

- **5.0 (this doc)** — DESIGN + Codex DESIGN-review.
- **5.1** — `sep_trapdoor`: `R_{d+1}` partial-trapdoor column + `A3` derivation; unit test the `d×k` shape + `A3 = t_{d+1}G − A·R_{d+1}`.
- **5.2** — `sep_sig` sign/verify: `v3` sample + syndrome-adjust + the `A3·v3` relation leg + `B3` check. Round-trip test (honest sig verifies; tampered `v3` / over-`B3` `v3` reject).
- **5.3** — β❶ recomputation with the `B3` leg; assert β❶ < q at production params.
- **5.4** — `proof_show`: the `v3` leg in the committed witness + opening relation; the show still verifies end-to-end.
- **5.5** — codec (v3 serialization + version bump) + the pq_vouch/issuance integration + full gate.

## 6. Risk

Soundness-critical (the credential). Mitigations: design-first (this doc) → Codex DESIGN-review → chunked
impl, each chunk Codex `exec review`-gated + round-trip/integration tested; the elliptic `SamplePre` is
UNCHANGED (only the syndrome fed to it changes), so the validated sampler (thesis Alg 4.5) is untouched.
Behind `experimental-unaudited` throughout; the precise β❶/core-SVP re-check remains HYP-330.
