"use client";

import React, { useState } from 'react';
import { useLawGuide } from '../hooks/useLawGuide';
import { useActionKit } from '../hooks/useActionKit';
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
    FileText,
    Search,
    Download,
    CheckCircle2,
    Info,
    Sparkles,
    FolderOpen,
    Eye,
    EyeOff
} from 'lucide-react';
import { LawItem, RelatedLaw } from '../types';

type LawItemWithChapter = LawItem & { chapterTitle: string };

interface LawGuideViewProps {
    initialSearch?: string;
    onNavigateToKit?: (kitName: string) => void;
}

export const LawGuideView = ({ initialSearch = "", onNavigateToKit }: LawGuideViewProps) => {
    const { data, loading, error } = useLawGuide();
    const { data: kitsData } = useActionKit();
    const [activeChapter, setActiveChapter] = useState<string>("1");
    const [searchQuery, setSearchQuery] = useState(initialSearch);

    // Manage completed/read status (in-memory for demo, would be localStorage/DB in real app)
    const [completedItems, setCompletedItems] = useState<Set<string>>(new Set());

    const toggleItemCompletion = (e: React.MouseEvent, itemName: string) => {
        e.stopPropagation();
        setCompletedItems(prev => {
            const next = new Set(prev);
            if (next.has(itemName)) {
                next.delete(itemName);
            } else {
                next.add(itemName);
            }
            return next;
        });
    };

    const isRelatedLawObject = (law: string | RelatedLaw): law is RelatedLaw => {
        return typeof law === "object" && law !== null && "name" in law;
    };

    const getRelatedKits = (lawName: string) => {
        if (!kitsData) return [];
        return Object.values(kitsData).flatMap(cat => cat.items)
            .filter(kit => kit.relatedLaws?.some(rl => {
                const checkName = isRelatedLawObject(rl) ? rl.name : rl;
                return checkName.includes(lawName) || lawName.includes(checkName);
            }));
    };

    if (loading) return <div className="p-8 text-center text-slate-500">법령 가이드를 불러오는 중...</div>;
    if (error) return <div className="p-8 text-center text-red-500">{error}</div>;
    if (!data) return null;

    const chapters = Object.entries(data);
    const currentChapter = data[activeChapter];

    const handleDownload = (path: string, filename: string) => {
        try {
            const baseURL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";

            // If path already starts with actionkits/files, just use it with baseURL
            // If it starts with library/resources, swap it to the new structure
            let finalPath = path;
            if (path.startsWith('library/resources/')) {
                finalPath = path.replace('library/resources/', 'actionkits/files/');
            }

            // Build absolute URL
            const url = finalPath.startsWith('http') ? finalPath : `${baseURL}/${finalPath}`;

            const link = document.createElement('a');
            link.href = url;
            link.target = "_blank";
            link.download = filename;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        } catch (err) {
            console.error('Download failed:', err);
            alert('다운로드 중 오류가 발생했습니다.');
        }
    };

    const filteredItems: LawItemWithChapter[] = Object.values(data).flatMap(chapter =>
        chapter.items.map(item => ({ ...item, chapterTitle: chapter.title }))
    ).filter(item =>
        item.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.summary.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const displayItems: Array<LawItem & { chapterTitle?: string }> = searchQuery
        ? filteredItems
        : (currentChapter?.items ?? []);

    return (
        <div className="space-y-8 animate-in fade-in duration-500">
            {/* Header with Search */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                    <h2 className="text-2xl font-bold text-slate-900">창업 법령 가이드</h2>
                    <p className="text-sm text-slate-500 mt-1">
                        {searchQuery ? `'${searchQuery}' 검색 결과` : `${currentChapter?.title} 관련 법령을 확인하세요.`}
                    </p>
                </div>
                <div className="relative w-full md:w-64">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 w-4 h-4" />
                    <input
                        type="text"
                        placeholder="법령, 조항 검색..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="w-full pl-10 pr-4 py-2 bg-white border border-slate-200 rounded-full text-sm focus:ring-2 focus:ring-[#36a4f2]/20 transition-all outline-none"
                    />
                </div>
            </div>

            {/* Chapter Navigation (Only show if not searching) */}
            {!searchQuery && (
                <div className="flex flex-wrap gap-2 overflow-x-auto pb-2">
                    {chapters.map(([id, chapter]) => (
                        <Button
                            key={id}
                            variant={activeChapter === id ? "default" : "outline"}
                            size="sm"
                            onClick={() => setActiveChapter(id)}
                            className={`rounded-full px-4 h-9 ${activeChapter === id ? 'bg-[#36a4f2] hover:bg-[#258bd1]' : 'text-slate-500'}`}
                        >
                            {chapter.title}
                        </Button>
                    ))}
                </div>
            )}

            {/* Law Cards Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {displayItems.map((item, index) => {
                    const isCompleted = completedItems.has(item.name);

                    return (
                        <Card
                            key={`${item.name}-${index}`}
                            className={`group transition-all duration-300 shadow-sm hover:shadow-md cursor-pointer flex flex-col justify-between ${isCompleted ? 'bg-slate-50/50 border-emerald-500/30' : 'hover:border-[#36a4f2]'
                                }`}
                        >
                            <CardContent className="p-6">
                                <div className="flex justify-between items-start mb-4">
                                    <div className={`w-10 h-10 rounded-xl flex items-center justify-center transition-colors ${isCompleted ? 'bg-emerald-100 text-emerald-600' :
                                        item.ext === '.pdf' ? 'bg-red-50 text-red-500' : 'bg-[#36a4f2]/10 text-[#36a4f2]'
                                        }`}>
                                        {isCompleted ? <CheckCircle2 className="w-5 h-5" /> : <FileText className="w-5 h-5" />}
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <button
                                            onClick={(e) => toggleItemCompletion(e, item.name)}
                                            className={`p-1.5 rounded-md transition-all ${isCompleted ? 'text-emerald-500 bg-emerald-50 hover:bg-emerald-100' : 'text-slate-300 hover:bg-slate-100 hover:text-slate-600'
                                                }`}
                                            title={isCompleted ? "읽음 표시 해제" : "읽음 표시"}
                                        >
                                            {isCompleted ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
                                        </button>
                                        <div className="flex flex-col items-end gap-1">
                                            {item.chapterTitle && (
                                                <Badge variant="secondary" className="text-[9px] px-1.5 py-0 bg-[#36a4f2]/5 text-[#36a4f2] uppercase">
                                                    {item.chapterTitle.split(' ')[0]}
                                                </Badge>
                                            )}
                                            <Badge variant="outline" className={`text-[10px] font-bold uppercase ${isCompleted ? 'text-emerald-400 border-emerald-200' : 'text-slate-400'}`}>
                                                {item.ext.replace('.', '')}
                                            </Badge>
                                        </div>
                                    </div>
                                </div>
                                <h4 className={`font-bold mb-2 transition-colors line-clamp-2 ${isCompleted ? 'text-slate-500' : 'text-slate-800 group-hover:text-[#36a4f2]'
                                    }`}>
                                    {item.name}
                                </h4>
                                <p className={`text-xs line-clamp-2 mb-4 leading-relaxed ${isCompleted ? 'text-slate-400' : 'text-slate-500'
                                    }`}>
                                    {item.summary}
                                </p>

                                {item.highlights && item.highlights.length > 0 && (
                                    <div className="space-y-1.5 mb-4">
                                        {item.highlights.slice(0, 2).map((h, i) => (
                                            <div key={i} className="flex items-start gap-2 text-[11px] text-slate-600">
                                                <CheckCircle2 className="w-3 h-3 text-[#36a4f2] mt-0.5 shrink-0" />
                                                <span className="line-clamp-1">{h}</span>
                                            </div>
                                        ))}
                                    </div>
                                )}

                                {/* Smart Linkage: Related Action Kits */}
                                {(() => {
                                    const relatedKits = getRelatedKits(item.name);
                                    if (relatedKits.length === 0) return null;
                                    return (
                                        <div className="mb-4 p-3 bg-slate-50 rounded-xl border border-slate-100/50">
                                            <div className="flex items-center gap-1.5 mb-2">
                                                <FolderOpen className="w-3 h-3 text-[#36a4f2]" />
                                                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-tighter">실무 활용 키트</span>
                                            </div>
                                            <div className="space-y-1.5">
                                                {relatedKits.map((kit, i) => (
                                                    <button
                                                        key={i}
                                                        onClick={(e) => {
                                                            e.stopPropagation();
                                                            onNavigateToKit?.(kit.name);
                                                        }}
                                                        className="w-full flex items-center justify-between gap-2 p-1.5 bg-white border border-slate-100 rounded-lg group/kit hover:border-[#36a4f2]/30 transition-all shadow-sm"
                                                    >
                                                        <span className="text-[10px] font-bold text-slate-700 line-clamp-1 group-hover/kit:text-[#36a4f2] text-left">
                                                            {kit.name}
                                                        </span>
                                                        <Badge variant="outline" className="text-[8px] py-0 px-1 border-slate-200 text-slate-400 group-hover/kit:border-[#36a4f2]/20 group-hover/kit:text-[#36a4f2]/70 shrink-0">
                                                            {kit.type}
                                                        </Badge>
                                                    </button>
                                                ))}
                                            </div>
                                        </div>
                                    );
                                })()}

                                <div className="mt-auto pt-4 border-t border-slate-50 flex justify-between items-center">
                                    <span className="text-[11px] font-medium text-slate-400">{item.size}</span>
                                    <Button
                                        variant="ghost"
                                        size="icon"
                                        className="w-8 h-8 rounded-full text-slate-400 hover:text-white hover:bg-[#36a4f2]"
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            handleDownload(item.path, item.name);
                                        }}
                                    >
                                        <Download className="w-4 h-4" />
                                    </Button>
                                </div>
                            </CardContent>
                        </Card>
                    );
                })}

                {displayItems.length === 0 && (
                    <div className="col-span-full py-20 flex flex-col items-center justify-center text-slate-400">
                        <Info className="w-12 h-12 mb-4 opacity-20" />
                        <p className="text-lg font-bold">검색 결과가 없습니다.</p>
                        <p className="text-sm">다른 키워드로 다시 검색해 보세요.</p>
                    </div>
                )}
            </div>

            {/* AI Call to Action */}
            <div className="bg-slate-900 rounded-3xl p-8 text-white relative overflow-hidden shadow-xl">
                <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-[#36a4f2]/20 to-purple-500/20 blur-2xl" />
                <div className="relative z-10 flex flex-col md:flex-row items-center justify-between gap-6">
                    <div>
                        <div className="flex items-center gap-2 mb-2">
                            <Sparkles className="w-4 h-4 text-[#36a4f2]" />
                            <span className="text-xs font-bold uppercase tracking-widest text-[#36a4f2]">AI Assistant</span>
                        </div>
                        <h3 className="text-xl font-bold mb-1">법적 의무 사항이 헷갈리시나요?</h3>
                        <p className="text-slate-400 text-sm">AI 법률 전문가에게 질문하고 즉시 해결책을 얻으세요.</p>
                    </div>
                    <Button className="bg-white text-slate-900 hover:bg-slate-100 rounded-full font-bold px-6">
                        AI 상담 시작하기
                    </Button>
                </div>
            </div>

            {/* Disclaimer */}
            <div className="mt-12 text-center border-t border-slate-100 pt-8 pb-4">
                <p className="text-xs font-bold text-slate-400 mb-2">📌 법적 면책 조항 (Disclaimer)</p>
                <p className="text-[11px] leading-relaxed text-slate-400 max-w-3xl mx-auto">
                    본 서비스에서 제공하는 창업 법령 가이드 콘텐츠는 초기 창업가의 이해를 돕기 위해 작성된 <span className="text-slate-500 font-bold">단순 참고용 자료</span>입니다.<br />
                    각 비즈니스의 구체적 상황, 업종, 규모 및 최신 법 개정 상황에 따라 적용 내용이 달라질 수 있으므로, 실제 의사결정 및 행정/세무 절차 진행 시에는 반드시 <span className="text-slate-500 font-bold">해당 분야 전문가(변호사, 노무사, 세무사 등)의 검토와 자문</span>을 거치시길 권장합니다.<br />
                    본 자료의 활용으로 인해 발생하는 직접·간접적인 결과에 대해 플랫폼은 법적인 책임을 지지 않습니다.
                </p>
            </div>
        </div>
    );
};
