"""Unit tests for v0.7.0 P0 content modules.

Coverage:
- metroai.content.kolas_guides — domain guides registry + structure invariants
- metroai.content.application_form — OrganizationProfile defaults + PDF generation
- metroai.content (top-level imports)

These tests prevent regression in the lab-operator journey features
(domain wizard / KOLAS guides / application form / SOP checklist).
"""

from __future__ import annotations

import pytest

from metroai.content import DomainGuide, get_domain_guide, list_domains
from metroai.content.application_form import (
    OrganizationProfile,
    generate_application_pdf,
    get_default_profile_for_domain,
)
from metroai.content.kolas_guides import (
    AFM_GUIDE,
    GENERAL_GUIDE,
    OCD_GUIDE,
    SEM_GUIDE,
    TEM_GUIDE,
)


# ──────────────────────────────────────────────────────────
# Registry + structural invariants
# ──────────────────────────────────────────────────────────


class TestDomainRegistry:
    """`list_domains()` and `get_domain_guide()` invariants."""

    def test_list_domains_returns_five(self):
        domains = list_domains()
        assert len(domains) == 5, "Must have exactly 5 domains (SEM/TEM/AFM/OCD/general)"

    def test_list_domains_keys_are_unique(self):
        keys = [d.key for d in list_domains()]
        assert len(keys) == len(set(keys)), "Domain keys must be unique"

    def test_list_domains_keys_lowercase(self):
        for d in list_domains():
            assert d.key == d.key.lower(), f"key must be lowercase: {d.key}"

    def test_expected_keys_present(self):
        keys = {d.key for d in list_domains()}
        assert keys == {"sem", "tem", "afm", "ocd", "general"}

    @pytest.mark.parametrize("key", ["sem", "tem", "afm", "ocd", "general"])
    def test_get_domain_guide_returns_guide(self, key):
        guide = get_domain_guide(key)
        assert guide is not None
        assert isinstance(guide, DomainGuide)
        assert guide.key == key

    def test_get_domain_guide_unknown_returns_none(self):
        assert get_domain_guide("unknown-domain-xyz") is None

    def test_get_domain_guide_case_insensitive(self):
        assert get_domain_guide("SEM") is not None
        assert get_domain_guide("Sem") is not None


