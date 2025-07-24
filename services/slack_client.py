import os
import requests

def send_to_slack(message, user_id=None):
    """Send message to Slack, optionally to a specific user."""
    try:
        webhook_url = os.getenv("SLACK_WEBHOOK")
        if not webhook_url:
            print("SLACK_WEBHOOK environment variable not set.")
            return False

        payload = {"text": message}
        if user_id:
            payload["channel"] = user_id  # Send DM to user

        response = requests.post(webhook_url, json=payload, timeout=10)
        print(f"Sent to Slack: {response.status_code}, Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error sending to Slack: {e}")
        return False