import { FolderOpen, Users, Download } from 'lucide-react';

export const StatsGrid = () => {
    return (
        <div className="flex flex-col gap-6">
            {/* Action Kit Card - Stitch Style */}
            <div className="bg-blue-50/80 rounded-3xl p-6 border border-blue-100/50 flex flex-col justify-between h-48 relative overflow-hidden group transition-all hover:shadow-md hover:border-blue-200">
                <div className="absolute top-0 right-0 w-24 h-24 bg-gradient-to-br from-white/60 to-transparent rounded-bl-[3rem] transition-transform duration-500 group-hover:scale-110" />

                <div>
                    <div className="w-12 h-12 rounded-2xl bg-white shadow-sm flex items-center justify-center mb-4 text-primary group-hover:scale-110 transition-transform duration-300">
                        <FolderOpen className="w-6 h-6" />
                    </div>
                    <h3 className="font-bold text-slate-900 text-base mb-1 tracking-tight">액션 키트 (Action Kit)</h3>
                    <p className="text-xs text-slate-500 font-medium">1단계 필수 행정 서류 묶음</p>
                </div>

                <button className="text-xs font-bold text-primary flex items-center mt-auto group/btn bg-white/50 w-fit px-3 py-2 rounded-xl hover:bg-white transition-colors">
                    다운로드
                    <Download className="w-3.5 h-3.5 ml-1.5 transition-transform group-hover/btn:translate-y-0.5" />
                </button>
            </div>

            {/* Community Notification - Stitch Style */}
            <div className="bg-white rounded-3xl p-6 shadow-sm border border-slate-100 flex items-center gap-5 transition-all hover:shadow-md">
                <div className="w-12 h-12 rounded-full bg-orange-50 flex items-center justify-center text-orange-500 shrink-0">
                    <Users className="w-6 h-6" />
                </div>
                <p className="text-xs text-slate-600 font-bold leading-relaxed">
                    오늘 <span className="text-orange-500">3명</span>의 동료 창업자가<br />이 단계를 완료했습니다!
                </p>
            </div>
        </div>
    );
};
