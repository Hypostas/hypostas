# CIRCUIT_BUILD_UNLINKABILITY_RESEARCH.md — literature ground for HYP-522

**Status:** RESEARCH front-matter for HYP-522 ("a real send emits no observable circuit build"), 2026-08-06. Literature-first, before design — the discipline that won GPA (NetShaper gave the primitive where 3 hand-derivations failed) and that HYP-493's 7-round graveyard lacked. Every paper claim below was read from the primary-source PDF; `[P]` = paper-stated, `[I]` = our inference/mapping. Companion to the design doc that follows and to `COVER_TRAFFIC.md §4.5a` (the observable enumeration). Sources: §10.

---

## §1 The finding that reframes the issue

HYP-522 is written as *"keep N idle circuits so a real send finds one ready and emits no handshake."* **The literature says that framing is subtly wrong in the same class as GPA's mean-vs-worst-case error:**

> **The security comes from a *continuous, activity-independent* circuit-setup cover stream — NOT from a finite pool being non-empty. The pre-built idle pool is a *latency optimization with zero security credit.***

Three independent sources converge on this:
- **Loopix** [P]: a fixed-rate Poisson emission clock where a real message *substitutes for* a drop-cover packet in a slot that would have been sent anyway ⇒ "perfect sender online unobservability." Activity changes a slot's *contents*, never the *rate*.
- **PCP** (Kadianakis et al.) [P]: dummy circuit-handshakes always in flight ⇒ a closed-form leakage bound; the guarantee holds because "a build is *always* in progress," independent of any pool being stocked.
- **Our own THREAT_MODEL §6.2.3** [P], written before this survey: *"you don't pre-route only when you're about to send — you pre-route **constantly**… fill at the cover cadence, unconditionally."*

**Consequence:** HYP-522 becomes an **affirmative-bound issue** (like HYP-329), not a mechanism-only build. The deliverable is a continuous constant-rate setup-cover channel with a stated leakage bound + explicit residuals — the pool rides on top as pure latency.

---

## §2 The literature, three families

