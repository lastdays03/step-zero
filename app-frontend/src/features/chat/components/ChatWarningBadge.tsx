"use client";

import { AlertTriangle } from "lucide-react";

// ------------------------------------------------------------------ //
//  ChatWarningBadge
// ------------------------------------------------------------------ //

interface ChatWarningBadgeProps {
  warning: {
    code: string;
    message: string;
  };
}

export function ChatWarningBadge({ warning }: ChatWarningBadgeProps) {
  return (
    <div className="mt-2 flex items-start gap-1.5 rounded-md bg-amber-50 border border-amber-200 px-2.5 py-1.5 text-xs text-amber-700">
      <AlertTriangle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
      <div>
        <p className="font-medium">출처 미확인 정보</p>
        <p className="mt-0.5 text-amber-600">{warning.message}</p>
      </div>
    </div>
  );
}
