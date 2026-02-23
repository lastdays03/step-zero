import { useEffect, useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Loader2 } from "lucide-react";
import { apiClient } from "@/lib/api-client";

interface ActionKitEditModalProps {
    item: any;
    isOpen: boolean;
    onClose: () => void;
    onSaved: () => void;
}

export function ActionKitEditModal({ item, isOpen, onClose, onSaved }: ActionKitEditModalProps) {
    const [loading, setLoading] = useState(false);
    const [formData, setFormData] = useState({
        name: "",
        summary: "",
        is_active: false,
        sort_order: 0,
    });

    useEffect(() => {
        if (item && isOpen) {
            setFormData({
                name: item.name || "",
                summary: item.summary || "",
                is_active: item.is_active ?? false,
                sort_order: item.sort_order || 0,
            });
        }
    }, [item, isOpen]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!item?.id) return;

        setLoading(true);
        try {
            await apiClient.patch(`/ops/actionkit/items/${item.id}`, formData);
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
                            문서 정보 수정
                        </DialogTitle>
                        <p className="text-sm text-slate-500 mt-1">
                            변경사항은 저장 즉시 앱 화면에 실시간으로 반영됩니다.
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
