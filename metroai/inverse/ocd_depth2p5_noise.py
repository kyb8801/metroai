"""
OCD depth #2.5 — noise robustness (the honest accuracy)
=======================================================
Depth #2 gave GPR RMSE ~0.2 nm, but that is on NOISE-FREE simulated spectra: clean sim
-> width is a smooth deterministic map, so any good regressor nearly memorizes it.
Real measurements carry noise. This adds measurement noise to the held-out spectra and
re-measures the GPR inverse RMSE vs noise level -> the realistic accuracy curve.

Reporting THIS (not the 0.2 nm) is what makes the claim defensible in an interview.

RUN:
  python ocd_depth2p5_noise.py
"""
import warnings
warnings.filterwarnings("ignore")
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ConstantKernel as C, RBF, WhiteKernel
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import KFold

Pi = np.loadtxt("Pi_L100P300_sim_467.csv", delimiter=",")
Phi = np.loadtxt("Phi_L100P300_sim_467.csv", delimiter=",")
names = ["bottom", "middle", "top"]
rng = np.random.default_rng(0)
scale = float(np.abs(Phi).mean())   # intensity scale for relative noise


def make_gpr():
    return make_pipeline(
        StandardScaler(),
        GaussianProcessRegressor(kernel=C(1.0) * RBF(10.0) + WhiteKernel(1e-2),
                                 normalize_y=True, alpha=1e-6, n_restarts_optimizer=1))


print("GPR OCD inverse RMSE (nm) vs measurement noise (10-fold CV)\n")
print(f"  {'noise':>7s} {'bottom':>8s} {'middle':>8s} {'top':>8s}")
for nz in [0.0, 0.005, 0.01, 0.02, 0.05]:
    errs = []
    for tr, te in KFold(10, shuffle=True, random_state=0).split(Phi):
        m = make_gpr(); m.fit(Phi[tr], Pi[tr])
        noisy = Phi[te] + nz * scale * rng.standard_normal(Phi[te].shape)
        errs.append(m.predict(noisy) - Pi[te])
    r = np.sqrt((np.vstack(errs) ** 2).mean(axis=0))
    print(f"  {nz*100:5.1f}% {r[0]:7.2f} {r[1]:7.2f} {r[2]:7.2f}")
print("\n  This noise->accuracy curve is the honest deliverable. The 0%-noise row reproduces")
print("  depth #2; realistic rows show how the GPR inverse degrades, per width.")
