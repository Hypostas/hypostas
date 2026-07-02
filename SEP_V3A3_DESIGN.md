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

## 2. The construction (from ePrint 2024/131 — the ACTUAL scheme, Alg lines 1968/1995/2006)

> **CORRECTION (found by reading the real algorithms, not the §5 intro):** in the SCHEME, `A3` is a
> **uniformly random `d×k` matrix** — `A3 ← U(R_q^{d×k})`, Setup line 1968, "A3 is a d×k random matrix"
> line 1907. It has **no trapdoor and no tag**. The `t_{d+1}G − A·R_{d+1}` form (line 1700) is the
> SECURITY PROOF's hybrid ONLY (the "partial-trapdoor switching", td+1=1, lines 1811–1835) — `R_{d+1}`
> does NOT exist in the scheme. This is much simpler than the proof form: keygen just samples one more
> random public matrix.

```
A3 ← U(R_q^{d×k})                 // a random d×k public matrix, part of pp (NO trapdoor, NO tag)
A_T = [ A | tG − B | A3 ]         // was [A | tG − B]; B = A·R as today
v   = [ v1 ; v2 ; v3 ]            // v3 ∈ R^k is the new short component; A3·v3 ∈ R^d
```

**Sign** (ref Alg line 1995 — `v3` sampled FIRST, syndrome adjusted, then `SamplePre` for `(v1,v2)`):
```
v3 ← D_{R^k, s2}                                   // fresh narrow Gaussian, width S2 (=68.17)
syn = u + D_s·s + D·m − A3·v3   (mod qR)
(v1, v2) ← SamplePre(R, A′, syn, t, s1, s2, sG)    // existing elliptic sampler, UNCHANGED
sig = (tag t, v1, v2, v3)
```

**Verify** (ref Alg line 2006/2040 — reconstruct `v1,1` from the relation, then bound-check):
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
| `sep_sig` keygen | sample `A3 ← U(R_q^{d×k})` (NUMS/rng), store in `SepSigKey`/`SepVerifyKey` + `pp`. **No trapdoor change** — `sep_trapdoor` is untouched. |
| `sep_sig::sign` | sample `v3 ← D_{R^k,s2}`; subtract `A3·v3` from the syndrome before `SamplePre`; add `v3` to `SepSignature` |
| `sep_sig::verify` | include `A3·v3` in the relation check; verify `‖v3‖₂² ≤ B3_SQ` |
| `proof_show` (LNP22) | prove the `v3` leg — `v3` becomes part of the committed witness `s1`, with the `A3·v3` term in the opening relation + its `b3`/norm coverage |
| `codec` | serialize `v3` (and `A3` in the key codec) ; version bump |

## 4. Open questions for impl (resolve against §5/§6 + code/src before/while chunking)

1. ~~Tag on A3~~ — **RESOLVED**: the scheme's `A3` is random, **no tag** (line 1968). The `t_{d+1}`
   form is proof-only.
2. **Does `A3·v3` enter the SHOW's exact-norm/quadratic legs**, or only the linear opening? (Affects
   `proof_show` witness layout + whether `v3` widens the approx-range dim.) Read the show's current
   `s1` packing; `v3` is `s2`-short so it joins the norm-proof witness like `v2`.
3. ~~R_{d+1} distribution~~ — **DISSOLVED**: no `R_{d+1}` in the scheme (proof-only artifact); `A3` is
   uniformly random.
4. ~~β❶ recomputation~~ — **RESOLVED**: the forgery M-SIS bound at `sep_sig.rs:1155`
   (`d4_forgery_bound_beta1_below_modulus`) **already includes the `B3` leg** (`+ b3*b3`, `b3 = √B3_SQ`).
   Verified numerically 2026-07-01: `B3 = 1242.7`, `β❶ = 199508.6`, `β❶/q = 0.4685 < 1`. The leg's
   soundness is therefore pre-validated — adding `v3` does NOT push β❶ over the modulus. So chunk 5.3 is
   already satisfied by the shipped test (it was written B3-inclusive in the HYP-354 resolution / FU4).

## 5. Chunk plan (each Codex-gate-clean, rule #27 smoke+integration)

