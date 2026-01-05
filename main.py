import os
import sys
from langchain_core.messages import HumanMessage
from graph import app_wanqing, app_xinjing, app_xingzhe, app_router
from dotenv import load_dotenv

load_dotenv()

def main():
    print("Elderly Care Agents Initialized. Type 'quit' to exit.")
    print("Note: Ensure you have set OPENAI_API_KEY and OPENAI_API_BASE in .env")
    print("------------------------------------------------")
    
    # Check for API Key
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not found in environment variables.")
        print("Please create a .env file with your API key.")
        return

    # Default to Router Agent
    agent_choice = "自动"
    app = app_router
    print(f"已激活模式：{agent_choice} (Router Mode)")
    print("------------------------------------------------")

    # Ask for name to establish long-term memory
    user_name = ""
    # sys.argv[1] is now user_name (since agent_choice is fixed)
    if len(sys.argv) > 1:
        user_name = sys.argv[1]
        
    if not user_name:
        user_name = input("请输入老人的名字 (这将用于加载专属记忆): ").strip()
        
    if not user_name:
        user_name = "default_user"
        print("未输入名字，使用默认记忆库: default_user")
    
    # 针对不同Agent使用独立的thread_id，避免记忆污染
    # thread_id 格式：Agent名:老人姓名
    # 对于Router模式，我们使用 "Router:老人姓名" 作为 thread_id
    thread_id = f"Router:{user_name}"
    print(f"\n已加载长期记忆库，ID: {thread_id}")
    print("------------------------------------------------")

    config = {"configurable": {"thread_id": thread_id}}
    
    initial_message = ""
    # sys.argv[2] is now initial_message
    if len(sys.argv) > 2:
        initial_message = sys.argv[2]
        print(f"User (Auto): {initial_message}")

    while True:
        try:
            if initial_message:
                user_input = initial_message
                initial_message = "" # Clear after first use
            else:
                user_input = input("User: ")
                
            if user_input.lower() in ["quit", "exit"]:
                break
            
            if not user_input.strip():
                continue

            inputs = {"messages": [HumanMessage(content=user_input)]}
            
            thinking_label = "Router Agent"
                
            print(f"{thinking_label} is thinking...", end="\r")

            
            # Stream the graph execution
            # We look for the final output from the agent
            for event in app.stream(inputs, config=config):
                for key, value in event.items():
                    if key in ["wan_qing", "xin_jing", "xing_zhe"]:
                        last_msg = value["messages"][-1]
                        
                        speaker = "晚晴"
                        if key == "xin_jing":
                            speaker = "心镜"
                        elif key == "xing_zhe":
                            speaker = "行者"
                            
                        print(f"\n{speaker}: {last_msg.content}")
                        print("------------------------------------------------")
                        
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"\nAn error occurred: {e}")

if __name__ == "__main__":
    main()
