# PRIVACY_DEPENDENCY_TREE.md — why the arc kept circling, and the order that stops it

**Written 2026-08-05.** Josh: *"we keep going in circles on each issue… we keep deferring and refuting
every issue due to problems."* He is right, the cause is structural, and it is not what it looks like.

---

## §1 The diagnosis

Every refutation in the 2026-08-03/04 sessions has the same shape:

> **a mechanism claiming a property whose preconditions do not exist yet.**

| Issue | Claimed | Actually needs | Outcome |
|---|---|---|---|
| HYP-493 | build events unlinkable from real traffic | *rarity* → HYP-522's idle pool | 7 gate rounds, parked |
| HYP-523 | a network-wide anonymity set | a *mixing vantage point* | refuted at root |
| HYP-527 | a DP bound on the dither | a *grounded bound* + a mechanism that can carry one | refuted, severity understated |
| §19.1 alone | circuit-timing unlinkability | §19.2 + §19.3 together | gate-refuted |

**The code was almost never wrong. The claims were.** We selected issues by priority and tractability
rather than by whether their preconditions held, so we repeatedly built a node whose parents were
missing, and the gate correctly refuted it. That is a dependency graph traversed in the wrong order —
and the graph was never written down. Linear ranks by priority; it does not say HYP-527 is
unanswerable before HYP-526.

## §2 The finding that reframes everything (VERIFIED)

`COVER_TRAFFIC.md` §7.1, verbatim:

> **Phase 1 baseline (this spec):** each dyad's own cover defends against same-link observation
> (Tier 1). **Anonymity set effectively 1**, but Tier 1 is defeated via timing-invariance.

`CIRCUIT_LIFECYCLE.md` §3: *"Circuit construction — **single-hop (Phase 1, N=1)**."*
`relay_padding.rs:1-5`: relay padding is **OFF BY DEFAULT**, opt-in, unmetered carriers only.
`COVER_TRAFFIC.md` §7.2: cover-relayed cover is *"Phase 3+ … deferred to Phase 3."*

**So Phase 1 ships anonymity set 1 on purpose, and says so.** Every issue above was claiming a
Phase-2/3 property during Phase 1. They are not *blocked* — they are **mis-phased**. The gates were
not obstacles; they were correctly refusing claims the shipped phase never promised.

That is the whole answer to "why do we keep circling."

## §3 The tree — three arcs, not one flat list

The 27 open `privacy-architecture` issues are **three arcs with different roots**, which is why a
single priority-ordered list keeps producing bad picks.

### Arc C — Foundations (roots; everything else cites these)

```
HYP-526  GPA_ANALYSIS.md does not exist          ← THE root. Cited by shipped protocol-core
  │                                                code + 5 gpa-sim files. It IS the Tier-3 bound.
  ├── gates every anonymity/DP CLAIM in Arc A
  └── gates HYP-527's retune (do not tune to a missing number)

HYP-488  specs off-main / dangling citations      ← HYP-526 is its worst instance
THREAT_MODEL self-contradiction: §6.2.4 Elevated = 1 s vs §11.2 = 500 ms   ← UNFILED
HYP-491  sweep ~95 Done issues for unfilled seams ← independent audit
HYP-492  re-review phasing across 6 specs         ← independent; would have caught §19
HYP-521  mechanize gate-plan compliance           ← independent; factory
HYP-490  cryptographer review board               ← unblocks Arc B's research gates
```

### Arc A — Traffic analysis / anonymity set

