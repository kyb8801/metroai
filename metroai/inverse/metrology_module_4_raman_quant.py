"""
Metrology inverse module #4 — Raman / near-field (TERS) quantification inverse
==============================================================================
forward: analyte concentration -> Raman spectrum (Lorentzian peaks)
inverse: nonlinear fit -> concentration  +  GUM uncertainty (curve_fit covariance)

VERIFIED in sandbox 2026-06:
  conc 0.30 -> 0.3000 +/- 0.0033 (k=1)
  conc 0.72 -> 0.7169 +/- 0.0032
  conc 0.95 -> 0.9555 +/- 0.0035

This is the 4th instrument on the same forward->inverse->GUM scaffold (OCD, XRR, TEM, Raman).
Maps to the user's PhD domain (Raman / TERS / NSOM). Real TERS adds plasmonic enhancement
and near-field deconvolution; CARS->Raman would use Kramers-Kronig (cf. RamPINN).

Deps: pip install numpy scipy
"""
import numpy as np
from scipy.optimize import curve_fit

WN = np.linspace(800, 1800, 600)   # wavenumber (cm^-1)


def lorentz(x, A, x0, g):
    return A * g ** 2 / ((x - x0) ** 2 + g ** 2)


def forward(conc):
    """concentration -> two-peak Raman spectrum + baseline."""
    return lorentz(WN, conc * 100, 1000, 15) + lorentz(WN, conc * 55, 1350, 20) + 3.0


def inverse(spectrum, p0=0.4):
    """spectrum -> (concentration, standard uncertainty) via GUM covariance."""
    popt, pcov = curve_fit(lambda x, c: forward(c), WN, spectrum, p0=[p0])
    return float(popt[0]), float(np.sqrt(pcov[0, 0]))


if __name__ == "__main__":
    rng = np.random.default_rng(0)
    print("[4] Raman/TERS quantification inverse + GUM:")
    for true in [0.30, 0.72, 0.95]:
        S = forward(true) + 1.5 * rng.standard_normal(len(WN))
        c, uc = inverse(S)
        print(f"    true conc={true:.2f} -> est={c:.4f} +/- {uc:.4f} (k=1) | U(k=2)={2*uc:.4f} | err={abs(c-true):.4f}")
