# PDF 생성 스크립트 사용 가이드

## 개요

`create_kolas_pdf.py`는 MetroAI의 KOLAS-G-001 2025 개정 변경사항 정리 PDF를 자동 생성합니다.

## 스크립트 구성

### 1. 한글 폰트 등록
```python
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

font_path = "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf"
pdfmetrics.registerFont(TTFont('KoreanFont', font_path))
```

- **사용 폰트**: DroidSansFallbackFull (CJK 전체 지원)
- **대체 폰트**: NanumGothic (시스템에 설치된 경우)

### 2. 스타일 정의

#### title_style
- 크기: 28pt
- 색상: #667eea (Professional Blue)
- 용도: 메인 제목

#### heading1_style / heading2_style
- 크기: 16pt / 13pt
- 색상: #667eea
- 용도: 섹션 제목

#### body_style / body_left_style
- 크기: 11pt
- 행높이: 16pt
- 정렬: 양쪽 정렬 / 좌측 정렬
- 용도: 본문 텍스트

### 3. 페이지 구성

| 페이지 | 제목 | 내용 |
|--------|------|------|
| 1 | 타이틀 페이지 | MetroAI 브랜딩, 제목, 발행 정보 |
| 2 | 개요 | KOLAS-G-001 설명, 개정 배경 |
| 3 | 요약표 | 7개 항목 비교 테이블 |
| 4 | 불확도 상세 | GUM/MCM/불확도예산표/CMC |
| 5 | 디지털 전환 | DCC/EDMS/ALCOA+ |
| 6 | 체크리스트 | 9개 항목 실무 체크리스트 |
| 7 | MetroAI 소개 | 플랫폼 기능, 가격, 연락처 |

### 4. 테이블 스타일

```python
TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), HexColor('#667eea')),  # 헤더
    ('TEXTCOLOR', (0, 0), (-1, 0), white),
    ('BACKGROUND', (0, 1), (-1, 1), HexColor('#f0f2f8')),  # 줄 번갈아
    # ...
])
```

- 헤더: 파란 배경 + 흰 글자
- 본문: 흰색 / 밝은 파란색 번갈아 (가독성 향상)

### 5. 페이지 번호 및 헤더/푸터

```python
def add_page_number(canvas, doc):
    canvas.setFont('KoreanFont', 9)
    page_number = doc.page
    
    # 하단 우측: 페이지 번호
    canvas.drawRightString(A4[0] - 1*cm, 0.7*cm, f"페이지 {page_number}")
    
    # 상단 좌측: MetroAI 브랜딩
    canvas.drawString(1.5*cm, A4[1] - 0.8*cm, "MetroAI")
```

## 설정 변경 방법

### 출력 경로 변경

```python
output_path = "/새로운/경로/파일명.pdf"
```

### 색상 변경

```python
primary_color = HexColor('#667eea')  # 파란색
secondary_color = HexColor('#f0f2f8')  # 밝은 파란색
```

### 폰트 변경

```python
# NanumGothic 사용
font_path = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
```

### 페이지 크기 변경

```python
from reportlab.lib.pagesizes import letter, A4, A3
doc = SimpleDocTemplate(output_path, pagesize=letter)  # Letter 크기
```

## 의존성 설치

```bash
pip install reportlab
```

## 실행 방법

### 1. 기본 실행
```bash
python3 create_kolas_pdf.py
```

### 2. 출력 경로 확인
```bash
ls -lh /sessions/inspiring-ecstatic-hawking/mnt/Desktop/metroai/static/
```

### 3. PDF 검증
```bash
pdfinfo KOLAS_G001_2025_변경사항_정리.pdf
file KOLAS_G001_2025_변경사항_정리.pdf
```

## 커스터마이징 예제

### 새로운 섹션 추가

```python
elements.append(Paragraph('새 섹션 제목', heading1_style))
elements.append(Spacer(1, 0.3*cm))

content = Paragraph(
    '새로운 내용...',
    body_style
)
elements.append(content)
```

### 이미지 추가

```python
from reportlab.platypus import Image

img = Image('/경로/이미지.png', width=10*cm, height=6*cm)
elements.append(img)
```

### 텍스트 박스 (Tip/Warning)

```python
from reportlab.platypus import Paragraph

warning = Paragraph(
    '<b><font color="#ff0000">주의:</font></b><br/>'
    '중요한 내용...',
    body_style
)
elements.append(warning)
```

## 문제 해결

### 한글이 깨짐

- 폰트 경로 확인: `find /usr/share/fonts -name "*.ttf" | grep -i nanum`
- 대체 폰트 사용: DroidSansFallbackFull (기본값)
- 폰트 설치: `apt-get install fonts-nanum` (권한 필요)

### PDF가 생성 안 됨

- reportlab 설치 확인: `pip list | grep reportlab`
- 출력 경로 권한 확인: `chmod 755 /경로/`
- 디렉토리 생성: `mkdir -p /경로/`

### 테이블 행이 겹침

- 셀 높이 조정: `rowHeights=[1.5*cm, ...]`
- 폰트 크기 줄임: `fontsize=9` → `fontsize=8`

## 성능 최적화

### PDF 파일 크기 압축

```python
doc = SimpleDocTemplate(
    output_path,
    pagesize=A4,
    compress=True  # 압축 활성화
)
```

### 이미지 최적화

```python
img = Image('/경로/이미지.png', width=10*cm, height=6*cm)
img._restrictSize(10*cm, 6*cm)  # 크기 제한
```

---

**Last Updated**: 2026-04-05
**Version**: 1.0
**Author**: MetroAI
