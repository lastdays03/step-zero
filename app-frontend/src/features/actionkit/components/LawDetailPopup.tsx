"use client";

import React from 'react';
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
    X,
    Gavel,
    FolderOpen,
    ArrowRight,
    MessageCircle,
    ExternalLink,
} from 'lucide-react';
import { LawItem, ActionKitItem } from '../types';

// Simple plain-language summaries keyed by partial law name match
const PLAIN_SUMMARIES: Record<string, string> = {
    "임대차보호법": "이 법은 상가 임차인의 보증금과 계약갱신 권리를 보호합니다. 환산보증금 기준 이하의 임차인은 대항력·우선변제권을 갖고, 최대 10년까지 계약갱신을 요구할 수 있습니다.",
    "근로기준법": "근로자의 기본적 근로조건을 정하는 법입니다. 임금, 근로시간, 해고 제한, 연차휴가 등 사용자가 반드시 지켜야 할 최저 기준을 규정합니다.",
    "건축법": "건축물의 대지, 구조, 설비, 용도 등에 관한 기준을 정한 법입니다. 건축 허가·신고 절차, 용도변경, 안전 기준 등을 규율합니다.",
    "소방시설": "다중이용업소 등에서의 화재 예방 및 안전관리 의무를 규정합니다. 소방시설 설치·유지, 안전교육, 정기 점검 등이 포함됩니다.",
    "식품위생법": "식품의 위생적 취급과 영업 허가·신고에 관한 법률입니다. 음식점 등 식품접객업의 영업 기준, 위생 관리, 표시 기준 등을 정합니다.",
    "산업안전": "사업장의 안전·보건 기준을 정하여 근로자의 생명과 건강을 보호하는 법입니다. 안전 교육, 위험성 평가, 안전관리 체계 등을 규정합니다.",
    "개인정보": "개인정보의 수집·이용·제공·파기 등에 관한 원칙을 정한 법입니다. 정보주체의 동의 원칙, 안전조치 의무, 위반 시 과징금 등을 규정합니다.",
    "세법": "사업자의 납세 의무와 세금 신고·납부 절차를 규정합니다. 부가가치세, 종합소득세, 원천징수 등 창업자가 알아야 할 조세 의무를 포함합니다.",
    "행정절차법": "행정기관의 처분, 신고, 인·허가 등의 절차를 규정하여 국민의 행정 참여와 권리 보호를 보장하는 법률입니다.",
    "default": "본 법령은 창업·사업 운영 과정에서 중요한 법적 기준과 의무를 규정하고 있습니다. 해당 조항의 핵심 내용을 확인하고 사업에 적용하시기 바랍니다."
};

function getPlainSummary(lawName: string): string {
    for (const key of Object.keys(PLAIN_SUMMARIES)) {
        if (key === "default") continue;
        if (lawName.includes(key)) {
            return PLAIN_SUMMARIES[key];
        }
    }
    return PLAIN_SUMMARIES["default"];
}

interface LawDetailPopupProps {
    item: LawItem;
    relatedKits: ActionKitItem[];
    onClose: () => void;
    onNavigateToKit?: (kitName: string) => void;
}

