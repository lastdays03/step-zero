# ActionKit 문서 파싱 가능성 및 RAG 파이프라인 갭 분석

> 작성일: 2026-02-24
> 담당: doc-parser agent

---

## 1. 파일 형식별 분포

### 1.1 전체 요약

| 형식 | 파일 수 | 비율 | 위치 |
|------|---------|------|------|
| PDF  | 39      | 84.8% | `laws/`, `kits/legal/`, `kits/tax/`, `kits/grant/`, `kits/hr/` |
| HWP  | 6       | 13.0% | `kits/hr/` |
| PPTX | 1       | 2.2%  | `kits/hr/` |
| **합계** | **46** | **100%** | |

### 1.2 디렉토리별 분류

**laws/ (법령 원문) - 21개 PDF**
- `laws/chapter-1/` (5): 건축법, 국토계획법, 식품위생법 등
- `laws/chapter-2/` (3): 식품위생법, 시행규칙, 시행령
- `laws/chapter-3/` (3): 소방시설법, 다중이용업소법
- `laws/chapter-4/` (3): 식품위생법, 부가가치세법
- `laws/chapter-5/` (1): 행정조사기본법
- `laws/chapter-6/` (6): 행정기본법, 행정절차법, 행정심판법, 행정소송법

**kits/ (실무 킷) - 25개 (PDF 18 + HWP 6 + PPTX 1)**
- `kits/legal/` (11): 법령 PDF (시행규칙 위주)
- `kits/tax/` (3): 부가가치세 관련 법령 PDF
- `kits/grant/` (3): 소상공인 정책자금/바우처 PDF
- `kits/hr/` (8): 근로계약서, 취업규칙, 4대보험 서식 등 (HWP 6 + PDF 1 + PPTX 1)

### 1.3 HWP 파일 상세

| 파일명 | 크기 | 용도 |
|--------|------|------|
| 개정 표준근로계약서(2025년, 배포).hwp | 68KB | HR 서식 |
| 개정 표준취업규칙(2025년, 배포).hwp | 276KB | HR 서식 |
| (공통서식)+사업장+성립신고서.hwp | 108KB | 4대보험 서식 |
| 4대보험_자격취득신고서_합본.hwp | 100KB | 4대보험 서식 |
| 국민건강보험_직장가입자_보수월액_변경신청서.hwp | 52KB | 건강보험 서식 |
| 두루누리+보험료+지원신청서(국민연금_고용보험).hwp | 52KB | 두루누리 서식 |

### 1.4 PPTX 파일 상세

| 파일명 | 크기 |
|--------|------|
| ★2025년 소규모 사업장을 위한 7가지 노른자 노동법(PPT).pptx | 12MB |

---

## 2. PDF 파싱 테스트 결과

### 2.1 테스트 도구
- **pdfplumber** (기존 RAG 파이프라인에서 사용 중)

### 2.2 전수 테스트 결과

| 분류 | 파일 수 | 비고 |
|------|---------|------|
| 텍스트 기반 (정상 추출) | **39/39** | 100% 성공 |
| 스캔/이미지 기반 (OCR 필요) | **0** | - |
| 혼합 (부분 추출) | **0** | - |
| 오류 | **0** | - |

### 2.3 대표 파일별 추출 결과

| 파일 | 페이지 | 추출 문자 수 | 품질 |
|------|--------|-------------|------|
| 식품위생법 시행규칙 | 324p | 250,557자 | 우수 |
| 부가가치세법 시행규칙 | 151p | 149,397자 | 우수 |
| 건축법 시행규칙 | 176p | 149,191자 | 우수 |
| 부가가치세법 시행령 | 82p | 124,224자 | 우수 |
| 국토계획법 | 65p | 119,278자 | 우수 |
| 건축법 | 52p | 95,363자 | 우수 |
| 소상공인 바우처 매뉴얼 | 20p | 1,957자 | 보통 (디자인 많은 문서) |
| 괴롭힘 인지 점검표 | 4p | 2,347자 | 보통 (서식 문서) |
| 소상공인 바우처 지원사업 | 16p | 14,170자 | 우수 |

### 2.4 PDF 파싱 결론
- **39개 PDF 모두 pdfplumber로 텍스트 추출 가능** (추가 OCR 불필요)
- 법령 PDF는 국가법령정보센터 출력본으로, 텍스트 레이어가 잘 포함됨
- 일부 디자인 위주 PDF (바우처 매뉴얼)는 추출 텍스트가 적지만 사용 가능 수준
- **기존 `law_fetcher.py`의 `_extract_text_from_pdf()` 그대로 사용 가능**

