---
title: Action Kit Law Snippet Feature
description: Specifications and implementation plan for the contextual law preview snippets
---

# Action Kit Law Snippet (법률 스니펫 미리보기) ⚖️

## 1. 개요 (Overview)
사용자가 액션 키트(실무 양식)를 보다가 관련 법령을 클릭했을 때, 페이지를 이동하기 전 해당 법령의 **핵심 내용과 법적 근거**를 즉시 파악할 수 있도록 팝오버(Popover) 또는 툴팁 형태의 미리보기를 제공합니다.

## 2. 주요 기능 (Key Features)
- **부드러운 호버/클릭 효과:** 관련 법률 태그에 마우스를 올리거나 클릭할 때 세련된 정보 창이 나타납니다.
- **핵심 조문 요약:** 해당 법령 가이트 전체로 가기 전, 이 서식과 직접적으로 관련된 법 조항의 핵심 문구를 보여줍니다.
- **맥락 유지:** 탭 이동 없이 액션 키트 모달 안에서 법적 근거를 확인하여 학습 흐름이 끊기지 않게 합니다.

## 3. UI/UX 디자인
- **Shadcn UI Popover 활용:** 단순 툴팁보다 풍부한 정보를 담기 위해 Popover 컴포넌트를 사용하여 조문 번호, 핵심 요약, '자세히 보기' 버튼 등을 포함합니다.
- **Rich Aesthetics:** Glassmorphism 스타일과 브랜드 컬러(#36a4f2)를 활용한 입체감 있는 카드 형태.
- **마이크로 애니메이션:** 정보 창이 나타날 때의 부드러운 Fade & Slide 효과.

## 4. 데이터 구조 (Proposed)
`RelatedLaw` 타입에 이미 `summary`가 존재하므로, 이를 확장하여 더 상세한 조문 정보를 담을 수 있도록 합니다.

```typescript
interface RelatedLaw {
    name: string;        // 예: "근로기준법 제17조"
    summary: string;     // 예: "근로조건의 명시"
    snippet?: string;     // 예: "사용자는 근로계약을 체결할 때 근로자에게 다음 각 호의 사항을 명시하여야 한다..."
}
```

## 5. 구현 단계 (Implementation Steps)
1. **Types 업데이트:** `ActionKitItem` 관련 타입에 `snippet` 필드 추가.
2. **UI 컴포넌트 개발:** `LawSnippetPopover.tsx` (커스텀 팝오버) 생성.
3. **Library View 통합:** `ActionKitLibraryView`에서 법령 태그에 팝오버 적용.
4. **Mock 데이터 시딩:** 주요 액션 키트에 풍부한 조문 스니펫 데이터 추가.

---
이 기능은 "실무 도구와 법적 근거의 유기적 결합"이라는 우리 플랫폼의 정체성을 가장 시각적으로 잘 보여주는 기능이 될 것입니다.
