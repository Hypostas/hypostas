#!/usr/bin/env python3
"""GPA_FORMAL_BOUND.md §7 — the reproducible derivation (HYP-329).

Run: `python3 gpa_formal_bound_derivation.py`. Every number in GPA_FORMAL_BOUND.md §7 comes from here,
so "machine-checked" is reproducible (the gate flagged that the prior derivation lived only in an
ephemeral shell). The arithmetic is cross-vendor reproduced; the numbers below are a COST model, not a
certified privacy guarantee (see the sensitivity caveat).

Grounding (cited in the doc):
- Gaussian mechanism, sensitivity Δ, noise σ: Dwork-Roth Thm 3.22 (classical, ε<1) / Balle-Wang analytic
  Gaussian (ε≥1).  σ = Δ·sqrt(2 ln(1.25/δ))/ε  (classical).
- Composition of a SUSTAINED D-interval event, under PER-INTERVAL adjacency (the GPA may test any temporal
  pattern — onset, offset, or a full sustained run — not only idle-throughout vs ceremony-throughout): the
  worst neighboring trace-difference is (Δ,…,Δ) over D intervals, so L2 sensitivity = sqrt(D)·Δ
  (Gaussian/zCDP). zCDP: ρ = Δ²/(2σ²); (ε,δ) via ε = ρ + 2 sqrt(ρ ln(1/δ)). Relationship = 2 partner
  traces ⇒ joint L2 sensitivity sqrt(2D)·Δ ⇒ ρ_rel = D·Δ²/σ² (exactly 2× the per-dyad ρ; this is the
  tight joint sensitivity, NOT generic group privacy Dwork-Roth Thm 2.2, which would be looser).
- SENSITIVITY: a *strict* (ε,δ) bound must use the WORST-CASE per-interval sensitivity — an all-XL Critical
  second (5·65536 B) vs an idle-silent second — because even a single XL cell (prob 0.02 ≫ δ=2⁻⁴⁰; the
  all-XL second is 0.02^5≈3e-9, still ≫ δ) cannot be tail-dropped. The mean-model Δ (the amortized volume
  gap) UNDER-noises and is only a LOWER BOUND on the true cost; it is reported for scale, labeled as such.
- COST is a proxy: composed_overhead() returns E[max(0,N(idle,σ))]/idle — an idealized order-of-magnitude
  cost of a Gaussian-noised shaper. A real shaper is upward-only (max(real,target)), so this reports the cost
  SCALE (the decision-relevant fact), not a certified implementable-mechanism cost. The (ε,δ) content is σ.
- CHANNELS: the 25× "floor" is the class/tempo RATE floor (hides that rate reveals the energy class — the §2
  leak). It does NOT hide the byte-VOLUME channel (per-cell sizes vary; real vs cover size distributions
  differ); that needs constant-size padding or the Gaussian frontier below. Different channels, not rivals.
- Lower bound (why a per-interval UTILITY-PRESERVING mechanism cannot beat √D): hiding D counting-like
  queries of sensitivity Δ requires Ω(sqrt(D)·Δ/ε) noise — Hardt-Talwar / fingerprinting. This bounds
  mechanisms that must preserve each interval's volume (can't constant-over-pad). It does NOT bound the
  deterministic floor, which is a per-interval, memoryless, ε=0 mechanism that escapes √D precisely by
  NOT preserving utility — it transmits ceremony volume ALWAYS, making idle and ceremony identical. So
  √D is the frontier for the *shaping* path, and the floor is the cheaper *non-shaping* answer.
"""
import math
from math import sqrt, log, pi, exp, erf

# --- dyados params (verified from source) ---
# cell on-wire totals S/M/L/XL (sealed_envelope CELL_TOTAL_*) x weights (generate.rs:25-31)
SIZES = [(512, 0.70), (4096, 0.20), (16384, 0.08), (65536, 0.02)]
RATES_MS = {"Ambient": 5000, "Standard": 1000, "Elevated": 500, "Critical": 200}  # cover_traffic.rs:44-53
DELTA_TM = 2.0 ** -40  # THREAT_MODEL Tier-3 δ ≤ 2^-40

