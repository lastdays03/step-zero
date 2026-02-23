import { useEffect, useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Loader2, UploadCloud, File as FileIcon, CheckCircle2 } from "lucide-react";
import { apiClient } from "@/lib/api-client";
import { useDropzone } from "react-dropzone";

interface ActionKitEditModalProps {
    item: any;
    isOpen: boolean;
    onClose: () => void;
    onSaved: () => void;
}

export function ActionKitEditModal({ item, isOpen, onClose, onSaved }: ActionKitEditModalProps) {
    const [loading, setLoading] = useState(false);
    const [uploading, setUploading] = useState(false);
    const [uploadSuccess, setUploadSuccess] = useState(false);

    const [formData, setFormData] = useState({
        domain: "kits",  // Default, to be safe. We'll set it properly or derive it.
        category_id: item?.category_id || 1,
        name: "",
        summary: "",
        is_active: false,
        sort_order: 0,
    });

    useEffect(() => {
        if (item && isOpen) {
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

    const isNew = item?.isNew === true;

    const onDrop = async (acceptedFiles: File[]) => {
        if (!item?.id || acceptedFiles.length === 0) return;

        const file = acceptedFiles[0];
        const formData = new FormData();
        formData.append("file", file);

        setUploading(true);
        setUploadSuccess(false);
        try {
            await apiClient.post(`/ops/actionkit/items/${item.id}/files`, formData, {
                headers: {
                    'Content-Type': 'multipart/form-data'
                }
            });
            setUploadSuccess(true);
            onSaved(); // trigger reload in background
            setTimeout(() => setUploadSuccess(false), 3000);
        } catch (error) {
            console.error("Failed to upload file:", error);
            alert("파일 업로드 중 오류가 발생했습니다.");
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
                if (!item?.id) return;
                await apiClient.patch(`/ops/actionkit/items/${item.id}`, formData);
            }
            onSaved();
            onClose();
        } catch (error) {
            console.error("Failed to update item:", error);
            alert("저장 중 오류가 발생했습니다.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <Dialog open={isOpen} onOpenChange={(open: boolean) => !open && onClose()}>
            <DialogContent className="sm:max-w-[500px] border-slate-100 p-0 overflow-hidden bg-white shadow-xl rounded-2xl">
                <DialogHeader className="p-6 pb-2 border-b border-slate-100 flex flex-row items-center justify-between">
                    <div>
                        <DialogTitle className="text-xl font-bold text-slate-800">
                            {isNew ? "새 문서 등록" : "문서 정보 수정"}
                        </DialogTitle>
                        <p className="text-sm text-slate-500 mt-1">
                            {isNew ? "새로운 문서 항목을 카테고리에 추가합니다." : "변경사항은 저장 즉시 앱 화면에 실시간으로 반영됩니다."}
                        </p>
                    </div>
                </DialogHeader>

                <form onSubmit={handleSubmit} className="p-6 space-y-5 bg-slate-50/50">
                    <div className="space-y-2">
                        <Label htmlFor="name" className="text-slate-700 font-semibold text-sm">항목 제목</Label>
                        <Input
                            id="name"
                            name="name"
                            value={formData.name}
                            onChange={(e: any) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                            className="bg-white border-slate-200 focus-visible:ring-[#36a4f2]/30 h-11"
                        />
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="summary" className="text-slate-700 font-semibold text-sm">요약 설명</Label>
                        <Textarea
                            id="summary"
                            name="summary"
                            value={formData.summary}
                            onChange={(e: any) => setFormData(prev => ({ ...prev, summary: e.target.value }))}
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
                                onChange={(e: any) => setFormData(prev => ({ ...prev, sort_order: parseInt(e.target.value) || 0 }))}
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
                    {!isNew && item?.id && (
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
                                            현재 첨부된 파일 버전: v{item.files?.length ? item.files[0].version : "없음"}
                                        </p>
                                    </div>
                                )}
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
