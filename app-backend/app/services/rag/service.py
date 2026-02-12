
from typing import Any

class RagService:
    def __init__(self, chain: Any = None):
        self.chain = chain

    async def query(self, question: str) -> str:
        if self.chain:
            response = await self.chain.ainvoke({"question": question})
            return response.get("answer", "")
        return "No chain provided"
