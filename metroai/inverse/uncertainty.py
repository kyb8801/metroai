"""
Unified GUM uncertainty layer  (metroai/uncertainty.py)
=======================================================
The single uncertainty engine ALL instrument modules call — so "uncertainty" is
consistent across OCD/XRR/TEM/SEM/AFM/PL/NSOM/Lamb instead of ad-hoc per module.

Implements ISO/IEC Guide 98-3 (GUM) + Supplement 1 (Monte Carlo):
  - combine_gum : combined standard uncertainty u_c (with optional correlations)
  - expand      : expanded uncertainty U = k*u_c
  - monte_carlo : distribution propagation (normal/rect/triangular)
  - budget      : per-contribution uncertainty budget (%)
  - sensitivity_fd : finite-difference sensitivity coefficients c_i = dy/dx_i

VERIFIED (sandbox): block gauge u_c=0.0594 mm, U(k=2)=0.1189; MC cross-check 0.0595 (match).
Deps: numpy
"""
import numpy as np


def sensitivity_fd(f, x0, rel=1e-6):
    """Finite-difference sensitivity coefficients c_i = ∂f/∂x_i at x0."""
    x0 = np.asarray(x0, float); y0 = f(*x0); c = np.zeros_like(x0)
    for i in range(len(x0)):
        h = rel * (abs(x0[i]) or 1.0)
        xp = x0.copy(); xp[i] += h
        c[i] = (f(*xp) - y0) / h
    return c


def combine_gum(sensitivities, uncertainties, correlations=None):
    """u_c = sqrt( Σ (c_i u_i)^2  [+ 2 Σ_{i<j} c_i c_j u_i u_j r_ij] )."""
    c = np.asarray(sensitivities, float); u = np.asarray(uncertainties, float)
    var = np.sum((c * u) ** 2)
    if correlations is not None:
        R = np.asarray(correlations, float)
        for i in range(len(u)):
            for j in range(i + 1, len(u)):
                var += 2 * c[i] * c[j] * u[i] * u[j] * R[i, j]
    return float(np.sqrt(var))


def expand(u_c, k=2):
    """Expanded uncertainty U = k*u_c (k=2 ≈ 95%)."""
    return k * u_c


def monte_carlo(f, means, us, dists, N=200000, seed=0):
    """GUM Supplement 1: propagate input distributions through f.
    dists ∈ {'normal','rect','tri'} per input (u = standard uncertainty)."""
    rng = np.random.default_rng(seed); S = []
    for m, s, d in zip(means, us, dists):
        if d == "normal": S.append(rng.normal(m, s, N))
        elif d == "rect": S.append(rng.uniform(m - s * np.sqrt(3), m + s * np.sqrt(3), N))
        elif d == "tri":  S.append(rng.triangular(m - s * np.sqrt(6), m, m + s * np.sqrt(6), N))
        else: raise ValueError(f"unknown dist {d}")
    Y = f(*S); lo, hi = np.percentile(Y, [2.5, 97.5])
    return dict(mean=float(Y.mean()), u_c=float(Y.std()), U95_halfwidth=float((hi - lo) / 2))


def budget(contributions):
    """contributions: list of (name, sensitivity c_i, std uncertainty u_i).
    Returns (u_c, rows) where rows = (name, u_i, |c_i u_i|, percent)."""
    uc = combine_gum([c for _, c, _ in contributions], [u for _, _, u in contributions])
    tot = sum((c * u) ** 2 for _, c, u in contributions) or 1.0
    rows = [(n, u, abs(c * u), 100 * (c * u) ** 2 / tot) for n, c, u in contributions]
    return uc, rows


if __name__ == "__main__":
    contribs = [("L_std", 1, 0.05), ("delta_T", 1, 0.02 / np.sqrt(3)), ("delta_R", 1, 0.03)]
    uc, rows = budget(contribs)
    print(f"u_c={uc:.4f} mm | U(k=2)={expand(uc):.4f} mm")
    for n, u, ci, pct in rows:
        print(f"  {n:9s} u={u:.4f} contrib={pct:.1f}%")
    print("MC:", monte_carlo(lambda L, dT, dR: L + dT + dR, [0, 0, 0],
                             [0.05, 0.02 / np.sqrt(3), 0.03], ["normal", "rect", "normal"]))
