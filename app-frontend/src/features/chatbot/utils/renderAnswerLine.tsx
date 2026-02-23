import React from "react";

const URL_PATTERN = /(https?:\/\/[^\s]+)/g;

export const renderAnswerLine = (line: string, keyPrefix: string) => {
  const parts = line.split(URL_PATTERN);
  return parts.map((part, idx) => {
    if (/^https?:\/\//.test(part)) {
      return (
        <a
          key={`${keyPrefix}-link-${idx}`}
          href={part}
          target="_blank"
          rel="noreferrer"
          className="text-blue-600 underline"
        >
          {part}
        </a>
      );
    }
    return <span key={`${keyPrefix}-text-${idx}`}>{part}</span>;
  });
};
