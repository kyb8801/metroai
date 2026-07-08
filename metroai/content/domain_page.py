"""분야별 dashboard 페이지 공통 렌더러 — v0.7.0 P0-1, P0-2.

SEM / TEM / AFM / OCD 4개 페이지가 동일 layout 으로 분야별 데이터를 표시.
"""

from __future__ import annotations

import streamlit as st

from metroai.content.kolas_guides import DomainGuide, get_domain_guide


_CSS = """
<style>
.dom-hero {
    background: linear-gradient(135deg, #1E40AF 0%, #06B6D4 100%);
    color: white;
    padding: 2.2rem 2rem;
    border-radius: 12px;
    margin-bottom: 1.5rem;
}
.dom-hero h1 { color: white; font-size: 2.1rem; margin: 0 0 0.6rem 0; letter-spacing: -0.02em; }
.dom-hero p { color: rgba(255,255,255,0.92); font-size: 1.05rem; margin: 0; }
.dom-section-h {
    font-size: 1.2rem; font-weight: 600; color: #0F172A;
    margin: 2rem 0 0.9rem 0; letter-spacing: -0.01em;
}
.dom-card {
    background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px;
    padding: 1rem 1.25rem; margin-bottom: 0.7rem;
}
.dom-card.iso { border-left: 4px solid #1E40AF; }
.dom-card.step { border-left: 4px solid #06B6D4; }
.dom-card.nc { border-left: 4px solid #F59E0B; }
.dom-card.tool { border-left: 4px solid #10B981; }
.dom-mono {
    font-family: JetBrains Mono, monospace; font-size: 0.82rem;
    color: #1E40AF; font-weight: 600;
}
.dom-budget {
    background: #F8FAFC; padding: 0.7rem 1rem; border-radius: 6px;
    font-family: JetBrains Mono, monospace; font-size: 0.83rem;
    color: #1E293B; margin-bottom: 0.4rem;
}
.dom-checklist {
    background: rgba(6, 182, 212, 0.06); border-left: 3px solid #06B6D4;
    padding: 0.55rem 0.9rem; border-radius: 6px;
    font-size: 0.88rem; color: #1E293B; margin-bottom: 0.3rem;
}
</style>
"""


