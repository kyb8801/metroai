# MetroAI v0.7.0 Release Notes

**Release date:** 2026-05-22
**Theme:** Lab-operator journey — entry wizard, KOLAS guides, application form, SOP checklist
**Tests:** 214 passing (Python 3.10 / 3.11 / 3.12 matrix CI)

---

## TL;DR

v0.6.0 was a "compliance OS for KOLAS-accredited labs." Solid backbone — six AI
agents, GUM/MCM uncertainty engine, Ed25519-signed audit trail. But a virtual
user-journey audit on 2026-05-19 revealed v0.6.0 only covered **45%** of what
a real SEM-lab operator wants on their first visit to the web app.

v0.7.0 reorients around the **applicant side** of the KOLAS accreditation
workflow. Four new features land specifically to bridge stages 1–5 of the
seven-stage lab-operator journey, lifting fit from **45% → 68%**.

The four "P0" features:

1. **Domain-specific entry wizard** (SEM/TEM/AFM/OCD/general)
2. **Per-domain KOLAS guides** with applicable standards, accreditation
   process, common nonconformities, and uncertainty budget components
3. **KOLAS application form auto-generator** — ISO 17025-style PDF
4. **Domain-specific SOP rule-based checklist** with gap scoring

The remaining 32% covers stages 6 ("simulation," already partially covered)
and 7 ("end-to-end consulting + on-site evaluator hand-holding") — the second
of which is fundamentally human work that MetroAI can support but not replace.

---

## What's new

### 🔬 Domain-specific entry wizard (P0-1)

Landing page (`app.py`) now asks **"Which instrument are you accrediting?"**
Five cards: SEM / TEM / AFM / OCD / general measurement.

Selecting one routes to a domain dashboard that shows only the standards,
KOLAS process steps, uncertainty templates, and SOP checks relevant to that
domain. Domain selection is persisted in `st.session_state["current_domain"]`
so other pages (SOP gap analyzer, application form) auto-filter accordingly.

**Files:** `app.py` (domain selector section), `metroai/content/domain_page.py`
(common renderer with 6 tabs: 개요 / ISO 표준 / KOLAS 절차 / 부적합 / 도구 / SOP).

### 📚 Per-domain KOLAS guides (P0-2)

Each of the five domains now has structured content covering:

- **Target users** (3+ user types per domain)
- **Applicable ISO/SEMI standards** (4–6 per domain) — every domain references
  ISO/IEC 17025 plus domain-specific standards (ISO 22489 for SEM-EDS,
  ISO 25178-2 for AFM surface roughness, SEMI MF-1789 for OCD, etc.)
- **Six-step KOLAS accreditation process** with typical duration, key
  documents, and common pitfalls per step
- **Common nonconformities** (3–4 per domain) — clause / finding / root
  cause / how MetroAI fixes it
- **MetroAI tools** (4–6 per domain) — mapping from the user's domain
  to the existing measurement templates and dashboards
- **SOP checklist** (10 items per domain) — KOLAS-evaluator-perspective
  common findings
- **Typical uncertainty budget components** (5+ per domain) — pre-built
  budget templates

Content is sourced from publicly available ISO/SEMI standards and the
KOLAS-G-002 / KAB-G-22 public documents. Generic guidance; final KOLAS
submission should always be cross-checked against KAB's latest official
forms and notices.

**Files:** `metroai/content/kolas_guides.py` (5 `DomainGuide` dataclasses).

### 📝 KOLAS application form auto-generator (P0-3)

New page `pages/20_📝_KOLAS_신청서_작성.py` — fill an `OrganizationProfile`
once (organization info, accreditation scope, ISO standards applied, personnel,
equipment, reference standards, environmental control, quality system) → click
"Generate PDF" → ReportLab outputs a 7-section ISO/IEC 17025-style accreditation
application form.

The default profile auto-fills with reasonable domain-specific examples (NIST
SRM-485 for SEM-EDS, Si SRM-640e for TEM, NIST step height standard for AFM,
VLSI Standards CD wafer for OCD, KRISS-traceable Grade K block gauges for the
general calibration domain).

**Disclaimer (also in the page):** The output is a generic ISO 17025-based
template, *not* the precise KAB-F-21 form. Use it as a structured first draft;
copy the content into the latest official KAB form before submission.

**Files:** `metroai/content/application_form.py` (`OrganizationProfile`,
`generate_application_pdf`, `get_default_profile_for_domain`),
`pages/20_📝_KOLAS_신청서_작성.py`.

### 📋 Domain SOP rule-based checklist (P0-4)

The existing SOP Gap Analyzer (`pages/12`) now has a new expander at the top:
"🎯 분야별 SOP 체크리스트 — rule-based 자동 갭 점검 (v0.7 P0-4)".

Select a domain → 10 checkboxes appear with that domain's SOP checklist
items → real-time score (compliant / gaps / percentage) → if there are gaps,
shows the specific gap items and offers a "Add gap list to orchestrator
queue" button.

This converts the abstract concept of "SOP completeness" into a concrete
per-domain rule-based gap report that takes 30 seconds to fill out.

**Files:** updates to `pages/12_📋_SOP_갭_분석.py` (the existing v0.6.0 page
gains the new expander, leaving its v2-spec gap-detail matrix intact below).

