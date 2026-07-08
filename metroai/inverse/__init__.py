"""
metroai.inverse — Uncertainty-Aware ML Metrology Platform
=========================================================
Core engines (import directly):
    from metroai.inverse import uncertainty   # ① unified GUM (combine/expand/MC/budget)
    from metroai.inverse import ml_inverse     # ②③ ML inverse + ML uncertainty (ensemble+conformal)

Instrument modules call the two cores for consistent uncertainty + AI.
Heavy/optional deps (meent, refnx, pySPM, torch, sklearn) are imported lazily by each
module, so importing this package stays light.

INSTRUMENTS maps a friendly name -> module filename (import on demand):
"""
from . import uncertainty
from . import ml_inverse
from . import measurement_gate      # I5 합부 게이트
from . import gum_posterior_bridge  # I2 GUM<->posterior 브리지

__all__ = ["uncertainty", "ml_inverse", "measurement_gate", "gum_posterior_bridge", "INSTRUMENTS"]

INSTRUMENTS = {
    # name                : module (metroai.inverse.<module>)        grade   data
    "OCD":                  "flagship_v0_forward_inverse",        # ★★★  NIST
    "OCD_autodiff":         "flagship_v1_autodiff_gpu",           # ★★   Meent torch
    "XRR":                  "metrology_module_2_xrr_refnx",       # ★★   synthetic
    "TEM_lattice":          "metrology_module_3_tem_lattice_gpa", # ★★   HRTEM
    "Raman":                "metrology_module_4_raman_quant",     # ★★   synthetic
    "TEM_strain":           "metrology_module_5_tem_gpa_strain",  # ★★   GPA
    "SEM_CD":               "metrology_module_6_sem_cd",          # ★★   synthetic
    "AFM":                  "metrology_module_7_afm_spm_real",    # ★★   real .spm
    "PL_exciton":           "metrology_module_8_pl_exciton",      # ★★★  PhD Valley (real)
    "NSOM":                 "metrology_module_9_nsom_defect_mapping",  # ★★ PhD ipynb
    "Lamb_acoustic":        "metrology_module_10_lamb_acoustic",  # ★★   ARS_TEAS (patent)
}

# OCD deep-dive (accuracy / GPR / noise robustness):
#   flagship_v0_forward_inverse, ocd_depth1_accuracy_cv, ocd_depth2_gpr,
#   ocd_depth2p5_noise, ocd_depth2p6_robust
# Real-data scripts (need downloaded data, run standalone):
#   nist_real_data_inverse, sem_depth_mds3838_segmentation, tem_depth_4dstem_strain_py4dstem
