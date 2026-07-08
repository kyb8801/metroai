"""
OCD depth #1 — NIST 467 library inverse ABSOLUTE ACCURACY (leave-one-out CV)
===========================================================================
The "real 9 dies" inverse has no ground-truth reference, so accuracy was unmeasured.
But each of the 467 SIMULATIONS has a KNOWN ground-truth Pi (bottom/middle/top width),
so leave-one-out cross-validation measures how accurately nearest-library inverse
recovers the true widths. RMSE per width = the inverse's intrinsic accuracy, limited
by library sampling density.

This turns "it runs" into "it is accurate to X nm" — the ★→★★ step.

RUN (NIST CSVs already downloaded by run_flagship.ps1):
  python ocd_depth1_accuracy_cv.py

Deps: pip install numpy
"""
import numpy as np

Pi = np.loadtxt("Pi_L100P300_sim_467.csv", delimiter=",")    # 467 x 3: bottom, middle, top (nm)
Phi = np.loadtxt("Phi_L100P300_sim_467.csv", delimiter=",")  # 467 x 84: simulated intensities
names = ["bottom", "middle", "top"]

# ---- leave-one-out: query each sim, match against the other 466 ----
err = np.zeros_like(Pi)
nn_dist = np.zeros(len(Phi))
for i in range(len(Phi)):
    d = np.sum((Phi - Phi[i]) ** 2, axis=1)
    d[i] = np.inf                       # exclude self
    j = int(np.argmin(d))
    err[i] = Pi[j] - Pi[i]              # estimated - true
    nn_dist[i] = d[j]

rmse = np.sqrt((err ** 2).mean(axis=0))
bias = err.mean(axis=0)
mae = np.abs(err).mean(axis=0)
p95 = np.percentile(np.abs(err), 95, axis=0)

print("NIST 467-library inverse — leave-one-out cross-validation (absolute accuracy)")
print(f"  (nearest-neighbour matching; ground truth known from Pi)\n")
print(f"  {'width':8s} {'RMSE':>8s} {'MAE':>8s} {'bias':>8s} {'p95|err|':>9s}")
for k, nm in enumerate(names):
    print(f"  {nm:8s} {rmse[k]:7.2f}n {mae[k]:7.2f}n {bias[k]:+7.2f}n {p95[k]:8.2f}n")

print(f"\n  Interpretation: RMSE is the nearest-neighbour resolution floor of the 467 library.")
print(f"  Tighter sampling, interpolation (parabolic/GPR), or gradient refinement (autodiff)")
print(f"  reduces it. Compare middle-width RMSE to the ~107-133 nm recovered for the 9 real dies.")
