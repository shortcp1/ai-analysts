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

load_dotenv()

app = Flask(__name__)

def extract_strategic_summary(analysis_text):
    """Extract the final strategic memo from CrewAI output"""
    lines = analysis_text.split('\n')
    
    # Find the "Final Output:" section
    final_output_start = -1
    for i, line in enumerate(lines):
        if 'Final Output:' in line:
            final_output_start = i
            break
    
    if final_output_start == -1:
        # Look for strategic memo
        for i, line in enumerate(lines):
            if 'Strategic Memo on' in line or 'Executive Summary' in line:
                final_output_start = i - 2
                break
    
    if final_output_start != -1:
        # Extract from final output to end
        memo_lines = lines[final_output_start:]
        
        # Clean and format the memo
        clean_memo = []
        for line in memo_lines:
            clean_line = re.sub(r'[│┌┐└┘├┤┬┴┼╭╮╯╰═]', '', line).strip()
            
            if (clean_line and 
                not clean_line.startswith('Tool Args:') and
                not clean_line.startswith('ID:') and
                not clean_line.startswith('╰') and
                len(clean_line) > 5):
                clean_memo.append(clean_line)
        
        # Extract key sections for Slack
        sections = []
        current_section = ""
        
        for line in clean_memo:
            if line.startswith('**') and (line.endswith('**') or 'Summary' in line or 'Assessment' in line or 'Recommendations' in line):
                if current_section:
                    sections.append(current_section.strip())
                current_section = f"{line}\n"
            elif line.startswith('- **') or line.startswith('1.') or line.startswith('2.') or line.startswith('•'):
                current_section += f"• {line}\n"
            elif line.strip() and not line.startswith('---') and not line.startswith('Final Output'):
                current_section += f"{line}\n"
        
        if current_section:
            sections.append(current_section.strip())
        
        # Return top 4 sections for Slack
        return '\n\n'.join(sections[:4]) if sections else "Strategic analysis completed with executive recommendations."
    
    return "Strategic analysis completed with executive recommendations."

def store_feedback(analysis_query, feedback_text, feedback_type="general"):
    """Store user feedback for learning"""
    os.makedirs('/root/ai-analysts/feedback', exist_ok=True)
    
    filename = f'/root/ai-analysts/feedback/feedback_{int(datetime.now().timestamp())}.txt'
    with open(filename, 'w') as f:
        f.write(f"Query: {analysis_query}\n")
        f.write(f"Feedback: {feedback_text}\n")
        f.write(f"Type: {feedback_type}\n")
        f.write(f"Timestamp: {datetime.now().isoformat()}\n")
    
    return filename

def get_relevant_feedback(query):
    """Get feedback relevant to current query"""
    feedback_files = glob.glob('/root/ai-analysts/feedback/*.txt')
    relevant_feedback = []
    
    for file in feedback_files:
        try:
            with open(file, 'r') as f:
                content = f.read()
                query_words = query.lower().split()
                if any(word in content.lower() for word in query_words):
                    relevant_feedback.append(content)
        except:
            continue
    
    return relevant_feedback[:3]

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

@app.route('/slack', methods=['POST'])
def slack_webhook():
    """Handle Slack slash commands"""
    try:
        text = request.form.get('text', '').strip()
        user_name = request.form.get('user_name', 'Unknown')
        
        print(f"Slack command from {user_name}: {text}")
        
        if text:
            thread = threading.Thread(target=run_analysis, args=(text,))
            thread.daemon = True
            thread.start()
            
            return jsonify({
                "text": f"🚀 Starting analysis: {text}\n\nI'll send results to this channel when complete..."
            })
        else:
            return jsonify({
                "text": "Please provide a query.\n\nExample: `/analyze residential generator market opportunity`"
            })
            
    except Exception as e:
        print(f"Slack error: {e}")
        return jsonify({"text": f"Error: {str(e)}"})

@app.route('/feedback', methods=['POST'])
def handle_feedback():
    """Handle feedback from Slack or other sources"""
    try:
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

