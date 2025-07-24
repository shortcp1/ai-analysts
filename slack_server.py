import logging
logging.basicConfig(
    filename='slack_server.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
from flask import Flask, request, jsonify
import threading
import time
from main import AnalystCrew
from services.slack_client import send_to_slack
from interactive_manager import InteractiveManager

app = Flask(__name__)

# Initialize the interactive manager
interactive_manager = InteractiveManager()

# ===============================
# Helper functions
# ===============================

def handle_approval(text, user_id):
    """Handle the 'approve' command, run the analysis, and send the results."""
    try:
        logging.info(f"Approval received from {user_id}: {text}")

        # Check conversation state
        if user_id not in interactive_manager.conversations:
            logging.warning(f"No conversation found for user {user_id} to approve.")
            send_to_slack("⚠️ No active conversation to approve. Please start a new analysis.", user_id)
            return

        context = interactive_manager.conversations[user_id]
        logging.info(f"Found conversation for user {user_id}, state: {context.state.value}")

        if interactive_manager.is_ready_to_execute(user_id):
            final_scope = interactive_manager.get_final_scope(user_id)
            logging.info(f"Deploying team with scope: {final_scope}")

            # Send confirmation that analysis is starting
            send_to_slack(
                f":hourglass_flowing_sand: *Analysis in Progress...*\n"
                f"Thanks for your approval, <@{user_id}>! Our team is now analyzing the following scope:\n"
                f"> _{final_scope}_\n\n"
                "This may take a few minutes. I'll send the full report here once it's complete.",
                user_id
            )

            # Deploy the analyst crew
            crew = AnalystCrew()
            result = crew.run_remaining_analysis(final_scope, "Scope approved by client")

            # Format and send final report
            formatted_result = (
                f":tada: *Analysis Complete & Delivered!* :tada:\n"
                f"<@{user_id}>, here is the full report for your request:\n\n"
                f"*Final Scope:*\n> {final_scope}\n\n"
                f"*Research Findings & Strategic Recommendations:*\n{result}\n\n"
                "This conversation is now complete. You can start a new analysis at any time."
            )
            send_to_slack(formatted_result, user_id)
            
            # Clean up the conversation
            interactive_manager.reset_conversation(user_id)
            logging.info(f"Successfully completed and archived conversation for user {user_id}.")

        else:
            # If not ready to execute, treat as a normal message
            logging.info(f"Handling '{text}' as a continuation for user {user_id}")
            response = interactive_manager.continue_conversation(user_id, text)
            send_to_slack(f"💼 {response}", user_id)

    except Exception as e:
        logging.error(f"❌ Error during approval handling for user {user_id}: {e}", exc_info=True)
        send_to_slack(f"🔥 An error occurred while processing your approval: {e}. Please try again.", user_id)

def handle_interactive_conversation(text, user_id):
    try:
        print(f"Handling conversation from {user_id}: {text}")
        
        # Check if this is a new conversation or continuation
        if user_id not in interactive_manager.conversations:
            # Start new conversation
            response = interactive_manager.start_conversation(user_id, text)
            send_to_slack(f"💼 **Project Scoping Session Started**\n\n{response}")
        else:
            # Continue existing conversation
            response = interactive_manager.continue_conversation(user_id, text)
            send_to_slack(f"💼 {response}")
        
    except Exception as e:
        print(f"❌ Error during conversation: {e}")
        send_to_slack(f"🔥 Conversation error: {e}")

def handle_legacy_analysis_request(text):
    """Fallback for direct analysis requests (legacy mode)"""
    try:
        print(f"Handling legacy analysis request: {text}")
        crew = AnalystCrew()
        result = crew.run_scope_analysis(text)
        
        # Send result back to slack
        send_to_slack(f"📊 Quick analysis complete! \n\n{result}")
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        send_to_slack(f"🔥 Analysis failed: {e}")

# ===============================
# Slack main endpoint
# ===============================

def process_slack_command(data):
    """Processes the slack command in a separate thread."""
    try:
        user_name = data.get('user_name', 'unknown')
        user_id = data.get('user_id', user_name)
        text = data.get('text', '').strip()

        logging.info(f"Processing command from {user_name} ({user_id}): '{text}'")

        if text.startswith('approve'):
            handle_approval(text, user_id)
        elif text.startswith('reset'):
            interactive_manager.reset_conversation(user_id)
            send_to_slack("🔄 Conversation reset. You can start a new project discussion.", user_id)
        elif text.startswith('status'):
            if user_id in interactive_manager.conversations:
                state = interactive_manager.conversations[user_id].state.value
                send_to_slack(f"📊 Current conversation state: {state}", user_id)
            else:
                send_to_slack("📊 No active conversation. Start by describing your business question.", user_id)
        elif text.startswith('legacy'):
            legacy_text = text.replace('legacy', '').strip()
            if legacy_text:
                handle_legacy_analysis_request(legacy_text)
            else:
                send_to_slack("⚠️ Please provide a topic for legacy analysis.", user_id)
        elif text:
            handle_interactive_conversation(text, user_id)
        else:
            send_to_slack(
                "⚠️ Please provide your business question or use:\n" +
                "• `reset` - Start a new conversation\n" +
                "• `status` - Check conversation status\n" +
                "• `legacy [topic]` - Run direct analysis\n" +
                "• `approve` - Approve current proposal",
                user_id
            )
    except Exception as e:
        logging.error(f"❌ Error processing Slack command: {e}")
        try:
            send_to_slack(f"❌ An error occurred: {str(e)}", user_id)
        except Exception as send_e:
            logging.error(f"❌ Failed to send error message to Slack: {send_e}")

@app.route('/slack', methods=['POST'])
def slack_command():
    """Main Slack command handler with interactive conversation support"""
    # Log incoming request details for debugging
    logging.info("="*50)
    logging.info(f"REQUEST RECEIVED: {request.method} {request.url}")
    logging.info(f"HEADERS: {request.headers}")
    logging.info(f"MIMETYPE: {request.mimetype}")
    raw_data = request.get_data(as_text=True)
    logging.info(f"RAW BODY: {raw_data}")
    logging.info("="*50)

    # Handle URL verification challenge
    if request.is_json and "challenge" in request.get_json():
        json_data = request.get_json()
        print(f"Received Slack challenge: {json_data['challenge']}")
        return jsonify({"challenge": json_data["challenge"]})

    # Handle Slack Events API
    if request.is_json and "event" in request.get_json():
        json_data = request.get_json()
        event = json_data["event"]
        
        # Avoid processing bot's own messages
        if event.get("subtype") == "bot_message":
            return "", 200

        if event["type"] == "message":
            user_id = event.get("user")
            text = event.get("text", "").strip()

            if not user_id or not text:
                return "", 200

            # Process in a thread and respond immediately
            thread = threading.Thread(target=handle_interactive_conversation, args=(text, user_id))
            thread.daemon = True
            thread.start()
            return "", 200

    # Handle slash commands
    try:
        data = request.form
        # Acknowledge the command immediately
        user_id = data.get('user_id')
        text = data.get('text', '').strip()
        
        # Start processing in a background thread
        thread = threading.Thread(target=process_slack_command, args=(data,))
        thread.daemon = True
        thread.start()

        # Return an immediate response to Slack
        if text.startswith('approve'):
             return jsonify({"text": "✅ Approval received! Kicking off the analysis now..."})
        elif text.startswith('legacy'):
             return jsonify({"text": f"🚀 Legacy analysis for '{text.replace('legacy', '').strip()}' is starting..."})
        else:
             return jsonify({"text": "💼 Your request is being processed. I'll be with you shortly..."})
        
    except Exception as e:
        logging.error(f"❌ Error in Slack command handler: {e}")
        return jsonify({"text": f"❌ A critical error occurred: {str(e)}"}), 500

# ===============================
# Simple test endpoints
# ===============================

@app.route('/test', methods=['GET', 'POST'])
def test_endpoint():
    """Simple test endpoint to verify server is working"""
    return jsonify({
        "status": "ok",
        "method": request.method,
        "timestamp": time.time()
    })

@app.route('/slack-test', methods=['POST'])
def slack_test():
    """Minimal Slack webhook test"""
    try:
        return jsonify({"text": "✅ Test successful! Server is responding."})
    except Exception as e:
        return jsonify({"text": f"❌ Test failed: {e}"}), 500

@app.route('/feedback', methods=['POST'])
def feedback_endpoint():
    """Capture Slack feedback"""
    try:
        data = request.get_json(force=True)
        print(f"Feedback received: {data}")
        return jsonify({"text": "🙏 Thanks for your feedback!"})
    except Exception as e:
        return jsonify({"text": f"❌ Feedback error: {e}"}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Basic health check"""
    return jsonify({"status": "healthy", "timestamp": time.time()})

@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "Slack Server is running!"})

# ===============================
# Entry point
# ===============================
if __name__ == '__main__':
    print("🚀 Starting Slack Flask server on port 8000...")
    app.run(host='0.0.0.0', port=8000, debug=False, threaded=True)