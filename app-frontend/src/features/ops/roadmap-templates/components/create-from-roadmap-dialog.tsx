"use client";

import { Loader2, Search } from "lucide-react";
import React, { useCallback, useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";

import { createTemplateFromRoadmap, searchRoadmaps } from "../api";
import type { RoadmapSearchResult } from "../types";

interface CreateFromRoadmapDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onCreated: () => void;
}

export function CreateFromRoadmapDialog({
  isOpen,
  onClose,
  onCreated,
}: CreateFromRoadmapDialogProps) {
  const [mode, setMode] = useState<"search" | "uuid">("search");
  const [roadmapId, setRoadmapId] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");

  // Search state
  const [searchQuery, setSearchQuery] = useState("");
  const [filterBusinessType, setFilterBusinessType] = useState("");
  const [filterStartupMethod, setFilterStartupMethod] = useState("");
  const [filterStartupType, setFilterStartupType] = useState("");
  const [searchResults, setSearchResults] = useState<RoadmapSearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [selectedId, setSelectedId] = useState<string>("");

  const handleSearch = useCallback(async () => {
    setIsSearching(true);
    setError("");
    try {
      const results = await searchRoadmaps({
        q: searchQuery || undefined,
        business_type: filterBusinessType || undefined,
        startup_method: filterStartupMethod || undefined,
        startup_type: filterStartupType || undefined,
      });
      setSearchResults(results);
    } catch {
      setError("검색에 실패했습니다.");
    } finally {
      setIsSearching(false);
    }
  }, [searchQuery, filterBusinessType, filterStartupMethod, filterStartupType]);

  const handleSubmit = async () => {
    const targetId = mode === "search" ? selectedId : roadmapId.trim();
    if (!targetId) {
      setError(mode === "search" ? "로드맵을 선택하세요." : "UUID를 입력하세요.");
      return;
    }
    setError("");
    setIsSubmitting(true);
    try {
      await createTemplateFromRoadmap(targetId);
      resetState();
      onCreated();
      onClose();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "템플릿 생성에 실패했습니다.",
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  const resetState = () => {
    setRoadmapId("");
    setSearchQuery("");
    setFilterBusinessType("");
    setFilterStartupMethod("");
    setFilterStartupType("");
    setSearchResults([]);
    setSelectedId("");
    setError("");
    setMode("search");
  };

  const handleOpenChange = (open: boolean) => {
    if (!open && !isSubmitting) {
      resetState();
      onClose();
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>로드맵에서 템플릿 생성</DialogTitle>
          <DialogDescription>
            기존 로드맵을 검색하여 선택하거나 UUID를 직접 입력할 수 있습니다.
          </DialogDescription>
        </DialogHeader>

        {/* Mode toggle */}
        <div className="flex gap-2 border-b pb-2">
          <button
            type="button"
            className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
              mode === "search"
                ? "bg-blue-100 text-blue-700 font-medium"
                : "text-slate-500 hover:text-slate-700"
            }`}
            onClick={() => setMode("search")}
          >
            검색
          </button>
          <button
            type="button"
            className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
              mode === "uuid"
                ? "bg-blue-100 text-blue-700 font-medium"
                : "text-slate-500 hover:text-slate-700"
            }`}
            onClick={() => setMode("uuid")}
          >
            UUID 직접 입력
          </button>
        </div>

        {mode === "search" ? (
          <div className="space-y-3">
            {/* Filters */}
            <div className="grid gap-2 md:grid-cols-4">
              <Input
                placeholder="업종"
                value={filterBusinessType}
                onChange={(e) => setFilterBusinessType(e.target.value)}
              />
              <Input
                placeholder="창업방식"
                value={filterStartupMethod}
                onChange={(e) => setFilterStartupMethod(e.target.value)}
              />
              <Input
                placeholder="창업형태"
                value={filterStartupType}
                onChange={(e) => setFilterStartupType(e.target.value)}
              />
              <div className="flex gap-1">
                <Input
                  placeholder="제목 검색"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") void handleSearch();
                  }}
                />
                <Button
                  size="sm"
                  className="shrink-0 px-3"
                  onClick={() => void handleSearch()}
                  disabled={isSearching}
                >
                  <Search size={14} />
                </Button>
              </div>
            </div>

            {/* Results */}
            <div className="max-h-60 overflow-y-auto rounded-md border">
              {isSearching ? (
                <div className="flex items-center justify-center py-8 text-slate-400">
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" /> 검색 중...
                </div>
              ) : searchResults.length > 0 ? (
                <table className="w-full text-sm">
                  <thead className="sticky top-0 bg-slate-50 text-left text-xs font-bold text-slate-500">
                    <tr>
                      <th className="px-3 py-2">제목</th>
                      <th className="px-3 py-2">업종</th>
                      <th className="px-3 py-2">방식</th>
                      <th className="px-3 py-2">형태</th>
                    </tr>
                  </thead>
                  <tbody>
                    {searchResults.map((r) => (
                      <tr
                        key={r.id}
                        className={`cursor-pointer border-t transition-colors ${
                          selectedId === r.id
                            ? "bg-blue-50"
                            : "hover:bg-slate-50"
                        }`}
                        onClick={() => setSelectedId(r.id)}
                      >
                        <td className="px-3 py-2 font-medium">{r.title}</td>
                        <td className="px-3 py-2 text-slate-600">{r.business_type}</td>
                        <td className="px-3 py-2 text-slate-600">{r.startup_method || "-"}</td>
                        <td className="px-3 py-2 text-slate-600">{r.startup_type || "-"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <div className="py-8 text-center text-sm text-slate-400">
                  검색 버튼을 클릭하여 로드맵을 찾으세요.
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700">
              로드맵 UUID
            </label>
            <Input
              placeholder="예: 550e8400-e29b-41d4-a716-446655440000"
              value={roadmapId}
              onChange={(e) => {
                setRoadmapId(e.target.value);
                if (error) setError("");
              }}
              disabled={isSubmitting}
            />
          </div>
        )}

        {error && <p className="text-sm text-red-500">{error}</p>}

        <DialogFooter>
          <Button
            variant="outline"
            onClick={onClose}
            disabled={isSubmitting}
          >
            취소
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={
              isSubmitting ||
              (mode === "search" ? !selectedId : !roadmapId.trim())
            }
            className="gap-2 bg-blue-600 hover:bg-blue-700"
          >
            {isSubmitting && <Loader2 className="h-4 w-4 animate-spin" />}
            {isSubmitting ? "생성 중..." : "생성"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
