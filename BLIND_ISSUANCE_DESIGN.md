# BLIND_ISSUANCE_DESIGN.md — anonymous credential issuance (`OblSign`) for the C3 vouch

**HYP-352 item 1, the issuance half.** The *show* half is complete + gate-clean (the dual-hybrid
`PqBlindedVouch`: BBS bound presentation + LNP22 SEP credential show + cross-group anchor + nullifier,
all under one `C_r`). This design covers the inverse direction: how a member *obtains* the SEP + BBS
credentials, anonymously.

**Refs (faithful transcription only):** thesis ePrint 2024/131 (`refs/jeudy_thesis_2024.pdf`) **Alg 7.1
`OblSign`** + §7.1.1 (`UKeyGen`, the `(upk = D_s·s, usk = s)` registration); `LNP22_SHOW_DESIGN.md` §1
(the `[s | m]` statement) + §5.8 (the issuance sketch + its open P2); the built `sep_sig`
(`c = A·r + D·m`, `v = SamplePre(t, u+c) − [r;0]`), `sep_trapdoor` (the `SamplePre` / EllipticSampler),
and the show's binary/range/linear blocks.

**Process:** design-first → Codex DESIGN-review gate → build chunks (each gated). Nothing here is built
yet. The standing constraints hold: faithful transcription, never approximate crypto from memory;
provisional params → HYP-330; behind `experimental-unaudited`.

**STATUS — pre-decision proposal.** This doc PROPOSES the issuance models; the Q1 model choice (§1) is
Josh's and is not yet made, so **no code and no other spec change lands from this doc yet**. The repo's
authoritative show relation remains `LNP22_SHOW_DESIGN.md` §1 (`[s|m]`); the real **drift** between the
spec (`[s|m]`) and the built code (message-only) is acknowledged (§1 / Model C) and is resolved *as part
of* whichever model Q1 selects — Model C ⇒ update §1 to message-only-as-built; Model B ⇒ extend the code
to `[s|m]`. So there is no standalone merge of a contradictory target: the §1 reconciliation is bound to
the Q1 decision, not to this doc.

---

## 0. The one-paragraph mechanism (so the rest has a spine)

Normal SEP sign (built): the **issuer** picks `r`, forms `c = A·r + D·m` (it knows `m`), samples
`v = SamplePre(t, u+c) − [r;0]`, so `[A | tG−B]·v = u + D·m`. **Blind** `OblSign` moves the commitment to
the **user**: the user picks `ru`, forms `c_u = A·ru + (D_s·s) + D·m` (hiding `m`, `s`), sends `c_u` plus
a **well-formedness proof** `π`; the issuer verifies `π`, samples `v' = SamplePre(t, u + c_u)`, returns
`(t, v')`; the user **unblinds** `v = v' − [ru;0]`, giving `[A | tG−B]·v = u + D_s·s + D·m` — a valid
credential the issuer produced **without learning `m`**. The Ajtai term `A·ru` (Gaussian `ru`)
statistically hides `m`/`s` in `c_u`; `π` is what stops the issuer from blindly signing garbage.

---

## 1. THE CENTRAL DECISION — what "anonymous issuance" must hide (needs Josh)

This decision sets the entire build scope, because of a **scope finding**:

> **The built credential and the just-completed show are MESSAGE-ONLY** (`[A | tG−B]·v = u + D·m`). The
> thesis/`§1` issuance model is `[s | m]` (`… = u + D_s·s + D·m`), where `upk = D_s·s` is the issuance
> handle. **Faithful blind issuance therefore re-opens both `sep_sig` AND the show** to carry the user
> key `s` — it is not a thin add-on.

Three coherent targets:

### Model A — issuer learns `w`; only the SHOW is anonymous (no blind issuance)
The issuer signs `m = bits(w)` in the clear (the built `sep_sig::sign`), knows `w`, rate-limits by `w`;
the vouch (show) is anonymous among the attested set. **Build: ~nothing new** — the construction is
done; "issuance" is a thin `issue(w) -> (SepSignature, BbsSignature)` wrapper + the canonical-range
check at issuance (R8 P1, line 77: "same constraint applies at issuance").
**Weakness:** the issuer learns the full member set (every `w`) and can link a future vouch's *epoch
key* to an issuance — anonymity rests entirely on the show + issuer-hiding (HYP-324), not on issuance.

