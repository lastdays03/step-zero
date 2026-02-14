from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_rag_query():
    print("Testing POST /api/v1/rag/query...")
    query = "일반음식점 영업신고 절차에 대해 알려줘."
    print(f"Query: {query}")
    
    response = client.post(
        "/api/v1/rag/query",
        json={"question": query}
    )
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print(f"Response: {response.json()}")
    else:
        print(f"Error: {response.text}")

if __name__ == "__main__":
    test_rag_query()
