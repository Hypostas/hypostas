# NETWORK_WIDE_COVER_DESIGN.md — what §6.2.2's anonymity set actually is

**Status:** ⛔ **REFUTED at the root by the cross-vendor DESIGN-review, 2026-08-04.** Do not act on §5.
Kept for the record and for the three findings that outlived it. Written 2026-08-04 for HYP-523.

> ## ⛔ The verdict below is WRONG, in both directions at once
>
> Three legs (Codex generic, Codex reasoning-hygiene, Claude depth) returned 5 + 6 + 14 findings.
> The central claim — *"§6.2.2 is emergent, there is nothing to build"* — is false, and the
> corrected claim in §3 is also false, in the opposite direction.
>
> **1. There IS a mechanism, and the spec names it.** `COVER_TRAFFIC.md:547` §7.1 states the shipped
> baseline outright: *"Phase 1 baseline (this spec): each dyad's own cover defends against same-link
> observation (Tier 1). **Anonymity set effectively 1**."* §6.2.2's property needs a vantage point
> where two dyads' streams merge, and `CIRCUIT_LIFECYCLE.md:86` §3 is *"single-hop (Phase 1, N=1)"* —
> there is no such vantage point today. The construction is named in three places this design never
> cited: `COVER_TRAFFIC.md:537-541` §7 (cover-sink addressing + multi-carrier fanout), `:553` §7.2
> cover-relayed cover, and `RELAY_LAYER` §6 relay padding (which `relay_padding.rs:1-3` confirms is
> **off by default**).
>
> **2. §1's inference rests on misreading one clause.** THREAT_MODEL:249's *"No relay coordination
> required"* means relays need not **coordinate** (unlike Loopix's per-hop batching). It does not say
> no relay is **required**. I read a negation of coordination as a negation of the mechanism.
>
> **3. So today's set is 1, not the rate-class cohort.** §3 is too weak, while §4's ε framing is too
> strong (see below). Both errors trace to the same omission §14 of the review names: an anonymity set
> is undefined without a (vantage point, target event) pair, and this document fixes neither.
>
> **What survives, verified:** §2's six `file:line` citations all resolve exactly; §4.1's ≥70% hole is
> accurate and correctly attributed; the directional claim that §6.2.2's precondition is violated is
> true. And three findings the review surfaced are now tracked in their own right — **HYP-526**
> (`GPA_ANALYSIS.md` does not exist), **HYP-527** (shipped γ=1/5 exceeds its own ε budget 2× in one
> epoch), and the §6.2.4-vs-§11.2 rate contradiction inside THREAT_MODEL itself.
>
> **Additional P1s against this document, for the record:** ε cannot move Elevated/Critical at all
> (`emitted_class` only flips `Ambient↔Standard`, `Critical` exempt), so §4's ε framing is irrelevant
> to the class §3.1 calls most sensitive; `gpa-sim` models a **binary** class bit, not a distribution,
> so §5 item 2 cannot be run as written; and the design omits the **cover-OFF** population entirely
> (cellular at 20–50% battery, background suspension) where every emitted packet is real — which
> `COVER_TRAFFIC.md §4.5a` row 11, **which I wrote the day before**, calls the *default cellular
> regime*.
>
> **The honest restatement**, from the review: *Phase 1 ships anonymity set 1 by design (single-hop,
> no mixing vantage); §6.2.2's property is gated on multi-hop + relay padding + cover-relayed cover,
> all tracked elsewhere; the rate-class partition, the carrier partition and the cover-OFF population
> are what will bound the set once a vantage point exists; and the shipped γ=1/5 does not meet the
> stated Tier-3 ε budget for any E ≥ 1.*
**Verdict up front:** §6.2.2 is **not a build item**, and its stated anonymity-set size is **wrong**.
The work is to restate the claim correctly and measure the parameter it actually depends on.

---

## §1 §6.2.2 is emergent, not constructed

THREAT_MODEL §6.2.2 describes network-wide cover as a *consequence*, not a mechanism:

> *"if every Hypostas dyad sends cover traffic at the same constant rate, any dyad's real message is
> indistinguishable from any other dyad's cover packet. The anonymity set is the entire active
> network… **No relay coordination required; emergent property of the cover-traffic mandate.**"*

