export interface CitationSource {
  id: number;
  type: "legal_basis" | "document";
  title: string;
  url?: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  source?: "legal_rag" | "general";
  sources?: CitationSource[];
  isStreaming?: boolean;
  timestamp: number;
}
