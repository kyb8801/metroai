"""Domain content module — KOLAS 분야별 가이드 + 신청서 양식 데이터.

v0.7.0 P0-2 (분야별 가이드 콘텐츠) + P0-3 (신청서 자동 작성기) 데이터 소스.
"""

from metroai.content.kolas_guides import (
    DomainGuide,
    get_domain_guide,
    list_domains,
)

__all__ = ["DomainGuide", "get_domain_guide", "list_domains"]
