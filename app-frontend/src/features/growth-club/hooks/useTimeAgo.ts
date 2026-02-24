import { useState, useEffect } from 'react';

export const formatTimeAgo = (dateString: string) => {
    // 백엔드에서 온 날짜 문자열이 UTC임을 명시하기 위해 'Z'가 없으면 추가합니다.
    const normalizedDateString = dateString.endsWith('Z') || dateString.includes('+')
        ? dateString
        : `${dateString}Z`;

    const date = new Date(normalizedDateString);
    const now = new Date();
    const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

    // 미래의 시간인 경우 (서버-클라이언트 간 미세한 시간 차이) 방금 전으로 표시
    if (diffInSeconds < 0) return '방금 전';

    if (diffInSeconds < 60) return '방금 전';
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}분 전`;
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}시간 전`;
    if (diffInSeconds < 2592000) return `${Math.floor(diffInSeconds / 86400)}일 전`;
    return date.toLocaleDateString('ko-KR');
};

export const useTimeAgo = (dateString: string) => {
    const [timeAgo, setTimeAgo] = useState(() => formatTimeAgo(dateString));

    useEffect(() => {
        const intervalId = setInterval(() => {
            setTimeAgo(formatTimeAgo(dateString));
        }, 60000);

        return () => clearInterval(intervalId);
    }, [dateString]);

    return timeAgo;
};