- **5.0 (this doc)** — DESIGN + Codex DESIGN-review.
- **5.1** — `sep_sig` keygen: sample `A3 ← U(R_q^{d×k})` into the signing/verify keys + `pp`; unit test the `d×k` shape + determinism from the NUMS seed. (No `sep_trapdoor` change — A3 is trapdoor-free.)
- **5.2** — `sep_sig` sign/verify: `v3 ← D_{R^k,s2}` sample + syndrome-adjust (`− A3·v3`) + the `A3·v3` relation leg + `‖v3‖²≤B3_SQ`. Round-trip test (honest sig verifies; tampered `v3` / over-`B3` `v3` reject). 5.1+5.2 may land together since A3 is simple.
- **5.3** — ✅ **DONE** (already shipped): β❶ with the `B3` leg is verified in
  `sep_sig.rs::d4_forgery_bound_beta1_below_modulus` (β❶/q = 0.4685 < 1, B3-inclusive). No new work — the
  test was written B3-inclusive in the HYP-354 resolution.
- **5.4** — `proof_show`: the `v3` leg in the committed witness + opening relation; the show still verifies end-to-end.
- **5.5** — codec (v3 + A3 serialization + version bump) + the pq_vouch/issuance integration + full gate.

## 5b. Impl map — blast radius + mechanical plan (derived 2026-07-01, rule #6 read-through)

Read the full show machinery (`proof_show.rs` §41–443, the witness layout + relation + carry). The v3 leg
is a **coupled** change (sig + show move together — appending `v3` to `sig.v` changes
`ShowWitness::from_signature`'s length check, the packed `s1` layout, `carry_block_offset`, and the LHS at
once). But it is **bounded and mostly mechanical** — the intricate parts adapt automatically:

- **Carry-lift `z = (lhs−rhs)/p` is computed FROM the blocks** (`compute_carry` in `pack_witness_with_carry`),
  not hand-derived. Once `sep_lhs_from_blocks` gains the `+ A3·v3` term, `z` absorbs it automatically.
- **The quadratic part `tag·(G·v2)` is UNTOUCHED** — `v3` has no bilinear term, so `sep_bilinear` and the
  garbage/quadratic proofs keep their structure; only the LINEAR part gains `A3·v3`.
- **`v3` is `s2`-short (like `v2`)** ⇒ `‖v3‖∞ ≤ witness_inf_bound` already, so the range/approx-range norm
  proofs cover it with NO change (confirmed: `proof_range/quadratic/challenge/approx_range` have **0**
  layout-offset sites — they operate on the generic `s1`/norm, not the SEP block layout).

**Blast radius (grep 2026-07-01):** `proof_show.rs` (140 sites — the core), `proof_agg_show.rs` (10),
`pq_vouch.rs` (9), `codec.rs` (3), `proof_garbage.rs` (2), `blind_issuance.rs` (2), `scheme.rs` (1). Five
files of real work, concentrated in `proof_show.rs`.

**Layout decision:** append `v3` to `sig.v` so `v = [v1(m1); v2(d·KG); v3(K)]` stays ONE vector
(`SepSignature` shape unchanged: `(tag, v)`, `v` just longer). Show witness block layout becomes
`[v1 | v2 | v3 | m | tag | z]` — `v3` (K blocks) inserts after `v2`, shifting `m`/`tag`/`z` by `K`.

**Mechanical touch-list (in order):**
1. `sep_sig.rs`: `SepSigKey.a3` + `SepVerifyKey.a3` (`d×K` random); `keygen` samples `A3 ← U(R_q^{d×K})`;
   `sign` samples `v3 ← D_{R^K,s2}`, sets `syn = u + D_s·s + D·m − A3·v3`, appends `v3` to `v`; `verify`
   adds `A3·v3` to the LHS + checks `‖v3‖²≤B3_SQ`. (`sep_trapdoor` UNCHANGED.)
2. `proof_show.rs`: `ShowWitness.v3`; `from_signature` (`expected_v += K`, split `v3=v[m1+dk..]`);
   `pack_witness`/`unpack_witness` (chain `v3` after `v2`); `carry_block_offset += K`;
   `expected_sep_s1_len += K`; `sep_lhs_over_proof_ring` + `sep_lhs_from_blocks` + `sep_linear` gain the
   `A3·v3` term (v3 blocks at `[m1+dk, m1+dk+K)`); shift `m`/`tag`/`z` offsets by `K`. Add `vk.a3()`.
3. `proof_agg_show.rs` (10 sites): follow the shifted layout.
4. `codec.rs`: serialize `A3` in the key codec (v3 rides `sig.v` automatically) + wire-version bump.
5. `pq_vouch.rs`/`blind_issuance.rs`/`scheme.rs`: thread `A3` through key construction; recheck the 9+2+1
   layout sites.

