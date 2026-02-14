from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser

from app.core.config import get_settings
from app.services.law_fetcher import LawData

class ProcessedLawData(BaseModel):
    """
    Structured output from LLM ETL process.
    """
    title: str = Field(..., description="Refined title")
    summary: str = Field(..., description="One-line summary")
    guide_text: str = Field(..., description="Founder-friendly practical guide (Markdown)")
    law_reference: str = Field(..., description="Format: [Law Name] Article X (Content)")
    category: str = Field(..., description="Category")
    original_data: LawData = Field(..., description="Original raw data reference")

class LawETLProcessor:
    def __init__(self):
        settings = get_settings()
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not set")
        
        self.llm = ChatOpenAI(
            model="gpt-4-turbo-preview",  # Use a capable model for structuring
            temperature=0,
            api_key=settings.OPENAI_API_KEY
        )
        
        # Define the prompt for structuring
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """
            You are a legal expert assistant for startup founders.
            Your task is to transform raw legal text into a practical guide while preserving the legal reference.
            
            Input Context:
            - Category: {category}
            - Title: {title}
            
            Instructions:
            1. Analyze the 'Raw Content'.
            2. Write a 'Guide Text' that explains what a founder needs to do in plain Korean. 
               - Use bullet points. 
               - Focus on "Actions" and "Requirements".
               - Tone: Professional but easy to understand.
            3. Extract the 'Law Reference' exactly as it appears or summarize it citations.
            4. Provide a one-line summary.
            
            Output Format: JSON matching the ProcessedLawData structure (excluding original_data).
            """),
            ("human", "Raw Content:\n{content}")
        ])
        
        self.parser = JsonOutputParser(pydantic_object=ProcessedLawData)

    async def process(self, law_data: LawData) -> ProcessedLawData:
        """
        Transforms raw LawData into ProcessedLawData using LLM.
        """
        from fastapi.concurrency import run_in_threadpool
        chain = self.prompt | self.llm | self.parser
        
        try:
            # Using run_in_threadpool + sync invoke for consistency with VectorStore behavior
            result = await run_in_threadpool(
                chain.invoke,
                {
                    "category": law_data.category,
                    "title": law_data.title,
                    "content": law_data.content_body[:10000]
                }
            )
            
            # Helper to ensure string
            def ensure_string(val):
                if isinstance(val, list):
                    return "\n".join(val)
                return str(val) if val else ""

            # Re-construct Pydantic object
            return ProcessedLawData(
                title=result.get("title", law_data.title),
                summary=result.get("summary", ""),
                guide_text=ensure_string(result.get("guide_text", "")),
                law_reference=ensure_string(result.get("law_reference", "")),
                category=law_data.category,
                original_data=law_data
            )
        except Exception as e:
            print(f"Error processing {law_data.title}: {e}")
            # Fallback: Return raw content as guide
            return ProcessedLawData(
                title=law_data.title,
                summary="Processing Failed",
                guide_text=f"Processing Failed. Raw:\n{law_data.content_body[:500]}...",
                law_reference="N/A",
                category=law_data.category,
                original_data=law_data
            )
