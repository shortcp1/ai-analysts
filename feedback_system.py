import weaviate
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class FeedbackLearner:
    def __init__(self):
        self.client = self.get_weaviate_client()
        self.setup_feedback_schema()
    
    def get_weaviate_client(self):
        """Get Weaviate client (handling version compatibility)"""
        try:
            # Try v4 first
            import weaviate.classes as wvc
            return weaviate.connect_to_local()
        except:
            # Fallback for current setup
            return None
    
    def setup_feedback_schema(self):
        """Set up schema for storing feedback"""
        # For now, we'll use simple file storage since Weaviate has version issues
        os.makedirs('/root/ai-analysts/feedback', exist_ok=True)
    
    def store_feedback(self, analysis_query, feedback_text, feedback_type="general"):
        """Store user feedback for learning"""
        feedback_entry = {
            "timestamp": datetime.now().isoformat(),
            "analysis_query": analysis_query,
            "feedback": feedback_text,
            "type": feedback_type,
            "user": "christian"
        }
        
        # Store in file for now
        filename = f'/root/ai-analysts/feedback/feedback_{int(datetime.now().timestamp())}.txt'
        with open(filename, 'w') as f:
            f.write(f"Query: {analysis_query}\n")
            f.write(f"Feedback: {feedback_text}\n")
            f.write(f"Type: {feedback_type}\n")
            f.write(f"Timestamp: {feedback_entry['timestamp']}\n")
        
        return f"Feedback stored: {filename}"
    
    def get_feedback_for_query(self, query):
        """Retrieve relevant feedback for similar queries"""
        import glob
        feedback_files = glob.glob('/root/ai-analysts/feedback/*.txt')
        relevant_feedback = []
        
        for file in feedback_files:
            with open(file, 'r') as f:
                content = f.read()
                # Simple keyword matching (can be improved with embeddings)
                query_words = query.lower().split()
                if any(word in content.lower() for word in query_words):
                    relevant_feedback.append(content)
        
        return relevant_feedback[:5]  # Return top 5 relevant feedback items

if __name__ == "__main__":
    learner = FeedbackLearner()
    print("Feedback system initialized")
