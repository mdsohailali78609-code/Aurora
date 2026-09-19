import os
from social_agent import agent_executor

try:
    response = agent_executor.invoke({
        "messages": [("user", "tell me most trending video from tiktok")]
    })
    print(response["messages"][-1].content)
except Exception as e:
    print(f"EXCEPTION_CAUGHT: {type(e).__name__}: {e}")
