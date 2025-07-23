from flask import Flask, request, jsonify
import subprocess
import os
import threading
import sys
import time
import re
import glob
from datetime import datetime
from dotenv import load_dotenv
import requests
from utils.feedback_manager import store_feedback, get_relevant_feedback
from services.slack_client import send_to_slack
from utils.summary_extractor import extract_strategic_summary
from main import AnalystCrew
import uuid

load_dotenv()

app = Flask(__name__)

FEEDBACK_DIR = 'feedback'
analysis_sessions = {}




@app.route('/slack', methods=['POST'])
def slack_webhook():
    """Handle Slack slash commands"""
    try:
        # Log all incoming request data for debugging
        print(f"Received request method: {request.method}")
        print(f"Request headers: {dict(request.headers)}")
        print(f"Request form data: {dict(request.form)}")
        print(f"Request content type: {request.content_type}")
        
        text = request.form.get('text', '').strip()
        user_name = request.form.get('user_name', 'Unknown')
        
        print(f"Parsed command from {user_name}: '{text}'")
        
        if text.startswith('approve'):
            thread = threading.Thread(target=handle_approval, args=(text,))
            thread.daemon = True
            thread.start()
            return jsonify({"text": "✅ Approval received. Kicking off the full analysis..."})
        
        elif text:
            thread = threading.Thread(target=handle_analysis_request, args=(text,))
            thread.daemon = True
            thread.start()
            return jsonify({"text": f"🚀 Request received: {text}. Scoping analysis is underway..."})

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
        return jsonify({"text": "Test successful! Server is responding."})
    except Exception as e:
        return jsonify({"text": f"Test failed: {e}"})
            
        else:
            return jsonify({"text": "Please provide a query. Example: `/analyze residential generator market opportunity`"})

    except Exception as e:
        print(f"Slack webhook error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"text": f"An unexpected error occurred: {e}"})

@app.route('/feedback', methods=['POST'])
def handle_feedback():
    """Handle feedback from Slack or other sources"""
    try:

def handle_analysis_request(query):
    """Wrapper to run initial analysis in a thread."""
    session_id = str(uuid.uuid4())
    analysis_sessions[session_id] = {"query": query, "status": "scoping"}
    run_initial_analysis(session_id, query)

def handle_approval(text):
    """Wrapper to run final analysis in a thread."""
    try:
        session_id = text.split(' ')[-1]
        
        if not session_id or session_id not in analysis_sessions:
            send_to_slack(f"Invalid session ID: {session_id}")
            return
            
        session = analysis_sessions[session_id]
        if session['status'] != 'pending_approval':
            send_to_slack(f"Session {session_id} is not pending approval.")
            return
            
        session['status'] = 'approved'
        run_final_analysis(session_id)
        
    except Exception as e:
        send_to_slack(f"Error handling approval: {e}")
        data = request.json
        analysis_query = data.get('analysis_query', 'Unknown')
        feedback_text = data.get('feedback', '')
        feedback_type = data.get('type', 'general')
        
        if feedback_text:
            filename = store_feedback(analysis_query, feedback_text, feedback_type)
            send_to_slack(f"📝 **Feedback Received**: {feedback_text}\n\nI'll incorporate this into future analyses. Thanks for helping me improve!")
            return jsonify({"status": "success", "message": "Feedback stored", "file": filename})
        else:
            return jsonify({"status": "error", "message": "No feedback provided"})
            
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


def run_initial_analysis(session_id, query):
    """Run the scoping analysis"""
    try:
        print(f"Running scoping for session {session_id}: {query}")
        
        analyst_crew = AnalystCrew()
        scoping_result = analyst_crew.run_scope_analysis(query)
        
        analysis_sessions[session_id]["scoping_result"] = scoping_result
        analysis_sessions[session_id]["status"] = "pending_approval"
        
        slack_message = f"""✅ **Project Scope Ready for Approval**: {query} (Session: {session_id})

**Scope Summary & Clarifications:**
{scoping_result}

**To proceed, type:** `/analyze approve {session_id}`

You can also provide feedback now, or wait for the full analysis.
"""
        send_to_slack(slack_message)
        
    except Exception as e:
        print(f"Error running scoping analysis for session {session_id}: {e}")
        send_to_slack(f"❌ **Scoping Error** (Session: {session_id}):\n\nError: {str(e)}")

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "service": "AI Analyst Chat Server with Strategic Summary Extraction"})



def run_final_analysis(session_id):
    """Run the rest of the analysis after approval"""
    try:
        session = analysis_sessions[session_id]
        query = session['query']
        scoping_result = session['scoping_result']
        
        print(f"Running final analysis for session {session_id}: {query}")
        send_to_slack(f"🚀 **Starting Full Analysis**: {query} (Session: {session_id})\n\nThis may take a few minutes...")
        
        analyst_crew = AnalystCrew()
        final_result = analyst_crew.run_remaining_analysis(query, scoping_result)
        
        strategic_summary = extract_strategic_summary(final_result)
        
        timestamp = str(int(time.time()))
        slack_message = f"""✅ **Analysis Complete**: {query} (Session: {session_id})

📊 **Strategic Summary:**
{strategic_summary[:1400]}

📈 **Next Steps:** 
- Full detailed analysis saved to server files
- Ready for executive presentation
- Follow-up analysis available on request

💡 **Give Feedback:**
- React with 👍 (good) or 👎 (needs work)
- Type: `feedback: [your specific comments]`
- Help me improve future analyses!

📁 **File**: analysis_{timestamp}_{query.replace(' ', '_')[:15]}.txt
*Completed by your AI analyst team*"""
        
        send_to_slack(slack_message)
        
        filename = f'analysis_{timestamp}_{query.replace(" ", "_")[:15]}.txt'
        with open(f'/root/ai-analysts/{filename}', 'w') as f:
            f.write(f"Analysis: {query}\n")
            f.write(f"Session ID: {session_id}\n")
            f.write("="*50 + "\n\n")
            f.write("--- SCOPING RESULTS ---\n")
            f.write(scoping_result)
            f.write("\n\n--- FINAL ANALYSIS ---\n")
            f.write(final_result)
        
        print(f"Analysis for session {session_id} saved to: {filename}")
        analysis_sessions[session_id]['status'] = 'complete'
        
    except Exception as e:
        print(f"Error running final analysis for session {session_id}: {e}")
        send_to_slack(f"❌ **Analysis Error** (Session: {session_id}):\n\nError: {str(e)}")
        analysis_sessions[session_id]['status'] = 'error'
@app.route('/', methods=['GET'])
def home():
    return "<h1>AI Analyst Chat Server</h1><p>Status: Running with Strategic Summary Extraction</p>"

if __name__ == '__main__':
    print("🌐 Starting AI Analyst Server with Strategic Summary Extraction...")
    app.run(host='0.0.0.0', port=8000, debug=False, threaded=True)