### Model B — blind issuance, issuer never learns `w` (the thesis/§1 model)
Credential binds `[s | m]`; `usk = s`, `upk = D_s·s` is registered (public to the issuer); `m = bits(w)`
stays hidden via `OblSign`. The issuer rate-limits by `upk`; the user proves `m` well-formed without
revealing it. **Strongest** (issuer cannot enumerate members or pre-link `w`).
**Build (large):** (i) extend `sep_sig` to `[s|m]` (add the `D_s` matrix + the `s` witness + the binary
constraint `s∘s=s`); (ii) extend the **show** to prove possession on `[s|m]` (the relation gains
`D_s·s`, the witness/commitment gain `s` — re-opening proof_show's SEP relation, the families, the
codec, the vouch); (iii) the `OblSign` protocol (§2–§3); (iv) blind-BBS (§4).

### Model C — message-only blind issuance (a first cut of B without `upk`)
`OblSign` over the **message-only** commitment `c_u = A·ru + D·m`.
⚠️ **Doc/code reconciliation (DESIGN-review P2):** the *built* `sep_sig` + `proof_show` are ALREADY
message-only (`A_t·v = u + D·m`); `LNP22_SHOW_DESIGN.md` §1's `[s|m]` relation (`… + D_s·s`) is **unbuilt
aspiration** — spec and code have drifted. So Model C matches the **built** show with **no code changes**,
but adopting it as the end state requires **updating §1 to record message-only-as-built** (and re-tagging
the `[s|m]`/`s`/`upk` material there as the Model-B-future), so the spec stops claiming a relation the
code does not implement. The issuer signs a hidden `m` and never learns `w`. **Medium build:** §2–§4 over
the existing credential **+ the §1 doc update**, no `[s|m]` code extension.
**Weakness:** without `upk` the issuer has **no issuance rate-limit** — one registrant can obtain
unlimited credentials (Sybil at issuance). Acceptable only if rate-limiting is enforced by an *external*
gate (e.g. the introduction-record ledger / web-of-trust caps issuance out-of-band), with the nullifier
still bounding one *show* per epoch.

### Recommendation
**Decide by threat model, but my lean is C now → B later, explicitly tracked — NOT A.**
- A undercuts the privacy arc's premise (THREAT_MODEL.md: 6 properties × 4 tiers, mixnet-grade): an
  issuer that learns every `w` is a single point of deanonymization. Reject A as the *end state*.
- B is the right end state but it re-opens the gate-clean show — a large, careful change that deserves
  its own design+build arc, not a tail-end rush. It is the natural home of the existing `s`/`upk`
  scaffolding already threaded through `LNP22_SHOW_DESIGN.md` §1.
- C delivers the **novel mechanism** (lattice oblivious signing: user-commit → blind preimage → unblind)
  over the *existing* credential, provable + gateable now, with the honest gap (issuance Sybil) named
  and pushed to an external rate-limit + a tracked B follow-up. It is the rule-#5 "implement what's
  buildable now, track the rest" path.

**Open question for Josh:** is issuance Sybil-resistance required *cryptographically at issuance* (⇒ B
now, accept the show re-open), or can it be enforced by the membership ledger / web-of-trust gate (⇒ C
now, B tracked)?

*(The rest of this doc specifies the mechanism common to B and C, and flags the `[s|m]` deltas where B
diverges, so the chosen model just selects which parts build.)*

---

## 2. SEP `OblSign` — the protocol (thesis Alg 7.1)

Public: `A` (`d×m1`), `u ∈ R_p^d`, `D` (`d×M_MSG`), `B = A·R` (`tG−B` forms `A_t`), [Model B adds `D_s`
(`d×2d`)]. Issuer secret: the trapdoor `R`. User input: `m = bits(w) ∈ T₁^{M_MSG}` [Model B: + `s ∈
T₁^{2d}`, with `upk = D_s·s` already registered].

