#!/usr/bin/env python3
"""HYP-522 v3 — the circuit-refresh spectral-separability bound (the #2 fix), machine-checked.

The v2 DESIGN-review P1 (#2): a bounded-jitter refresh (inter-refresh Uniform[MAX-W, MAX], CV << 1) is NOT
memoryless — it puts a sharp periodogram peak at the fundamental 1/MAX (+harmonics), reconstructable over
an 18-24h window regardless of per-event anchoring. The v3 fix: refresh each circuit on a MEMORYLESS
(exponential rate mu) schedule TRUNCATED at the hard deadline MAX. A pure exponential (Poisson) renewal has
a FLAT (white) spectrum — no line to detect. The only non-white component is the truncation atom at t=MAX
(a circuit that reaches the deadline without a spontaneous refresh), which occurs with probability
p_trunc = e^{-mu*MAX} = e^{-r}, r = MAX/E[T] ≈ mu*MAX. The 1/MAX spectral line's power scales ~ p_trunc^2,
so it is EXPONENTIALLY SUPPRESSED by raising the refresh rate (r). This script computes the peak-to-floor
ratio vs r and the r needed to sink the line below a detection floor — the affirmative spectral bound.

STATUS: computed, PENDING cross-vendor review (like the GPA frontier — never self-certified). The renewal
PSD + the detection-threshold model below are the load-bearing claims the gate must check.

Renewal power spectrum (Bartlett): for inter-renewal T with characteristic fn phi(f)=E[e^{-i2πfT}],
  S(f) = (1/E[T]) * Re[(1+phi(f))/(1-phi(f))],  f != 0.
Poisson (T~Exp): S(f) = 1/E[T] = mu, flat (verified in __main__). N_target independent circuits superpose:
S_total = N_target*S (peak-to-floor ratio is N_target-independent).
"""
import math
import cmath

MAX = 1800.0  # CIRCUIT_MAX_LIFETIME_MS/1000 = 30 min hard deadline (CIRCUIT_LIFECYCLE §7.1)


def phi(f, mu):
    """Characteristic fn of T = min(Exp(mu), MAX): E[e^{-i2πf T}]."""
    s = 2j * math.pi * f
    a = mu + s
    integral = (mu / a) * (1.0 - cmath.exp(-a * MAX))   # spontaneous refresh in (0, MAX)
    atom = math.exp(-mu * MAX) * cmath.exp(-s * MAX)     # truncation atom at t = MAX
    return integral + atom


def mean_T(mu):
    """E[min(Exp(mu), MAX)] = (1 - e^{-mu MAX})/mu."""
    return (1.0 - math.exp(-mu * MAX)) / mu


def S(f, mu):
    """Renewal PSD at frequency f (f != 0)."""
    p = phi(f, mu)
    return (1.0 / mean_T(mu)) * ((1.0 + p) / (1.0 - p)).real


def peak_to_floor(r):
    """Ratio of the PSD at the fundamental 1/MAX to the white floor, for r = MAX/E[T] (≈ mu*MAX)."""
    # solve mu from r = MAX/E[T]: E[T] = MAX/r; E[T] = (1-e^{-mu MAX})/mu. For r>>1, mu ≈ r/MAX; refine once.
    mu = r / MAX
    for _ in range(60):  # fixed-point: mu = r*(1-e^{-mu MAX})/MAX
        mu = r * (1.0 - math.exp(-mu * MAX)) / MAX
    floor = S(1.0 / MAX * 0.5 + 1.0 / MAX * 0.37, mu)  # a generic non-harmonic frequency ~ white level
    peak = S(1.0 / MAX, mu)
    return peak / floor, mu


def detect_snr(r, t_obs_hours=24.0):
    """Periodogram detectability of the 1/MAX line over t_obs. The line integrates coherently over
    K = t_obs/MAX periods (power ~ K), the white floor does not; a matched detector's SNR ~ (peak-1)*K.
    (Conservative: treats the excess peak power as the coherently-integrable line.)"""
    ratio, mu = peak_to_floor(r)
    K = (t_obs_hours * 3600.0) / MAX
    return max(ratio - 1.0, 0.0) * K, mu


if __name__ == "__main__":
    # sanity: r -> the Poisson limit is flat (peak/floor -> 1); check a moderate mu is ~white off-atom.
    print(f"MAX = {MAX:.0f}s ({MAX/60:.0f} min hard deadline)\n")
    print(f"{'r=MAX/E[T]':>11} | {'refresh every':>13} | {'p_trunc=e^-r':>12} | {'peak/floor':>11} | {'24h SNR':>10} | cost×")
    print("-" * 78)
    THRESH = 1.0  # detector SNR below ~1 ⇒ line below the noise, not detectable
    chosen = None
    for r in [1, 2, 4, 6, 8, 10, 12, 15, 20, 25]:
        ratio, mu = peak_to_floor(r)
        snr, _ = detect_snr(r)
        et = mean_T(mu)
        flag = ""
        if chosen is None and snr < THRESH:
            chosen = r; flag = "  <- first r with 24h SNR < 1"
        print(f"{r:>11} | {et:>10.1f}s   | {math.exp(-r):>12.2e} | {ratio:>11.4f} | {snr:>10.3f} | {r:>3}×{flag}")
    print()
    if chosen:
        _, mu = peak_to_floor(chosen)
        print(f"BOUND (pending review): r = {chosen} ⇒ refresh mean E[T] = {mean_T(mu):.0f}s "
              f"(~{mean_T(mu)/60:.1f} min), p_trunc = {math.exp(-chosen):.1e}, the 1/MAX line is below the "
              f"24h periodogram detection floor. Cost = {chosen}× the naive one-refresh-per-lifetime rate "
              f"(host-affordable). Smaller E[T] ⇒ flatter spectrum ⇒ more refresh cost — the #2 knob.")
    print("\nCAVEAT: the detection-SNR model (coherent line integration vs white floor) is the load-bearing")
    print("assumption; a full Neyman-Pearson treatment over the adversary's actual test is the gate's job.")