| System (venue) | Family | Mechanism (1 line) | Property PROVEN | Residual that survives |
|---|---|---|---|---|
| **Loopix** (USENIX Sec'17) | A · constant-rate substitution | Fixed Poisson clock; real msg pops from buffer *else* a drop-cover packet is sent — emission `Pois(λ)` ⊥ activity | **Perfect sender online unobservability** (info-theoretic, memoryless) [P] | Does not hide membership/online-ness; 24/7 idle bandwidth |
| **Nym** | A | Loopix at incentivized scale; per-user loop cover **tunable** | Same indistinguishability basis (no separate theorem) [P] | Cover is optional ⇒ zeroing it restores the activity signal; gateway sees membership |
| **Herd** (SIGCOMM'15) | A | Permanent per-link constant-rate chaff; call payload replaces chaff in-place | **Zone anonymity** vs global passive adversary (invariant I6: link series ⊥ payload) [P] | Aggregate: observer learns an upper bound on concurrent calls/zone; anon-set = a trust zone |
| **PCP** (Kadianakis, arXiv 2103.03831 §8) | A | 3 preemptive circuits kept warm by dummy handshake triplets at rate λ_d (exp inter-arrival) | **Closed-form leakage bound** on handshake-count/shape (Thm 8.2) [P] | **Timing channel real-vs-cover left as future work**; λ_u leaks to middle relay |
| **Vuvuzela** (SOSP'15) | B · DP-noised rounds | Dialing (=setup) over dead drops; **every server adds truncated-Laplace noise** to dead-drop counts | **(computational) (ε,δ)-DP**, ε=ln2 δ=10⁻⁴ over 200k rounds [P] | Setup DP-*bounded* not zero; leak **composes** over a finite round budget; 12 KB/s/user |
| **Stadium** (SOSP'17) | B | Vuvuzela as verifiable distributed mixnet | (ε,δ)-DP, malicious-server-robust [P] | Same residual class; **punts setup to a separate dialing protocol (Alpenhorn)** |
| **Karaoke** (OSDI'18) | B | Round dead-drops; idle users send cover to a random drop; Bloom-verified noise | (ε,δ)-DP + **optimistic indistinguishability** (leak only on message loss) [P] | Guarantee degrades under **active** attack; punts setup to Alpenhorn |
| **Aqua** (SIGCOMM'13) | C · k-set chaff | Core: constant-rate chaffed flows; edge: group correlated clients to a common uniform rate | **k-anonymity** (k≈100) [P] | Cheap **only** when real demand is already correlated + simultaneously active; bad for bursty |
| **BriK / k-funnels** (CoNEXT'23) | C | k clients tunnel through a shared bridge, indistinguishable at egress | **k-anonymity** (1-of-k) [P] | Needs k mutually-trusted clients synchronously online; throughput 1–3 Mbps |

**Takeaways.** Family A (constant-rate substitution) is the only one that makes "a send emits nothing" *true by construction*. Family B keeps the setup event and DP-noises it (bounded, composing leak) — and Vuvuzela/Stadium/Karaoke all treat **setup as its own dialing sub-problem**, evidence it must not be folded into steady-state. Family C is cheap only under pre-correlated demand.

---

## §3 The affirmative-bound target

Two published results give HYP-522 a real bound (the setup-channel analog of our GPA volume result):

- **Loopix Poisson-indistinguishability** [P]: emission is `Pois(λ_P + λ_L + λ_D)` regardless of queue state ⇒ information-theoretic indistinguishability of "real send" from "drop cover" in any slot. No composition budget (memoryless).
- **PCP Thm 8.2** [P, exact form to re-verify against the PDF at design time]: the optimal classifier's accuracy predicting connection type from observed handshake count is stated as `max{c, 1 − c·φ/(φ+1)}` where **φ = λ_d/λ_u** (dummy-setup rate ÷ real-setup rate) and `c` = base rate; **leakage = accuracy − c decreases in φ**. Cost `≈ φ · 22.5 KB/connection`, zero added latency.

**The design should target the Loopix form** (constant-rate substitution ⇒ info-theoretic, no composing budget) as primary, with PCP Thm 8.2 as the quantified fallback for the residual real builds that *do* reach the wire. **Do NOT assert a precise φ-for-zero-leakage until re-derived against the PDF** (`§10`) — the GPA lesson: a bound that merely sounds right is a graveyard.

---

## §4 The mechanism thesis (what the design builds)

**Apply Loopix's substitution discipline to the circuit-setup channel.** Run a circuit-**warming handshake clock** at a fixed cover rate, activity-independent. Each tick emits one warming handshake whose *contents* are either a **real cold-start** (a circuit the dyad actually needs) or a **cover pre-warm** (toward a cover-eligible likely destination). The setup-event **rate is constant**; only the slot's contents vary. A real send to an already-warm destination consumes a ready circuit and adds **no** marginal setup observable.

- The **idle pool** (§19.2 / HYP-331) is the buffer that makes warming productive — pure latency, no security credit (§1).
- **Setup-fingerprint identity is a precondition** [Kadianakis, I]: cover and real handshakes must be byte- and timing-identical at the setup-packet level, or the build is classified regardless of rate. Our Sphinx-shaped `sealed_envelope` plausibly gives this for free (as Sphinx does for Loopix) — **verify at design**.
- **Evaluate the emit hook once per slot regardless of `SlotOutcome`** [Leg D, I-2]: the fatal 493 property was cover-rate ∝ (1 − activity). Loopix's fix is the exact inverse — hold rate constant, vary contents.

---

## §5 Residuals — state in THREAT_MODEL, never imply zero

1. **Membership / online-ness** [P, universal]: *no* system in the survey hides that a node runs the protocol / that N warm circuits exist. Loopix's provider link, Nym's gateway, Karaoke's own admission, Aqua's edge mix all reveal it.
2. **Timing channel** real-send-vs-surrounding-cover [P]: PCP explicitly leaves it as future work; no surveyed system proves it closed. The standing open residual.
3. **Aggregate-N upper bound** [P, Herd]: a warm rate/pool advertises "≤ N concurrent real sends possible"; resizing it with demand is itself observable.
4. **Cold-start to a never-contacted peer** [Leg D, R-1]: `P(cold-start)=1` for first contact (you cannot pre-warm a circuit to a peer you have never contacted), nonzero for any finite warm rate. Bounded only by the *continuous cover rate*, not the pool size.
5. **Multi-carrier fan-out** [Leg C F2 / HYP-518]: the set/order/timing of carriers that activate per setup is a linkage signal; must be part of the shaped observable (constant fan-out across real and cover).
6. **Structural distinguishers** [Leg D, §4.5a]: #2 destination eligibility (cover can only address cover-eligible peers), #5 rate asymmetry, #6 follow-up (DATA follows a real build with P≈1). Each must MATCH across paths or be stated STRUCTURAL.

---

## §6 The adversary to design against [Leg C]

Global-passive, **multi-carrier** observer (sees every setup handshake and its full carrier fan-out across all transports), applying **Tightrope's privacy-loss-optimal Bayesian linkage** (weights each setup by its individual leakage), persisting over **18–24 h** windows, able to **actively probe/trigger** setups to run **intersection attacks** over the fan-out. Our data-plane cover (the GPA/NetShaper result) gives this adversary **nothing** on the setup channel — NetShaper explicitly declares flow existence and connection count public [Leg C F6].

---

## §7 Anti-patterns (do not repeat)

- **Cover-rate ∝ (1 − activity)** — the 493 fatal P1: cover builds reachable only on an empty real queue ⇒ real traffic suppresses its own cover, restoring 1:1 correlation exactly under load. Loopix fix: constant rate, varying contents.
- **A rate *cap* on cover-driven builds** — 10 of 16 findings across 7 rounds were the same admission-vs-wire defect; the cap that exists to hide builds *is itself the fingerprint* (§4.5a #5). Rarity closes this; a cap never can. **Do not re-open the cap-enforcement surface.**
- **Padding-machine *reshaping* for the guarantee** — WTF-PAD/adaptive padding carry no theorem and were broken by Deep Fingerprinting (~90%). Use Tor's circuit-padding *framework* as the engineering vehicle; source the bound from Loopix/PCP continuous cover, not from reshaping a build to "look like" cover.
- **A partial subset claiming the property** — §19.1 built alone was gate-refuted (a partial defense read as progress). HYP-522 is ONE deliverable.

---

## §8 Prerequisite + build order [Leg D §4, code-verified @ dyados main 62ee9dfc]

**HYP-331 is a genuine prerequisite, not already-satisfied.** HYP-320 shipped the guarded 6-state `ChannelState {Idle, Warming, Active, Refreshing, Cooling, Closing}` enum + transitions (`lifecycle.rs:30-159`), with `Warming` documented as the §19.2 pre-build state — but it is **not stored or driven** in production. The live `channel_state()` is a read-only projection reaching only 3 of 6 states; `Warming`/`Cooling` are **unreachable because no pool exists**. No idle pool, no `IDLE_CIRCUIT_POOL_SIZE`, exists in the tree.

**Build order: HYP-331 (store+drive the lifecycle; build the pool that produces `Warming`) → HYP-522 (the continuous-cover unlinkability property + bound on top).**

---

## §9 The open decision (for Josh) — guarantee vs cost

The continuous-rate setup-cover floor is the source of the bound, and it has a real 24/7 cost [Aqua caution: uniform-rate cover is expensive precisely for idle/bursty per-dyad circuits]. Three points on the curve:

- **(a) Full continuous-rate setup cover** (Loopix/PCP/Herd) → the affirmative bound, but a 24/7 handshake-cover floor (bandwidth + battery) on every dyad.
- **(b) Optimistic** (Karaoke) → spend setup-cover only on the rare leaking event; cheaper, but the guarantee **degrades under active attack** — when it's needed most.
- **(c) Accept the residual** (Leg D fork B) → real-only builds + a best-effort latency pool, and *concede in THREAT_MODEL* that build-timing leaks activity for cold-starts. No affirmative bound; cheapest.

This is a privacy-vs-sovereignty/bandwidth/battery tradeoff — Josh's call, like the ceremony-delay decision. It gates the design's shape.

---

## §10 Provenance

Papers (primary-source PDFs read this session): Loopix (USENIX Sec'17); Nym whitepaper (Diaz et al.); Herd (SIGCOMM'15, `dl.acm.org/doi/10.1145/2785956.2787491`); PCP / "Tor circuit fingerprinting defenses using adaptive padding" (Kadianakis, Polyzos, Perry, Chatzikokolakis — arXiv **2103.03831**, §7–§8); Vuvuzela (SOSP'15); Stadium (SOSP'17, eprint 2016/943); Karaoke (OSDI'18); Aqua (SIGCOMM'13); BriK/k-funnels (CoNEXT'23, `10.1145/3629140`); Circuit Fingerprinting Attacks (USENIX Sec'15); Deep Fingerprinting (CCS'18, arXiv 1801.02265); Tik-Tok (PoPETs'20); Robust Fingerprinting (USENIX Sec'23); Mixnets on a Tightrope (IEEE S&P'25); NetShaper (USENIX Sec'24, arXiv 2310.06293). Internal: `COVER_TRAFFIC.md §4.5/§4.5a`, `CIRCUIT_LIFECYCLE.md §7/§19`, `THREAT_MODEL.md §6.2/§6.2.3/§11.6`, `RELAY_LAYER.md §15.3/§15.4`, and the 8 `scripts/factory/verdicts/dyados-cover-cap-*` gate verdicts.
