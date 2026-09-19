import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent

from desktop_ops import (
    execute_computer_use_vision, bridge_legacy_app, use_semantic_clipboard, execute_meeting_to_action,
    record_auto_macro, organize_downloads_folder, visual_form_rekeying, triage_local_email,
    semantic_screen_rewind, natural_language_terminal, context_hover_summary, search_local_knowledge_graph,
    intercept_os_notifications, orchestrate_workspace, compile_async_status, synthesize_read_it_later,
    process_local_slm, request_permission_gate, audit_visual_trail, access_sandboxed_credentials
)
from dotenv import load_dotenv

# Load API Keys securely from .env
load_dotenv()

def main():
    print("\n============================================")
    print("AUTONOMOUS DESKTOP OS AGENT")
    print("============================================")
    
    # 1. Setup Agent with paid tier configuration
    llm = ChatGoogleGenerativeAI(model="gemini-3.6-flash")
    
    tools = [
        execute_computer_use_vision, bridge_legacy_app, use_semantic_clipboard, execute_meeting_to_action,
        record_auto_macro, organize_downloads_folder, visual_form_rekeying, triage_local_email,
        semantic_screen_rewind, natural_language_terminal, context_hover_summary, search_local_knowledge_graph,
        intercept_os_notifications, orchestrate_workspace, compile_async_status, synthesize_read_it_later,
        process_local_slm, request_permission_gate, audit_visual_trail, access_sandboxed_credentials
    ]
    
    system_message = "You are an autonomous OS-level Desktop Assistant. You have deep system access to control mouse/keyboard, manage files, search screen history, and organize the user's workspace. Always respect the Enterprise Trust Layer (ask for permission on destructive actions)."
    agent_executor = create_react_agent(llm, tools, state_modifier=system_message)
    
    print("Agent: Hello! I am your AI Desktop Copilot. I can organize files, summarize meetings, orchestrate your workspace, and operate legacy apps via Computer Vision.")
    print("Type 'exit' to quit.\n")
    
    while True:
        try:
            user_input = input("You: ")
            if user_input.lower() in ["exit", "quit"]:
                print("Agent: Shutting down OS Copilot. Goodbye!")
                break
                
            print("\nAgent is thinking and processing...")
            
            try:
                response = agent_executor.invoke({"messages": [("user", user_input)]})
                final_msg = response["messages"][-1].content
                print(f"\nAgent: {final_msg}\n")
            except Exception as e:
                print(f"\nAgent Encountered an Error: {str(e)}")
                    
        except KeyboardInterrupt:
            print("\nAgent: Shutting down OS Copilot. Goodbye!")
            break

if __name__ == "__main__":
    main()
