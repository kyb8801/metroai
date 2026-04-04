# MetroAI 배포 가이드 — Streamlit Cloud

## 전체 순서
1. GitHub 레포 생성 + 코드 푸시 (5분)
2. Streamlit Cloud 연결 + 배포 (3분)
3. 도메인 확보 + 연결 (선택, 10분)

---

## Step 1: GitHub 레포 생성 + 코드 푸시

### 1-1. GitHub에서 새 레포 생성
1. https://github.com/new 접속
2. Repository name: `metroai`
3. Description: `KOLAS 측정불확도 예산 자동화 도구`
4. **Private** 선택 (나중에 Public 전환 가능)
5. "Create repository" 클릭
6. **나오는 HTTPS URL 복사** (예: `https://github.com/kyb8801/metroai.git`)

### 1-2. 로컬에서 git 초기화 + 푸시
**cmd (명령 프롬프트) 에서:**
```cmd
cd C:\Users\kyb88\Desktop\metroai

git init -b main
git add -A
git commit -m "MetroAI Phase 1 — GUM+MCM 불확도 엔진, PT분석, 교정성적서 PDF"
git remote add origin https://github.com/kyb8801/metroai.git
git push -u origin main
```

> ⚠️ GitHub 로그인 팝업이 뜨면 로그인하세요.
> ⚠️ `kyb8801` 부분은 본인의 GitHub 사용자명으로 교체하세요.

---

## Step 2: Streamlit Cloud 배포

### 2-1. Streamlit Cloud 가입
1. https://share.streamlit.io 접속
2. "Sign up" → **"Continue with GitHub"** 클릭 (GitHub 계정 연결)
3. 약관 동의 후 대시보드 진입

### 2-2. 앱 배포
1. 대시보드에서 **"New app"** 클릭
2. 설정:
   - **Repository:** `kyb8801/metroai` (본인 레포 선택)
   - **Branch:** `main`
   - **Main file path:** `app.py`
3. **"Deploy!"** 클릭
4. 1~2분 기다리면 배포 완료!

### 2-3. 배포 완료 후
- 자동 생성된 URL: `https://kyb8801-metroai-app-xxxxx.streamlit.app`
- 이 URL로 누구나 접속 가능

---

## Step 3: 도메인 연결 (선택)

### 3-1. 도메인 구매
- **가비아** (gabia.com) 또는 **호스팅KR** (hosting.kr)
- `metroai.kr` 또는 `metrolab.kr` 검색 후 구매
- 가격: 약 ₩11,000~22,000/년

### 3-2. Streamlit Cloud에 커스텀 도메인 연결
1. Streamlit Cloud 대시보드 → 앱 선택 → **Settings**
2. "Custom subdomain" 또는 "Custom domain" 설정
3. 도메인 DNS에서 CNAME 레코드 추가:
   - 호스트: `@` 또는 `www`
   - 값: Streamlit이 제공하는 주소
4. 반영까지 최대 24시간 소요

> 💡 도메인은 나중에 해도 됩니다. 먼저 Streamlit 기본 URL로 배포 후 테스트하세요.

---

## 배포 후 체크리스트

- [ ] 메인 랜딩 페이지 접속 확인
- [ ] "지금 시작하기" 버튼 → 불확도 계산 페이지 이동
- [ ] 위자드 모드에서 간단한 계산 테스트
- [ ] 직접입력 모드에서 블록게이지 템플릿 테스트
- [ ] PT 분석 페이지 접속 확인
- [ ] 교정성적서 PDF 생성 테스트
- [ ] 엑셀 출력 다운로드 테스트

---

## 코드 업데이트 방법

코드를 수정한 후:
```cmd
cd C:\Users\kyb88\Desktop\metroai
git add -A
git commit -m "변경 내용 설명"
git push
```
→ Streamlit Cloud가 자동으로 재배포합니다 (1~2분)

---

## 트러블슈팅

### "ModuleNotFoundError" 에러
→ `requirements.txt`에 해당 패키지가 있는지 확인

### 한글 깨짐
→ 교정성적서 PDF 한글 폰트는 `reportlab`의 기본 CID 폰트 사용 중.
   문제 시 NanumGothic.ttf를 프로젝트에 포함하고 경로 수정 필요

### 느린 로딩
→ Streamlit Cloud 무료 티어는 첫 접속 시 30초 정도 걸릴 수 있음 (cold start)
