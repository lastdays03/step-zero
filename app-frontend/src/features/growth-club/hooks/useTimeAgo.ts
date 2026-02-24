import { useState, useEffect } from 'react';

/**
 * 실시간으로 상대 시간을 업데이트하는 훅
 * @param dateString ISO 형식의 날짜 문자열
 * @returns '방금 전', 'n분 전' 등 포맷팅된 문자열
 */
export const useTimeAgo = (dateString: string | Date) => {
    const [timeAgo, setTimeAgo] = useState('');

    useEffect(() => {
        const update = () => {
            let date: Date;

            if (typeof dateString === 'string') {
                // 서버(KST) 환경에서 naive datetime(UTC)을 보낼 때, 
                // 브라우저가 이를 로컬 시간으로 오해하여 9시간 차이가 나는 문제 해결
                if (!dateString.endsWith('Z') && !dateString.includes('+')) {
                    // T가 없는 경우(YYYY-MM-DD HH:mm:ss) 대응을 위해 T로 변환 시도
                    const isoString = dateString.includes(' ') ? dateString.replace(' ', 'T') : dateString;
                    date = new Date(isoString + 'Z');
                } else {
                    date = new Date(dateString);
                }
            } else {
                date = dateString;
            }

            const now = new Date();
            const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

            let result = '';
            let nextInterval = 60000; // 기본 1분

            if (diffInSeconds < 60) {
                result = '방금 전';
                nextInterval = 10000; // 10초마다 체크 (방금 전 -> 1분 전 전환을 위해)
            } else if (diffInSeconds < 3600) {
                result = `${Math.floor(diffInSeconds / 60)}분 전`;
                nextInterval = 60000; // 1분마다
            } else if (diffInSeconds < 86400) {
                result = `${Math.floor(diffInSeconds / 3600)}시간 전`;
                nextInterval = 3600000; // 1시간마다
            } else if (diffInSeconds < 2592000) {
                result = `${Math.floor(diffInSeconds / 86400)}일 전`;
                nextInterval = 86400000; // 1일마다
            } else {
                result = date.toLocaleDateString('ko-KR');
                nextInterval = 0; // 업데이트 중단
            }

            setTimeAgo(result);
            return nextInterval;
        };

        const firstInterval = update();

        if (firstInterval > 0) {
            const timer = setInterval(update, firstInterval);
            return () => clearInterval(timer);
        }
    }, [dateString]);

    return timeAgo;
};
