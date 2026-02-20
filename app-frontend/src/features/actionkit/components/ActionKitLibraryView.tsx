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
            </div>

            {/* Legal Disclaimer */}
            <div className="pt-8 border-t border-slate-100 text-center">
                <p className="text-[10px] text-slate-400 leading-relaxed max-w-4xl mx-auto break-keep italic">
                    <span className="font-bold">Disclaimer</span> : 본 조사자료는 고객의 창업에 정보를 제공할 목적으로 작성되었으며, 어떠한 경우에도 무단 복제 및 배포될 수 없습니다.
                    또한 본 자료에 수록된 내용은 당사가 신뢰할 만한 자료 및 정보로 얻어진 것이나, 그 정확성이나 완전성을 보장할 수 없으므로 창업자 자신의 판단과 책임 하에 최종 결정을 하시기 바랍니다.
                    따라서 어떠한 경우에도 본 자료는 창업자의 창업에 따른 결과에 대한 법적 책임 소재의 증빙자료로 사용될 수 없습니다.
                </p>
            </div>
        </div>
    );
};
