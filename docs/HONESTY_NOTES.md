# MetroAI 정직 노트 (v0.6.0)

> 외부 약속·인용·홍보 자료 작성 전 반드시 확인.
> 본 문서는 박수연(MetroAI advisor) 통합 sprint 의 정직 점검 결과를 누적한다.

마지막 업데이트: 2026-05-12 (D sprint)

---

## 1. 인용 가능한 사실 vs 인용 금지 사실

### ✅ 인용 가능 (sandbox 또는 합리적 추정으로 검증)

| 사실 | 근거 | 어디까지 말해도 되는가 |
|---|---|---|
| Streamlit v0.5.0 deployment 운영 중 | `https://metroai-gnbdv7pqq3quqsudb5pwvj.streamlit.app` 살아있음 | "현재 v0.5 가 배포 운영 중이며 v0.6 으로 업그레이드 중" |
| GUM/MCM 계산 엔진 통과 | `tests/test_gum.py`, `tests/test_mcm.py` 통과 | "GUM ISO 98-3 표준 계산 통과" |
| QMC vs GUM 정합성 ±0.003% | `tests/test_v060_modules.py::test_qmc_matches_gum_analytic_linear_model` | "Sobol QMC 가 단순 선형 모델에서 GUM 해석해와 ±0.003% 일치" |
| 9개 templates 동작 (v0.5 5 + v0.6 4) | `tests/test_v060_modules.py` 29 통과 | "9개 교정·시험 분야 템플릿 보유" |
| Ed25519 sign/verify + tamper 감지 | `tests/test_v060_modules.py::test_ed25519_*` | "Ed25519 무결성 서명 + 변조 자동 감지" |
| PROV-O 그래프 생성 | `metroai/audit/provenance.py` + tests | "W3C PROV-O 호환 프로비넌스" |
| GBT 모델 합성 acc 60.6% ± 3.1pp | `tests/test_v060_ml.py` 6 통과 + D sprint 검증 | "합성 데이터 5-fold CV 결과 acc 60.6% (실데이터 검증 진행 중)" |
| 4개 vertical-mcp 보유 (kolas/dart/ntis/grant) | 각 폴더 `mcp.json` 존재 | "한국 vertical MCP 4종 manifest 보유. marketplace 등록 진행 중" |
| KIM's Reference KOLAS KRMPs-021 인증 | 사용자 보유 자료 | "본 서비스는 KOLAS 인정 기관 실무자에 의해 설계되었음" |

### ❌ 인용 금지 (sandbox 결과인데 실데이터 미검증, 또는 검증 자체 부재)

| 인용 금지 표현 | 이유 | 대체 표현 |
|---|---|---|
| "kolas-audit-predictor 87.1% accuracy" | cross-source fusion prototype 의 sandbox 1회 결과. 합성 데이터 GBT 재현 시 60% 대 | "v0.6 baseline. 합성 데이터 60.6% acc, 실데이터 검증 진행 중" |
| "World's first AI metrology platform" | 입증 자료 부족. 비슷한 시도 다수 존재 | "novel within prior-art search (GUM Workbench / NIST UM 등 미발견)" |
| "10x faster than spreadsheet" | 벤치마크 미수행 | 정량 인용 자제. "엑셀 수작업 대비 자동화" 정도 |
| "실시간 KOLAS 모니터링" | knab.go.kr live fetch 가 stub fallback 가능 (대시보드의 `is_live` 플래그로 구분 필요) | "KOLAS 고시 자동 모니터링 (live fetch + 보수적 fallback)" |
| "6 AI agents 가 실시간 학습" | semi-intel/job-scout/orchestrator/schedule 은 룰 기반. 학습은 audit-predictor 만 | "6 AI agents 자동 협업. 그 중 kolas-audit-predictor 가 모델 학습 기반" |

---

## 2. 데이터 origin 표기 규칙

모든 메트릭·예측·통계는 다음 라벨 중 하나를 동반해야 한다.

| 라벨 | 의미 | 외부 약속 가능? |
|---|---|---|
| `live` | 실제 외부 API/페이지에서 fetch 성공 | YES |
| `stub` | 보수적 더미 fallback | NO — 명시적으로 stub 라고 말해야 함 |
| `synthetic` | 본 프로젝트가 생성한 합성 데이터 | 학습/검증 목적 한정 |
| `mixed` | live + 합성 fusion | 둘 다 명시 |
| `unknown` | 검증 불가 | 인용 불가 |

코드에서는 이 라벨이 `AgentResult.payload["is_live"]`, `ConnectorResult.is_live`, `ModelEvaluation.data_origin` 으로 노출된다. UI 는 모두 cyan AI 배지와 함께 status dot 으로 표시.

---

## 3. D sprint 검증 절차

```bash
pip install -e ".[dev,ml]"
pytest tests/test_v060_ml.py -v
# 합성 데이터 60.6% acc 재현 + tampering 감지 + save/load roundtrip
```

```python
from metroai.ml import train_audit_risk_model
model, ev = train_audit_risk_model(n_samples=2000, seed=42, cv_folds=5)
print(ev.honest_summary())
# [synthetic] 5-fold CV on 2000 samples × 6 features: acc 60.6% ± 3.1pp, AUC 0.628 ± 0.038, Brier 0.241, F1 0.636
```

---

## 4. 미해결 정직 항목 (다음 sprint)

1. **실 KOLAS 부적합 데이터 확보** — 87.1% 등 외부 약속 가능한 정확도를 받으려면 필수. KOLAS 공개 데이터 조사 + 협력 기관 데이터 동의 절차 필요.
2. **MetroAI_Design_Outputs/01_landing/metroai_landing_v1.html** — 이미 87.1% 가 박혀있는 상태. 디자인 새션 재실행 시 PROMPTS_READY.md 최신본 사용해서 자동 정정.
3. **NTIS connector live fetch** — 현재 NotImplementedError → stub. ntis.go.kr 검색 페이지 selector 검증 후 구현.
4. **kolas_monitor live fetch** — URL 후보 2개만 시도. 실제 KOLAS 게시판 URL 정밀 확인 후 selector 견고화.
5. **이전 sprint 산출물 (이력서·자소서·STAR 라이브러리)** — KOLAS KRMPs-021 "상용기업 세계 최초" 표현은 별도 sprint 에서 출처 재검증 필요.

---

## 5. 외부 공개 자료 작성 체크리스트

자료를 외부 (LinkedIn, 면접, 카페, MCPize submit description) 에 내보내기 전:

- [ ] 87.1% 또는 그에 준하는 미검증 정확도 수치 없음
- [ ] "World's first" / "세계 최초" 단언 없음 (RMP cert KRMPs-021 만 별도 명시)
- [ ] 모든 메트릭에 데이터 origin (synthetic/live/stub) 명기
- [ ] 6 AI agents 중 stub/baseline 인 항목 정직 표시 (semi-intel/job-scout/audit-predictor baseline)
- [ ] 9개 templates 중 v0.5 vs v0.6 신규 구분
- [ ] live fetch 가 fallback 될 수 있음을 사용자에게 알릴 수단 (UI 또는 footer)

체크리스트 모두 ✅ 일 때만 발행.
