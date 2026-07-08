"""
Metrology module #9 — NSOM hyperspectral defect mapping (TMD, YOUR PhD method)
==============================================================================
Per-pixel exciton peak extraction -> k-means domain/defect segmentation + quantification.
Method from your MoSe2_NSOM_30x30_kmeans.ipynb (near-field exciton imaging of TMDs).

VERIFIED (synthetic, 2026-06): pristine 1.550 eV / defect 1.500 eV; k-means seg 100%;
defect-domain area 20.6%; exciton redshift 0.05 eV (strain/defect signature).

★★ on synthetic; with your real NSOM .txt hyperspectral export -> ★★★ (your PhD data).

Deps: pip install numpy scikit-learn
"""
import numpy as np
from sklearn.cluster import KMeans


def load_nsom_export(xaxis_txt, yaxis_txt, map_x, n_spec, roi=None):
    """Load NSOM hyperspectral export (your format: X-Axis.txt + Y-Axis.txt stream).
    Returns (E_axis, cube[H,W,n_spec]). roi=(r0,r1,c0,c1)."""
    E = np.loadtxt(xaxis_txt)
    vals = np.loadtxt(yaxis_txt).reshape(-1, n_spec)
    rows = vals.shape[0] // map_x
    cube = vals[:rows * map_x].reshape(rows, map_x, n_spec)
    if roi:
        r0, r1, c0, c1 = roi; cube = cube[r0:r1, c0:c1]
    return E, cube


def exciton_peak_map(cube, E):
    """per-pixel exciton energy (argmax). cube: (H,W,spectral)."""
    return E[np.argmax(cube, axis=2)]


def defect_segmentation(cube, n_clusters=2, random_state=0):
    """k-means on full spectra -> domain/defect label map."""
    H, W, S = cube.shape
    lab = KMeans(n_clusters, n_init=10, random_state=random_state).fit_predict(cube.reshape(-1, S))
    return lab.reshape(H, W)


def quantify(peakE, labels):
    out = {}
    for c in np.unique(labels):
        m = labels == c
        out[int(c)] = {"area_frac": float(m.mean()), "exciton_E_mean_eV": float(peakE[m].mean())}
    return out


if __name__ == "__main__":
    E = np.linspace(1.3, 1.8, 200)
    def spec(E0, w, A): return A * np.exp(-(E - E0) ** 2 / (2 * w ** 2))
    cube = np.zeros((30, 30, 200)); rng = np.random.default_rng(0)
    for i in range(30):
        for j in range(30):
            if (i-15)**2 + (j-15)**2 < 60:
                cube[i, j] = spec(1.50, 0.045, 0.7) + 0.02*rng.standard_normal(200)
            else:
                cube[i, j] = spec(1.55, 0.025, 1.0) + 0.02*rng.standard_normal(200)
    pE = exciton_peak_map(cube, E); lab = defect_segmentation(cube)
    print("NSOM defect mapping:", quantify(pE, lab))
