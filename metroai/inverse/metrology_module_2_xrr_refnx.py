"""
Metrology inverse module #2 — X-ray Reflectivity (XRR) via refnx
================================================================
Same pattern as OCD module #1, DIFFERENT physics (Parratt/Abeles vs RCWA):
   forward (thin-film reflectivity)  ->  inverse (recover thickness/roughness)
   ->  GUM uncertainty (covariance / Hessian).

VERIFIED in sandbox 2026-06-01:
   thickness  220 A  -> 220.0 +/- 0.09 A (k=1), U(k=2)=0.19 A
   roughness  5.0 A  ->   4.99 +/- 0.02 A (k=1)

WHY THIS MATTERS — the "one module per instrument" framework:
   #1 OCD  (Meent / RCWA)            DONE  (forward + library inverse + MC uncertainty)
   #2 XRR  (refnx / Parratt)         DONE  <-- this file
   #3 TEM  (py4DSTEM / diff Bloch)   planned
   #4 Raman (RamPINN)                planned
Each module = an existing physics/differentiable forward + inverse + GUM uncertainty.
The UNIFYING layer (uncertainty quantification + ISO/GUM traceability across instruments)
is the blue-ocean differentiator — most ML-inverse papers report accuracy but not uncertainty.

Deps:  pip install refnx numpy
"""
import numpy as np
from refnx.reflect import SLD, ReflectModel
from refnx.analysis import Objective, CurveFitter
from refnx.dataset import ReflectDataset


def build_structure(film_thick, film_rough, film_sld=4.5):
    """air | film(thick, rough) | SiO2 | Si  — SLD in 1e-6 A^-2."""
    air = SLD(0.0); film = SLD(film_sld); sio2 = SLD(3.47); si = SLD(2.07)
    return air | film(film_thick, film_rough) | sio2(15, 3) | si(0, 3)


def forward(struct, q=None):
    """Abeles/Parratt thin-film reflectivity R(q)."""
    if q is None:
        q = np.linspace(0.012, 0.25, 120)
    return q, ReflectModel(struct, bkg=1e-7, dq=5.0)(q)


def inverse_with_uncertainty(q, R_meas, dR, init_thick=200.0, init_rough=5.0):
    """Recover film thickness & roughness + GUM (covariance) uncertainty."""
    struct = build_structure(init_thick, init_rough)
    model = ReflectModel(struct, bkg=1e-7, dq=5.0)
    data = ReflectDataset((q, R_meas, dR))
    struct[1].thick.setp(vary=True, bounds=(0.5 * init_thick, 2.0 * init_thick))
    struct[1].rough.setp(vary=True, bounds=(1, 15))
    obj = Objective(model, data)
    CurveFitter(obj).fit("differential_evolution", seed=0, maxiter=20, popsize=12)
    obj.covar()  # populate covariance-based standard errors (GUM 1st-order)
    th, ro = struct[1].thick, struct[1].rough
    return {"thickness": (th.value, th.stderr), "roughness": (ro.value, ro.stderr)}


if __name__ == "__main__":
    true_t, true_r = 220.0, 5.0
    s = build_structure(true_t, true_r)
    q, R = forward(s)
    print(f"[1] XRR forward: R(low-q)={R[0]:.3f}  R(high-q)={R[-1]:.2e}")

    rng = np.random.default_rng(0)
    R_meas = R * (1 + 0.04 * rng.standard_normal(len(q)))   # 4% measurement noise
    dR = 0.04 * R + 1e-12
    res = inverse_with_uncertainty(q, R_meas, dR)
    (t, ut), (r, ur) = res["thickness"], res["roughness"]
    print(f"[3+4] thickness = {t:.1f} +/- {ut:.2f} A (true {true_t}) | "
          f"roughness = {r:.2f} +/- {ur:.2f} A (true {true_r})")
