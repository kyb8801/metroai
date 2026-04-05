# MetroAI 인증 시스템 빠른 시작

## 설치 (1분)

```bash
cd /sessions/inspiring-ecstatic-hawking/mnt/Desktop/metroai
pip install -r requirements.txt
```

## 실행 (30초)

```bash
streamlit run app.py
```

## 테스트 계정

| 계정 | 비밀번호 | 용도 |
|---|---|---|
| `admin` | `admin123` | 관리자/테스트 |
| `guest` | `guest` | 게스트/테스트 |

## 주요 기능

### 1️⃣ 로그인/회원가입
- 사이드바의 🔐 인증 섹션에서 진행
- 새 계정 생성 가능

### 2️⃣ 사용량 제한
| 사용자 | 월 계산 횟수 |
|---|---|
| 게스트 | 1회 |
| 로그인 | 3회 |

### 3️⃣ 실시간 표시
- 로그인 상태: ✅ 또는 👤
- 남은 계산: 📊 X/3

## 파일 위치

```
metroai/auth/
├── auth_manager.py    ← 핵심 로직
├── __init__.py        ← 공개 API
├── config.yaml        ← 설정 (자동)
└── usage_data.json    ← 데이터 (자동)
```

## 코드 통합 (페이지에서)

```python
from metroai.auth import (
    init_auth_state,
    render_auth_sidebar,
    show_usage_info,
    check_and_track_calculation,
    increment_calculation_usage,
)

# 사이드바 인증 위젯
init_auth_state()
username, name = render_auth_sidebar()

# 계산 전 확인
can_proceed, msg = check_and_track_calculation(username)
if not can_proceed:
    st.error(msg)
else:
    # 계산 실행...
    result = calculate()
    # 계산 후 증가
    increment_calculation_usage(username)
```

## 문제 해결

### Q: 패키지를 찾을 수 없다
```bash
pip install streamlit-authenticator==0.3.3 pyyaml
```

### Q: 로그인이 안 된다
1. 사용자명/비밀번호 확인
2. 페이지 새로고침
3. 브라우저 캐시 삭제

### Q: 사용량이 저장 안 됨
1. `metroai/auth/` 디렉토리 권한 확인
2. `usage_data.json` 파일 형식 확인

## 더 알아보기

| 문서 | 내용 |
|---|---|
| `AUTH_IMPLEMENTATION.md` | 상세 기술 문서 |
| `TEST_AUTH_MANUAL.md` | 테스트 가이드 |
| `IMPLEMENTATION_SUMMARY.md` | 구현 요약 |

## 트러블슈팅 체크리스트

- [ ] `requirements.txt` 의존성 설치됨
- [ ] `metroai/auth/config.yaml` 존재
- [ ] `pages/1_📐_불확도_계산.py` 수정됨
- [ ] Streamlit 버전 >= 1.30
- [ ] Python 버전 >= 3.8

## 다음 단계

### 즉시 가능
- [x] 로그인/회원가입 테스트
- [x] 사용량 제한 테스트
- [x] 데이터 저장 확인

### 향후 추가 (로드맵)
- [ ] 다른 페이지에도 적용
- [ ] Pro 플랜 추가
- [ ] PostgreSQL 마이그레이션
- [ ] 결제 시스템 통합

---

**🚀 준비 완료!** 이제 MetroAI에서 사용자 인증과 사용량 관리를 이용할 수 있습니다.
