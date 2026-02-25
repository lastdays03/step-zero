#!/usr/bin/env bash
#
# reset_migrations.sh
# 마이그레이션 통합 실행 스크립트
#
# 용도:
#   1) 새 DB에 처음부터 테이블 생성  → ./scripts/reset_migrations.sh fresh
#   2) 기존 DB에 버전만 stamp          → ./scripts/reset_migrations.sh stamp
#   3) autogenerate로 모델 diff 검증  → ./scripts/reset_migrations.sh verify
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"
cd "$BACKEND_DIR"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()  { echo -e "${GREEN}[OK]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
err()  { echo -e "${RED}[ERROR]${NC} $1" >&2; }

usage() {
    cat <<EOF
Usage: $0 <command>

Commands:
  fresh    새 DB에 마이그레이션 전체 적용 (upgrade head)
  stamp    기존 DB 스키마는 유지하고 alembic_version만 최신으로 갱신
  verify   autogenerate로 모델과 DB 차이 검증 (diff 없으면 성공)
  status   현재 마이그레이션 상태 확인
  history  마이그레이션 체인 출력

EOF
    exit 1
}

check_env() {
    if [ ! -f ".env" ] && [ -z "${DATABASE_URL:-}" ]; then
        err ".env 파일 또는 DATABASE_URL 환경변수가 필요합니다."
        exit 1
    fi
}

cmd_status() {
    echo "=== Alembic Current ==="
    alembic current
    echo ""
    echo "=== Alembic Heads ==="
    alembic heads
}

cmd_history() {
    echo "=== Migration History ==="
    alembic history --verbose
}

cmd_fresh() {
    check_env
    echo "=== 새 DB에 마이그레이션 적용 ==="
    echo "마이그레이션 체인:"
    alembic history --indicate-current 2>/dev/null || true
    echo ""

    echo "upgrade head 실행 중..."
    alembic upgrade head
    log "마이그레이션 완료!"

    echo ""
    cmd_status
}

cmd_stamp() {
    check_env
    echo "=== 기존 DB에 alembic_version stamp ==="
    warn "이 명령은 DB 스키마를 변경하지 않고 alembic_version 테이블만 업데이트합니다."
    echo ""

    echo "현재 상태:"
    alembic current 2>/dev/null || echo "(alembic_version 테이블 없음)"
    echo ""

    read -p "HEAD(006_notification)로 stamp 하시겠습니까? [y/N] " confirm
    if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
        echo "취소됨."
        exit 0
    fi

    alembic stamp head
    log "stamp 완료! 현재 버전:"
    alembic current
}

cmd_verify() {
    check_env
    echo "=== 모델 ↔ DB 스키마 diff 검증 ==="

    TEMP_FILE=$(mktemp /tmp/alembic_verify_XXXXXX.py)
    alembic revision --autogenerate -m "verify_no_diff" 2>&1 | tee /dev/stderr

    # 마지막으로 생성된 파일 찾기
    LATEST=$(ls -t alembic/versions/*.py 2>/dev/null | head -1)
    if [ -z "$LATEST" ]; then
        err "마이그레이션 파일을 찾을 수 없습니다."
        exit 1
    fi

    # upgrade() 함수 내용 확인
    if grep -qE '^\s+pass$' "$LATEST" || ! grep -qE '^\s+op\.' "$LATEST"; then
        log "모델과 DB 스키마가 일치합니다! (diff 없음)"
        rm -f "$LATEST"
    else
        warn "모델과 DB 사이에 차이가 발견되었습니다:"
        echo "  파일: $LATEST"
        echo "  내용을 확인하세요."
        echo ""
        grep -A 50 'def upgrade' "$LATEST" | head -60
    fi

    rm -f "$TEMP_FILE"
}

# -- Main --
if [ $# -lt 1 ]; then
    usage
fi

case "$1" in
    fresh)   cmd_fresh   ;;
    stamp)   cmd_stamp   ;;
    verify)  cmd_verify  ;;
    status)  cmd_status  ;;
    history) cmd_history ;;
    *)       usage       ;;
esac