MEAN_CELL = sum(b * w for b, w in SIZES)                 # 3799.04 B
VOL = {c: (1000.0 / r) * MEAN_CELL for c, r in RATES_MS.items()}  # bytes / 1s interval
IDLE, CER = VOL["Ambient"], VOL["Critical"]
DELTA_MEAN = CER - IDLE                                   # amortized idle<->ceremony volume gap (mean model)
# Worst-case per-interval sensitivity for a STRICT (ε,δ) bound: all-XL Critical second vs idle-silent.
DELTA_WC = (1000.0 / RATES_MS["Critical"]) * SIZES[3][0]  # 5 cells/s · 64 KiB = 327680 B/s
FLOOR = CER / IDLE                                        # deterministic ε=0 RATE/class floor = rate ratio

def npdf(x): return exp(-x * x / 2) / sqrt(2 * pi)
def ncdf(x): return 0.5 * (1 + erf(x / sqrt(2)))
def clamped_mean(mu, s):  # E[max(0, N(mu, s^2))] — the mechanism's mean added volume
    if s <= 0: return max(0.0, mu)
    z = mu / s
    return mu * ncdf(z) + s * npdf(z)

def rho_for_eps(eps, delta):  # largest ρ with ρ + 2 sqrt(ρ ln(1/δ)) = eps (ε increasing in ρ)
    L = sqrt(log(1.0 / delta)); u = -L + sqrt(L * L + eps)
    return u * u

def composed_overhead(D, delta_sens, eps_target=math.log(2), delta=DELTA_TM):
    # relationship (2 traces) sustained D-interval: ρ_rel = D·Δ²/σ² ⇒ σ = Δ·sqrt(D/ρ_rel)
    rho = rho_for_eps(eps_target, delta)
    sigma = delta_sens * sqrt(D / rho)
    return clamped_mean(IDLE, sigma) / IDLE

if __name__ == "__main__":
    print(f"mean cell = {MEAN_CELL:.2f} B; idle {IDLE:.2f} B/s, ceremony {CER:.2f} B/s")
    print(f"mean-model Δ = {DELTA_MEAN:.1f} B/s ({DELTA_MEAN/1024:.2f} KiB/s)  [amortized gap — LOWER bound only]")
    print(f"worst-case Δ = {DELTA_WC:.1f} B/s ({DELTA_WC/1024:.2f} KiB/s)  [strict (ε,δ) sensitivity, {DELTA_WC/DELTA_MEAN:.1f}× mean]")
    print(f"RATE/CLASS FLOOR = {FLOOR:.1f}x (ε=0, constant rate hides the class channel; NOT the byte-volume channel)")
    print(f"\nSTRICT (ε,δ) relationship frontier (zCDP, ×2 group, worst-case Δ, ε≤ln2, δ={DELTA_TM:.1e}):")
    for D, lab in [(1, "1s"), (300, "5min"), (1200, "20min")]:
        print(f"  D={D:>4} ({lab:5s}): {composed_overhead(D, DELTA_WC):>10.0f}x idle")
    print("amortized LOWER bound (mean-model Δ — under-noised, NOT a valid (ε,δ) cost):")
    for D, lab in [(1, "1s"), (300, "5min"), (1200, "20min")]:
        print(f"  D={D:>4} ({lab:5s}): {composed_overhead(D, DELTA_MEAN):>10.0f}x idle")
    print("\nSETTLEMENT: the class/tempo channel is hidden by the 25x RATE floor (ε=0); the relationship")
    print("channel is Phase-2 mixing. The byte-volume SHAPING path costs thousands-to-~10^5× (strict, worst-case)")
    print("and grows √D (this is an upper bound + an asymptotic √D lower bound), so shaping is strongly indicated")
    print("to lose to the floor+Phase-2 — the numbers are a cost SCALE, not a certified implementable mechanism.")
