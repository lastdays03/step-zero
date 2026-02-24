"use client";

import React, { useState } from 'react';
import { useActionKit } from '../hooks/useActionKit';
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
    FolderOpen,
    Search,
    Download,
    Info,
    Calendar,
    Layers,
    Briefcase,
    TrendingUp,
    Sparkles,
    Gavel,
    CheckSquare,
    Package,
    Users,
    Building,
    Eye,
    LucideIcon,
} from 'lucide-react';
import { ActionKitItem, RelatedLaw } from '../types';

const STARTER_PACKS = [
    {
        id: "hire",
        title: "직원 채용 필수 팩",
        icon: Users,
        color: "text-purple-500",
        bg: "bg-purple-100",
        keywords: ["근로계약서", "취업규칙", "비밀유지"]
    },
    {
        id: "office",
        title: "사무실 계약 팩",
        icon: Building,
        color: "text-[#36a4f2]",
        bg: "bg-[#36a4f2]/10",
        keywords: ["임대차", "화재안전", "건축물"]
    },
    {
        id: "invest",
        title: "투자 유치 준비 팩",
        icon: Package,
        color: "text-orange-500",
        bg: "bg-orange-100",
        keywords: ["주주", "정관", "이사회"]
    }
];

const CATEGORY_ICONS: Record<string, LucideIcon> = {
    all: Layers,
    legal: Gavel,
    tax: TrendingUp,
    hr: Briefcase,
    grant: Sparkles,
};

const CATEGORY_COLORS: Record<string, string> = {
    all: 'bg-slate-100 text-slate-600',
    legal: 'bg-[#36a4f2]/10 text-[#36a4f2]',
    tax: 'bg-green-100 text-green-600',
    hr: 'bg-purple-100 text-purple-600',
    grant: 'bg-orange-100 text-orange-600',
};

const isRelatedLawObject = (law: string | RelatedLaw): law is RelatedLaw => {
    return typeof law === "object" && law !== null && "name" in law;
};

interface ActionKitLibraryViewProps {
    initialSearch?: string;
    onNavigateToLaw?: (lawTitle: string) => void;
}

