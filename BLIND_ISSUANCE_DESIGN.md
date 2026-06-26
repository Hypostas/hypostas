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

**STATUS — Model B DECIDED (Q1, §1; Josh 2026-06-25).** The build path is fixed: extend the credential +
show to the `[s|m]` relation (§5.0), then `OblSign` with `upk` rate-limiting (§2–§4). This reconciles the
spec/code drift by **extending the code up to `LNP22_SHOW_DESIGN.md` §1 (`[s|m]`)** — §1 stays the
authoritative target; the message-only code moves to meet it. The `[s|m]` show extension deliberately
re-opens the gate-clean show (new witness `s`, new relation term `D_s·s`, new binariness/registration
constraints), so it is its **own gated sub-arc (§5.0)** that must land + re-green the existing 16
vouch/show tests BEFORE `OblSign` proper begins. (Models A and C below are retained only as the rejected
/ deferred alternatives that motivated the decision.)

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

### DECISION (Josh, 2026-06-25) — **Model B**
Issuance Sybil-resistance **must be cryptographic at issuance**: the issuer never learns `w` and
rate-limits by `upk = D_s·s`. This is the strongest model and the privacy-arc-aligned end state (an
issuer that can enumerate `w` — Model A — is a single deanonymization point; rejected). Iris's working
lean had been C-now-→-B-later (defer the show re-open); Josh chose **B now**, accepting that the
gate-clean show is re-opened to carry the user key `s`. The `s`/`upk` scaffolding already threaded
through `LNP22_SHOW_DESIGN.md` §1 is the home for this — the credential + show move from message-only
(`u + D·m`) to the full `[s | m]` relation (`u + D_s·s + D·m`), **reconciling §1 with the code by
extending the code to §1** (not by retagging §1 to message-only).

⇒ The build is the **Model B path (§5)**: extend `sep_sig` + the show to `[s|m]` FIRST, then `OblSign`
with `D_s·s`/`upk` live. The `[s|m]` show extension is a sub-design in its own right (§5.0) — it changes
the SEP relation, the show witness/commitment, the vouch families, and the codec.

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

**Retry × quota accounting (DESIGN-review P2).** Step 4's reject loop restarts with a fresh `ru`, which
**changes `c_u`** — so the quota rule must handle a changed commitment, not assume a fixed one:
- **Model C (no `upk` quota — external rate-limit):** the fresh-`ru` restart is a pure correctness loop;
  no quota interaction. Done.
- **Model B (`upk` quota):** one quota unit = one `(upk, nonce)`, and the issuer **locks** the first
  `c_u` it signs under that nonce — it **rejects any different `c_u` for the same nonce** — and derives
  the preimage **deterministically** from `H(upk, nonce, c_u)`. So a `(upk, nonce)` admits exactly one
  `c_u` and yields exactly one `v'` ⇒ one usable credential ⇒ one quota unit; a same-nonce, same-`c_u`
  retry returns the identical `v'` (no new candidate, no Sybil). Because the preimage is deterministic, a
  genuine norm-tail rejection **cannot** be cleared by re-requesting the locked nonce — the fresh-`ru`
  restart is necessarily a **fresh nonce = a fresh quota unit** (under Model B, fresh `ru` ⇒ fresh quota).
  This is sound precisely because the params make that rejection **negligible** (the restart test →
  HYP-330), so honest issuance almost never burns a second unit.
The deterministic preimage is the user's secret credential — never revealed (the show proves possession
in ZK) — so determinism leaks nothing to third parties. *(Model-B requirement; does not bite under Model
C, which has no quota.)*

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

## 5. Build order — Model B (DECIDED)

### 5.0 The `[s|m]` extension — re-open the credential + show (the prerequisite sub-arc)
A sub-design in its own right; the faithful relation deltas (thesis §6/§7 with `D_s`, `UKeyGen` §7.1.1)
are the **first build-design step** before any code. **Key tractability fact:** `D_s·s` is a *public
matrix × a single committed witness* = a **linear** term — NOT a witness×witness product like `tG·v₂`.
So the show's quadratic machinery (the one masked quadratic, R1–R5 fold) is **unchanged**; the extension
is *witness growth + extra linear/binariness rows*, not a new quadratic. Deltas:
- **`sep_sig` (0a):** keygen adds the key matrix `D_s` (`d×2d`); `UKeyGen`: `s ← T₁^{2d}`, `upk = D_s·s`.
  Sign/verify gain the term: `c = A·r + D_s·s + D·m`, `A_t·v = u + D_s·s + D·m`; `s` binary (`s∘s=s`).
  *Migration:* the message-only path is the `s = 0` / `D_s = 0` degenerate case — keep a note so the
  reconciliation with `LNP22_SHOW_DESIGN.md` §1 is explicit. **Smoke:** an `[s|m]` credential
  signs+verifies.
