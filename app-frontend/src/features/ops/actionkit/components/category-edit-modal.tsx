import React, { useState, useEffect } from "react";
import { toast } from "sonner";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useConfirmDialog } from "@/features/ops/shared/confirm-dialog";
import { createCategory, updateCategory, deleteCategory } from "../api";

interface Category {
    id: number;
    title: string;
    domain: string;
    slug: string;
    sort_order: number;
    is_active: boolean;
}

interface CategoryEditModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSaved: () => void;
    category?: Category | null;
    activeDomain: string;
}

export function CategoryEditModal({ isOpen, onClose, onSaved, category, activeDomain }: CategoryEditModalProps) {
    const isEditing = !!category;
    const { openConfirm, confirmDialog } = useConfirmDialog();
    const [title, setTitle] = useState("");
    const [slug, setSlug] = useState("");
    const [sortOrder, setSortOrder] = useState("0");
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (isOpen) {
            if (isEditing && category) {
                setTitle(category.title);
                setSlug(category.slug || "");
                setSortOrder(String(category.sort_order || 0));
            } else {
                setTitle("");
                setSlug("");
                setSortOrder("0");
            }
        }
    }, [isOpen, category, isEditing]);

    const handleSave = async () => {
        if (!title.trim() || !slug.trim()) {
            toast.warning("카테고리명과 슬러그(영어 영문명)는 필수입니다.");
            return;
        }

        setLoading(true);
        try {
            const payload = {
                title,
                slug,
                sort_order: parseInt(sortOrder) || 0,
                domain: isEditing && category ? category.domain : activeDomain,
                is_active: true
            };

            if (isEditing && category) {
                await updateCategory(category.id, payload);
            } else {
                await createCategory(payload);
            }
            onSaved();
            onClose();
        } catch (err) {
            console.error("Failed to save category:", err);
            toast.error("카테고리 저장 중 오류가 발생했습니다.");
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = () => {
        if (!category) return;
        openConfirm(
            {
                title: `"${category.title}" 카테고리를 정말 삭제하시겠습니까?`,
                description: "이 작업은 되돌릴 수 없으며 내부 항목이 연결되어 있으면 실패할 수 있습니다.",
                confirmLabel: "삭제",
                destructive: true,
            },
            async () => {
                setLoading(true);
                try {
                    await deleteCategory(category.id);
                    onSaved();
                    onClose();
                } catch (err) {
                    console.error("Failed to delete category:", err);
                    toast.error("삭제 중 오류가 발생했습니다. 카테고리에 속한 항목을 먼저 모두 삭제하거나 이동하세요.");
                } finally {
                    setLoading(false);
                }
            }
        );
    };

    return (
        <>
            <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
                <DialogContent className="sm:max-w-[425px]">
                    <DialogHeader>
                        <DialogTitle>{isEditing ? "카테고리 수정" : "새 카테고리 추가"}</DialogTitle>
                    </DialogHeader>
                    <div className="grid gap-4 py-4">
                        <div className="grid gap-2">
                            <label className="text-sm font-bold text-slate-700">카테고리명</label>
                            <Input
                                value={title}
                                onChange={(e) => setTitle(e.target.value)}
                                placeholder="예: 정부지원사업, 창업가이드"
                            />
                        </div>
                        <div className="grid gap-2">
                            <label className="text-sm font-bold text-slate-700">고유 슬러그 (영어)</label>
                            <Input
                                value={slug}
                                onChange={(e) => setSlug(e.target.value)}
                                placeholder="예: startup-fund"
                            />
                            <p className="text-[10px] text-slate-400">URL이나 시스템 식별자로 사용되는 고유한 영어 소문자 조합입니다.</p>
                        </div>
                        <div className="grid gap-2">
                            <label className="text-sm font-bold text-slate-700">정렬 순서</label>
                            <Input
                                type="number"
                                value={sortOrder}
                                onChange={(e) => setSortOrder(e.target.value)}
                            />
                            <p className="text-[10px] text-slate-400">숫자가 작을수록 탭 앞쪽에 배치됩니다.</p>
                        </div>
                    </div>
                    <DialogFooter className="flex justify-between sm:justify-between w-full">
                        {isEditing ? (
                            <Button variant="destructive" onClick={handleDelete} disabled={loading} className="mr-auto">
                                삭제
                            </Button>
                        ) : <div></div>}
                        <div className="flex gap-2">
                            <Button variant="outline" onClick={onClose}>취소</Button>
                            <Button onClick={handleSave} disabled={loading} className="bg-[#36a4f2] hover:bg-[#258bd1]">
                                {loading ? "저장 중..." : "저장"}
                            </Button>
                        </div>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
            {confirmDialog}
        </>
    );
}
