import tiktoken
import os

def estimate_costs(prompt: str, expected_response_tokens: int = 500, model: str = "gpt-4o"):
    """Estimate API costs for a request"""
    try:
        # Get encoding for the model
        if "gpt" in model.lower():
            encoding = tiktoken.encoding_for_model("gpt-4")
        else:
            encoding = tiktoken.get_encoding("cl100k_base")
        
        # Count input tokens
        input_tokens = len(encoding.encode(prompt))
        output_tokens = expected_response_tokens
        
        # Pricing (approximate, update as needed)
        pricing = {
            "gpt-4o": {"input": 0.0025, "output": 0.01},  # per 1K tokens
            "claude-3-opus": {"input": 0.015, "output": 0.075},
            "claude-3-sonnet": {"input": 0.003, "output": 0.015}
        }
        
        model_key = "gpt-4o" if "gpt" in model.lower() else "claude-3-sonnet"
        rates = pricing.get(model_key, pricing["gpt-4o"])
        
        input_cost = (input_tokens / 1000) * rates["input"]
        output_cost = (output_tokens / 1000) * rates["output"]
        total_cost = input_cost + output_cost
        
        return {
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "input_cost": round(input_cost, 4),
            "output_cost": round(output_cost, 4),
            "total_cost": round(total_cost, 4),
            "total_cost_with_buffer": round(total_cost * 1.25, 4)  # 25% buffer
        }
        
    except Exception as e:
        return f"Error estimating costs: {str(e)}"
