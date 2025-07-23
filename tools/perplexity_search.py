import requests
import os
import json
from tools.weaviate_storage import store_in_weaviate

def research_topic(query: str, focus: str = "comprehensive"):
    """
    Use Perplexity API to research a topic with real data & URLs.
    Store the result and citations in Weaviate Memory.
    """
    try:
        api_key = os.getenv("PERPLEXITY_API_KEY")
        if not api_key:
            print("⚠️ Missing PERPLEXITY_API_KEY.")
            return "⚠️ Missing PERPLEXITY_API_KEY."

        url = "https://api.perplexity.ai/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        system_prompt = (
            f"You are a research analyst. Provide {focus} research with:\n"
            "1. Exact market size (USD) & CAGR %\n"
            "2. Key competitors with approximate market share %\n"
            "3. Risks & growth drivers\n"
            "4. Always include at least 3 reliable URLs as 'Sources:' at the end."
        )

        payload = {
            "model": "sonar-pro",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            "temperature": 0.1
        }

        # DEBUG: Show payload
        print("\n=== DEBUG: Sending Perplexity request ===")
        print(json.dumps(payload, indent=2))

        response = requests.post(url, json=payload, headers=headers, timeout=60)
        print(f"DEBUG Perplexity status: {response.status_code}")
        print(f"DEBUG Raw Perplexity response:\n{response.text}\n")

        response.raise_for_status()
        result = response.json()

        if "choices" not in result:
            print("⚠️ Perplexity returned no valid result")
            return "⚠️ No valid Perplexity result."

        content = result["choices"][0]["message"]["content"]
        print("\n=== DEBUG: Perplexity Content ===")
        print(content)

        # Extract any URLs as citations
        citations = []
        for line in content.splitlines():
            if "http" in line:
                citations.extend([w.strip(" ,.") for w in line.split() if w.startswith("http")])
        citations = list(set(citations))  # remove duplicates

        print("\n=== DEBUG: Citations extracted ===")
        print(citations)

        # Store in Weaviate Memory
        print("\n=== DEBUG: Storing in Weaviate ===")
        store_in_weaviate(
            topic=query,
            content=content,
            citations=citations,
            category="market-research"
        )

        return content

    except Exception as e:
        print(f"❌ Error in research_topic: {e}")
        return f"❌ Error researching topic: {str(e)}"