- **`proof_show` (0b):** the SEP relation row gains the linear `D_s·s`; the witness/commitment gain `s`
  (`2d` ring elems) + an `s`-binariness family (reuse the pure-const/`s∘s=s` block); `pq_layout`, the
  families, `PqBlindedVouch`, and codec v* grow to carry `s`. **Integration:** the **16 existing
  vouch/show tests re-green** with `[s|m]` credentials; a `[s|m]` vouch proves+verifies end-to-end.
- **Registration tie (0c):** the show does NOT re-check `D_s·s = upk` (that would de-anonymize, §1.5) —
  it only proves `s` is the SAME `s` bound under the signature (implied by the relation carrying `s`).
  `upk` enforcement is issuance-only (§2 step 3).

### 5.1 `OblSign` proper (over the `[s|m]` credential)
1. `obl_sign` module — `user_commit` (`c_u = A·ru + D_s·s + D·m`), `issuer_blind_sign` (verify `π`;
   `SamplePre` via `apply_tagged_with`; the `(upk, nonce)` quota lock + deterministic preimage, §2
   accounting), `user_unblind` (`v = v' − [ru;0]`) + the reject loop. **Smoke:** unblinded `σ` passes the
   `[s|m]` `sep_sig::verify`.
2. `π` well-formedness (π-a) — fold opening + `m,s` binary + `m = bits(w)` canonical + the mod-`p`
   quotient `z_c` + `D_s·s = upk` over `[ru | m | s]`. **Integration:** a malformed `m`/`s`, a
   non-canonical `w`, or a wrong `upk` ⇒ `π` rejects ⇒ no signature.
3. Blind-BBS (§4) — user-commit + Schnorr-PoK of *that opening only*, issuer blind-signs, user unblinds.
   No issuance-time same-`w` tie (§4/Q5).
4. `BlindIssuance::{register, request, issue, finalize}` end-to-end + the `(upk, nonce)` quota:
   a member registers `upk`, blind-requests, gets `(SepSignature[s|m], BbsSignature)` on a hidden `w`,
   builds a `PqBlindedVouch` that verifies. **Capstone (rule 27): the issuer never saw `w`, the `upk`
   quota is enforced, yet the vouch verifies.**
5. Codec for the issuance transcript + the `upk` ledger interface; file the HYP-330 param items (`[s|m]`
   norms, `z_c`/`B_ru` bounds, the reject-loop restart test).

*(Models A and C — the rejected / deferred alternatives — are retained in §1 only as the motivation for
the Model B decision.)*

## 6. Open questions (for Codex DESIGN-review + Josh)
- **Q1 (RESOLVED, Josh 2026-06-25): Model B.** Issuance Sybil-resistance is required cryptographically
  (issuer never learns `w`, rate-limits by `upk`); the credential + show extend to `[s|m]` (§5.0).
- **Q2:** `π` construction — π-a (reuse the aggregated-show fold) vs π-b (bespoke). Lean π-a.
- **Q3:** the user-side reject loop termination at provisional `s2`/`B1`/`B2` (restart-test + → HYP-330).
- **Q4:** blind-BBS — compose from `schnorr_pok` + arkworks (sovereign, no new C dep) vs a docknetwork
  primitive; confirm the cc-free path (the `lib.rs` STRICT-all-Rust constraint).
- **Q5 (RESOLVED, DESIGN-review P2):** the same-`w` tie is enforced at SHOW time by the cross-group
  anchor against the one `C_r` (a mismatched SEP/BBS pair yields no verifying vouch). Issuance needs no
  cross-proof and no `c_u ↔ t_A` binding — issuance and show are separate ceremonies linked only by the
  member's choice of one `w`. See §4. (Model B may add an up-front equality commitment for `upk`
  rate-limiting; tracked.)
