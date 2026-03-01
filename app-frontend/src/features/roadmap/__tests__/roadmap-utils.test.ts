import { computeEndowedProgress, computeReadinessLevel } from "../components/roadmap-utils";

describe("computeEndowedProgress", () => {
    it("returns ~17% for a new roadmap with 0 completed steps", () => {
        const result = computeEndowedProgress(0, 15);
        // 3 / (15+3) = 3/18 ≈ 17%
        expect(result.display).toBe(17);
        expect(result.actual).toBe(0);
        expect(result.endowedSteps).toBe(3);
        expect(result.totalWithEndowed).toBe(18);
    });

    it("returns ~33% when 3 of 15 steps are completed", () => {
        const result = computeEndowedProgress(3, 15);
        // (3+3) / (15+3) = 6/18 ≈ 33%
        expect(result.display).toBe(33);
        expect(result.actual).toBe(20);
    });

    it("returns 50% at midpoint", () => {
        const result = computeEndowedProgress(6, 15);
        // (6+3) / (15+3) = 9/18 = 50%
        expect(result.display).toBe(50);
        expect(result.actual).toBe(40);
    });

    it("returns 100% when all steps are completed", () => {
        const result = computeEndowedProgress(15, 15);
        // (15+3) / (15+3) = 18/18 = 100%
        expect(result.display).toBe(100);
        expect(result.actual).toBe(100);
    });

    it("handles 0 total steps without dividing by zero", () => {
        const result = computeEndowedProgress(0, 0);
        // 3 / (0+3) = 3/3 = 100%
        expect(result.display).toBe(100);
        expect(result.actual).toBe(0);
    });

    it("handles single step roadmap", () => {
        const result = computeEndowedProgress(0, 1);
        // 3 / (1+3) = 3/4 = 75%
        expect(result.display).toBe(75);
        expect(result.actual).toBe(0);
    });
});

describe("computeReadinessLevel", () => {
    it("returns 🌱 아이디어 for 0%", () => {
        const result = computeReadinessLevel(0);
        expect(result.level).toBe(1);
        expect(result.emoji).toBe("🌱");
        expect(result.label).toBe("아이디어");
    });

    it("returns 📋 준비 착수 for 10%", () => {
        const result = computeReadinessLevel(10);
        expect(result.level).toBe(2);
        expect(result.label).toBe("준비 착수");
    });

    it("returns 📝 서류 준비 중 for 50%", () => {
        const result = computeReadinessLevel(50);
        expect(result.level).toBe(3);
        expect(result.label).toBe("서류 준비 중");
    });

    it("returns ✅ 인허가 완료 for 65%", () => {
        const result = computeReadinessLevel(65);
        expect(result.level).toBe(4);
        expect(result.label).toBe("인허가 완료");
    });

    it("returns 🚀 창업 준비 완료 for 90%", () => {
        const result = computeReadinessLevel(90);
        expect(result.level).toBe(5);
        expect(result.label).toBe("창업 준비 완료");
    });

    it("returns 🚀 창업 준비 완료 for 100%", () => {
        const result = computeReadinessLevel(100);
        expect(result.level).toBe(5);
        expect(result.label).toBe("창업 준비 완료");
    });

    it("returns 🌱 아이디어 for 9% (below 10 threshold)", () => {
        const result = computeReadinessLevel(9);
        expect(result.level).toBe(1);
    });

    it("returns 📋 준비 착수 for 34% (below 35 threshold)", () => {
        const result = computeReadinessLevel(34);
        expect(result.level).toBe(2);
    });
});
