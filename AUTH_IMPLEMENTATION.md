# MetroAI 인증 및 사용량 관리 구현

## 개요

MetroAI Streamlit 앱에 로그인/회원가입 기능과 Free 플랜 사용량 제한 (월 3회 계산) 기능을 추가했습니다.

## 설치

### 1. 패키지 설치

`requirements.txt`에 다음 패키지가 추가되었습니다:

```
streamlit-authenticator==0.3.3
pyyaml>=6.0
```

설치:
```bash
pip install -r requirements.txt
```

### 2. 파일 구조

```
metroai/auth/
├── __init__.py                  # 모듈 초기화 및 공개 API
├── auth_manager.py              # 인증 및 사용량 관리 핵심 로직
├── config.yaml                  # 인증 설정 파일 (자동 생성)
└── usage_data.json              # 사용량 데이터 (런타임 생성)

pages/
└── 1_📐_불확도_계산.py         # 인증 통합된 메인 계산 페이지
```

## 주요 기능

### 1. 인증 시스템 (`metroai/auth/auth_manager.py`)

#### `UsageManager` 클래스
- 사용자별 월간 사용량 추적
- JSON 파일 기반 저장소 (외부 DB 불필요)
- 월 리셋 자동 처리

**메서드:**
- `get_usage(username)` - 사용자 사용량 조회
- `check_limit(username, limit=3)` - 사용 가능 여부 확인
- `increment_usage(username)` - 사용량 증가
- `get_remaining(username, limit=3)` - 남은 계산 횟수

#### `AuthManager` 클래스
- streamlit-authenticator 래퍼
- YAML 기반 자격증명 저장소
- 회원가입 기능 포함

**메서드:**
- `get_authenticator()` - 인증자 인스턴스 반환
- `login_widget()` - 로그인 위젯 렌더링
- `signup_widget()` - 회원가입 위젯 렌더링

#### 편의 함수
- `get_auth_manager()` - AuthManager 싱글톤
- `get_usage_manager()` - UsageManager 싱글톤
- `init_auth_state()` - 세션 상태 초기화
- `render_auth_sidebar()` - 사이드바 인증 위젯 (통합)
- `show_usage_info(username)` - 사용량 정보 표시
- `show_guest_notice()` - 게스트 안내 표시

### 2. 로그인/회원가입

#### 기본 자격증명 (테스트용)
- **admin** / `admin123` (기본 관리자)
- **guest** / `guest` (테스트 계정)

자격증명은 `config.yaml`에 저장되며, 자동으로 bcrypt로 해시됩니다.

#### 사이드바 UI
```
🔐 인증
├─ [로그인 탭]
│  └─ 로그인 폼
├─ [회원가입 탭]
│  └─ 회원가입 폼
└─ (로그인 후) 로그아웃 버튼
```

### 3. 사용량 제한

#### Free 플랜
- **월 3회 계산 제한**
- 매월 1일 자동 리셋
- 계산 실행 시 자동 증가

#### 게스트 모드 (로그인 안함)
- **1회 계산만 가능** (세션 내)
- 기록 저장 안함
- "로그인하면 이용 기록이 저장됩니다" 안내 표시

#### 로그인 사용자
- 월 3회 계산 가능
- "이번 달 남은 계산: X/3" 표시
- 계산 기록 저장 (월별 추적)

## 사용량 추적 로직

### 계산 전 확인
```python
can_proceed, msg = check_and_track_calculation(username)
if not can_proceed:
    st.error(msg)  # "한도 초과" 등의 메시지
else:
    # 계산 실행
    ...
```

### 계산 후 증가
```python
increment_calculation_usage(username)
```

## 데이터 저장소

### 1. 인증 설정 (`config.yaml`)
```yaml
credentials:
  usernames:
    admin:
      name: Admin
      password: $2b$12$... (bcrypt 해시)
    ...
cookie:
  expiry_days: 30
  key: metroai_auth_key
  name: metroai_auth_cookie
preauthorized:
  emails: []
```

### 2. 사용량 데이터 (`usage_data.json`)
```json
{
  "user1": {
    "count": 2,
    "month": "2026-04",
    "first_used": "2026-04-05T12:34:56.789012"
  },
  "user2": {
    "count": 0,
    "month": "2026-05",
    "first_used": "2026-05-01T10:00:00"
  }
}
```

## 페이지 통합

### `pages/1_📐_불확도_계산.py` 수정 사항

#### 임포트 추가
```python
from metroai.auth import (
    init_auth_state,
    render_auth_sidebar,
    show_usage_info,
    show_guest_notice,
    get_usage_manager,
)
```

