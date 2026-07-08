"""
OCD depth #2.6 — which inverse is NOISE-ROBUST?  (fair comparison)
=================================================================
Depth #2.5 showed GPR's 0.2 nm collapses to 13 nm at 0.5% noise (overfitting).
But NN/KNN were only evaluated noise-free. This adds the SAME measurement noise to
the query for all three methods (NN, KNN-weighted, GPR) and compares RMSE vs noise.

Expected honest result: nearest-neighbour / KNN are far more noise-robust than a
weakly-regularized GPR — because matching/averaging tolerates noise, while GPR
memorizes fine structure. This is THE deliverable: not "GPR is best" but
"choose the inverse for the noise regime, and report it."

RUN:
  python ocd_depth2p6_robust.py
"""
import warnings
warnings.filterwarnings("ignore")
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ConstantKernel as C, RBF, WhiteKernel
from sklearn.neighbors import KNeighborsRegressor
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import KFold

Pi = np.loadtxt("Pi_L100P300_sim_467.csv", delimiter=",")
Phi = np.loadtxt("Phi_L100P300_sim_467.csv", delimiter=",")
rng = np.random.default_rng(0)
scale = float(np.abs(Phi).mean())


def nn_rmse(nz):
    e = []
    for i in range(len(Phi)):
        q = Phi[i] + nz * scale * rng.standard_normal(Phi.shape[1])
        d = np.sum((Phi - q) ** 2, axis=1); d[i] = np.inf
        e.append(Pi[np.argmin(d)] - Pi[i])
    return np.sqrt((np.array(e) ** 2).mean())


def cv_rmse(make_model, nz):
    e = []
    for tr, te in KFold(10, shuffle=True, random_state=0).split(Phi):
        m = make_model(); m.fit(Phi[tr], Pi[tr])
        q = Phi[te] + nz * scale * rng.standard_normal(Phi[te].shape)
        e.append(m.predict(q) - Pi[te])
    return np.sqrt((np.vstack(e) ** 2).mean())


def gpr():
    return make_pipeline(StandardScaler(),
        GaussianProcessRegressor(kernel=C(1.0)*RBF(10.0)+WhiteKernel(1e-2),
                                 normalize_y=True, alpha=1e-6, n_restarts_optimizer=1))
def knn():
    return KNeighborsRegressor(n_neighbors=8, weights="distance")

print("OCD inverse — overall RMSE (nm) vs measurement noise, fair comparison\n")
print(f"  {'noise':>7s} {'NN':>9s} {'KNN-w':>9s} {'GPR':>9s}   most-robust")
for nz in [0.0, 0.005, 0.01, 0.02, 0.05]:
    rn, rk, rg = nn_rmse(nz), cv_rmse(knn, nz), cv_rmse(gpr, nz)
    best = min([("NN", rn), ("KNN", rk), ("GPR", rg)], key=lambda t: t[1])[0]
    print(f"  {nz*100:5.1f}% {rn:8.2f} {rk:8.2f} {rg:8.2f}   {best}")
print("\n  Honest takeaway: report the noise-robust method for the actual measurement noise,")
print("  not the noise-free champion. This is the OCD module's ★★★ result.")
