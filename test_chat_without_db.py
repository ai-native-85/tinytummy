#!/usr/bin/env python3
"""
Database-free end-to-end test for /chat/query using FastAPI TestClient.
Bypasses DB via dependency overrides and simulates JWT + GPT response.
"""

import os
from dotenv import load_dotenv

load_dotenv()

from fastapi.testclient import TestClient

from main import app
from app.database import get_db
from app.auth.jwt import get_current_user


class _FakeUser:
    def __init__(self, user_id: str):
        self.id = user_id
        self.email = "test@example.com"
        self.subscription_tier = "premium"


class _FakeSession:
    def __init__(self, user_id: str):
        self._user = _FakeUser(user_id)

    # Minimal query/ORM simulation used by chat route
    def query(self, model):
        # Return a simple object that supports filter(...).first()
        class _Query:
            def __init__(self, model, user_obj):
                self.model = model
                self.user_obj = user_obj

            def filter(self, *args, **kwargs):
                return self

            def first(self):
                from app.models.user import User
                from app.models.chat import ChatSession
                # Return a premium user for User queries
                if self.model is User:
                    return self.user_obj
                # Return a non-None chat session to bypass insert path
                if self.model is ChatSession:
                    class _Session:
                        id = "fake-session-id"
                    return _Session()
                # For other models (e.g., Child) return None so logic skips
                return None

        return _Query(model, self._user)

    def add(self, obj):
        pass

    def commit(self):
        pass

    def refresh(self, obj):
        # Ensure session id exists if needed
        if not getattr(obj, "id", None):
            setattr(obj, "id", "fake-session-id")

    def close(self):
        pass


def _override_get_db():
    fake = _FakeSession(user_id="68251b05-9143-4c59-80d1-6d1a55885f67")
    try:
        yield fake
    finally:
        fake.close()


def _override_get_current_user():
    # Return fixed user id; JWT is not validated in this override
    return "68251b05-9143-4c59-80d1-6d1a55885f67"


def _mock_rag_service():
    # Monkeypatch RAGService.generate_rag_response to avoid network
    from app.services import rag_service as rag_module

    def fake_generate_rag_response(self, query: str, user_context: str = ""):
        return {
            "response": "Based on WHO and CDC guidance, offer iron-rich purees and soft finger foods. Introduce one new food at a time and avoid honey before age 1.",
            "context_used": [
                {
                    "title": "WHO Infant Feeding Guidelines",
                    "source": "WHO",
                    "region": "Global",
                    "age_group": "6-12 months",
                    "topic": "Feeding",
                    "content": "Start complementary feeding at 6 months; continue breastfeeding...",
                    "score": 0.91,
                },
                {
                    "title": "CDC Baby Nutrition",
                    "source": "CDC",
                    "region": "US",
                    "age_group": "6-12 months",
                    "topic": "Nutrition",
                    "content": "Introduce a variety of textures; avoid honey...",
                    "score": 0.86,
                },
            ],
            "confidence": "high",
            "sources": ["WHO", "CDC"],
        }

    rag_module.RAGService.generate_rag_response = fake_generate_rag_response


def run_test() -> bool:
    # Apply dependency overrides
    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_get_current_user

    # Mock RAG to avoid network calls while preserving endpoint flow
    _mock_rag_service()

    client = TestClient(app)

    # Hardcoded JWT; not validated due to dependency override
    headers = {"Authorization": "Bearer dev-test-token"}
    payload = {"user_input": "What should I feed my 9-month-old baby?", "child_id": None}

    resp = client.post("/chat/query", json=payload, headers=headers)
    print(f"Status: {resp.status_code}")
    if resp.status_code != 200:
        print(f"Body: {resp.text}")
        return False

    data = resp.json()
    print(f"Response: {data.get('response', '')}")
    meta = data.get("metadata", {})
    print(f"Confidence: {meta.get('rag_confidence')}")
    print(f"Sources: {meta.get('rag_sources')}")
    print(f"Context Count: {meta.get('context_count')}")

    # Assertions
    assert data["response"], "Expected non-empty response"
    assert meta.get("context_count", 0) >= 1, "Expected at least one context item"
    assert isinstance(meta.get("rag_sources", []), list), "Expected sources list"

    return True


if __name__ == "__main__":
    print("🚀 Running database-free /chat/query test...\n")
    ok = run_test()
    print("\n📊 Result:")
    print(f"  Chat Endpoint: {'✅ PASS' if ok else '❌ FAIL'}")
    if ok:
        print("\n🎉 Test passed without any database access.")
    else:
        print("\n⚠️ Test failed. See output above.")