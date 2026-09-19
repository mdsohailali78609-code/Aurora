import os
import json
import logging
from typing import Dict, Any

from langchain_core.messages import SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from tool_registry import get_tools

logger = logging.getLogger(__name__)

# Cache for loaded agents to avoid recreating them on every request
_AGENT_CACHE: Dict[str, Any] = {}

def load_client_config(client_id: str) -> dict:
    """Loads a client's agent configuration from the mock JSON database."""
    try:
        with open("custom_agents.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get(client_id)
    except FileNotFoundError:
        logger.error("custom_agents.json database not found.")
        return None

def create_custom_agent(client_id: str):
    """
    Dynamically constructs a LangGraph ReAct agent based on the client's configuration.
    Uses caching so the agent doesn't need to be rebuilt from scratch on every chat message.
    """
    if client_id in _AGENT_CACHE:
        return _AGENT_CACHE[client_id]

    config = load_client_config(client_id)
    if not config:
        raise ValueError(f"No custom agent configuration found for client: {client_id}")
        
    agent_name = config.get("name", "Custom Agent")
    logger.info(f"Building Custom Agent: {agent_name} for {client_id}...")

    # 1. Initialize the LLM (Gemini 3.6 Flash)
    llm = ChatGoogleGenerativeAI(model="gemini-3.6-flash", temperature=0.2)
    
    # 2. Fetch the specific tools authorized for this client
    tool_ids = config.get("tools", [])
    tools = get_tools(tool_ids)
    
    if not tools:
        logger.warning(f"Agent {agent_name} has no valid tools configured!")
        
    # 4. Build the ReAct Agent using LangGraph
    agent_executor = create_react_agent(
        model=llm,
        tools=tools
    )
    
    # Store system prompt in cache alongside the executor so it can be used during invocation
    _AGENT_CACHE[client_id] = {
        "executor": agent_executor,
        "system_prompt": config.get("system_prompt", "You are a helpful AI assistant.")
    }
    return _AGENT_CACHE[client_id]