1. **User — commit.** Sample `ru ← D_{R^{m1}, s2}` (the same Gaussian width `sep_sig` uses for `r`).
   Form `c_u = A·ru + D·m` [Model B: `+ D_s·s`]. This is an Ajtai commitment; `A·ru` hides `m`(`,s`).

2. **User — well-formedness proof `π`** (§3). A NIZK that `∃ (ru, m[, s])` with:
   `c_u = A·ru + D·m [+ D_s·s]` (opening) ∧ `m∘m=m` [∧ `s∘s=s`] (binary) ∧ `m = bits(w)` **canonical**
   `0 ≤ w < Fr::MODULUS` (the 255-bit range proof, R8) [Model B: ∧ `D_s·s = upk` for the registered
   `upk`] ∧ `‖ru‖₂ ≤ B_ru` (bounded randomness). Send `(c_u, π)`.

3. **Issuer — verify + sign.** Verify `π` (abort if it fails — this is the whole security of blind
   issuance: a bad `π` ⇒ the issuer would sign out-of-space/non-canonical `m` that later collides mod
   `Fr`, R8 P1 / §5.8 ⚠️). [Model B: also check `upk` is registered + not over its issuance quota — the
   rate-limit.] Pick the tag `t = F(st) ∈ Tw`. Sample `v' = SamplePre(t, u + c_u)` via the trapdoor
   (`apply_tagged_with`), so `A_t·v' = u + c_u`. Return `(t, v')`.

