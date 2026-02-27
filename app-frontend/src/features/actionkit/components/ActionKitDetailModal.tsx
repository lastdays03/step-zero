"use client";

import React from 'react';
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
    Download,
    X,
    Calendar,
    CheckSquare,
    Sparkles,
    Gavel,
    Star,
    ArrowRight,
    ShieldCheck,
    BookOpen,
} from 'lucide-react';
import { ActionKitItem, RelatedLaw } from '../types';

const isRelatedLawObject = (law: string | RelatedLaw): law is RelatedLaw => {
    return typeof law === "object" && law !== null && "name" in law;
};

// Contextual usage tips based on document tag/type
const USAGE_GUIDE: Record<string, { about: string; tips: string[] }> = {
    "근로계약서": {
        about: "근로계약서는 사용자(기업)와 근로자 간의 근로조건을 서면으로 명시하는 핵심 법률 문서입니다. 근로기준법 제17조에 따라 반드시 서면으로 교부해야 하며, 미교부 시 500만원 이하의 벌금이 부과될 수 있습니다.",
        tips: [
            "근로계약서는 반드시 2부를 작성하여 1부는 근로자에게 교부하세요.",
            "임금, 소정근로시간, 휴일, 연차유급휴가 등 필수 기재사항을 빠뜨리지 마세요.",
            "수습기간을 둘 경우 기간과 조건을 명확히 기재해야 합니다.",
            "계약기간, 업무내용, 근무장소 변경 시 반드시 근로자 동의를 받으세요."
        ]
    },
    "임대차": {
        about: "상가건물 임대차보호법에 따라 보호받는 임대차계약 관련 서류입니다. 환산보증금 기준, 계약갱신요구권(10년), 권리금 보호 등 상가 임차인의 핵심 권리를 이해하고 활용할 수 있습니다.",
        tips: [
            "확정일자를 반드시 받아두세요 (대항력 + 우선변제권 확보).",
            "환산보증금을 계산하여 상가임대차보호법 적용 여부를 확인하세요.",
            "계약갱신요구권은 최초 계약일로부터 10년까지 행사 가능합니다.",
            "권리금 회수기회 보호: 임대인이 정당한 사유 없이 방해하면 손해배상 청구 가능합니다."
        ]
    },
    "default": {
        about: "본 문서는 창업 및 사업 운영 과정에서 필수적으로 활용되는 실무 서류입니다. 관련 법령의 요건을 충족하도록 작성되었으며, 실제 사용 시에는 사업의 특성에 맞게 내용을 검토·수정하여 활용하시기 바랍니다.",
        tips: [
            "서류 작성 전 최신 법령 개정사항을 반드시 확인하세요.",
            "중요한 계약이나 신고는 전문가(변호사, 세무사 등)의 검토를 권장합니다.",
            "원본은 안전하게 보관하고, 사본을 별도로 관리하세요.",
            "작성일자와 서명/날인을 빠뜨리지 않도록 주의하세요."
        ]
    }
};

function getUsageGuide(item: ActionKitItem): { about: string; tips: string[] } {
    // Try to match by name keyword
    for (const key of Object.keys(USAGE_GUIDE)) {
        if (key === "default") continue;
        if (item.name?.includes(key)) {
            return USAGE_GUIDE[key];
        }
    }
    return USAGE_GUIDE["default"];
}

interface ActionKitDetailModalProps {
    item: ActionKitItem;
    onClose: () => void;
    onDownload: (path: string, name: string, id?: number) => void;
    onNavigateToLaw?: (lawTitle: string) => void;
    onToggleBookmark: (item: ActionKitItem, e: React.MouseEvent) => void;
    isBookmarked: boolean;
    checkedItems: Record<string, boolean>;
    onToggleChecklist: (kitIdentifier: string, checkItem: string) => void;
    getKitProgress: (kit: ActionKitItem) => { checked: number; total: number; percentage: number } | null;
}