export const ActionKitLibraryView = ({ initialSearch = "", onNavigateToLaw }: ActionKitLibraryViewProps) => {
    const { data, loading, error } = useActionKit();
    const [selectedCategory, setSelectedCategory] = useState<string>("all");
    const [searchQuery, setSearchQuery] = useState(initialSearch);
    const [activeStarterPack, setActiveStarterPack] = useState<string | null>(null);
    const [previewKit, setPreviewKit] = useState<ActionKitItem | null>(null);

    if (loading) return <div className="p-8 text-center text-slate-500">액션 키트 라이브러리를 불러오는 중...</div>;
    if (error) return <div className="p-8 text-center text-red-500">{error}</div>;
    if (!data) return null;

    const categories = Object.entries(data);
    const currentCategory = data[selectedCategory];

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

    const filteredItems = Object.values(data).flatMap(cat =>
        cat.items.map(item => ({ ...item, categoryTitle: cat.title }))
    ).filter(item => {
        const isMatch = item.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
            item.summary.toLowerCase().includes(searchQuery.toLowerCase());

        if (activeStarterPack) {
            const pack = STARTER_PACKS.find(p => p.id === activeStarterPack);
            if (pack) {
                return pack.keywords.some(keyword =>
                    item.name.toLowerCase().includes(keyword.toLowerCase()) ||
                    item.summary.toLowerCase().includes(keyword.toLowerCase())
                );
            }
        }

        return isMatch;
    });

    const displayItems = (searchQuery || activeStarterPack) ? filteredItems : (currentCategory?.items || []);

    return (
        <div className="space-y-8 animate-in fade-in duration-500">
            {/* Header with Search */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                    <h2 className="text-2xl font-bold text-slate-900">액션 키트 라이브러리</h2>
                    <p className="text-sm text-slate-500 mt-1">
                        {searchQuery ? `'${searchQuery}' 검색 결과` : "실무에 즉시 투입 가능한 문서와 도구들을 확인하세요."}
                    </p>
                </div>
                <div className="relative w-full md:w-64">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 w-4 h-4" />
                    <input
                        type="text"
                        placeholder="키트 검색..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="w-full pl-10 pr-4 py-2 bg-white border border-slate-200 rounded-full text-sm focus:ring-2 focus:ring-[#36a4f2]/20 transition-all outline-none"
                    />
                </div>
            </div>

            {/* Category Cards (Only show if not searching or pack) */}
            {!searchQuery && !activeStarterPack && (
                <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
                    {categories.map(([id, category]) => {
                        const Icon = CATEGORY_ICONS[id] || FolderOpen;
                        const isSelected = selectedCategory === id;
                        return (
                            <button
                                key={id}
                                onClick={() => setSelectedCategory(id)}
                                className={`flex flex-col items-center p-4 rounded-2xl transition-all ${isSelected
                                    ? 'bg-[#36a4f2] text-white shadow-lg scale-105'
                                    : 'bg-white hover:bg-slate-50 border border-slate-100 text-slate-600'
                                    }`}
                            >
                                <div className={`w-10 h-10 rounded-full flex items-center justify-center mb-2 ${isSelected ? 'bg-white/20' : CATEGORY_COLORS[id] || 'bg-slate-100'
                                    }`}>
                                    <Icon className="w-5 h-5" />
                                </div>
                                <span className="text-xs font-bold whitespace-nowrap">{category.title.split(' ')[0]}</span>
                            </button>
                        );
                    })}
                </div>
            )}

            {/* Starter Packs UI and logic */}
            {!searchQuery && selectedCategory === "all" && (
                <div className="space-y-3 animate-in fade-in slide-in-from-bottom-4 duration-500 delay-100">
                    <h3 className="text-sm font-bold text-slate-700 flex items-center gap-2">
                        <Sparkles className="w-4 h-4 text-[#36a4f2]" />
                        스타터 팩 컬렉션
                    </h3>
                    <div className="flex flex-col md:flex-row gap-4">
                        {STARTER_PACKS.map(pack => {
                            const PIcon = pack.icon;
                            const isActive = activeStarterPack === pack.id;
                            return (
                                <button
                                    key={pack.id}
                                    onClick={() => {
                                        if (isActive) {
                                            setActiveStarterPack(null);
                                            setSearchQuery("");
                                        } else {
                                            setActiveStarterPack(pack.id);
                                            setSearchQuery(""); // Clear search to use starter pack filter
                                        }
                                    }}
                                    className={`flex-1 p-4 rounded-2xl border transition-all text-left group flex items-start justify-between ${isActive
                                        ? "bg-slate-900 border-slate-900 shadow-lg text-white"
                                        : `border-slate-200 hover:shadow-md bg-white`
                                        }`}
                                >
                                    <div>
                                        <div className={`w-8 h-8 rounded-full flex items-center justify-center mb-2 ${isActive ? 'bg-white/20' : pack.bg}`}>
                                            <PIcon className={`w-4 h-4 ${isActive ? 'text-white' : pack.color}`} />
                                        </div>
                                        <div className={`font-bold text-sm ${isActive ? 'text-white' : 'text-slate-800'}`}>
                                            {pack.title}
                                        </div>
                                        <div className={`text-[10px] mt-1 ${isActive ? 'text-slate-300' : 'text-slate-500'}`}>
                                            주요: {pack.keywords.join(', ')}
                                        </div>
                                    </div>
                                </button>
                            );
                        })}
                    </div>
                </div>
            )}

            {/* Kits Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {displayItems.length > 0 ? (
                    displayItems.map((item, index) => (
                        <Card key={`${item.name}-${index}`} className="group hover:border-[#36a4f2] transition-all duration-300 shadow-sm hover:shadow-md cursor-pointer flex flex-col justify-between overflow-hidden">
                            <CardContent className="p-0 flex flex-col h-full">
                                <div className="p-6 pb-0">
                                    <div className="flex justify-between items-start mb-4">
                                        <Badge variant="outline" className="text-[10px] font-black text-[#36a4f2] bg-[#36a4f2]/5 border-[#36a4f2]/10 uppercase py-0.5 px-2">
                                            {item.tag || '[실무]'}
                                        </Badge>
                                        <div className="flex items-center gap-2">
                                            {item.dday && (
                                                <Badge className="bg-orange-500 hover:bg-orange-600 text-[10px] font-bold py-0 h-5">
                                                    {item.dday}
                                                </Badge>
                                            )}
                                            <Badge variant="secondary" className="text-[10px] font-bold text-slate-400 py-0 h-5">
                                                {item.type}
                                            </Badge>
                                        </div>
                                    </div>
                                    <h4 className="font-bold text-slate-800 mb-2 group-hover:text-[#36a4f2] transition-colors leading-tight min-h-[2.5rem] line-clamp-2">
                                        {item.name}
                                    </h4>
                                    <p className="text-xs text-slate-400 mb-3 line-clamp-2 leading-relaxed">
                                        {item.summary}
                                    </p>
                                    {(item as any).highlights?.length > 0 && (
                                        <div className="flex flex-wrap gap-1 mb-3">
                                            {(item as any).highlights.slice(0, 2).map((hl: any, i: number) => (
                                                <span key={hl.id || i} className="text-[10px] font-medium text-amber-700 bg-amber-50 border border-amber-100 px-2 py-0.5 rounded-full truncate max-w-[180px]">
                                                    ⭐ {hl.content}
                                                </span>
                                            ))}
                                            {(item as any).highlights.length > 2 && (
                                                <span className="text-[10px] text-slate-400 font-medium">+{(item as any).highlights.length - 2}개</span>
                                            )}
                                        </div>
                                    )}
                                </div>

                                <div className="mt-auto px-6 pb-6 space-y-4">
                                    <div className="pt-2 border-t border-slate-50">
                                        {item.relatedLaws && item.relatedLaws.length > 0 && (
                                            <div className="space-y-2">
                                                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1">
                                                    <Gavel className="w-3 h-3" /> 관련 조문 및 해설
                                                </p>
                                                <div className="space-y-1.5">
                                                    {item.relatedLaws.map((law, i) => {
                                                        const name = isRelatedLawObject(law) ? law.name : law;
                                                        const summary = isRelatedLawObject(law) ? law.summary : null;
                                                        const snippet = isRelatedLawObject(law) ? law.snippet : null;

                                                        return (
                                                            <div key={i} className="group/law relative inline-block mr-2 mb-2">
                                                                <button onClick={(e) => {
                                                                    e.stopPropagation();
                                                                    onNavigateToLaw?.(name);
                                                                }} className="flex items-center gap-1.5 w-full text-left">
                                                                    <span className="text-[10px] font-bold text-[#36a4f2] bg-[#36a4f2]/5 px-1.5 py-0.5 rounded border border-[#36a4f2]/10 transition-colors group-hover/law:bg-[#36a4f2]/10">
                                                                        #{name}
                                                                    </span>
                                                                    {summary && (
                                                                        <span className="text-[10px] text-slate-500 line-clamp-1 flex-1 transition-colors group-hover/law:text-slate-700">
                                                                            {summary}
                                                                        </span>
                                                                    )}
                                                                </button>
                                                                {/* Simple Snippet implementation using CSS hover */}
                                                                {snippet && (
                                                                    <div className="absolute z-50 bottom-full left-0 mb-2 hidden w-64 p-3 bg-slate-900 border border-slate-800 text-slate-200 text-xs rounded-xl shadow-xl group-hover/law:block group-hover/law:animate-in group-hover/law:fade-in duration-200">
                                                                        <p className="font-bold text-[#36a4f2] mb-1">법령 스니펫 미리보기</p>
                                                                        <p className="leading-relaxed whitespace-pre-wrap">{snippet}</p>
                                                                    </div>
                                                                )}
                                                            </div>
                                                        );
                                                    })}
                                                </div>
                                            </div>
                                        )}
                                    </div>

                                    <div className="pt-4 border-t border-slate-50 flex justify-between items-center">
                                        <div className="flex items-center gap-2 text-slate-400">
                                            <Calendar className="w-3 h-3" />
                                            <span className="text-[10px] font-medium">Updated: 2026.02</span>
                                        </div>
                                        <Button
                                            size="sm"
                                            variant="outline"
                                            className="h-8 rounded-full border-slate-200 hover:bg-slate-50 gap-1.5 px-3"
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                setPreviewKit(item);
                                            }}
                                        >
                                            <Eye className="w-3 h-3 text-slate-400" />
                                            <span className="text-[11px] font-bold text-slate-600">미리보기</span>
                                        </Button>
                                        <Button
                                            size="sm"
                                            className="h-8 rounded-full bg-[#36a4f2] hover:bg-[#258bd1] gap-1.5 px-4"
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                handleDownload(item.path, item.name);
                                            }}
                                        >
                                            <Download className="w-3 h-3" />
                                            <span className="text-[11px] font-bold">다운로드</span>
                                        </Button>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    ))
                ) : (
                    <div className="col-span-full py-20 flex flex-col items-center justify-center text-slate-400">
                        <Info className="w-12 h-12 mb-4 opacity-20" />
                        <p className="text-lg font-bold">검색 결과가 없습니다.</p>
                        <p className="text-sm">다른 키워드로 다시 검색해 보세요.</p>
                    </div>
                )}
            </div>

            {/* Checklist Modal Preview */}
            {previewKit && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm animate-in fade-in duration-200">
                    <div className="bg-white rounded-3xl shadow-2xl w-full max-w-lg overflow-hidden animate-in zoom-in-95 duration-200">
                        <div className="p-6 border-b border-slate-100 flex justify-between items-start bg-slate-50">
                            <div>
                                <Badge className="mb-2 bg-[#36a4f2]/10 text-[#36a4f2] hover:bg-[#36a4f2]/20 border-none">
                                    {previewKit.type}
                                </Badge>
                                <h3 className="text-xl font-bold text-slate-900">{previewKit.name}</h3>
                            </div>
                            <Button
                                variant="ghost"
                                size="sm"
                                className="h-8 w-8 p-0 rounded-full"
                                onClick={() => setPreviewKit(null)}
                            >
                                ✕
                            </Button>
                        </div>
                        <div className="p-6 max-h-[60vh] overflow-y-auto space-y-6">
                            {previewKit.complianceChecklist && previewKit.complianceChecklist.length > 0 && (
                                <div className="space-y-3">
                                    <h4 className="font-bold flex items-center gap-2 text-slate-800">
                                        <CheckSquare className="w-4 h-4 text-emerald-500" />
                                        사용 전 필수 체크리스트
                                    </h4>
                                    <div className="space-y-2">
                                        {previewKit.complianceChecklist.map((item, i) => (
                                            <label key={i} className="flex items-start gap-3 p-3 rounded-xl border border-slate-100 hover:border-[#36a4f2]/30 hover:bg-[#36a4f2]/5 transition-colors cursor-pointer group">
                                                <input type="checkbox" className="mt-1 w-4 h-4 rounded border-slate-300 text-[#36a4f2] focus:ring-[#36a4f2]" />
                                                <span className="text-sm text-slate-600 group-hover:text-slate-900 leading-tight">
                                                    {item}
                                                </span>
                                            </label>
                                        ))}
                                    </div>
                                    <p className="text-[10px] text-slate-400 mt-2 ml-7">* 이 체크리스트는 법률 컨설팅을 대체하지 않습니다.</p>
                                </div>
                            )}
                            {(previewKit as any).highlights?.length > 0 && (
                                <div className="space-y-3">
                                    <h4 className="font-bold flex items-center gap-2 text-slate-800">
                                        <Sparkles className="w-4 h-4 text-amber-500" />
                                        핵심 포인트
                                    </h4>
                                    <div className="space-y-2">
                                        {(previewKit as any).highlights.map((hl: any, i: number) => (
                                            <div key={hl.id || i} className="flex items-start gap-2.5 p-3 rounded-xl bg-amber-50 border border-amber-100">
                                                <span className="text-amber-500 font-bold text-sm mt-0.5">⭐</span>
                                                <span className="text-sm text-slate-700 leading-relaxed">{hl.content}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                            <div>
                                <h4 className="font-bold mb-2 text-slate-800 text-sm">문서 내용 요약</h4>
                                <p className="text-sm text-slate-600 leading-relaxed bg-slate-50 p-4 rounded-xl border border-slate-100">
                                    {previewKit.summary}
                                </p>
                            </div>
                        </div>
                        <div className="p-6 border-t border-slate-100 flex justify-end gap-3 bg-white">
                            <Button variant="outline" onClick={() => setPreviewKit(null)}>
                                닫기
                            </Button>
                            <Button
                                className="bg-[#36a4f2] hover:bg-[#258bd1] gap-2"
                                onClick={() => {
                                    handleDownload(previewKit.path, previewKit.name);
                                    setPreviewKit(null);
                                }}
                            >
                                <Download className="w-4 h-4" />
                                원본 다운로드
                            </Button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};