def render_domain_page(domain_key: str) -> None:
    """주어진 분야 key 로 dashboard 전체 렌더."""
    guide: DomainGuide | None = get_domain_guide(domain_key)
    if guide is None:
        st.error(f"Unknown domain: {domain_key}")
        return

    # session state 에 현재 분야 저장 (다른 페이지가 활용 가능)
    st.session_state["current_domain"] = domain_key

    st.markdown(_CSS, unsafe_allow_html=True)

    # Hero
    st.markdown(
        f"""
        <div class='dom-hero'>
          <h1>{guide.icon} {guide.label_ko}</h1>
          <p>{guide.one_liner}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        ["📌 개요", "📚 ISO 표준", "🗓 KOLAS 절차", "⚠️ 흔한 부적합", "🧰 MetroAI 도구", "📋 SOP 체크"]
    )

    # ── Tab 1: 개요
    with tab1:
        st.markdown("<div class='dom-section-h'>주요 사용자</div>", unsafe_allow_html=True)
        for u in guide.target_users:
            st.markdown(f"- {u}")

        st.markdown("<div class='dom-section-h'>전형적 측정 불확도 Budget</div>", unsafe_allow_html=True)
        for line in guide.typical_uncertainty_budget:
            st.markdown(f"<div class='dom-budget'>{line}</div>", unsafe_allow_html=True)

        st.info(
            "💡 본 가이드는 ISO 표준 + KOLAS 공개 문서 (KOLAS-G-002 등) 기반 generic 콘텐츠입니다. "
            "실제 인정 신청 시 KAB (knab.go.kr) 의 최신 양식·고시를 직접 확인하세요."
        )

    # ── Tab 2: ISO 표준
    with tab2:
        st.markdown(
            f"<div class='dom-section-h'>{guide.label_ko} 에 적용되는 표준 ({len(guide.iso_standards)} 종)</div>",
            unsafe_allow_html=True,
        )
        for s in guide.iso_standards:
            st.markdown(
                f"<div class='dom-card iso'>"
                f"<span class='dom-mono'>{s['code']}</span>"
                f"<div style='margin-top:0.3rem;color:#0F172A;font-weight:500;'>{s['title']}</div>"
                f"<small style='color:#475569;'>{s['scope']}</small>"
                f"</div>",
                unsafe_allow_html=True,
            )

    # ── Tab 3: KOLAS 절차
    with tab3:
        st.markdown(
            f"<div class='dom-section-h'>KOLAS 인정 절차 ({len(guide.kolas_steps)} 단계)</div>",
            unsafe_allow_html=True,
        )
        for step in guide.kolas_steps:
            pitfalls_html = "".join([f"<li>{p}</li>" for p in step["common_pitfalls"]])
            docs_html = " · ".join([f"<span class='dom-mono'>{d}</span>" for d in step["key_docs"]])
            st.markdown(
                f"<div class='dom-card step'>"
                f"<div style='display:flex;justify-content:space-between;'>"
                f"<span style='font-weight:600;color:#0F172A;font-size:1.05rem;'>"
                f"단계 {step['order']} · {step['name']}</span>"
                f"<span class='dom-mono' style='color:#06B6D4;'>{step['duration']}</span>"
                f"</div>"
                f"<div style='margin-top:0.5rem;'><strong style='font-size:0.85rem;color:#475569;'>"
                f"핵심 문서:</strong> {docs_html}</div>"
                f"<div style='margin-top:0.5rem;'><strong style='font-size:0.85rem;color:#475569;'>"
                f"흔한 함정:</strong></div>"
                f"<ul style='margin:0.3rem 0 0 1.2rem;color:#1E293B;font-size:0.88rem;'>{pitfalls_html}</ul>"
                f"</div>",
                unsafe_allow_html=True,
            )

    # ── Tab 4: 흔한 부적합
    with tab4:
        st.markdown(
            f"<div class='dom-section-h'>흔한 부적합 사례 ({len(guide.common_nonconformities)} 건) — KOLAS 평가관 관점</div>",
            unsafe_allow_html=True,
        )
        for nc in guide.common_nonconformities:
            st.markdown(
                f"<div class='dom-card nc'>"
                f"<span class='dom-mono' style='color:#F59E0B;'>{nc['clause']}</span>"
                f"<div style='margin-top:0.4rem;color:#0F172A;font-weight:500;'>"
                f"부적합: {nc['finding']}</div>"
                f"<div style='margin-top:0.4rem;color:#475569;font-size:0.88rem;'>"
                f"<strong>근본 원인:</strong> {nc['root_cause']}</div>"
                f"<div style='margin-top:0.4rem;color:#10B981;font-size:0.88rem;'>"
                f"<strong>MetroAI 해결:</strong> {nc['fix']}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

    # ── Tab 5: MetroAI 도구
    with tab5:
        st.markdown(
            f"<div class='dom-section-h'>{guide.label_ko} 분야에 즉시 활용 가능한 MetroAI 도구</div>",
            unsafe_allow_html=True,
        )
        for tool in guide.metroai_tools:
            st.markdown(
                f"<div class='dom-card tool'>"
                f"<span style='font-weight:600;color:#0F172A;font-size:1.0rem;'>{tool['tool_name']}</span>"
                f"<div style='margin-top:0.3rem;color:#475569;font-size:0.88rem;'>{tool['value']}</div>"
                f"<div style='margin-top:0.4rem;'>"
                f"<span class='dom-mono' style='color:#06B6D4;'>→ 사이드바 \"{tool['page'].replace('_', ' ')}\"</span>"
                f"</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

    # ── Tab 6: SOP 체크리스트
    with tab6:
        st.markdown(
            f"<div class='dom-section-h'>{guide.label_ko} 특화 SOP 체크리스트 ({len(guide.sop_checklist)} 항목)</div>",
            unsafe_allow_html=True,
        )
        st.caption(
            "각 항목이 귀하의 SOP 에 정량적으로 명시되어 있는지 점검하세요. "
            "체크 결과를 SOP 갭 분석 페이지 (12_📋_SOP_갭_분석) 에 입력하면 위험 점수 산출."
        )
        for i, item in enumerate(guide.sop_checklist, 1):
            checked = st.checkbox(f"{i}. {item}", key=f"{domain_key}_sop_{i}")
            if checked:
                st.markdown(
                    f"<div class='dom-checklist'>✅ {item}</div>",
                    unsafe_allow_html=True,
                )

        # 진행률
        total = len(guide.sop_checklist)
        done = sum(
            1 for i in range(1, total + 1)
            if st.session_state.get(f"{domain_key}_sop_{i}", False)
        )
        st.progress(done / total if total > 0 else 0.0)
        st.caption(f"진행률: {done} / {total} ({100*done/total:.0f}%)")

    st.markdown("---")
    st.caption(
        f"본 페이지는 v0.7.0 P0-1·P0-2 기반 분야별 dashboard 입니다. "
        f"콘텐츠 출처: ISO 표준 공개 정보 + KOLAS-G-002 + practitioner-informed. "
        f"current_domain={domain_key}"
    )
