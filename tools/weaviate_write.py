import weaviate
import os
import uuid
from datetime import datetime

def store_memory(content: str, memory_type: str, metadata: dict = None):
    """Store information in the agent's memory"""
    try:
        client = weaviate.Client(os.getenv("WEAVIATE_URL"))
        
        # Create schema if it doesn't exist
        try:
            client.schema.get_class("Memory")
        except:
            schema = {
                "class": "Memory",
                "properties": [
                    {"name": "content", "dataType": ["text"]},
                    {"name": "type", "dataType": ["string"]},
                    {"name": "timestamp", "dataType": ["string"]},
                    {"name": "metadata", "dataType": ["text"]}
                ]
            }
            client.schema.create_class(schema)
        
        # Store the memory
        memory_obj = {
            "content": content,
            "type": memory_type,
            "timestamp": datetime.now().isoformat(),
            "metadata": str(metadata or {})
        }
        
        result = client.data_object.create(memory_obj, "Memory", uuid.uuid4())
        return f"Memory stored successfully: {result}"
        
    except Exception as e:
        return f"Error storing memory: {str(e)}"
