# YPIR_PORT_DESIGN.md — sovereign pure-Rust YPIR for the single-server mailbox fallback (HYP-328b)

**Issue:** HYP-328b — the single-server PIR mailbox tier (`MailboxTier::LimitedSingleServer`, the
"Limited" rung of the privacy-status ladder). Assumption-free single-server PIR over a
Constellation-sized shard: the shard gives k-anonymity, the PIR gives cryptographic index-privacy
*within* the shard, rides `DhtMailboxCarrier`. Behind the existing `MailboxRetrieval` trait, beside
`xor_pir::TwoServerXorPir` (2-server foundation) and `MycoMailbox` (2-server scale-up).

**Decision (Josh, popup 2026-06-28): the FULL YPIR port**, not the simpler SimplePIR-first option.
Spec-literal (`MAILBOX_PIR.md` §4.2/§6 names YPIR/VIA), hint-free (zero offline communication).

**References (faithful transcription ONLY — never approximate crypto from memory):**
- `refs/ypir` — Menon–Wu YPIR, github.com/menonsamir/ypir. Paper: eprint 2024/270 (USENIX Sec 2024).
- `refs/spiral-rs` @ rev `6929441` — the RLWE/polynomial substrate YPIR builds on.
- ⚠️ **The reference requires AVX-512 (x86); this is ARM.** The reference will NOT run here — so we port
  the *algorithm* in **portable scalar Rust** and validate against the reference's *logic + test
  vectors transcribed by hand*, not by running it. Correctness first, optimization (SIMD) never (the
  edge target is phone-class anyway). The AVX kernels (`matmul`/`kernel`/`convolution`/`transpose`/
  `packing`) are REPLACED by portable scalar, not ported.

**Process:** design-first → Codex DESIGN-review → port chunk-by-chunk bottom-up, each gated
(clippy + test + a transcribed reference vector). Nothing here is built yet. This is a multi-session
port on the scale of the Myco port + the lattice work.

---

## 0. The construction (YPIR+SP, faithful to the refs)

The mailbox stores fixed-width sealed cells (`MESSAGE_SIZE`-class, > 8 bits), so the relevant variant is
**YPIR+SP** (`scheme.rs::run_simple_ypir_on_params`), not standard YPIR (1–8-bit items). The DB is a
matrix of plaintext coefficients `T = u16 (mod pt_modulus)`, `db_rows_padded × db_cols`. Retrieval of
item `(target_row, target_col)` is two dimensions:

1. **First dimension — SimplePIR/LWE row-select (the portable scan).** The client LWE-encrypts (mod
   `2^32`, `lwe.rs`) an indicator vector for `target_row`; the server computes the matrix–vector product
   `DBᵀ · query` over the whole DB (the linear scan — `O(N)`, the memory-bandwidth-bound step the
   reference does in AVX, **we do portable scalar**). Result: one LWE-encrypted column of `db_cols`
   coefficients.
