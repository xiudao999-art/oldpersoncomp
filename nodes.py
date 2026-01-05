import os
import re
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from state import AgentState
from prompts import WAN_QING_SYSTEM_PROMPT, XIN_JING_SYSTEM_PROMPT, XING_ZHE_SYSTEM_PROMPT, ROUTER_SYSTEM_PROMPT
from dotenv import load_dotenv

load_dotenv()

# Initialize the model
# Using ChatOpenAI compatible client for Doubao (Volcengine)
# The user needs to set OPENAI_API_KEY and OPENAI_API_BASE in .env
# Defaulting to Volcengine endpoint if not set, but key is required.
llm = ChatOpenAI(
    model=os.getenv("MODEL_NAME", "doubao-pro-32k"),
    temperature=0.7,
    openai_api_base=os.getenv("OPENAI_API_BASE", "https://ark.cn-beijing.volces.com/api/v3"),
    openai_api_key=os.getenv("OPENAI_API_KEY"),
)

def clean_history(messages):
    """
    Clean the message history for context consistency:
    1. Remove Router's internal SystemMessages (ROUTER_JSON_START)
    2. Remove <inner_thought> and <inner_monologue> blocks from AIMessages
    3. Keep only the last 20 messages (approx 10 turns) to focus on recent context
    """
    cleaned = []
    for msg in messages:
        # 1. Skip Router internal messages
        if isinstance(msg, SystemMessage) and "ROUTER_JSON_START" in str(msg.content):
            continue
            
        # 2. Clean AIMessages
        if isinstance(msg, AIMessage):
            content = msg.content
            # Remove <inner_thought>
            content = re.sub(r'<inner_thought>.*?</inner_thought>', '', content, flags=re.DOTALL)
            # Remove <inner_monologue>
            content = re.sub(r'<inner_monologue>.*?</inner_monologue>', '', content, flags=re.DOTALL)
            
            content = content.strip()
            # If empty after cleaning (e.g. only had thought), skip it to avoid confusing the model
            if not content:
                continue 
                
            cleaned.append(AIMessage(content=content))
        else:
            cleaned.append(msg)
            
    # 3. Slice to keep last 20 messages (User + AI pairs = 10 turns)
    # We prioritize keeping the most recent interactions
    if len(cleaned) > 20:
        cleaned = cleaned[-20:]
        
    return cleaned

def router_node(state: AgentState):
    messages = state["messages"]
    
    # Use clean history for context so Router sees the conversation flow
    clean_msgs = clean_history(messages)
    
    # Construct the input for the router
    router_input = [SystemMessage(content=ROUTER_SYSTEM_PROMPT)] + clean_msgs
    
    response = llm.invoke(router_input)
    content = response.content.strip()
    
    # Clean up markdown code blocks if present
    if content.startswith("```json"):
        content = content[7:]
    if content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]
    content = content.strip()
    
    try:
        analysis = json.loads(content)
        
        # Handle both flat and nested structures for robustness
        target = analysis.get("分发目标")
        if not target:
            target = analysis.get("分发决策", {}).get("目标Agent", "晚晴")
            
        # Normalize target name
        if "晚晴" in target:
            target = "wan_qing"
        elif "心镜" in target:
            target = "xin_jing"
        elif "行者" in target:
            target = "xing_zhe"
        else:
            target = "wan_qing" # Default fallback
            
        print("\n[Router Analysis JSON]")
        print(json.dumps(analysis, ensure_ascii=False, indent=2))
        print("-" * 40)
        
        # Pass the analysis JSON string in the SystemMessage so the UI can extract it
        analysis_json_str = json.dumps(analysis, ensure_ascii=False)
        return {"messages": [SystemMessage(content=f"ROUTER_JSON_START{analysis_json_str}ROUTER_JSON_END\nRouter Decision: {target}. Suggestion: {analysis.get('建议话术')}")], "next": target}
    except Exception as e:
        print(f"Router parsing error: {e}")
        return {"messages": [], "next": "wan_qing"} # Fallback to safety

def wan_qing_node(state: AgentState):
    messages = state["messages"]
    clean_msgs = clean_history(messages)
    full_messages = [SystemMessage(content=WAN_QING_SYSTEM_PROMPT)] + clean_msgs
    response = llm.invoke(full_messages)
    return {"messages": [response]}

def xin_jing_node(state: AgentState):
    messages = state["messages"]
    clean_msgs = clean_history(messages)
    full_messages = [SystemMessage(content=XIN_JING_SYSTEM_PROMPT)] + clean_msgs
    response = llm.invoke(full_messages)
    return {"messages": [response]}

def xing_zhe_node(state: AgentState):
    messages = state["messages"]
    clean_msgs = clean_history(messages)
    full_messages = [SystemMessage(content=XING_ZHE_SYSTEM_PROMPT)] + clean_msgs
    response = llm.invoke(full_messages)
    return {"messages": [response]}
