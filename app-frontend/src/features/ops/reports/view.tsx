"use client";

import { useCallback, useEffect, useState } from "react";

import { TrendingDown, TrendingUp } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { OpsAccessPlaceholder } from "@/features/ops/shared/ops-access-placeholder";
import { useOpsAccessGuard } from "@/features/ops/shared/use-ops-access-guard";
import { cn } from "@/lib/utils";

import { fetchOpsSummary } from "./api";
import type { OpsSummary } from "./types";

type RangeOption = "7d" | "30d";

/* ── MetricCard ─────────────────────────────────────── */

function MetricCard({
  title,
  value,
  delta,
  suffix,
  badge,
}: {
  title: string;
  value: string | number;
  delta?: number | null;
  suffix?: string;
  badge?: string;
}) {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <p className="text-xs font-medium text-muted-foreground">{title}</p>
          {badge && (
            <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-medium text-slate-600">
              {badge}
            </span>
          )}
        </div>
        <p className="mt-2 text-2xl font-bold text-slate-900">
          {value}
          {suffix && (
            <span className="ml-0.5 text-sm font-normal text-muted-foreground">
              {suffix}
            </span>
          )}
        </p>
        {delta !== undefined && <DeltaBadge delta={delta} />}
      </CardContent>
    </Card>
  );
}

function DeltaBadge({ delta }: { delta: number | null }) {
  if (delta === null) {
    return (
      <p className="mt-1 text-xs text-muted-foreground">전기간 데이터 없음</p>
    );
  }

  const pct = (delta * 100).toFixed(1);
  const isPositive = delta > 0;
  const isZero = delta === 0;

  return (
    <p
      className={cn(
        "mt-1 flex items-center gap-1 text-xs font-medium",
        isZero && "text-muted-foreground",
        isPositive && "text-emerald-600",
        !isPositive && !isZero && "text-red-600",
      )}
    >
      {!isZero &&
        (isPositive ? (
          <TrendingUp className="h-3 w-3" />
        ) : (
          <TrendingDown className="h-3 w-3" />
        ))}
      {isPositive ? "+" : ""}
      {pct}% 전기간 대비
    </p>
  );
}

/* ── OpsReportsView ─────────────────────────────────── */

export function OpsReportsView() {
  const { canRender, isAuthReady } = useOpsAccessGuard();
  const [summary, setSummary] = useState<OpsSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [range, setRange] = useState<RangeOption>("7d");

  const load = useCallback(
    async (r: RangeOption) => {
      if (!canRender) return;
      setIsLoading(true);
      setError(null);
      try {
        setSummary(await fetchOpsSummary(r));
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "알 수 없는 오류가 발생했습니다.",
        );
      } finally {
        setIsLoading(false);
      }
    },
    [canRender],
  );

  useEffect(() => {
    void load(range);
  }, [load, range]);

  if (!isAuthReady || !canRender) return <OpsAccessPlaceholder />;

  const handleRange = (r: RangeOption) => {
    setRange(r);
  };

  return (
    <section className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-slate-900">운영 리포트</h1>
        <div className="flex items-center gap-2">
          <div className="flex rounded-lg border border-slate-200 bg-white p-0.5">
            {(["7d", "30d"] as const).map((r) => (
              <button
                key={r}
                onClick={() => handleRange(r)}
                className={cn(
                  "rounded-md px-3 py-1 text-sm font-medium transition-colors",
                  range === r
                    ? "bg-slate-900 text-white"
                    : "text-slate-600 hover:text-slate-900",
                )}
              >
                {r === "7d" ? "7일" : "30일"}
              </button>
            ))}
          </div>
          {summary && (
            <p className="text-xs text-muted-foreground">
              {new Date(summary.generated_at).toLocaleString("ko-KR")}
            </p>
          )}
        </div>
      </div>

      {/* Loading / Error */}
      {isLoading && (
        <p className="text-sm text-slate-600">
          운영 지표를 불러오는 중입니다...
        </p>
      )}
      {error && <p className="text-sm text-red-600">{error}</p>}

      {/* KPI Grid */}
      {summary && !isLoading && (
        <>
          {/* Row 1: 핵심 지표 (with delta) */}
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <MetricCard
              title="활성 사용자"
              value={summary.active_users.toLocaleString()}
              delta={summary.active_users_delta}
            />
            <MetricCard
              title="신규 가입"
              value={summary.new_signups.toLocaleString()}
              delta={summary.new_signups_delta}
            />
            <MetricCard
              title="로드맵 생성"
              value={summary.roadmaps_generated.toLocaleString()}
              delta={summary.roadmaps_generated_delta}
            />
            <MetricCard
              title="채팅 세션"
              value={summary.chat_sessions.toLocaleString()}
            />
          </div>

          {/* Row 2: 비율 + 총계 */}
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <MetricCard
              title="DAU/MAU 비율"
              value={(summary.dau_mau_ratio * 100).toFixed(1)}
              suffix="%"
              badge="고정 7d/30d"
            />
            <MetricCard
              title="가입→로드맵 전환율"
              value={(summary.signup_to_roadmap_rate * 100).toFixed(1)}
              suffix="%"
            />
            <MetricCard
              title="커뮤니티 게시글"
              value={summary.community_posts.toLocaleString()}
            />
            <MetricCard
              title="총 사용자 / 팀"
              value={summary.total_users.toLocaleString()}
              suffix={`/ ${summary.total_teams.toLocaleString()}팀`}
              badge={`로드맵 ${summary.total_roadmaps.toLocaleString()}`}
            />
          </div>
        </>
      )}
    </section>
  );
}
