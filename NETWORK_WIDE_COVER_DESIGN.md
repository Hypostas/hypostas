# NETWORK_WIDE_COVER_DESIGN.md — what §6.2.2's anonymity set actually is

**Status:** DESIGN, pre-gate. Written 2026-08-04 for HYP-523.
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

## §7 Open questions carried from HYP-523

- [ ] Restated §6.2.2 claim, with the ε-dependence explicit — §5 item 1
- [ ] Effective anonymity set under the live class distribution + shipped ε — §5 item 2, `gpa-sim`
- [ ] The ε trade — §6, needs Josh
- [ ] Adversary tier: §6.2.2 as written implies a global passive observer who can compare rates across
      links, i.e. THREAT_MODEL Tier 2+. State it explicitly; a single-link observer never sees the
      partition at all.

## §8 Method note

Written from THREAT_MODEL §6.2.1–§6.2.4 and the shipped `cover_traffic` surface, with every claim in
§2 cited to a file:line rather than recalled. **This design has not been gated.** Per FACTORY.md the
next step is a cross-vendor DESIGN-review before any of §5 is acted on — and per HYP-521's lesson,
that means the full `gate-plan.sh` leg set, not a subset.
