import json
import os
from datetime import datetime

OUTPUT_DIR = "outputs"

def save_agent_output(session_id, agent_name, output_data):
    """
    Saves the output of a specific agent to a file in a session directory.
    """
    session_path = os.path.join(OUTPUT_DIR, session_id)
    os.makedirs(session_path, exist_ok=True)
    
    file_path = os.path.join(session_path, f"{agent_name}_output.json")
    
    # Add metadata
    output_data_with_metadata = {
        "agent": agent_name,
        "timestamp": datetime.now().isoformat(),
        "data": output_data
    }
    
    with open(file_path, 'w') as f:
        json.dump(output_data_with_metadata, f, indent=4)
        
    print(f"Saved output for {agent_name} in session {session_id}")

def load_session_outputs(session_id):
    """
    Loads all agent outputs for a given session.
    """
    session_path = os.path.join(OUTPUT_DIR, session_id)
    if not os.path.isdir(session_path):
        return {}
        
    outputs = {}
    for filename in os.listdir(session_path):
        if filename.endswith(".json"):
            agent_name = filename.replace("_output.json", "")
            file_path = os.path.join(session_path, filename)
            with open(file_path, 'r') as f:
                outputs[agent_name] = json.load(f)
                
    return outputs

def get_all_sessions():
    """
    Lists all available session IDs from the output directory.
    """
    if not os.path.isdir(OUTPUT_DIR):
        return []
    return [d for d in os.listdir(OUTPUT_DIR) if os.path.isdir(os.path.join(OUTPUT_DIR, d))]

if __name__ == '__main__':
    # Example usage: create some dummy files for testing
    print("Creating dummy output files for testing...")
    test_session_id = "session_20250723_001"
    
    manager_output = {"scope": "Analyze the EV market.", "cost_estimate": "$5,000"}
    researcher_output = {"summary": "The EV market is growing.", "citations": ["ev_report.pdf"]}
    viz_analyst_output = {"chart_type": "bar_chart", "data": {"Tesla": 50, "Ford": 20}}
    
    save_agent_output(test_session_id, "manager", manager_output)
    save_agent_output(test_session_id, "researcher", researcher_output)
    save_agent_output(test_session_id, "viz_analyst", viz_analyst_output)
    
    print("\nLoading session outputs:")
    loaded_outputs = load_session_outputs(test_session_id)
    print(json.dumps(loaded_outputs, indent=2))

    print("\nAvailable sessions:")
    print(get_all_sessions())