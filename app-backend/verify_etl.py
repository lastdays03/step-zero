import asyncio
import os
import sys
from dotenv import load_dotenv

# Load env variables (API Key)
load_dotenv()

# Add app directory to sys.path
sys.path.append(os.getcwd())

from app.services.law_fetcher import LocalFileSource
from app.services.law_etl import LawETLProcessor

async def main():
    root_dir = os.path.abspath(os.path.join(os.getcwd(), "../.temp"))
    print(f"Source Directory: {root_dir}")
    
    # 1. Fetch
    source = LocalFileSource(root_dir)
    laws = await source.fetch_all_laws()
    
    if not laws:
        print("No laws found.")
        return

    # Pick a sample (preferably a PDF law because MD is already structured in theory, but let's test a raw one)
    # Try to find a PDF file if possible
    sample_law = next((law for law in laws if law.metadata.get("extension") == ".pdf"), laws[0])
    
    print(f"\n--- Processing Sample: {sample_law.title} ---")
    print(f"Category: {sample_law.category}")
    print(f"Original Length: {len(sample_law.content_body)} chars")
    
    # 2. ETL
    try:
        etl = LawETLProcessor()
        processed_data = await etl.process(sample_law)
        
        print("\n=== ETL Result ===")
        print(f"Title: {processed_data.title}")
        print(f"Summary: {processed_data.summary}")
        print("\n[Guide Text Preview]")
        print(processed_data.guide_text[:300] + "...")
        print("\n[Law Reference Preview]")
        print(str(processed_data.law_reference)[:300] + "...")
        
    except Exception as e:
        print(f"ETL Failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
