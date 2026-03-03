import React, { type ReactNode } from "react";
import { Gavel, FileText } from "lucide-react";
import type { CitationSource } from "../types";

// ------------------------------------------------------------------ //
//  인용 패턴: [법령 N] 또는 [서류 N]
// ------------------------------------------------------------------ //

const CITATION_REGEX = /\[(법령|서류)\s*(\d+)\]/g;

/**
 * 텍스트 내 [법령 N], [서류 N] 패턴을 감지하여 인라인 배지로 변환
 */
export function renderCitationLine(
  text: string,
  sources?: CitationSource[],
): ReactNode {
  if (!sources?.length) {
    return <>{text}</>;
  }

  const parts: ReactNode[] = [];
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  // 매번 새 regex 인스턴스 사용 (전역 플래그 lastIndex 충돌 방지)
  const regex = new RegExp(CITATION_REGEX.source, "g");

  while ((match = regex.exec(text)) !== null) {
    // 매치 앞 텍스트
    if (match.index > lastIndex) {
      parts.push(
        <React.Fragment key={`t-${lastIndex}`}>
          {text.slice(lastIndex, match.index)}
        </React.Fragment>,
      );
    }

    const citationType = match[1]; // "법령" | "서류"
    const citationNum = parseInt(match[2], 10);
    const sourceType = citationType === "법령" ? "legal_basis" : "document";

    // 소스 매칭 (law 타입도 호환)
    const matchedSource = sources.find(
      (s) =>
        (s.type === sourceType || (sourceType === "legal_basis" && s.type === "law")) &&
        s.id === citationNum,
    );

    parts.push(
      <span
        key={`c-${match.index}`}
        className="inline-flex items-center gap-0.5 px-1 py-0.5 rounded bg-blue-50 text-blue-600 text-xs font-medium cursor-default"
        title={matchedSource?.title ?? `${citationType} ${citationNum}`}
      >
        {citationType === "법령" ? (
          <Gavel className="w-3 h-3" />
        ) : (
          <FileText className="w-3 h-3" />
        )}
        {match[0]}
      </span>,
    );

    lastIndex = match.index + match[0].length;
  }

  // 마지막 텍스트
  if (lastIndex < text.length) {
    parts.push(
      <React.Fragment key={`t-${lastIndex}`}>
        {text.slice(lastIndex)}
      </React.Fragment>,
    );
  }

  return parts.length > 0 ? <>{parts}</> : <>{text}</>;
}
