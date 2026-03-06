"use client";

import { useState, useCallback, useEffect, useMemo, useRef } from "react";
import type { ChatSession } from "../types";
import {
  fetchSessions,
  createSession,
  updateSessionTitle,
  deleteSession,
} from "../utils/api";
import {
  useChatProvider,
  type SessionPreview,
} from "../providers/ChatProvider";

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
  const {
    setCurrentSessionId,
    sessionListVersion,
    sessionPreview,
    sessionPreviewVersion,
  } = useChatProvider();
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const sessionPreviewRef = useRef<SessionPreview | null>(sessionPreview);
  const sessionPreviewVersionRef = useRef(sessionPreviewVersion);

  // 세션 목록 로드
  const loadSessions = useCallback(async (limit = 50, offset = 0) => {
    setIsLoading(true);
    setError(null);
    const previewVersionAtStart = sessionPreviewVersionRef.current;
    try {
      const res = await fetchSessions(limit, offset);
      const latestPreview = sessionPreviewRef.current;
      const previewChangedDuringLoad =
        sessionPreviewVersionRef.current !== previewVersionAtStart;

      setSessions(
        previewChangedDuringLoad && latestPreview
          ? upsertSession(res.sessions, latestPreview)
          : res.sessions,
      );
    } catch {
      setError("세션 목록을 불러오지 못했습니다.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    sessionPreviewRef.current = sessionPreview;
    sessionPreviewVersionRef.current = sessionPreviewVersion;
  }, [sessionPreview, sessionPreviewVersion]);

  useEffect(() => {
    if (sessionPreviewVersion === 0 || !sessionPreview) return;
    setSessions((prev) => upsertSession(prev, sessionPreview));
  }, [sessionPreview, sessionPreviewVersion]);

  useEffect(() => {
    if (sessionListVersion === 0) return;
    void loadSessions();
  }, [sessionListVersion, loadSessions]);

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

function upsertSession(
  sessions: ChatSession[],
  preview: SessionPreview,
): ChatSession[] {
  const existing = sessions.find((session) => session.id === preview.id);

  const nextSession: ChatSession = existing
    ? {
        ...existing,
        title: existing.title ?? preview.title ?? null,
        message_count: Math.max(
          existing.message_count,
          preview.message_count ?? existing.message_count,
        ),
        roadmap_id: existing.roadmap_id ?? preview.roadmap_id ?? null,
        step_id: existing.step_id ?? preview.step_id ?? null,
        created_at: existing.created_at,
        updated_at: isAfter(preview.updated_at, existing.updated_at)
          ? preview.updated_at
          : existing.updated_at,
      }
    : {
        id: preview.id,
        title: preview.title ?? null,
        message_count: preview.message_count ?? 0,
        roadmap_id: preview.roadmap_id ?? null,
        step_id: preview.step_id ?? null,
        created_at: preview.created_at ?? preview.updated_at,
        updated_at: preview.updated_at,
      };

  return [
    nextSession,
    ...sessions.filter((session) => session.id !== preview.id),
  ];
}

function isAfter(left: string, right: string): boolean {
  return new Date(left).getTime() > new Date(right).getTime();
}
