"""
Hex Data Analysis Tool
This tool uses the Hex API to programmatically run Python code in a Hex notebook,
allowing for data analysis and visualization.
"""

import os
import requests

HEX_API_TOKEN = os.getenv("HEX_API_TOKEN")
HEX_PROJECT_ID = os.getenv("HEX_PROJECT_ID")

def run_data_analysis(code: str, description: str = "Data analysis"):
    """
    Run Python code in a Hex notebook project for data analysis.

    Args:
        code (str): The Python code to execute in the Hex notebook.
        description (str): A brief description of the analysis.

    Returns:
        str: A message indicating the status of the analysis run.
    """
    if not HEX_API_TOKEN or not HEX_PROJECT_ID:
        return "❌ **Hex API token or Project ID not set.** Please configure HEX_API_TOKEN and HEX_PROJECT_ID environment variables."

    headers = {
        "Authorization": f"Bearer {HEX_API_TOKEN}",
        "Content-Type": "application/json"
    }

    # API endpoint to run a project
    run_url = f"https://app.hex.tech/api/v1/project/{HEX_PROJECT_ID}/run"

    # Define the payload for the API request
    payload = {
        "notebookState": {
            "cells": [
                {
                    "id": "code_cell",
                    "type": "code",
                    "source": code
                }
            ]
        },
        "description": description
    }

    try:
        response = requests.post(run_url, headers=headers, json=payload, timeout=30)
        
        if response.status_code in [200, 201, 202]:
            run_id = response.json().get("runId")
            run_url = response.json().get("runUrl")
            return f"✅ **Hex analysis started successfully!**\n- Run ID: {run_id}\n- Track progress: {run_url}"
        else:
            return f"❌ **Error starting Hex analysis:**\n- Status: {response.status_code}\n- Response: {response.text}"
            
    except Exception as e:
        return f"❌ **An unexpected error occurred:** {e}"

# Example usage (for testing):
# if __name__ == "__main__":
#     test_code = 'import pandas as pd\ndf = pd.DataFrame({"a": [1, 2], "b": [3, 4]})\nprint(df)'
#     result = run_data_analysis(test_code, "Test data analysis")
#     print(result)