---

## 3. HWP 파싱 방안 분석

### 3.1 라이브러리 비교 매트릭스

| 라이브러리 | PyPI | HWP 지원 | HWPX 지원 | 텍스트 추출 품질 | 난이도 | 상태 |
|-----------|------|----------|-----------|----------------|--------|------|
| **olefile + 수동 파싱** | `olefile` 0.47 | O (OLE2 기반) | X | 중~상 | 중 | 유지보수 중 |
| **pyhwp (hwp5txt)** | `pyhwp` | O | X | 상 | 하 (CLI) | 오래된 코드, 제한적 유지보수 |
| **python-hwpx** | `python-hwpx` | X | O (HWPX만) | 상 | 하 | 활발히 개발 중 (2024~) |
| **pyhwpx** | `pyhwpx` | O | O | 상 | 중 | Windows 한/글 COM 필요 |

### 3.2 각 방안 상세

#### 방안 A: olefile + 수동 바이너리 파싱 (추천)
```
의존성: olefile (pip install olefile)
원리: HWP는 OLE2 Compound File → BodyText/Section0,1,... 스트림에서 바이너리 파싱
장점: 순수 Python, 크로스플랫폼, 경량
단점: 표(Table) 구조 추출 어려움, 이미지 추출 불가
텍스트 추출 방법:
  1) PrvText 스트림 → UTF-16 디코딩 (간편하지만 서식 정보 손실)
  2) BodyText/Section* → zlib 해제 + 레코드 파싱 (더 정확)
```

**핵심 코드 패턴:**
```python
import olefile

# 방법 1: PrvText 스트림 (간편)
f = olefile.OleFileIO('file.hwp')
text = f.openstream('PrvText').read().decode('utf-16')

# 방법 2: BodyText 섹션 파싱 (정확)
# → zlib 압축 해제 후 struct.unpack으로 레코드 타입별 텍스트 추출
```

#### 방안 B: pyhwp / hwp5txt (CLI 기반)
```
의존성: pyhwp (pip install --pre pyhwp)
원리: hwp5txt CLI 도구로 HWP → TXT 변환
장점: 사용 간편, 텍스트 품질 좋음
단점: Python 3 호환성 이슈 보고됨, 마지막 업데이트 오래됨
       subprocess 호출 필요
```

#### 방안 C: python-hwpx (HWPX 전용)
```
의존성: python-hwpx (pip install python-hwpx)
원리: HWPX(OWPML/OPC 기반 XML) 직접 파싱
장점: 최신, 활발한 개발, 크로스플랫폼
한계: .hwp 바이너리 지원 안 함 (HWPX만)
현재 파일: 6개 모두 .hwp (바이너리) → 직접 사용 불가
```

### 3.3 HWP 파싱 추천 전략

**1순위: olefile + PrvText 스트림** (가장 실용적)
- 6개 HWP 파일 모두 서식 문서 (양식 텍스트 추출이 주 목적)
- PrvText 스트림은 모든 HWP에 존재하며 UTF-16으로 전체 텍스트 포함
- 별도 바이너리 파싱 없이 2줄 코드로 추출 가능
- 표 구조는 유실되지만, RAG 검색용 텍스트 추출에는 충분

**2순위: olefile + BodyText 섹션 파싱**
- 표 경계 등 구조 정보가 필요한 경우
- 복잡도 증가하지만 더 정확한 텍스트 추출

**비추천: pyhwpx** (Windows + 한/글 설치 필요 → 서버 환경에서 사용 불가)

---

## 4. PPTX 파싱 방안 분석

### 4.1 라이브러리: python-pptx

| 항목 | 내용 |
|------|------|
| PyPI | `python-pptx` (활발히 유지보수) |
| 슬라이드별 텍스트 | O (slide.shapes 순회) |
| 표 텍스트 | O (table.cell.text) |
| 노트 | O (slide.notes_slide) |
| 이미지 텍스트 | X (OCR 별도 필요) |
| 차트 데이터 | 제한적 |

### 4.2 텍스트 추출 코드 패턴
```python
from pptx import Presentation

prs = Presentation('file.pptx')
for slide_idx, slide in enumerate(prs.slides):
    text_parts = []
    for shape in slide.shapes:
        if shape.has_text_frame:
            for paragraph in shape.text_frame.paragraphs:
                text_parts.append(paragraph.text)
        if shape.has_table:
            for row in shape.table.rows:
                for cell in row.cells:
                    text_parts.append(cell.text)
    slide_text = '\n'.join(text_parts)
```

