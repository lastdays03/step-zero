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
    FileText,
    Briefcase,
    TrendingUp,
    ChevronRight,
    Sparkles,
    Gavel
} from 'lucide-react';
import { ActionKitItem, ActionKitCategory } from '../types';

const CATEGORY_ICONS: Record<string, any> = {
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

export const ActionKitLibraryView = () => {
    const { data, loading, error } = useActionKit();
    const [selectedCategory, setSelectedCategory] = useState<string>("all");
    const [searchQuery, setSearchQuery] = useState("");

    const [selectedItem, setSelectedItem] = useState<ActionKitItem | null>(null);

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
    ).filter(item =>
        item.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.summary.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const displayItems = searchQuery ? filteredItems : (currentCategory?.items || []);

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

            {/* Category Cards (Only show if not searching) */}
            {!searchQuery && (
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
                                    <p className="text-xs text-slate-400 mb-6 line-clamp-2 leading-relaxed">
                                        {item.summary}
                                    </p>
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
                                                        const isObject = typeof law === 'object';
                                                        const name = isObject ? (law as any).name : law;
                                                        const summary = isObject ? (law as any).summary : null;

                                                        return (
                                                            <div key={i} className="group/law">
                                                                <div className="flex flex-wrap items-center gap-1.5">
                                                                    <span className="text-[10px] font-bold text-[#36a4f2] bg-[#36a4f2]/5 px-1.5 py-0.5 rounded border border-[#36a4f2]/10 transition-colors group-hover/law:bg-[#36a4f2]/10">
                                                                        #{name}
                                                                    </span>
                                                                    {summary && (
                                                                        <span className="text-[10px] text-slate-500 line-clamp-1 flex-1 transition-colors group-hover/law:text-slate-700">
                                                                            {summary}
                                                                        </span>
                                                                    )}
                                                                </div>
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

        </div>
    );
};
