// ------------------------------------------------------------------ //
//  채팅 도메인 타입 (BE schemas.py 매칭)
// ------------------------------------------------------------------ //

/** 의도 분류 5카테고리 */
export type IntentCategory =
  | "current_step"
  | "other_step"
  | "legal_general"
  | "general"
  | "out_of_scope";

/** 인용 출처 */
export interface CitationSource {
  id: number;
  type: string;
  title: string;
  url?: string;
}

/** 채팅 메시지 */
export interface ChatMessage {
  id?: number;
  role: "user" | "assistant";
  content: string;
  sources?: CitationSource[];
  intent_category?: IntentCategory;
  isStreaming?: boolean;
  warning?: { code: string; message: string };
  created_at?: string;
}

/** 채팅 세션 */
export interface ChatSession {
  id: string;
  title: string | null;
  message_count: number;
  roadmap_id?: string | null;
  step_id?: number | null;
  created_at: string;
  updated_at: string;
}

// ------------------------------------------------------------------ //
//  SSE 이벤트 타입
// ------------------------------------------------------------------ //

export type SSEEventType =
  | "token"
  | "sources"
  | "meta"
  | "intent"
  | "warning"
  | "done"
  | "error";

export interface SSEEvent {
  type: SSEEventType;
  [key: string]: unknown;
}

export interface TokenEvent extends SSEEvent {
  type: "token";
  token: string;
}

export interface SourcesEvent extends SSEEvent {
  type: "sources";
  sources: CitationSource[];
}

export interface MetaEvent extends SSEEvent {
  type: "meta";
  session_id: string;
  message_id?: number;
}

export interface IntentEvent extends SSEEvent {
  type: "intent";
  category: IntentCategory;
  step_title?: string;
}

export interface WarningEvent extends SSEEvent {
  type: "warning";
  code: string;
  message: string;
}

export interface DoneEvent extends SSEEvent {
  type: "done";
}

export interface ErrorEvent extends SSEEvent {
  type: "error";
  code: string;
  message: string;
}

// ------------------------------------------------------------------ //
//  API 응답 타입 (BE SessionListResponse / MessageListResponse 매칭)
// ------------------------------------------------------------------ //

export interface SessionListResponse {
  sessions: ChatSession[];
  total: number;
}

export interface MessageListResponse {
  messages: ChatMessage[];
  total: number;
}