**Tests (rule #27):** SEP round-trip (honest verifies; tampered/over-B3 `v3` rejects); the ZK show still
proves+verifies end-to-end (`sep_relation_holds_over_proof_ring` + a full `prove_show`/`verify_show`
round-trip); `expected_sep_s1_len`/`carry_block_offset` consistency test. Then Codex-gate.

**Sequencing note (2026-07-01):** design + Codex DESIGN-review + soundness-validation (5.3, β❶<q with B3)
are COMPLETE. The impl above is a bounded-but-deep change to the `[LNP22]` witness layout — the crate's
most soundness-sensitive machinery. Per rules #1/#6 ("never self-certify soundness / never rush crypto
understanding") it is sequenced for focused execution rather than a session-tail build; it is Medium-priority
reference-fidelity (the shipped simplified SEP is already sound, β❶<q) behind `experimental-unaudited`
(HYP-330-gated regardless), so sequencing costs nothing on the critical path. The map above makes the build
turn-key.

## 5c. The blind-issuance (OblSign) v3 path — design (2026-07-02, the previously-undesigned piece)

§2 designed the DIRECT `sign` leg. The credential is ALSO minted via blind issuance (`oblivious_sign` /
`oblivious_sign_checked`), and blind creds must carry a proper `v3` — else blind-vs-direct creds are
distinguishable (a `v3=0` blind cred is not reference-faithful and leaks the issuance path). Reading the
blind flow (`sep_sig.rs:332` `oblivious_sign`, `:369` `oblivious_sign_checked`, and the user's
`prove_request`/`verify_request` in `proof_show`) settles who samples `v3` and where it folds.

**DECISION — the USER samples `v3` and folds `−A3·v3` into the commitment `c_u`.** So the credential
relation `A_t·[v1;v2] + A3·v3 = u + D_s·s + D·m` holds after unblinding, with `v3` entirely user-side:

```
User:   v3 ← D_{R^K, s2};   c_u = A·ru + D_s·s + D·m − A3·v3   (was: A·ru + D_s·s + D·m)
Issuer: syndrome = u + c_u;  v_blinded = SamplePre(t, u + c_u)          ← UNCHANGED (`oblivious_sign` code untouched)
User:   v = v_blinded − [ru;0];  credential = (t, [v1;v2;v3])           ← append the user's own v3
```

Verify: `A_t·v = u + c_u − A·ru = u + D_s·s + D·m − A3·v3`, so `A_t·[v1;v2] + A3·v3 = u + D_s·s + D·m`. ✅

**Why user-side (not issuer-sampled):** `v3` is the user's secret-adjacent randomness like `ru` — the
issuer NEVER sees it, so it cannot become an issuance→show linkage. (Even issuer-sampled `v3` would be
hidden by the ZK show, but user-side is strictly safer + symmetric with `ru`/`s`/`m`.) **Everlasting
anonymity (BBS half) is untouched** — `v3` is entirely lattice-side and independent of `[s|m]`.

**Coupling consequence (a SIMPLIFICATION):** the **issuer's `oblivious_sign` needs NO change** — it
consumes `c_u` opaquely. The blind-path change is entirely USER-side:
- `prove_request` (the user builds `c_u` incl. `−A3·v3`) + the well-formedness proof `π` must now ALSO
  prove `‖v3‖²≤B3_SQ` AND that `−A3·v3` is the folded term (a linear relation on the committed `v3`).
- `verify_request` (the issuer's Model-B check) must verify that extended `π`.
- the user's unblind appends `v3` to `v`.

So the atomic unit is: `sep_sig` (keygen A3 + direct sign/verify + the `‖v3‖≤B3` check) + `proof_show`
(the show witness `v3` **and** the request-π `v3` leg + `verify_request`) + `codec` + `pq_vouch`/`scheme`
key threading. `oblivious_sign` itself is untouched — smaller blast radius than §5b feared.

**Open Q (resolve in impl):** does `prove_request`'s existing binariness/`upk`-binding π already carry a
short-witness slot the `v3` norm proof can reuse, or does `v3` widen the request-π approx-range dim? Read
`proof_show::prove_request`'s witness packing (same `s1`-layout question as the show, §5b Q2).

## 6. Risk

Soundness-critical (the credential). Mitigations: design-first (this doc) → Codex DESIGN-review → chunked
impl, each chunk Codex `exec review`-gated + round-trip/integration tested; the elliptic `SamplePre` is
UNCHANGED (only the syndrome fed to it changes), so the validated sampler (thesis Alg 4.5) is untouched.
Behind `experimental-unaudited` throughout; the precise β❶/core-SVP re-check remains HYP-330.
