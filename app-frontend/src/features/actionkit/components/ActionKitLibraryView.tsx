"use client";

import React, { useState, useEffect } from 'react';
import { toast } from "sonner";
import JSZip from 'jszip';
import { saveAs } from 'file-saver';
import { useActionKit } from '../hooks/useActionKit';
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
    FolderOpen,
    Search,
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
    Star,
    X,
    Trash2,
    LucideIcon,
    History,
    ExternalLink,
} from 'lucide-react';
import { ActionKitItem, RelatedLaw } from '../types';
import { apiClient } from '@/lib/api-client';
import { ActionKitDetailModal } from './ActionKitDetailModal';

const API_URL = process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ?? "";

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
    const [selectedTag, setSelectedTag] = useState<string>("all");
    const [previewKit, setPreviewKit] = useState<ActionKitItem | null>(null);
    const [detailItem, setDetailItem] = useState<ActionKitItem | null>(null);
    const [recentItems, setRecentItems] = useState<ActionKitItem[]>([]);
    const [isHistoryOpen, setIsHistoryOpen] = useState(false);


    useEffect(() => {
        setSelectedTag("all");
    }, [selectedCategory, searchQuery, activeStarterPack]);

    const [checkedItems, setCheckedItems] = useState<Record<string, boolean>>({});
    const [bookmarkedItems, setBookmarkedItems] = useState<Record<string, ActionKitItem>>({});
    const [isDrawerOpen, setIsDrawerOpen] = useState(false);
    const [isZipping, setIsZipping] = useState(false);

    // Onboarding State
    const [isOnboardingOpen, setIsOnboardingOpen] = useState(false);
    const [onboardingStep, setOnboardingStep] = useState<1 | 2>(1);
    const [selectedPackId, setSelectedPackId] = useState<string | null>(null);

    useEffect(() => {
        const hasSeenOnboarding = localStorage.getItem('actionkit_onboarding_shown');
        if (!hasSeenOnboarding) {
            setIsOnboardingOpen(true);
        }
    }, []);

    useEffect(() => {
        const storedChecklists = localStorage.getItem('actionkit_checklists');
        if (storedChecklists) {
            try { setCheckedItems(JSON.parse(storedChecklists)); } catch { /* ignore */ }
        }
        const storedBookmarks = localStorage.getItem('actionkit_bookmarks');
        if (storedBookmarks) {
            try { setBookmarkedItems(JSON.parse(storedBookmarks)); } catch { /* ignore */ }
        }
        const storedRecents = localStorage.getItem('actionkit_recents');
        if (storedRecents) {
            try { setRecentItems(JSON.parse(storedRecents)); } catch { /* ignore */ }
        }
    }, []);

    const handleItemClick = (item: ActionKitItem) => {
        setDetailItem(item);
        setRecentItems(prev => {
            const filtered = prev.filter(i => i.name !== item.name);
            const next = [item, ...filtered].slice(0, 5); // Keep up to 5 items
            localStorage.setItem('actionkit_recents', JSON.stringify(next));
            return next;
        });
    };

    const toggleBookmark = (kit: ActionKitItem, e: React.MouseEvent) => {
        e.stopPropagation();
        const identifier = kit.id ?? kit.name;
        const newBookmarks = { ...bookmarkedItems };
        if (newBookmarks[identifier]) {
            delete newBookmarks[identifier];
        } else {
            newBookmarks[identifier] = kit;
        }
        setBookmarkedItems(newBookmarks);
        localStorage.setItem('actionkit_bookmarks', JSON.stringify(newBookmarks));
    };

    const handleBulkDownload = async () => {
        setIsZipping(true);
        try {
            const zip = new JSZip();
            const items = Object.values(bookmarkedItems);

            await Promise.all(items.map(async (item) => {
                const itemId = item.id;
                let blob: Blob | null = null;
                if (itemId) {
                    try {
                        const res = await apiClient.get(`/actionkits/items/${itemId}/download`, { responseType: 'blob' });
                        blob = new Blob([res.data]);
                    } catch (apiErr: unknown) {
                        const err = apiErr as { response?: { status?: number } };
                        if (err.response?.status !== 404) throw apiErr;
                    }
                }

                if (!blob && item.path) {
                    let finalPath = item.path;
                    if (finalPath.startsWith('library/resources/')) {
                        finalPath = finalPath.replace('library/resources/', 'actionkits/files/');
                    }
                    if (finalPath.startsWith('http')) {
                        const res = await fetch(finalPath);
                        blob = await res.blob();
                    } else {
                        const baseURL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";
                        const res = await fetch(`${baseURL}/${finalPath}`);
                        blob = await res.blob();
                    }
                }

                if (blob) {
                    const filename = item.files?.[0]?.original_filename || `${item.name}.${item.ext || 'pdf'}`;
                    zip.file(filename, blob);
                }
            }));

            const content = await zip.generateAsync({ type: 'blob' });
            saveAs(content, '나만의_액션키트_보관함.zip');
        } catch (error) {
            console.error(error);
            toast.error("다운로드 중 오류가 발생했습니다.");
        } finally {
            setIsZipping(false);
        }
    };

    const toggleChecklist = (kitId: number | string, itemText: string) => {
        const key = `${kitId}_${itemText}`;
        const newChecked = { ...checkedItems, [key]: !checkedItems[key] };
        setCheckedItems(newChecked);
        localStorage.setItem('actionkit_checklists', JSON.stringify(newChecked));
    };

    const handleAddPackToDrawer = () => {
        if (!selectedPackId || !data) return;
        const pack = STARTER_PACKS.find(p => p.id === selectedPackId);
        if (!pack) return;

        const newBookmarks = { ...bookmarkedItems };
        let addedCount = 0;

        Object.values(data).forEach(cat => {
            cat.items.forEach(item => {
                const isMatch = pack.keywords.some(keyword =>
                    item.name.toLowerCase().includes(keyword.toLowerCase()) ||
                    item.summary.toLowerCase().includes(keyword.toLowerCase()) ||
                    (item.tag && item.tag.toLowerCase() === keyword.toLowerCase())
                );
                if (isMatch) {
                    const identifier = item.id ?? item.name;
                    if (!newBookmarks[identifier]) {
                        newBookmarks[identifier] = item;
                        addedCount++;
                    }
                }
            });
        });

        if (addedCount > 0) {
            setBookmarkedItems(newBookmarks);
            localStorage.setItem('actionkit_bookmarks', JSON.stringify(newBookmarks));
        }

        setIsOnboardingOpen(false);
        localStorage.setItem('actionkit_onboarding_shown', 'true');
        setTimeout(() => setIsDrawerOpen(true), 300);
    };

    const handleOnboardingSkip = () => {
        setIsOnboardingOpen(false);
        localStorage.setItem('actionkit_onboarding_shown', 'true');
    };

    const getKitProgress = (kit: ActionKitItem) => {
        if (!kit.complianceChecklist || kit.complianceChecklist.length === 0) return null;
        const kitIdentifier = kit.id ?? kit.name;
        const total = kit.complianceChecklist.length;
        const checked = kit.complianceChecklist.filter(item => checkedItems[`${kitIdentifier}_${item}`]).length;
        const percentage = Math.round((checked / total) * 100);
        return { total, checked, percentage };
    };

    if (loading) return <div className="p-8 text-center text-slate-500">액션 키트 라이브러리를 불러오는 중...</div>;
    if (error) return <div className="p-8 text-center text-red-500">{error}</div>;
    if (!data) return null;

    const categories = Object.entries(data);
    const currentCategory = data[selectedCategory];

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

    const baseDisplayItems = (searchQuery || activeStarterPack) ? filteredItems : (currentCategory?.items || []);
    const availableTags = Array.from(new Set(baseDisplayItems.map(item => item.tag).filter(Boolean))).sort();
    const displayItems = selectedTag === "all" ? baseDisplayItems : baseDisplayItems.filter(item => item.tag === selectedTag);

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
                <div className="flex items-center gap-2 w-full md:w-auto">
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
                    <Button
                        onClick={() => {
                            setOnboardingStep(1);
                            setSelectedPackId(null);
                            setIsOnboardingOpen(true);
                        }}
                        variant="outline"
                        className="rounded-full border-[#36a4f2]/30 text-[#36a4f2] hover:bg-[#36a4f2]/5 whitespace-nowrap h-10 px-4"
                    >
                        🎁 맞춤 팩 받기
                    </Button>

                    {/* Recent Items Dropdown */}
                    <div className="relative">
                        <Button
                            variant="outline"
                            onClick={() => setIsHistoryOpen(!isHistoryOpen)}
                            className="rounded-full border-slate-200 text-slate-600 hover:bg-slate-50 h-10 px-4 gap-2 whitespace-nowrap"
                        >
                            <History className="w-4 h-4" />
                            <span className="hidden sm:inline">최근 본 액션키트</span>
                            {recentItems.length > 0 && (
                                <span className="bg-slate-100 text-slate-500 text-[10px] font-bold px-1.5 py-0.5 rounded-full min-w-[1.25rem] text-center">
                                    {recentItems.length}
                                </span>
                            )}
                        </Button>

                        {isHistoryOpen && (
                            <>
                                <div className="fixed inset-0 z-40" onClick={() => setIsHistoryOpen(false)} />
                                <div className="absolute right-0 mt-2 w-72 bg-white rounded-2xl shadow-xl shadow-slate-200/50 border border-slate-100 z-50 overflow-hidden animate-in fade-in slide-in-from-top-2 duration-200">
                                    <div className="p-3 border-b border-slate-50 bg-slate-50/50 flex justify-between items-center">
                                        <h4 className="text-xs font-bold text-slate-700 flex items-center gap-1.5">
                                            <History className="w-3.5 h-3.5 text-slate-400" />
                                            최근 열람한 문서
                                        </h4>
                                        {recentItems.length > 0 && (
                                            <button onClick={() => { setRecentItems([]); localStorage.setItem('actionkit_recents', '[]'); }} className="text-[10px] text-slate-400 hover:text-red-500 font-medium px-2 py-1 rounded hover:bg-red-50 transition-colors">
                                                기록 지우기
                                            </button>
                                        )}
                                    </div>
                                    <div className="max-h-64 overflow-y-auto">
                                        {recentItems.length === 0 ? (
                                            <div className="p-6 text-center text-slate-400 text-xs">
                                                열람한 문서 기록이 없습니다.
                                            </div>
                                        ) : (
                                            <div className="p-2 space-y-1">
                                                {recentItems.map((item, i) => (
                                                    <button
                                                        key={i}
                                                        onClick={() => { handleItemClick(item); setIsHistoryOpen(false); }}
                                                        className="w-full text-left p-2 hover:bg-[#36a4f2]/5 rounded-xl transition-colors group flex items-start gap-2.5 outline-none focus:bg-[#36a4f2]/5"
                                                    >
                                                        <div className="w-6 h-6 rounded bg-slate-100 flex items-center justify-center shrink-0 group-hover:bg-[#36a4f2]/10 transition-colors">
                                                            <FolderOpen className="w-3 h-3 text-slate-400 group-hover:text-[#36a4f2]" />
                                                        </div>
                                                        <div className="flex-1 min-w-0">
                                                            <p className="text-[11px] font-bold text-slate-700 truncate group-hover:text-[#36a4f2] transition-colors">
                                                                {item.name}
                                                            </p>
                                                            <p className="text-[9px] text-slate-400 truncate mt-0.5">
                                                                {item.tag || item.type}
                                                            </p>
                                                        </div>
                                                    </button>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </>
                        )}
                    </div>

                    <Button
                        onClick={() => setIsDrawerOpen(true)}
                        className="rounded-full bg-yellow-50 hover:bg-yellow-100 border border-yellow-200 text-yellow-700 relative h-10 px-4 whitespace-nowrap"
                    >
                        <Star className={`w-4 h-4 mr-1 ${Object.keys(bookmarkedItems).length > 0 ? 'fill-yellow-500 text-yellow-500' : ''}`} />
                        서랍장
                        {Object.keys(bookmarkedItems).length > 0 && (
                            <span className="absolute -top-1 -right-1 bg-red-500 text-white text-[10px] font-bold w-5 h-5 flex items-center justify-center rounded-full border-2 border-white shadow-sm">
                                {Object.keys(bookmarkedItems).length}
                            </span>
                        )}
                    </Button>
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

            {/* Tag Filter Bar */}
            {availableTags.length > 0 && (
                <div className="flex flex-wrap items-center gap-2 py-2 animate-in fade-in slide-in-from-bottom-2 duration-300">
                    <button
                        onClick={() => setSelectedTag("all")}
                        className={`px-4 py-1.5 rounded-full text-[13px] font-bold transition-all ${selectedTag === "all" ? "bg-slate-800 text-white shadow-md" : "bg-slate-100 text-slate-500 hover:bg-slate-200"}`}
                    >
                        전체보기
                    </button>
                    {availableTags.map(tag => (
                        <button
                            key={tag as string}
                            onClick={() => setSelectedTag(tag as string)}
                            className={`px-4 py-1.5 rounded-full text-[13px] font-bold transition-all border ${selectedTag === tag ? "bg-[#36a4f2]/10 border-[#36a4f2] text-[#36a4f2] shadow-sm" : "bg-white border-slate-200 text-slate-500 hover:border-[#36a4f2]/50 hover:bg-[#36a4f2]/5 hover:text-[#36a4f2]"}`}
                        >
                            {tag as string}
                        </button>
                    ))}
                </div>
            )}

            {/* Kits Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {displayItems.length > 0 ? (
                    displayItems.map((item, index) => (
                        <Card key={`${item.name}-${index}`} className="group hover:border-[#36a4f2] transition-all duration-300 shadow-sm hover:shadow-md cursor-pointer flex flex-col justify-between overflow-hidden" onClick={() => handleItemClick(item)}>
                            <CardContent className="p-0 flex flex-col h-full">
                                <div className="p-6 pb-0">
                                    <div className="flex justify-between items-start mb-4">
                                        <div className="flex items-center gap-2">
                                            <Badge variant="outline" className="text-[10px] font-black text-[#36a4f2] bg-[#36a4f2]/5 border-[#36a4f2]/10 uppercase py-0.5 px-2">
                                                {item.tag || '[실무]'}
                                            </Badge>
                                            {(item.name.includes("근로계약서") || item.name.includes("임대차") || item.name.includes("동업") || item.name.includes("주주") || item.name.includes("정관")) && (
                                                <Badge className="bg-gradient-to-r from-rose-500 to-orange-500 hover:from-rose-600 hover:to-orange-600 border-none px-1.5 py-0 h-4 text-[9px] font-black shadow-sm gap-1">
                                                    <span className="animate-pulse">🔥</span> HOT
                                                </Badge>
                                            )}
                                        </div>
                                        <div className="flex items-center gap-2">
                                            {item.dday && (
                                                <Badge className="bg-orange-500 hover:bg-orange-600 text-[10px] font-bold py-0 h-5">
                                                    {item.dday}
                                                </Badge>
                                            )}
                                            <Badge variant="secondary" className="text-[10px] font-bold text-slate-400 py-0 h-5">
                                                {item.type}
                                            </Badge>
                                            <button
                                                onClick={(e) => toggleBookmark(item, e)}
                                                className={`p-1 -mr-2 rounded-full transition-colors ${bookmarkedItems[item.id ?? item.name] ? 'text-yellow-400 hover:text-yellow-500' : 'text-slate-200 hover:text-yellow-400'}`}
                                            >
                                                <Star className={`w-5 h-5 ${bookmarkedItems[item.id ?? item.name] ? 'fill-current' : ''}`} />
                                            </button>
                                        </div>
                                    </div>
                                    <h4 className="font-bold text-slate-800 mb-2 group-hover:text-[#36a4f2] transition-colors leading-tight min-h-[2.5rem] line-clamp-2">
                                        {item.name}
                                    </h4>
                                    <p className="text-xs text-slate-400 mb-3 line-clamp-2 leading-relaxed">
                                        {item.summary}
                                    </p>
                                    {(() => {
                                        const progress = getKitProgress(item);
                                        if (!progress) return null;
                                        return (
                                            <div className="mb-3 space-y-1.5">
                                                <div className="flex justify-between items-end">
                                                    <span className="text-[10px] font-bold text-slate-500 flex items-center gap-1">
                                                        <CheckSquare className="w-3 h-3 text-emerald-500" /> 필수 체크리스트
                                                    </span>
                                                    <span className={`text-[10px] font-black ${progress.percentage === 100 ? 'text-emerald-500' : 'text-slate-400'}`}>
                                                        {progress.percentage}%
                                                    </span>
                                                </div>
                                                <div className="w-full bg-slate-100 rounded-full h-1.5 overflow-hidden">
                                                    <div
                                                        className={`h-1.5 rounded-full transition-all duration-500 ${progress.percentage === 100 ? 'bg-emerald-500' : 'bg-[#36a4f2]'}`}
                                                        style={{ width: `${progress.percentage}%` }}
                                                    />
                                                </div>
                                            </div>
                                        );
                                    })()}
                                    {item.highlights && item.highlights.length > 0 && (
                                        <div className="flex flex-wrap gap-1 mb-3">
                                            {item.highlights.slice(0, 2).map((hl, i) => (
                                                <span key={hl.id || i} className="text-[10px] font-medium text-amber-700 bg-amber-50 border border-amber-100 px-2 py-0.5 rounded-full truncate max-w-[180px]">
                                                    ⭐ {hl.content}
                                                </span>
                                            ))}
                                            {item.highlights.length > 2 && (
                                                <span className="text-[10px] text-slate-400 font-medium">+{item.highlights.length - 2}개</span>
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
                                        {item.id && (
                                            <Button
                                                size="sm"
                                                className="h-8 rounded-full bg-[#36a4f2] hover:bg-[#258bd1] gap-1.5 px-4"
                                                asChild
                                                onClick={(e) => e.stopPropagation()}
                                            >
                                                <a
                                                    href={`${API_URL}/api/v1/actionkits/items/${item.id}/view`}
                                                    target="_blank"
                                                    rel="noreferrer"
                                                >
                                                    <ExternalLink className="w-3 h-3" />
                                                    <span className="text-[11px] font-bold">문서 보기</span>
                                                </a>
                                            </Button>
                                        )}
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

            {/* Detail View Modal */}
            {(detailItem || previewKit) && (
                <ActionKitDetailModal
                    item={(detailItem || previewKit)!}
                    onClose={() => { setDetailItem(null); setPreviewKit(null); }}
                    onNavigateToLaw={onNavigateToLaw}
                    onToggleBookmark={toggleBookmark}
                    isBookmarked={!!bookmarkedItems[(detailItem || previewKit)?.id ?? (detailItem || previewKit)?.name ?? '']}
                    checkedItems={checkedItems}
                    onToggleChecklist={toggleChecklist}
                    getKitProgress={getKitProgress}
                />
            )}

            {/* Bookmark Drawer */}
            {isDrawerOpen && (
                <div className="fixed inset-0 z-50 flex mb-0 bg-slate-900/40 backdrop-blur-sm justify-end">
                    <div className="w-full max-w-sm h-full bg-white shadow-2xl animate-in slide-in-from-right duration-300 flex flex-col">
                        <div className="p-4 border-b border-slate-100 flex justify-between items-center bg-yellow-50/50">
                            <h3 className="font-bold flex items-center gap-2 text-slate-800">
                                <Star className="w-5 h-5 fill-yellow-400 text-yellow-500" />
                                나만의 서랍장
                            </h3>
                            <button onClick={() => setIsDrawerOpen(false)} className="p-2 text-slate-400 hover:text-slate-600 rounded-full hover:bg-slate-100">
                                <X className="w-5 h-5" />
                            </button>
                        </div>
                        <div className="flex-1 overflow-y-auto p-4 space-y-3">
                            {Object.values(bookmarkedItems).length === 0 ? (
                                <div className="py-20 text-center text-slate-400">
                                    <Star className="w-12 h-12 mx-auto mb-4 opacity-20" />
                                    <p className="text-sm font-bold">서랍장이 비어있습니다.</p>
                                    <p className="text-xs mt-2">필요한 키트에 ⭐️ 별을 눌러 담아보세요.</p>
                                </div>
                            ) : (
                                Object.values(bookmarkedItems).map((item, i) => (
                                    <div key={i} className="flex gap-3 bg-white border border-slate-100 p-3 rounded-xl shadow-sm relative group pr-10">
                                        <div className="w-8 h-8 rounded bg-slate-50 border border-slate-100 flex items-center justify-center flex-shrink-0">
                                            <FolderOpen className="w-4 h-4 text-slate-400" />
                                        </div>
                                        <div>
                                            <h4 className="font-bold text-sm text-slate-800 line-clamp-1">{item.name}</h4>
                                            <p className="text-[10px] text-slate-500 mt-1 line-clamp-1">{item.summary}</p>
                                        </div>
                                        <button
                                            onClick={(e) => toggleBookmark(item, e)}
                                            className="absolute right-3 top-1/2 -translate-y-1/2 p-2 text-slate-300 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity"
                                        >
                                            <Trash2 className="w-4 h-4" />
                                        </button>
                                    </div>
                                ))
                            )}
                        </div>
                        {Object.values(bookmarkedItems).length > 0 && (
                            <div className="p-4 border-t border-slate-100 bg-slate-50">
                                <Button
                                    className="w-full bg-[#36a4f2] hover:bg-[#258bd1] text-white font-bold h-12 rounded-xl"
                                    onClick={handleBulkDownload}
                                    disabled={isZipping}
                                >
                                    {isZipping ? '압축하는 중...' : `${Object.keys(bookmarkedItems).length}개 한 번에 ZIP 다운로드`}
                                </Button>
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* Onboarding Modal */}
            {isOnboardingOpen && (
                <div className="fixed inset-0 z-[60] flex items-center justify-center bg-slate-900/40 backdrop-blur-sm p-4">
                    <div className="bg-white rounded-3xl w-full max-w-lg shadow-2xl overflow-hidden animate-in zoom-in-95 duration-300">
                        {/* Header */}
                        <div className="p-6 pb-0 flex justify-between items-start">
                            <div className="pr-8">
                                <h3 className="text-xl md:text-2xl font-bold text-slate-800 tracking-tight leading-tight">
                                    {onboardingStep === 1 ? "대표님, 지금 가장 고민되시는 단계가 어디인가요?" : "대표님을 위한 맞춤 스타터 팩이 준비되었습니다!"}
                                </h3>
                                <p className="text-slate-500 text-sm mt-2">
                                    {onboardingStep === 1
                                        ? "현재 상황에 꼭 맞는 필수 서류 세트를 즉시 추천해 드릴게요."
                                        : "버튼 한 번만 누르면 내 서랍장에 쏙! 일괄 다운로드도 가능합니다."}
                                </p>
                            </div>
                            <button onClick={handleOnboardingSkip} className="p-2 -my-2 -mx-2 text-slate-400 hover:text-slate-600 rounded-full hover:bg-slate-100 transition-colors shrink-0">
                                <X className="w-5 h-5" />
                            </button>
                        </div>

                        {/* Content */}
                        <div className="p-6">
                            {onboardingStep === 1 ? (
                                <div className="space-y-3">
                                    {STARTER_PACKS.map(pack => (
                                        <button
                                            key={pack.id}
                                            onClick={() => {
                                                setSelectedPackId(pack.id);
                                                setOnboardingStep(2);
                                            }}
                                            className={`w-full text-left p-4 rounded-2xl border-2 transition-all group flex items-center gap-4 ${selectedPackId === pack.id
                                                ? 'border-[#36a4f2] bg-[#36a4f2]/5 shadow-sm'
                                                : 'border-slate-100 hover:border-[#36a4f2]/30 hover:bg-slate-50'
                                                }`}
                                        >
                                            <div className={`w-12 h-12 rounded-xl flex items-center justify-center shrink-0 ${pack.bg} ${pack.color}`}>
                                                <pack.icon className="w-6 h-6" />
                                            </div>
                                            <div>
                                                <h4 className="font-bold text-slate-800 text-lg group-hover:text-[#36a4f2] transition-colors">{pack.title}</h4>
                                                <p className="text-xs text-slate-500 mt-1 line-clamp-1">포함 서류: {pack.keywords.join(', ')} 등</p>
                                            </div>
                                        </button>
                                    ))}
                                    <button
                                        onClick={handleOnboardingSkip}
                                        className="w-full text-center p-4 rounded-2xl border-2 border-transparent text-slate-400 hover:text-slate-600 hover:bg-slate-50 transition-colors text-sm font-medium mt-2"
                                    >
                                        ⚖️ 기타 / 나중에 혼자 둘러볼래요 (스킵)
                                    </button>
                                </div>
                            ) : (
                                <div className="space-y-6">
                                    {(() => {
                                        const pack = STARTER_PACKS.find(p => p.id === selectedPackId);
                                        if (!pack) return null;
                                        return (
                                            <div className="flex flex-col items-center py-6 text-center">
                                                <div className={`w-20 h-20 rounded-2xl flex items-center justify-center mb-4 ${pack.bg} ${pack.color}`}>
                                                    <pack.icon className="w-10 h-10" />
                                                </div>
                                                <h4 className="text-xl font-bold text-slate-800">
                                                    <span className={pack.color}>{pack.title}</span> 증정
                                                </h4>
                                                <div className="flex flex-wrap justify-center gap-2 mt-4">
                                                    {pack.keywords.map((kw, i) => (
                                                        <Badge key={i} variant="outline" className="bg-slate-50 border-slate-200 text-slate-600 font-medium">
                                                            {kw}
                                                        </Badge>
                                                    ))}
                                                </div>
                                            </div>
                                        );
                                    })()}
                                    <Button
                                        onClick={handleAddPackToDrawer}
                                        className="w-full h-14 rounded-2xl bg-[#36a4f2] hover:bg-[#258bd1] text-white font-bold text-lg shadow-lg shadow-[#36a4f2]/20 gap-2"
                                    >
                                        <Star className="w-5 h-5 fill-white" />
                                        내 서랍장에 모두 담기
                                    </Button>
                                    <button
                                        onClick={() => setOnboardingStep(1)}
                                        className="w-full text-center text-sm text-slate-400 hover:text-slate-600 underline underline-offset-4"
                                    >
                                        이전으로 돌아가기
                                    </button>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}

            {/* Disclaimer */}
            <div className="mt-16 bg-slate-50/50 rounded-2xl p-6 md:p-8 border border-slate-100">
                <h5 className="text-xs font-bold text-slate-500 mb-3 tracking-tight">법적 면책 조항 (Disclaimer)</h5>
                <p className="text-[11px] leading-relaxed text-slate-400 break-keep">
                    본 조사자료는 고객의 창업에 정보를 제공할 목적으로 작성되었으며, 어떠한 경우에도 무단 복제 및 배포 될 수 없습니다.<br />
                    또한 본 자료에 수록된 내용은 당사가 신뢰할 만한 자료 및 정보로 얻어진 것이나, 그 정확성이나 완전성을 보장할 수 없으므로
                    창업자 자신의 판단과 책임하에 최종결정을 하시기 바랍니다.<br />
                    <span className="text-slate-500 font-medium mt-1 inline-block">따라서 어떠한 경우에도 본 자료는 고객의 창업의 결과에 대한 법적 책임소재의 증빙자료로 사용될 수 없습니다.</span>
                </p>
            </div>
        </div>
    );
};
