import asyncio
import os
import sys

# Add app directory to sys.path
sys.path.append(os.getcwd())

from app.services.law_fetcher import LocalFileSource

async def main():
    # Use the absolute path to .temp directory
    # Assuming we are running from app-backend, so we need to go up two levels
    root_dir = os.path.abspath(os.path.join(os.getcwd(), "../.temp"))
    
    print(f"Scanning directory: {root_dir}")
    
    source = LocalFileSource(root_dir)
    laws = await source.fetch_all_laws()
    
    print(f"\nTotal documents successfully fetched: {len(laws)}")
    
    categories = {}
    for law in laws:
        categories[law.category] = categories.get(law.category, 0) + 1
        
    print("\nDocument count by category:")
    for cat, count in categories.items():
        print(f"- {cat}: {count}")

    if laws:
        print(f"\nSample Document:\nTitle: {laws[0].title}\nCategory: {laws[0].category}\nSource: {laws[0].source_type}\nContent Preview: {laws[0].content_body[:100]}...")

if __name__ == "__main__":
    asyncio.run(main())
