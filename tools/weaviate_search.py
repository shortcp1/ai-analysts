import weaviate
import os

def search_memory(query: str, limit: int = 5):
    """Search the agent's memory for relevant information"""
    try:
        client = weaviate.Client(os.getenv("WEAVIATE_URL"))
        
        result = client.query.get("Memory") \
            .with_near_text({"concepts": [query]}) \
            .with_limit(limit) \
            .with_additional(["certainty"]) \
            .do()
            
        if result.get("data", {}).get("Get", {}).get("Memory"):
            return result["data"]["Get"]["Memory"]
        return []
        
    except Exception as e:
        return f"Error searching memory: {str(e)}"
