"use client";

import React from 'react';
import { Card, CardContent } from "@/components/ui/card";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";

interface GrowthClubCardProps {
    onlineCount: number;
}

export const GrowthClubCard = ({ onlineCount }: GrowthClubCardProps) => {
    return (
        <Card className="bg-slate-900 rounded-3xl shadow-sm text-white relative overflow-hidden group h-full transition-all hover:shadow-lg hover:shadow-slate-900/20 border-none">
            <CardContent className="p-6 h-full flex flex-col justify-between">
                {/* Content Left */}
                <div className="space-y-3 z-10">
                    <div className="flex items-center space-x-2">
                        <span className="relative flex h-2 w-2">
                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                            <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                        </span>
                        <Badge variant="outline" className="text-[10px] font-bold text-slate-400 uppercase tracking-widest border-slate-700/50 hover:bg-transparent">
                            LIVE: GROWTH CLUB
                        </Badge>
                    </div>
                    <p className="text-base font-bold leading-snug tracking-tight text-white">
                        {onlineCount}명의 동료 창업자와<br />실시간으로 소통하기
                    </p>
                </div>

                {/* Avatar Pile Right */}
                <div className="flex -space-x-3 relative z-10 mr-2">
                    <Avatar className="w-10 h-10 border-2 border-slate-900 shadow-sm transition-transform hover:z-20 hover:scale-110">
                        <AvatarImage src={`https://api.dicebear.com/7.x/avataaars/svg?seed=A`} />
                        <AvatarFallback className="bg-pink-500 text-white text-xs font-bold">A</AvatarFallback>
                    </Avatar>
                    <Avatar className="w-10 h-10 border-2 border-slate-900 shadow-sm transition-transform hover:z-20 hover:scale-110">
                        <AvatarImage src={`https://api.dicebear.com/7.x/avataaars/svg?seed=B`} />
                        <AvatarFallback className="bg-sky-400 text-white text-xs font-bold">B</AvatarFallback>
                    </Avatar>
                    <Avatar className="w-10 h-10 border-2 border-slate-900 shadow-sm transition-transform hover:z-20 hover:scale-110">
                        <AvatarFallback className="bg-primary text-white text-[10px] font-bold">+{onlineCount}</AvatarFallback>
                    </Avatar>
                </div>
            </CardContent>
        </Card>
    );
};
