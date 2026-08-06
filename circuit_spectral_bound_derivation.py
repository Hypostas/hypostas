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


def mu_of_r(r):
    mu = r / MAX
    for _ in range(60):  # fixed-point: mu = r*(1-e^{-mu MAX})/MAX
        mu = r * (1.0 - math.exp(-mu * MAX)) / MAX
    return mu


def spectral_peak_over_TRUE_white(r):
    """1/MAX tooth height relative to the TRUE white level 1/E[T] (NOT an off-comb sample — the v3-review
    P2: the truncation makes a harmonic COMB, so any k/MAX sample is a tooth, and sampling near one gave a
    reference > the peak ⇒ a clamp that manufactured a pass. rule #36: reference the analytic white level)."""
    mu = mu_of_r(r)
    true_white = 1.0 / mean_T(mu)
    return S(1.0 / MAX, mu) / true_white, mu


def spectral_detect_snr(r, t_obs_hours=24.0):
    """Two-sided (no clamp) coarse SNR of the 1/MAX line vs the TRUE white floor over K periods.
    NOTE (v3-review P1): even when this says 'detectable', a MATCHED FILTER over the N_target-circuit
    SUPERPOSITION is near chance (Palm–Khintchine whitening) — so the SPECTRAL channel is not the binding
    one. This number is illustrative; the LIFETIME channel below is what actually sizes r."""
    ratio, _ = spectral_peak_over_TRUE_white(r)
    K = (t_obs_hours * 3600.0) / MAX
    return (ratio - 1.0) * K


def lifetime_atom_detect(r, n_target=20, t_obs_hours=24.0):
    """THE (v3) NON-DITHERED lifetime point-mass channel. `T=min(Exp(μ),MAX)` puts a point mass at t=MAX;
    superposition does NOT whiten a per-circuit observable. Rate of at-MAX deaths = n_target·p_trunc/E[T];
    a Poisson H0 has ~0 there, so any at-MAX pile-up is detectable. P(detect≥1)=1-e^{-E[atMAX]}. This models
    the v3 (undithered) spike ONLY. The v4 DITHER does NOT hard-zero this — it reshapes the spike into the
    SHELF computed in __main__ (mass unchanged ≈e^{-r}); do NOT cite this fn as evidence the dither 'removes'
    the atom (the v4-review #4 correction). No dither param: the dithered residual is the shelf, not this."""
    mu = mu_of_r(r)
    p_trunc = math.exp(-r)  # v3 undithered spike; dithered case = the shelf (see __main__), not a hard-zero
    e_atmax = n_target * (t_obs_hours * 3600.0) / mean_T(mu) * p_trunc
    return e_atmax, 1.0 - math.exp(-e_atmax)


if __name__ == "__main__":
    print(f"MAX = {MAX:.0f}s ({MAX/60:.0f} min hard deadline)\n")
    print("SPECTRAL channel (corrected: vs TRUE white 1/E[T]; but NOT the binding channel — superposition")
    print("whitens the comb, so a matched filter is near chance regardless):")
    print(f"  {'r':>3} | {'E[T]':>8} | {'peak/true-white':>15} | {'24h SNR (illustrative)':>22}")
    for r in [2, 4, 6, 8]:
        ratio, mu = spectral_peak_over_TRUE_white(r)
        print(f"  {r:>3} | {mean_T(mu):>7.0f}s | {ratio:>15.4f} | {spectral_detect_snr(r):>22.2f}")

    print("\nLIFETIME-ATOM channel (THE BINDING one — v3-review P1): circuits dying at exactly MAX, N_target=20:")
    print(f"  {'r':>3} | {'E[T]':>8} | {'E[atMAX]/24h':>12} | {'P(det) 24h':>10} | {'P(det) 30d':>10}")
    r_safe_30d = None
    for r in [8, 10, 12, 14, 16, 18]:
        e24, p24 = lifetime_atom_detect(r, t_obs_hours=24)        # N_target=20 (default), 24h window
        e30, p30 = lifetime_atom_detect(r, t_obs_hours=30 * 24)   # N_target=20 (default), 30d window
        mu = mu_of_r(r)
        flag = ""
        if r_safe_30d is None and p30 < 0.05:
            r_safe_30d = r; flag = "  <- first r with 30d P(det) < 5%"
        print(f"  {r:>3} | {mean_T(mu):>7.0f}s | {e24:>12.3f} | {p24:>10.3f} | {p30:>10.3f}{flag}")

    print("\nDITHERED-CAP shelf (v4 — teardown at min(Exp(μ), MAX−U), U~U[0,D]). CORRECTED per v4-review #4:")
    print("dither does NOT remove the ~e^{−r} cap-hitter mass — it RESHAPES the sharp atom into a smooth SHELF")
    print("on [MAX−D, MAX]. Density there: f(t) = (e^{−μt}/D)·[μ(MAX−t)+1]. Excess mass over pure-exp:")
    print(f"  {'r':>3} | {'D=10%MAX':>9} | {'shelf mass':>11} | {'exp mass':>9} | {'excess×':>8}")
    for r in [4, 6, 8]:
        mu = mu_of_r(r)
        D = 0.10 * MAX
        n = 20000
        lo, hi = MAX - D, MAX
        shelf = sum((math.exp(-mu * (lo + (i + 0.5) * (hi - lo) / n)) / D)
                    * (mu * (MAX - (lo + (i + 0.5) * (hi - lo) / n)) + 1.0) * ((hi - lo) / n) for i in range(n))
        expmass = math.exp(-mu * lo) - math.exp(-mu * hi)
        print(f"  {r:>3} | {D:>7.0f}s | {shelf:>11.2e} | {expmass:>9.2e} | {shelf/expmass:>7.2f}×")

    print("\nHONEST STATE (v4 REFUTED on the BOUND's framing, not the mechanism):")
    print("- ACTIVITY: {count, transient, lifetime} ⊥ activity is STRUCTURAL (v4-review credited SOUND) — every")
    print("  circuit is the identical code path, verified on idle vs max-active dyads. Not a tuned bound.")
    print("- MEMBERSHIP residual = the cap-hitter mass ≈ e^{−r} (role-INDEPENDENT ⇒ membership, conceded by all")
    print("  surveyed systems). The DITHER's only job is de-SHARPENING (point mass → shelf), NOT shrinking the")
    print("  mass — an earlier version wrongly credited it with removal. Exact membership ROC (dithered vs")
    print("  ideal-Poisson) is owed + Codex cross-vendor (HYP-533).")
    print("- The dominant residual is NOT lifetime at all: it is R-dest-chain — a real conversation's successive")
    print("  carriers re-address the same peer (P(repeat)=1 vs cover ≈1/K), an ACTIVITY (conversation-presence)")
    print("  signal 522 must close via recipient-anonymous delivery (Myco/YPIR) or name as an activity residual.")
