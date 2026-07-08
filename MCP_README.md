# MetroAI MCP Server — Measurement Uncertainty for AI Agents

> **World's first** measurement uncertainty MCP server.
> GUM-based calculation + Monte Carlo validation + Reverse Uncertainty Engineering.

## What it does

Two tools that any AI agent (Claude, ChatGPT, etc.) can call:

1. **`calculate_uncertainty`** — Input measurement data → Get full GUM uncertainty budget
2. **`pt_analysis`** — Input PT results → Get z-score/En/ζ judgment instantly

## Quick Start

```bash
pip install sympy numpy scipy pyyaml
python -m metroai.mcp_server  # Test locally
```

## Usage with Claude

```
"Calculate the measurement uncertainty for a gauge block calibration 
 with readings [0.10, 0.12, 0.08, 0.11, 0.09] μm 
 and standard uncertainty U=0.05 μm (k=2)"
```

## Supported Templates

| Template | Field | Model |
|---|---|---|
| `gauge_block` | Length (block gauge) | L = dL + d_std + α·L·ΔT |
| `mass` | Mass (weights) | m = dm + d_std + dm_b + dm_a |
| `temperature` | Temperature (thermometer) | T = dT + d_std + stab + uni + res |
| `pressure` | Pressure (gauge) | P = dP + d_std + res + hyst + zero |
| `dc_voltage` | Electrical (DC voltage) | V = dV + d_std + res + stab + temp |

## Standards Compliance

- ISO/IEC Guide 98-3 (GUM)
- GUM Supplement 1 (Monte Carlo)
- ISO/IEC 17025:2017
- KOLAS-G-002 (Korean format)
- ISO 13528 / ISO 17043 (PT)

## Unique Features

- **Reverse Uncertainty Engineering** (novel within prior-art search — not found in GUM Workbench, NIST Uncertainty Machine, or major open-source GUM tools as of 2026-05) — Target CMC → allowable component limits
- **MCM Validation** — 100K Monte Carlo simulations to verify GUM results
- **KOLAS-G-002 format** — Korean accreditation body format support

## License

MIT

## Author

Yongbeom Kim, PhD — Metrology & Semiconductor | kyb8801@gmail.com
