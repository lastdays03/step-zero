import React from 'react';
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from "@/components/ui/tooltip";

interface LawSnippetTagProps {
    name: string;
    summary?: string;
    snippet?: string;
    onClick?: () => void;
}

export const LawSnippetTag: React.FC<LawSnippetTagProps> = ({ name, summary, snippet, onClick }) => {
    return (
        <TooltipProvider delayDuration={300}>
            <Tooltip>
                <TooltipTrigger asChild>
                    <button
                        onClick={(e) => {
                            if (onClick) {
                                e.stopPropagation();
                                onClick();
                            }
                        }}
                        className="group/law flex flex-wrap items-center gap-1.5 w-full text-left"
                    >
                        <span className="text-[10px] font-bold text-[#36a4f2] bg-[#36a4f2]/5 px-1.5 py-0.5 rounded border border-[#36a4f2]/10 transition-colors group-hover/law:bg-[#36a4f2]/10">
                            #{name}
                        </span>
                        {summary && (
                            <span className="text-[10px] text-slate-500 line-clamp-1 flex-1 transition-colors group-hover/law:text-slate-700">
                                {summary}
                            </span>
                        )}
                    </button>
                </TooltipTrigger>
                {snippet && (
                    <TooltipContent side="top" className="max-w-xs bg-slate-900 border-slate-800 text-slate-200">
                        <div className="space-y-1">
                            <p className="font-bold text-[#36a4f2] text-xs">법령 요약 스니펫</p>
                            <p className="text-xs leading-relaxed">{snippet}</p>
                        </div>
                    </TooltipContent>
                )}
            </Tooltip>
        </TooltipProvider>
    );
};
