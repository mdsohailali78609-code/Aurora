import os
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

os.environ["GOOGLE_API_KEY"] = "AQ.Ab8RN6KTK73UufbJrKVNckqfVisJhpk4p6eHIaZ18WX7_dVqcQ"

# ==========================================
# 🌐 REAL E-COMMERCE API (PLACEHOLDERS)
# ==========================================
# When you get a real website (like Shopify/WooCommerce), paste your API keys here!
REAL_STORE_API_URL = "PASTE_YOUR_STORE_URL_HERE"
REAL_STORE_API_KEY = "PASTE_YOUR_STORE_API_KEY_HERE"

# ==========================================
# 💾 MOCK DATABASE (Fallback System)
# ==========================================
# We have a fake database of orders to test the logic.
MOCK_ORDERS = {
    "101": {"item": "iPhone 15", "type": "mobile", "status": "Shipped", "arrival": "Tomorrow"},
    "102": {"item": "Nike Shoes", "type": "clothing", "status": "Pending Processing", "arrival": "In 3 days"},
    "103": {"item": "Rolex Submariner", "type": "watch", "status": "Pending Processing", "arrival": "In 5 days"}
}

MOCK_PRODUCTS = {
    "mobile": "Samsung Galaxy S24 Ultra (On Sale: 10% Off!)",
    "clothing": "Adidas Ultraboost (Buy 1 Get 1 Free!)",
    "watch": "Apple Watch Ultra 2 (Free Express Shipping!)"
}

# ==========================================
# 🛠️ E-COMMERCE TOOLS
# ==========================================

@tool
def check_order_status(order_id: str) -> str:
    """Use this tool to check the status of a customer's order. Provide the exact order ID."""
    print(f"\n[🔄 BACKEND API] Checking database for Order #{order_id}...")
    
    # --- REAL API INTEGRATION GOES HERE ---
    if REAL_STORE_API_URL != "PASTE_YOUR_STORE_URL_HERE":
        # Future code to pull from real website:
        # response = requests.get(f"{REAL_STORE_API_URL}/orders/{order_id}", headers={"Authorization": REAL_STORE_API_KEY})
        # return response.json()['status']
        pass
        
    # --- FALLBACK TO MOCK DATABASE ---
    order = MOCK_ORDERS.get(order_id)
    if order:
        return f"Order #{order_id} contains {order['item']}. Status: {order['status']}. Expected Arrival: {order['arrival']}."
    return f"Order #{order_id} not found in the system."

@tool
def cancel_order(order_id: str) -> str:
    """Use this tool to cancel an order. Returns the item type that was cancelled so you can up-sell them."""
    print(f"\n[⚠️ BACKEND API] Attempting to cancel Order #{order_id}...")
    
    # --- REAL API INTEGRATION GOES HERE ---
    if REAL_STORE_API_URL != "PASTE_YOUR_STORE_URL_HERE":
        # Future code to push to real website:
        # response = requests.post(f"{REAL_STORE_API_URL}/orders/{order_id}/cancel", headers={"Authorization": REAL_STORE_API_KEY})
        pass
        
    # --- FALLBACK TO MOCK DATABASE ---
    order = MOCK_ORDERS.get(order_id)
    if order:
        if order["status"] == "Shipped":
            return f"Cannot cancel Order #{order_id}. It has already shipped."
        else:
            order["status"] = "Cancelled"
            return f"Order #{order_id} successfully cancelled. The item type was: {order['type']}."
    return f"Order #{order_id} not found."

@tool
def recommend_alternative(item_type: str) -> str:
    """Use this tool immediately after a customer cancels an order to find a replacement item to up-sell them."""
    print(f"\n[🛍️ BACKEND API] Finding alternative deals for category: '{item_type}'...")
    
    # --- REAL API INTEGRATION GOES HERE ---
    if REAL_STORE_API_URL != "PASTE_YOUR_STORE_URL_HERE":
        # Future code to pull from real website:
        # response = requests.get(f"{REAL_STORE_API_URL}/products?category={item_type}&sort=discount", headers={"Authorization": REAL_STORE_API_KEY})
        pass
        
    # --- FALLBACK TO MOCK DATABASE ---
    deal = MOCK_PRODUCTS.get(item_type.lower())
    if deal:
        return f"We have a special promotion available right now: {deal}"
    return "No alternative products found in that category."

# ==========================================
# 🤖 THE SUPPORT BOT
# ==========================================

tools = [check_order_status, cancel_order, recommend_alternative]
llm = ChatGoogleGenerativeAI(model="gemini-3.6-flash")

system_prompt = """You are an automated Customer Support Bot for an e-commerce store.
You are chatting directly with customers on WhatsApp. Keep your replies friendly, helpful, and concise.

CRITICAL RULES:
1. If they don't provide an Order ID, politely ask for it.
2. If they ask where their order is, use the `check_order_status` tool.
3. If they want to cancel an order, use the `cancel_order` tool.
4. UP-SELL PROTOCOL: If you successfully cancel an order, you MUST immediately use the `recommend_alternative` tool using the item type returned from the cancellation. Then, pitch that new alternative to the customer to save the sale!"""

# Setup the looping agent with state memory
checkpointer = MemorySaver()
agent = create_react_agent(llm, tools, checkpointer=checkpointer)

# ==========================================
# 📥 INBOX SIMULATOR
# ==========================================
if __name__ == "__main__":
    print("\n==========================================")
    print("🎧 E-COMMERCE CUSTOMER SUPPORT BOT ONLINE")
    print("==========================================")
    print("Hint: Try saying 'Where is my order 101?' or 'Cancel order 103'")
    
    config = {"configurable": {"thread_id": "support_session_1"}}
    
    while True:
        try:
            customer_msg = input("\n[📥 WhatsApp Customer]: ")
            if customer_msg.lower() in ['quit', 'exit']:
                break
            if not customer_msg.strip():
                continue
                
            print("[🤖 Bot is reading and processing...]")
            
            # The agent autonomously processes the message and uses tools.
            # We inject the system prompt here to avoid version compatibility issues with create_react_agent.
            result = agent.invoke({"messages": [("system", system_prompt), ("user", customer_msg)]}, config=config)
            
            final_reply = result['messages'][-1].content
            print(f"\n[📤 Automated Reply]: {final_reply}")
            
        except Exception as e:
            print(f"\n[❌ RATE LIMIT ERROR] Google API exhausted. Wait until tomorrow or enable billing.\nError Code: {e}")
            break
