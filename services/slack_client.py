import os
import requests

def send_to_slack(message):
    """Send message to Slack"""
    try:
        webhook_url = os.getenv("SLACK_WEBHOOK")
        if webhook_url:
            payload = {"text": message}
            response = requests.post(webhook_url, json=payload, timeout=10)
            print(f"Sent to Slack: {response.status_code}")
            return response.status_code == 200
    except Exception as e:
        print(f"Error sending to Slack: {e}")
        return False