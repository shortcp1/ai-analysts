# Getting Your Analyst Crew Working in Hex

You're right, the previous instructions were confusing. Here is a clear, step-by-step guide to get your local AI crew running inside a real Hex notebook.

The key is to package your local code and install it from within Hex. This allows your Hex notebooks to import your custom modules like `hex_crew_interface`.

---

## **Step 1: Make Your Local Code Installable**

I've created a `setup.py` file for you. This file tells Python how to treat your project as an installable package. You don't need to modify it, but it's the key to making this work.

## **Step 2: Install Your Local Code**

From your terminal, in the project's root directory, run this command:

```bash
pip install -e .
```

- `pip install`: The standard command to install a Python package.
- `-e`: This stands for "editable." It installs your project in a way that lets you make changes to your code without having to reinstall it every time.
- `.`: This tells `pip` to look for the `setup.py` file in the current directory.

This command makes your local code, including `hex_crew_interface`, available to any Python script on your system, including the environment that Hex uses.

## **Step 3: Run Your Backend Server**

Your analyst crew needs a backend to run. The `slack_server.py` you already have is perfect for this. Let's start it:

```bash
python slack_server.py
```
This server will listen for requests and manage the AI agent workflows.

---

## **Step 4: Use Your Crew in a Hex Notebook**

Now, you can go into any Hex notebook and use your analyst crew. Here is the code to put in a Hex cell:

```python
# This cell runs your analyst crew from within Hex

# First, make sure all dependencies are installed
%pip install requests python-dotenv crewai==0.28.8 langchain_openai==0.1.1 ipython

# Now you can import and use your local code
from hex_crew_interface import HexCrewInterface

# Initialize the interface with the correct server URL
# The default port for your slack_server.py is 8000
crew = HexCrewInterface(server_url="http://127.0.0.1:8000")

# Kick off an analysis
crew.start_analysis("What are the key investment trends in the battery storage market?")
```

### **How to Handle Follow-up Questions:**

If your crew has clarifying questions, they will be printed in the output of the cell above. To respond, you can use a new cell:

```python
# Use this cell to respond to the crew's questions
crew.send_response("Focus on commercial-scale battery storage solutions, not residential.")
```

---

## **Troubleshooting**

- **"No module named 'hex_crew_interface'"**: This means Step 2 was not successful. Make sure you run `pip install -e .` from your project's root directory.
- **"ConnectionError"**: This means your backend server is not running. Make sure you have `python slack_server.py` running in a terminal.
- **Other Errors**: Check the terminal where your `slack_server.py` is running. Any errors from the AI agents will be printed there.

This approach correctly uses your existing backend and makes your local code available to Hex in a standard way.