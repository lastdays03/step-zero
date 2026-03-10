"use client";

import React, { useState, useEffect, useCallback } from "react";
import { toast } from "sonner";
import { DragDropContext, Droppable, Draggable, DropResult } from "@hello-pangea/dnd";

import { fetchCategories, fetchCategoryItems, fetchSummary, updateItemOrders } from "./api";
import type { ActionKitItem } from "@/features/actionkit";
import { useConfirmDialog } from "@/features/ops/shared/confirm-dialog";

interface OpsActionKitItem extends ActionKitItem {
  id: number;
  category_id: number;
  is_active: boolean;
  sort_order: number;
  ext?: string;
  file_type?: string;
  updated_at?: string;
  files?: { id: number; version: number; is_current: boolean, created_at?: string }[];
}

import { OpsAccessPlaceholder } from "@/features/ops/shared/ops-access-placeholder";
import { useOpsAccessGuard } from "@/features/ops/shared/use-ops-access-guard";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Search, FolderOpen, Loader2, Edit3, Trash2, Package, Paperclip, EyeOff, Scale, Highlighter, Settings, Plus, GripVertical, BarChart3, AlertTriangle } from "lucide-react";
import { ActionKitEditModal } from "@/features/ops/actionkit/components/actionkit-edit-modal";
import { CategoryEditModal } from "@/features/ops/actionkit/components/category-edit-modal";
import { OpsActionKitStatsDashboard } from "@/features/ops/actionkit/components/stats-dashboard";
import { apiClient } from "@/lib/api-client";

