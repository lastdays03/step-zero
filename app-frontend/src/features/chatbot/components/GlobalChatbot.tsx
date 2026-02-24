"use client";

import { useChatbot } from "../hooks/useChatbot";
import { ChatFAB } from "./ChatFAB";
import { ChatPanel } from "./ChatPanel";

export function GlobalChatbot() {
  const {
    messages,
    isOpen,
    isLoading,
    error,
    input,
    setInput,
    sendMessage,
    togglePanel,
    clearHistory,
    scrollRef,
  } = useChatbot();

  return (
    <>
      {isOpen && (
        <ChatPanel
          messages={messages}
          isLoading={isLoading}
          error={error}
          input={input}
          onInputChange={setInput}
          onSend={sendMessage}
          onClear={clearHistory}
          onClose={togglePanel}
          scrollRef={scrollRef}
        />
      )}
      {!isOpen && <ChatFAB isOpen={isOpen} onClick={togglePanel} />}
    </>
  );
}
