"""
Hex Notebook Interface for Analyst Crew
This module provides a simple interface to run and interact with the analyst crew
from within a Hex data notebook.
"""

import requests
import time
from IPython.display import display, Markdown

class HexCrewInterface:
    def __init__(self, server_url="http://127.0.0.1:8000", user_id=None):
        self.server_url = server_url
        self.user_id = user_id or f"hex_user_{int(time.time())}"
        self._check_server_status()

    def _check_server_status(self):
        """Check if the backend server is online."""
        try:
            response = requests.get(f"{self.server_url}/health", timeout=5)
            if response.status_code == 200:
                display(Markdown("✅ **Analyst Crew Server is online and ready.**"))
            else:
                display(Markdown(f"⚠️ **Server returned status {response.status_code}.** Please check the server logs."))
        except requests.ConnectionError:
            display(Markdown("❌ **Could not connect to Analyst Crew server.**"))
            display(Markdown("Please ensure the server is running with `python slack_server.py` and is accessible."))

    def start_analysis(self, business_question: str):
        """
        Kick off a new analysis from a Hex notebook cell.
        
        Args:
            business_question (str): The question or topic for the analyst crew.
        """
        display(Markdown(f"🚀 **Kicking off analysis for:** '{business_question}'"))
        
        response = requests.post(
            f"{self.server_url}/slack",
            data={"text": business_question, "user_id": self.user_id}
        )
        
        self._handle_response(response)

    def send_response(self, response_text: str):
        """
        Send a response to the analyst crew during an interactive session.
        
        Args:
            response_text (str): Your response to the crew's questions.
        """
        display(Markdown(f"💬 **Sending response:** '{response_text}'"))
        
        response = requests.post(
            f"{self.server_url}/slack",
            data={"text": response_text, "user_id": self.user_id}
        )
        
        self._handle_response(response)

    def _handle_response(self, response):
        """Process and display the response from the server."""
        if response.status_code == 200:
            result = response.json()
            display(Markdown(f"✅ **Request sent.** Server says: {result.get('text')}"))
            display(Markdown("Check the `slack_server.log` file for detailed output from the crew."))
        else:
            display(Markdown(f"❌ **Error:** Received status code {response.status_code}"))
            display(Markdown(f"```\n{response.text}\n```"))

# Example usage in a Hex notebook cell:
# 
# from hex_crew_interface import HexCrewInterface
# 
# crew = HexCrewInterface()
# crew.start_analysis("What is the market size for residential solar panels in North America?")
#
#_or_
#
# crew.send_response("My priority is understanding the competitive landscape.")