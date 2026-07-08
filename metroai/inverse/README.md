# Uncertainty-Aware Differentiable Metrology Inverse

Forward → inverse → **GUM uncertainty** for semiconductor / thin-film metrology —
one module per instrument, unified by uncertainty quantification.

Built by a measurement scientist (ISO 18516 first-author contributor; KOLAS-accredited
calibration/testing background), so the **uncertainty budget is first-class** — the gap
most ML-inverse work leaves open.

## TL;DR
Not "I know PINN." This is a set of *runnable* inverse solvers across **3 instruments +
real NIST measured data**, each reporting a GUM-style uncertainty. One command reproduces
everything on a normal Windows PC (CPU).

## Verified results (run on CPU, 2026-06)

| Module | Physics / tool | Inverse result | Uncertainty |
|---|---|---|---|
| OCD (library) | RCWA / [Meent](https://github.com/kc-ml2/meent) | energy R+T = 1.000000; CD err < 2 nm. **Non-convex**: naive local → 244 nm, global DE → 388 nm for a true 350 nm; only library matching recovers truth | Monte-Carlo |
| XRR | Parratt / [refnx](https://refnx.readthedocs.io) | thickness 220 → **220.0 Å** (err 0); roughness 5.0 → 4.99 Å | covariance ± 0.09 Å (U, k=2 = 0.19 Å) |
| OCD (autodiff) | RCWA / Meent + PyTorch | gradient descent CD 97 → **119.75 nm** (true 120, err 0.25 nm) | **exact-Jacobian GUM**: u(CD) = 0.96 nm @0.5 % noise · 1.91 @1 % · 3.83 @2 % |
| **NIST real data** | measured scatterometry, 9 dies | mid-CD recovered **107–133 nm** across a focus/exposure matrix | top-5 library spread 1.9–9.2 nm (k=1) |

Real data: NIST **L100P300** angle-resolved scatterometry (Barnes, Henn, Silver),
`data.nist.gov` `ark:/88434/mds2-2290`, CHIPS METIS, public.

## Why this matters
- **Non-convexity, shown in code.** OCD spectrum-fitting has many local minima — a naive
  optimizer and even global differential-evolution miss the truth on the discretized
  landscape; exhaustive library matching (and gradient fitting from a good init) recover it.
  This is *why* production OCD uses libraries.
- **Uncertainty is first-class.** The autodiff module computes the exact sensitivity
  dR/dCD via automatic differentiation — precisely the sensitivity coefficient that
  GUM (ISO/IEC Guide 98-3) needs for a defensible budget. Rarely reported in ML-inverse work.
- **Cross-instrument framework.** Identical forward→inverse→uncertainty pattern holds across
  RCWA (OCD), Parratt (XRR), and FFT (TEM lattice) — different physics, same scaffold.

## OCD Deep Dive — accuracy & noise robustness (★★★)

Beyond "it runs" → "how accurate, and when does it break." On the NIST 467-point library
(known ground-truth widths), measured by cross-validation:

**Absolute accuracy (nearest-neighbour, leave-one-out):**

| width | RMSE | note |
|---|---|---|
| top | 2.9 nm | most optically sensitive |
| bottom | 3.6 nm | |
| middle | 6.0 nm | **least sensitive — sidewall, OCD's known weak axis** |

bias ≈ 0 (±0.2 nm) → unbiased.

**Interpolation vs noise robustness (the key finding):**

| measurement noise | NN | KNN-weighted | GPR |
|---|---|---|---|
| 0 % | 4.4 | 3.5 | **0.19** |
| 0.5 % | 4.4 | **3.5** | 12.8 |
| 1 % | 4.5 | **3.6** | 24.8 |
| 5 % | 4.5 | **3.8** | 128.7 |

GPR's 0.19 nm is an **overfit illusion** on noise-free simulation — it collapses past
12 nm at just 0.5 % measurement noise, worse than nearest-neighbour. **KNN-weighted is
robust across all noise (3.5–3.8 nm).**

**Takeaway:** report the noise-robust method (KNN, ~3.5 nm) for real measurements, not the
noise-free champion (GPR 0.2 nm). This noise-aware honesty — and identifying middle/sidewall
as the least-sensitive axis — is what separates a metrologist's inverse from a naive ML demo.

Scripts: `ocd_depth1_accuracy_cv.py` (LOO accuracy), `ocd_depth2_gpr.py` (interpolation),
`ocd_depth2p5_noise.py` (GPR noise collapse), `ocd_depth2p6_robust.py` (fair NN/KNN/GPR).
Require the NIST CSVs (fetched by `run_flagship.ps1`).

## Reproduce (one command)
```powershell
powershell -ExecutionPolicy Bypass -File .\run_flagship.ps1
```
Installs deps, downloads the NIST real data, runs all four modules.

## Files
| file | what |
|---|---|
| `flagship_v0_forward_inverse.py` | OCD library inverse (synthetic) + non-convexity demo |
| `metrology_module_2_xrr_refnx.py` | XRR inverse + covariance GUM uncertainty |
| `flagship_v1_autodiff_gpu.py` | OCD autodiff inverse + exact-Jacobian GUM uncertainty |
| `nist_real_data_inverse.py` | NIST real-data OCD inverse (9 measured dies) |
| `run_flagship.ps1` | one-shot runner |

## Honest limitations
- Synthetic OCD/XRR are toy-scale (1-D grating, single film); real fab stacks are richer.
- TEM lattice via FFT has good *precision* but pixel-quantization *bias* (precision ≠ accuracy)
  → production needs GPA / Peak-Pairs / 4D-STEM.
- NIST recovered CDs are **not yet cross-checked** against the published regression
  (Barnes & Henn, *Proc. SPIE* 2020, doi:10.1117/12.2551504) — that comparison is the next step.
- "Novel within prior-art search," **not** "world first." OCD/XRR ML-inverse is an active field
  (NIST, IBM, Samsung, Nova); the contribution here is the *uncertainty-integrated,
  reproducible, cross-instrument* framing by a metrology specialist.

## License
Code: MIT. NIST data: NIST open-access license.
