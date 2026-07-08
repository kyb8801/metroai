# MetroAI — Uncertainty-Aware ML Metrology Platform

**계측 + 불확도 + AI** 를 한 구조로. 각 장비 모듈은 공용 코어 2개(①, ②③)를 호출해
**일관된 GUM 불확도 + ML inverse + ML 불확도**를 얻는다. (이전: 불확도 절반·AI 2-3개 → 코어로 구조 해결)

---

## Core (재사용 엔진)

| | 파일 | 역할 | 검증 |
|---|---|---|---|
| ① | `uncertainty.py` | 통일 GUM: 합성 u_c · 확장 U(k=2) · Monte Carlo · budget · 감도계수 | block-gauge u_c=0.0594, MC 일치 |
| ②③ | `ml_inverse.py` | ML inverse(ensemble) + ML 불확도(epistemic + conformal) + GUM 결합 | conformal 90%→89% coverage |

```python
# 모든 장비 공통 사용 패턴
from uncertainty import budget, expand, monte_carlo
from ml_inverse import MLInverse
mdl = MLInverse().fit(X_train, y_train)              # ② ML inverse
out = mdl.predict(X_query)                           # ③ pred + u_epistemic + conformal
u_tot = MLInverse.combine_with_gum(out['u_epistemic'], u_gum)   # ①+③
```

---

## Instrument modules (장비별, 코어 호출 대상)

| # | 장비 | 방법 | ① 불확도 | ②③ AI | 등급 | 네 IP |
|---|---|---|:---:|:---:|---|---|
| 1 | OCD | RCWA(Meent)+library | ✅ | ✅ GPR/KNN/conformal | ★★★ | NIST |
| 8 | PL/exciton | peak fit | ✅ | (peak fit) | ★★★ | 박사 Valley |
| 9 | NSOM | hyperspectral | ⟶① | ✅ k-means | ★★ | 박사 ipynb |
| 10 | Lamb acoustic | f0+4D | ⟶① | ✅ Mahalanobis | ★★ | 특허 ARS_TEAS |
| 7 | AFM | roughness/tip | ⟶① | ⟶②③ | ★★ | 논문+.spm |
| 3·5 | TEM 격자/GPA | FFT/phase | ⟶① | ⟶②③ | ★★ | HRTEM |
| 2·4·6 | XRR·Raman·SEM | fit/threshold | ✅/⟶① | ⟶②③ | ★★ | 합성/NIST |

`⟶` = 코어 호출로 추가 예정(refactor). ✅ = 이미 탑재.

---

## 네 계측 IP → 플랫폼 (본질)

- **박사(광학·분광)**: PL/exciton(Valley) · NSOM(MoSe2/WSe2 defect) · TERS/confocal · valley DCP
- **ARS_TEAS(특허 V9)**: Lamb acoustic + Q²-AFM-IR (Module 10, 공개 물리 엔진만 코드화; 발명 핵심은 명세서)
- **traceability chain**: HRTEM 격자 → trench CRM → AFM tip → 측정 보정 (네 독점)

## 네 비전(METROAI_INTEGRATION_SPEC) 매핑
- Module 1-5 Compliance Core ← `uncertainty.py`(Module 2) + traceability
- Module 6 SpectraGuard(28/28) ← acoustic 4D 확장 hook
- Module 9 SEM AI / Track 1 TEM ← #6/#3
- **Module 10 Acoustic-Photothermal** ← `metrology_module_10_lamb_acoustic.py` (skeleton ✅)

---

## 정직한 현황

- ✅ **코어 ①②③ 완성** — "계측+불확도+AI"가 구조적으로 가능해짐
- ✅ 실측 ★★★: OCD(NIST) · PL(MoS2 1.85eV)
- ⏳ refactor 필요: 7개 장비를 코어 호출로 전환(불확도/AI 일관화)
- ⏳ 통합: 코어 2 + 모듈 13 → `Desktop/metroai/metroai/` 편입
- ⚠️ ML inverse 는 forward library(훈련데이터) 필요 — OCD(NIST)/합성은 OK, PL/NSOM은 소량이라 peak-fit/clustering 이 적절(장비별 최적 AI 선택)

## 다음
1. OCD·(합성 library 장비)에 `ml_inverse` 실제 적용 → ML+불확도 실증 확대
2. 7개 장비 `uncertainty.py` 호출 refactor (불확도 일관화)
3. 코어+모듈 → `metroai` repo 통합, README, 공개
