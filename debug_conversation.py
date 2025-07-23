#!/usr/bin/env python3

import os
from dotenv import load_dotenv
from interactive_manager import InteractiveManager

# Load environment variables
load_dotenv()

def debug_conversation():
    manager = InteractiveManager()
    user_id = "U096X5ZPKJA"  # Christian's user ID from the logs
    
    print("=== Debugging Conversation State ===")
    
    # Check if conversation exists
    if user_id in manager.conversations:
        context = manager.conversations[user_id]
        print(f"✅ Conversation found for user {user_id}")
        print(f"Current state: {context.state.value}")
        print(f"User responses: {context.user_responses}")
        print(f"Questions asked: {context.questions_asked}")
        print(f"Ready to execute: {manager.is_ready_to_execute(user_id)}")
    else:
        print(f"❌ No conversation found for user {user_id}")
        print("Available conversations:")
        for uid in manager.conversations.keys():
            print(f"  - {uid}: {manager.conversations[uid].state.value}")
    
    print("\n=== Testing Approval Flow ===")
    
    # Simulate the approval process
    if user_id in manager.conversations:
        print("Testing continue_conversation with 'approve'...")
        try:
            response = manager.continue_conversation(user_id, "approve")
            print(f"Response: {response}")
            print(f"New state: {manager.conversations[user_id].state.value}")
            print(f"Ready to execute: {manager.is_ready_to_execute(user_id)}")
        except Exception as e:
            print(f"Error in continue_conversation: {e}")
    else:
        print("Cannot test approval - no conversation exists")

if __name__ == "__main__":
    debug_conversation()