2. **Second dimension — RLWE packing + silent preprocessing (the spiral-rs-heavy step).** The server
   packs the LWE column into RLWE ciphertexts using the client's **expansion / key-switching public
   params** (`raw_generate_expansion_params` + `condense_matrix` — Regev/GSW-style key-switching over the
   polynomial ring, gadget-decomposed, NTT-multiplied), then **modulus-switches** (`modulus_switch.rs`)
   to compress. The **offline precomputation** (`perform_offline_precomputation_simplepir`) is what makes
   it *silent* — zero client hint download (YPIR's whole advantage over SimplePIR). The client decodes
   the RLWE response with its secret key to recover `target_col`'s coefficient.

**Index privacy** = LWE/RLWE semantic security: the query (the LWE row indicator + the RLWE expansion
params) is computationally independent of `(target_row, target_col)`, so a single — even fully malicious
— server learns nothing beyond "an oblivious read occurred" (`MAILBOX_PIR.md` §6: no trust assumption).
This is exactly the `MailboxRetrieval` contract ("server view identically distributed for `i ≠ j`").

---

## 1. The sovereign port scope

Two layers to port + one to replace.

### 1a. spiral-rs RLWE substrate (~3,150 LoC ref; port only what YPIR uses)
Bottom-up — each its own gated chunk, validated against transcribed reference vectors:
| Module | ref LoC | What | Portability note |
|---|---|---|---|
| `number_theory` | 96 | primes, 2n-th roots of unity, `invert_uint_mod` | pure, trivial |
| `arith` | 532 | Barrett reduction (`barrett_reduction_u128`, `barrett_coeff_u64`), `rescale`, mod-switch helpers | pure scalar |
| `ntt` | 895 | forward/inverse negacyclic NTT (poly mult) | port scalar; ref has AVX inner loops → portable |
| `poly` | 1013 | `PolyMatrixRaw`/`PolyMatrixNTT` + matrix arithmetic (the core RLWE type) | `AlignedMemory64` → `Vec<u64>` |
| `discrete_gaussian` | 206 | the error sampler (`DiscreteGaussian::{init, sample}`) | pure; **production = OsRng-seeded**, not the ref's static seeds |
| `params` | 306 | `Params` (poly_len, moduli, db_dim, instances, `t_exp_left`, …) | data + helpers |
| `gadget` | 96 | gadget decomposition (key-switching) | pure |
| (parts of) `client` | — | RLWE `sk_reg` keygen + `raw_generate_expansion_params` + `condense_matrix` | the keygen YPIR reuses |

### 1b. YPIR proper (~2,730 LoC ref)
| Module | ref LoC | What |
|---|---|---|
| `lwe` | 128 | plain LWE mod `2^32` (query enc/dec, `negacyclic_matrix` batch) — **portable already** |
| `params` | 179 | YPIR param extensions on `Params` |
| `client` (`YClient`) | 390 | `generate_query`, `pack_query`, decode |
| `server` (`YServer`) | 1246 | the DB, the SimplePIR scan, the RLWE packing, `perform_offline_precomputation_simplepir` |
| `modulus_switch` | 63 | response compression |
| `scheme` | 722 | orchestration — **we take the offline/query/answer/decode flow, NOT the benchmark harness** |

### 1c. REPLACED, not ported (the AVX kernels)
`matmul`, `kernel`, `convolution`, `transpose`, `packing` (+ `aligned_memory`, `measurement`, `bits`,
`util`) are SIMD/measurement scaffolding. The scan + transpose + negacyclic convolution become
**portable scalar loops** (correctness-first; `negacyclic_matrix_u32` already shows the scalar form).
`AlignedMemory64` → `Vec<u64>`.

---

## 2. The `MailboxRetrieval` trait fit

```rust
pub struct PirMailbox { /* YPIR params for the shard */ }   // single-server (HYP-328b)
impl MailboxRetrieval for PirMailbox {
    type Query = YpirQuery;        // (packed LWE row query, RLWE expansion pub params)
    type Answer = YpirAnswer;      // the packed + modulus-switched RLWE response
    type ClientState = YpirClientState; // RLWE sk_reg + (target_row, target_col)
    fn num_servers(&self) -> usize { 1 }
    fn query(&self, db_len, index, rng) -> (Vec<Query>, ClientState);   // index → (row,col); LWE+RLWE keygen
    fn answer(&self, query, db: &MailboxDb) -> Answer;                  // offline-precomp + scan + pack + modswitch
    fn reconstruct(&self, answers, state) -> Cell;                     // RLWE decode
}
```
`MailboxDb` is the Constellation-sized shard laid out as the `db_rows_padded × db_cols` plaintext
matrix; a mailbox slot ↦ a DB index. `num_servers()==1` (no non-collusion assumption). The `Mailbox`
seam (`MycoMailbox`'s sibling) wraps this as `PirMailbox` once the retrieval is correct.

⚠️ The trait is "online" (query/answer/reconstruct). YPIR's *offline* precomputation is **server-side
+ silent** (no client hint) → it folds inside `answer` (or a one-time `MailboxDb`-derived cache), so the
trait needs no offline method. Confirm the precompute is `MailboxDb`-derived (not query-derived) so it
caches across reads (it is — it depends only on the DB).

---

## 3. Build order (each chunk: clippy + test + a transcribed reference vector; Codex gate)

**Substrate (bottom-up):**
1. `number_theory` + `arith` — mod-q math, Barrett, rescale. Gate: known-answer vectors (a few hand-
   transcribed from the ref) + round-trips.
2. `ntt` — forward/inverse negacyclic NTT. Gate: `INTT(NTT(p)) == p`; NTT-domain pointwise-mul ==
   schoolbook negacyclic convolution.
3. `poly` — `PolyMatrixRaw`/`PolyMatrixNTT` + add/mul/automorphism. Gate: ring-mult round-trip; raw↔NTT.
4. `discrete_gaussian` + `params` — the sampler (OsRng in prod) + the `Params` struct/helpers. Gate:
   sampler bound/centering; params field-for-field vs a chosen reference param set.
5. `gadget` + RLWE keygen/expansion (`sk_reg`, `raw_generate_expansion_params`, `condense_matrix`).
   Gate: key-switch a known ciphertext; expansion round-trip.

**YPIR layer:**
6. `lwe` (mod 2^32) + the portable SimplePIR **scan** (replacing matmul/transpose). Gate: LWE
   enc→scan→dec recovers a known DB row; **the scan transcript is index-independent** (the privacy
   assertion, in-crate).
7. `YServer` (DB layout + `perform_offline_precomputation_simplepir` + RLWE packing) + `YClient`
   (`generate_query`/`pack_query`/decode) + `modulus_switch`. Gate: **full YPIR+SP retrieves a known
   item end-to-end** (the capstone — recovers `db[i]` for random `i`, server view independent of `i`).
8. `PirMailbox: MailboxRetrieval` + the shard layout (`MailboxDb` ↦ matrix). Gate (rule 27): integration
   — deposit cells, retrieve one obliviously, **malicious-single-server transcript independent of `i`**
   (the §6 / 328b acceptance test); smoke — wire behind the `Mailbox` seam as the `LimitedSingleServer`
   tier.

**Calibration + sign-off:**
9. **Params for the shard** (§4 Q1) — the ref params target 32 GB DBs; recalibrate `db_dim`/`instances`/
   moduli for a Constellation-sized shard at 128-bit LWE/RLWE security (lattice-estimator, like HYP-354
   FU1). Gate: a `params_provable` security assertion (fail-closed on an uncalibrated set, as the lattice
   work does).
10. **Tier wiring + 328f Codex sign-off** — `MailboxTier::LimitedSingleServer` selection by reachability;
    confirm the single-server unlinkability argument (the §8 sign-off, "no external audit — Opus + Codex
    + Josh").

---

## 4. Open questions (Codex DESIGN-review + Josh)

- **Q1 (Josh/params): shard size + security params.** The reference params are datacenter-DB-sized; our
  shard is small + edge-served. Pick `(db_dim_1, instances, poly_len, moduli)` for the
  Constellation-shard size at λ=128, balancing the `O(N)` scan against phone-class edge budget
  (`MAILBOX_PIR.md` §7 Decision 2 — "decide at the params chunk with measured edge numbers"). Default:
  derive a small-shard param set + gate it on the security assertion.
- **Q2 (DESIGN-review): portable-scalar scan feasibility.** Replacing the AVX scan with scalar loops is
  correct but slower; confirm it's edge-feasible for the *small shard* (the whole point of sharding is to
  keep `O(N)` small). Measure at chunk 6; if infeasible, the shard size is the dial (Q1), not SIMD.
- **Q3 (DESIGN-review): the `2^32` LWE modulus + `pt_modulus` correctness margin.** Confirm the noise
  budget (`noise_analysis.rs`) holds at our params through the two dimensions + modulus switch (the
  decode must round correctly w.h.p.). Transcribe the ref's noise bound as a runtime assertion.
- **Q4 (write-side obliviousness, `MAILBOX_PIR.md` §5/§7 Decision 3): is a pseudorandom deposit slot
  enough** against an active operator that probes by writing known slots? Argued sufficient in §5;
  confirm at the params/sign-off chunk. (Read-side is the PIR; write-side is slot pseudorandomness.)
- **Q5 (future): VIA** (eprint 2025/2074, ~3.7× lighter online) as a later swap behind the same trait —
  noted, not built (newer, less analysis; the trait makes it additive).

---

## 5. DESIGN-review log

*(to be appended by the Codex gpt-5.5/high DESIGN-review before any code)*
