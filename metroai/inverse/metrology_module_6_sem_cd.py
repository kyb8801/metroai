"""
Metrology inverse module #6 — CD-SEM linewidth via edge detection
=================================================================
Linewidth (critical dimension) from a SEM secondary-electron intensity profile,
50%-threshold edge detection + Monte-Carlo (GUM) uncertainty.

VERIFIED (synthetic) 2026-06:
  true 100 nm -> 98.0 nm (bias -2 nm, set by beam-blur/threshold model)
  precision robust to noise: 2%->±0.0, 5%->±0.24, 10%->±0.75, 20%->±1.51 nm
  => precision != accuracy again: low scatter but a model-dependent bias.

★★ on synthetic. Real CD-SEM needs a MEASURED point-spread/beam model and a
threshold calibrated to a reference (e.g. TEM cross-section) to remove the bias.

Deps: pip install numpy scipy
"""
import numpy as np
from scipy.ndimage import gaussian_filter1d


def measure_cd(profile, px=1.0, thr=0.5, smooth=2.0):
    """linewidth (nm) from an SE line profile via threshold edge detection."""
    p = gaussian_filter1d(profile, smooth)
    half = p.min() + thr * (p.max() - p.min())
    idx = np.where(p >= half)[0]
    return (idx[-1] - idx[0]) * px if len(idx) > 1 else float("nan")


if __name__ == "__main__":
    N, px, true_cd = 400, 1.0, 100.0
    x = np.arange(N) * px; c = N * px / 2
    prof0 = gaussian_filter1d(((x > c - true_cd/2) & (x < c + true_cd/2)).astype(float), 4)
    rng = np.random.default_rng(0)
    print(f"[6] CD-SEM: clean CD={measure_cd(prof0):.2f} nm (true {true_cd})")
    for nz in [0.02, 0.05, 0.10, 0.20]:
        e = np.array([measure_cd(prof0 + nz*rng.standard_normal(N)) for _ in range(150)])
        e = e[np.isfinite(e)]
        print(f"    noise={nz*100:4.0f}%  CD={e.mean():6.2f} +/- {e.std():.2f} nm (k=1) | U(k=2)={2*e.std():.2f}")
