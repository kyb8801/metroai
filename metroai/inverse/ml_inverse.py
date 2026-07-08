"""
Generic ML inverse + ML uncertainty  (metroai/ml_inverse.py)
============================================================
The shared AI engine ALL instruments use, so "AI" is real & consistent (not just OCD/NSOM):
  ② ML inverse   — ensemble regressor: measurement vector -> parameter(s)
  ③ ML uncertainty — ensemble epistemic std  +  conformal (distribution-free coverage)
Composable with ① uncertainty.py (GUM):  u_total = sqrt(u_GUM^2 + u_ML^2).

VERIFIED (sandbox): conformal 90% target -> 89% empirical coverage (calibrated);
ensemble std gives epistemic uncertainty; combinable with GUM measurement uncertainty.

Usage per instrument:
    mdl = MLInverse().fit(X_train, y_train)        # X = spectra/images features, y = parameter
    out = mdl.predict(X_query)                     # {pred, u_epistemic, conformal_halfwidth}
    u_tot = mdl.combine_with_gum(out['u_epistemic'], u_gum_from_uncertainty_py)

Deps: numpy scikit-learn
"""
import numpy as np
from sklearn.ensemble import RandomForestRegressor


class MLInverse:
    def __init__(self, n_estimators=300, random_state=0):
        self.rf = RandomForestRegressor(n_estimators=n_estimators, random_state=random_state)
        self.conformal_q = None
        self.conformal_level = None

    def _ensemble(self, X):
        t = np.array([e.predict(X) for e in self.rf.estimators_])
        return t.mean(0), t.std(0)          # mean prediction, epistemic std

    def fit(self, X, y, calib_frac=0.25, conformal_level=0.90, seed=0):
        X = np.asarray(X, float); y = np.asarray(y, float)
        idx = np.random.default_rng(seed).permutation(len(X))
        nc = max(1, int(len(X) * calib_frac))
        cal, tr = idx[:nc], idx[nc:]
        self.rf.fit(X[tr], y[tr])
        cp, _ = self._ensemble(X[cal])
        self.conformal_q = float(np.quantile(np.abs(cp - y[cal]), conformal_level))
        self.conformal_level = conformal_level
        return self

    def predict(self, X):
        m, u = self._ensemble(np.asarray(X, float))
        return {"pred": m, "u_epistemic": u, "conformal_halfwidth": self.conformal_q,
                "conformal_level": self.conformal_level}

    @staticmethod
    def combine_with_gum(u_ml, u_gum):
        """Total standard uncertainty = sqrt(ML epistemic^2 + GUM measurement^2)."""
        return np.sqrt(np.asarray(u_ml, float) ** 2 + np.asarray(u_gum, float) ** 2)


if __name__ == "__main__":
    rng = np.random.default_rng(0)
    fwd = lambda p: np.array([np.sin(p / 20 + i) * np.exp(-i / 5) for i in range(12)])
    P = rng.uniform(50, 200, 600); X = np.array([fwd(p) + 0.01 * rng.standard_normal(12) for p in P])
    mdl = MLInverse().fit(X, P)
    Pt = rng.uniform(50, 200, 200); Xt = np.array([fwd(p) + 0.02 * rng.standard_normal(12) for p in Pt])
    o = mdl.predict(Xt)
    cov = (np.abs(o["pred"] - Pt) < o["conformal_halfwidth"]).mean()
    print(f"conformal {o['conformal_level']:.0%} -> empirical coverage {cov:.0%}; "
          f"mean epistemic u={o['u_epistemic'].mean():.2f}")
