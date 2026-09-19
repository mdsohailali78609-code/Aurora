import os
import sys
from langchain_core.messages import SystemMessage, HumanMessage
from custom_agent_factory import create_custom_agent
import logging

# Hide langgraph/langchain debug warnings
logging.getLogger("aurora_server").setLevel(logging.ERROR)

os.environ["GOOGLE_API_KEY"] = "AQ.Ab8RN6KTK73UufbJrKVNckqfVisJhpk4p6eHIaZ18WX7_dVqcQ"

def start_ecommerce_cli():
    print("\n===========================================")
    print("🛍️  E-COMMERCE AGENT - INTERACTIVE TEST")
    print("===========================================")
    print("\nTools Available:")
    print("- intercept_abandoned_cart")
    print("- generate_personal_shopper_bundle")
    print("- deflect_return_request")
    print("- trigger_vip_restock")
    print("- predict_creative_fatigue")
    print("\nType 'quit' to exit.")
    
    # We will hijack the custom agent factory by temporarily modifying the cache/config or just creating one inline.
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langgraph.prebuilt import create_react_agent
    from tool_registry import get_tools

    llm = ChatGoogleGenerativeAI(model="gemini-3.6-flash", temperature=0.2)
    tools = get_tools([
        "intercept_abandoned_cart", "generate_personal_shopper_bundle", 
        "trigger_vip_restock", "deflect_return_request", "predict_creative_fatigue"
    ])
    
    system_prompt = "You are a high-level E-Commerce AI. You have access to tools to manage stores. Execute them when requested."
    
    agent_executor = create_react_agent(model=llm, tools=tools)
    
    chat_history = [SystemMessage(content=system_prompt)]
    
    while True:
        try:
            user_input = input("\nYou: ")
            if user_input.lower() in ['quit', 'exit']:
                break
                
            chat_history.append(HumanMessage(content=user_input))
            
            print("🤖 Agent is thinking (and possibly executing tools)...")
            response = agent_executor.invoke({"messages": chat_history}, config={"configurable": {"thread_id": "test_ecom_cli"}})
            
            final_msg = response["messages"][-1]
            chat_history.append(final_msg)
            
            print(f"\nAgent:\n{final_msg.content}")
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    start_ecommerce_cli()
