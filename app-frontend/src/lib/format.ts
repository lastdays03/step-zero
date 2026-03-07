/**
 * 날짜 문자열을 상대 시간으로 포맷팅하는 유틸 함수
 */
export const formatTimeAgo = (dateString: string | Date): string => {
    let date: Date;

    if (typeof dateString === 'string') {
        if (!dateString.endsWith('Z') && !dateString.includes('+')) {
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

    if (diffInSeconds < 60) return '방금 전';
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}분 전`;
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}시간 전`;
    if (diffInSeconds < 2592000) return `${Math.floor(diffInSeconds / 86400)}일 전`;
    return date.toLocaleDateString('ko-KR');
};
