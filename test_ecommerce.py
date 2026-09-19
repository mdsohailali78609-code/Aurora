import os
from custom_agent_factory import create_custom_agent
from langchain_core.messages import SystemMessage, HumanMessage

os.environ["GOOGLE_API_KEY"] = "AQ.Ab8RN6KTK73UufbJrKVNckqfVisJhpk4p6eHIaZ18WX7_dVqcQ"

def test_ecommerce_agent():
    print("\n--- E-COMMERCE AGENT TEST ---")
    print("Loading Acme Support & E-commerce Bot from database...")
    
    # In custom_agents.json, we have 'client_acme_001' which currently has 'search_web' and 'deflect_return_request'
    # We will temporarily update custom_agents.json to add 'intercept_abandoned_cart'
    agent_data = create_custom_agent("client_acme_001")
    
    print("Agent Loaded! Sending Command: 'John abandoned a cart with a Nike Shirt in it. Text him on WhatsApp.'\n")
    
    messages = [
        SystemMessage(content=agent_data["system_prompt"]),
        HumanMessage(content="John abandoned a cart with a Nike Shirt in it. Intercept him on WhatsApp.")
    ]
    
    response = agent_data["executor"].invoke({"messages": messages}, config={"configurable": {"thread_id": "test_ecom_1"}})
    
    print("🤖 Agent Output:")
    print(response["messages"][-1].content)
    print("-----------------------------\n")

if __name__ == "__main__":
    test_ecommerce_agent()
