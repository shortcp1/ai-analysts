from crewai import Agent
from crewai.tools import BaseTool
from langchain_openai import ChatOpenAI
from tools.weaviate_search import search_memory
from tools.weaviate_write import store_memory
from tools.perplexity_search import research_topic
from tools.hex_analysis import run_data_analysis
from tools.token_estimator import estimate_costs
import os
import json

AGENTS_FILE = "agents_config.json"

def load_agent_config_from_json():
    if os.path.exists(AGENTS_FILE):
        with open(AGENTS_FILE, "r") as f:
            return json.load(f)
    return {}

# Define custom tools
class WeaviateSearchTool(BaseTool):
    name: str = "search_memory"
    description: str = "Search the agent's memory for relevant information from previous projects"
    
    def _run(self, query: str) -> str:
        return str(search_memory(query))

class WeaviateWriteTool(BaseTool):
    name: str = "store_memory" 
    description: str = "Store important information in the agent's memory for future reference"
    
    def _run(self, content: str, memory_type: str = "general", metadata: dict = None) -> str:
        return str(store_memory(content, memory_type, metadata))

class PerplexityTool(BaseTool):
    name: str = "research_topic"
    description: str = "Research a topic using live web search with citations"
    
    def _run(self, query: str) -> str:
        return str(research_topic(query))

class HexTool(BaseTool):
    name: str = "analyze_data"
    description: str = "Run data analysis and create visualizations using Python"
    
    def _run(self, code: str, description: str = "Analysis") -> str:
        return str(run_data_analysis(code, description))

class TokenEstimatorTool(BaseTool):
    name: str = "estimate_costs"
    description: str = "Estimate API costs for planned work before execution"
    
    def _run(self, prompt: str, expected_tokens: int = 500) -> str:
        return str(estimate_costs(prompt, expected_tokens))

# Initialize tools
weaviate_search = WeaviateSearchTool()
weaviate_write = WeaviateWriteTool()
perplexity_search = PerplexityTool()
hex_analysis = HexTool() 
token_estimator = TokenEstimatorTool()

# Define agents
def create_agents():
    # Set up LLM
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        api_key=os.getenv("OPENAI_API_KEY")
    )
    
    # Load agent configurations from JSON
    agent_configs = load_agent_config_from_json()

    # Helper to get config or default
    def get_config(agent_name, key, default_value):
        return agent_configs.get(agent_name, {}).get(key, default_value)

    manager = Agent(
        role=get_config('manager', 'role', 'Engagement Manager'),
        goal=get_config('manager', 'goal', 'Scope projects clearly, estimate costs, and ensure client satisfaction'),
        backstory=get_config('manager', 'backstory', """You are an experienced engagement manager at a top-tier consulting firm.
        You interview clients, understand their real needs, define clear scope, estimate costs,
        and ensure projects deliver value. You ask sharp, executive-level questions."""),
        tools=[token_estimator],
        llm=llm,
        verbose=True,
        allow_delegation=False
    )
    
    consultant = Agent(
        role=get_config('consultant', 'role', 'Strategy Consultant'),
        goal=get_config('consultant', 'goal', 'Provide strategic insights and synthesize findings into executive recommendations'),
        backstory=get_config('consultant', 'backstory', """You are a senior strategy consultant with 10+ years experience.
        You excel at structured problem-solving, creating compelling narratives, and
        presenting complex analysis in clear, actionable recommendations."""),
        tools=[weaviate_search, weaviate_write],
        llm=llm,
        verbose=True
    )
    
    researcher = Agent(
        role=get_config('researcher', 'role', 'Research Analyst'),
        goal=get_config('researcher', 'goal', 'Conduct thorough market research with reliable sources and citations'),
        backstory=get_config('researcher', 'backstory', """You are a research analyst specializing in market intelligence.
        You use multiple sources, validate information, and always provide citations.
        You excel at finding market data, competitive intelligence, and trends."""),
        tools=[perplexity_search, weaviate_write],
        llm=llm,
        verbose=True
    )
    
    data_engineer = Agent(
        role=get_config('data_engineer', 'role', 'Data Engineer'),
        goal=get_config('data_engineer', 'goal', 'Find, clean, and prepare datasets for analysis'),
        backstory=get_config('data_engineer', 'backstory', """You are a data engineer who finds public datasets, cleans data,
        and prepares it for analysis. You write clean Python code and work with
        APIs, CSVs, and various data sources."""),
        tools=[hex_analysis, weaviate_write],
        llm=llm,
        verbose=True
    )
    
    viz_analyst = Agent(
        role=get_config('viz_analyst', 'role', 'Visualization Analyst'),
        goal=get_config('viz_analyst', 'goal', 'Create compelling charts, dashboards, and visual analysis'),
        backstory=get_config('viz_analyst', 'backstory', """You are a visualization expert who turns data into compelling
        stories through charts and dashboards. You specialize in executive-friendly
        visuals that clearly communicate insights."""),
        tools=[hex_analysis, weaviate_write],
        llm=llm,
        verbose=True
    )
    
    return manager, consultant, researcher, data_engineer, viz_analyst

print("✅ Agent configuration created successfully!")
