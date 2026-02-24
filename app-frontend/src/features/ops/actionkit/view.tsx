"use client";

import React, { useState, useEffect } from "react";
import { Link } from "lucide-react";

import { fetchCategories, fetchCategoryItems } from "./api";
import { ActionKitItem } from "@/features/actionkit/types";
import { OpsAccessPlaceholder } from "@/features/ops/shared/ops-access-placeholder";
import { useOpsAccessGuard } from "@/features/ops/shared/use-ops-access-guard";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Search, FolderOpen, Loader2, Edit3, Trash2 } from "lucide-react";
import { ActionKitEditModal } from "@/features/ops/actionkit/components/actionkit-edit-modal";
import { apiClient } from "@/lib/api-client";

export function OpsActionKitView() {
  const { canRender } = useOpsAccessGuard();

  const [loading, setLoading] = useState(true);
  const [categories, setCategories] = useState<any[]>([]);
  const [items, setItems] = useState<ActionKitItem[]>([]);
  const [activeCategory, setActiveCategory] = useState<number | null>(null);
  const [editingItem, setEditingItem] = useState<ActionKitItem | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  const filteredItems = items.filter(item => {
    const q = searchQuery.toLowerCase();
    return (
      item.name?.toLowerCase().includes(q) ||
      item.summary?.toLowerCase().includes(q)
    );
  });

  const loadItems = (categoryId: number) => {
    setLoading(true);
    fetchCategoryItems(categoryId)
      .then((data) => setItems(data))
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  const handleDelete = async (item: ActionKitItem) => {
    if (!confirm(`"${item.name}" 항목을 정말 삭제하시겠습니까?\n이 작업은 되돌릴 수 없습니다.`)) return;
    try {
      await apiClient.delete(`/ops/actionkit/items/${(item as any).id}`);
      if (activeCategory) loadItems(activeCategory);
    } catch (error) {
      console.error("Failed to delete item:", error);
      alert("삭제 중 오류가 발생했습니다.");
    }
  };

  useEffect(() => {
    if (!canRender) return;

    fetchCategories()
      .then((data) => {
        setCategories(data);
        if (data.length > 0) {
          setActiveCategory(data[0].id);
        }
      })
      .catch(console.error);
  }, [canRender]);

  useEffect(() => {
    if (activeCategory === null) return;
    loadItems(activeCategory);
  }, [activeCategory]);

  if (!canRender) return <OpsAccessPlaceholder />;

  return (
    <div className="space-y-6">
      <header className="flex justify-between items-end">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">액션 키트 관리 (Admin)</h1>
          <p className="mt-1 text-sm text-slate-500">
            앱 화면에 노출되는 액션 키트 라이브러리와 법령 가이드를 운영할 수 있습니다.
          </p>
        </div>
        <Button
          className="bg-[#36a4f2] hover:bg-[#258bd1]"
          onClick={() => setIsCreating(true)}
          disabled={!activeCategory}
        >
          + 새 항목 등록
        </Button>
      </header>

      {/* Category Tabs */}
      <div className="flex gap-2 border-b border-slate-200 pb-2 overflow-x-auto">
        {categories.map((cat) => (
          <button
            key={cat.id}
            onClick={() => setActiveCategory(cat.id)}
            className={`px-4 py-2 font-bold text-sm rounded-t-xl transition-colors ${activeCategory === cat.id
              ? "bg-slate-100 text-[#36a4f2] border-b-2 border-[#36a4f2]"
              : "text-slate-500 hover:bg-slate-50"
              }`}
          >
            {cat.title} ({cat.domain})
          </button>
        ))}
      </div>

      <Card className="shadow-sm border-slate-200">
        <div className="p-4 border-b border-slate-100 flex justify-between">
          <div className="relative w-64">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              placeholder="항목 검색..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-4 py-1.5 text-sm border-slate-200 rounded-lg focus:ring-[#36a4f2]/20 outline-none border"
            />
          </div>
          <div className="text-sm font-semibold text-slate-500 flex items-center">
            총 {filteredItems.length}개 항목
          </div>
        </div>
        <CardContent className="p-0">
          {loading ? (
            <div className="py-20 flex justify-center items-center text-slate-400">
              <Loader2 className="w-8 h-8 animate-spin" />
            </div>
          ) : filteredItems.length === 0 ? (
            <div className="py-20 text-center text-slate-400">
              <FolderOpen className="w-12 h-12 mx-auto mb-4 opacity-20" />
              <p className="text-sm font-bold">
                {searchQuery ? "검색 결과가 없습니다." : "이 카테고리에는 아직 항목이 없습니다."}
              </p>
            </div>
          ) : (
            <div className="w-full">
              <table className="w-full text-left text-sm whitespace-nowrap">
                <thead className="bg-slate-50 text-slate-500 font-semibold border-b border-slate-100">
                  <tr>
                    <th className="px-6 py-3">상태</th>
                    <th className="px-6 py-3 w-1/3">제목</th>
                    <th className="px-6 py-3">종류/태그</th>
                    <th className="px-6 py-3">첨부버전</th>
                    <th className="px-6 py-3">순서</th>
                    <th className="px-6 py-3 text-right">관리</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {filteredItems.map((item) => (
                    <tr key={item.name} className="hover:bg-slate-50 transition-colors">
                      <td className="px-6 py-4">
                        <Badge className={`border-none ${(item as any).is_active ? 'bg-emerald-100 text-emerald-600' : 'bg-slate-100 text-slate-400'}`}>
                          {(item as any).is_active ? '게시중' : '숨김'}
                        </Badge>
                      </td>
                      <td className="px-6 py-4">
                        <p className="font-bold text-slate-800 line-clamp-1">{item.name}</p>
                        <p className="text-xs text-slate-400 line-clamp-1 mt-0.5">{item.summary}</p>
                      </td>
                      <td className="px-6 py-4">
                        <Badge variant="outline" className="text-[10px] text-slate-500">{item.type || (item as any).ext || (item as any).file_type || "유형없음"}</Badge>
                      </td>
                      <td className="px-6 py-4 text-xs font-semibold text-slate-500">
                        v{(item as any).files?.length ? (item as any).files[0].version : "1"} (최신)
                      </td>
                      <td className="px-6 py-4 text-xs text-slate-500">
                        {(item as any).sort_order || 0}
                      </td>
                      <td className="px-6 py-4 text-right">
                        <div className="flex justify-end gap-2">
                          <Button
                            variant="outline"
                            size="icon"
                            onClick={() => setEditingItem(item)}
                            className="w-8 h-8 rounded-md text-slate-400 hover:text-[#36a4f2]"
                          >
                            <Edit3 className="w-4 h-4" />
                          </Button>
                          <Button variant="outline" size="icon" className="w-8 h-8 rounded-md text-slate-400 hover:text-red-500" onClick={() => handleDelete(item)}>
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {editingItem && (
        <ActionKitEditModal
          item={editingItem}
          isOpen={!!editingItem}
          onClose={() => setEditingItem(null)}
          onSaved={() => {
            if (activeCategory) loadItems(activeCategory);
          }}
        />
      )}

      {isCreating && activeCategory && (
        <ActionKitEditModal
          item={{ category_id: activeCategory, isNew: true }}
          isOpen={isCreating}
          onClose={() => setIsCreating(false)}
          onSaved={() => {
            if (activeCategory) loadItems(activeCategory);
          }}
        />
      )}
    </div>
  );
}
