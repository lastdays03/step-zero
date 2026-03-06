'use client';

import { useEffect, useRef } from 'react';
import { getApiBaseUrl } from '@/lib/env';
import { getAuthHeaders, tryRefreshToken } from '@/features/chat/utils/sse';

interface UseNotificationSSEOptions {
    enabled: boolean;
    onMessage: () => void;
}

/**
 * SSE hook that listens to /notifications/stream and calls onMessage
 * whenever a new notification event arrives, triggering a re-fetch.
 */
export function useNotificationSSE({ enabled, onMessage }: UseNotificationSSEOptions) {
    const onMessageRef = useRef(onMessage);
    onMessageRef.current = onMessage;

    useEffect(() => {
        if (!enabled) return;

        let cancelled = false;
        let reader: ReadableStreamDefaultReader<Uint8Array> | null = null;

        async function connect() {
            const baseUrl = getApiBaseUrl();
            const url = `${baseUrl}/notifications/stream`;

            try {
                const headers = getAuthHeaders();
                // Remove Content-Type for SSE (not sending JSON body)
                delete headers["Content-Type"];

                const response = await fetch(url, {
                    headers,
                    signal: AbortSignal.timeout(300_000), // 5 min timeout
                });

                if (response.status === 401) {
                    const refreshed = await tryRefreshToken();
                    if (refreshed && !cancelled) {
                        // Retry with new token
                        setTimeout(connect, 100);
                    }
                    return;
                }

                if (!response.ok || !response.body) return;

                reader = response.body.getReader();
                const decoder = new TextDecoder();
                let buffer = '';

                while (!cancelled) {
                    const { done, value } = await reader.read();
                    if (done) break;

                    buffer += decoder.decode(value, { stream: true });
                    const lines = buffer.split('\n');
                    buffer = lines.pop() || '';

                    for (const line of lines) {
                        if (!line.startsWith('data: ')) continue;
                        try {
                            const data = JSON.parse(line.slice(6));
                            if (data.type === 'new_notification') {
                                onMessageRef.current();
                            }
                        } catch {
                            // ignore parse errors
                        }
                    }
                }
            } catch {
                // Connection lost — retry after delay
            } finally {
                reader?.cancel().catch(() => {});
                reader = null;
            }

            // Auto-reconnect after 3 seconds
            if (!cancelled) {
                await new Promise((r) => setTimeout(r, 3000));
                if (!cancelled) connect();
            }
        }

        connect();

        return () => {
            cancelled = true;
            reader?.cancel().catch(() => {});
        };
    }, [enabled]);
}
