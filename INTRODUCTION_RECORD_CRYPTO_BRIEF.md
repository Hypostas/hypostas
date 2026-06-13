# INTRODUCTION_RECORD — Crypto-construction decision brief (HYP-322 sign-off prep)

**Status:** decision input for the Fable 5 + Codex crypto sign-off. **This brief does NOT pick the construction** — per the no-human-cryptographer decision, the choice + parameters are the reserved sign-off call. It grounds the three candidates (INTRODUCTION_RECORD.md §5 a/b/c) in the actual 2022–2025 literature + implementation reality so the sign-off session starts from facts, not a blank page.

**Anchored to:** [INTRODUCTION_RECORD.md](INTRODUCTION_RECORD.md) §4 (the 4 security properties) + §5 (candidates a/b/c) + §6 (adversary model); [THREAT_MODEL.md](THREAT_MODEL.md) §5.3; [POST_QUANTUM.md](POST_QUANTUM.md) (the PQ-hybrid constraint).

**Author:** Iris, 2026-06-13. Compiled from public literature (sources at the end). **Confidence is flagged per claim**; anything I could not ground is marked ⚠️ UNVERIFIED.

---

## 0. The decision in one paragraph

We need a `BlindedVouch` that proves *"some attested introducer vouched for dyad D"* with four properties: **blindness** (the introducer B can't link its signing to the published record), **introducer-anonymity** (the verifier learns only "an attested member vouched," not which), **unlinkability** (two records don't correlate), **soundness** (no valid vouch without a real attested signer). A plain blind signature gives blindness + soundness but verifies against B's *individual* key — so the open problem is the **verifier-side anonymity layer**. Three constructions can supply it (a: aggregate/group epoch key; b: blind sig + ZK set-membership; c: anonymous credential). All three are now *implementable from published lattice work* — but **none has a production-audited, ARM-capable implementation**, which is exactly why the sign-off + the HYP-330 external audit gates exist.

---

## 1. What changed since INTRODUCTION_RECORD.md v0.1 was written

The spec (2026-06-12) framed candidate (c) as "the mature constructions are pairing-based — a PQ variant is the open question." **That framing is now out of date in our favor:**

- **Lattice anonymous credentials are a concrete, implemented thing** as of CCS 2024 (the IBM/LaZer framework — §3c below). The PQ variant is no longer purely hypothetical.
- **The base lattice blind signature got practical**: 20 KB publicly-verifiable (CCS 2023), down from ~100 KB (CRYPTO 2022).
- **A lattice *threshold* blind signature now exists** (2025, eprint 2025/1566) — candidate (a)'s hardest sub-primitive is no longer missing, just young.

So the decision is less "which one is even possible" and more **"which property-fit / size / implementation-risk tradeoff do we accept, and how do we satisfy the PQ-hybrid constraint."**

---

## 2. The base primitive: lattice blind signatures (feeds candidates a + b)

| Scheme | Venue | Size | Assumptions | Note |
|---|---|---|---|---|
| del Pino–Katsumata | CRYPTO 2022 | ~100 KB sig | standard (M-SIS/LWE), round-optimal | first practical round-optimal lattice blind sig |
| Agrawal et al. | CCS 2022 | ~ (smaller) | **non-standard** (one-more-ISIS) | new assumption — a sign-off red flag per our "battle-tested assumptions" rule |
| **Beullens–Lyubashevsky–Nguyen–Seiler** | **CCS 2023** | **20 KB sig, ~60 KB transcript** | standard (Ring/Module-SIS/LWE + NTRU), 2-round | **current practical landmark**; ~4× smaller than CRYPTO 2022 |
| — same paper, keyed-verification variant | CCS 2023 | **48 bytes** | shared signer/verifier key | tiny, but needs a *designated* verifier (see §3c caveat) |
| Baldimtsi et al. (NIBS) | Asiacrypt 2024 | — | rOM-ISIS (non-standard) | *non-interactive* blind sig — attractive flow, newer assumption |
| Faller–Niot, threshold | eprint 2025/1566 | — | — | **lattice *threshold* blind sig** — directly candidate (a) |

