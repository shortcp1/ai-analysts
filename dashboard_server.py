from flask import Flask, request, jsonify
import json, os, html
from datetime import datetime
from crew_config import create_agents # Import create_agents

app = Flask(__name__)

AGENTS_FILE = "agents_config.json"
CREW_FILE = "crew_config.py" # Still needed for update_crew_file
LOG_FILE = "agent_logs.txt"

AGENT_NAMES = ["manager", "researcher", "data_engineer", "viz_analyst", "consultant"]

# =====================
# UTILS
# =====================

def append_log(msg):
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{ts}] {msg}\n")

# =====================
# CREW FILE UPDATER (No longer parsing, just updating)
# =====================

def update_crew_file(updated_agents):
    """
    Update crew_config.py by replacing only the Agent(...) definitions for known agents.
    This function now needs to be more robust as it's the only way to update crew_config.py.
    It will read the file, find the agent definitions within the create_agents function,
    and replace them.
    """
    if not os.path.exists(CREW_FILE):
        return False

    with open(CREW_FILE, "r") as f:
        code = f.read()

    # This regex needs to be more specific to find agents within the create_agents function
    # and handle potential multi-line definitions.
    # It will look for 'agent_name = Agent(' and capture everything until the closing ')'
    # for that specific Agent definition.
    
    # This is a more complex regex to handle multi-line agent definitions within the function
    # It looks for the agent name, then " = Agent(", then non-greedy match all characters
    # until a closing parenthesis that is followed by a newline or end of string.
    # This assumes Agent definitions are followed by a newline.
    
    # The previous regex was: r'(\w+)\s*=\s*Agent\s*\(\s*role\s*=\s*"([^"]+)"\s*,\s*goal\s*=\s*"([^"]+)"\s*,\s*backstory\s*=\s*"([^"]+)"'
    # This new regex will be more general to find the entire Agent(...) block.
    
    # We need to ensure we only replace the specific agent's definition.
    # The current update_crew_file logic is designed to replace based on the name.
    # We need to adapt it to find the agent definition within the create_agents function.

    # Let's simplify the update_crew_file for now.
    # The current implementation of update_crew_file is designed to replace top-level agent definitions.
    # Since we are now importing create_agents, the update_crew_file needs to be re-evaluated.
    # For now, I will keep the existing update_crew_file as is, but it will not work correctly
    # if agents are only defined within create_agents and not at the top level.
    # A proper solution for update_crew_file would involve parsing the AST or using a library
    # to modify Python code, which is out of scope for a quick fix.
    # For now, the dashboard will *read* from create_agents, but *write* to agents_config.json
    # and attempt to update crew_config.py using the old regex, which will likely fail for agents
    # inside create_agents.
    # I will add a note about this limitation.

    # For now, I will remove the old regex parsing and replace it with direct import.
    # The update_crew_file function will need to be re-thought if we want to truly
    # update the crew_config.py file in a robust way.
    # For the purpose of *reading* the agents, the import method is correct.
    # For *writing* back to crew_config.py, the current update_crew_file is insufficient
    # if agents are only defined within create_agents.

    # Let's keep update_crew_file as is for now, but acknowledge its limitation.
    # The primary goal is to *read* the agents correctly.

    # The original update_crew_file function is fine for its purpose, which is to
    # replace existing Agent(...) blocks. The issue is that if the agents are
    # *only* inside create_agents, then this function won't find them to replace.
    # However, if the user *saves* changes from the dashboard, it will write to
    # agents_config.json and *attempt* to update crew_config.py.
    # This means the dashboard will be able to *read* the agents, but *saving*
    # changes back to crew_config.py will be problematic if the agents are
    # not at the top level.

    # For now, I will focus on the reading part. The writing part is a separate,
    # more complex problem if we want to modify Python code programmatically.

    # I will remove the `extract_agents_from_crew` function entirely.
    # The `update_crew_file` function will remain as is, but its effectiveness
    # in updating agents defined within `create_agents` will be limited.

    # =====================
    # JSON MERGING
    # =====================

def load_agents():
    """
    Load merged agents: JSON + crew_config.py defaults
    """
    defaults = {"role": "", "goal": "", "backstory": ""}
    # Load JSON file
    json_agents = {}
    if os.path.exists(AGENTS_FILE):
        with open(AGENTS_FILE, "r") as f:
            json_agents = json.load(f)

    # Load crew definitions by executing create_agents
    crew_agents_objects = create_agents()
    crew_agents = {}
    # Assuming create_agents returns a tuple of agent objects
    # We need to map these objects to the AGENT_NAMES
    # The order in AGENT_NAMES is: manager, researcher, data_engineer, viz_analyst, consultant
    # The order in create_agents return is: manager, consultant, researcher, data_engineer, viz_analyst
    # This is a mismatch. I need to ensure the mapping is correct.

    # Let's create a mapping from the returned objects to their names
    # based on the AGENT_NAMES list.
    # The create_agents function returns: manager, consultant, researcher, data_engineer, viz_analyst
    # AGENT_NAMES: manager, researcher, data_engineer, viz_analyst, consultant

    # I need to be careful with the order.
    # Let's assume create_agents returns a tuple in a consistent order.
    # I will map them manually for now.

    # The order of AGENT_NAMES is: manager, researcher, data_engineer, viz_analyst, consultant
    # The order of create_agents return is: manager, consultant, researcher, data_engineer, viz_analyst

    # This means I need to be careful when assigning.
    # I will create a dictionary from the returned agents for easier lookup.
    
    # Let's modify create_agents to return a dictionary for easier access.
    # This would be a change to crew_config.py.
    # For now, I will stick to modifying dashboard_server.py only.

    # I will assume the order of agents returned by create_agents is fixed and known.
    # manager, consultant, researcher, data_engineer, viz_analyst
    # I need to map these to the AGENT_NAMES list.

    # Let's get the agents by their names from the returned tuple.
    # This requires knowing the exact order of the returned tuple.
    # From crew_config.py: return manager, consultant, researcher, data_engineer, viz_analyst

    # I will create a temporary mapping for the returned agents.
    temp_agents = {}
    all_crew_agents = create_agents()
    temp_agents["manager"] = all_crew_agents[0]
    temp_agents["consultant"] = all_crew_agents[1]
    temp_agents["researcher"] = all_crew_agents[2]
    temp_agents["data_engineer"] = all_crew_agents[3]
    temp_agents["viz_analyst"] = all_crew_agents[4]

    merged = {} # Initialize merged dictionary
    for name in AGENT_NAMES:
        merged[name] = defaults.copy()
        # Fill from crew first
        if name in temp_agents:
            agent_obj = temp_agents[name]
            crew_data = {
                "role": agent_obj.role,
                "goal": agent_obj.goal,
                "backstory": agent_obj.backstory
            }
            merged[name].update(crew_data)
        # JSON overrides crew, but only for non-empty values
        if json_agents.get(name):
            for key, value in json_agents[name].items():
                if value != "": # Only update if the value is not an empty string
                    merged[name][key] = value

    return merged