#### 사이드바 통합
- 사이드바 상단에 인증 위젯 렌더링
- 로그인 상태별로 다른 안내 메시지 표시
- 사용량 정보 실시간 업데이트

#### 계산 버튼 수정 (5개 위치)
1. 템플릿 모드 - 블록게이지 (`key="gb_calc"`)
2. 템플릿 모드 - 분동 (`key="mass_calc"`)
3. 템플릿 모드 - 온도계 (`key="temp_calc"`)
4. 템플릿 모드 - 압력계 (`key="pres_calc"`)
5. 직접 입력 모드 (`key="manual_calc"`)
6. 위자드 모드 (`key="wizard_calc"`)

각 버튼 전에 사용량 체크, 성공 후 사용량 증가 로직 추가.

## 테스트 절차

### 1. 환경 설정
```bash
cd /sessions/inspiring-ecstatic-hawking/mnt/Desktop/metroai
pip install -r requirements.txt
```

### 2. 앱 실행
```bash
streamlit run app.py
```

### 3. 테스트 시나리오

#### 게스트 모드
1. 앱 접속 (로그인 안함)
2. 사이드바에 "👤 게스트 모드" 안내 표시 확인
3. 계산 실행 → 성공
4. 다시 계산 시도 → "게스트는 1번의 계산만 가능합니다" 메시지

#### 로그인 모드
1. 사이드바의 "로그인" 탭 클릭
2. `admin` / `admin123` 입력 → 로그인 성공
3. "✅ Admin 로그인됨" 표시 확인
4. "📊 이번 달 남은 계산: 3/3" 표시 확인
5. 계산 3회 실행 → "이번 달 남은 계산: 0/3"
6. 4번째 계산 시도 → "이번 달 계산 한도(3회)를 초과했습니다" 메시지

#### 회원가입
1. 사이드바의 "회원가입" 탭 클릭
2. 새 사용자명/비밀번호 입력 → 회원가입 성공
3. 다시 로그인 탭에서 새 계정으로 로그인

## 주요 설계 결정

### 1. 왜 JSON 저장소인가?
- **MVP 단계**: 외부 DB 불필요
- **간단함**: 파일 기반으로 의존성 최소화
- **확장성**: 나중에 DB로 마이그레이션 가능

### 2. 월 단위 리셋
- GUM 가이드라인과 유사한 교정 주기 개념
- 사용량 추적 시 `month: "2026-04"` 형식 사용
- 새 월이면 자동으로 `count: 0` 초기화

### 3. 게스트 vs 로그인 사용자
- **게스트**: 세션 내 1회 (기록 안함, 장기 추적 불가)
- **로그인**: 월별 기록, 다음 달에 리셋

### 4. 사이드바 통합
- 인증 위젯과 모드 선택을 같은 사이드바에 배치
- 인증 상태가 UI에 즉시 반영됨 (상단 표시)
- 사용량 정보 실시간 업데이트

## 보안 고려사항

### 현재 상태 (MVP)
- ✅ bcrypt 패스워드 해시
- ✅ 세션 쿠키 (30일 만료)
- ⚠️ HTTPS 필수 (프로덕션)
- ⚠️ YAML 파일 보안 (git에서 제외 권장)

### 프로덕션 개선 사항
1. `config.yaml`을 환경 변수로 관리
2. `usage_data.json`을 데이터베이스로 이동
3. HTTPS 강제 적용
4. 관리자 인터페이스 추가
5. IP 기반 레이트 리미팅

## 문제 해결

### 로그인 안됨
- `config.yaml` 파일이 있는지 확인
- bcrypt 해시가 유효한지 확인
- streamlit-authenticator 버전 호환성 확인

### 사용량이 리셋 안됨
- `usage_data.json`의 `month` 값 확인
- 시스템 시간이 올바른지 확인
- JSON 파일 형식이 유효한지 확인

### 회원가입 후 로그인 불가
- `config.yaml`이 올바르게 업데이트되었는지 확인
- 세션 상태 초기화 시도 (페이지 새로고침)

## 향후 개선 사항

### Phase 2
- [ ] 결제 시스템 (Pro 플랜)
- [ ] 사용량 분석 대시보드
- [ ] 이메일 알림 (한도 도달)

### Phase 3
- [ ] PostgreSQL 이동
- [ ] API 토큰 인증
- [ ] SSO (Google, GitHub)

## 참고

- streamlit-authenticator: https://github.com/mkhorasani/Streamlit-Authenticator
- GUM Guide: ISO/IEC Guide 98-3:2008
