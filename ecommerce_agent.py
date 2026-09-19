import os
import sys
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent

from ecommerce_ops import (
    intercept_abandoned_cart, generate_personal_shopper_bundle, trigger_vip_restock,
    deflect_return_request, handle_shipping_exception, optimize_agentic_seo,
    trigger_post_purchase_upsell, predict_creative_fatigue, adjust_dynamic_pricing,
    run_liquidity_copilot, fight_fraud_chargeback, calculate_autonomous_reorder,
    audit_vendor_accountability
)
from dotenv import load_dotenv

# Load API Keys securely from .env
load_dotenv()

def main():
    print("\n============================================")
    print("AUTONOMOUS E-COMMERCE ENTERPRISE AGENT")
    print("============================================")
    
    # 1. Setup Agent with paid tier configuration
    llm = ChatGoogleGenerativeAI(model="gemini-3.6-flash")
    
    tools = [
        intercept_abandoned_cart, generate_personal_shopper_bundle, trigger_vip_restock,
        deflect_return_request, handle_shipping_exception, optimize_agentic_seo,
        trigger_post_purchase_upsell, predict_creative_fatigue, adjust_dynamic_pricing,
        run_liquidity_copilot, fight_fraud_chargeback, calculate_autonomous_reorder,
        audit_vendor_accountability
    ]
    
    system_message = "You are an autonomous E-Commerce Enterprise Agent. You handle operations, marketing, supply chain, and customer experience. Use the provided tools to solve the user's e-commerce problems."
    agent_executor = create_react_agent(llm, tools, state_modifier=system_message)
    
    print("Agent: Hello! I am your AI E-Commerce Copilot. I can negotiate abandoned carts, optimize SEO, adjust dynamic pricing, and fight chargebacks automatically.")
    print("Type 'exit' to quit.\n")
    
    while True:
        try:
            user_input = input("You: ")
            if user_input.lower() in ["exit", "quit"]:
                print("Agent: Shutting down E-Commerce operations. Goodbye!")
                break
                
            print("\nAgent is thinking and processing...")
            
            try:
                response = agent_executor.invoke({"messages": [("user", user_input)]})
                final_msg = response["messages"][-1].content
                print(f"\nAgent: {final_msg}\n")
            except Exception as e:
                print(f"\nAgent Encountered an Error: {str(e)}")
                    
        except KeyboardInterrupt:
            print("\nAgent: Shutting down E-Commerce operations. Goodbye!")
            break

if __name__ == "__main__":
    main()