class TestDomainGuideStructure:
    """Each DomainGuide must satisfy minimum content requirements."""

    @pytest.mark.parametrize(
        "guide", [SEM_GUIDE, TEM_GUIDE, AFM_GUIDE, OCD_GUIDE, GENERAL_GUIDE]
    )
    def test_required_string_fields_nonempty(self, guide: DomainGuide):
        assert guide.key
        assert guide.label_ko
        assert guide.label_en
        assert guide.icon
        assert guide.one_liner
        assert len(guide.one_liner) > 20, "one_liner should be informative"

    @pytest.mark.parametrize(
        "guide", [SEM_GUIDE, TEM_GUIDE, AFM_GUIDE, OCD_GUIDE, GENERAL_GUIDE]
    )
    def test_target_users_at_least_three(self, guide: DomainGuide):
        assert len(guide.target_users) >= 3

    @pytest.mark.parametrize(
        "guide", [SEM_GUIDE, TEM_GUIDE, AFM_GUIDE, OCD_GUIDE, GENERAL_GUIDE]
    )
    def test_iso_standards_at_least_three(self, guide: DomainGuide):
        assert len(guide.iso_standards) >= 3
        for s in guide.iso_standards:
            assert "code" in s and s["code"]
            assert "title" in s and s["title"]
            assert "scope" in s and s["scope"]

    @pytest.mark.parametrize(
        "guide", [SEM_GUIDE, TEM_GUIDE, AFM_GUIDE, OCD_GUIDE, GENERAL_GUIDE]
    )
    def test_iso_includes_17025(self, guide: DomainGuide):
        codes = [s["code"] for s in guide.iso_standards]
        assert any("17025" in c for c in codes), "All domains must reference ISO/IEC 17025"

    @pytest.mark.parametrize(
        "guide", [SEM_GUIDE, TEM_GUIDE, AFM_GUIDE, OCD_GUIDE, GENERAL_GUIDE]
    )
    def test_kolas_steps_six(self, guide: DomainGuide):
        assert len(guide.kolas_steps) == 6, "KOLAS journey has six steps"
        orders = [s["order"] for s in guide.kolas_steps]
        assert orders == [1, 2, 3, 4, 5, 6]

    @pytest.mark.parametrize(
        "guide", [SEM_GUIDE, TEM_GUIDE, AFM_GUIDE, OCD_GUIDE, GENERAL_GUIDE]
    )
    def test_kolas_step_fields(self, guide: DomainGuide):
        for step in guide.kolas_steps:
            assert "name" in step
            assert "duration" in step
            assert "key_docs" in step and isinstance(step["key_docs"], list)
            assert "common_pitfalls" in step and isinstance(step["common_pitfalls"], list)
            assert len(step["common_pitfalls"]) >= 1

    @pytest.mark.parametrize(
        "guide", [SEM_GUIDE, TEM_GUIDE, AFM_GUIDE, OCD_GUIDE, GENERAL_GUIDE]
    )
    def test_nonconformities_at_least_three(self, guide: DomainGuide):
        assert len(guide.common_nonconformities) >= 3
        for nc in guide.common_nonconformities:
            assert "clause" in nc and nc["clause"]
            assert "finding" in nc and nc["finding"]
            assert "root_cause" in nc and nc["root_cause"]
            assert "fix" in nc and nc["fix"]

    @pytest.mark.parametrize(
        "guide", [SEM_GUIDE, TEM_GUIDE, AFM_GUIDE, OCD_GUIDE, GENERAL_GUIDE]
    )
    def test_tools_at_least_four(self, guide: DomainGuide):
        assert len(guide.metroai_tools) >= 4
        for t in guide.metroai_tools:
            assert "tool_name" in t and t["tool_name"]
            assert "page" in t and t["page"]
            assert "value" in t and t["value"]

    @pytest.mark.parametrize(
        "guide", [SEM_GUIDE, TEM_GUIDE, AFM_GUIDE, OCD_GUIDE, GENERAL_GUIDE]
    )
    def test_sop_checklist_at_least_ten(self, guide: DomainGuide):
        assert len(guide.sop_checklist) >= 10
        for item in guide.sop_checklist:
            assert isinstance(item, str)
            assert len(item) > 10, "Each SOP item should be specific"

    @pytest.mark.parametrize(
        "guide", [SEM_GUIDE, TEM_GUIDE, AFM_GUIDE, OCD_GUIDE, GENERAL_GUIDE]
    )
    def test_budget_at_least_five(self, guide: DomainGuide):
        assert len(guide.typical_uncertainty_budget) >= 5
        for b in guide.typical_uncertainty_budget:
            # Each budget line should start with a u_ prefix for component name
            assert b.startswith("u_"), f"budget line should start with u_: {b}"


# ──────────────────────────────────────────────────────────
# Domain-specific content sanity checks (smoke tests)
# ──────────────────────────────────────────────────────────


class TestDomainSpecificContent:
    """Domain-specific content sanity — referenced ISO codes match the domain."""

    def test_sem_references_22489(self):
        codes = [s["code"] for s in SEM_GUIDE.iso_standards]
        assert any("22489" in c for c in codes), "SEM must reference ISO 22489 (EDS)"

    def test_tem_references_29301(self):
        codes = [s["code"] for s in TEM_GUIDE.iso_standards]
        assert any("29301" in c for c in codes), "TEM must reference ISO 29301"

    def test_afm_references_25178(self):
        codes = [s["code"] for s in AFM_GUIDE.iso_standards]
        assert any("25178" in c for c in codes), "AFM must reference ISO 25178-2"

    def test_ocd_references_semi_mf1789(self):
        codes = [s["code"] for s in OCD_GUIDE.iso_standards]
        assert any("MF-1789" in c or "MF 1789" in c for c in codes), (
            "OCD must reference SEMI MF-1789"
        )

    def test_general_references_gum(self):
        codes = [s["code"] for s in GENERAL_GUIDE.iso_standards]
        assert any("98-3" in c for c in codes), "general domain must reference Guide 98-3 (GUM)"


# ──────────────────────────────────────────────────────────
# Application form — profile defaults
# ──────────────────────────────────────────────────────────


