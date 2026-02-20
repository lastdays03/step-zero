"use client";

import React, { useState } from 'react';
import { LawGuideView } from './LawGuideView';
import { ActionKitLibraryView } from './ActionKitLibraryView';
import { cn } from "@/lib/utils";
import { Gavel, FolderOpen } from 'lucide-react';

export const ActionKitContainer = () => {
    const [activeTab, setActiveTab] = useState<'laws' | 'kits'>('laws');

    return (
        <div className="p-8 pb-32">
            {/* Tab Header */}
            <div className="flex p-1 bg-slate-100 rounded-2xl w-full max-w-md mx-auto mb-12 shadow-inner">
                <button
                    onClick={() => setActiveTab('laws')}
                    className={cn(
                        "flex items-center justify-center gap-2 flex-1 py-3 px-4 rounded-xl text-sm font-bold transition-all",
                        activeTab === 'laws'
                            ? "bg-white text-[#36a4f2] shadow-sm"
                            : "text-slate-500 hover:text-slate-700"
                    )}
                >
                    <Gavel className="w-4 h-4" />
                    창업 법령 가이드
                </button>
                <button
                    onClick={() => setActiveTab('kits')}
                    className={cn(
                        "flex items-center justify-center gap-2 flex-1 py-3 px-4 rounded-xl text-sm font-bold transition-all",
                        activeTab === 'kits'
                            ? "bg-white text-[#36a4f2] shadow-sm"
                            : "text-slate-500 hover:text-slate-700"
                    )}
                >
                    <FolderOpen className="w-4 h-4" />
                    액션 키트 라이브러리
                </button>
            </div>

            {/* View Content */}
            <div className="max-w-7xl mx-auto">
                {activeTab === 'laws' ? <LawGuideView /> : <ActionKitLibraryView />}
            </div>
        </div>
    );
};
