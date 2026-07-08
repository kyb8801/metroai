"""
NIST L100P300 — REAL scatterometry data OCD inverse   [RUN ON YOUR PC]
======================================================================
The synthetic->REAL jump for the OCD flagship. Real measured + simulated
angle-resolved scatterometry from NIST (Barnes, Henn, Silver).

Dataset: data.nist.gov  ark:/88434/mds2-2290  (CHIPS METIS; public; NIST license)
  Phi_L100P300_sim_467.csv : 467 x 84  simulated intensities  (forward library)
  Pi_L100P300_sim_467.csv  : 467 x 3   linewidth params (top/mid/bottom, nm) = labels
  Imean_L100P300_exp.csv   :   9 x 84  MEASURED intensities   (9 real dies)

DOWNLOAD (PowerShell, run inside this folder):
  $B="https://data.nist.gov/od/ds/mds2-2290"
  iwr "$B/Pi_L100P300_sim_467.csv"  -OutFile Pi_L100P300_sim_467.csv
  iwr "$B/Phi_L100P300_sim_467.csv" -OutFile Phi_L100P300_sim_467.csv
  iwr "$B/Imean_L100P300_exp.csv"   -OutFile Imean_L100P300_exp.csv

RUN:
  python nist_real_data_inverse.py

NOTE: MoR-format CSVs. If a header/orientation differs in your download, the loader
tries plain -> skip-header; if shapes look transposed (e.g. 84xN), set TRANSPOSE=True.
Compare your recovered CD against NIST's published regression (Barnes & Henn 2020,
doi:10.1117/12.2551504) as the ground-truth baseline.
"""
import numpy as np

TRANSPOSE = False  # flip to True if loaded matrices come in transposed


def load_csv(path):
    for kw in (dict(delimiter=","), dict(delimiter=",", skiprows=1)):
        try:
            a = np.loadtxt(path, **kw)
            return a.T if TRANSPOSE else a
        except ValueError:
            continue
    raise RuntimeError(f"could not parse {path} — open it and check delimiter/header")


def main():
    Pi = load_csv("Pi_L100P300_sim_467.csv")     # 467 x 3 (linewidth nm)
    Phi = load_csv("Phi_L100P300_sim_467.csv")   # 467 x 84 (sim intensity)
    Imean = load_csv("Imean_L100P300_exp.csv")   # 9 x 84 (measured)
    print("shapes:", Pi.shape, Phi.shape, Imean.shape)
    if Imean.ndim == 1:
        Imean = Imean[None, :]

    print("\n[NIST REAL-data OCD inverse — library matching]")
    for i in range(Imean.shape[0]):
        d = np.sum((Phi - Imean[i]) ** 2, axis=1)
        j = int(np.argmin(d))
        bot, mid, top = Pi[j]   # readme col order: widthBottom, widthMiddle, widthTop
        print(f"  Die {i+1}: bottom={bot:6.1f}  middle(CD)={mid:6.1f}  top={top:6.1f} nm  (residual {d[j]:.3e})")

    print("\n[uncertainty — spread of top-5 library neighbours]")
    for i in range(Imean.shape[0]):
        d = np.sum((Phi - Imean[i]) ** 2, axis=1)
        idx = np.argsort(d)[:5]
        mids = Pi[idx, 1]
        print(f"  Die {i+1}: mid-CD = {mids.mean():6.1f} +/- {mids.std():4.1f} nm (k=1, top-5 spread)")


if __name__ == "__main__":
    main()