@app.route('/webhook', methods=['POST', 'GET'])
def webhook():
    """Handle Google Chat messages"""
    try:
        if request.method == 'GET':
            return jsonify({"status": "ok", "message": "AI Analyst webhook is ready"})
        
        data = request.json
        print(f"Received webhook data: {data}")
        
        if 'message' in data and 'text' in data['message']:
            message_text = data['message']['text'].strip()
            print(f"Message text: {message_text}")
            
            if message_text.startswith('feedback:') or message_text.startswith('👍') or message_text.startswith('👎'):
                feedback_text = message_text.replace('feedback:', '').replace('👍', 'Good analysis').replace('👎', 'Needs improvement').strip()
                store_feedback("recent_analysis", feedback_text, "reaction")
                send_to_slack(f"📝 **Feedback Noted**: {feedback_text}\n\nThanks! I'll improve future analyses.")
                return jsonify({"text": "Feedback received and stored!"})
            
            elif message_text.startswith('/analyze'):
                query = message_text.replace('/analyze', '').strip()
                if query:
                    print(f"Starting analysis for: {query}")
                    thread = threading.Thread(target=run_analysis, args=(query,))
                    thread.daemon = True
                    thread.start()
                    return jsonify({"text": f"🚀 Starting analysis: {query}\n\nI'll send results when complete..."})
            
            elif 'test' in message_text.lower():
                send_to_slack("🧪 **Test Response**: AI Analyst system is running!\n\nUse `/analyze [your request]` to start an analysis.\n\nGive feedback with: `feedback: [your comments]` or react with 👍👎")
                return jsonify({"text": "Test message sent to Slack!"})
            
            else:
                return jsonify({"text": "Hi! I'm your AI Analyst team.\n\nCommands:\n• `/analyze [question]` - Run analysis\n• `feedback: [comments]` - Give feedback\n• `👍👎` - Quick reactions"})
        
        return jsonify({"text": "Send `/analyze [your request]` to start an analysis"})
        
    except Exception as e:
        print(f"Webhook error: {e}")
        return jsonify({"text": f"Error processing request: {str(e)}"})

def run_analysis(query):
    """Run the analysis with improved summary extraction"""
    try:
        print(f"Running analysis: {query}")
        
        relevant_feedback = get_relevant_feedback(query)
        
        enhanced_query = query
        if relevant_feedback:
            feedback_context = "\n".join([f"Previous feedback: {fb[:200]}..." for fb in relevant_feedback])
            enhanced_query = f"{query}\n\nContext from previous feedback:\n{feedback_context}\n\nPlease incorporate lessons learned from this feedback."
        
        send_to_slack(f"🚀 **Starting Analysis**: {query}\n\nIncorporating insights from {len(relevant_feedback)} previous feedback items...")
        
        os.chdir('/root/ai-analysts')
        
        result = subprocess.run([
            '/root/ai-analysts/venv/bin/python', 
            'main.py', 
            enhanced_query
        ], cwd='/root/ai-analysts', capture_output=True, text=True, timeout=600)
        
        print(f"Analysis completed with return code: {result.returncode}")
        
        if result.returncode == 0 and result.stdout:
            analysis_output = result.stdout
            strategic_summary = extract_strategic_summary(analysis_output)
            
            timestamp = str(int(time.time()))
            slack_message = f"""✅ **Analysis Complete**: {query}

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
                f.write("="*50 + "\n")
                f.write(analysis_output)
            
            print(f"Analysis saved to: {filename}")
            
        else:
            error_msg = result.stderr if result.stderr else "Unknown error"
            send_to_slack(f"❌ **Analysis Error**: {query}\n\n```{error_msg[:300]}```")
            
    except subprocess.TimeoutExpired:
        send_to_slack(f"⏱️ **Analysis Timeout**: {query}\n\nAnalysis took too long (>10 min).")
    except Exception as e:
        print(f"Error running analysis: {e}")
        send_to_slack(f"❌ **System Error**: {query}\n\nError: {str(e)}")

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "service": "AI Analyst Chat Server with Strategic Summary Extraction"})

@app.route('/', methods=['GET'])
def home():
    return "<h1>AI Analyst Chat Server</h1><p>Status: Running with Strategic Summary Extraction</p>"

if __name__ == '__main__':
    print("🌐 Starting AI Analyst Server with Strategic Summary Extraction...")
    app.run(host='0.0.0.0', port=8000, debug=False, threaded=True)
