"use client";

import { useCallback, useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  ArrowLeft,
  X,
  Plus,
  MoreVertical,
  Pencil,
  Trash2,
  MessageSquare,
  Loader2,
} from "lucide-react";
import { useSessions, type SessionGroup } from "../hooks/useSessions";
import { useChatProvider } from "../providers/ChatProvider";
import type { ChatSession } from "../types";

// ------------------------------------------------------------------ //
//  상대시간 포맷
// ------------------------------------------------------------------ //

function formatRelativeTime(dateStr: string): string {
  const now = Date.now();
  const date = new Date(dateStr).getTime();
  const diffMs = now - date;
  const diffMin = Math.floor(diffMs / 60_000);
  const diffHour = Math.floor(diffMs / 3_600_000);

  if (diffMin < 1) return "방금 전";
  if (diffMin < 60) return `${diffMin}분 전`;
  if (diffHour < 24) return `${diffHour}시간 전`;

  const d = new Date(dateStr);
  const today = new Date();
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);

  if (isSameDay(d, yesterday)) return "어제";
  return `${diffHour >= 48 ? Math.floor(diffHour / 24) : 2}일 전`;
}

function isSameDay(a: Date, b: Date): boolean {
  return (
    a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate()
  );
}

// ------------------------------------------------------------------ //
//  SessionItem
// ------------------------------------------------------------------ //

interface SessionItemProps {
  session: ChatSession;
  isActive: boolean;
  onSelect: (id: string) => void;
  onRename: (id: string, title: string) => void;
  onDelete: (id: string) => void;
}

function SessionItem({
  session,
  isActive,
  onSelect,
  onRename,
  onDelete,
}: SessionItemProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editTitle, setEditTitle] = useState("");

  const handleStartRename = useCallback(() => {
    setEditTitle(session.title || "새 대화");
    setIsEditing(true);
  }, [session.title]);

  const handleConfirmRename = useCallback(() => {
    const trimmed = editTitle.trim();
    if (trimmed && trimmed !== session.title) {
      onRename(session.id, trimmed);
    }
    setIsEditing(false);
  }, [editTitle, session.id, session.title, onRename]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (e.key === "Enter") {
        e.preventDefault();
        handleConfirmRename();
      } else if (e.key === "Escape") {
        setIsEditing(false);
      }
    },
    [handleConfirmRename],
  );

  const handleDelete = useCallback(() => {
    if (window.confirm("이 대화를 삭제하시겠습니까?")) {
      onDelete(session.id);
    }
  }, [session.id, onDelete]);

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={() => !isEditing && onSelect(session.id)}
      onKeyDown={(e) => {
        if (e.key === "Enter" && !isEditing) onSelect(session.id);
      }}
      className={`group flex items-start gap-2.5 px-3 py-2.5 rounded-lg cursor-pointer transition-colors ${
        isActive
          ? "bg-blue-50 border border-blue-200"
          : "hover:bg-slate-50 border border-transparent"
      }`}
    >
      <MessageSquare className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />

      <div className="flex-1 min-w-0">
        {isEditing ? (
          <input
            type="text"
            value={editTitle}
            onChange={(e) => setEditTitle(e.target.value)}
            onBlur={handleConfirmRename}
            onKeyDown={handleKeyDown}
            autoFocus
            className="w-full text-sm font-medium bg-white border border-blue-300 rounded px-1.5 py-0.5 outline-none focus:ring-1 focus:ring-blue-400"
          />
        ) : (
          <p className="text-sm font-medium text-slate-700 truncate">
            {session.title || "새 대화"}
          </p>
        )}
        <p className="text-[11px] text-slate-400 mt-0.5">
          {formatRelativeTime(session.updated_at || session.created_at)}
          {session.message_count > 0 && (
            <span> · {session.message_count}개 메시지</span>
          )}
        </p>
      </div>

      {/* 드롭다운 메뉴 — 호버 시 표시 */}
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <button
            type="button"
            onClick={(e) => e.stopPropagation()}
            className="opacity-0 group-hover:opacity-100 focus:opacity-100 p-1 rounded hover:bg-slate-200 transition-opacity"
          >
            <MoreVertical className="w-3.5 h-3.5 text-slate-400" />
          </button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-32">
          <DropdownMenuItem
            onClick={(e) => {
              e.stopPropagation();
              handleStartRename();
            }}
          >
            <Pencil className="w-3.5 h-3.5 mr-2" />
            이름 변경
          </DropdownMenuItem>
          <DropdownMenuItem
            onClick={(e) => {
              e.stopPropagation();
              handleDelete();
            }}
            className="text-red-600 focus:text-red-600"
          >
            <Trash2 className="w-3.5 h-3.5 mr-2" />
            삭제
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
}

// ------------------------------------------------------------------ //
//  ChatHistory
// ------------------------------------------------------------------ //

interface ChatHistoryProps {
  onClose: () => void;
  onSelectSession: (sessionId: string) => void;
}

export function ChatHistory({ onClose, onSelectSession }: ChatHistoryProps) {
  const { currentSessionId, setCurrentSessionId } = useChatProvider();
  const {
    groupedSessions,
    isLoading,
    error,
    loadSessions,
    createSession,
    renameSession,
    deleteSession,
  } = useSessions();

  // 마운트 시 세션 로드
  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  const handleNewChat = useCallback(async () => {
    const session = await createSession();
    if (session) {
      onSelectSession(session.id);
    }
  }, [createSession, onSelectSession]);

  const handleSelectSession = useCallback(
    (sessionId: string) => {
      setCurrentSessionId(sessionId);
      onSelectSession(sessionId);
    },
    [setCurrentSessionId, onSelectSession],
  );

  return (
    <div className="flex flex-col h-full">
      {/* 헤더 */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-200">
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={onClose}
            className="p-1 rounded hover:bg-slate-100 transition-colors"
          >
            <ArrowLeft className="w-4 h-4 text-slate-600" />
          </button>
          <h2 className="text-sm font-semibold text-slate-800">대화 목록</h2>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="p-1 rounded hover:bg-slate-100 transition-colors"
        >
          <X className="w-4 h-4 text-slate-500" />
        </button>
      </div>

      {/* 새 대화 버튼 */}
      <div className="px-3 pt-3 pb-1">
        <Button
          onClick={handleNewChat}
          variant="outline"
          size="sm"
          className="w-full justify-start gap-2 text-blue-600 border-blue-200 hover:bg-blue-50"
        >
          <Plus className="w-4 h-4" />새 대화
        </Button>
      </div>

      {/* 세션 목록 */}
      <div className="flex-1 overflow-y-auto px-2 py-2">
        {isLoading && (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-5 h-5 text-slate-400 animate-spin" />
          </div>
        )}

        {error && (
          <p className="text-xs text-red-500 text-center py-4">{error}</p>
        )}

        {!isLoading && !error && groupedSessions.length === 0 && (
          <p className="text-xs text-slate-400 text-center py-8">
            아직 대화가 없습니다
          </p>
        )}

        {groupedSessions.map((group: SessionGroup) => (
          <div key={group.label} className="mb-3">
            <p className="text-[11px] font-medium text-slate-400 uppercase tracking-wider px-3 py-1.5">
              {group.label}
            </p>
            <div className="space-y-0.5">
              {group.sessions.map((session) => (
                <SessionItem
                  key={session.id}
                  session={session}
                  isActive={session.id === currentSessionId}
                  onSelect={handleSelectSession}
                  onRename={renameSession}
                  onDelete={deleteSession}
                />
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
