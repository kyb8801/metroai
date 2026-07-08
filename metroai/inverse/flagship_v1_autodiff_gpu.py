"""
flagship_v1 — Gradient-based OCD inverse via Meent PyTorch autodiff   [RUN ON YOUR PC]
=====================================================================================
v0 (flagship_v0_forward_inverse.py) used DISCRETE library lookup: robust but quantized,
no gradient. v1 uses Meent's CORE advantage:
    VECTOR modeling (continuous CD) + AUTOMATIC DIFFERENTIATION
  -> CD recovered by gradient descent in continuous space
  -> analytic sensitivity (Jacobian, exact via AD) -> GUM uncertainty budget.

The Jacobian-based uncertainty is the differentiator: autodiff gives the EXACT
sensitivity coefficient dR/dCD that GUM (ISO/IEC Guide 98-3) needs — most ML-OCD
work never reports this.

Based on the official Meent OCD example:
  github.com/kc-ml2/meent/blob/main/examples/ocd/arxiv_ocd_optimize.py
  github.com/kc-ml2/meent/blob/main/examples/vector_1d.py

RUN (Windows PowerShell / cmd):
  pip install meent torch
  python flagship_v1_autodiff_gpu.py

NOTES
  * Meent eigendecomposition runs on CPU even with CUDA (known limitation), so GPU
    mainly helps at higher Fourier order / batched wavelengths.
  * OCD spectrum-fitting is non-convex (see v0): gradient descent can stall in a local
    min from a bad init. v1 uses a reasonable init; for production use multi-start or
    warm-start from the v0 library match, then refine with this gradient step.
  * If the FIRST run throws on the ucell format, capture the traceback — only a
    minor API alignment to your installed meent version is expected.
"""
import numpy as np
import torch
import meent

torch.manual_seed(0)
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"device: {device} | torch {torch.__version__} | cuda available: {torch.cuda.is_available()}")

WLS    = list(range(500, 901, 50))   # 9-point reflectance spectrum (nm)
PERIOD = [300.0, 300.0]
FTO    = [5, 0]                      # 1D grating in x
N_SI   = 3.48
THICK  = [200.0, 100000.0]           # grating layer + (thick) substrate layer


def spectrum(cd):
    """0th-order reflectance spectrum of a 1D Si grating.
    cd = line width (length_x); differentiable through Meent vector modeling."""
    spec = []
    for wl in WLS:
        mee = meent.call_mee(backend=2, thickness=THICK, period=PERIOD, fto=FTO,
                             n_top=1.0, n_bot=1.0, wavelength=float(wl), pol=0.5)
        # vector modeling: one Si rectangle of width `cd` on an air base; Si substrate below
        mee.ucell = [
            [1.0, [['rectangle', 150.0, 150.0, cd, 300.0, N_SI, 0.0, 0.0, 0.0]]],
            [N_SI, []],
        ]
        res = mee.conv_solve().res
        de_ri = res.de_ri
        xc, yc = np.array(de_ri.shape) // 2
        spec.append(de_ri[xc, yc])
    out = torch.stack(spec)
    return out.real if torch.is_complex(out) else out


# ---------- ground-truth "measurement" ----------
cd_true = torch.tensor(120.0)
with torch.no_grad():
    target = spectrum(cd_true)

# ---------- inverse: autodiff gradient descent from a deliberately off init ----------
cd = torch.tensor(95.0, requires_grad=True)
opt = torch.optim.Adam([cd], lr=2.0)
print("\n[v1 autodiff gradient descent]")
for step in range(80):
    opt.zero_grad()
    loss = torch.norm(spectrum(cd) - target)
    loss.backward()
    opt.step()
    if step % 20 == 0 or step == 79:
        g = cd.grad.item() if cd.grad is not None else float("nan")
        print(f"  step {step:3d} | CD={cd.item():7.2f} nm | loss={loss.item():.3e} | grad={g:+.3e}")
print(f"=> true CD={cd_true.item():.1f} | recovered CD={cd.item():.2f} | err={abs(cd.item()-cd_true.item()):.2f} nm")

# ---------- GUM uncertainty via analytic sensitivity (Jacobian from AD) ----------
print("\n[GUM uncertainty from exact autodiff Jacobian dR/dCD]")
cd_hat = cd.detach().clone().requires_grad_(True)
J = torch.autograd.functional.jacobian(spectrum, cd_hat)      # exact d(spectrum)/d(CD)
sens = float(torch.linalg.norm(J.flatten()))                  # overall sensitivity
for noise in [0.005, 0.01, 0.02]:
    u_cd = noise * np.sqrt(len(WLS)) / sens if sens > 0 else float("nan")   # 1st-order GUM
    print(f"  reflectance noise={noise*100:4.1f}%  ->  u(CD)={u_cd:.3f} nm (k=1) | U(k=2)={2*u_cd:.3f} nm  [sensitivity |J|={sens:.3e}]")

print("\nDone. v1 = continuous gradient inverse + exact-sensitivity GUM budget (Meent's autodiff edge).")