---

## Roadmap reorganization (5/19)

v0.6.0's roadmap was outbound-first: cold email → first user → real data
→ feature depth. After the 5/19 user-journey audit, the philosophy shifted
to **user-fit-first**: ship enough of the journey that the first user
doesn't churn on contact, *then* go outbound.

New priority order:

| Priority | Items | Status |
|---|---|---|
| **P0** | 4 user-fit features (this release) | ✅ shipped |
| P1 | Real KOLAS audit data + GBT retrain | pending |
| P2 | HF Spaces migration, Show HN / Reddit, cold email (post-P0) | drafts ready |
| P3 | Consulting SOP guide; LLM-assisted kolas-monitor | needs author |

See `docs/v0.7.0_ROADMAP.md` for the full reorganization.

---

## External signals snapshot (2026-05-22)

After the 5/19 P0 implementation push:

- ✅ Awesome MCP PR [#6594](https://github.com/punkpeye/awesome-mcp-servers/pull/6594)
  open, auto-labeled `has-emoji` / `has-glama` / `valid-name` (AI-agent
  fast-track engaged).
- ✅ Glama Maintenance Grade **B** (License A; "Research & Data" + "AI &
  Machine Learning" tags; verified namespace badge on `kyb8801`).
- ✅ MCPize 4 servers (metroai + kolas-mcp + dart-mcp + ntis-mcp) live with
  rich descriptions.
- ✅ Smithery 4 server listings public.
- ⚠️ Streamlit Cloud demo still has free-tier sleep — HF Spaces migration
  guide in `docs/HF_SPACES_MIGRATION.md` but not yet executed.
- ⚠️ GitHub stars/forks/watchers all at 0 — outbound (Show HN / Reddit /
  LinkedIn) drafts in `docs/PROMO_5_19.md` are user-pending.

---

## Tests

- **214 tests passing** (up from 105 in v0.6.0; +109 new tests for P0 modules).
- Python 3.10 / 3.11 / 3.12 matrix on GitHub Actions.
- New `tests/test_v070_p0_content.py` covers domain guide structural
  invariants, profile defaults, PDF generation, and cross-module consistency.

---

## Honest metrics (unchanged from v0.6.0)

- `kolas-audit-predictor` Gradient Boosting Classifier: **5-fold CV
  accuracy 60.6% ± 3.1pp** on synthetic data (n=2000, 6 features, label noise
  15%), ROC-AUC 0.628 ± 0.038, F1 0.636, Brier 0.241.
- **Real KOLAS audit outcome data is not collected yet.** The 60.6% number
  is a sanity check, not a claim of real-world performance. Real data
  acquisition is P1 of v0.7+ work.
- "Novel within prior-art search," not "world's first."
- All MCP/agent outputs carry `is_live` / `data_origin` flags distinguishing
  live data from cached stubs.

---

## File changes summary

**New files (12):**

- `metroai/content/__init__.py`
- `metroai/content/kolas_guides.py` (1,000+ LOC of domain content)
- `metroai/content/domain_page.py` (common renderer)
- `metroai/content/application_form.py` (ReportLab PDF generator)
- `pages/16_🔬_SEM_분야.py` through `pages/19_📏_OCD_분야.py`
- `pages/20_📝_KOLAS_신청서_작성.py`
- `tests/test_v070_p0_content.py` (109 unit tests)
- `docs/RELEASE_NOTES_v0.7.0.md` (this file)

**Modified files:**

- `app.py` (domain wizard hero section)
- `pages/12_📋_SOP_갭_분석.py` (per-domain SOP checklist expander)
- `README.md` (badges, NEW in v0.7.0 section, 11-page Streamlit catalogue,
  reorganized roadmap table)
- `docs/v0.7.0_ROADMAP.md` (P0/P1/P2/P3 reordered around user fit)

**Lines added:** ~2,500+ LOC + ~250 LOC of new tests.

---

## Acknowledgments

Architecture, code, and content shipped by Yongbeom Kim with the
**Park Soo-yeon** AI advisor persona for the P0 sprint planning, journey
mapping, and the per-domain content scaffolding.

ISO and SEMI standards content is summarized from publicly available
descriptions; nothing in this release reproduces standard text in violation
of copyright. KOLAS-G-002 references are to public guidance documents.

---

## Migration from v0.6.0

No breaking changes. `app.py` gains a new section but preserves the v0.6.0
hero + 6-agent grid. Existing pages 1–15 unchanged in behavior. New pages
16–20 are additive.

For users of the MCP server: no API changes. The same three tools
(`compute_uncertainty`, `apply_template`, `pt_analysis`) remain.

```bash
pip install -e ".[dev,ml]"
streamlit run app.py
```

---

## Links

- GitHub: https://github.com/kyb8801/metroai
- Streamlit demo: https://measurement-uncertainty.streamlit.app
- MCPize: https://mcpize.com/mcp/measurement-uncertainty
- Glama: https://glama.ai/mcp/servers/kyb8801/metroai
- Smithery: https://smithery.ai/servers/kyb8801/metroai
- Awesome MCP PR: https://github.com/punkpeye/awesome-mcp-servers/pull/6594

MIT licensed.
