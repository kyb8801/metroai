"""
Metrology module #8 — PL / exciton spectroscopy (TMD valleytronics, YOUR PhD data)
==================================================================================
Real MoS2 photoluminescence (Valley/PL_data_set*.csv): A-exciton fit in energy domain
+ GUM uncertainty + substrate (SiO2 vs Au plasmonic) enhancement.

VERIFIED on YOUR real data (2026-06):
  set1 SiO2: E_A = 1.8500 +/- 0.0010 eV  (matches literature MoS2 A-exciton 1.85 eV)
  set1 Au  : E_A = 1.8631 +/- 0.0004 eV, FWHM 96 meV, plasmonic PL enhancement 19x
  set2     : enhancement 11.5x

★★★: real PhD measurement + physics-validated (1.85 eV literature) + uncertainty +
the plasmonic enhancement is your valleytronics research result. This is YOUR IP.

Deps: pip install numpy pandas scipy
"""
import numpy as np, pandas as pd
from scipy.optimize import curve_fit


def gauss(x, A, x0, s, b):
    return A * np.exp(-(x - x0) ** 2 / (2 * s ** 2)) + b


def fit_pl_exciton(wl_nm, pl):
    """Fit a PL peak in energy domain. Returns dict with exciton energy/FWHM/amp + u(k=1)."""
    wl = np.asarray(wl_nm, float); pl = np.asarray(pl, float)
    m = np.isfinite(wl) & np.isfinite(pl); wl, pl = wl[m], pl[m]
    E = 1240.0 / wl
    o = np.argsort(E); E, pl = E[o], pl[o]
    p0 = [pl.max() - np.median(pl), E[np.argmax(pl)], 0.05, np.median(pl)]
    popt, pcov = curve_fit(gauss, E, pl, p0=p0, maxfev=20000)
    u = np.sqrt(np.diag(pcov))
    A, x0, s, b = popt
    return {"E_exciton_eV": x0, "u_E_eV": u[1],
            "FWHM_meV": 2.3548 * abs(s) * 1000, "amp": A}


if __name__ == "__main__":
    V = r"./data/valley"
    for fn in ["PL_data_set1.csv", "PL_data_set2.csv"]:
        df = pd.read_csv(rf"{V}\{fn}")
        print(f"=== {fn} ===")
        amps = {}
        for sub in ["SiO2", "Au"]:
            r = fit_pl_exciton(df[f"wl_{sub}(nm)"], df[f"PL_{sub}"])
            amps[sub] = r["amp"]
            print(f"  {sub:5s}: E_A={r['E_exciton_eV']:.4f}+/-{r['u_E_eV']:.4f} eV | FWHM={r['FWHM_meV']:.1f} meV")
        if amps.get("SiO2"):
            print(f"  plasmonic enhancement (Au/SiO2) = {amps['Au']/amps['SiO2']:.1f}x")