export function OpsActionKitView() {
  const { canRender } = useOpsAccessGuard();
  const { openConfirm, confirmDialog } = useConfirmDialog();

  const [loading, setLoading] = useState(true);
  const [categories, setCategories] = useState<{ id: number; title: string; domain: string; slug: string; sort_order: number; is_active: boolean }[]>([]);
  const [items, setItems] = useState<OpsActionKitItem[]>([]);
  const [activeCategory, setActiveCategory] = useState<number | null>(null);
  const [editingItem, setEditingItem] = useState<OpsActionKitItem | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [summary, setSummary] = useState<{
    total_items: number;
    items_with_files: number;
    inactive_items: number;
    total_related_laws: number;
    total_highlights: number;
  } | null>(null);
  const [activeDomain, setActiveDomain] = useState<"kits" | "laws" | "stats">("kits");

  const [allItems, setAllItems] = useState<OpsActionKitItem[]>([]);
  const [isCategoryModalOpen, setIsCategoryModalOpen] = useState(false);
  const [editingCategory, setEditingCategory] = useState<{ id: number; title: string; domain: string; slug: string; sort_order: number; is_active: boolean } | null>(null);

  const filteredCategories = categories.filter(cat => cat.domain === activeDomain);

  const filteredItems = items.filter(item => {
    const q = searchQuery.toLowerCase();
    return (
      item.name?.toLowerCase().includes(q) ||
      item.summary?.toLowerCase().includes(q)
    );
  });

  const loadItems = useCallback((categoryId: number) => {
    setLoading(true);
    fetchCategoryItems(categoryId)
      .then((data) => setItems(data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const handleDragEnd = async (result: DropResult) => {
    if (!result.destination) return;
    if (result.source.index === result.destination.index) return;
    if (searchQuery) return; // Disable drag during search

    const reorderedItems = Array.from(filteredItems);
    const [movedItem] = reorderedItems.splice(result.source.index, 1);
    reorderedItems.splice(result.destination.index, 0, movedItem);

    // Update sort_order locally
    const updatedItems = reorderedItems.map((item, index) => ({
      ...item,
      sort_order: index + 1
    }));

    setItems(updatedItems);

    try {
      const payload = updatedItems.map(item => ({ id: item.id, sort_order: item.sort_order }));
      await updateItemOrders(payload);
    } catch (e) {
      console.error("Failed to reorder items", e);
      if (activeCategory) loadItems(activeCategory); // Revert on failure
    }
  };

  const handleDelete = (item: OpsActionKitItem) => {
    openConfirm(
      {
        title: `\u0022${item.name}\u0022 항목을 정말 삭제하시겠습니까?`,
        description: "이 작업은 되돌릴 수 없습니다.",
        confirmLabel: "삭제",
        destructive: true,
      },
      async () => {
        try {
          await apiClient.delete(`/ops/actionkit/items/${item.id}`);
          if (activeCategory) loadItems(activeCategory);
          fetchSummary().then(setSummary).catch(console.error);
        } catch (error) {
          console.error("Failed to delete item:", error);
          toast.error("삭제 중 오류가 발생했습니다.");
        }
      },
    );
  };

  useEffect(() => {
    if (!canRender) return;

    fetchCategories()
      .then((data: { id: number; title: string; domain: string; slug: string; sort_order: number; is_active: boolean }[]) => {
        setCategories(data);
        const kitsCategories = data.filter((c) => c.domain === "kits");
        if (kitsCategories.length > 0) {
          setActiveCategory(kitsCategories[0].id);
        } else if (data.length > 0) {
          setActiveCategory(data[0].id);
        }
      })
      .catch(console.error);
    fetchSummary().then(setSummary).catch(console.error);
    // Load all items for stats tab outdated detection
    fetchCategories()
      .then(async (cats: { id: number; domain: string }[]) => {
        const allItemsResult: OpsActionKitItem[] = [];
        for (const cat of cats) {
          try {
            const catItems = await fetchCategoryItems(cat.id);
            allItemsResult.push(...catItems.map((i: OpsActionKitItem) => ({ ...i, domain: cat.domain })));
          } catch { /* skip */ }
        }
        setAllItems(allItemsResult);
      })
      .catch(console.error);
  }, [canRender]);

  useEffect(() => {
    if (activeCategory === null) return;
    let cancelled = false;
    const load = async () => {
      setLoading(true);
      try {
        const data = await fetchCategoryItems(activeCategory);
        if (!cancelled) setItems(data);
      } catch (err) {
        if (!cancelled) console.error(err);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    void load();
    return () => { cancelled = true; };
  }, [activeCategory]);

  const handleDomainChange = (domain: "kits" | "laws" | "stats") => {
    setActiveDomain(domain);
    if (domain !== "stats") {
      const domainCats = categories.filter(c => c.domain === domain);
      if (domainCats.length > 0) {
        setActiveCategory(domainCats[0].id);
      }
    }
  };

  const handleCategorySaved = () => {
    fetchCategories()
      .then((data: { id: number; title: string; domain: string; slug: string; sort_order: number; is_active: boolean }[]) => {
        setCategories(data);
        const domainCats = data.filter((c) => c.domain === activeDomain);
        if (domainCats.length > 0 && !domainCats.find((c) => c.id === activeCategory)) {
          setActiveCategory(domainCats[0].id);
        } else if (data.length > 0 && !activeCategory) {
          setActiveCategory(data[0].id);
        }
      })
      .catch(console.error);
  };

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

      {/* Statistics Cards */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          {[
            { icon: Package, label: "전체 항목", value: summary.total_items, color: "text-[#36a4f2]", bg: "bg-[#36a4f2]/10" },
            { icon: Paperclip, label: "파일 첨부", value: summary.items_with_files, color: "text-emerald-500", bg: "bg-emerald-50" },
            { icon: EyeOff, label: "미공개", value: summary.inactive_items, color: "text-orange-500", bg: "bg-orange-50" },
            { icon: Scale, label: "관련 법령", value: summary.total_related_laws, color: "text-violet-500", bg: "bg-violet-50" },
            { icon: Highlighter, label: "하이라이트", value: summary.total_highlights, color: "text-amber-500", bg: "bg-amber-50" },
          ].map((stat) => (
            <Card key={stat.label} className="border-none shadow-sm hover:shadow-md transition-shadow">
              <CardContent className="p-4 flex items-center gap-3">
                <div className={`w-10 h-10 rounded-xl ${stat.bg} flex items-center justify-center flex-shrink-0`}>
                  <stat.icon className={`w-5 h-5 ${stat.color}`} />
                </div>
                <div>
                  <p className="text-2xl font-black text-slate-800 leading-none">{stat.value}</p>
                  <p className="text-[10px] font-bold text-slate-400 mt-1">{stat.label}</p>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Domain Tabs (Top Level) */}
      <div className="flex p-1 bg-slate-100 rounded-2xl w-full md:w-fit shadow-inner overflow-x-auto">
        <button
          onClick={() => handleDomainChange("kits")}
          className={`flex items-center justify-center gap-1.5 md:gap-2 flex-1 md:flex-none py-2.5 px-4 md:px-6 rounded-xl text-sm font-bold whitespace-nowrap transition-all ${activeDomain === "kits"
            ? "bg-white text-[#36a4f2] shadow-sm"
            : "text-slate-500 hover:text-slate-700"
            }`}
        >
          <FolderOpen className="w-4 h-4 shrink-0" />
          액션 키트
        </button>
        <button
          onClick={() => handleDomainChange("laws")}
          className={`flex items-center justify-center gap-1.5 md:gap-2 flex-1 md:flex-none py-2.5 px-4 md:px-6 rounded-xl text-sm font-bold whitespace-nowrap transition-all ${activeDomain === "laws"
            ? "bg-white text-[#36a4f2] shadow-sm"
            : "text-slate-500 hover:text-slate-700"
            }`}
        >
          <Scale className="w-4 h-4 shrink-0" />
          법령 가이드
        </button>
        <button
          onClick={() => handleDomainChange("stats")}
          className={`flex items-center justify-center gap-1.5 md:gap-2 flex-1 md:flex-none py-2.5 px-4 md:px-6 rounded-xl text-sm font-bold whitespace-nowrap transition-all ${activeDomain === "stats"
            ? "bg-white text-[#36a4f2] shadow-sm"
            : "text-slate-500 hover:text-slate-700"
            }`}
        >
          <BarChart3 className="w-4 h-4 shrink-0" />
          통계 대시보드
        </button>
      </div>

      {activeDomain === "stats" ? (
        <OpsActionKitStatsDashboard items={allItems} />
      ) : (
        <>
          {/* Category Tabs (Sub Level) */}
          <div className="flex gap-2 border-b border-slate-200 pb-2 overflow-x-auto items-center">
            {filteredCategories.map((cat) => (
              <div key={cat.id} className="group relative flex items-center">
                <button
                  onClick={() => setActiveCategory(cat.id)}
                  onDoubleClick={() => {
                    setEditingCategory(cat);
                    setIsCategoryModalOpen(true);
                  }}
                  className={`px-4 py-2 font-bold text-sm rounded-t-xl transition-colors ${activeCategory === cat.id
                    ? "bg-slate-100 text-[#36a4f2] border-b-2 border-[#36a4f2]"
                    : "text-slate-500 hover:bg-slate-50"
                    }`}
                  title="더블 클릭하여 수정"
                >
                  {cat.title}
                </button>
                <button
                  title="카테고리 수정/삭제"
                  onClick={() => { setEditingCategory(cat); setIsCategoryModalOpen(true); }}
                  className="opacity-0 group-hover:opacity-100 absolute right-1 top-1 text-slate-400 hover:text-[#36a4f2] bg-white rounded-full p-0.5"
                >
                  <Settings className="w-3 h-3" />
                </button>
              </div>
            ))}
            <button
              title="새 카테고리 추가"
              onClick={() => { setEditingCategory(null); setIsCategoryModalOpen(true); }}
              className="ml-2 w-8 h-8 rounded-full border border-dashed border-slate-300 flex items-center justify-center text-slate-400 hover:text-[#36a4f2] hover:border-[#36a4f2] transition-colors"
            >
              <Plus className="w-5 h-5" />
            </button>
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
                        <th className="px-3 py-3 w-8"></th>
                        <th className="px-6 py-3">상태</th>
                        <th className="px-6 py-3 w-1/3">제목</th>
                        <th className="px-6 py-3">종류/태그</th>
                        <th className="px-6 py-3">첨부버전</th>
                        <th className="px-6 py-3">순서</th>
                        <th className="px-6 py-3 text-right">관리</th>
                      </tr>
                    </thead>
                    <DragDropContext onDragEnd={handleDragEnd}>
                      <Droppable droppableId="items_list">
                        {(provided) => (
                          <tbody
                            className="divide-y divide-slate-100"
                            {...provided.droppableProps}
                            ref={provided.innerRef}
                          >
                            {filteredItems.map((item, index) => (
                              <Draggable key={item.id.toString()} draggableId={item.id.toString()} index={index} isDragDisabled={!!searchQuery}>
                                {(provided, snapshot) => (
                                  <tr
                                    ref={provided.innerRef}
                                    {...provided.draggableProps}
                                    className={`transition-colors ${snapshot.isDragging ? 'bg-white shadow-xl ring-1 ring-[#36a4f2]/20' : 'hover:bg-slate-50'}`}
                                  >
                                    <td className="px-3 py-4" {...provided.dragHandleProps}>
                                      <GripVertical className="w-4 h-4 text-slate-300 hover:text-slate-500 cursor-grab active:cursor-grabbing" />
                                    </td>
                                    <td className="px-6 py-4">
                                      <Badge className={`border-none ${item.is_active ? 'bg-emerald-100 text-emerald-600' : 'bg-slate-100 text-slate-400'}`}>
                                        {item.is_active ? '게시중' : '숨김'}
                                      </Badge>
                                    </td>
                                    <td className="px-6 py-4">
                                      <div className="font-bold flex items-center gap-2">
                                        {item.name}
                                        {!item.is_active && <Badge variant="secondary" className="text-xs bg-slate-100 text-slate-500 hover:bg-slate-200 border-none px-1.5 py-0">미공개</Badge>}
                                        {(() => {
                                          let isOutdated = false;
                                          if (item.updated_at) {
                                            const updatedDate = new Date(item.updated_at);
                                            const now = new Date();
                                            const diffTime = Math.abs(now.getTime() - updatedDate.getTime());
                                            const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
                                            if (diffDays > 365) isOutdated = true;
                                          }
                                          if (isOutdated) {
                                            return <Badge variant="destructive" className="text-[10px] bg-red-50 text-red-600 border border-red-200 hover:bg-red-100 px-1.5 py-0 shadow-none"><AlertTriangle className="w-3 h-3 mr-1" />갱신 필요</Badge>
                                          }
                                          return null;
                                        })()}
                                      </div>
                                      <p className="text-xs text-slate-400 line-clamp-1 mt-0.5">{item.summary}</p>
                                    </td>
                                    <td className="px-6 py-4">
                                      <Badge variant="outline" className="text-[10px] text-slate-500">{item.type || item.ext || item.file_type || "유형없음"}</Badge>
                                    </td>
                                    <td className="px-6 py-4 text-xs font-semibold text-slate-500">
                                      v{item.files?.length ? item.files[0].version : "1"} (최신)
                                    </td>
                                    <td className="px-6 py-4 text-xs text-slate-500">
                                      {item.sort_order || 0}
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
                                )}
                              </Draggable>
                            ))}
                            {provided.placeholder}
                          </tbody>
                        )}
                      </Droppable>
                    </DragDropContext>
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
                fetchSummary().then(setSummary).catch(console.error);
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
                fetchSummary().then(setSummary).catch(console.error);
              }}
            />
          )}

          {(isCategoryModalOpen) && (
            <CategoryEditModal
              isOpen={isCategoryModalOpen}
              onClose={() => setIsCategoryModalOpen(false)}
              onSaved={handleCategorySaved}
              category={editingCategory}
              activeDomain={activeDomain}
            />
          )}
          {confirmDialog}
        </>
      )}
    </div>
  );
}
