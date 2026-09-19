import os
from custom_agent_factory import create_custom_agent

os.environ["GOOGLE_API_KEY"] = "AQ.Ab8RN6KTK73UufbJrKVNckqfVisJhpk4p6eHIaZ18WX7_dVqcQ"

def test_custom_agent():
    print("Initializing Acme Support Bot...")
    try:
        agent_data = create_custom_agent("client_acme_001")
        agent_executor = agent_data["executor"]
        system_prompt = agent_data["system_prompt"]
        print("Agent created successfully!")
        
        print("\nSending test prompt: 'Hi, I need a refund.'")
        from langchain_core.messages import SystemMessage, HumanMessage
        messages = [SystemMessage(content=system_prompt), HumanMessage(content="Hi, I need a refund.")]
        response = agent_executor.invoke({"messages": messages}, config={"configurable": {"thread_id": "test_1"}})
        
        final_msg = response["messages"][-1]
        print("\nAgent Response:")
        print(final_msg.content)
        
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    test_custom_agent()
