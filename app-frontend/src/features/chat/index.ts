// types
export type {
  IntentCategory,
  CitationSource,
  ChatMessage,
  ChatSession,
  SSEEventType,
  SSEEvent,
  TokenEvent,
  SourcesEvent,
  MetaEvent,
  IntentEvent,
  WarningEvent,
  DoneEvent,
  ErrorEvent,
  SessionListResponse,
  MessageListResponse,
} from "./types";

// SSE 유틸
export { getApiBaseUrl } from "@/lib/env";
export { getAuthHeaders, tryRefreshToken } from "@/lib/sse-auth";
export { parseSSELine } from "./utils/sse";

// Provider
export { ChatProvider, useChatProvider } from "./providers/ChatProvider";
export type { RoadmapContext, ChatProviderValue } from "./providers/ChatProvider";

// Hooks
export { useChat } from "./hooks/useChat";
export type { UseChatReturn } from "./hooks/useChat";
export { useSessions } from "./hooks/useSessions";
export type { SessionGroup } from "./hooks/useSessions";

// Components
export { ChatWidget } from "./components/ChatWidget";
export { ChatFAB } from "./components/ChatFAB";
export { ChatPanel } from "./components/ChatPanel";
export { ChatMessages } from "./components/ChatMessages";
export { ChatMessage as ChatMessageBubble } from "./components/ChatMessage";
export { ChatInput } from "./components/ChatInput";
export { ChatHistory } from "./components/ChatHistory";
export { ChatEmptyState } from "./components/ChatEmptyState";
export { SourcesCard } from "./components/SourcesCard";
export { ChatWarningBadge } from "./components/ChatWarningBadge";

// 유틸
export { renderCitationLine } from "./utils/citations";

// API 클라이언트
export {
  fetchSessions,
  createSession,
  fetchMessages,
  updateSessionTitle,
  deleteSession,
} from "./utils/api";
