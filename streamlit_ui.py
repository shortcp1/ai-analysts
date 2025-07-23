import streamlit as st
import pandas as pd
from output_store import get_all_sessions, load_session_outputs

st.set_page_config(layout="wide")

def display_dashboard():
    """
    Main function to display the Streamlit dashboard.
    """
    st.title("AI Analyst Crew - Output Dashboard")

    # --- Sidebar for session selection ---
    st.sidebar.title("Analysis Sessions")
    all_sessions = get_all_sessions()
    if not all_sessions:
        st.warning("No analysis sessions found. Run an analysis to generate outputs.")
        return
        
    selected_session = st.sidebar.selectbox("Select a session to view", all_sessions)

    if not selected_session:
        return

    # --- Main content area ---
    st.header(f"Results for Session: {selected_session}")
    
    session_outputs = load_session_outputs(selected_session)
    
    if not session_outputs:
        st.error("Could not load outputs for this session.")
        return

    # --- Tabs for each agent's output ---
    tab_titles = [agent.capitalize() for agent in session_outputs.keys()]
    tabs = st.tabs(tab_titles)

    for i, agent_name in enumerate(session_outputs.keys()):
        with tabs[i]:
            st.subheader(f"{agent_name.capitalize()}'s Output")
            
            agent_data = session_outputs[agent_name]
            st.text(f"Timestamp: {agent_data.get('timestamp', 'N/A')}")
            
            output_content = agent_data.get('data', {})
            
            # Display content as a dataframe or json based on type
            if isinstance(output_content, dict):
                st.json(output_content)
            elif isinstance(output_content, list):
                st.dataframe(pd.DataFrame(output_content))
            else:
                st.text(output_content)

if __name__ == "__main__":
    display_dashboard()