export const LawDetailPopup = ({
    item,
    relatedKits,
    onClose,
    onNavigateToKit,
}: LawDetailPopupProps) => {
    const plainSummary = getPlainSummary(item.name);

    return (
        <div
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm animate-in fade-in duration-200"
            onClick={onClose}
        >
            <div
                className="bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-hidden animate-in zoom-in-95 slide-in-from-bottom-3 duration-300 flex flex-col"
                onClick={(e) => e.stopPropagation()}
            >
                {/* ── Header ── */}
                <div className="p-5 pb-4 bg-gradient-to-br from-violet-50 to-[#36a4f2]/5 border-b border-violet-100/50">
                    <div className="flex justify-between items-start">
                        <div className="flex-1 pr-3">
                            <div className="flex items-center gap-2 mb-2">
                                <div className="w-7 h-7 rounded-lg bg-violet-100 flex items-center justify-center">
                                    <Gavel className="w-4 h-4 text-violet-600" />
                                </div>
                                <Badge className="bg-violet-100 text-violet-600 hover:bg-violet-200 border-none text-[10px] font-black uppercase">
                                    {item.ext?.replace('.', '') || '법령'}
                                </Badge>
                            </div>
                            <h3 className="text-lg font-bold text-slate-900 leading-tight">
                                {item.name}
                            </h3>
                        </div>
                        <button
                            onClick={onClose}
                            className="p-1.5 rounded-full text-slate-400 hover:text-slate-600 bg-white/80 border border-slate-100 shadow-sm hover:bg-slate-50 transition-colors shrink-0"
                        >
                            <X className="w-4 h-4" />
                        </button>
                    </div>
                </div>

                {/* ── Body ── */}
                <div className="p-5 space-y-4 max-h-[55vh] overflow-y-auto">

                    {/* Section 1: Plain Language Summary */}
                    <div className="space-y-2">
                        <h4 className="text-xs font-bold text-slate-500 flex items-center gap-1.5 uppercase tracking-wider">
                            <MessageCircle className="w-3.5 h-3.5 text-violet-500" />
                            쉬운 설명
                        </h4>
                        <div className="text-sm text-slate-700 leading-relaxed bg-violet-50/50 p-4 rounded-xl border border-violet-100/50">
                            {plainSummary}
                        </div>
                    </div>

                    {/* Section 2: Original Summary */}
                    {item.summary && (
                        <div className="space-y-2">
                            <h4 className="text-xs font-bold text-slate-500 flex items-center gap-1.5 uppercase tracking-wider">
                                <Gavel className="w-3.5 h-3.5 text-slate-400" />
                                원문 요약
                            </h4>
                            <p className="text-xs text-slate-500 leading-relaxed bg-slate-50 p-3 rounded-xl border border-slate-100">
                                {item.summary}
                            </p>
                        </div>
                    )}

                    {/* Section 3: Related Action Kits (Reverse Cross-Link) */}
                    {relatedKits.length > 0 && (
                        <div className="space-y-2">
                            <h4 className="text-xs font-bold text-slate-500 flex items-center gap-1.5 uppercase tracking-wider">
                                <FolderOpen className="w-3.5 h-3.5 text-[#36a4f2]" />
                                관련 실무 서류 (액션 키트)
                            </h4>
                            <div className="space-y-1.5">
                                {relatedKits.slice(0, 4).map((kit, i) => (
                                    <button
                                        key={i}
                                        onClick={() => {
                                            onNavigateToKit?.(kit.name);
                                            onClose();
                                        }}
                                        className="w-full flex items-center gap-3 p-3 rounded-xl border border-slate-100 bg-white hover:bg-[#36a4f2]/5 hover:border-[#36a4f2]/30 transition-all group text-left shadow-sm"
                                    >
                                        <div className="w-7 h-7 rounded-lg bg-[#36a4f2]/10 flex items-center justify-center shrink-0 group-hover:bg-[#36a4f2]/20 transition-colors">
                                            <FolderOpen className="w-3.5 h-3.5 text-[#36a4f2]" />
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <p className="text-sm font-bold text-slate-700 group-hover:text-[#36a4f2] transition-colors truncate">
                                                {kit.name}
                                            </p>
                                            <p className="text-[10px] text-slate-400 mt-0.5">{kit.type}</p>
                                        </div>
                                        <ArrowRight className="w-3.5 h-3.5 text-slate-300 group-hover:text-[#36a4f2] transition-colors shrink-0 group-hover:translate-x-0.5 transform" />
                                    </button>
                                ))}
                            </div>
                            <p className="text-[10px] text-slate-400 pl-1">
                                클릭하면 액션 키트 탭으로 이동하여 해당 서류를 확인할 수 있습니다.
                            </p>
                        </div>
                    )}

                    {/* Highlights (if available) */}
                    {item.highlights && item.highlights.length > 0 && (
                        <div className="space-y-2">
                            <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider">핵심 포인트</h4>
                            <div className="space-y-1.5">
                                {item.highlights.map((h, i) => (
                                    <div key={i} className="flex items-start gap-2 text-xs text-slate-600 bg-amber-50/50 p-2.5 rounded-lg border border-amber-100/50">
                                        <span className="text-amber-500 mt-0.5">⭐</span>
                                        <span className="leading-relaxed">{h}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>

                {/* ── Footer ── */}
                <div className="p-4 border-t border-slate-100 bg-slate-50/50 flex items-center justify-between">
                    <span className="text-[10px] text-slate-400 font-medium">{item.size}</span>
                    <div className="flex items-center gap-2">
                        <Button
                            variant="outline"
                            size="sm"
                            className="rounded-full border-slate-200 hover:bg-slate-100 h-8 text-xs"
                            onClick={onClose}
                        >
                            닫기
                        </Button>
                        {item.id && <Button
                            size="sm"
                            className="rounded-full bg-[#36a4f2] hover:bg-[#258bd1] gap-1.5 h-8 text-xs px-4 shadow-md shadow-[#36a4f2]/20"
                            asChild
                        >
                            <a
                                href={`${process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ?? ""}/api/v1/actionkits/items/${item.id}/view`}
                                target="_blank"
                                rel="noreferrer"
                            >
                                <ExternalLink className="w-3 h-3" />
                                문서 보기
                            </a>
                        </Button>}
                    </div>
                </div>
            </div>
        </div>
    );
};
