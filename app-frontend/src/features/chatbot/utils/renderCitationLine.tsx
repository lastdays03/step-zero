import React, { type ReactNode } from "react";
import { Gavel, FileText } from "lucide-react";
import type { CitationSource } from "../types/chat";

const CITATION_REGEX = /\[(법령|서류)\s*(\d+)\]/g;

export function renderCitationLine(
  line: string,
  keyPrefix: string,
  sources?: CitationSource[],
): ReactNode[] {
  if (!sources?.length) {
    return [<span key={`${keyPrefix}-text`}>{line}</span>];
  }

  const parts: ReactNode[] = [];
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  const regex = new RegExp(CITATION_REGEX.source, "g");
  while ((match = regex.exec(line)) !== null) {
    if (match.index > lastIndex) {
      parts.push(
        <span key={`${keyPrefix}-t-${lastIndex}`}>
          {line.slice(lastIndex, match.index)}
        </span>,
      );
    }

    const citationType = match[1]; // "법령" or "서류"
    const citationNum = parseInt(match[2], 10);
    const sourceType = citationType === "법령" ? "legal_basis" : "document";
    const matchedSource = sources.find(
      (s) => s.type === sourceType && s.id === citationNum,
    );

    parts.push(
      <span
        key={`${keyPrefix}-c-${match.index}`}
        className="inline-flex items-center gap-0.5 px-1 py-0.5 rounded bg-[#36a4f2]/10 text-[#36a4f2] text-xs font-medium cursor-default"
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

  if (lastIndex < line.length) {
    parts.push(
      <span key={`${keyPrefix}-t-${lastIndex}`}>{line.slice(lastIndex)}</span>,
    );
  }

  return parts.length ? parts : [<span key={`${keyPrefix}-text`}>{line}</span>];
}