```
PHASE 1 (shipped, Tier 1 only, set = 1 BY DESIGN)
  ├── constant-rate per-dyad cover  ✅ HYP-312
  ├── single-hop circuits           ✅ N=1
  └── concrete defects, NO phase dependency — buildable today:
        HYP-432  wall-clock lifetimes / NTP jump
        HYP-435  reply-open expiry check (DECISION, vendor split)
        HYP-436  relay padding on expired legs

PHASE 2+ (needs a MIXING VANTAGE POINT — none exists at N=1)
  ├── enable multi-hop (built via HYP-209, configured N=1)
  ├── enable relay padding (built, off by default)
  ├── HYP-522  idle circuit pool (§19.1+§19.2+§19.3+§6.2.3 — ONE deliverable)
  │      └── unblocks → HYP-493 (parked), HYP-518
  ├── HYP-523  network-wide anonymity set  ← needs the vantage point AND HYP-526
  └── HYP-527  DP claim on the dither      ← needs HYP-526 AND a mechanism redesign:
                                              ε = ∞ today on a reachable subset
PHASE 3+
  └── HYP-327 archival Loopix batching · cover-relayed cover (§7.2)

GATED ON DEPLOYMENT, not on us:
  HYP-171 30-day cover validation · HYP-330 external audit
```

### Arc B — Anonymous credentials / relay identity

```
HYP-490  review board (findings memory)
  └── C3 §7 construction gates (4 open)
        └── HYP-486  credential-per-dyad cap
              ├── HYP-416  seen-N live wiring
              ├── HYP-322  blinded counterparty refs → HYP-425 vouch transport
              └── RELAY_LAYER §15's missing primitive
                    (anonymous-but-accountable relay identity)
                    └── HYP-168  Phase 3 relay directory

Self-contained chain follow-ups (no C3 dependency):
  HYP-467 envelope/receipt harness · HYP-468 authority rotation · HYP-469 chain-derived anchor
```

## §4 The path forward

**Stop attempting Arc-A Phase-2 properties.** HYP-523, HYP-493, HYP-518 and HYP-527's retune all
claim properties Phase 1 explicitly does not promise. Re-label them Phase 2 and gate them on the
vantage point, rather than re-attempting and re-refuting them. *This alone stops most of the circling.*

**Then the order is forced:**

1. **HYP-526 — write the Tier-3 bound.** The deepest root. A derivation, needing no other mechanism,
   blocking every anonymity claim in the arc, and currently cited by shipped code as if it existed.
   Nothing in Arc A can be honestly stated until it does.
2. **Phase-1 defects in parallel** — HYP-432, HYP-435 (a decision), HYP-436. Real bugs in shipped
   code, no phase dependency, no property claim beyond Tier 1.
3. **Foundations in parallel** — HYP-491 (the sweep), HYP-521 (gate-plan mechanism), HYP-492 (phasing
   re-review), and file the THREAT_MODEL rate contradiction.
4. **Arc B via HYP-490** — the review board is the only thing that moves the C3 gates, and those gates
   block five issues.
5. **Phase 2 only when the vantage point is a decision, not an accident** — enabling multi-hop and
   relay padding is a *product* decision (bandwidth, battery, sovereignty), not a build task. It
   should be taken deliberately, with HYP-522 built to meet it.

## §5 The mechanism this file is (rule #32)

A tree in a document decays. What stops the circling is a **precondition check at issue-selection
time**, not a doc someone remembers to read:

- [ ] `/frontier` must refuse to recommend an issue whose phase exceeds the shipped phase, or whose
      cited foundation (e.g. `GPA_ANALYSIS.md`) does not resolve.
- [ ] Every issue claiming a *property* names its required *vantage point / precondition* in its
      description, and that line is checkable.
- [ ] `spec-guard` already reports dangling citations; wire its output into frontier eligibility so a
      claim resting on a missing document is not selectable.

Until that exists, this file is `vigilance-only` with a review date of **2026-08-19**, and by rule
#32's fired-twice clause it is already past the threshold — HYP-493 and HYP-523 are two firings of the
same rule in two days.

## §6 Provenance

**VERIFIED verbatim this session:** COVER_TRAFFIC §7.1 / §7.2, CIRCUIT_LIFECYCLE §3,
`relay_padding.rs:1-5`, the absence of `GPA_ANALYSIS.md` (`find` across the whole workspace),
`emitted_class`'s Critical exemption, `TIER3_EPSILON_BUDGET` vs shipped γ.

**INFERRED, not verified:** the Arc-B edges below HYP-486 are drawn from RELAY_LAYER §15 and the C3
§7 item list, not re-derived here. The 27-issue set is what carries the `privacy-architecture` label —
issues that lost the label are not represented.
