"use client";

import { useChatProvider } from "../providers/ChatProvider";
import { ChatFAB } from "./ChatFAB";
import { ChatPanel } from "./ChatPanel";

export function ChatWidget() {
  const { isPanelOpen } = useChatProvider();

  return (
    <div data-testid="chat-widget" data-state={isPanelOpen ? "open" : "closed"}>
      {isPanelOpen ? <ChatPanel /> : <ChatFAB />}
    </div>
  );
}
