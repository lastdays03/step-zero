import type { ReadinessInfo } from "./roadmap-utils";

/* ─── Suggestion Chips ─── */

/** EmptyHero page recommendation keywords */
export const HERO_SUGGESTIONS = ["카페 프랜차이즈", "SaaS 스타트업", "온라인 의류 쇼핑몰", "샐러드 배달 전문점"] as const;

/** Per-field suggestion chips for the ChatIntake form */
export const INTAKE_FIELD_SUGGESTIONS: Record<string, string[]> = {
    business_type: ["카페", "온라인 쇼핑몰", "SaaS"],
    location: ["서울 마포구", "서울 강남구", "부산 해운대구"],
    startup_type: ["개인사업자", "법인", "미정"],
    startup_method: ["신규 창업", "양수양도", "프랜차이즈"],
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

/* ─── Endowed Progress ─── */

export const ENDOWED_STEPS = 3;
export const ENDOWED_LABELS = ["비즈니스 정보 수집", "업종별 규제 분석", "맞춤 로드맵 설계"];

/* ─── Readiness Levels ─── */

export const READINESS_LEVELS: ReadinessInfo[] = [
    { level: 1, emoji: "🌱", label: "아이디어", description: "창업 아이디어를 구체화하는 단계" },
    { level: 2, emoji: "📋", label: "준비 착수", description: "필요한 절차를 파악하고 있는 단계" },
    { level: 3, emoji: "📝", label: "서류 준비 중", description: "서류와 인허가를 준비하는 단계" },
    { level: 4, emoji: "✅", label: "인허가 완료", description: "주요 인허가가 완료된 단계" },
    { level: 5, emoji: "🚀", label: "창업 준비 완료", description: "사업 시작을 위한 모든 준비가 끝난 단계" },
];

/* ─── Milestone Insights ─── */

export const MILESTONE_INSIGHTS: Record<string, string[]> = {
    default: [
        "한 단계를 끝내면 다음 단계가 훨씬 수월해집니다. 계속 진행해보세요!",
        "지금까지의 진행 속도라면, 목표보다 빠르게 준비를 마칠 수 있습니다.",
        "창업 준비의 가장 어려운 부분은 '시작'입니다. 이미 해내고 있습니다!",
        "꾸준히 진행 중이시네요. 이 기세를 이어가세요!",
        "다음 단계도 곧 완료할 수 있습니다. 화이팅!",
    ],
};

/* ─── Intake Confirmation Messages ─── */

export const INTAKE_CONFIRMATION_MESSAGES: Record<string, (value: string) => string> = {
    business_type: (v) => `업종을 '${v}'(으)로 설정합니다.`,
    location: (v) => `지역을 '${v}'(으)로 설정합니다.`,
    startup_type: (v) => `창업 형태를 '${v}'(으)로 설정합니다.`,
    startup_method: (v) => `창업 방식을 '${v}'(으)로 설정합니다.`,
    open_timeline: (v) => `오픈 목표를 '${v}'(으)로 설정합니다.`,
    budget_range: (v) => `초기 예산을 '${v}'(으)로 설정합니다.`,
};

/* ─── Stage Messages ─── */

export const STAGE_MESSAGES: Record<string, string> = {
    QUEUED: "로드맵 생성을 준비하고 있습니다...",
    OUTLINE_GENERATING: "업종별 규제를 분석하여 전체 단계를 구성 중입니다...",
    DETAIL_GENERATING: "각 단계별 상세 체크리스트와 필요 서류를 매칭 중입니다...",
    SAVING: "생성된 로드맵을 저장하고 있습니다...",
};

/* ─── Generating Insights ─── */

export const GENERATING_INSIGHTS = [
    "💡 카페 창업 시 가장 먼저 확인할 것: 해당 지역의 영업 가능 용도",
    "💡 개인사업자 등록은 보통 1-2일이면 완료됩니다",
    "💡 위생교육은 사전 이수가 필요하며, 온라인으로도 가능합니다",
    "💡 인테리어 공사 전 소방시설 완비증명을 받아야 합니다",
];
