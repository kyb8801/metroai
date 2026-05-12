# MetroAI v0.6.0 — KOLAS Compliance OS

> Release date: 2026-05-12
> 정직 메트릭 + 6 AI agents + 4종 신규 나노메트롤로지 템플릿

## What's new

### 6 AI Agents 백본 (NEW)
KOLAS 컴플라이언스 운영을 24/7 모니터링하는 자율 에이전트:

- `semi-intel` — 반도체 산업 동향 (DART · NTIS live fetch with stub fallback)
- `job-scout` — 채용·인력 회전율 신호 (baseline stub)
- `kolas-monitor` — KOLAS 고시 일일 스캔 (knab.go.kr live fetch with stub fallback)
- `kolas-audit-predictor` — 감사 위험 예측 (룰 baseline + 선택적 GradientBoosting)
- `orchestrator` — 통합 작업 큐 (P0/P1/P2)
- `schedule` — 검토·교정·심사 일정 자동 관리

각 에이전트의 출력에 `is_live` / `data_origin` 플래그가 동반되어 live vs stub 을 UI 에서 명확히 구분합니다.

### 신규 4종 나노메트롤로지 템플릿 (NEW)
ISO 18516 / ISO 25178-2 / ISO 22489 / SEMI MF-1789 호환:

- `tem_lattice` — TEM 격자상수 (HRTEM 기반 d-spacing, Si CRM)
- `sem_eds` — SEM-EDS 원소 정량 (ZAF 보정)
- `afm_roughness` — AFM 표면 거칠기 (Sa·Sq, ISO 25178-2)
- `ocd_scatterometry` — OCD CD 측정 (RCWA forward)

### Verifiable Audit Trail (NEW)
- **Ed25519 디지털 서명** (RFC 8032) — 모든 AI 출력의 무결성 + tampering 자동 감지
- **W3C PROV-O 프로비넌스** — 입력 → 모델 → 출력의 lineage 그래프 (JSON-LD)
- KOLAS 정기심사 대비: AI 출력이 사후 변조되지 않음을 입증 가능

### Sobol QMC 보강
- ISO 98-3/Suppl. 1 MCM + Sobol low-discrepancy QMC
- 단순 선형 모델에서 GUM 해석해와 **±0.003%** 일치 (sandbox 검증)

### Pydantic v2 입력 검증
- 6 schemas + 4 enums
- MCP / FastAPI / Streamlit 폼에서 동일 검증 계층 공유

### v2 Design Spec 정합
- 색상: `#1E40AF` (Indigo 800) + `#06B6D4` (Cyan 500) + slate scale + 감사 시맨틱 (#10B981 / #F59E0B / #EF4444)
- 폰트: Pretendard / Inter / JetBrains Mono
- Document-first, no decorative gradients, no parallax — compliance-grade tone

### 신규 페이지
- 🤖 **6 AI Agents 대시보드** — KPI strip + 감사 위험 + 작업 큐 + KOLAS 피드 + 6-strip
- 📋 **SOP 갭 분석** — 기술관리자 작업 화면, 필터 + 매트릭스 + AI 갭 사이드 패널

### CI/CD
- GitHub Actions tests.yml — Python 3.10/3.11/3.12 매트릭스 + ruff + Codecov
- release.yml — 태그 push → PyPI OIDC trusted publishing
- **36 passing tests in 6.07s**

---

## 정직 메트릭 (D sprint 결과)

`kolas-audit-predictor` GradientBoosting 모델 평가:

> **합성 데이터 5-fold CV: acc 60.6% ± 3.1pp · ROC-AUC 0.628 ± 0.038 · Brier 0.241 · F1 0.636** (n=2000, 6 features, label noise 0.15)

- Feature importance 상위 3: `months_since_last_audit` (0.34) · `personnel_turnover` (0.25) · `sop_completeness` (0.24) — 도메인 상식과 일치
- 실 KOLAS 감사 데이터로 외부 검증 진행 중. 그 전까지 60.6% 는 실세계 정확도를 의미하지 않습니다.
- 이전 sandbox 의 "87.1%" 수치는 코드 / 매니페스트 / 디자인 prompts 모두에서 제거됨

자세한 정직 라벨링 규칙은 `docs/HONESTY_NOTES.md` 참조.

---

## Breaking changes

없음. v0.5.0 GUM 엔진 그대로 유지.

새 의존성:
- `pydantic>=2.0` — 입력 검증
- `cryptography>=42.0` — Ed25519
- (선택) `scikit-learn>=1.4`, `joblib>=1.3` — `pip install metroai[ml]`

---

## Upgrade

```bash
pip install --upgrade metroai
# 또는 from source
git pull && pip install -e ".[dev,ml]"
```

---

## Credits

- Solo build by Yongbeom Kim (KTR ISO 17034 cert. 2024-CM-007)
- Inspired by KIM's Reference KOLAS metrology operations
- v0.6.0 architecture reviewed by 박수연 (AI advisor) — 73 sprint integration

---

## What's next (planned for v0.7.0)

- 실 KOLAS 부적합 데이터 확보 → GBT retrain → 정직 acc 외부 공개
- v2 design spec 블록 1·3·5·6 페이지 구현 (현재 2·4 만 완료)
- NTIS connector live fetch 구현
- vertical-mcp 4개 marketplace 등록 완료
- MetroAI MCP server 의 FastAPI 백엔드 분리 (스케일링용)