class TestProfileDefaults:
    """`get_default_profile_for_domain` smoke tests."""

    @pytest.mark.parametrize("domain", ["sem", "tem", "afm", "ocd", "general"])
    def test_default_profile_returns_organization_profile(self, domain):
        p = get_default_profile_for_domain(domain)
        assert isinstance(p, OrganizationProfile)
        assert p.accreditation_domain == domain

    @pytest.mark.parametrize("domain", ["sem", "tem", "afm", "ocd", "general"])
    def test_default_profile_has_organization_name(self, domain):
        p = get_default_profile_for_domain(domain)
        assert p.org_name_ko
        assert p.org_name_en

    @pytest.mark.parametrize("domain", ["sem", "tem", "afm", "ocd", "general"])
    def test_default_profile_has_iso_17025(self, domain):
        p = get_default_profile_for_domain(domain)
        assert any("17025" in s for s in p.iso_standards_applied)

    @pytest.mark.parametrize("domain", ["sem", "tem", "afm", "ocd", "general"])
    def test_default_profile_has_at_least_one_equipment(self, domain):
        p = get_default_profile_for_domain(domain)
        assert len(p.main_equipment_list) >= 1
        for eq in p.main_equipment_list:
            assert "model" in eq
            assert "manufacturer" in eq

    @pytest.mark.parametrize("domain", ["sem", "tem", "afm", "ocd", "general"])
    def test_default_profile_has_at_least_one_reference_standard(self, domain):
        p = get_default_profile_for_domain(domain)
        assert len(p.reference_standards) >= 1
        for r in p.reference_standards:
            assert "name" in r
            assert "source" in r


# ──────────────────────────────────────────────────────────
# Application form — PDF generation
# ──────────────────────────────────────────────────────────


class TestPDFGeneration:
    """`generate_application_pdf` produces a non-trivial PDF."""

    @pytest.mark.parametrize("domain", ["sem", "tem", "afm", "ocd", "general"])
    def test_pdf_for_default_profile(self, domain):
        p = get_default_profile_for_domain(domain)
        pdf_bytes = generate_application_pdf(p)
        # ReportLab PDFs start with %PDF-
        assert pdf_bytes.startswith(b"%PDF-"), "Output must be a valid PDF"
        # Reasonable minimum size for a 7-section form
        assert len(pdf_bytes) > 2000, f"PDF too small ({len(pdf_bytes)} bytes)"

    def test_pdf_for_empty_profile(self):
        """Even an empty profile should generate a valid PDF (with dashes)."""
        p = OrganizationProfile()
        pdf_bytes = generate_application_pdf(p)
        assert pdf_bytes.startswith(b"%PDF-")
        assert len(pdf_bytes) > 1000

    def test_pdf_changes_with_org_name(self):
        """Different org names should produce different PDFs."""
        p1 = OrganizationProfile(org_name_ko="기관 A")
        p2 = OrganizationProfile(org_name_ko="완전히 다른 기관 이름 B")
        pdf1 = generate_application_pdf(p1)
        pdf2 = generate_application_pdf(p2)
        # Total bytes should differ (different name length)
        assert pdf1 != pdf2

    def test_pdf_includes_equipment_when_provided(self):
        """Profile with equipment should produce larger PDF than without."""
        p_with = OrganizationProfile(
            main_equipment_list=[
                {"model": "TEST-001", "manufacturer": "TestCorp", "year": 2024,
                 "calibration_date": "2024-01-01", "traceability": "NIST"},
                {"model": "TEST-002", "manufacturer": "TestCorp", "year": 2024,
                 "calibration_date": "2024-02-01", "traceability": "NIST"},
            ]
        )
        p_without = OrganizationProfile()
        pdf_with = generate_application_pdf(p_with)
        pdf_without = generate_application_pdf(p_without)
        assert len(pdf_with) > len(pdf_without)


# ──────────────────────────────────────────────────────────
# Cross-module consistency
# ──────────────────────────────────────────────────────────


class TestCrossModuleConsistency:
    """Consistency between guides and application form."""

    @pytest.mark.parametrize("domain", ["sem", "tem", "afm", "ocd", "general"])
    def test_profile_iso_standards_subset_of_guide_or_general(self, domain):
        """Default profile ISO standards should overlap with the guide's ISO standards."""
        p = get_default_profile_for_domain(domain)
        guide = get_domain_guide(domain)
        guide_codes = {s["code"] for s in guide.iso_standards}
        profile_codes = set(p.iso_standards_applied)
        # At least one overlap (17025 minimum)
        overlap = guide_codes & profile_codes
        assert len(overlap) >= 1, (
            f"Profile for {domain} should reference at least one of the guide's ISO standards"
        )

    @pytest.mark.parametrize("domain", ["sem", "tem", "afm", "ocd", "general"])
    def test_guide_tools_reference_existing_pages(self, domain):
        """metroai_tools.page should reference real page slugs (not validated against fs, just format)."""
        guide = get_domain_guide(domain)
        for tool in guide.metroai_tools:
            page = tool["page"]
            # Must contain a digit (page number) and an underscore (separator)
            assert any(c.isdigit() for c in page), f"page slug should have a number: {page}"
            assert "_" in page or page.isdigit()