**Read for the sign-off:** the **CCS 2023 standard-assumption 20 KB scheme is the conservative base**. The newer non-standard-assumption schemes (one-more-ISIS, rOM-ISIS) trade size/flow for assumptions we have explicitly said we don't want to lead with (POST_QUANTUM.md: never lattice-only-on-fresh-assumptions before they're battle-tested). 20 KB is fine for a single on-chain publish.

---

## 3. The three candidates, grounded

### (a) Blind sig + epoch group / aggregate key
- **Construction:** all attested introducers in an epoch sit under one epoch verification key (group signature with blind issuance, or an aggregatable/threshold blind sig); a `BlindedVouch` verifies against the epoch key → V learns only "an epoch member signed."
- **Primitive reality:** lattice **group signatures** exist (Libert–Ling–Mouhartem–Nguyen–Wang, "ZK arguments for lattice accumulators → log-size group sigs without trapdoors," J. Cryptology 2023). A lattice **threshold blind signature** now exists (Faller–Niot 2025). But *group-signature-with-blind-issuance* as one primitive is the least off-the-shelf of the three.
- **Size/perf:** group/threshold lattice constructions are the heaviest; epoch-key management (re-aggregation as the attested set changes each epoch) is live operational complexity.
- **Pro:** verification is against a single fixed epoch key → cheapest *verifier* (good for light clients). **Con:** heaviest issuance/setup; epoch re-keying as the introducer set churns; "research-heaviest" per the spec, and the brief agrees.

