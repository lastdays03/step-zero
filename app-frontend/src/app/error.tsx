'use client';

import { useEffect } from 'react';
import { RefreshCcw, Home, AlertCircle } from 'lucide-react';
import Link from 'next/link';

export default function Error({
    error,
    reset,
}: {
    error: Error & { digest?: string };
    reset: () => void;
}) {
    useEffect(() => {
        // 서버사이드 로깅 서비스가 있다면 여기서 호출
        console.error('Unhandled Application Error:', error);
    }, [error]);

    return (
        <div className="min-h-screen bg-background flex items-center justify-center p-4 font-sans">
            <div className="premium-card max-w-md w-full p-8 text-center space-y-6">
                <div className="mx-auto w-16 h-16 bg-destructive/10 rounded-full flex items-center justify-center text-destructive">
                    <AlertCircle size={32} />
                </div>

                <div className="space-y-2">
                    <h2 className="text-2xl font-bold tracking-tight text-foreground">
                        문제가 발생했습니다
                    </h2>
                    <p className="text-muted-foreground">
                        예기치 못한 오류가 발생하여 요청을 처리할 수 없습니다.<br />
                        불편을 드려 죄송합니다.
                    </p>
                </div>

                <div className="pt-4 flex flex-col sm:flex-row gap-3">
                    <button
                        onClick={() => reset()}
                        className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2.5 bg-primary text-primary-foreground rounded-xl font-medium transition-all hover:bg-primary/90 hover:scale-[1.02] active:scale-[0.98]"
                    >
                        <RefreshCcw size={18} />
                        다시 시도
                    </button>

                    <Link
                        href="/dashboard"
                        className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2.5 bg-secondary text-secondary-foreground rounded-xl font-medium transition-all hover:bg-secondary/80 hover:scale-[1.02] active:scale-[0.98]"
                    >
                        <Home size={18} />
                        홈으로 가기
                    </Link>
                </div>

                {error.digest && (
                    <p className="text-[10px] text-muted-foreground mt-4 opacity-50 uppercase font-mono">
                        Error ID: {error.digest}
                    </p>
                )}
            </div>
        </div>
    );
}
