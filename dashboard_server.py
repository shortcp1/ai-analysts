from flask import Flask, request, jsonify
import json, os, re
from datetime import datetime

app = Flask(__name__)

AGENTS_FILE = "agents_config.json"
CREW_FILE = "crew_config.py"
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
# CREW FILE PARSER
# =====================

def extract_agents_from_crew():
    """
    Parse crew_config.py and extract Agent(role=..., goal=..., backstory=...)
    Returns dict: {agent_name: {role,goal,backstory}}
    """
    if not os.path.exists(CREW_FILE):
        return {}

    with open(CREW_FILE, "r") as f:
        code = f.read()

    # Regex matches lines like:
    # manager = Agent(role="...", goal="...", backstory="...")
    pattern = re.compile(
        r'(\w+)\s*=\s*Agent\s*\(\s*role\s*=\s*"([^"]+)"\s*,\s*goal\s*=\s*"([^"]+)"\s*,\s*backstory\s*=\s*"([^"]+)"',
        re.DOTALL
    )

    crew_agents = {}
    for match in pattern.finditer(code):
        name, role, goal, backstory = match.groups()
        crew_agents[name] = {
            "role": role,
            "goal": goal,
            "backstory": backstory
        }

    return crew_agents

def update_crew_file(updated_agents):
    """
    Update crew_config.py by replacing only the Agent(...) definitions for known agents.
    """
    if not os.path.exists(CREW_FILE):
        return False

    with open(CREW_FILE, "r") as f:
        code = f.read()

    # For each agent, replace its Agent(...) block
    for name, data in updated_agents.items():
        if name not in AGENT_NAMES:
            continue

        role = data.get("role", "")
        goal = data.get("goal", "")
        backstory = data.get("backstory", "")

        new_def = f'{name} = Agent(role="{role}", goal="{goal}", backstory="{backstory}")'

        # Replace existing or insert if missing
        if re.search(rf'{name}\s*=\s*Agent\s*\(.*?\)', code, flags=re.DOTALL):
            code = re.sub(
                rf'{name}\s*=\s*Agent\s*\(.*?\)',
                new_def,
                code,
                flags=re.DOTALL
            )
        else:
            # Append at end if not found
            code += f"\n{new_def}\n"

    # Write back
    with open(CREW_FILE, "w") as f:
        f.write(code)

    return True

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

    # Load crew definitions
    crew_agents = extract_agents_from_crew()

    merged = {}
    for name in AGENT_NAMES:
        merged[name] = defaults.copy()
        # Fill from crew first
        if crew_agents.get(name):
            merged[name].update(crew_agents[name])
        # JSON overrides crew
        if json_agents.get(name):
            merged[name].update(json_agents[name])

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
        # Also write back to crew_config.py
        update_crew_file(data)
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
            <textarea class="form-control agent-role" data-agent="{name}" rows="1">{info.get('role','')}</textarea><br/>
            <label>Goal</label>
            <textarea class="form-control agent-goal" data-agent="{name}" rows="2">{info.get('goal','')}</textarea><br/>
            <label>Backstory</label>
            <textarea class="form-control agent-backstory" data-agent="{name}" rows="3">{info.get('backstory','')}</textarea>
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
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
