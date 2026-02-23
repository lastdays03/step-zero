"use client";

import React, { useState } from 'react';
import { useActionKit } from '../hooks/useActionKit';
import { Disclaimer } from '@/components/ui/Disclaimer';
import { ActionKitItem, RelatedLaw } from '../types';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
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
    LucideIcon,
    CheckSquare,
    Package,
    Users,
    Building,
} from 'lucide-react';

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

const STARTER_PACKS = [
    {
        id: "employee-onboarding",
        title: "직원 채용 필수 팩",
        icon: Users,
        color: "bg-blue-50 text-blue-600 border-blue-200",
        keywords: ["근로계약서", "보안서약서", "개인정보 이용 동의서"]
    },
    {
        id: "office-setup",
        title: "사무실 계약 팩",
        icon: Building,
        color: "bg-amber-50 text-amber-600 border-amber-200",
        keywords: ["임대차", "전대차"]
    },
    {
        id: "investment-prep",
        title: "투자 유치 준비 팩",
        icon: Package,
        color: "bg-purple-50 text-purple-600 border-purple-200",
        keywords: ["주주명부", "정관", "투자"]
    }
];

const isRelatedLawObject = (law: string | RelatedLaw): law is RelatedLaw => {
    return typeof law === "object" && law !== null && "name" in law;
};

const LawSnippetTag = ({
    law,
    onClick
}: {
    law: string | RelatedLaw,
    onClick: (e: React.MouseEvent, name: string) => void
}) => {
    const [isHovered, setIsHovered] = useState(false);
    const name = isRelatedLawObject(law) ? law.name : law;
    const summary = isRelatedLawObject(law) ? law.summary : null;
    const snippet = isRelatedLawObject(law) ? law.snippet : null;

    return (
        <div
            className="relative group/law-tag"
            onMouseEnter={() => setIsHovered(true)}
            onMouseLeave={() => setIsHovered(false)}
        >
            <div
                className="flex flex-wrap items-center gap-1.5 cursor-pointer"
                onClick={(e) => onClick(e, name)}
            >
                <span className="text-[10px] font-bold text-[#36a4f2] bg-[#36a4f2]/5 px-1.5 py-0.5 rounded border border-[#36a4f2]/10 transition-colors group-hover/law-tag:bg-[#36a4f2]/20 group-hover/law-tag:border-[#36a4f2]/30">
                    #{name}
                </span>
                {summary && (
                    <span className="text-[10px] text-slate-500 line-clamp-1 flex-1 transition-colors group-hover/law-tag:text-slate-700">
                        {summary}
                    </span>
                )}
            </div>

            {isHovered && snippet && (
                <div className="absolute bottom-full left-0 mb-3 z-50 w-72 p-4 bg-white/95 backdrop-blur-md rounded-2xl shadow-2xl border border-[#36a4f2]/10 animate-in fade-in slide-in-from-bottom-2 duration-200 pointer-events-none">
                    <div className="absolute -bottom-1.5 left-6 w-3 h-3 bg-white border-r border-b border-[#36a4f2]/10 rotate-45" />
                    <div className="flex items-center gap-2 mb-2">
                        <div className="w-6 h-6 rounded-lg bg-[#36a4f2]/10 flex items-center justify-center">
                            <Gavel className="w-3.5 h-3.5 text-[#36a4f2]" />
                        </div>
                        <span className="text-[11px] font-black text-slate-800">{name} 핵심 요약</span>
                    </div>
                    <p className="text-[10px] text-slate-600 leading-relaxed break-keep font-medium">
                        {snippet}
                    </p>
                    <div className="mt-3 pt-2 border-t border-slate-50 text-[10px] text-[#36a4f2] font-black flex items-center gap-1 capitalize tracking-tighter">
                        CLICK TO VIEW FULL GUIDE <Search className="w-2.5 h-2.5" />
                    </div>
                </div>
            )}
        </div>
    );
};

interface ActionKitLibraryViewProps {
    onNavigateToLaw?: (lawTitle: string) => void;
}

