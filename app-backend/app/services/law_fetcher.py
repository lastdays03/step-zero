from abc import ABC, abstractmethod
from typing import List, Optional
from pydantic import BaseModel, Field
from enum import Enum

class SourceType(str, Enum):
    LOCAL = "LOCAL"
    API = "API"

class LawData(BaseModel):
    """
    Standardized data model for legal documents (Laws, Ordinances, Guides).
    Used by both LocalFileSource and MolegApiSource.
    """
    title: str = Field(..., description="법령 또는 가이드의 제목")
    category: str = Field(..., description="업종 카테고리 (예: 휴게음식점, 일반음식점)")
    content_body: str = Field(..., description="본문 내용 (Raw Text or Markdown)")
    source_type: SourceType = Field(..., description="데이터 출처 유형")
    file_path: Optional[str] = Field(None, description="로컬 파일 경로 (API인 경우 None)")
    url: Optional[str] = Field(None, description="원본 링크 (API인 경우 URL)")
    metadata: dict = Field(default_factory=dict, description="기타 메타데이터 (시행일자, 법령ID 등)")

class LawDataSource(ABC):
    """
    Abstract Base Class for Data Ingestion Strategy.
    Enables switching between Local Files and API without changing core logic.
    """
    
    @abstractmethod
    async def fetch_all_laws(self) -> List[LawData]:
        """
        Fetches all available legal data from the source.
        Returns a unified list of LawData objects.
        """
        pass

import os
import pdfplumber
from pathlib import Path

class LocalFileSource(LawDataSource):
    """
    Ingestion Strategy for Local Files (.pdf, .md).
    Scans the .temp directory and extracts content.
    """
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)

    def _extract_text_from_pdf(self, file_path: Path) -> str:
        try:
            with pdfplumber.open(file_path) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() + "\n"
                return text
        except Exception as e:
            print(f"Error reading PDF {file_path}: {e}")
            return ""

    def _extract_text_from_md(self, file_path: Path) -> str:
        try:
            return file_path.read_text(encoding="utf-8")
        except Exception as e:
            print(f"Error reading MD {file_path}: {e}")
            return ""

    def _get_category_from_path(self, file_path: Path) -> str:
        # Example path: /.../.temp/휴게음식점/영업신고/file.pdf
        # Relative path: 휴게음식점/영업신고/file.pdf
        # Category: 휴게음식점
        try:
            relative_path = file_path.relative_to(self.root_dir)
            return relative_path.parts[0]
        except Exception:
            return "Uncategorized"

    async def fetch_all_laws(self) -> List[LawData]:
        results = []
        if not self.root_dir.exists():
            print(f"Warning: Directory {self.root_dir} does not exist.")
            return results

        # Walk through the directory
        for file_path in self.root_dir.rglob("*"):
            if not file_path.is_file():
                continue
            
            # Skip hidden files
            if file_path.name.startswith("."):
                continue

            if file_path.suffix.lower() == ".pdf":
                content = self._extract_text_from_pdf(file_path)
            elif file_path.suffix.lower() == ".md":
                content = self._extract_text_from_md(file_path)
            else:
                continue # Skip other formats for now

            if not content.strip():
                continue

            category = self._get_category_from_path(file_path)
            
            law_data = LawData(
                title=file_path.stem, # Filename without extension
                category=category,
                content_body=content,
                source_type=SourceType.LOCAL,
                file_path=str(file_path),
                metadata={
                    "filename": file_path.name,
                    "extension": file_path.suffix
                }
            )
            results.append(law_data)
            
        print(f"Fetched {len(results)} documents from {self.root_dir}")
        return results
