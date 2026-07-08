"""분야별 KOLAS 인정 가이드 콘텐츠 — v0.7.0 P0-2.

각 분야 (SEM, TEM, AFM, OCD, general) 의 KOLAS 인정 절차, 적용 ISO 표준,
흔한 부적합 사례, MetroAI 제공 도구 mapping 을 데이터로 보유.

콘텐츠 출처:
- ISO/IEC 17025, ISO/IEC 17034, ISO 13528, ISO 17043 (공개 표준)
- KOLAS-G-002, KAB-G-22 (KOLAS 공개 문서)
- ISO 22489 (SEM-EDS), ISO 25178-2 (AFM), SEMI MF-1789 (OCD)
- practitioner-informed 일반 KOLAS 인정 lab 실무 경험

⚠️ 본 콘텐츠는 공개 정보 기반 generic 가이드입니다. 실제 인정 신청 시
   KAB (knab.go.kr) 의 최신 양식·고시·KOLAS-G-002 를 직접 확인하세요.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DomainGuide:
    """분야별 KOLAS 가이드 데이터 컨테이너."""

    key: str  # 'sem', 'tem', 'afm', 'ocd', 'general'
    label_ko: str
    label_en: str
    icon: str
    one_liner: str
    target_users: list[str]
    iso_standards: list[dict]  # [{code, title, scope}, ...]
    kolas_steps: list[dict]  # [{order, name, duration, key_docs, common_pitfalls}, ...]
    common_nonconformities: list[dict]  # [{clause, finding, root_cause, fix}, ...]
    metroai_tools: list[dict]  # [{tool_name, page, value}, ...]
    sop_checklist: list[str]  # 분야 특이 SOP 점검 포인트
    typical_uncertainty_budget: list[str]  # 불확도 budget 의 typical 성분


# ──────────────────────────────────────────────────────────
# SEM (Scanning Electron Microscope)
# ──────────────────────────────────────────────────────────
SEM_GUIDE = DomainGuide(
    key="sem",
    label_ko="SEM (주사전자현미경)",
    label_en="Scanning Electron Microscope",
    icon="🔬",
    one_liner="반도체 wafer, 미세입자, MEMS 표면을 nm 분해능으로 관찰·정량.",
    target_users=[
        "반도체 FAB 의 inline metrology lab",
        "재료 분석 lab (입자 크기, 표면 morphology)",
        "MEMS / display 부품 lab",
        "KRISS / 출연연 산하 표면 분석실",
    ],
    iso_standards=[
        {
            "code": "ISO/IEC 17025:2017",
            "title": "시험·교정 기관 일반 요구사항",
            "scope": "전 분야 공통. SEM 측정도 7.6 항 측정 불확도 산출 필수.",
        },
        {
            "code": "ISO 22489:2016",
            "title": "Microbeam analysis — Quantitative point analysis by energy-dispersive X-ray spectrometry (EDS)",
            "scope": "SEM-EDS 정량 분석의 표준 절차. ZAF 보정 + 표준시료 매칭 의무.",
        },
        {
            "code": "ISO 16700:2016",
            "title": "Microbeam analysis — Scanning electron microscopy — Guidelines for calibrating image magnification",
            "scope": "SEM magnification 교정 표준. 표준 격자 시료 (예: 463 nm pitch) 사용.",
        },
        {
            "code": "ISO 18516:2019",
            "title": "Surface chemical analysis — Auger electron spectroscopy and X-ray photoelectron spectroscopy — Determination of lateral resolution, analysis area, and sample area viewed by the analyser",
            "scope": "공간 분해능 정량 표준.",
        },
        {
            "code": "ASTM E1508:2012a",
            "title": "Standard Guide for Quantitative Analysis by Energy-Dispersive Spectroscopy",
            "scope": "EDS 정량 분석 가이드. ISO 22489 와 상호 참조.",
        },
    ],
    kolas_steps=[
        {
            "order": 1,
            "name": "사전 검토 (Self-assessment)",
            "duration": "2-4주",
            "key_docs": ["KOLAS-G-002", "KAB-G-22", "ISO/IEC 17025:2017 7장"],
            "common_pitfalls": [
                "SEM-EDS 정량 분석을 '시험 분야' 와 '교정 분야' 중 어디로 신청할지 혼동",
                "EDS 표준시료 출처 (NIST SRM, BAM-S005 등) 미확보",
            ],
        },
        {
            "order": 2,
            "name": "인정 신청서 작성 (KAB-F-21)",
            "duration": "1-2주",
            "key_docs": ["KAB-F-21 신청서 양식", "SOP 전수 (각 측정마다)", "교정 인증서 사본"],
            "common_pitfalls": [
                "측정 범위 (예: '1 nm ~ 100 μm magnification') 와 측정 불확도 (typical 5-10%) 의 일관성 확인 안 함",
                "SEM 본체 + EDS detector + 표준시료 + standard reference 의 traceability chain 누락",
            ],
        },
        {
            "order": 3,
            "name": "서류 평가",
            "duration": "4-6주",
            "key_docs": ["평가팀 의견서 응답 자료"],
            "common_pitfalls": [
                "EDS 정량 분석의 detection limit (typical 0.1 wt%) 명시 안 함",
                "ZAF 보정 알고리즘의 software 출처 (예: Oxford INCA, Bruker Esprit) 명시 누락",
            ],
        },
        {
            "order": 4,
            "name": "현장 평가 (방문 1-2일)",
            "duration": "1-2일 + 사후 30일",
            "key_docs": ["live demo 측정 결과", "평가관 질의 응답"],
            "common_pitfalls": [
                "live demo 에서 표준시료 (예: NIST SRM-485 Au-Cu) 의 reference 값 vs 측정 값 정직하지 않게 보고",
                "operator 의 ISO 22489 quantitative analysis 절차 숙지 부족",
            ],
        },
        {
            "order": 5,
            "name": "부적합 시정 + 인정 결정",
            "duration": "4-12주",
            "key_docs": ["부적합 시정 보고서", "인정 결정서"],
            "common_pitfalls": [
                "주요 부적합 (major NC) 30일 내 시정 의무 미준수",
                "관찰사항 (observation) 무시 → 다음 정기심사 시 major 로 격상",
            ],
        },
        {
            "order": 6,
            "name": "사후 정기심사 (3년 주기)",
            "duration": "3년 cycle",
            "key_docs": ["연간 내부 audit 기록", "PT 참가 결과 (ISO 17043)"],
            "common_pitfalls": [
                "ISO 17043 PT (proficiency testing) 참가 누락 — KOLAS 가 매년 권장",
                "z'-score > 2 인 PT 결과의 시정 조치 기록 부재",
            ],
        },
    ],
    common_nonconformities=[
        {
            "clause": "ISO/IEC 17025 7.6.2",
            "finding": "측정 불확도 budget 에 EDS 표준시료의 인증 불확도가 빠짐",
            "root_cause": "NIST SRM 인증서의 U 를 budget 에 합산하지 않음. operator 가 '표준이 정확'하다고 가정.",
            "fix": "MetroAI SEM-EDS 템플릿이 표준시료 U 를 input 으로 받아 GUM budget 에 자동 합산.",
        },
        {
            "clause": "ISO/IEC 17025 6.4.5",
            "finding": "SEM magnification 교정 주기 명시 안 됨",
            "root_cause": "internal SOP 에 '정기 교정' 만 명시. 주기 (예: 6개월) 가 정량적이지 않음.",
            "fix": "MetroAI schedule 에이전트가 magnification 교정 주기를 자동 산정 + 만료 60/30/7일 알림.",
        },
        {
            "clause": "ISO 22489 7.3",
            "finding": "ZAF 보정 software 의 버전 + parameter 가 보고서에 없음",
            "root_cause": "Oxford / Bruker GUI 가 자동 적용 → operator 가 인식 못 함.",
            "fix": "MetroAI 가 인증서 generator 에 software · version · parameter snapshot 자동 포함.",
        },
        {
            "clause": "ISO/IEC 17025 7.8.5",
            "finding": "EDS spectrum 의 peak overlap (예: S Kα vs Mo Lα) 처리 방법 미문서화",
            "root_cause": "operator 가 software 의 default deconvolution 사용. SOP 에 명시 없음.",
            "fix": "분야별 SOP checklist (P0-4) 에 'peak overlap deconvolution 방법' 항목 포함.",
        },
    ],
    metroai_tools=[
        {
            "tool_name": "SEM-EDS 측정 불확도 템플릿",
            "page": "1_📐_불확도_계산",
            "value": "ISO 22489 의 quantitative analysis 절차 + GUM budget 자동 계산. ZAF + 표준시료 U 합산.",
        },
        {
            "tool_name": "감사 위험 시뮬레이션",
            "page": "14_🎯_감사_위험_상세",
            "value": "SEM 분야 시나리오 (SOP 완성도, 인력 회전율, PT 결과) 입력 → 다음 정기심사 부적합 위험 예측.",
        },
        {
            "tool_name": "SOP 갭 분석 (SEM 모드)",
            "page": "12_📋_SOP_갭_분석",
            "value": "SEM 특화 checklist 30 항목 자동 평가. SOP 업로드 → 갭 리스트.",
        },
        {
            "tool_name": "인증서 / 인력 / 일정",
            "page": "15_📅_인증서_인력_일정",
            "value": "magnification 교정·EDS 표준시료 갱신·operator 자격 갱신 자동 추적.",
        },
        {
            "tool_name": "KOLAS 인정 신청서 자동 작성",
            "page": "20_📝_KOLAS_신청서_작성",
            "value": "조직 프로필 1회 입력 → ISO 17025 generic 신청 양식 PDF 출력 (KAB-F-21 양식과 유사).",
        },
    ],
    sop_checklist=[
        "SEM 본체의 가속 전압 (kV) 범위 + 작동 조건 명시",
        "EDS detector 의 silicon drift detector spec + active area 명시",
        "표준시료 (예: NIST SRM-485 Au-Cu) 출처 + 인증 불확도 기재",
        "magnification 교정 주기 (정량적, 예: 6개월) + 교정 시 사용 표준 (예: 463 nm pitch grating)",
        "EDS quantitative analysis 의 ZAF 보정 software · version · parameter 명시",
        "EDS detection limit (typical 0.1 wt%) 정량 기재",
        "peak overlap deconvolution 방법 + 알고리즘",
        "표준시료 측정 vs 인증값 비교 (control chart, ISO 8258)",
        "operator 의 ISO 22489 training 기록",
        "측정 결과 보고서의 측정 불확도 (k=2, 95% CI) 표기 의무",
    ],
    typical_uncertainty_budget=[
        "u_ref: 표준시료 인증 불확도 (NIST SRM, typical 0.1-1.0%)",
        "u_repeat: 반복 측정 표준편차 (10회 측정, ISO 5725)",
        "u_drift: 측정 중 beam current drift (typical 0.5%/hr)",
        "u_zaf: ZAF 보정 알고리즘의 systematic 불확도 (typical 2-5%)",
        "u_overlap: peak overlap deconvolution 의 불확도 (typical 1-3%, peak 별)",
        "u_count: counting statistics (Poisson, dead-time corrected)",
        "u_mag: magnification 교정 불확도 (typical 0.5-1%)",
    ],
)


# ──────────────────────────────────────────────────────────
# TEM (Transmission Electron Microscope)
# ──────────────────────────────────────────────────────────
TEM_GUIDE = DomainGuide(
    key="tem",
    label_ko="TEM (투과전자현미경)",
    label_en="Transmission Electron Microscope",
    icon="⚛️",
    one_liner="원자 격자상수, 결정 구조, 박막 조성을 sub-Å 분해능으로 분석.",
    target_users=[
        "반도체 R&D 의 박막 분석 lab",
        "재료 R&D (격자상수, dislocation, grain boundary)",
        "출연연 (KIST, KAIST, KBSI) 의 ultra-high resolution lab",
        "촉매 / 나노입자 분석 lab",
    ],
    iso_standards=[
        {
            "code": "ISO/IEC 17025:2017",
            "title": "시험·교정 기관 일반 요구사항",
            "scope": "공통.",
        },
        {
            "code": "ISO 29301:2017",
            "title": "Microbeam analysis — Analytical electron microscopy — Methods for calibrating image magnification using reference materials with periodic structures",
            "scope": "TEM magnification 교정 방법. 격자상수 known 인 SRM (예: Si 5.4310 Å) 사용.",
        },
        {
            "code": "ISO 14709-1:2002",
            "title": "Microbeam analysis — TEM — Method for thin-film analysis",
            "scope": "TEM 박막 두께·조성 측정 표준.",
        },
        {
            "code": "ASTM E2142-08",
            "title": "Standard Test Methods for Rating and Classifying Inclusions in Steel using the Scanning Electron Microscope",
            "scope": "SEM 위주이나 TEM micro-inclusion 분석에도 reference.",
        },
    ],
    kolas_steps=[
        {
            "order": 1,
            "name": "사전 검토",
            "duration": "2-4주",
            "key_docs": ["KOLAS-G-002", "ISO 29301", "ISO 14709-1"],
            "common_pitfalls": [
                "TEM 시료 준비 (FIB lift-out / ion milling) 의 reproducibility 미문서화",
                "격자상수 측정의 indexing 절차 SOP 부재",
            ],
        },
        {
            "order": 2,
            "name": "인정 신청서 작성",
            "duration": "1-2주",
            "key_docs": ["측정 범위 (예: 격자상수 1-10 Å, atomic-resolution imaging)"],
            "common_pitfalls": [
                "측정 불확도 (typical 격자상수의 0.5-1%) 의 budget 미흡",
                "표준 시료 (Si SRM, 격자상수 5.4310 Å) 의 traceability chain 누락",
            ],
        },
        {
            "order": 3,
            "name": "서류 평가",
            "duration": "4-6주",
            "key_docs": ["평가팀 의견서"],
            "common_pitfalls": [
                "TEM 시료 준비의 artifact (ion damage, amorphization) 평가 방법 미명시",
                "image drift correction algorithm 의 정량 효과 분석 누락",
            ],
        },
        {
            "order": 4,
            "name": "현장 평가",
            "duration": "1-2일",
            "key_docs": ["live demo (Si 격자상수 측정)", "evaluator Q&A"],
            "common_pitfalls": [
                "Si 표준 시료의 격자상수 측정 demo 에서 평가관 입회 의무화 못 함",
                "operator 의 Cs corrector tuning 절차 미숙",
            ],
        },
        {
            "order": 5,
            "name": "부적합 시정 + 인정",
            "duration": "4-12주",
            "key_docs": ["시정 보고서"],
            "common_pitfalls": [
                "TEM 분야의 비표준 측정 (HRTEM dynamical scattering) 에 대한 평가관 의견 응답 지연",
            ],
        },
        {
            "order": 6,
            "name": "사후 정기심사",
            "duration": "3년 cycle",
            "key_docs": ["PT 참가 결과", "Cs corrector 교정 기록"],
            "common_pitfalls": [
                "TEM 의 ISO 17043 PT provider 매우 적음 (NIST, KRISS 일부). 대안 inter-lab comparison 기록 필수.",
            ],
        },
    ],
    common_nonconformities=[
        {
            "clause": "ISO/IEC 17025 7.6.2",
            "finding": "격자상수 측정 불확도 budget 에 사선 보정 (tilt correction) 의 systematic 불확도 누락",
            "root_cause": "operator 가 software 의 auto-correction 사용. SOP 에 budget 항목 없음.",
            "fix": "MetroAI TEM 격자상수 템플릿이 tilt angle + correction algorithm 불확도를 input 으로.",
        },
        {
            "clause": "ISO 29301 8.2",
            "finding": "magnification 교정에 single-point Si standard 만 사용 (multi-point 권장)",
            "root_cause": "표준시료 1종만 보유.",
            "fix": "MetroAI 가이드가 multi-point 표준 (Si + Au + SrTiO3) 보유 권장.",
        },
        {
            "clause": "ISO/IEC 17025 6.4.5",
            "finding": "Cs corrector 의 정기 교정 (1년 주기) 기록 부재",
            "root_cause": "manufacturer 서비스 계약에 포함된다고 가정.",
            "fix": "MetroAI schedule 에이전트에 Cs corrector 교정 추가.",
        },
    ],
    metroai_tools=[
        {
            "tool_name": "TEM 격자상수 측정 템플릿",
            "page": "1_📐_불확도_계산",
            "value": "Bragg 법칙 + tilt correction + drift correction 의 합성 불확도 자동 budget.",
        },
        {
            "tool_name": "감사 위험 시뮬레이션",
            "page": "14_🎯_감사_위험_상세",
            "value": "TEM 시나리오 입력 → 부적합 위험 예측.",
        },
        {
            "tool_name": "SOP 갭 분석 (TEM 모드)",
            "page": "12_📋_SOP_갭_분석",
            "value": "TEM 시료 준비, Cs corrector tuning, indexing 의 SOP 검사.",
        },
        {
            "tool_name": "KOLAS 인정 신청서 자동 작성",
            "page": "20_📝_KOLAS_신청서_작성",
            "value": "TEM 측정 범위에 맞게 신청 양식 자동 채움.",
        },
    ],
    sop_checklist=[
        "TEM 본체의 가속 전압 (typical 200-300 kV) + 작동 모드 명시",
        "Cs corrector 의 spec + tuning 주기 (typical 1년)",
        "시료 준비 (FIB lift-out / ion milling / cleaving) 절차 + artifact 평가",
        "표준 시료 (Si SRM, 격자상수 5.4310 Å) 출처 + 인증 불확도",
        "tilt correction algorithm + software · version",
        "drift correction frame-by-frame 알고리즘",
        "HRTEM imaging 의 dynamical scattering 보정 (또는 simulation matching)",
        "EDS / EELS 정량 분석 SOP (TEM 부착 시)",
        "operator 의 atomic-resolution training 기록",
        "측정 결과 보고서의 격자상수 ± U (k=2) 표기",
    ],
    typical_uncertainty_budget=[
        "u_ref: Si SRM 격자상수 인증 불확도 (NIST, typical 0.01 Å)",
        "u_indexing: indexing 알고리즘의 systematic 불확도 (typical 0.5%)",
        "u_tilt: tilt correction 불확도 (typical 0.3%)",
        "u_drift: image drift correction 잔여 불확도 (typical 0.2%)",
        "u_mag: magnification 교정 불확도 (typical 0.5%)",
        "u_repeat: 반복 측정 (typical 10회) 표준편차",
    ],
)


# ──────────────────────────────────────────────────────────
# AFM (Atomic Force Microscope)
# ──────────────────────────────────────────────────────────
AFM_GUIDE = DomainGuide(
    key="afm",
    label_ko="AFM (원자력현미경)",
    label_en="Atomic Force Microscope",
    icon="📐",
    one_liner="표면 거칠기 (Sa, Sq, Sz), step height, lateral feature 를 sub-nm 분해능.",
    target_users=[
        "반도체 inline lab (CMP polished wafer 거칠기)",
        "광학 부품 lab (mirror, lens surface)",
        "MEMS / nano-patterned device lab",
        "재료 R&D (thin film morphology)",
    ],
    iso_standards=[
        {
            "code": "ISO/IEC 17025:2017",
            "title": "시험·교정 기관 일반 요구사항",
            "scope": "공통.",
        },
        {
            "code": "ISO 25178-2:2012",
            "title": "Geometrical product specifications (GPS) — Surface texture: Areal — Part 2: Terms, definitions and surface texture parameters",
            "scope": "Sa, Sq, Sz 등 areal parameter 정의. AFM 측정의 표준.",
        },
        {
            "code": "ISO 25178-606:2015",
            "title": "GPS — Surface texture: Areal — Part 606: Nominal characteristics of non-contact (focus variation) instruments",
            "scope": "비접촉 측정 장비 (AFM 포함) 의 spec 표준.",
        },
        {
            "code": "ISO 11952:2019",
            "title": "Surface chemical analysis — Scanning probe microscopy — Determination of geometric quantities using SPM",
            "scope": "SPM (AFM 포함) 의 geometric measurement 표준.",
        },
        {
            "code": "VDI/VDE 2656-1:2008",
            "title": "Reference normals for scanning probe microscopy",
            "scope": "AFM 교정용 reference normal (step height standard) 표준.",
        },
    ],
    kolas_steps=[
        {
            "order": 1,
            "name": "사전 검토",
            "duration": "2-4주",
            "key_docs": ["KOLAS-G-002", "ISO 25178-2", "ISO 11952"],
            "common_pitfalls": [
                "AFM 측정 모드 (contact / tapping / non-contact) 별 SOP 분리 안 함",
                "tip wear 의 정량 평가 기준 부재",
            ],
        },
        {
            "order": 2,
            "name": "신청서 작성",
            "duration": "1-2주",
            "key_docs": ["측정 범위 (예: Sa 0.1 nm ~ 1 μm), 측정 영역 (예: 1 μm × 1 μm ~ 100 μm × 100 μm)"],
            "common_pitfalls": [
                "step height standard (typical 18 nm, 100 nm, 1 μm) traceability chain 누락",
                "tip radius 의 영향 (Bouguer-Lambert 효과) 평가 미흡",
            ],
        },
        {
            "order": 3,
            "name": "서류 평가",
            "duration": "4-6주",
            "key_docs": ["평가팀 의견서"],
            "common_pitfalls": [
                "ISO 25178-2 의 areal parameter (Sa vs Sq vs Sz) 별 측정 영역 spec 미일치",
                "leveling / form removal 알고리즘 (예: polynomial fit order) 명시 안 함",
            ],
        },
        {
            "order": 4,
            "name": "현장 평가",
            "duration": "1-2일",
            "key_docs": ["live demo (step height standard 18 nm 측정)"],
            "common_pitfalls": [
                "live demo 에서 measurement 영역의 thermal drift 보정 미흡",
                "tip 교체 후 first measurement 의 conditioning 절차 미숙",
            ],
        },
        {
            "order": 5,
            "name": "부적합 시정 + 인정",
            "duration": "4-12주",
            "key_docs": ["시정 보고서"],
            "common_pitfalls": [
                "주요 NC: tip wear 관리 SOP 미흡 → 매월 verification 측정 도입 요구",
            ],
        },
        {
            "order": 6,
            "name": "사후 정기심사",
            "duration": "3년 cycle",
            "key_docs": ["월간 verification 측정 기록", "PT 참가"],
            "common_pitfalls": [
                "AFM PT 의 ISO 17043 provider 제한적. inter-lab comparison 으로 대체 가능.",
            ],
        },
    ],
    common_nonconformities=[
        {
            "clause": "ISO/IEC 17025 7.6.2",
            "finding": "Sa 측정의 불확도 budget 에 tip radius 의 systematic 효과 누락",
            "root_cause": "tip 이 무한히 sharp 하다고 가정. 실제 tip radius (typical 10 nm) 가 Sa 측정값에 영향.",
            "fix": "MetroAI AFM 거칠기 템플릿이 tip radius 를 input 으로 받아 deconvolution 적용.",
        },
        {
            "clause": "ISO 25178-2 4.3",
            "finding": "Sq 측정에 leveling 알고리즘 (1st order polynomial fit) 만 사용. surface form 큰 경우 부적합.",
            "root_cause": "operator 가 default 사용. SOP 에 polynomial order 선택 기준 없음.",
            "fix": "분야별 SOP checklist 에 surface form 별 polynomial order 선택 가이드.",
        },
        {
            "clause": "ISO/IEC 17025 6.4.5",
            "finding": "tip 교체 후 verification 측정 (step height standard) 누락",
            "root_cause": "tip 교체 시 즉시 사용. verification 없음.",
            "fix": "MetroAI schedule 에이전트가 tip 교체 이벤트에 verification 측정 task 자동 생성.",
        },
    ],
    metroai_tools=[
        {
            "tool_name": "AFM 거칠기 (Sa/Sq/Sz) 측정 템플릿",
            "page": "1_📐_불확도_계산",
            "value": "ISO 25178-2 areal parameter + tip radius deconvolution + leveling 효과 합성 불확도.",
        },
        {
            "tool_name": "감사 위험 시뮬레이션",
            "page": "14_🎯_감사_위험_상세",
            "value": "AFM 시나리오 (tip 관리, verification 주기) 입력 → 부적합 위험.",
        },
        {
            "tool_name": "SOP 갭 분석 (AFM 모드)",
            "page": "12_📋_SOP_갭_분석",
            "value": "AFM 특화 checklist 25 항목 평가.",
        },
        {
            "tool_name": "KOLAS 인정 신청서",
            "page": "20_📝_KOLAS_신청서_작성",
            "value": "AFM 측정 범위 + 거칠기 parameter spec 자동 채움.",
        },
    ],
    sop_checklist=[
        "AFM 본체의 측정 모드 (contact / tapping / non-contact) 별 별도 SOP",
        "tip 의 nominal radius + manufacturer + lot 명시",
        "tip wear 평가 주기 (typical 매월) + verification 측정 절차",
        "step height standard (18 nm / 100 nm / 1 μm) 출처 + 인증 U",
        "leveling / form removal 알고리즘 (polynomial order) 선택 기준",
        "thermal drift 보정 절차 (typical 측정 전 30분 warm-up)",
        "scan rate (typical 0.5-2 Hz) + pixel resolution (typical 512×512) spec",
        "Sa, Sq, Sz 별 측정 영역 (ISO 25178-2 권장: 5×5 μm 또는 50×50 μm)",
        "operator 의 ISO 25178-2 training 기록",
        "측정 결과 보고서의 areal parameter ± U (k=2)",
    ],
    typical_uncertainty_budget=[
        "u_ref: step height standard 인증 불확도 (typical 0.5 nm)",
        "u_z_cal: z-axis 교정 불확도 (typical 1%)",
        "u_xy_cal: xy-axis 교정 불확도 (typical 1%)",
        "u_tip: tip radius 의 effective filtering 효과 (typical 1-3%)",
        "u_thermal: thermal drift 잔여 (typical 0.3 nm/min)",
        "u_repeat: 반복 측정 표준편차 (5회, ISO 5725)",
        "u_leveling: leveling 알고리즘의 잔여 systematic (typical 0.5%)",
    ],
)


# ──────────────────────────────────────────────────────────
# OCD (Optical Critical Dimension / Scatterometry)
# ──────────────────────────────────────────────────────────
OCD_GUIDE = DomainGuide(
    key="ocd",
    label_ko="OCD (광학적 임계치수)",
    label_en="Optical Critical Dimension (Scatterometry)",
    icon="📏",
    one_liner="반도체 patterned wafer 의 CD, sidewall angle, height 를 비파괴 측정.",
    target_users=[
        "반도체 FAB inline metrology (logic / memory)",
        "EUV photomask inspection lab",
        "MEMS / nano-patterned device lab",
        "OCD 장비 제조사 (KLA, Nova, Onto) 의 calibration lab",
    ],
    iso_standards=[
        {
            "code": "ISO/IEC 17025:2017",
            "title": "시험·교정 기관 일반 요구사항",
            "scope": "공통.",
        },
        {
            "code": "SEMI MF-1789-1112",
            "title": "Test Method for the Determination of Critical Dimension (CD), Sidewall Angle, and Height of Critical Patterns on Semiconductor Wafers by Optical Critical Dimension (OCD)",
            "scope": "OCD 측정의 표준 절차. RCWA library matching 의 정확도 평가.",
        },
        {
            "code": "ISO 17078-2:2014",
            "title": "Optical metrology of patterned wafers",
            "scope": "광학 metrology 의 일반 요구사항.",
        },
        {
            "code": "SEMI E89-0414",
            "title": "Specification for Standard Reference Materials for CD Metrology",
            "scope": "CD metrology 용 표준 시료 spec.",
        },
    ],
    kolas_steps=[
        {
            "order": 1,
            "name": "사전 검토",
            "duration": "2-4주",
            "key_docs": ["KOLAS-G-002", "SEMI MF-1789", "ISO 17078-2"],
            "common_pitfalls": [
                "OCD 가 KOLAS 의 어느 분야 (시험 vs 교정) 에 해당하는지 명확화 안 함",
                "RCWA library 의 정확도 vs measurement uncertainty 의 관계 미숙",
            ],
        },
        {
            "order": 2,
            "name": "신청서 작성",
            "duration": "1-2주",
            "key_docs": ["측정 범위 (예: CD 10-100 nm, sidewall angle 80-90°), wavelength range (typical 200-800 nm)"],
            "common_pitfalls": [
                "RCWA library 의 source (in-house 생성 vs commercial software) + version 누락",
                "CD-AFM cross-check 결과 (typical 5% 일치) 미문서화",
            ],
        },
        {
            "order": 3,
            "name": "서류 평가",
            "duration": "4-6주",
            "key_docs": ["평가팀 의견서"],
            "common_pitfalls": [
                "RCWA library matching 의 confidence metric (typical R² > 0.95) 정량 평가 누락",
                "parameter correlation (CD vs height vs sidewall angle) 의 covariance 미고려",
            ],
        },
        {
            "order": 4,
            "name": "현장 평가",
            "duration": "1-2일",
            "key_docs": ["live demo (line/space patterned wafer)", "CD-SEM cross-check"],
            "common_pitfalls": [
                "live demo 에서 RCWA library 의 cutoff (예: harmonic truncation order) 설명 미숙",
                "CD-SEM 과의 cross-check 결과 차이 (typical 1-3 nm) 의 root cause 분석 미흡",
            ],
        },
        {
            "order": 5,
            "name": "부적합 시정 + 인정",
            "duration": "4-12주",
            "key_docs": ["시정 보고서"],
            "common_pitfalls": [
                "주요 NC: RCWA library 의 정기 update (typical 6개월) 누락",
            ],
        },
        {
            "order": 6,
            "name": "사후 정기심사",
            "duration": "3년 cycle",
            "key_docs": ["RCWA library 갱신 기록", "CD-SEM cross-check 통계"],
            "common_pitfalls": [
                "OCD PT 의 ISO 17043 provider 사실상 없음. SEMI 의 inter-lab comparison 참여 권장.",
            ],
        },
    ],
    common_nonconformities=[
        {
            "clause": "ISO/IEC 17025 7.6.2",
            "finding": "OCD 측정 불확도 budget 에 RCWA library matching 의 systematic 잔여 누락",
            "root_cause": "operator 가 library matching R² 값만 기록. systematic 불확도 미산정.",
            "fix": "MetroAI OCD 템플릿이 RCWA library quality metric 을 input 으로 받아 systematic 불확도 자동 산정.",
        },
        {
            "clause": "SEMI MF-1789 6.3",
            "finding": "parameter correlation (CD-height) 의 covariance matrix 미산정",
            "root_cause": "OCD 의 multi-parameter inverse problem 의 ill-posedness 인식 부족.",
            "fix": "MetroAI 역설계 엔진 (4_🔄_불확도_역설계) 이 sensitivity matrix + correlation 자동 산정.",
        },
        {
            "clause": "ISO/IEC 17025 6.4.5",
            "finding": "RCWA library 의 정기 update SOP 부재",
            "root_cause": "commercial software 사용 시 update 자동이라고 가정.",
            "fix": "schedule 에이전트가 RCWA library update task 자동 생성.",
        },
    ],
    metroai_tools=[
        {
            "tool_name": "OCD CD 측정 템플릿 (RCWA forward)",
            "page": "1_📐_불확도_계산",
            "value": "RCWA forward model + library matching + parameter correlation 의 합성 불확도.",
        },
        {
            "tool_name": "불확도 역설계 엔진",
            "page": "4_🔄_불확도_역설계",
            "value": "OCD 의 ill-posed inverse problem 의 sensitivity matrix + 성분별 최대 허용 표준불확도 산정.",
        },
        {
            "tool_name": "감사 위험 시뮬레이션",
            "page": "14_🎯_감사_위험_상세",
            "value": "OCD 시나리오 (library quality, cross-check 빈도) 입력 → 부적합 위험.",
        },
        {
            "tool_name": "SOP 갭 분석 (OCD 모드)",
            "page": "12_📋_SOP_갭_분석",
            "value": "OCD 특화 checklist 28 항목 평가.",
        },
        {
            "tool_name": "KOLAS 인정 신청서",
            "page": "20_📝_KOLAS_신청서_작성",
            "value": "OCD 측정 범위 + library spec 자동 채움.",
        },
    ],
    sop_checklist=[
        "OCD 장비의 wavelength range + polarization spec 명시",
        "RCWA library 의 source (in-house / commercial) + version + 갱신 주기",
        "harmonic truncation order (typical 7-15) 선택 기준",
        "CD-SEM / TEM cross-check 주기 (typical 매월) + 허용 차이 (typical < 3 nm)",
        "parameter correlation matrix (CD vs height vs sidewall angle) 의 covariance 산정 절차",
        "library matching 의 confidence metric (R², chi-square) 보고 의무",
        "표준 시료 (line/space patterned wafer) 출처 + 인증 CD",
        "wavelength calibration 주기 (typical 6개월)",
        "operator 의 SEMI MF-1789 training 기록",
        "측정 결과 보고서의 CD ± U (k=2) + library quality metric 표기",
    ],
    typical_uncertainty_budget=[
        "u_ref: 표준 시료 (patterned wafer) CD 인증 불확도 (typical 0.5 nm)",
        "u_rcwa: RCWA library matching 의 systematic 불확도 (typical 1-2 nm)",
        "u_corr: parameter correlation 의 residual 불확도 (CD-height covariance)",
        "u_wavelength: wavelength 교정 불확도 (typical 0.1 nm)",
        "u_polarization: polarization 교정 불확도 (typical 0.5°)",
        "u_repeat: 반복 측정 표준편차 (10회)",
        "u_cross: CD-SEM cross-check 와의 일치도 (typical 1-2 nm)",
    ],
)


# ──────────────────────────────────────────────────────────
# General (일반 측정)
# ──────────────────────────────────────────────────────────
GENERAL_GUIDE = DomainGuide(
    key="general",
    label_ko="일반 측정",
    label_en="General Measurement",
    icon="📊",
    one_liner="블록게이지, 마이크로미터, 전기·질량·차원 등 전통 분야 + ISO 17043 PT.",
    target_users=[
        "전통적 교정 lab (블록게이지, 마이크로미터, 캘리퍼)",
        "전기 / 질량 / 압력 교정 lab",
        "ISO 17043 PT provider",
        "KRISS 산하 교정 분야 lab",
    ],
    iso_standards=[
        {
            "code": "ISO/IEC 17025:2017",
            "title": "시험·교정 기관 일반 요구사항",
            "scope": "전 분야 공통.",
        },
        {
            "code": "ISO/IEC Guide 98-3:2008 (GUM)",
            "title": "Uncertainty of measurement — Part 3: Guide to the expression of uncertainty in measurement",
            "scope": "측정 불확도 산정의 표준. 모든 분야 적용.",
        },
        {
            "code": "ISO/IEC Guide 98-3 Suppl. 1:2008",
            "title": "Propagation of distributions using a Monte Carlo method",
            "scope": "Monte Carlo 기반 불확도 propagation.",
        },
        {
            "code": "ISO 13528:2022",
            "title": "Statistical methods for use in proficiency testing by interlaboratory comparison",
            "scope": "PT 의 z-score, z'-score 산정 방법.",
        },
        {
            "code": "ISO/IEC 17043:2010",
            "title": "Conformity assessment — General requirements for proficiency testing",
            "scope": "PT provider 의 일반 요구사항.",
        },
        {
            "code": "ISO 5725 series",
            "title": "Accuracy (trueness and precision) of measurement methods and results",
            "scope": "repeatability + reproducibility 산정.",
        },
    ],
    kolas_steps=[
        {
            "order": 1,
            "name": "사전 검토",
            "duration": "2-4주",
            "key_docs": ["KOLAS-G-002", "ISO/IEC 17025 7장"],
            "common_pitfalls": [
                "교정 분야와 시험 분야의 SOP 분리 모호",
                "측정 표준의 traceability chain 단순화 가정",
            ],
        },
        {
            "order": 2,
            "name": "신청서 작성",
            "duration": "1-2주",
            "key_docs": ["측정 범위 + 측정 불확도 (CMC 형식)"],
            "common_pitfalls": [
                "CMC (Calibration and Measurement Capability) 의 정량 표기 부정확",
                "환경 조건 (온도 20 ± 1°C, RH 50 ± 10%) 제어 SOP 미흡",
            ],
        },
        {
            "order": 3,
            "name": "서류 평가",
            "duration": "4-6주",
            "key_docs": ["평가팀 의견서"],
            "common_pitfalls": [
                "GUM budget 의 분포 가정 (Normal / Rectangular / Triangular) 일관성 부족",
                "Welch-Satterthwaite 자유도 계산 missing",
            ],
        },
        {
            "order": 4,
            "name": "현장 평가",
            "duration": "1-2일",
            "key_docs": ["live demo (블록게이지 / 마이크로미터 교정)"],
            "common_pitfalls": [
                "환경 chamber (20°C ± 0.1°C) 의 변동 기록 미흡",
                "operator 의 GUM 산정 절차 숙지 부족",
            ],
        },
        {
            "order": 5,
            "name": "부적합 시정 + 인정",
            "duration": "4-12주",
            "key_docs": ["시정 보고서"],
            "common_pitfalls": [
                "주요 NC: PT 참가 (ISO 17043) 매년 권장 → 누락 시 시정",
            ],
        },
        {
            "order": 6,
            "name": "사후 정기심사",
            "duration": "3년 cycle",
            "key_docs": ["PT 참가 결과", "내부 audit 기록"],
            "common_pitfalls": [
                "z'-score > 2 인 PT 결과의 root cause analysis 부재",
            ],
        },
    ],
    common_nonconformities=[
        {
            "clause": "ISO/IEC 17025 7.6.2",
            "finding": "GUM budget 의 표준 분포 가정 (Rectangular vs Normal) 의 일관성 부족",
            "root_cause": "operator 가 input 별로 다르게 가정. SOP 명시 없음.",
            "fix": "MetroAI 가 분포 선택 기준을 가이드 + GUM budget 자동 산정.",
        },
        {
            "clause": "ISO/IEC 17025 6.4.5",
            "finding": "표준기 (블록게이지 100 mm) 교정 주기 미정량",
            "root_cause": "SOP 에 '정기 교정' 만 명시.",
            "fix": "MetroAI schedule 에이전트가 표준기별 교정 주기 자동 산정 + 알림.",
        },
        {
            "clause": "ISO 13528 9.3",
            "finding": "PT z'-score > 2 의 시정 조치 기록 부재",
            "root_cause": "PT 결과 받기만 하고 분석 안 함.",
            "fix": "MetroAI PT 분석 page (2_📊) 가 z'-score 시각화 + 알림.",
        },
    ],
    metroai_tools=[
        {
            "tool_name": "GUM + MCM 불확도 계산 (6 템플릿)",
            "page": "1_📐_불확도_계산",
            "value": "블록게이지, 마이크로미터, KOLAS PT, 차원, 전기, 질량 — 모두 ISO Guide 98-3 표준 budget.",
        },
        {
            "tool_name": "PT 분석 (z-score / z'-score)",
            "page": "2_📊_PT_분석",
            "value": "ISO 13528 의 PT 통계 + 시각화.",
        },
        {
            "tool_name": "교정 성적서 PDF 생성",
            "page": "3_📄_교정성적서",
            "value": "KOLAS 양식 + 5개국 (KOLAS/JCSS/TAF/A2LA/CNAS) 표지.",
        },
        {
            "tool_name": "감사 위험 시뮬레이션",
            "page": "14_🎯_감사_위험_상세",
            "value": "일반 분야 시나리오 평가.",
        },
        {
            "tool_name": "SOP 갭 분석",
            "page": "12_📋_SOP_갭_분석",
            "value": "ISO 17025 의 일반 SOP checklist 평가.",
        },
        {
            "tool_name": "KOLAS 인정 신청서",
            "page": "20_📝_KOLAS_신청서_작성",
            "value": "CMC (Calibration Measurement Capability) 양식 자동 채움.",
        },
    ],
    sop_checklist=[
        "측정 표준의 traceability chain (KRISS / NIST 경유) 명시",
        "환경 조건 (온도 20 ± 1°C, RH 50 ± 10%) 제어 SOP",
        "표준기 교정 주기 (typical 1년) + 외부 교정 기관",
        "GUM budget 의 표준 분포 (Normal / Rectangular / Triangular / U-shape) 선택 기준",
        "Welch-Satterthwaite 자유도 산정 절차",
        "CMC (Calibration Measurement Capability) 정량 표기",
        "내부 audit 매년 1회 + 시정 조치 기록",
        "PT 참가 (ISO 17043) 매년 + z'-score 분석",
        "operator 의 ISO/IEC 17025 training 기록",
        "측정 결과 보고서의 측정 불확도 (k=2, 95% CI) 표기 + 분포 가정 명시",
    ],
    typical_uncertainty_budget=[
        "u_ref: 표준기 인증 불확도 (KRISS, typical 0.05-0.1 μm for gauge block)",
        "u_repeat: 반복 측정 표준편차 (10회, ISO 5725)",
        "u_temp: 온도 효과 (typical α × ΔT × L, 강철 α = 11.5 × 10⁻⁶ /K)",
        "u_resolution: 측정기 분해능 (rectangular distribution)",
        "u_alignment: 측정자 alignment 효과 (typical 0.5 μm)",
        "u_drift: 표준기 drift (typical 0.1 μm/year)",
    ],
)


# ──────────────────────────────────────────────────────────
# Registry
# ──────────────────────────────────────────────────────────
_GUIDES = {
    "sem": SEM_GUIDE,
    "tem": TEM_GUIDE,
    "afm": AFM_GUIDE,
    "ocd": OCD_GUIDE,
    "general": GENERAL_GUIDE,
}


def get_domain_guide(domain: str) -> DomainGuide | None:
    """분야 키로 가이드 조회."""
    return _GUIDES.get(domain.lower())


def list_domains() -> list[DomainGuide]:
    """모든 분야 가이드 리스트."""
    return list(_GUIDES.values())