export const ActionKitDetailModal = ({
    item,
    onClose,
    onDownload,
    onNavigateToLaw,
    onToggleBookmark,
    isBookmarked,
    checkedItems,
    onToggleChecklist,
    getKitProgress,
}: ActionKitDetailModalProps) => {
    const guide = getUsageGuide(item);
    const kitIdentifier = String(item.id ?? item.name);
    const progress = getKitProgress(item);

    return (
        <div
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-in fade-in duration-200"
            onClick={onClose}
        >
            <div
                className="bg-white rounded-3xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-hidden animate-in zoom-in-95 slide-in-from-bottom-4 duration-300 flex flex-col"
                onClick={(e) => e.stopPropagation()}
            >
                {/* ── Header ── */}
                <div className="relative p-6 pb-5 bg-gradient-to-br from-slate-50 to-[#36a4f2]/5 border-b border-slate-100">
                    <div className="flex justify-between items-start">
                        <div className="flex-1 pr-4">
                            <div className="flex items-center gap-2 mb-3">
                                <Badge className="bg-[#36a4f2]/10 text-[#36a4f2] hover:bg-[#36a4f2]/20 border-none text-xs font-black uppercase">
                                    {item.tag || '[실무]'}
                                </Badge>
                                <Badge variant="secondary" className="text-[10px] font-bold text-slate-400">
                                    {item.type}
                                </Badge>
                                {item.dday && (
                                    <Badge className="bg-orange-500 hover:bg-orange-600 text-[10px] font-bold">
                                        {item.dday}
                                    </Badge>
                                )}
                            </div>
                            <h2 className="text-xl font-bold text-slate-900 leading-tight">
                                {item.name}
                            </h2>
                            <p className="text-sm text-slate-500 mt-2 leading-relaxed">
                                {item.summary}
                            </p>
                        </div>
                        <div className="flex items-center gap-2 shrink-0">
                            <button
                                onClick={(e) => onToggleBookmark(item, e)}
                                className={`p-2 rounded-full transition-all ${isBookmarked
                                    ? 'text-yellow-400 bg-yellow-50 hover:bg-yellow-100'
                                    : 'text-slate-300 bg-white hover:text-yellow-400 hover:bg-yellow-50'
                                    } border border-slate-100 shadow-sm`}
                                title={isBookmarked ? '서랍장에서 제거' : '서랍장에 추가'}
                            >
                                <Star className={`w-5 h-5 ${isBookmarked ? 'fill-current' : ''}`} />
                            </button>
                            <button
                                onClick={onClose}
                                className="p-2 rounded-full text-slate-400 hover:text-slate-600 bg-white border border-slate-100 shadow-sm hover:bg-slate-50 transition-colors"
                            >
                                <X className="w-5 h-5" />
                            </button>
                        </div>
                    </div>

                    {/* Progress Bar (if applicable) */}
                    {progress && (
                        <div className="mt-4 flex items-center gap-3">
                            <div className="flex-1 bg-white rounded-full h-2 overflow-hidden border border-slate-100">
                                <div
                                    className={`h-2 rounded-full transition-all duration-700 ${progress.percentage === 100 ? 'bg-emerald-500' : 'bg-[#36a4f2]'}`}
                                    style={{ width: `${progress.percentage}%` }}
                                />
                            </div>
                            <span className={`text-xs font-black tabular-nums ${progress.percentage === 100 ? 'text-emerald-500' : 'text-slate-500'}`}>
                                {progress.percentage}%
                            </span>
                        </div>
                    )}
                </div>

                {/* ── Body ── */}
                <div className="flex-1 overflow-y-auto p-6 space-y-6">

                    {/* Section 1 : About This Document */}
                    <div className="space-y-3">
                        <h3 className="font-bold text-sm text-slate-800 flex items-center gap-2">
                            <div className="w-6 h-6 rounded-lg bg-[#36a4f2]/10 flex items-center justify-center">
                                <BookOpen className="w-3.5 h-3.5 text-[#36a4f2]" />
                            </div>
                            이 서류는 어떤 문서인가요?
                        </h3>
                        <div className="text-sm text-slate-600 leading-relaxed bg-slate-50 p-4 rounded-2xl border border-slate-100">
                            {guide.about}
                        </div>
                    </div>

                    {/* Section 2 : Usage Tips */}
                    <div className="space-y-3">
                        <h3 className="font-bold text-sm text-slate-800 flex items-center gap-2">
                            <div className="w-6 h-6 rounded-lg bg-emerald-50 flex items-center justify-center">
                                <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" />
                            </div>
                            실무 활용 팁
                        </h3>
                        <div className="space-y-2">
                            {guide.tips.map((tip, i) => (
                                <div key={i} className="flex items-start gap-3 p-3 rounded-xl bg-emerald-50/50 border border-emerald-100/50">
                                    <span className="text-emerald-500 font-black text-xs mt-0.5 bg-emerald-100 w-5 h-5 rounded-full flex items-center justify-center shrink-0">
                                        {i + 1}
                                    </span>
                                    <span className="text-sm text-slate-700 leading-relaxed">{tip}</span>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Section 3 : Compliance Checklist */}
                    {item.complianceChecklist && item.complianceChecklist.length > 0 && (
                        <div className="space-y-3">
                            <div className="flex justify-between items-center">
                                <h3 className="font-bold text-sm text-slate-800 flex items-center gap-2">
                                    <div className="w-6 h-6 rounded-lg bg-blue-50 flex items-center justify-center">
                                        <CheckSquare className="w-3.5 h-3.5 text-[#36a4f2]" />
                                    </div>
                                    사용 전 필수 체크리스트
                                </h3>
                                {progress && (
                                    <span className={`text-xs font-black ${progress.percentage === 100 ? 'text-emerald-500' : 'text-slate-400'}`}>
                                        {progress.checked}/{progress.total} 완료
                                    </span>
                                )}
                            </div>
                            <div className="space-y-2">
                                {item.complianceChecklist.map((checkItem, i) => {
                                    const key = `${kitIdentifier}_${checkItem}`;
                                    const isChecked = !!checkedItems[key];
                                    return (
                                        <label key={i} className={`flex items-start gap-3 p-3 rounded-xl border transition-all cursor-pointer group ${isChecked
                                            ? 'border-emerald-300 bg-emerald-50'
                                            : 'border-slate-100 hover:border-[#36a4f2]/30 hover:bg-[#36a4f2]/5'
                                            }`}>
                                            <input
                                                type="checkbox"
                                                className="mt-0.5 w-4 h-4 rounded border-slate-300 text-emerald-500 focus:ring-emerald-500 cursor-pointer"
                                                checked={isChecked}
                                                onChange={() => onToggleChecklist(kitIdentifier, checkItem)}
                                            />
                                            <span className={`text-sm leading-tight transition-all ${isChecked ? 'text-emerald-700 font-medium line-through opacity-70' : 'text-slate-600 group-hover:text-slate-900'}`}>
                                                {checkItem}
                                            </span>
                                        </label>
                                    );
                                })}
                            </div>
                        </div>
                    )}

                    {/* Section 4 : Highlights */}
                    {item.highlights && item.highlights.length > 0 && (
                        <div className="space-y-3">
                            <h3 className="font-bold text-sm text-slate-800 flex items-center gap-2">
                                <div className="w-6 h-6 rounded-lg bg-amber-50 flex items-center justify-center">
                                    <Sparkles className="w-3.5 h-3.5 text-amber-500" />
                                </div>
                                핵심 포인트
                            </h3>
                            <div className="space-y-2">
                                {item.highlights.map((hl, i) => (
                                    <div key={hl.id || i} className="flex items-start gap-2.5 p-3 rounded-xl bg-amber-50 border border-amber-100">
                                        <span className="text-amber-500 font-bold text-sm mt-0.5">⭐</span>
                                        <span className="text-sm text-slate-700 leading-relaxed">{hl.content}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Section 5 : Related Laws Cross-Navigation */}
                    {item.relatedLaws && item.relatedLaws.length > 0 && (
                        <div className="space-y-3">
                            <h3 className="font-bold text-sm text-slate-800 flex items-center gap-2">
                                <div className="w-6 h-6 rounded-lg bg-violet-50 flex items-center justify-center">
                                    <Gavel className="w-3.5 h-3.5 text-violet-500" />
                                </div>
                                관련 법령 가이드
                            </h3>
                            <div className="space-y-2">
                                {item.relatedLaws.map((law, i) => {
                                    const name = isRelatedLawObject(law) ? law.name : law;
                                    const summary = isRelatedLawObject(law) ? law.summary : null;
                                    return (
                                        <button
                                            key={i}
                                            onClick={() => {
                                                onNavigateToLaw?.(name);
                                                onClose();
                                            }}
                                            className="w-full flex items-center gap-3 p-3.5 rounded-2xl border border-violet-100 bg-violet-50/50 hover:bg-violet-100/60 hover:border-violet-200 transition-all group text-left"
                                        >
                                            <div className="w-8 h-8 rounded-xl bg-white border border-violet-100 flex items-center justify-center shrink-0 shadow-sm group-hover:shadow transition-shadow">
                                                <Gavel className="w-4 h-4 text-violet-500" />
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <p className="text-sm font-bold text-violet-800 group-hover:text-violet-900 transition-colors truncate">
                                                    {name}
                                                </p>
                                                {summary && (
                                                    <p className="text-xs text-violet-500 mt-0.5 line-clamp-1">{summary}</p>
                                                )}
                                            </div>
                                            <ArrowRight className="w-4 h-4 text-violet-300 group-hover:text-violet-500 transition-colors shrink-0 group-hover:translate-x-0.5 transform" />
                                        </button>
                                    );
                                })}
                            </div>
                            <p className="text-[10px] text-slate-400 pl-1">
                                클릭하면 법령 가이드 탭으로 이동하여 해당 법률의 핵심 내용을 확인할 수 있습니다.
                            </p>
                        </div>
                    )}
                </div>

                {/* ── Footer Action Bar ── */}
                <div className="p-5 border-t border-slate-100 bg-slate-50/80 flex items-center justify-between gap-3">
                    <div className="flex items-center gap-2 text-slate-400">
                        <Calendar className="w-3.5 h-3.5" />
                        <span className="text-xs font-medium">Updated: 2026.02</span>
                    </div>
                    <div className="flex items-center gap-3">
                        <Button
                            variant="outline"
                            className="rounded-full border-slate-200 hover:bg-slate-100"
                            onClick={onClose}
                        >
                            닫기
                        </Button>
                        <Button
                            className="bg-[#36a4f2] hover:bg-[#258bd1] gap-2 rounded-full px-6 shadow-lg shadow-[#36a4f2]/20"
                            onClick={() => {
                                onDownload(item.path, item.name, item.id);
                            }}
                        >
                            <Download className="w-4 h-4" />
                            원본 다운로드
                        </Button>
                    </div>
                </div>
            </div>
        </div>
    );
};