### 4.3 PPTX 파싱 결론
- **python-pptx로 텍스트 추출 충분히 가능**
- 대상 파일이 12MB PPTX 1개 (노동법 교육 자료)
- 교육용 PPT이므로 텍스트 위주 → 추출 품질 높을 것으로 예상
- 이미지 내 텍스트는 OCR 없이는 추출 불가하나, 제목/본문 텍스트만으로 RAG 검색에 충분

---

## 5. 기존 RAG 파이프라인 분석

### 5.1 현재 아키텍처

```
데이터 소스                  ETL                     벡터 DB               검색
─────────                ─────                   ──────              ─────
.temp/ (MD/PDF)  →  LocalFileSource  →  LawETLProcessor  →  PGVector  →  RagService
                    (law_fetcher.py)    (law_etl.py)      (vector_store.py)  (rag_service.py)
```

### 5.2 주요 컴포넌트

| 컴포넌트 | 파일 | 역할 | 지원 형식 |
|----------|------|------|-----------|
| `LocalFileSource` | `app/services/law_fetcher.py` | 파일 탐색 + 텍스트 추출 | PDF, MD |
| `LawETLProcessor` | `app/services/law_etl.py` | LLM으로 법령→가이드 변환 | 텍스트 입력 |
| `VectorStoreService` | `app/services/vector_store.py` | PGVector 임베딩 저장 | Document 객체 |
| `RagService` | `app/features/rag/application/rag_service.py` | 질의 응답 체인 | PGVector 검색 |

### 5.3 현재 데이터 경로
- **기존**: `.temp/` 디렉토리 (카테고리별 하위 폴더, MD/PDF)
- **ActionKit**: `uploads/actionkit/` (laws/chapter-N/, kits/카테고리/아이템ID/vN/)

### 5.4 주요 한계점
1. **형식 제한**: PDF와 MD만 지원, HWP/PPTX는 `continue`로 스킵
2. **카테고리 추출**: 경로의 첫 번째 디렉토리를 카테고리로 사용 → ActionKit 구조에 맞지 않음
3. **경로 하드코딩**: `.temp/` 경로 기반 설계
4. **중복 파일**: ActionKit에 같은 법령이 laws/와 kits/ 양쪽에 존재 (중복 임베딩 위험)

---

## 6. RAG 파이프라인 확장에 필요한 변경사항

### 6.1 변경 목록

| # | 변경 대상 | 현재 상태 | 필요 변경 | 난이도 | 우선순위 |
|---|----------|-----------|-----------|--------|---------|
| 1 | `law_fetcher.py` - 형식 지원 | PDF, MD만 | HWP, PPTX 추가 | 중 | P0 |
| 2 | `law_fetcher.py` - 경로/카테고리 | `.temp/` 첫 디렉토리 | ActionKit 경로 구조 파싱 | 하 | P0 |
| 3 | `law_fetcher.py` - root_dir | 단일 디렉토리 | 다중 소스 지원 or 경로 변경 | 하 | P0 |
| 4 | `law_etl.py` - 프롬프트 | 법령 원문 → 가이드 변환 | 서식/교육자료 등 문서 유형별 프롬프트 | 중 | P1 |
| 5 | 중복 파일 처리 | 없음 | 파일 해시 또는 제목 기반 중복 제거 | 중 | P1 |
| 6 | `config.py` | `.temp/` 관련 설정 | ACTIONKIT_STORAGE_PATH 활용 | 하 | P0 |
| 7 | 의존성 추가 | pdfplumber | + olefile, python-pptx | 하 | P0 |

### 6.2 상세 변경 내역

#### 변경 1: HWP/PPTX 파서 추가 (`law_fetcher.py`)

```python
# 추가할 메서드 (개념)
def _extract_text_from_hwp(self, file_path: Path) -> str:
    """olefile + PrvText 스트림으로 HWP 텍스트 추출"""
    import olefile
    f = olefile.OleFileIO(str(file_path))
    text = f.openstream('PrvText').read().decode('utf-16')
    f.close()
    return text

def _extract_text_from_pptx(self, file_path: Path) -> str:
    """python-pptx로 슬라이드별 텍스트 추출"""
    from pptx import Presentation
    prs = Presentation(str(file_path))
    texts = []
    for slide in prs.slides:
        for shape in slide.shapes:
            if shape.has_text_frame:
                texts.append(shape.text_frame.text)
    return '\n\n'.join(texts)
```

