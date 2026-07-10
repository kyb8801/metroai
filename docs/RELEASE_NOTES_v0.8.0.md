# MetroAI v0.8.0 — Release Notes (2026-07-10)

## Highlights
- **Inverse metrology engine**: 2 shared cores (GUM uncertainty + ML uncertainty) + 11 instrument modules — forward uncertainty propagation and inverse parameter estimation with uncertainty
- **Trustworthy AI policy** (`docs/TRUSTWORTHY_AI.md`): data-origin labels, honest metrics, Ed25519 + PROV-O verifiable audit trail, uncertainty quantification
- 214 automated tests passing in CI (Python 3.10 / 3.11 / 3.12)

## Housekeeping
- Version unified to 0.8.0 across `pyproject.toml`, package `__version__`, `mcp_manifest.json`, and README badge
- Removed stale badges: Streamlit demo (unresponsive — Hugging Face Spaces migration planned, Roadmap P2) and Awesome MCP listing (PR still under review)
- PyPI publish workflow switched to manual dispatch until trusted publishing is configured

## History note
Repository history was re-baselined on 2026-07-08 into a single clean-history commit (`db06174`).
Earlier tags v0.6.0 / v0.7.0 referred to pre-baseline history; their feature notes remain in
`docs/RELEASE_NOTES_v0.6.0.md` and `docs/RELEASE_NOTES_v0.7.0.md`.
