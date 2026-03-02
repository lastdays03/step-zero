import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Loader2, UploadCloud, File as FileIcon, CheckCircle2, Download, Clock, Scale, Highlighter, CheckSquare, Plus, X } from "lucide-react";
import { apiClient } from "@/lib/api-client";
import { useDropzone } from "react-dropzone";
import { fetchItemDetail } from "../api";

interface ActionKitFileRecord {
    id: number;
    version: number;
    is_current: boolean;
    original_filename?: string;
    size_bytes?: number;
}

interface ActionKitEditItem {
    id?: number;
    isNew?: boolean;
    category_id?: number;
    name?: string;
    summary?: string;
    is_active?: boolean;
    sort_order?: number;
    files?: ActionKitFileRecord[];
    related_laws?: RelatedLawRecord[];
    highlights?: HighlightRecord[];
    checklists?: ChecklistRecord[];
}

interface RelatedLawRecord {
    id: number;
    law_name: string;
    law_summary?: string;
}

interface HighlightRecord {
    id: number;
    content: string;
}

interface ChecklistRecord {
    id: number;
    content: string;
}

interface ActionKitEditModalProps {
    item: ActionKitEditItem;
    isOpen: boolean;
    onClose: () => void;
    onSaved: () => void;
}

export function ActionKitEditModal({ item, isOpen, onClose, onSaved }: ActionKitEditModalProps) {
    const [loading, setLoading] = useState(false);
    const [uploading, setUploading] = useState(false);
    const [uploadSuccess, setUploadSuccess] = useState(false);
    const [currentItem, setCurrentItem] = useState<ActionKitEditItem>(item);

    const [formData, setFormData] = useState({
        domain: "kits",
        category_id: item?.category_id || 1,
        name: "",
        summary: "",
        is_active: false,
        sort_order: 0,
    });

    useEffect(() => {
        if (item && isOpen) {
            setCurrentItem(item);
            setFormData({
                domain: "kits",
                category_id: item.category_id || 1,
                name: item.name || "",
                summary: item.summary || "",
                is_active: item.is_active ?? false,
                sort_order: item.sort_order || 0,
            });
        }
    }, [item, isOpen]);

    const refreshItem = async () => {
        if (!currentItem?.id) return;
        try {
            const updated = await fetchItemDetail(currentItem.id);
            setCurrentItem(updated);
        } catch (e) {
            console.error('Failed to refresh item:', e);
        }
    };

    const isNew = currentItem?.isNew === true;

    const onDrop = async (acceptedFiles: File[]) => {
        if (!currentItem?.id || acceptedFiles.length === 0) return;

        const file = acceptedFiles[0];
        const formData = new FormData();
        formData.append("file", file);

        setUploading(true);
        setUploadSuccess(false);
        try {
            await apiClient.post(`/ops/actionkit/items/${currentItem.id}/files`, formData, {
                headers: {
                    'Content-Type': 'multipart/form-data'
                }
            });
            setUploadSuccess(true);
            onSaved();
            await refreshItem();
            setTimeout(() => setUploadSuccess(false), 3000);
        } catch (error) {
            console.error("Failed to upload file:", error);
            toast.error("파일 업로드 중 오류가 발생했습니다.");
        } finally {
            setUploading(false);
        }
    };

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        multiple: false
    });

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        try {
            if (isNew) {
                await apiClient.post(`/ops/actionkit/items`, formData);
            } else {
                if (!currentItem?.id) return;
                await apiClient.patch(`/ops/actionkit/items/${currentItem.id}`, formData);
            }
            onSaved();
            onClose();
        } catch (error) {
            console.error("Failed to update item:", error);
            toast.error("저장 중 오류가 발생했습니다.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <Dialog open={isOpen} onOpenChange={(open: boolean) => !open && onClose()}>
            <DialogContent className="sm:max-w-[500px] max-h-[85vh] border-slate-100 p-0 bg-white shadow-xl rounded-2xl flex flex-col">
                <DialogHeader className="p-6 pb-2 border-b border-slate-100 flex flex-row items-center justify-between flex-shrink-0">
                    <div>
                        <DialogTitle className="text-xl font-bold text-slate-800">
                            {isNew ? "새 문서 등록" : "문서 정보 수정"}
                        </DialogTitle>
                        <p className="text-sm text-slate-500 mt-1">
                            {isNew ? "새로운 문서 항목을 카테고리에 추가합니다." : "변경사항은 저장 즉시 앱 화면에 실시간으로 반영됩니다."}
                        </p>
                    </div>
                </DialogHeader>

                <form onSubmit={handleSubmit} className="p-6 space-y-5 bg-slate-50/50 overflow-y-auto flex-1">
                    <div className="space-y-2">
                        <Label htmlFor="name" className="text-slate-700 font-semibold text-sm">항목 제목</Label>
                        <Input
                            id="name"
                            name="name"
                            value={formData.name}
                            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                            className="bg-white border-slate-200 focus-visible:ring-[#36a4f2]/30 h-11"
                        />
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="summary" className="text-slate-700 font-semibold text-sm">요약 설명</Label>
                        <Textarea
                            id="summary"
                            name="summary"
                            value={formData.summary}
                            onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setFormData(prev => ({ ...prev, summary: e.target.value }))}
                            className="bg-white border-slate-200 focus-visible:ring-[#36a4f2]/30 min-h-[100px] resize-none"
                        />
                    </div>

                    <div className="grid grid-cols-2 gap-4 pt-1">
                        <div className="space-y-2">
                            <Label htmlFor="sort_order" className="text-slate-700 font-semibold text-sm">노출 순서 (낮을수록 먼저)</Label>
                            <Input
                                id="sort_order"
                                name="sort_order"
                                type="number"
                                value={formData.sort_order}
                                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFormData(prev => ({ ...prev, sort_order: parseInt(e.target.value) || 0 }))}
                                className="bg-white border-slate-200 focus-visible:ring-[#36a4f2]/30 h-11"
                            />
                        </div>

                        <div className="space-y-3 flex flex-col justify-end pb-2">
                            <div className="flex items-center justify-between bg-white border border-slate-200 p-3 rounded-lg h-11">
                                <Label htmlFor="is_active" className="text-slate-600 font-semibold text-sm cursor-pointer mb-0">
                                    사용자에게 공개
                                </Label>
                                <Switch
                                    id="is_active"
                                    checked={formData.is_active}
                                    onCheckedChange={(checked: boolean) => setFormData(prev => ({ ...prev, is_active: checked }))}
                                />
                            </div>
                        </div>
                    </div>

                    {/* File Upload Area (Only show for existing items, not when creating new) */}
                    {!isNew && currentItem?.id && (
                        <div className="pt-2">
                            <Label className="text-slate-700 font-semibold text-sm mb-2 block">파일 관리</Label>
                            <div
                                {...getRootProps()}
                                className={`border-2 border-dashed rounded-xl p-6 text-center transition-colors cursor-pointer
                                    ${isDragActive ? 'border-[#36a4f2] bg-[#36a4f2]/5' : 'border-slate-200 bg-white hover:bg-slate-50'}`}
                            >
                                <input {...getInputProps()} />
                                {uploading ? (
                                    <div className="flex flex-col items-center justify-center space-y-2 text-[#36a4f2]">
                                        <Loader2 className="w-8 h-8 animate-spin" />
                                        <p className="text-sm font-semibold">새 버전을 업로드하는 중입니다...</p>
                                    </div>
                                ) : uploadSuccess ? (
                                    <div className="flex flex-col items-center justify-center space-y-2 text-emerald-500">
                                        <CheckCircle2 className="w-8 h-8" />
                                        <p className="text-sm font-semibold">최신 파일로 성공적으로 업데이트되었습니다!</p>
                                    </div>
                                ) : (
                                    <div className="flex flex-col items-center justify-center space-y-2 text-slate-500">
                                        <div className="w-10 h-10 rounded-full bg-slate-100 flex items-center justify-center mb-1">
                                            <UploadCloud className="w-5 h-5 text-slate-400" />
                                        </div>
                                        <p className="text-sm font-semibold text-slate-700">
                                            마우스로 파일을 끌어다 놓거나 <span className="text-[#36a4f2]">클릭해서 선택</span>하세요.
                                        </p>
                                        <p className="text-xs text-slate-400">
                                            현재 첨부된 파일 버전: v{currentItem.files?.length ? Math.max(...currentItem.files.map((f: ActionKitFileRecord) => f.version)) : "없음"}
                                        </p>
                                    </div>
                                )}
                            </div>

                            {/* Version History */}
                            {currentItem.files && currentItem.files.length > 0 && (
                                <div className="mt-3">
                                    <div className="flex items-center gap-1.5 mb-2">
                                        <Clock className="w-3.5 h-3.5 text-slate-400" />
                                        <span className="text-xs font-semibold text-slate-500">버전 히스토리 ({currentItem.files.length}개)</span>
                                    </div>
                                    <div className="space-y-1.5 max-h-[160px] overflow-y-auto">
                                        {[...currentItem.files].sort((a: ActionKitFileRecord, b: ActionKitFileRecord) => b.version - a.version).map((f: ActionKitFileRecord) => (
                                            <div key={f.id} className={`flex items-center justify-between p-2.5 rounded-lg border text-xs transition-colors ${f.is_current
                                                ? 'bg-[#36a4f2]/5 border-[#36a4f2]/20'
                                                : 'bg-white border-slate-100 hover:bg-slate-50'
                                                }`}>
                                                <div className="flex items-center gap-2 min-w-0 flex-1">
                                                    <FileIcon className={`w-4 h-4 flex-shrink-0 ${f.is_current ? 'text-[#36a4f2]' : 'text-slate-400'}`} />
                                                    <div className="min-w-0">
                                                        <p className="font-semibold text-slate-700 truncate">
                                                            v{f.version} {f.is_current && <span className="text-[#36a4f2]">(최신)</span>}
                                                        </p>
                                                        <p className="text-slate-400 truncate">
                                                            {f.original_filename || '파일명 없음'} · {f.size_bytes ? `${(f.size_bytes / 1024).toFixed(0)}KB` : ''}
                                                        </p>
                                                    </div>
                                                </div>
                                                <button
                                                    type="button"
                                                    onClick={async () => {
                                                        try {
                                                            const res = await apiClient.get(`/ops/actionkit/files/${f.id}/download`, { responseType: 'blob' });
                                                            const url = window.URL.createObjectURL(new Blob([res.data]));
                                                            const link = document.createElement('a');
                                                            link.href = url;
                                                            link.setAttribute('download', f.original_filename || 'download');
                                                            document.body.appendChild(link);
                                                            link.click();
                                                            link.remove();
                                                            window.URL.revokeObjectURL(url);
                                                        } catch {
                                                            toast.error("파일 다운로드 중 오류가 발생했습니다.");
                                                        }
                                                    }}
                                                    className="flex items-center gap-1 px-2.5 py-1.5 rounded-md bg-white border border-slate-200 text-slate-500 hover:text-[#36a4f2] hover:border-[#36a4f2]/30 transition-colors flex-shrink-0 ml-2"
                                                >
                                                    <Download className="w-3.5 h-3.5" />
                                                    <span className="font-semibold">받기</span>
                                                </button>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    )}

                    {/* Related Laws Section */}
                    {!isNew && currentItem?.id && (
                        <div className="pt-2">
                            <Label className="text-slate-700 font-semibold text-sm mb-2 flex items-center gap-1.5">
                                <Scale className="w-3.5 h-3.5" /> 관련 법령
                            </Label>
                            <div className="space-y-1.5 mt-2">
                                {currentItem.related_laws?.map((law) => (
                                    <div key={law.id} className="flex items-center justify-between p-2.5 rounded-lg border border-slate-100 bg-white text-xs">
                                        <div className="min-w-0 flex-1">
                                            <p className="font-semibold text-slate-700 truncate">{law.law_name}</p>
                                            {law.law_summary && <p className="text-slate-400 truncate mt-0.5">{law.law_summary}</p>}
                                        </div>
                                        <button type="button" onClick={async () => {
                                            await apiClient.delete(`/ops/actionkit/related-laws/${law.id}`);
                                            onSaved?.();
                                            await refreshItem();
                                        }} className="text-slate-300 hover:text-red-400 transition-colors ml-2 flex-shrink-0">
                                            <X className="w-4 h-4" />
                                        </button>
                                    </div>
                                ))}
                            </div>
                            <div className="flex gap-2 mt-2">
                                <Input id="add_law_name" placeholder="법령명 (예: 건축법 제11조)" className="bg-white border-slate-200 h-9 text-xs flex-1" />
                                <Input id="add_law_summary" placeholder="요약 (선택)" className="bg-white border-slate-200 h-9 text-xs flex-1" />
                                <Button type="button" size="sm" className="bg-[#36a4f2] hover:bg-[#258bd1] h-9 px-3 flex-shrink-0" onClick={async () => {
                                    const nameEl = document.getElementById('add_law_name') as HTMLInputElement;
                                    const summaryEl = document.getElementById('add_law_summary') as HTMLInputElement;
                                    if (!nameEl.value.trim()) return;
                                    await apiClient.post(`/ops/actionkit/items/${currentItem.id}/related-laws`, {
                                        law_name: nameEl.value.trim(),
                                        law_summary: summaryEl.value.trim() || null
                                    });
                                    nameEl.value = '';
                                    summaryEl.value = '';
                                    onSaved?.();
                                    await refreshItem();
                                }}>
                                    <Plus className="w-3.5 h-3.5" />
                                </Button>
                            </div>
                        </div>
                    )}

                    {/* Highlights Section */}
                    {!isNew && currentItem?.id && (
                        <div className="pt-2">
                            <Label className="text-slate-700 font-semibold text-sm mb-2 flex items-center gap-1.5">
                                <Highlighter className="w-3.5 h-3.5" /> 핵심 포인트 (하이라이트)
                            </Label>
                            <div className="space-y-1.5 mt-2">
                                {currentItem.highlights?.map((hl) => (
                                    <div key={hl.id} className="flex items-center justify-between p-2.5 rounded-lg border border-amber-100 bg-amber-50/50 text-xs">
                                        <p className="font-medium text-slate-700 flex-1 min-w-0 truncate">{hl.content}</p>
                                        <button type="button" onClick={async () => {
                                            await apiClient.delete(`/ops/actionkit/highlights/${hl.id}`);
                                            onSaved?.();
                                            await refreshItem();
                                        }} className="text-slate-300 hover:text-red-400 transition-colors ml-2 flex-shrink-0">
                                            <X className="w-4 h-4" />
                                        </button>
                                    </div>
                                ))}
                            </div>
                            <div className="flex gap-2 mt-2">
                                <Input id="add_hl_content" placeholder="핵심 내용을 입력하세요 (예: 건축 허가 필수 조건)" className="bg-white border-slate-200 h-9 text-xs flex-1" />
                                <Button type="button" size="sm" className="bg-amber-500 hover:bg-amber-600 h-9 px-3 flex-shrink-0" onClick={async () => {
                                    const el = document.getElementById('add_hl_content') as HTMLInputElement;
                                    if (!el.value.trim()) return;
                                    await apiClient.post(`/ops/actionkit/items/${currentItem.id}/highlights`, {
                                        content: el.value.trim()
                                    });
                                    el.value = '';
                                    onSaved?.();
                                    await refreshItem();
                                }}>
                                    <Plus className="w-3.5 h-3.5" />
                                </Button>
                            </div>
                        </div>
                    )}

                    {/* ── Checklist ── */}
                    {currentItem.id && (
                        <div className="mt-6 space-y-3">
                            <div className="flex items-center gap-2">
                                <CheckSquare className="w-4 h-4 text-teal-500" />
                                <h3 className="text-sm font-bold text-slate-700">체크리스트</h3>
                            </div>
                            <div className="space-y-1.5">
                                {(currentItem.checklists || []).map((cl) => (
                                    <div key={cl.id} className="flex items-center justify-between bg-teal-50 rounded-lg px-3 py-2 text-sm text-teal-700">
                                        <div className="flex items-center gap-2 min-w-0">
                                            <CheckSquare className="w-3.5 h-3.5 flex-shrink-0" />
                                            <span className="truncate">{cl.content}</span>
                                        </div>
                                        <button type="button" onClick={async () => {
                                            await apiClient.delete(`/ops/actionkit/checklists/${cl.id}`);
                                            onSaved?.();
                                            await refreshItem();
                                        }} className="text-slate-300 hover:text-red-400 transition-colors ml-2 flex-shrink-0">
                                            <X className="w-4 h-4" />
                                        </button>
                                    </div>
                                ))}
                            </div>
                            <div className="flex gap-2 mt-2">
                                <Input id="add_cl_content" placeholder="체크 항목을 입력하세요 (예: 소방안전점검 완료 여부)" className="bg-white border-slate-200 h-9 text-xs flex-1" />
                                <Button type="button" size="sm" className="bg-teal-500 hover:bg-teal-600 h-9 px-3 flex-shrink-0" onClick={async () => {
                                    const el = document.getElementById('add_cl_content') as HTMLInputElement;
                                    if (!el.value.trim()) return;
                                    await apiClient.post(`/ops/actionkit/items/${currentItem.id}/checklists`, {
                                        content: el.value.trim()
                                    });
                                    el.value = '';
                                    onSaved?.();
                                    await refreshItem();
                                }}>
                                    <Plus className="w-3.5 h-3.5" />
                                </Button>
                            </div>
                        </div>
                    )}

                    <div className="flex justify-end gap-2 pt-4 border-t border-slate-200 mt-6">
                        <Button type="button" variant="outline" onClick={onClose} className="border-slate-200 text-slate-600 hover:bg-slate-100">
                            취소
                        </Button>
                        <Button type="submit" disabled={loading} className="bg-[#36a4f2] hover:bg-[#258bd1] text-white shadow-md shadow-[#36a4f2]/20 font-bold px-6">
                            {loading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
                            {loading ? "저장 중..." : "변경사항 저장"}
                        </Button>
                    </div>
                </form>
            </DialogContent>
        </Dialog>
    );
}