#### 변경 2: 카테고리 매핑 로직

```
현재: .temp/{카테고리}/{하위}/{파일} → 카테고리 = parts[0]
필요: uploads/actionkit/laws/chapter-N/{id}/v{ver}/{파일} → "법령-챕터N"
      uploads/actionkit/kits/{category}/{id}/v{ver}/{파일} → "킷-{category}"
```

#### 변경 3: 중복 파일 처리
- 같은 법령이 `laws/`와 `kits/` 양쪽에 존재
- 예: `건축법(법률)(제21035호)` → `laws/chapter-1/1/` + `kits/legal/22/`
- **방안**: 파일명 기반 중복 제거 또는 해시 비교

---

## 7. 파일 형식별 파싱 가능성 매트릭스 (종합)

| 형식 | 파일 수 | 파싱 라이브러리 | 텍스트 추출 난이도 | 한계 | RAG 적합성 |
|------|---------|----------------|-------------------|------|-----------|
| **PDF** | 39 | pdfplumber (기존) | **쉬움** - 변경 불필요 | 디자인 PDF 일부 추출량 적음 | **높음** |
| **HWP** | 6 | olefile (신규) | **보통** - 2줄 코드 | 표 구조 유실, 서식 레이아웃 유실 | **보통** (텍스트 중심 추출) |
| **PPTX** | 1 | python-pptx (신규) | **쉬움** - 표준 라이브러리 | 이미지 내 텍스트 불가 | **높음** |

---

## 8. 추천 파싱 전략 (우선순위 포함)

### Phase 1: PDF 경로 확장 (난이도: 하, 즉시 실행 가능)
- `LocalFileSource`의 `root_dir`을 `uploads/actionkit/`으로 지정
- 카테고리 추출 로직을 ActionKit 경로 구조에 맞게 수정
- 중복 파일 제거 로직 추가
- **효과: 39개 PDF (84.8%) 즉시 RAG 편입**

### Phase 2: HWP 파서 추가 (난이도: 중, 1-2시간)
- `olefile` 의존성 추가
- `_extract_text_from_hwp()` 메서드 추가 (PrvText 스트림 방식)
- 6개 HWP 서식 문서 텍스트 추출
- **효과: 6개 HWP (13.0%) 추가 편입**

### Phase 3: PPTX 파서 추가 (난이도: 하, 30분)
- `python-pptx` 의존성 추가
- `_extract_text_from_pptx()` 메서드 추가
- 1개 PPTX 교육자료 텍스트 추출
- **효과: 1개 PPTX (2.2%) 추가 편입 → 전체 46개 100% 커버**

### Phase 4: ETL 프롬프트 최적화 (난이도: 중, 선택)
- `LawETLProcessor`의 프롬프트를 문서 유형별로 분기
- 법령 원문 vs 서식 문서 vs 교육 자료 별 다른 변환 전략
- 서식 문서는 "가이드 변환" 대신 "서식 사용법 설명" 프롬프트

---

## 9. 추가 의존성 요약

```
# pyproject.toml 또는 requirements.txt에 추가 필요
olefile>=0.47       # HWP 파싱용
python-pptx>=1.0.0  # PPTX 파싱용
# pdfplumber는 이미 설치되어 있음
```

---

## 10. 리스크 및 고려사항

| 리스크 | 영향 | 대응 |
|--------|------|------|
| HWP 파일이 OLE2가 아닌 경우 (HWPX) | olefile 파싱 실패 | 확장자 .hwp이므로 OLE2일 가능성 높음. 실패 시 python-hwpx fallback |
| HWP 서식 문서의 텍스트가 양식 라벨만 추출 | RAG 품질 저하 | 서식 문서는 "이 서식의 용도와 작성법" 메타데이터와 함께 저장 |
| 12MB PPTX의 이미지 내 텍스트 누락 | 교육 내용 일부 유실 | 이미지가 많을 경우 OCR (pytesseract) 2차 적용 고려 |
| 중복 임베딩 (같은 법령 2번 저장) | 벡터 DB 비효율, 검색 중복 | 파일명/해시 기반 중복 제거 필수 |
| 대용량 PDF (250K+ chars) 청킹 | LLM 컨텍스트 초과 | law_etl.py에서 이미 `content_body[:10000]` 잘라서 사용 중 |
