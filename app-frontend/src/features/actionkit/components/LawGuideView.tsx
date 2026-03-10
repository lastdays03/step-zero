"use client";

import React, { useState, useRef, useEffect } from 'react';
import { useLawGuide } from '../hooks/useLawGuide';
import { Disclaimer } from '@/components/ui/Disclaimer';
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
    Search,
    FileText,
    Download,
    CheckCircle2,
    Info,
    FolderOpen,
    Eye,
    EyeOff
} from 'lucide-react';
import { LawItem, RelatedLaw } from '../types';
import { useActionKit } from '../hooks/useActionKit';
import { LawDetailPopup } from './LawDetailPopup';
import { trackEvent } from '@/features/ops/actionkit/api';

const API_URL = process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ?? "";

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
    const [selectedLaw, setSelectedLaw] = useState<LawItem | null>(null);

    const searchTrackTimer = useRef<ReturnType<typeof setTimeout>>();
    useEffect(() => {
        if (searchQuery.length >= 2) {
            clearTimeout(searchTrackTimer.current);
            searchTrackTimer.current = setTimeout(() => {
                trackEvent({ event_type: "search", search_query: searchQuery });
            }, 1000);
        }
        return () => clearTimeout(searchTrackTimer.current);
    }, [searchQuery]);

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
                const name = isRelatedLawObject(rl) ? rl.name : rl;
                return name.includes(lawName) || lawName.includes(name);
            }))
            .slice(0, 3);
    };

    React.useEffect(() => {
        if (initialSearch) {
            setSearchQuery(initialSearch);
        }
    }, [initialSearch]);

    if (loading) return <div className="p-8 text-center text-slate-500">법령 가이드를 불러오는 중...</div>;
    if (error) return <div className="p-8 text-center text-red-500">{error}</div>;
    if (!data) return null;

    const chapters = Object.entries(data);
    const currentChapter = data[activeChapter];

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
                            onClick={() => { setSelectedLaw(item); if (item.id) trackEvent({ event_type: "detail_view", item_id: item.id }); }}
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
                                    {item.id && (
                                        <Button
                                            variant="ghost"
                                            size="icon"
                                            className="w-8 h-8 rounded-full text-slate-400 hover:text-white hover:bg-[#36a4f2]"
                                            asChild
                                            onClick={(e) => e.stopPropagation()}
                                        >
                                            <a
                                                href={`${API_URL}/api/v1/actionkits/items/${item.id}/view`}
                                                target="_blank"
                                                rel="noreferrer"
                                            >
                                                <Download className="w-4 h-4" />
                                            </a>
                                        </Button>
                                    )}
                                </div>
                            </CardContent>
                        </Card>
                    );
                })}

                {
                    displayItems.length === 0 && (
                        <div className="col-span-full py-20 flex flex-col items-center justify-center text-slate-400">
                            <Info className="w-12 h-12 mb-4 opacity-20" />
                            <p className="text-lg font-bold">검색 결과가 없습니다.</p>
                            <p className="text-sm">다른 키워드로 다시 검색해 보세요.</p>
                        </div>
                    )
                }
            </div >

            {/* Law Detail Popup */}
            {selectedLaw && (
                <LawDetailPopup
                    item={selectedLaw}
                    relatedKits={getRelatedKits(selectedLaw.name)}
                    onClose={() => setSelectedLaw(null)}
                    onNavigateToKit={onNavigateToKit}
                />
            )}
            <Disclaimer />
        </div >
    );
};