So there is nothing to build. HYP-523 was filed as *"cover that fills the mesh, not just per-dyad
slots"* — that mischaracterises §6.2.2, which asks for no mesh-filling at all. It claims the per-dyad
engine (§6.2.1, shipped as HYP-312) **already** produces a network-wide anonymity set.

**HYP-523 is therefore a verification issue, not a construction issue.** The question is whether the
emergent property emerges.

## §2 The precondition is false by design

§6.2.2's claim is conditional — *"**if** every Hypostas dyad sends cover traffic at the same constant
rate"* — and the system deliberately violates that condition.

| Evidence | Source |
|---|---|
| Cover rate is a function of the dyad's `EnergyClass` | `vita-carriers/src/cover_traffic.rs:134-140` |
| Four distinct rates: Ambient 5 s · Standard 1 s · Elevated 500 ms · Critical 200 ms | same, + THREAT_MODEL §6.2.4's table |
| `EnergyClass` tracks the dyad's own activity | `scheduler.rs:218` `note_activity(active_base, …)` |
| §2.2 floor: Standard while active, Ambient once idle | COVER_TRAFFIC §2.2 |

Dyads do not emit at a common rate. **They emit at one of four rates, and which one is a function of
what the dyad is doing.** §6.2.4 specifies this deliberately — it is the latency/bandwidth tiering the
whole design rests on, not an oversight.

## §3 Consequence: the stated anonymity-set size is wrong

§6.2.2 reasons:

> *"N=100 dyads: 1-in-100 chance any given packet is real. N=10,000 dyads: 1-in-10,000 — approaching
> theoretical maximum."*

An observer partitions by rate **before** asking which packet is real. A packet emitted on a 1 s grid
cannot be confused with one from a dyad on a 5 s grid; the rate is visible without decrypting anything.
So the correct statement is:

> The anonymity set is **the set of dyads in the same rate class at that moment**, not the active
> network.

Two further consequences the spec does not state:

1. **The set shrinks exactly when it is needed most.** `Critical` is ceremony / dissolution /
   succession (`EnergyClass` docs) and carries the highest rate (200 ms). The rarest class is the
   most sensitive one, so the most protected traffic sits in the smallest set.
2. **Class membership is itself the signal.** Even with a large cohort, "this dyad moved from Ambient
   to Standard" reveals it became active — §2.2's floor makes that transition a direct function of
   activity. This is the aggregate-level analogue of the per-dyad enumeration in COVER_TRAFFIC §4.5a.

## §4 What dithering already buys, and what it does not

HYP-357 / HYP-359 shipped class dithering, live at three layers (`cover_traffic.rs:77` `dither_epoch`,
`:455` and `scheduler.rs:242` `dithered_rate_ms`, `driver.rs:663`), with a tunable ε_epoch DP knob.

Dithering perturbs the emitted rate so class is not perfectly readable. It therefore moves the true
anonymity set somewhere between "your class cohort" and "the network" — **as a function of ε, not of
N.** That is the parameter §6.2.2's claim actually depends on, and the spec never names it.

The existence of HYP-357/359 is itself evidence the concern is real and was already recognised at the
mechanism layer; what did not happen is propagating that recognition back into §6.2.2's claim.

### §4.1 Correction — what the dither actually defends, and a known hole (added after premise-check)

`premise-check.sh` flagged that `COVER_BUDGET_FORECAST_WIRE_DESIGN.md` (on `origin/main`, binding
canon) discusses `EnergyClass`, `cover_traffic` and `dithered_rate_ms` and that this design never cited
it. It was right, and reading it corrects two things above.

**1. The dither's up-flip is a specific defense, not generic blurring.** It *"manufactures the false
co-active floor against the **intersection attack**"* (`cover_traffic.rs:370-372`). §4 as first written
described dithering as perturbing the rate so class is not perfectly readable — true but under-stated.
The up-flip half exists so an idle dyad *appears* co-active; that is what enlarges the set, and it is
the half that can be suppressed independently.

