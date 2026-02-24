export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  source?: "legal_rag" | "general";
  timestamp: number;
}
