---
title: Action Kit Quick Preview Feature
description: Specifications and implementation plan for the Action Kit Quick Preview Modal
---

# Action Kit Quick Preview Feature (액션키트 퀵 프리뷰)

## 1. 개요 (Overview)
현재 Action Kit Library는 파일의 제목과 요약만 제공하여 사용자가 다운로드하기 전 문서의 내용을 파악하기 어렵습니다. 
이를 해결하기 위해 사용자가 Action Kit 카드를 클릭했을 때, 파일의 미리보기 이미지와 간략한 사용 가이드를 제공하는 **Quick Preview Modal (퀵 프리뷰 모달)**을 구현합니다.

## 2. 사용자 경험 (UX Flow)
1. **탐색:** 사용자가 Action Kit Library 페이지에서 카드를 살펴봅니다.
2. **미리보기 접근:** 
   - 사용자가 카드 영역 전체를 클릭하면 Quick Preview Modal이 부드럽게 열립니다.
   - 단, 기존의 다운로드 버튼(아이콘) 클릭 시에는 모달 없이 바로 다운로드가 실행되도록 유지합니다.
3. **정보 확인 (모달 내부):**
   - **좌측:** 문서의 견본 이미지 또는 스크린샷 1장을 확인하여 문서 포맷을 시각적으로 파악합니다.
   - **우측:** 문서의 카테고리(태그), 제목, 상세 설명, 그리고 3단계(사용 방법) 가이드, 업데이트 날짜 및 파일 크기 정보를 확인합니다.
4. **액션:** 정보를 확인한 후, 우측 하단의 큰 **[다운로드]** 버튼을 클릭하여 파일을 다운로드합니다. 이 때 모달이 닫히거나 다운로드가 진행됩니다.
   - 우측 상단의 [X] 버튼을 눌러 모달을 닫고 원래 화면으로 돌아갈 수 있습니다.

## 3. 화면 구성안 (UI Layout - Modal)
반응형 레이아웃을 적용하여 데스크탑에서는 좌우 2단(Two-Column), 모바일에서는 상하 배치되도록 설계합니다.

*   **[좌측 영역] Visual Preview (시각적 미리보기)**
    *   기본 placeholder 이미지 적용 (추후 실제 데이터의 `previewImageUrl`로 교체 가능하도록 설계).
    *   회색 배경에 둥근 모서리, 은은한 그림자로 문서 느낌 강조.
    *   중앙 확대 아이콘(`ZoomIn`) 배치.

*   **[우측 영역] Quick Guide & Details**
    *   **헤더:** `[태그]` 및 뱃지(예: D-day, 확장자 타입).
    *   **제목:** `Card`의 `name` 데이터 매핑 (h2 스타일).
    *   **상세 설명:** `Card`의 `summary` 데이터 자세히 표시.
    *   **💡 사용 팁 (How to Use):** 기본 3단계 텍스트 노출 (추후 확장 가능).
    *   **메타 정보:** 파일 크기(`size`), 업데이트 예정일 정보 등 하단 배치.
    *   **액션 영역:** 크고 눈에 띄는 파란색 다운로드(`Download`) 버튼.

## 4. 데이터 구조 변경 사항 (Data Types)
프리뷰에 필요한 추가 비주얼 정보를 위해 기존 `ActionKitItem` 또는 관련 타입 정의에 프리뷰 이미지 경로를 추가할 수 있도록 준비합니다. (현재는 구현 편의상 로컬 상태(Dummy data) 또는 기존 데이터를 최대한 활용)

```typescript
// 추후 반영될 수 있는 형태
interface ActionKitPreviewData {
   previewImageUrl?: string;
   usageTips?: string[];
}
```

## 5. 구현 계획 (Implementation Steps)
1.  **공용 UI 점검:** `@/components/ui/dialog` 컴포넌트(shadcn/ui 기반)가 존재하는지 확인. (이미 존재함이 확인됨)
2.  **모달 상태 관리 추가:** `ActionKitLibraryView.tsx` 내에 선택된 아이템을 추적하는 state (`selectedPreviewItem`)와 모달 가시성 상태 제어 변수 추가.
3.  **UI 렌더링 작성 (Modal 내부):** `Dialog`, `DialogContent`, `DialogHeader`, `DialogTitle` 등을 활용하여 Quick Preview 레이아웃 코딩.
4.  **클릭 이벤트 바인딩:**
    - Action Kit 카드의 `onClick` 이벤트에 `setPreviewItem` 함수 연결.
    - 기존 다운로드 버튼의 `onClick` 이벤트 내에 `e.stopPropagation()`이 제대로 동작하여 클릭 이벤트 버블링을 막는지 확인.
5.  **테스트 및 보완:** 모달 열림/닫힘 액션 확인 및 반응형 디자인 적용 확인.
