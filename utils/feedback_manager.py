import os
import glob
from datetime import datetime

FEEDBACK_DIR = 'feedback'

def store_feedback(analysis_query, feedback_text, feedback_type="general"):
    """Store user feedback for learning"""
    os.makedirs(FEEDBACK_DIR, exist_ok=True)
    
    filename = os.path.join(FEEDBACK_DIR, f'feedback_{int(datetime.now().timestamp())}.txt')
    with open(filename, 'w') as f:
        f.write(f"Query: {analysis_query}\n")
        f.write(f"Feedback: {feedback_text}\n")
        f.write(f"Type: {feedback_type}\n")
        f.write(f"Timestamp: {datetime.now().isoformat()}\n")
    
    return filename

def get_relevant_feedback(query):
    """Get feedback relevant to current query"""
    feedback_files = glob.glob(os.path.join(FEEDBACK_DIR, '*.txt'))
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