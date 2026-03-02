"use client";

import { useState } from "react";
import {
  Gavel,
  FileText,
  ExternalLink,
  ChevronUp,
  ChevronDown,
} from "lucide-react";
import type { CitationSource } from "../types/chat";

interface SourcesCardProps {
  sources: CitationSource[];
}

export function SourcesCard({ sources }: SourcesCardProps) {
  const [expanded, setExpanded] = useState(false);

  if (!sources.length) return null;

  return (
    <div className="mt-2 pt-2 border-t border-slate-100">
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-1 text-xs font-medium text-slate-500 hover:text-[#36a4f2] transition-colors"
      >
        {expanded ? (
          <ChevronUp className="w-3 h-3" />
        ) : (
          <ChevronDown className="w-3 h-3" />
        )}
        출처 {sources.length}건
      </button>
      {expanded && (
        <ul className="mt-1.5 space-y-1">
          {sources.map((src) => (
            <li
              key={`${src.type}-${src.id}`}
              className="flex items-start gap-2 px-2 py-1.5 rounded-md bg-slate-50 text-xs"
            >
              {src.type === "legal_basis" ? (
                <Gavel className="w-3.5 h-3.5 text-amber-600 shrink-0 mt-0.5" />
              ) : (
                <FileText className="w-3.5 h-3.5 text-blue-600 shrink-0 mt-0.5" />
              )}
              <div className="min-w-0">
                <p className="font-medium text-slate-700 truncate">
                  [{src.type === "legal_basis" ? "법령" : "서류"} {src.id}]{" "}
                  {src.title}
                </p>
                {src.url && (
                  <a
                    href={src.url}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-0.5 mt-0.5 text-[#36a4f2] hover:underline"
                  >
                    원문 보기 <ExternalLink className="w-3 h-3" />
                  </a>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
