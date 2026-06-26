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
`OblSign` over the **message-only** commitment `c_u = A·ru + D·m` (matches the built credential/show —
**no `s`, no show changes**). The issuer signs a hidden `m` and never learns `w`. **Medium build:** just
§2–§4 over the existing credential, no `[s|m]` extension.
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
| [Model B: `D_s·s = upk`] | `proof_linear` against the public `upk` | the registration check |

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

**Binding (§5):** the SEP `m` and the BBS `messages[BRIDGE_MSG_IDX]` are the **same `w`**. At *show* time
the cross-group anchor already binds `w_bits ↔ C_r` and the BBS half opens `C_r` — so issuance need only
ensure both credentials are issued on the same `w` (the user supplies one `w`; `π` ties the SEP `m` to
`bits(w)` and the Schnorr PoK ties the BBS message to the same `w`). No new cross-domain machinery — it
reuses the vouch's existing `C_r` binding at show time.

---

## 5. Build order (once the model is chosen)

**Model C path (recommended-now):**
1. `obl_sign` module — the SEP `OblSign` over `c_u = A·ru + D·m`: `user_commit`, `issuer_blind_sign`
   (reuses `apply_tagged_with`), `user_unblind` + the reject loop. **Smoke:** unblinded `σ` passes
   `sep_sig::verify`. (No `π` yet — `issuer_blind_sign` takes a *trusted* commit, gated as a step.)
2. `π` well-formedness (π-a) — fold opening+binary+range over `[ru|m]`; the issuer verifies before
   signing. **Integration:** a malformed `m` (non-binary / non-canonical) ⇒ `π` rejects ⇒ no signature.
3. Blind-BBS (§4) + the same-`w` Schnorr tie.
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
- **Q5:** does `OblSign`'s `c_u` need its own commitment binding to the eventual show `t_A`, or is the
  same-`w` tie at show time (the anchor) sufficient? (Lean: sufficient — issuance and show are separate
  ceremonies linked only by `w`.)
