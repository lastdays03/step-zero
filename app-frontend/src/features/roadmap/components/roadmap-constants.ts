/* ─── Suggestion Chips ─── */

/** EmptyHero page recommendation keywords */
export const HERO_SUGGESTIONS = ["카페 프랜차이즈", "SaaS 스타트업", "온라인 의류 쇼핑몰", "샐러드 배달 전문점"] as const;

/** Per-field suggestion chips for the ChatIntake form */
export const INTAKE_FIELD_SUGGESTIONS: Record<string, string[]> = {
    business_type: ["카페", "온라인 쇼핑몰", "SaaS"],
    location: ["서울 마포구", "서울 강남구", "부산 해운대구"],
    startup_type: ["개인사업자", "법인", "미정"],
    open_timeline: ["3개월 내", "6개월 내", "1년 내"],
    budget_range: ["3천만 원 이하", "1억 이하", "1억 이상"],
};

/* ─── Error Messages ─── */

export const VALIDATE_FALLBACK_MESSAGE = "입력값 검증에 실패했습니다. 업종/지역 정보를 다시 확인해 주세요.";

export function mapJobFailureMessage(errorCode?: string | null, errorMessage?: string | null): string {
    if (errorMessage?.trim()) return errorMessage;
    switch (errorCode) {
        case "QUEUE_UNAVAILABLE":
            return "작업 대기열 연결이 불안정합니다. 잠시 후 다시 시도해 주세요.";
        case "VALIDATION_FAILED":
            return VALIDATE_FALLBACK_MESSAGE;
        case "GENERATION_TIMEOUT":
            return "로드맵 생성 시간이 초과되었습니다. 다시 시도해 주세요.";
        case "GENERATION_FAILED":
            return "AI 로드맵 생성 중 오류가 발생했습니다. 다시 시도해 주세요.";
        default:
            return "로드맵 생성에 실패했습니다. 잠시 후 다시 시도해 주세요.";
    }
}
