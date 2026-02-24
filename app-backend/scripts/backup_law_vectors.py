#!/usr/bin/env python3
"""law_vectors 컬렉션을 JSON 파일로 백업하는 스크립트.

재인덱싱 전 기존 벡터 데이터를 보존하기 위해 사용한다.
백업 데이터에는 page_content, metadata (cmetadata), embedding 차원 수가 포함된다.
실제 embedding 벡터는 용량 문제로 제외하고, 메타데이터만 보존한다.

Usage:
    cd app-backend
    python -m scripts.backup_law_vectors [--output backup.json]
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import create_engine, text

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger("scripts.backup_law_vectors")

BACKUP_DIR = Path(__file__).resolve().parents[1] / ".temp" / "backups"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="law_vectors 컬렉션 백업")
    parser.add_argument(
        "--output",
        default=None,
        help="백업 파일 경로 (기본: .temp/backups/law_vectors_YYYYMMDD_HHMMSS.json)",
    )
    return parser.parse_args()


def backup() -> int:
    args = parse_args()
    settings = get_settings()

    sync_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    engine = create_engine(sync_url)

    # 컬렉션 UUID 조회
    with engine.connect() as conn:
        row = conn.execute(
            text(
                "SELECT uuid FROM langchain_pg_collection WHERE name = :name"
            ),
            {"name": "law_vectors"},
        ).fetchone()

        if not row:
            logger.error("law_vectors 컬렉션이 존재하지 않습니다.")
            return 1

        collection_id = str(row[0])
        logger.info("컬렉션 발견: uuid=%s", collection_id)

        # 임베딩 데이터 조회 (벡터 제외, 메타데이터만)
        rows = conn.execute(
            text(
                """
                SELECT id, document, cmetadata
                FROM langchain_pg_embedding
                WHERE collection_id = :cid
                ORDER BY id
                """
            ),
            {"cid": collection_id},
        ).fetchall()

    if not rows:
        logger.warning("law_vectors에 임베딩 데이터가 없습니다.")
        return 1

    records = []
    for r in rows:
        records.append({
            "id": str(r[0]),
            "document": r[1],
            "cmetadata": r[2] if isinstance(r[2], dict) else json.loads(r[2]) if r[2] else {},
        })

    backup_payload = {
        "collection_name": "law_vectors",
        "collection_id": collection_id,
        "backed_up_at": datetime.now(timezone.utc).isoformat(),
        "total_records": len(records),
        "records": records,
    }

    # 출력 경로 결정
    if args.output:
        output_path = Path(args.output)
    else:
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = BACKUP_DIR / f"law_vectors_{timestamp}.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(backup_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    logger.info("백업 완료: %d건 → %s", len(records), output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(backup())