export const ActionKitLibraryView = ({ onNavigateToLaw }: ActionKitLibraryViewProps) => {
    const { data, loading, error } = useActionKit();
    const [selectedCategory, setSelectedCategory] = useState<string>("all");
    const [searchQuery, setSearchQuery] = useState("");
    const [activeStarterPack, setActiveStarterPack] = useState<string | null>(null);
    const [previewItem, setPreviewItem] = useState<ActionKitItem | null>(null);

    const handleLawClick = (e: React.MouseEvent, lawName: string) => {
        e.stopPropagation();
        if (onNavigateToLaw) {
            onNavigateToLaw(lawName);
        }
    };

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
        cat.items.map(item => ({
            ...item,
            categoryTitle: cat.title,
            relatedLaws: item.relatedLaws?.map(law => {
                const name = isRelatedLawObject(law) ? law.name : law;
                // Demo snippet for a specific law
                if (name === "근로기준법 제17조") {
                    return {
                        name,
                        summary: "근로조건의 명시",
                        snippet: "사용자는 근로계약을 체결할 때 근로자에게 임금, 소정근로시간, 휴일, 연차 유급휴가 등을 명시해야 하며, 근로자에게 서면으로 교부해야 합니다."
                    };
                }
                if (name === "상가건물 임대차보호법 제10조") {
                    return {
                        name,
                        summary: "계약갱신 요구 등",
                        snippet: "임차인이 임대차기간이 만료되기 6개월 전부터 1개월 전까지 사이에 계약갱신을 요구할 경우 임대인은 정당한 사유 없이 거절하지 못합니다."
                    };
                }
                if (name === "상법 제170조") {
                    return {
                        name,
                        summary: "회사의 정관",
                        snippet: "회사를 설립함에는 발기인이 정관을 작성하여 각 발기인이 이에 기명날인 또는 서명하여야 합니다. 이는 회사의 헌법과 같은 역할을 합니다."
                    };
                }
                return law;
            }),
            complianceChecklist: item.name.includes("근로계약서") ? [
                "임금(기본급, 수당 등) 구성항목 및 계산방법 명시 여부",
                "소정근로시간 및 휴게시간 명시 여부",
                "휴일(주휴일 등) 및 연차 유급휴가 확인",
                "근로계약서 2부 작성 후 근로자에게 1부 교부 완료 여부"
            ] : undefined
        }))
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
                        onChange={(e) => {
                            setSearchQuery(e.target.value);
                            if (activeStarterPack) setActiveStarterPack(null);
                        }}
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

            {/* Starter Packs (Only show if not searching and category is 'all') */}
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
                                        : `${pack.color} hover:shadow-md bg-white`
                                        }`}
                                >
                                    <div>
                                        <div className={`w-8 h-8 rounded-lg mb-3 flex items-center justify-center ${isActive ? 'bg-white/20' : 'bg-white shadow-sm'}`}>
                                            <PIcon className={`w-4 h-4 ${isActive ? 'text-white' : ''}`} />
                                        </div>
                                        <h4 className={`font-bold text-sm mb-1 ${isActive ? 'text-white' : 'text-slate-900'}`}>{pack.title}</h4>
                                        <p className={`text-[10px] line-clamp-1 ${isActive ? 'text-slate-300' : 'text-slate-500'}`}>
                                            {pack.keywords.join(', ')} 포함
                                        </p>
                                    </div>
                                    <div className={`w-6 h-6 rounded-full flex items-center justify-center border transition-colors ${isActive ? 'border-[#36a4f2] bg-[#36a4f2]' : 'border-slate-200 group-hover:bg-white'
                                        }`}>
                                        <CheckSquare className={`w-3 h-3 ${isActive ? 'text-white' : 'text-transparent'}`} />
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
                        <Card
                            key={`${item.name}-${index}`}
                            className="group hover:border-[#36a4f2] transition-all duration-300 shadow-sm hover:shadow-md cursor-pointer flex flex-col justify-between overflow-hidden"
                            onClick={() => setPreviewItem(item)}
                        >
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
                                                    {item.relatedLaws.map((law, i) => (
                                                        <LawSnippetTag
                                                            key={i}
                                                            law={law}
                                                            onClick={handleLawClick}
                                                        />
                                                    ))}
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

            <Dialog open={!!previewItem} onOpenChange={(open) => !open && setPreviewItem(null)}>
                <DialogContent className="max-w-4xl w-full p-0 overflow-hidden bg-white/95 backdrop-blur-xl border-white/20">
                    {previewItem && (
                        <div className="flex flex-col md:flex-row h-full max-h-[85vh]">
                            {/* Left Side: Visual Preview */}
                            <div className="w-full md:w-1/2 bg-slate-50 p-8 flex flex-col items-center justify-center border-r border-slate-100 relative">
                                <div className="absolute inset-0 bg-gradient-to-br from-[#36a4f2]/5 to-transparent pointer-events-none" />
                                <div className="relative z-10 w-full aspect-[1/1.4] max-w-sm bg-white rounded-xl shadow-xl overflow-hidden flex items-center justify-center border border-slate-200">
                                    <div className="text-center p-6 bg-slate-50/50 w-full h-full flex flex-col items-center justify-center">
                                        <FolderOpen className="w-16 h-16 text-slate-300 mb-4" />
                                        <p className="text-sm font-bold text-slate-500 mb-2">프리뷰 이미지가 제공되지 않았습니다.</p>
                                        <p className="text-xs text-slate-400">파일을 다운로드하여 확인해 주세요.</p>
                                    </div>
                                </div>
                            </div>

                            {/* Right Side: Information & Action */}
                            <div className="w-full md:w-1/2 p-8 flex flex-col h-full overflow-y-auto">
                                <DialogHeader className="mb-6">
                                    <div className="flex items-center gap-2 mb-3">
                                        <Badge variant="outline" className="text-[10px] font-black text-[#36a4f2] bg-[#36a4f2]/5 border-[#36a4f2]/10 uppercase py-0.5 px-2">
                                            {previewItem.tag || '[실무]'}
                                        </Badge>
                                        <Badge variant="secondary" className="text-[10px] font-bold text-slate-400 py-0 h-5 mt-0">
                                            {previewItem.type}
                                        </Badge>
                                        {previewItem.dday && (
                                            <Badge className="bg-orange-500 hover:bg-orange-600 text-[10px] font-bold py-0 h-5 mt-0">
                                                {previewItem.dday}
                                            </Badge>
                                        )}
                                    </div>
                                    <DialogTitle className="text-2xl font-bold text-slate-800 leading-tight">
                                        {previewItem.name}
                                    </DialogTitle>
                                    <DialogDescription className="text-sm text-slate-500 mt-2 leading-relaxed">
                                        {previewItem.summary}
                                    </DialogDescription>
                                </DialogHeader>

                                <div className="space-y-6 flex-1">
                                    <div className="p-4 bg-[#36a4f2]/5 rounded-xl border border-[#36a4f2]/10">
                                        <h4 className="flex items-center gap-2 text-sm font-bold text-slate-700 mb-3">
                                            <Sparkles className="w-4 h-4 text-[#36a4f2]" />
                                            💡 사용 팁 (How to Use)
                                        </h4>
                                        <ul className="space-y-2 text-xs text-slate-600">
                                            {previewItem.usageTips ? (
                                                previewItem.usageTips.map((tip, i) => (
                                                    <li key={i} className="flex gap-2"  >
                                                        <span className="text-[#36a4f2] font-bold">{i + 1}.</span> {tip}
                                                    </li>
                                                ))
                                            ) : (
                                                <>
                                                    <li className="flex gap-2"><span className="text-[#36a4f2] font-bold">1.</span> 다운로드 버튼을 눌러 파일을 저장합니다.</li>
                                                    <li className="flex gap-2"><span className="text-[#36a4f2] font-bold">2.</span> 파일 내 빈칸(노란색 셀 또는 괄호)을 양식에 맞게 입력합니다.</li>
                                                    <li className="flex gap-2"><span className="text-[#36a4f2] font-bold">3.</span> 작성 완료 후, 필요한 곳에 즉시 활용하세요.</li>
                                                </>
                                            )}
                                        </ul>
                                    </div>

                                    {/* Compliance Checklist */}
                                    {previewItem.complianceChecklist && previewItem.complianceChecklist.length > 0 && (
                                        <div className="p-4 bg-amber-50 rounded-xl border border-amber-200">
                                            <h4 className="flex items-center gap-2 text-sm font-bold text-amber-700 mb-3">
                                                <CheckSquare className="w-4 h-4" />
                                                법적 필수 확인 사항 (Checklist)
                                            </h4>
                                            <div className="space-y-2">
                                                {previewItem.complianceChecklist.map((task, i) => (
                                                    <label key={i} className="flex items-start gap-3 p-2 bg-white rounded-lg border border-amber-100 hover:border-amber-300 transition-colors cursor-pointer group/check">
                                                        <div className="relative flex items-start justify-center pt-0.5">
                                                            <input type="checkbox" className="peer appearance-none w-4 h-4 border-2 border-slate-300 rounded cursor-pointer checked:bg-amber-500 checked:border-amber-500 transition-all" />
                                                            <CheckSquare className="w-3 h-3 text-white absolute top-1 pointer-events-none opacity-0 peer-checked:opacity-100" />
                                                        </div>
                                                        <span className="text-xs text-slate-700 font-medium peer-checked:text-slate-400 peer-checked:line-through transition-all select-none">
                                                            {task}
                                                        </span>
                                                    </label>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    {previewItem.relatedLaws && previewItem.relatedLaws.length > 0 && (
                                        <div className="space-y-3">
                                            <h4 className="flex items-center gap-2 text-sm font-bold text-slate-700">
                                                <Gavel className="w-4 h-4 text-[#36a4f2]" />
                                                관련 법령 가이드
                                            </h4>
                                            <div className="flex flex-wrap gap-2">
                                                {previewItem.relatedLaws.map((law, i) => (
                                                    <LawSnippetTag
                                                        key={i}
                                                        law={law}
                                                        onClick={(e, name) => {
                                                            handleLawClick(e, name);
                                                            setPreviewItem(null);
                                                        }}
                                                    />
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                </div>

                                <div className="pt-6 mt-6 border-t border-slate-100">
                                    <Button
                                        size="lg"
                                        className="w-full rounded-xl bg-[#36a4f2] hover:bg-[#258bd1] text-white shadow-lg shadow-[#36a4f2]/25 font-bold h-14 text-base"
                                        onClick={() => {
                                            handleDownload(previewItem.path, previewItem.name);
                                            setPreviewItem(null); // 모달 닫기
                                        }}
                                    >
                                        <Download className="w-5 h-5 mr-2" />
                                        파일 다운로드 ({previewItem.type})
                                    </Button>
                                    <p className="text-[11px] text-slate-400 text-center mt-3">
                                        다운로드 시 <span className="font-semibold text-slate-500">Disclaimer(면책조항)</span>에 동의한 것으로 간주됩니다.
                                    </p>
                                </div>
                            </div>
                        </div>
                    )}
                </DialogContent>
            </Dialog>

            <Disclaimer />
        </div>
    );
};