**2. There is a known, tested hole exactly in the property this design is about.** At
`fraction_consumed ≥ 0.70` the budget ceiling is `Ambient`, so `dithered_rate_ms` clamps the up-flip:
the intersection-attack defense is **fully removed for an idle dyad in [70%, 80%) consumed**. This is
disclosed and pinned by `dither_up_flip_fully_suppressed_at_70pct_consumed`. §5's simulation must model
it rather than rediscover it — the anonymity set has a documented hole keyed on budget consumption, and
therefore on carrier and usage, not just on class.

**Method note.** This is the second time in two days that a decision record I had not read already
contained the answer. Here the mechanism caught it *before* a gate was spent, which is precisely what
rule #33 was written for.

## §5 The work

This is a spec-correctness and measurement issue, not a build:

1. **Restate §6.2.2** in terms of the rate-class partition and ε, replacing the 1-in-N arithmetic.
   Quantified honestly, including the Critical-class inversion in §3.1.
2. **Measure the real set size.** `gpa-sim` already exists and was hardened during HYP-357. Given a
   class distribution and an ε, what is the effective anonymity set? This is answerable by simulation
   now — it does **not** need the deployed mesh HYP-523 was parked for.
3. **Decide the ε trade** (§6, below) — Josh's call, not a build decision.
4. **Only then** consider whether any mechanism is warranted beyond dithering.

**Note on the parking rationale.** HYP-523 was filed at Low on the grounds that mesh-uniform cover
needs mesh scale that does not exist. Items 1–3 need no scale at all; the simulation and the spec
correction are available today. The scale dependency applies only to *validating* the modelled set
against reality (HYP-171).

## §6 The decision this design cannot make

Larger ε → rates blur across classes → bigger anonymity set → **but** the dyad's actual energy/latency
tier is no longer honoured, so an Ambient dyad on battery pays a Standard dyad's bandwidth, and a
Critical ceremony may not get its 200 ms grid.

That is the sovereignty trade COVER_TRAFFIC §5 and §2.3 exist to arbitrate: **how much of a dyad's own
battery and metered bandwidth may be spent to enlarge someone else's anonymity set?** It is a product
and values question, not an engineering one, and per the standing rule it goes to Josh rather than
being resolved here.

**Correction: this question is not new, and Josh has already answered a version of it.**
`COVER_BUDGET_FORECAST_WIRE_DESIGN.md` frames it as the **up-flip decoupling tradeoff** —
*"at ≥70% consumed, cap the committed class for cost BUT keep the idle-dyad protective RR-dither
up-flip firing (bandwidth-vs-intersection-defense), currently resolved for bandwidth (fully suppressed
at ≥70%)"* — and records it as a *remaining, optional, non-blocking* decision with the decoupling
explicitly available as a follow-up.

So the correct framing is **not** "here is an open sovereignty question." It is: *the tradeoff was
decided for bandwidth at the ≥70% boundary; does the network-wide anonymity-set analysis in §3 change
that answer?* That is a smaller, better-posed question, and it should be asked with §5's measurement in
hand rather than in the abstract.

## §7 Open questions carried from HYP-523

- [ ] Restated §6.2.2 claim, with the ε-dependence explicit — §5 item 1
- [ ] Effective anonymity set under the live class distribution + shipped ε — §5 item 2, `gpa-sim`
- [ ] The ε trade — §6. **Re-posed:** not an open question but a re-examination of the up-flip
      decoupling already decided for bandwidth at ≥70%. Ask it with §5's numbers, not in the abstract.
- [ ] Adversary tier: §6.2.2 as written implies a global passive observer who can compare rates across
      links, i.e. THREAT_MODEL Tier 2+. State it explicitly; a single-link observer never sees the
      partition at all.

## §8 Method note

Written from THREAT_MODEL §6.2.1–§6.2.4 and the shipped `cover_traffic` surface, with every claim in
§2 cited to a file:line rather than recalled. **This design has not been gated.** Per FACTORY.md the
next step is a cross-vendor DESIGN-review before any of §5 is acted on — and per HYP-521's lesson,
that means the full `gate-plan.sh` leg set, not a subset.