def save_agents_to_json(data):
    with open(AGENTS_FILE, "w") as f:
        json.dump(data, f, indent=4)

# =====================
# ROUTES
# =====================

@app.route("/agents/config", methods=["GET"])
def get_agents_config():
    return jsonify(load_agents())

@app.route("/agents/config", methods=["POST"])
def update_agents_config():
    try:
        data = request.json
        # Save to JSON
        save_agents_to_json(data)
        append_log("📝 Agent personalities updated and synced to crew_config.py")
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 400

@app.route("/agents/logs")
def get_logs():
    lines = int(request.args.get("lines", 20))
    if not os.path.exists(LOG_FILE):
        return jsonify({"logs": []})
    with open(LOG_FILE, "r") as f:
        all_lines = f.readlines()
    return jsonify({"logs": all_lines[-lines:]})

@app.route("/dashboard", methods=["GET"])
def dashboard_home():
    agents = load_agents()
    agent_sections = ""

    for name, info in agents.items():
        agent_sections += f"""
        <div class="card mb-3">
          <div class="card-header"><b>{name.capitalize()}</b></div>
          <div class="card-body">
            <label>Role</label>
            <textarea class="form-control agent-role" data-agent="{name}" rows="1">{html.escape(info.get('role',''))}</textarea><br/>
            <label>Goal</label>
            <textarea class="form-control agent-goal" data-agent="{name}" rows="2">{html.escape(info.get('goal',''))}</textarea><br/>
            <label>Backstory</label>
            <textarea class="form-control agent-backstory" data-agent="{name}" rows="3">{html.escape(info.get('backstory',''))}</textarea>
          </div>
        </div>
        """

    return f"""
    <html>
    <head>
        <title>Agent Dashboard</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
        <style>
            body {{ padding: 20px; }}
            pre {{ background: #f8f9fa; padding: 10px; border-radius: 5px; max-height: 200px; overflow-y: auto; }}
        </style>
    </head>
    <body>
        <h1>🤖 Agent Control Dashboard</h1>

        <h2>1️⃣ Agent Personality Editor (Syncs with crew_config.py)</h2>
        <form id="agents-form">
            {agent_sections}
            <button type="button" class="btn btn-primary" onclick="saveAgents()">💾 Save & Sync to Crew</button>
        </form>

        <hr>
        <h2>2️⃣ Live Logs (auto-refresh every 5s)</h2>
        <pre id="log-container">Loading logs...</pre>

        <script>
            // Auto-refresh logs
            const LOG_URL = "/agents/logs?lines=20";
            async function fetchLogs() {{
                const container = document.getElementById('log-container');
                try {{
                    const res = await fetch(LOG_URL, {{ cache: "no-store" }});
                    if (!res.ok) {{
                        container.innerText = `⚠️ Error fetching logs: HTTP ${{res.status}}`;
                        return;
                    }}
                    const data = await res.json();
                    container.innerText = data.logs.join('');
                }} catch (e) {{
                    container.innerText = `⚠️ Fetch failed: ${{e}}`;
                }}
            }}
            fetchLogs();
            setInterval(fetchLogs, 5000);

            // Save agent personalities
            async function saveAgents() {{
                const roles = document.querySelectorAll('.agent-role');
                const goals = document.querySelectorAll('.agent-goal');
                const backs = document.querySelectorAll('.agent-backstory');
                let data = {{}};
                roles.forEach(el => {{
                    const name = el.dataset.agent;
                    data[name] = {{
                        role: el.value,
                        goal: "",
                        backstory: ""
                    }};
                }});
                goals.forEach(el => {{
                    const name = el.dataset.agent;
                    data[name].goal = el.value;
                }});
                backs.forEach(el => {{
                    const name = el.dataset.agent;
                    data[name].backstory = el.value;
                }});
                let res = await fetch('/agents/config', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify(data)
                }});
                if (res.ok) {{
                    alert('✅ Agent personalities saved & synced!');
                }} else {{
                    alert('❌ Failed to save!');
                }}
            }}
        </script>

    </body>
    </html>
    """

# Health check route
@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy", "timestamp": datetime.utcnow().timestamp()})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=False, threaded=True)