4. **User — unblind + check.** `v = v' − [ru; 0]` (subtract `ru` from the first `m1` coords). Then
   `A_t·v = (u + c_u) − A·ru = u + D·m [+ D_s·s]` — exactly `SEP.Verify`. Check `‖v1‖₂ ≤ B1`,
   `‖v2‖₂ ≤ B2`, `t ∈ Tw`; if a bound is violated (the issuer's preimage + `ru` overshot), **restart**
   from step 1 with fresh `ru` (reject-resample, mirroring `sep_sig::sign`'s `SIGN_RETRY_CAP` loop, but
   driven from the user side since only the user knows `ru`). Output the credential `σ = (t, v)`.

**Correctness:** identical algebra to `sep_sig::sign`, with `r` split as "user's `ru`" — the issuer's
`SamplePre` targets `u + c_u` instead of `u + c`, and the `−[ru;0]` unblind recovers the same
`A_t·v = u + D·m[+D_s·s]`. **Blindness:** the issuer sees only `c_u` (Ajtai-hiding `ru`) and `π`
(zero-knowledge) — it learns nothing about `m` beyond "well-formed", which is the point.

**Norm-budget note (→ HYP-330):** `‖v‖ ≤ ‖v'‖ + ‖ru‖`, the same split `sep_sig::sign` already absorbs
(`v = SamplePre − [r;0]`), so `B1/B2` need no change — but the user-side reject loop must be proven to
terminate w.h.p. at the provisional `s2`/`B1`/`B2` (a restart test, rule 27).

**Retry × quota accounting (DESIGN-review P2).** The user-side reject loop (step 4) runs AFTER the issuer
produced a preimage, so under a per-registrant rate-limit it must be **quota-neutral** — else a norm-tail
rejection either costs an honest user their quota or lets a user keep requesting until they collect
multiple credentials. Resolution: (i) size `s2`/`B1`/`B2` so the unblind-reject probability is
cryptographically **negligible** (the restart test above is the gate → HYP-330) — retries are a safety
cap, not an operational path; (ii) for rate-limited issuance (Model B `upk`), bind one quota unit to a
`(upk, request-nonce)` pair and derive the issuer preimage **deterministically** from
`H(upk, nonce, c_u)` (seeded sampler), so every retry for that nonce returns the SAME `v'` — idempotent:
one `(upk, nonce)` ⇒ exactly one usable credential ⇒ one quota unit, regardless of retries; a genuine
(negligible) rejection requires a fresh nonce (a fresh quota unit). For Model C (no `upk`, external
rate-limit) the retry is a pure correctness loop with no quota interaction. The deterministic preimage is
the user's secret credential — never revealed (the show proves possession in ZK) — so determinism leaks
nothing to third parties. *(This accounting is a Model-B build requirement; it does not bite under
Model C.)*

---

## 3. The well-formedness proof `π` (the open P2, §5.8)

`π` is the issuance-time analogue of the show, minus signature-possession (there's no `σ` yet). It
proves a **commitment opening + the same domain constraints the show enforces**, so the issuer cannot be
tricked into signing a message the show would later reject. Reuse, do not reinvent:

| Constraint | Built block to reuse | Notes |
|---|---|---|
| `c_u = A·ru + D·m [+ D_s·s]` (opening) | `proof_linear` (linear opening) | over the issuance commitment `c_u`, not the show `t_A` |
| `m∘m=m` [`s∘s=s`] (binary) | `proof_quadratic` / the show's pure-const binariness | per ring-elem |
| `m = bits(w)`, `0 ≤ w < Fr::MODULUS` (canonical 255-bit) | the show's R4 borrow gadget + range (`proof_ltconst`/`proof_range`) | the SAME canonical-range proof as the vouch |
| `‖ru‖₂ ≤ B_ru` | the show's approx-range (`proof_approx_range`) | bounds the blinding |
| `A·ru + D·m [+ D_s·s] − c_u = p·z_c` (mod-`p` lift) | committed quotient `z_c` + its ℓ₂ bound | see below |
| [Model B: `D_s·s = upk`] | `proof_linear` against the public `upk` (+ its own quotient) | the registration check |

**Mod-`p` → `q̂` lift (DESIGN-review P2 — non-negotiable).** Every linear equality above is over `R_p`,
but `π` (like the show) runs over `R_q̂ = p·q1`, and `R_p → R_q̂` is **not** a homomorphic embedding. So
each `R_p` equality must be proven as `LHS − RHS = p·z_c (mod q̂)` for a **committed, bounded quotient
witness `z_c`** — exactly as the show's signature relation already carries its quotient `z`
(`LNP22_SHOW_DESIGN.md` §1 R3 P1). The opening becomes `A·ru + D·m [+ D_s·s] − c_u = p·z_c (mod q̂)`, with
`z_c` joining the committed witness under its own ℓ₂ bound (and a separate quotient for `D_s·s = upk` in
Model B). Omitting `z_c` either rejects honest openings over `q̂` or proves the wrong ring relation. The
`z_c` bound is a provisional param → HYP-330.

**Construction options for `π`** (a Codex DESIGN-review question):
- **(π-a) Reuse the LNP22 aggregated-show harness** — commit `[ru | m (| s)]`, fold the table's
  constraints into one masked quadratic exactly as the vouch's R1–R5 fold, dropping only the
  signature-relation rows. Maximal reuse; same params; same `proof_show` machinery. **Preferred.**
- **(π-b) A bespoke smaller Σ-protocol** for just the opening+binary+range. Less reuse, possibly smaller,
  but a second proof system to audit. Reject unless π-a's size is shown prohibitive.

**Soundness boundary:** `π` must enforce **canonical** `m = bits(w)` (R8 P1) — without it, a malicious
user obtains a credential on a non-canonical `m' ≡ w (mod r)` that maps to the same `C_r`/`N` as a
different identity (a second credential per identity / nullifier collision). This is the §5.8 ⚠️ and the
reason "opening correctness alone" is insufficient.

---

## 4. The BBS blind-signing half

The dual-hybrid vouch carries a BBS credential too (`bbs.rs::sign` is cleartext today). Blind-BBS is a
known protocol and should mirror the SEP `OblSign` shape so both halves hide `w` from the issuer under
**one** flow:
1. User Pedersen-commits the BBS messages `C_b = Σ mᵢ·hᵢ + s_b·h₀` (with `messages[BRIDGE_MSG_IDX] = w`)
   + a Schnorr PoK of the opening (reuse `schnorr_pok`, already a dep).
2. Issuer blind-signs `C_b` (the docknetwork-style blind BBS+: `A = (g₁ + C_b + …)^{1/(x+e)}`), returns
   the blinded signature.
3. User unblinds with `s_b`.

**Binding — enforced at SHOW, not issuance (DESIGN-review P2).** Issuance does **not** cross-prove that
the SEP `m` and the BBS `messages[BRIDGE_MSG_IDX]` are the same `w`, and it does not need to. `π` proves
a lattice bit-decomposition of *some* `w_SEP`; the BBS Schnorr PoK proves an opening of `C_b` to *some*
`w_BBS` — at issuance these are uncompared, so a client *can* blindly request SEP on `w1` and BBS on
`w2 ≠ w1`. That is harmless: at **show** time the cross-group anchor binds the SEP `w_bits` (in `t_A`) to
`C_r` **and** the BBS half opens the same `C_r`, so a vouch verifies ONLY if `bits(w_SEP) = w_BBS`
(the anchor forces `w1 = w2` against the one shared `C_r`). A mismatched credential pair therefore yields
**no verifying vouch** — a wasted request, not a security break. So the single same-`w` enforcement point
is the existing `C_r` binding at show time; no issuance-time equality proof is required. *(If a future
model wants issuance to refuse mismatched requests up front — e.g. to bind both credentials to one
registration `upk` under Model B — add an explicit equality commitment tying `c_u`'s `m` to `C_b`'s
message; tracked, not built.)*

---

## 5. Build order (once the model is chosen)

**Model C path (recommended-now):**
1. `obl_sign` module — the SEP `OblSign` over `c_u = A·ru + D·m`: `user_commit`, `issuer_blind_sign`
   (reuses `apply_tagged_with`), `user_unblind` + the reject loop. **Smoke:** unblinded `σ` passes
   `sep_sig::verify`. (No `π` yet — `issuer_blind_sign` takes a *trusted* commit, gated as a step.)
2. `π` well-formedness (π-a) — fold opening+binary+range over `[ru|m]`; the issuer verifies before
   signing. **Integration:** a malformed `m` (non-binary / non-canonical) ⇒ `π` rejects ⇒ no signature.
3. Blind-BBS (§4) — user Pedersen-commits the BBS messages + a Schnorr PoK of *that opening only*,
   issuer blind-signs, user unblinds. **No issuance-time same-`w` tie** (§4/Q5: equality is show-time
   only, via the `C_r` anchor).
4. `BlindIssuance::{request, issue, finalize}` end-to-end: a member with no credential → blind requests →
   gets `(SepSignature, BbsSignature)` on a hidden `w` → builds a `PqBlindedVouch` that verifies. The
   capstone rule-27 test: **issuance never saw `w`, yet the vouch verifies.**
5. Codec + the issuance-Sybil gap documented (external rate-limit) + the **Model B** follow-up issue
   filed (extend `[s|m]` + the show).

**Model B path** prepends: 0a. extend `sep_sig` to `[s|m]`; 0b. extend `proof_show` + the vouch families
+ codec to the `[s|m]` relation; then 1–5 with the `D_s·s`/`upk` rows live.

## 6. Open questions (for Codex DESIGN-review + Josh)
- **Q1 (Josh, §1):** Model B-now vs C-now? = is issuance Sybil-resistance required cryptographically, or
  ledger-enforced?
- **Q2:** `π` construction — π-a (reuse the aggregated-show fold) vs π-b (bespoke). Lean π-a.
- **Q3:** the user-side reject loop termination at provisional `s2`/`B1`/`B2` (restart-test + → HYP-330).
- **Q4:** blind-BBS — compose from `schnorr_pok` + arkworks (sovereign, no new C dep) vs a docknetwork
  primitive; confirm the cc-free path (the `lib.rs` STRICT-all-Rust constraint).
- **Q5 (RESOLVED, DESIGN-review P2):** the same-`w` tie is enforced at SHOW time by the cross-group
  anchor against the one `C_r` (a mismatched SEP/BBS pair yields no verifying vouch). Issuance needs no
  cross-proof and no `c_u ↔ t_A` binding — issuance and show are separate ceremonies linked only by the
  member's choice of one `w`. See §4. (Model B may add an up-front equality commitment for `upk`
  rate-limiting; tracked.)
