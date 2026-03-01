import logging
import sys
from typing import Any

# 로깅 포맷 정의
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def setup_logging() -> None:
    """
    기본 로깅 설정을 수행합니다.
    """
    logging.basicConfig(
        level=logging.INFO,
        format=LOG_FORMAT,
        handlers=[
            logging.StreamHandler(sys.stdout),
            # 필요한 경우 파일 핸들러 추가 가능
            # logging.FileHandler("app.log", encoding="utf-8")
        ],
    )

    # 타사 라이브러리 로그 레벨 조정 (필요 시)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    지정된 이름의 로거를 반환합니다.
    """
    return logging.getLogger(name)
