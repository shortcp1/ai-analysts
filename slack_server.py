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
    try:
        print(f"Approval received from {user_id}: {text}")
        
        # Debug: Check conversation state
        print(f"DEBUG: Checking conversations for user {user_id}")
        if user_id in interactive_manager.conversations:
            context = interactive_manager.conversations[user_id]
            print(f"DEBUG: Found conversation, state: {context.state.value}")
        else:
            print(f"DEBUG: No conversation found for user {user_id}")
            print(f"DEBUG: Available conversations: {list(interactive_manager.conversations.keys())}")
        
        # Check if this user has an active conversation and is ready to execute
        if interactive_manager.is_ready_to_execute(user_id):
            # Get the final scope from the conversation
            final_scope = interactive_manager.get_final_scope(user_id)
            
            print(f"Deploying team with scope: {final_scope}")
            
            # Send confirmation message
            send_to_slack(
                f":white_check_mark: *Approval Confirmed* :white_check_mark:\n"
                f"• *User*: <@{user_id}>\n"
                f"• *Scope*: {final_scope}\n\n"
                f"Starting analysis now..."
            )
            
            # Deploy the analyst crew with the refined scope
            crew = AnalystCrew()
            result = crew.run_remaining_analysis(final_scope, "Scope approved by client")
            
            # Clean up the conversation
            interactive_manager.reset_conversation(user_id)
            
            # Format and send final results
            formatted_result = (
                f":tada: *Analysis Complete* :tada:\n"
                f"• *Scope*: {final_scope}\n"
                f"• *Requested by*: <@{user_id}>\n\n"
                f"*Results*:\n{result}\n\n"
                f"_This conversation has been archived. Start a new one anytime!_"
            )
            send_to_slack(formatted_result)
            
        else:
            # Handle as a continuation of the conversation
            print(f"DEBUG: Handling as continuation for user {user_id}")
            response = interactive_manager.continue_conversation(user_id, text)
            print(f"DEBUG: Response from continue_conversation: {response}")
            send_to_slack(f"💼 {response}")
        logging.info(f"Approval handled for user {user_id}. New state: {context.state.value}")
        
    except Exception as e:
        print(f"❌ Error during approval handling: {e}")
        send_to_slack(f"🔥 Error processing approval: {e}")

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

@app.route('/slack', methods=['POST'])
def slack_command():
    """Main Slack command handler with interactive conversation support"""
    try:
        # Slack URL verification challenge
        # Log incoming request details for debugging
        logging.info("="*50)
        logging.info(f"REQUEST RECEIVED: {request.method} {request.url}")
        logging.info(f"HEADERS: {request.headers}")
        logging.info(f"MIMETYPE: {request.mimetype}")
        raw_data = request.get_data(as_text=True)
        logging.info(f"RAW BODY: {raw_data}")
        logging.info("="*50)

        if request.is_json:
            json_data = request.get_json()
            if "challenge" in json_data:
                print(f"Received Slack challenge: {json_data['challenge']}")
                return jsonify({"challenge": json_data["challenge"]})

            # Handle Slack Events API
            if "event" in json_data:
                event = json_data["event"]
                # Avoid processing bot's own messages
                if event.get("subtype") == "bot_message":
                    return jsonify({"status": "ok, bot message ignored"})

                if event["type"] == "message":
                    user_id = event.get("user")
                    text = event.get("text", "").strip()

                    # Ignore messages without user or text (e.g., file uploads)
                    if not user_id or not text:
                        return jsonify({"status": "ok, message without user or text ignored"})

                    thread = threading.Thread(target=handle_interactive_conversation, args=(text, user_id))
                    thread.daemon = True
                    thread.start()
                    return jsonify({"status": "ok, event processed"})

        data = request.form
        user_name = data.get('user_name', 'unknown')
        user_id = data.get('user_id', user_name)  # Use user_id for conversation tracking
        text = data.get('text', '').strip()

        print(f"Parsed command from {user_name} ({user_id}): '{text}'")
        logging.info(f"Received message from {user_name} ({user_id}): {text}")

        # Handle special commands
        if text.startswith('approve'):
            thread = threading.Thread(target=handle_approval, args=(text, user_id))
            thread.daemon = True
            thread.start()
            return jsonify({"text": "✅ Processing your approval..."})
        
        elif text.startswith('reset'):
            interactive_manager.reset_conversation(user_id)
            return jsonify({"text": "🔄 Conversation reset. You can start a new project discussion."})
        
        elif text.startswith('status'):
            if user_id in interactive_manager.conversations:
                state = interactive_manager.conversations[user_id].state.value
                return jsonify({"text": f"📊 Current conversation state: {state}"})
            else:
                return jsonify({"text": "📊 No active conversation. Start by describing your business question."})
        
        elif text.startswith('legacy'):
            # Legacy mode for direct analysis
            legacy_text = text.replace('legacy', '').strip()
            if legacy_text:
                thread = threading.Thread(target=handle_legacy_analysis_request, args=(legacy_text,))
                thread.daemon = True
                thread.start()
                return jsonify({"text": f"🚀 Legacy analysis mode: {legacy_text}. Running direct analysis..."})
            else:
                return jsonify({"text": "⚠️ Please provide a topic for legacy analysis."})
        
        elif text:
            # Interactive conversation mode (default)
            thread = threading.Thread(target=handle_interactive_conversation, args=(text, user_id))
            thread.daemon = True
            thread.start()
            return jsonify({"text": "💼 Starting interactive project scoping..."})

        # No valid text provided
        return jsonify({
            "text": "⚠️ Please provide your business question or use:\n" +
                   "• `reset` - Start a new conversation\n" +
                   "• `status` - Check conversation status\n" +
                   "• `legacy [topic]` - Run direct analysis\n" +
                   "• `approve` - Approve current proposal"
        })

    except Exception as e:
        print(f"❌ Error in Slack command: {e}")
        return jsonify({"text": f"❌ Error: {str(e)}"}), 500

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