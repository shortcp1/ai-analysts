import requests
import os
from datetime import datetime, timezone

WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://localhost:8080")

def store_in_weaviate(topic: str, content: str, citations=None, category: str = "general"):
    """
    Store a research entry into the Weaviate 'Memory' class safely.
    Fixes timestamp formatting to RFC3339.
    """
    # ✅ Normalize citations
    if not citations:
        citations = ["No citations provided"]
    elif isinstance(citations, str):
        citations = [citations]
    elif not isinstance(citations, list):
        citations = [str(citations)]

    # ✅ Truncate overly long content
    MAX_LENGTH = 15000
    if len(content) > MAX_LENGTH:
        print(f"⚠️ Content too long ({len(content)} chars), truncating.")
        content = content[:MAX_LENGTH] + "\n...[TRUNCATED]"

    # ✅ Correct RFC3339 timestamp
    timestamp_rfc3339 = datetime.now(timezone.utc).isoformat(timespec="seconds")

    payload = {
        "class": "Memory",
        "properties": {
            "topic": str(topic),
            "content": str(content),
            "citations": [str(c) for c in citations],
            "category": str(category),
            "timestamp": timestamp_rfc3339  # RFC3339 compliant
        }
    }

    print("\n=== DEBUG: Attempting to store in Weaviate ===")
    print(payload)

    try:
        resp = requests.post(f"{WEAVIATE_URL}/v1/objects", json=payload, timeout=10)
        print(f"DEBUG Weaviate status: {resp.status_code}")
        print(f"DEBUG Weaviate response: {resp.text}")
        resp.raise_for_status()
        print(f"✅ Successfully stored research for topic: {topic}")
        return resp.json()

    except requests.exceptions.RequestException as req_err:
        print(f"❌ Network/connection error with Weaviate: {req_err}")
        return None

    except Exception as e:
        print(f"❌ Unexpected error storing in Weaviate: {e}")
        return None
