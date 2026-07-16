# KOLAS / ISO 17025 교정성적서 기재사항 ↔ DCC 3.3.0 요소 매핑

> **지위**: 실무 참고용 초안 (MetroAI `dcc` 모듈 v1과 함께 작성).
> KS Q ISO/IEC 17025:2017 및 KOLAS 규정 **원문 대조 검증 전**이며, 요구항목은
> 요지 기준으로 정리했다 (조항 부호 a)~p) 수준의 정밀 대조는 후속 작업).
> 법적·인정 심사 목적의 근거 문서가 아니다.

기준 문서:

- KS Q ISO/IEC 17025:2017 §7.8.2 (성적서 공통 요구사항), §7.8.4 (교정성적서 특정 요구사항), §7.8.6 (적합성 진술)
- KOLAS-G-002 (측정결과의 불확도 추정 및 표현을 위한 지침) — MetroAI GUM 엔진 준거 문서
- DCC 스키마 3.3.0 (https://gitlab.com/ptb/dcc/xsd-dcc, 문서: https://wiki.dcc.ptb.de)
- D-SI 2.2.1 (SI_Format.xsd — 수치·단위·불확도 표현)

표기: `dcc:` = https://ptb.de/dcc, `si:` = https://ptb.de/si.
경로는 `dcc:digitalCalibrationCertificate` 루트 기준 축약형.

---

## 1. 공통 기재사항 (ISO/IEC 17025:2017 §7.8.2 요지)

| # | 기재사항 (요지) | DCC 3.3.0 요소 | MetroAI `cert_info` 키 | v1 상태 |
|---|---|---|---|---|
| 1 | 제목 ("교정성적서") | 데이터 포맷에는 별도 '제목' 요소 없음 — 표시계층(렌더링/PDF)에서 처리 | — | 해당 없음(표시계층) |
| 2 | 교정기관 명칭·주소 | `administrativeData/calibrationLaboratory/contact/name·location` | `cal_org`, `cal_org_address`, `cal_org_city` | 지원 |
| 3 | 교정 수행 장소 (자체/현장 등) | `coreData/performanceLocation` (enum: laboratory·customer·laboratoryBranch·customerBranch·other) | `performance_location` (한국어 별칭 "교정실"·"현장" 매핑) | 지원 |
| 4 | 성적서 고유 식별 (성적서 번호) | `coreData/uniqueIdentifier` | `cert_number` | 지원 |
| 4a | 페이지 번호·종료 표시 | 단일 XML 문서 개념 — 페이지 개념 없음. 무결성은 전자서명(ds:Signature)이 대체 | — | 미구현 (서명은 로드맵) |
| 5 | 고객 명칭·연락처 | `administrativeData/customer/name·location` | `client_org`, `client_address`, `client_city` | 지원 |
| 6 | 사용 방법(교정절차) 식별 | `measurementResult/usedMethods/usedMethod/name·norm·reference` | `method_name`, `method_norm`, `method_reference` | 지원 |
| 7 | 교정대상 기술·명확한 식별 (기기명·제작사·모델·기기번호) | `administrativeData/items/item/name·manufacturer·model·identifications` | `equipment_name`, `manufacturer`, `model`, `serial_number`, `equipment_id` | 지원 |
| 8 | 품목 상태 (필요시) | `items/item/description` | — | 미구현 (v2) |
| 9 | 접수일 | `coreData/receiptDate` | `receipt_date` | 지원 |
| 10 | 교정 수행일 | `coreData/beginPerformanceDate·endPerformanceDate` | `cal_date` 또는 `cal_date_begin/end` | 지원 |
| 11 | 발행일 | `coreData/issueDate` | `issue_date` | 지원 |
| 12 | 결과 + 측정단위 | `measurementResult/results/result/data/…/si:real(value·unit)` — 단위는 D-SI 표기 | GUMResult (`measurand_value`, `measurand_unit` → `units.to_dsi_unit`) | 지원 |
| 13 | 방법 추가·이탈·제외 사항 | `administrativeData/statements/statement` | — | 부분 (statements 일반 지원, 전용 키 없음) |
| 14 | 결과 승인자 식별 (서명권자) | `administrativeData/respPersons/respPerson/person/name·role·mainSigner` | `calibrator_name`, `approver_name` | 지원 (역할 고정: 교정담당자/기술책임자) |
| 15 | "결과는 교정된 품목에만 유효" 등 제한 문구 | `statements/statement/declaration` | `traceability_statement` 외 일반 문구는 전용 키 없음 | 부분 |

## 2. 교정성적서 특정 기재사항 (§7.8.4 요지)

| # | 기재사항 (요지) | DCC 3.3.0 요소 | MetroAI 연계 | v1 상태 |
|---|---|---|---|---|
| C1 | **측정불확도** (확장불확도 U, 포함인자 k, 신뢰수준) | `si:real/si:measurementUncertaintyUnivariate/si:expandedMU` (valueExpandedMU·coverageFactor·coverageProbability·distribution) | GUMResult (`expanded_uncertainty`, `coverage_factor`, `confidence_level`) — KOLAS-G-002 계산 결과 그대로 | 지원 |
| C1a | 불확도 예산표 (KOLAS 실무 첨부 관행) | `results/result[@refType='metroai_uncertaintyBudget']/data/list/quantity` (성분별 기여량 \|cᵢ\|·u(xᵢ), u_c, ν_eff) | GUMResult.components | 지원 (MetroAI 자체 refType) |
| C2 | 교정 결과에 영향을 주는 조건 (환경조건: 온도·습도 등) | `measurementResult/influenceConditions/influenceCondition` (refType basic_temperature·basic_humidityRelative) | `ambient_temperature`, `ambient_humidity` | 지원 (온·습도 2종) |
| C3 | **측정 소급성 진술** | `administrativeData/statements/statement/declaration` | `traceability_statement` | 지원 (자유문) |
| C4 | 조정·수리 전/후 결과 (가용 시) | `measurementResults/measurementResult` 복수 블록 (before/after refType) | — | 미구현 (v2) |
| C5 | 적합성 진술 (§7.8.6, 요청 시) | `statement/conformity` + `measurementMetaData/metaData[@refType='basic_conformity']` | — | 미구현 (파서는 statements 일반 해석) |
| C6 | 교정 주기 권고 금지/조건 (합의 시만) | `statement` | — | 미구현 |

## 3. KOLAS 실무 항목 (인정제도 특유)

| # | 항목 | DCC 3.3.0 요소 | v1 상태 |
|---|---|---|---|
| K1 | KOLAS 인정번호 (예: KC-XXX) | `calibrationLaboratory/calibrationLaboratoryCode` | 지원 (`cal_org_kolas_id`) |
| K2 | KOLAS(ILAC-MRA) 인정마크 이미지 | `dcc:document` 또는 contact `descriptionData`(byteData, base64) | 미구현 — 표시계층/차기 |
| K3 | 국문 기재 (필요시 영문 병기) | `coreData/usedLangCodeISO639_1`(ko·en) + `mandatoryLangCodeISO639_1`(ko), 모든 `dcc:content@lang` | 지원 (기본 ko, en 병기 옵션) |
| K4 | 서명 (기술책임자 등 직인·서명) | `ds:Signature` (XML-DSig) — DCC의 법적 효력 핵심 | **미구현 (로드맵 최우선)** — MetroAI `audit/signature.py`(Ed25519)와 별개로 XML-DSig(W3C) 필요 |
| K5 | 국가측정표준 소급 체계 표시 (KRISS 등) | `statement/declaration` + `measuringEquipments/measuringEquipment/certificate`(상위 표준기 성적서 해시 참조) | 부분 (진술문만; 표준기 연결은 파서만 지원) |

## 4. 알려진 갭 및 로드맵 (정직 원칙 — 미구현 명시)

1. **XML-DSig 전자서명 미구현** — 서명 없는 DCC는 초안이다. builder 출력은 `warnings` 확인 후 검토·서명 절차를 별도로 거쳐야 한다.
2. **refType 어휘 정합** — `metroai_*` refType은 자체 어휘다. PTB Good Practice의 `basic_*`/`gp_*` 어휘(CIPM 산하 refType 레지스트리) 정렬은 차기 과제.
3. **다품목·다결과** — builder는 품목 1개·measurementResult 1개만 생성 (파서는 복수 해석 가능).
4. **si:constant / si:complex / byteData 첨부 미해석** (파서 1차 범위 밖).
5. **조항 부호 정밀 대조** — 본 표의 요구항목은 요지 정리이며, KS Q ISO/IEC 17025:2017 원문 및 KOLAS-R 시리즈(성적서 발급 관련 운영요령)와의 문항 단위 대조는 미완.
6. **DCC 3.4.0 대응** — 3.4.0은 현재 RC 단계 (2026-07 기준 wiki.dcc.ptb.de 공지). 정식 릴리스 후 검토.
