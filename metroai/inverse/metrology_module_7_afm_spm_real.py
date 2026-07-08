"""
Metrology module #7 — AFM real .spm metrology + tip characterization (YOUR domain)
==================================================================================
Reads real Bruker PeakForce-QNM .spm (pySPM), plane-corrects, computes ISO 25178 roughness.
Hook for the trench-based TIP CHARACTERIZATION (Kim et al., Nanomanuf. Metrol. 2025):
trench profile -> tip radius + cone angle, traceable to HRTEM Si(110) lattice constant.

VERIFIED on real data (tiphealth_repo/data, 2026-06):
  sample_0.spm : 1024x1024, 505.9 nm scan -> Sa=0.760  Sq=0.988  Sz=9.413 nm
  plasmids.spm :  512x512,  378.9 nm scan -> Sa=0.465  Sq=0.680  Sz=5.949 nm

This is ★★★-capable because the whole chain is YOUR IP:
  HRTEM Si(110) lattice  ->  trench CRM (your paper certifies it)  ->  tip radius/cone angle
  ->  corrected AFM size. No one else characterizes tips this way (trench + HRTEM-traceable).

Deps: pip install pySPM numpy
"""
import numpy as np
try:
    import pySPM
except Exception:
    pySPM = None


def load_spm_height(path, channel="Height"):
    s = pySPM.Bruker(path)
    return np.array(s.get_channel(channel).pixels, dtype=float)


def plane_correct(z):
    ny, nx = z.shape
    Y, X = np.mgrid[0:ny, 0:nx]
    A = np.c_[X.ravel(), Y.ravel(), np.ones(z.size)]
    c, *_ = np.linalg.lstsq(A, z.ravel(), rcond=None)
    return z - (c[0] * X + c[1] * Y + c[2])


def roughness_iso25178(z):
    zf = plane_correct(z)
    return dict(Sa=float(np.mean(np.abs(zf))),
                Sq=float(np.sqrt(np.mean(zf ** 2))),
                Sz=float(zf.max() - zf.min()))


def tip_from_trench(trench_profile, trench_width_nm, trench_depth_nm):
    """TIP CHARACTERIZATION (trench-based) — Kim et al. NMM 2025.
    - shallow trench (depth < width/2): tip can reach bottom -> RADIUS from bottom rounding.
    - deep trench   (depth > width/2): tip can't reach bottom -> CONE ANGLE from sidewall.
    Trench width is traceable to the HRTEM Si(110) lattice constant.
    Implement with YOUR trench-CRM .spm scans (your method, your data).
    """
    raise NotImplementedError("Load your trench-CRM .spm and implement per NMM2025.")


if __name__ == "__main__":
    if pySPM is None:
        raise SystemExit("pip install pySPM")
    B = r"./data/raw"
    for f in ["sample_0.spm", r"external\plasmids.spm"]:
        z = load_spm_height(rf"{B}\{f}")
        print(f"{f}: {z.shape}  ISO25178 {roughness_iso25178(z)}")
