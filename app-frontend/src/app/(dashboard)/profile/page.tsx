"use client";

import React, { useState, useEffect, useRef } from "react";
import {
    Camera,
    Plus,
    X,
    Save,
    RotateCcw,
    CheckCircle2,
    AlertCircle,
    LayoutGrid,
    MapPin,
    Quote,
    Briefcase,
    Trophy,
    Award,
    Pencil
} from "lucide-react";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { getMyProfile, updateMyProfile, uploadProfileImage } from "@/features/profile/api";
import { UserProfile, UserProfileUpdate } from "@/features/profile/types";
import { useAuth } from "@/providers/AuthProvider";

export default function ProfilePage() {
    const { user: authUser, updateUser } = useAuth();
    const fileInputRef = useRef<HTMLInputElement>(null);
    const [profile, setProfile] = useState<UserProfile | null>(null);
    const [formData, setFormData] = useState<UserProfileUpdate>({});
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [currentTime, setCurrentTime] = useState(new Date());
    const [isAutoFilled, setIsAutoFilled] = useState(false);
    const apiHost = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/$/, "");

    useEffect(() => {
        const timer = setInterval(() => {
            setCurrentTime(new Date());
        }, 1000 * 60); // 1분마다 업데이트 (최적화)
        return () => clearInterval(timer);
    }, []);

    const formatDateTime = (date: Date) => {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        return `${year}-${month}-${day}-${hours}:${minutes}`;
    };

    useEffect(() => {
        fetchProfile();
    }, []);

    const fetchProfile = async () => {
        try {
            setLoading(true);
            const data = await getMyProfile();
            setProfile(data);

            // Check if backend auto-filled these fields (they would come from roadmap)
            // It's a heuristic: we assume if they are filled on first fetch but user never explicitly saved them, it might be auto-filled.
            // A more robust way is for the backend to flag it, but for UX, just showing the hint if they exist is helpful.
            // Since we can't perfectly know if it's auto-filled vs previously saved just from the payload,
            // we will show the hint if category and region have values.
            if (data.category || data.region) {
                setIsAutoFilled(true);
            }

            setFormData({
                nickname: data.nickname || "",
                full_name: data.full_name || "",
                is_public: data.is_public,
                category: data.category || "",
                region: data.region || "",
                philosophy: data.philosophy || "",
                experiences: data.experiences || [],
                awards: data.awards || [],
                certificates: data.certificates || [],
            });
        } catch (err) {
            console.error("Failed to fetch profile:", err);
            setError("프로필을 불러오는 데 실패했습니다.");
        } finally {
            setLoading(false);
        }
    };

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleTogglePublic = async () => {
        if (!profile) return;
        const newValue = !formData.is_public;
        setFormData(prev => ({ ...prev, is_public: newValue }));

        // Immediate save for toggle as per requirements
        try {
            await updateMyProfile({ is_public: newValue });
            setError(null);
        } catch (err) {
            console.error("Failed to update visibility:", err);
            setError("프로필 공개 설정 업데이트에 실패했습니다.");
            // Revert local state on failure
            setFormData(prev => ({ ...prev, is_public: !newValue }));
        }
    };

    const handleListChange = (key: 'experiences' | 'awards' | 'certificates', index: number, value: string) => {
        setFormData(prev => {
            const newList = [...(prev[key] || [])];
            newList[index] = value;
            return { ...prev, [key]: newList };
        });
    };

    const addListItem = (key: 'experiences' | 'awards' | 'certificates') => {
        setFormData(prev => ({
            ...prev,
            [key]: [...(prev[key] || []), ""]
        }));
    };

    const removeListItem = (key: 'experiences' | 'awards' | 'certificates', index: number) => {
        setFormData(prev => ({
            ...prev,
            [key]: (prev[key] || []).filter((_, i) => i !== index)
        }));
    };

    const handleSave = async () => {
        try {
            setSaving(true);
            const updated = await updateMyProfile(formData);
            setProfile(updated);

            // 전역 인증 상태의 사용자 정보 즉시 업데이트
            if (authUser) {
                updateUser({
                    full_name: updated.full_name ?? undefined,
                    username: updated.full_name || authUser.username
                });
            }

            // 최근 수정일 시계 즉시 업데이트
            setCurrentTime(new Date());

            setError(null);
            alert("프로필이 성공적으로 저장되었습니다.");
        } catch (err) {
            console.error("Failed to save profile:", err);
            setError("저장 중 오류가 발생했습니다.");
        } finally {
            setSaving(false);
        }
    };

    const handleImageClick = () => {
        fileInputRef.current?.click();
    };

    const handleImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        try {
            setSaving(true);
            const updated = await uploadProfileImage(file);
            setProfile(updated);

            // 이미지 업로드 후 전역 상태 동기화 (필요한 경우)
            if (authUser) {
                updateUser({
                    full_name: updated.full_name ?? undefined,
                    username: updated.full_name || authUser.username
                });
            }

            setError(null);
        } catch (err) {
            console.error("Failed to upload image:", err);
            setError("이미지 업로드에 실패했습니다.");
        } finally {
            setSaving(false);
        }
    };

    const handleCancel = () => {
        if (profile) {
            setFormData({
                nickname: profile.nickname || "",
                full_name: profile.full_name || "",
                is_public: profile.is_public,
                category: profile.category || "",
                region: profile.region || "",
                philosophy: profile.philosophy || "",
                experiences: profile.experiences || [],
                awards: profile.awards || [],
                certificates: profile.certificates || [],
            });
        }
    };

    if (loading) {
        return <div className="flex h-[400px] items-center justify-center">Loading...</div>;
    }

    return (
        <div className="mx-auto max-w-4xl space-y-8 p-4 pb-20 md:p-8">
            {/* Header Section */}
            <Card className="overflow-hidden border-none bg-gradient-to-r from-slate-900 to-slate-800 text-white shadow-xl">
                <CardContent className="p-8">
                    <div className="flex flex-col items-center gap-8 md:flex-row md:items-start">
                        <div className="relative group">
                            <input
                                type="file"
                                ref={fileInputRef}
                                onChange={handleImageUpload}
                                className="hidden"
                                accept="image/*"
                            />
                            <Avatar className="h-24 w-24 border-4 border-slate-700 shadow-2xl transition-transform group-hover:scale-105 md:h-32 md:w-32">
                                <AvatarImage src={profile?.profile_img ? `${apiHost}/api/uploads/${profile.profile_img}` : ""} />
                                <AvatarFallback className="bg-slate-700 text-2xl font-bold">{profile?.full_name?.[0]}</AvatarFallback>
                            </Avatar>
                            <button
                                onClick={handleImageClick}
                                className="absolute bottom-0 right-0 rounded-full bg-blue-600 p-2 text-white shadow-lg transition-colors hover:bg-blue-500"
                            >
                                <Camera size={18} />
                            </button>
                        </div>

                        <div className="flex-1 space-y-4 text-center md:text-left">
                            <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
                                <div>
                                    <div className="flex items-center gap-2">
                                        <div className="relative group/input">
                                            <input
                                                name="full_name"
                                                value={formData.full_name ?? ""}
                                                onChange={handleInputChange}
                                                placeholder="성함을 입력하세요"
                                                className="bg-transparent text-3xl font-bold tracking-tight outline-none border-b border-transparent hover:border-slate-600 focus:border-blue-500 focus:ring-4 focus:ring-blue-500/20 transition-all w-48 pr-8"
                                            />
                                            <Pencil size={16} className="absolute right-2 top-1/2 -translate-y-1/2 text-white/50 opacity-0 group-hover/input:opacity-100 transition-opacity pointer-events-none" />
                                        </div>
                                        <h1 className="text-3xl font-bold tracking-tight">사장님</h1>
                                    </div>
                                    <div className="relative group/input mt-1 w-fit">
                                        <input
                                            name="nickname"
                                            value={formData.nickname ?? ""}
                                            onChange={handleInputChange}
                                            placeholder="닉네임을 입력해 주세요"
                                            className="bg-transparent text-slate-300 outline-none border-b border-transparent hover:border-slate-600 focus:border-blue-500 focus:ring-4 focus:ring-blue-500/20 transition-all text-lg pr-8"
                                        />
                                        <Pencil size={14} className="absolute right-2 top-1/2 -translate-y-1/2 text-white/50 opacity-0 group-hover/input:opacity-100 transition-opacity pointer-events-none" />
                                    </div>
                                    {profile?.email && (
                                        <p className="mt-1 text-sm text-slate-400 font-medium">{profile.email}</p>
                                    )}
                                </div>

                                <div className="flex items-center justify-center gap-3 rounded-full bg-slate-800/50 px-4 py-2 ring-1 ring-slate-700">
                                    <span className="text-sm font-medium text-slate-400">프로필 공개</span>
                                    <button
                                        onClick={handleTogglePublic}
                                        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none ${formData.is_public ? 'bg-green-500' : 'bg-slate-600'}`}
                                    >
                                        <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${formData.is_public ? 'translate-x-6' : 'translate-x-1'}`} />
                                    </button>
                                </div>
                            </div>

                            <div className="space-y-2">
                                <div className="flex justify-between text-sm font-medium">
                                    <span className="text-slate-400">프로필 완성도</span>
                                    <span className="text-blue-400">{profile?.completeness_rate}%</span>
                                </div>
                                <Progress value={profile?.completeness_rate} className="h-2 bg-slate-700 overflow-hidden" indicatorClassName="bg-blue-500 shadow-[0_0_8px_rgba(59,130,246,0.5)]" />
                            </div>
                        </div>
                    </div>
                </CardContent>
            </Card>

            <div className="grid gap-8 md:grid-cols-3">
                {/* Main Info Section */}
                <div className="md:col-span-2 space-y-8">
                    <Card className="border-slate-100 shadow-sm">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2 text-xl font-bold text-slate-800">
                                <LayoutGrid size={20} className="text-blue-600" />
                                브랜딩 기본 정보
                            </CardTitle>
                            <CardDescription>타인에게 자신을 홍보하고 전문성을 증빙하는 영역입니다.</CardDescription>
                        </CardHeader>
                        <Separator className="bg-slate-50" />
                        <CardContent className="space-y-6 p-6">
                            {isAutoFilled && (
                                <div className="rounded-lg bg-blue-50 p-4 border border-blue-100 flex items-start gap-3">
                                    <AlertCircle className="text-blue-500 mt-0.5 shrink-0" size={16} />
                                    <p className="text-sm text-blue-800 font-medium">
                                        💡 대시보드에서 입력하신 정보가 자동으로 채워졌습니다. 자유롭게 수정 가능합니다.
                                    </p>
                                </div>
                            )}
                            <div className="grid gap-6 md:grid-cols-2">
                                <div className="space-y-2">
                                    <label className="text-sm font-bold text-slate-600">업종</label>
                                    <div className="relative">
                                        <input
                                            name="category"
                                            value={formData.category ?? ""}
                                            onChange={handleInputChange}
                                            placeholder="예: 일식 전문점"
                                            className="w-full rounded-lg border border-slate-200 px-4 py-3 pl-10 text-sm transition-all focus:border-blue-500 focus:ring-4 focus:ring-blue-50/50 outline-none"
                                        />
                                        <Briefcase className="absolute left-3 top-3.5 text-slate-400" size={16} />
                                    </div>
                                </div>
                                <div className="space-y-2">
                                    <label className="text-sm font-bold text-slate-600">창업 지역</label>
                                    <div className="relative">
                                        <input
                                            name="region"
                                            value={formData.region ?? ""}
                                            onChange={handleInputChange}
                                            placeholder="예: 서울 강남구"
                                            className="w-full rounded-lg border border-slate-200 px-4 py-3 pl-10 text-sm transition-all focus:border-blue-500 focus:ring-4 focus:ring-blue-50/50 outline-none"
                                        />
                                        <MapPin className="absolute left-3 top-3.5 text-slate-400" size={16} />
                                    </div>
                                </div>
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm font-bold text-slate-600">요리 철학</label>
                                <div className="relative">
                                    <textarea
                                        name="philosophy"
                                        value={formData.philosophy ?? ""}
                                        onChange={handleInputChange}
                                        placeholder="사장님만의 요리 철학을 입력해 주세요"
                                        rows={3}
                                        className="w-full rounded-lg border border-slate-200 px-4 py-3 pl-10 text-sm transition-all focus:border-blue-500 focus:ring-4 focus:ring-blue-50/50 outline-none resize-none"
                                    ></textarea>
                                    <Quote className="absolute left-3 top-3.5 text-slate-400" size={16} />
                                </div>
                            </div>
                        </CardContent>
                    </Card>

                    {/* Dynamic Lists Section */}
                    <Card className="border-slate-100 shadow-sm">
                        <CardHeader>
                            <CardTitle className="text-xl font-bold text-slate-800">전문성 증빙 데이터</CardTitle>
                        </CardHeader>
                        <Separator className="bg-slate-50" />
                        <CardContent className="space-y-8 p-6">
                            {/* Experiences */}
                            <div className="space-y-4">
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-2">
                                        <div className="rounded-full bg-blue-100 p-1.5 text-blue-600">
                                            <Briefcase size={16} />
                                        </div>
                                        <span className="font-bold text-slate-700">경력 사항</span>
                                    </div>
                                    <Button variant="ghost" size="sm" onClick={() => addListItem('experiences')} className="text-blue-600 hover:text-blue-700 hover:bg-blue-50">
                                        <Plus size={16} className="mr-1" /> 항목 추가
                                    </Button>
                                </div>
                                <div className="space-y-3">
                                    {formData.experiences?.map((item, index) => (
                                        <div key={index} className="flex gap-2">
                                            <input
                                                value={item}
                                                onChange={(e) => handleListChange('experiences', index, e.target.value)}
                                                placeholder="경력 사항을 입력하세요"
                                                className="flex-1 rounded-lg border border-slate-200 px-4 py-2 text-sm focus:border-blue-500 outline-none"
                                            />
                                            <Button variant="ghost" size="icon" onClick={() => removeListItem('experiences', index)} className="text-slate-400 hover:text-red-500">
                                                <X size={18} />
                                            </Button>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            {/* Awards */}
                            <div className="space-y-4">
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-2">
                                        <div className="rounded-full bg-amber-100 p-1.5 text-amber-600">
                                            <Trophy size={16} />
                                        </div>
                                        <span className="font-bold text-slate-700">수상 이력</span>
                                    </div>
                                    <Button variant="ghost" size="sm" onClick={() => addListItem('awards')} className="text-amber-600 hover:text-amber-700 hover:bg-amber-50">
                                        <Plus size={16} className="mr-1" /> 항목 추가
                                    </Button>
                                </div>
                                <div className="space-y-3">
                                    {formData.awards?.map((item, index) => (
                                        <div key={index} className="flex gap-2">
                                            <input
                                                value={item}
                                                onChange={(e) => handleListChange('awards', index, e.target.value)}
                                                placeholder="수상 이력을 입력하세요"
                                                className="flex-1 rounded-lg border border-slate-200 px-4 py-2 text-sm focus:border-amber-500 outline-none"
                                            />
                                            <Button variant="ghost" size="icon" onClick={() => removeListItem('awards', index)} className="text-slate-400 hover:text-red-500">
                                                <X size={18} />
                                            </Button>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            {/* Certificates */}
                            <div className="space-y-4">
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-2">
                                        <div className="rounded-full bg-emerald-100 p-1.5 text-emerald-600">
                                            <Award size={16} />
                                        </div>
                                        <span className="font-bold text-slate-700">자격증</span>
                                    </div>
                                    <Button variant="ghost" size="sm" onClick={() => addListItem('certificates')} className="text-emerald-600 hover:text-emerald-700 hover:bg-emerald-50">
                                        <Plus size={16} className="mr-1" /> 항목 추가
                                    </Button>
                                </div>
                                <div className="space-y-3">
                                    {formData.certificates?.map((item, index) => (
                                        <div key={index} className="flex gap-2">
                                            <input
                                                value={item}
                                                onChange={(e) => handleListChange('certificates', index, e.target.value)}
                                                placeholder="자격증을 입력하세요"
                                                className="flex-1 rounded-lg border border-slate-200 px-4 py-2 text-sm focus:border-emerald-500 outline-none"
                                            />
                                            <Button variant="ghost" size="icon" onClick={() => removeListItem('certificates', index)} className="text-slate-400 hover:text-red-500">
                                                <X size={18} />
                                            </Button>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </div>

                {/* Sidebar Info & Footer */}
                <div className="space-y-6">
                    <Card className="border-blue-100 bg-blue-50/30">
                        <CardHeader className="pb-2">
                            <CardTitle className="text-sm font-bold text-blue-800">최근 수정일</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <p className="text-lg font-bold text-blue-600">{formatDateTime(currentTime)}</p>
                        </CardContent>
                    </Card>

                    <div className="sticky top-8 space-y-4">
                        <Button
                            className="w-full h-12 bg-blue-600 hover:bg-blue-700 text-base font-bold shadow-lg shadow-blue-200 transition-all active:scale-[0.98]"
                            onClick={handleSave}
                            disabled={saving}
                        >
                            {saving ? "저장 중..." : <><Save size={18} className="mr-2" /> 설정 내용 최종 저장하기</>}
                        </Button>
                        <Button
                            variant="outline"
                            className="w-full h-12 border-slate-200 bg-white text-slate-600 hover:bg-slate-50 font-bold transition-all"
                            onClick={handleCancel}
                        >
                            <RotateCcw size={18} className="mr-2" /> 취소
                        </Button>

                        {error && (
                            <div className="flex items-center gap-2 rounded-lg bg-red-50 p-4 text-xs font-medium text-red-600 ring-1 ring-red-100">
                                <AlertCircle size={14} />
                                {error}
                            </div>
                        )}

                        <div className="rounded-xl border border-dashed border-slate-200 p-6 text-center">
                            <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-full bg-slate-50 text-slate-400">
                                <CheckCircle2 size={20} />
                            </div>
                            <p className="text-[13px] leading-relaxed text-slate-500">
                                입력된 모든 정보는 매칭 AI가 사장님의 스타일을 이해하는 데 큰 도움이 됩니다.
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
