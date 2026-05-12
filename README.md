# 📐 MetroAI — KOLAS 컴플라이언스 OS (v0.6.0)

> **"KOLAS 감사를 데이터로 관리합니다."**

한국 1,200+ KOLAS 인정기관을 위한 컴플라이언스 운영 시스템.
6개 AI agents 가 SOP · 인증서 · 인력 · 감사이력 · 규제변경을 24시간 모니터링하고,
부적합 위험을 사전에 예측합니다.

> v0.6.0 (2026-05) — 6 AI agents 백본 + 4종 신규 나노메트롤로지 템플릿 + Ed25519 audit log + QMC.

## 주요 기능

### 컴플라이언스 OS (v0.6.0 신규)

1. **6 AI Agents 자동 모니터링** — `semi-intel`(반도체 동향, DART·NTIS 연동) · `job-scout`(인력 회전율, baseline stub) · `kolas-monitor`(KOLAS 고시 일일 스캔, knab.go.kr live fetch + stub fallback) · `kolas-audit-predictor`(감사 위험 예측 — 룰 베이스라인 + GBT 모델 옵션) · `orchestrator`(통합 작업 큐) · `schedule`(일정 자동 관리). 외부 데이터는 모두 `*_is_live` 플래그로 live/stub 구분.
2. **Verifiable Audit Trail** — Ed25519 디지털 서명 + W3C PROV-O 프로비넌스로 모든 AI 출력의 무결성을 입증. KOLAS 정기심사 시 사후 변조 없음 입증 가능.
3. **Pydantic v2 입력 검증** — MCP 도구·FastAPI·Streamlit 폼 모두 동일 스키마로 검증.

### 불확도 엔진 (v0.5.0 기반 + v0.6.0 신규 4종)

4. **GUM 자동 계산** — sympy 기반 편미분, Welch-Satterthwaite, 확장불확도.
5. **MCM + QMC 검증** — 몬테카를로(ISO 98-3/Suppl. 1) + Sobol QMC (O(1/N) 수렴, baseline 검증 정확도 ±0.003%).
6. **불확도 역설계** (Novel — GUM Workbench 등 기존 SW에 없음) — 목표 U_target 만족하는 성분별 최대 허용 표준불확도 자동 산출.
7. **9개 교정·시험 템플릿** — v0.5 (블록게이지·분동·온도·압력·DC전압) + v0.6 신규 (TEM 격자상수 · SEM-EDS 원소 정량 · AFM 거칠기 · OCD scatterometry CD).
8. **KOLAS 양식 출력** — 엑셀/PDF 예산서 + 교정성적서 자동 생성.
9. **PT 분석** — z/En/ζ-score (ISO 13528, ISO 17043).

## kolas-audit-predictor 정직 메트릭 (D sprint, 2026-05-12)

> **외부 인용용 정직 한 줄:**
> *합성 데이터 기반 5-fold CV: **accuracy 60.6% ± 3.1pp · ROC-AUC 0.628 ± 0.038 · Brier 0.241 · F1 0.636** (n=2000 × 6 features, label noise 15%). 실 KOLAS 감사 결과 데이터로 외부 검증 진행 중이며, 그 전까지는 상기 메트릭이 실세계 성능을 의미하지 않습니다.*

설계 결정:
- GradientBoostingClassifier (n_estimators=200, depth=3, lr=0.05)
- Feature 중요도 상위 3: `months_since_last_audit` (0.34) · `personnel_turnover` (0.25) · `sop_completeness` (0.24) — 도메인 상식과 일치
- 합성 데이터에서 60%대 정확도는 label noise=0.15 환경에서 합리적 (오라클 상한 ≈ 85%)
- "87.1%" 등 이전 sprint 의 sandbox 수치는 모델 메타데이터·랜딩 페이지·MCP manifest 어디에도 박지 않음 (`docs/HONESTY_NOTES.md` 참조)

코드 경로: `metroai/ml/audit_risk_model.py`, `metroai/ml/synthetic_audit_data.py`
테스트: `tests/test_v060_ml.py` (6 통과)

## 스크린샷

> *(추후 추가 예정)*

## 설치 및 실행

### 로컬 실행

```bash
# 의존성 설치
pip install -e ".[dev]"

# 앱 실행
streamlit run app.py
```

### 테스트

```bash
pytest tests/ -v
```

## 기술 스택

- Python 3.10+
- sympy, numpy, scipy (수치 계산)
- Streamlit (웹 UI)
- reportlab (PDF 생성)
- openpyxl (엑셀 출력)
- plotly (차트/시각화)

## 프로젝트 구조

```
metroai/
├── app.py                   ← 랜딩 페이지 (Streamlit Cloud 진입점)
├── pages/                   ← Streamlit 멀티페이지
│   ├── 1_📐_불확도_계산.py   ← 템플릿 + 직접입력 + 위자드 모드
│   ├── 2_📊_PT_분석.py      ← 숙련도시험 분석
│   └── 3_📄_교정성적서.py    ← 교정성적서 PDF 생성
├── metroai/
│   ├── core/                ← GUM/MCM 계산 엔진
│   ├── export/              ← 엑셀/PDF 출력
│   ├── modules/             ← PT 분석기 등
│   └── templates/           ← 교정 분야별 템플릿
└── tests/                   ← 55개 유닛 테스트
```

## 라이선스

MIT License