### (b) Blind sig + ZK set-membership proof
- **Construction:** B issues a plain CCS-2023 lattice blind sig; D additionally proves in ZK that B's verifying key ∈ the epoch's attested-introducer set, revealing neither B nor the index. The membership anchor is a **lattice accumulator** over the attested set.
- **Primitive reality:** the most off-the-shelf path. Lattice accumulators + ZK membership are mature (Libert et al.; the LaZer library ships a **lattice accumulator built for exactly this — anonymous-credential revocation**, CCS 2024). The ZK framework (LaBRADOR / Lyubashevsky-et-al proofs) is the LaZer core.
- **Size/perf:** the ZK membership proof is the cost — **~500 KB for a 2³² -member accumulator** (public literature figure; smaller sets are smaller). Heavy but **single-publish on-chain**, which our size budget explicitly tolerates. Verifier cost is the ZK-verify (heavier than (a)'s single sig-check — matters for light clients).
- **Pro:** clean separation (blind sig ⟂ membership), each component independently studyable + swappable; strongest "compose audited parts" story. **Con:** ~500 KB record; ZK-verify cost on light clients.

### (c) Anonymous credential (keyed-verification / BBS-style, PQ variant)
- **Construction:** model "B vouches for D" as B issuing D a one-attribute anonymous credential; D presents an unlinkable proof-of-possession as the `BlindedVouch`.
- **Primitive reality — the spec's "open question" is now partly answered:** there is a **published, implemented lattice anonymous-credential framework** (IBM, "a framework for practical anonymous credentials from lattices"; prover/verifier time **independent of #users, linear in #attributes**) shipped in the **LaZer library (CCS 2024)**, plus **PQ-ABC (CCS 2024)** and lattice CTS-based ACs. Closest *property-fit* to our exact need.
- **⚠️ Verifier-key caveat (important, flag for sign-off):** "keyed-verification"/BBS-KVAC means a *designated* verifier holds an issuer/verifier secret. Our model is "**any** chain observer verifies." A KVAC fits **only if verification is delegated to chain validators** (who could hold the epoch verifier key) rather than arbitrary light clients. **Publicly-verifiable** lattice ACs exist but are larger/heavier. *This is a genuine sub-decision, not a footnote: who is "the verifier" — every light client, or the validator set on their behalf?*
- **Pro:** designed for exactly this (issue-once, present-unlinkably-many) — strongest property fit incl. unlinkability; revocation has a ready lattice-accumulator story (LaZer). **Con:** the public-verifiability-vs-KVAC fork; newest/most-moving literature; the framework is the heaviest *code* to port.

---

## 4. Cross-cutting constraints (apply to whichever wins)

1. **⚠️ PQ-hybrid is NOT free for these primitives.** POST_QUANTUM.md mandates lattice + a classical hedge. For KEMs/signatures hybrid = concatenate. For **blind sigs / anonymous credentials it is a genuine open design question**: you must hybridize *blindness/anonymity* (should hold if **either** assumption holds) and *one-more-unforgeability/soundness* (should hold if **both**, or at least one, hold) — there is no drop-in "hybrid blind signature" pattern in the literature I found. **This may be the single biggest sign-off item**, and it may push toward (b) (hybridize the *blind sig* and the *membership proof* independently — easier to reason about than hybridizing a monolithic credential).
2. **⚠️ Implementation is x86/AVX-512-bound; our target is ARM (Mac + iOS).** LaZer's LaBRADOR core **requires AVX-512 + AES, Linux amd64** — it will not run natively on Apple Silicon or iOS. Options: (i) port/replace the proof core with a portable/ARM-NEON path (large effort), (ii) run intro-record *issuance + verification server-side / on a validator* and ship only the verified result to clients (fits the on-chain model — clients trust the chain, not the proof), (iii) wait for / fund a Rust ARM-capable implementation (`lattirust`, `Lazarus` are Rust lattice-ZK efforts but less mature than LaZer). **Option (ii) interacts with the §3c verifier-key fork** — if validators verify anyway, KVAC (c) becomes very attractive and the ARM problem mostly evaporates.
3. **No audited production implementation exists** for any candidate. LaZer is MIT-licensed (usable!) but is a **research artifact** (demos / artifact-evaluation). This is the HYP-330 external-audit gate's reason for existing — but note an audit of a *research* codebase is a different scope than auditing a hardened port.
4. **Size budget:** on-chain, single-publish, not per-cell → tens-to-hundreds of KB is acceptable (the spec already says so). Verifier cost is the tighter constraint *if* light clients verify (favoring (a)); a non-constraint if validators verify (§4.2.ii).
5. **No trusted setup:** the epoch anchor must derive from the Vita-Chain attested set. All three can satisfy this (accumulator root for (b), epoch group key for (a), issuer set for (c)) — confirm per construction.

---

## 5. Comparison at a glance

| Axis | (a) epoch group/aggregate | (b) blind sig + ZK membership | (c) anonymous credential |
|---|---|---|---|
| Property fit (§4.1–4.4) | good | good | **best** (built for issue/present-unlinkable) |
| Off-the-shelf primitives | weakest (group-blind-issuance) | **strongest** (CCS23 sig ⟂ LaZer accumulator) | strong (LaZer AC framework) |
| Record size | medium | **largest** (~500 KB ZK) | medium |
| Verifier cost | **cheapest** (1 epoch-key check) | heaviest (ZK verify) | medium |
| PQ-hybrid tractability | hard (monolithic) | **easiest** (hybridize 2 parts independently) | hard (monolithic credential) |
| Epoch / churn ops | heaviest (re-aggregate key) | clean (re-accumulate root) | clean (issuer-set update) |
| Audit surface | one complex primitive | **two simpler primitives** | one complex framework |
| ARM/iOS story | same LaZer constraint | same; but parts are swappable | best *if* validators verify (KVAC) |

*Iris's read (NOT the decision):* **(b) is the conservative engineering choice** — it composes the best-understood, standard-assumption base sig (CCS 2023, 20 KB) with a separately-auditable, independently-hybridizable membership proof, at the cost of a ~500 KB record we can afford on-chain. **(c) is the best *property* fit and may be the better long-term answer** *if* the sign-off resolves the public-verifiability-vs-KVAC fork in favor of validator-side verification (which also dissolves the ARM problem). **(a) optimizes the one axis we care least about (verifier cost) at the highest research + ops cost.** This is input, not a verdict — Fable 5 + Codex decide.

---

## 6. Questions the sign-off session must resolve (the actual agenda)

1. **Who verifies?** Every light client, or the validator set on their behalf? This single answer reorders the whole table (it gates §3c KVAC and the §4.2 ARM problem). *Recommend deciding this first.*
2. **PQ-hybrid shape.** What exactly must hold under which assumption for blindness vs soundness, and is there a hybrid construction (or does (b)'s "hybridize the two parts separately" win by default)?
3. **Assumption appetite.** Standard-only (CCS 2023, 20 KB) vs accepting one-more-ISIS / rOM-ISIS for smaller/non-interactive flows? Our stated rule says standard-only until battle-tested.
4. **Implementation route.** Port LaZer's relevant subset to ARM, run verification server/validator-side, or back a Rust impl (`lattirust`/`Lazarus`)? What is the realistic effort + who owns the port?
5. **Epoch length + introducer-set churn** (deferred from the spec) — drives accumulator/group re-keying cadence and record-refresh frequency.
6. **Scope of the eventual external audit (HYP-330)** — auditing a research artifact vs a hardened port are different asks; decide what gets audited.

---

## 7. What I did NOT do / honest limits (rule #1)

- I did **not** select a construction, pick parameters, or design any lattice math. That is the reserved sign-off.
- Sizes/figures are from public abstracts + the LaZer materials; **exact parameters at our target security level are UNVERIFIED here** and must be confirmed against the papers + LaZer during sign-off.
- I did not independently assess whether any cited scheme has an *unpatched break* since publication — the sign-off must check current cryptanalysis status (lattice blind sigs have a real history of breaks; this is non-negotiable diligence).
- The PQ-hybrid-for-blind-sigs gap (§4.1) is my analysis from not finding a drop-in pattern; **treat it as a hypothesis to confirm**, not a settled fact.

---

## Sources

- del Pino & Katsumata, *A New Framework for More Efficient Round-Optimal Lattice-Based (Partially) Blind Signature via Trapdoor Sampling*, CRYPTO 2022 — https://eprint.iacr.org/2022/834
- Beullens, Lyubashevsky, Nguyen, Seiler, *Lattice-Based Blind Signatures: Short, Efficient, and Round-Optimal*, CCS 2023 — https://eprint.iacr.org/2023/077
- Agrawal et al., *Practical, Round-Optimal Lattice-Based Blind Signatures*, CCS 2022 — https://dl.acm.org/doi/abs/10.1145/3548606.3560650
- Baldimtsi et al., lattice NIBS, Asiacrypt 2024; Faller & Niot, *Lattice-Based Threshold Blind Signatures*, eprint 2025/1566 — https://eprint.iacr.org/2025/1566.pdf
- The LaZer Library (Lattice-Based ZK + Succinct Proofs), CCS 2024 — https://eprint.iacr.org/2024/1846 ; code (MIT) — https://github.com/lazer-crypto/lazer
- Libert, Ling, Mouhartem, Nguyen, Wang, *ZK Arguments for Lattice-Based Accumulators: Log-Size Ring & Group Signatures Without Trapdoors*, J. Cryptology 2023
- IBM, *A Framework for Practical Anonymous Credentials from Lattices* — https://research.ibm.com/publications/a-framework-for-practical-anonymous-credentials-from-lattices
- Rust lattice-ZK efforts: `lattirust` (https://github.com/lattirust) ; `Lazarus` (https://github.com/lattice-complete/Lazarus)

| Version | Author | Notes |
|---|---|---|
| 2026-06-13 v0.1 | Iris | Sign-off prep for HYP-322. Grounds candidates a/b/c in 2022–2025 literature + LaZer; surfaces two findings that update INTRODUCTION_RECORD §5 (lattice ACs are now implemented; PQ-hybrid-for-blind-sigs is an unsolved sub-problem) + the ARM/AVX-512 implementation constraint. Decision reserved for Fable 5 + Codex. |
