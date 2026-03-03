"use client";

import { useState, useCallback, useEffect, useMemo, useRef } from "react";
import type { ChatSession } from "../types";
import {
  fetchSessions,
  createSession,
  updateSessionTitle,
  deleteSession,
} from "../utils/api";
import { useChatProvider } from "../providers/ChatProvider";

// ------------------------------------------------------------------ //
//  타입
// ------------------------------------------------------------------ //

export interface SessionGroup {
  label: string; // '오늘', '어제', '이전'
  sessions: ChatSession[];
}

// ------------------------------------------------------------------ //
//  Hook
// ------------------------------------------------------------------ //

export function useSessions() {
  const { currentSessionId, setCurrentSessionId } = useChatProvider();
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 세션 목록 로드
  const loadSessions = useCallback(async (limit = 50, offset = 0) => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetchSessions(limit, offset);
      setSessions(res.sessions);
    } catch {
      setError("세션 목록을 불러오지 못했습니다.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  // 서버에서 새 세션 생성 시 (null→non-null) 목록 자동 갱신
  const prevSessionIdRef = useRef<string | null>(currentSessionId);
  useEffect(() => {
    if (prevSessionIdRef.current === null && currentSessionId !== null) {
      loadSessions();
    }
    prevSessionIdRef.current = currentSessionId;
  }, [currentSessionId, loadSessions]);

  // 새 세션 생성
  const handleCreateSession = useCallback(async () => {
    setError(null);
    try {
      const session = await createSession();
      setSessions((prev) => [session, ...prev]);
      setCurrentSessionId(session.id);
      return session;
    } catch {
      setError("새 세션을 생성하지 못했습니다.");
      return null;
    }
  }, [setCurrentSessionId]);

  // 세션 이름 변경
  const handleRenameSession = useCallback(
    async (id: string, title: string) => {
      setError(null);
      try {
        const updated = await updateSessionTitle(id, title);
        setSessions((prev) =>
          prev.map((s) => (s.id === id ? { ...s, title: updated.title } : s)),
        );
      } catch {
        setError("세션 이름을 변경하지 못했습니다.");
      }
    },
    [],
  );

  // 세션 삭제
  const handleDeleteSession = useCallback(async (id: string) => {
    setError(null);
    try {
      await deleteSession(id);
      setSessions((prev) => prev.filter((s) => s.id !== id));
    } catch {
      setError("세션을 삭제하지 못했습니다.");
    }
  }, []);

  // 날짜별 그룹핑
  const groupedSessions = useMemo((): SessionGroup[] => {
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    const todaySessions: ChatSession[] = [];
    const yesterdaySessions: ChatSession[] = [];
    const olderSessions: ChatSession[] = [];

    sessions.forEach((session) => {
      const date = new Date(session.updated_at || session.created_at);
      if (isSameDay(date, today)) todaySessions.push(session);
      else if (isSameDay(date, yesterday)) yesterdaySessions.push(session);
      else olderSessions.push(session);
    });

    const groups: SessionGroup[] = [];
    if (todaySessions.length)
      groups.push({ label: "오늘", sessions: todaySessions });
    if (yesterdaySessions.length)
      groups.push({ label: "어제", sessions: yesterdaySessions });
    if (olderSessions.length)
      groups.push({ label: "이전", sessions: olderSessions });
    return groups;
  }, [sessions]);

  return {
    sessions,
    groupedSessions,
    isLoading,
    error,
    loadSessions,
    createSession: handleCreateSession,
    renameSession: handleRenameSession,
    deleteSession: handleDeleteSession,
  };
}

// ------------------------------------------------------------------ //
//  유틸
// ------------------------------------------------------------------ //

export function isSameDay(a: Date, b: Date): boolean {
  return (
    a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate()
  );
}
