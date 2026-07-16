# Changelog

All notable changes to MetroAI are documented in this file.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · Versioning: [SemVer](https://semver.org/).

## [Unreleased]

### Fixed
- Aligned the remaining user-facing version strings with the package version 0.8.0
  (landing-page status card / pricing note / footer, KOLAS connector `User-Agent`,
  PROV-O `software_agent` default). The latter two are now derived from
  `metroai.__version__` so they cannot drift again.
- Restored the two status badges removed in the 0.8.0 housekeeping pass, now with
  verified, honest labels: Streamlit demo (Community Cloud — sleeps when idle) and
  Awesome MCP listing (PR punkpeye/awesome-mcp-servers#6980, open / in review as of
  2026-07-16; successor of #6594, closed for being multi-server).

### Added
- This `CHANGELOG.md`.

## [0.8.0] — 2026-07-10

### Added
- **Inverse metrology engine** (`metroai.inverse`): 2 shared cores (GUM uncertainty
  + ML uncertainty) and 11 instrument modules — forward uncertainty propagation and
  inverse parameter estimation with uncertainty.
- **Trustworthy AI policy** (`docs/TRUSTWORTHY_AI.md`): data-origin labels, honest
  metrics, Ed25519 + PROV-O verifiable audit trail, uncertainty quantification.
- Korean summary section, architecture figure, and `CITATION.cff`.

### Changed
- Version unified to 0.8.0 across `pyproject.toml`, `metroai.__version__`,
  `mcp_manifest.json`, and the README badge.
- PyPI publish workflow switched to manual dispatch until trusted publishing is
  configured.

### Removed
- Stale badges and dead demo links (broken Streamlit URL; Awesome MCP #6594 link).

### Tests
- 214 automated tests passing in CI (Python 3.10 / 3.11 / 3.12).

### History note
- Repository history was re-baselined on 2026-07-08 into a single clean-history
  commit (`db06174`). Earlier tags v0.6.0 / v0.7.0 referred to pre-baseline history;
  their feature notes remain in `docs/RELEASE_NOTES_v0.6.0.md` and
  `docs/RELEASE_NOTES_v0.7.0.md`.

## [0.7.0] — 2026-05-22 (pre-baseline)

- Lab-operator journey: domain entry wizard, per-domain KOLAS accreditation guides
  (SEM / TEM / AFM / OCD), KOLAS application-form generator, rule-based SOP gap
  checklist. See `docs/RELEASE_NOTES_v0.7.0.md`.

## [0.6.0] — 2026-05-12 (pre-baseline)

- KOLAS Compliance OS backbone: 6 AI agents, 4 new nano-metrology templates
  (TEM lattice / SEM-EDS / AFM roughness / OCD scatterometry), Ed25519 audit
  signatures + W3C PROV-O provenance, honest-metrics policy.
  See `docs/RELEASE_NOTES_v0.6.0.md`.

[Unreleased]: https://github.com/kyb8801/metroai/compare/v0.8.0...HEAD
[0.8.0]: https://github.com/kyb8801/metroai/releases/tag/v0.8.0
