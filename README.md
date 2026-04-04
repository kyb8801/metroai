# 📐 MetroAI — KOLAS 측정불확도 예산 자동화

> **"KOLAS 불확도 예산서, 5분 만에."**

한국 KOLAS 인정기관을 위한 측정불확도 예산 자동화 웹 도구입니다.

## 주요 기능

1. **GUM 자동 계산** — sympy 기반 편미분 자동 계산, 합성불확도, Welch-Satterthwaite 유효자유도, 확장불확도를 한 번에 산출합니다.
2. **MCM 검증** — 몬테카를로 시뮬레이션(GUM Supplement 1)으로 GUM 결과를 교차 검증합니다.
3. **KOLAS 양식 출력** — KOLAS-G-002 양식 불확도 예산표를 엑셀/PDF로 자동 생성합니다.
4. **위자드 모드** — GUM을 몰라도 단계별 질문으로 불확도 예산표를 작성할 수 있습니다.
5. **숙련도시험(PT) 분석** — z-score, En number, ζ-score 자동 계산 및 판정 (ISO 13528, ISO 17043).
6. **교정성적서 PDF** — KOLAS 양식 교정성적서를 PDF로 자동 생성합니다.
7. **다양한 교정 분야 템플릿** — 블록게이지, 분동, 온도계, 압력계 교정 불확도 템플릿 내장.

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
