#!/usr/bin/env python3
"""GPA_FORMAL_BOUND.md §7 — the reproducible derivation (HYP-329).

Run: `python3 gpa_formal_bound_derivation.py`. Every number in GPA_FORMAL_BOUND.md §7 comes from here,
so "machine-checked" is reproducible (the gate flagged that the prior derivation lived only in an
ephemeral shell). Cross-vendor verified: the composed frontier below reproduces the Claude depth-leg's
independent derivation (147x / 2536x / 5072x) to within rounding.

Grounding (cited in the doc):
- Gaussian mechanism, sensitivity Δ, noise σ: Dwork-Roth Thm 3.22 (classical, ε<1) / Balle-Wang analytic
  Gaussian (ε≥1).  σ = Δ·sqrt(2 ln(1.25/δ))/ε  (classical).
- Composition of a SUSTAINED D-interval event: the two hypotheses' trace-difference is (Δ,…,Δ) over D
  intervals, so L2 sensitivity = sqrt(D)·Δ (Gaussian/zCDP) — NOT bounded-constant. zCDP: ρ = Δ2²/(2σ²);
  (ε,δ) via ε = ρ + 2 sqrt(ρ ln(1/δ)). Relationship = 2 traces ⇒ group privacy ×2 (Dwork-Roth Thm 2.2).
- Lower bound (why NO per-interval mechanism escapes): hiding D counting-like queries of sensitivity Δ
  requires Ω(sqrt(D)·Δ/ε) noise — Hardt-Talwar / fingerprinting. So sqrt(D) is a floor, not a Gaussian
  artifact.
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
DELTA = CER - IDLE                                        # idle<->ceremony volume sensitivity (mean model)
FLOOR = CER / IDLE                                        # deterministic ε=0 floor = rate ratio

def npdf(x): return exp(-x * x / 2) / sqrt(2 * pi)
def ncdf(x): return 0.5 * (1 + erf(x / sqrt(2)))
def clamped_mean(mu, s):  # E[max(0, N(mu, s^2))] — amortized shaping overhead
    if s <= 0: return max(0.0, mu)
    z = mu / s
    return mu * ncdf(z) + s * npdf(z)

def sigma_classical(eps, delta=DELTA_TM):  # Dwork-Roth Thm 3.22 (valid ε<1)
    return DELTA * sqrt(2 * log(1.25 / delta)) / eps

def rho_for_eps(eps, delta):  # smallest ρ with ρ + 2 sqrt(ρ ln(1/δ)) = eps
    L = sqrt(log(1.0 / delta)); u = -L + sqrt(L * L + eps)
    return u * u

def composed_overhead(D, eps_target=math.log(2), delta=DELTA_TM):
    # relationship (2 traces) sustained D-interval: L2 sens = sqrt(2D)·Δ ⇒ ρ_rel = D·Δ²/σ²
    rho = rho_for_eps(eps_target, delta)
    sigma = DELTA * sqrt(D / rho)
    return clamped_mean(IDLE, sigma) / IDLE

if __name__ == "__main__":
    print(f"mean cell = {MEAN_CELL:.2f} B; idle {IDLE:.2f} B/s, ceremony {CER:.2f} B/s")
    print(f"sensitivity Δ = {DELTA:.1f} B/s ({DELTA/1024:.2f} KiB/s); DETERMINISTIC FLOOR = {FLOOR:.1f}x (ε=0, no composition)")
    print("\nper-interval Gaussian idle overhead (single interval, ε<1 rows only are in Thm 3.22 domain):")
    for eps in [math.log(2)]:
        s = sigma_classical(eps); print(f"  ε_T={eps:.3f}: {clamped_mean(IDLE, s)/IDLE:.1f}x  (ε≥1 rows need the analytic Gaussian)")
    print(f"\nCOMPOSED relationship frontier (zCDP, ×2 group, ε≤ln2, δ={DELTA_TM:.1e}) — the corrected §7 table:")
    for D, lab in [(1, "1s"), (300, "5min"), (1200, "20min")]:
        print(f"  D={D:>4} ({lab:5s}): {composed_overhead(D):.0f}x idle")
    print("\nSETTLEMENT: sustained ceremony ⇒ 25x floor (ε=0) or Phase-2; per-interval is 147x–5070x + √D lower-bounded.")
