"use client";

import { useChatbot } from "../hooks/useChatbot";
import { ChatFAB } from "./ChatFAB";
import { ChatPanel } from "./ChatPanel";

export function GlobalChatbot() {
  const {
    messages,
    isOpen,
    isStreaming,
    isLoading,
    error,
    input,
    setInput,
    sendMessage,
    togglePanel,
    clearHistory,
    scrollRef,
    hasCoachContext,
    stepTitle,
  } = useChatbot();

  return (
    <>
      {isOpen && (
        <ChatPanel
          messages={messages}
          isStreaming={isStreaming}
          isLoading={isLoading}
          error={error}
          input={input}
          hasCoachContext={hasCoachContext}
          stepTitle={stepTitle}
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
