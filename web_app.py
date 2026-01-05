import streamlit as st
import os
import sys
import numpy as np

# Load secrets into environment variables for Streamlit Cloud
# This must be done BEFORE importing modules that initialize clients (like graph -> nodes)
try:
    if hasattr(st, "secrets"):
        for key in ["OPENAI_API_KEY", "OPENAI_API_BASE", "MODEL_NAME", "ALIYUN_APPKEY", "ALIYUN_TOKEN"]:
            if key in st.secrets and key not in os.environ:
                os.environ[key] = st.secrets[key]
except FileNotFoundError:
    pass # No secrets file found, likely running locally without .streamlit/secrets.toml
except Exception as e:
    print(f"Warning: Failed to load secrets: {e}")

# Monkeypatch to fix compatibility between bokeh<3.0.0 and numpy>=2.0.0
# These types were removed in NumPy 1.24/2.0 but are used by older Bokeh versions
try:
    if not hasattr(np, 'bool8'):
        np.bool8 = np.bool_
    if not hasattr(np, 'int'):
        np.int = int
    if not hasattr(np, 'float'):
        np.float = float
    if not hasattr(np, 'object'):
        np.object = object
except Exception as e:
    print(f"Warning: NumPy monkeypatch failed: {e}")

from langchain_core.messages import HumanMessage, AIMessage
from dotenv import load_dotenv
import re
import json

# Load environment variables (for local dev)
load_dotenv()

# Import graph AFTER loading secrets/env vars
from graph import app_router

# Page Config
st.set_page_config(page_title="老年陪伴 Agent", page_icon="👴", initial_sidebar_state="expanded")

# Custom Header
st.markdown("""
<div class="custom-header" style="
    position: sticky;
    top: 0;
    width: 100%;
    height: 3.5rem;
    background-color: #ffffff;
    border-bottom: 1px solid #cccccc;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    z-index: 50;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.2rem;
    font-weight: 600;
    color: #000;
    margin-bottom: 1rem;
">
    👴 老年陪伴 Agent
</div>
""", unsafe_allow_html=True)

# Footer Background (White layer spanning 100vw)
st.markdown("""
<div id="footer-bg" style="
    position: fixed;
    bottom: 0;
    left: 0;
    width: 100vw;
    height: 80px; /* Adjust height as needed */
    background-color: #ffffff;
    border-top: 1px solid #e0e0e0;
    z-index: 49; /* Behind the content */
    box-shadow: 0 -2px 10px rgba(0,0,0,0.05);
    transition: left 0.3s ease;
"></div>
""", unsafe_allow_html=True)

# Custom CSS
st.markdown("""
    <style>
    /* Force wrapping for code blocks and preformatted text to avoid horizontal scrolling */
    pre, code {
        white-space: pre-wrap !important;
        word-break: break-word !important;
    }
    /* Ensure main chat container allows wrapping */
    .stChatMessage .stMarkdown {
        word-wrap: break-word !important;
    }
    
    /* App background color */
    .stApp {
        background-color: #f5f5f5;
    }
    
    /* Hide the default Streamlit footer and header */
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Remove top padding so sticky header sits at top */
    .block-container {
        padding-top: 0rem !important;
        padding-bottom: 120px !important; /* Space for footer */
    }
    
    /* Input Content Container (The Columns) */
    div[data-testid="stHorizontalBlock"]:has(div#input-anchor) {
        position: fixed;
        bottom: 15px; /* Vertically centered in the 80px footer-bg */
        left: 50%;
        transform: translateX(-50%);
        width: 100%;
        max-width: 46rem; /* Standard Streamlit width constraint */
        z-index: 50;
        align-items: center;
        transition: left 0.3s ease;
    }

    /* Sidebar Awareness: Shift Footer Background */
    div.stApp:has(section[data-testid="stSidebar"][aria-expanded="true"]) div#footer-bg {
        left: 21rem;
        width: calc(100vw - 21rem);
    }
    
    /* Sidebar Awareness: Shift Input Content */
    div.stApp:has(section[data-testid="stSidebar"][aria-expanded="true"]) div[data-testid="stHorizontalBlock"]:has(div#input-anchor) {
        /* Shift the center point to be the center of the remaining space */
        left: calc(21rem + (100vw - 21rem)/2);
        transform: translateX(-50%);
    }
    
    /* Ensure Header doesn't overlap Sidebar on mobile or small screens if Sidebar is open */
    div.stApp:has(section[data-testid="stSidebar"][aria-expanded="true"]) .custom-header {
         /* Sticky header usually respects sidebar, but if it doesn't, we can force it */
    }
    
    /* Hide default form borders to make it cleaner */
    div[data-testid="stHorizontalBlock"]:has(div#input-anchor) .stTextInput > div > div {
        border: none;
        background-color: #f0f2f5;
        border-radius: 20px;
    }
    
    /* Adjust padding for smaller screens */
    @media (max-width: 640px) {
        div[data-testid="stHorizontalBlock"]:has(div#input-anchor) {
            padding: 0 10px;
        }
    }
    </style>
""", unsafe_allow_html=True)

# Sidebar for User Settings
with st.sidebar:
    st.header("设置")
    user_name = st.text_input("请输入您的名字", value="张伯伯")
    st.markdown("---")
    st.markdown("**说明**：")
    st.markdown("1. 支持文字输入")
    st.markdown("2. 系统会自动选择最合适的陪伴模式 (晚晴/心镜/行者)")

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = []
if "thread_id" not in st.session_state:
    st.session_state.thread_id = f"Router:{user_name}"
if "processing_input" not in st.session_state:
    st.session_state.processing_input = False
if "last_audio_bytes" not in st.session_state:
    st.session_state.last_audio_bytes = None

# Update thread_id if user_name changes
current_thread_id = f"Router:{user_name}"
if st.session_state.thread_id != current_thread_id:
    st.session_state.thread_id = current_thread_id
    st.toast(f"已切换用户: {user_name}")

# Display Chat History
for msg in st.session_state.messages:
    if isinstance(msg, HumanMessage):
        with st.chat_message("user"):
            st.markdown(msg.content)
    elif isinstance(msg, AIMessage):
        with st.chat_message("assistant"):
            # Display Router Analysis if available
            if "router_analysis" in msg.additional_kwargs and msg.additional_kwargs["router_analysis"]:
                with st.expander("🔍 Router 意图分析 (点击展开)", expanded=False):
                    st.json(msg.additional_kwargs["router_analysis"])
            
            # Display Thought Process if available
            if "thought_content" in msg.additional_kwargs and msg.additional_kwargs["thought_content"]:
                agent_name = msg.additional_kwargs.get("agent_name", "Agent")
                with st.expander(f"💭 {agent_name} Agent 思考过程 (点击展开)", expanded=False):
                    st.markdown(msg.additional_kwargs["thought_content"])
            
            st.markdown(msg.content)

# Logic to generate response
def generate_response(user_input):
    # Process with Agent
    config = {"configurable": {"thread_id": st.session_state.thread_id}}
    inputs = {"messages": [HumanMessage(content=user_input)]}
    
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        router_analysis = None
        thought_content = None
        agent_name_for_history = "Agent"
        
        # Show "Thinking..." indicator
        with st.spinner("Agent正在思考中..."):
            try:
                # Use stream to get real-time response
                for event in app_router.stream(inputs, config=config):
                    for key, value in event.items():
                        # Capture Router Analysis if available
                        if "messages" in value:
                            messages = value["messages"]
                            if messages:
                                last_msg_content = messages[-1].content
                                # Check for hidden Router JSON
                                if "ROUTER_JSON_START" in last_msg_content and "ROUTER_JSON_END" in last_msg_content:
                                    try:
                                        start_idx = last_msg_content.find("ROUTER_JSON_START") + 17
                                        end_idx = last_msg_content.find("ROUTER_JSON_END")
                                        json_str = last_msg_content[start_idx:end_idx]
                                        router_analysis = json.loads(json_str)
                                    except Exception as e:
                                        print(f"Error parsing router JSON in web app: {e}")

                        # We are looking for the final response from one of the agents
                        if "messages" in value:
                            messages = value["messages"]
                            if messages and isinstance(messages[-1], (AIMessage, HumanMessage)): # Usually AIMessage from agent
                                content = messages[-1].content
                                
                                # If the key is one of our agents, it's likely the final response
                                if key in ["wan_qing", "xin_jing", "xing_zhe"]:
                                    full_response = content
                                    
                                    # Clean up Markdown code blocks if present
                                    full_response = re.sub(r'^```\w*\s*', '', full_response)
                                    full_response = re.sub(r'\s*```$', '', full_response)
                                    
                                    # Extract inner_thought
                                    thought_pattern = re.compile(r'<inner_thought>(.*?)</inner_thought>', re.DOTALL)
                                    match = thought_pattern.search(full_response)
                                    if match:
                                        thought_content = match.group(1).strip()
                                        full_response = thought_pattern.sub('', full_response).strip()
                                    
                                    monologue_pattern = re.compile(r'<inner_monologue>(.*?)</inner_monologue>', re.DOTALL)
                                    match = monologue_pattern.search(full_response)
                                    if match:
                                        thought_content = match.group(1).strip()
                                        full_response = monologue_pattern.sub('', full_response).strip()
                                    
                                    # Display Router Analysis Expander if available
                                    if router_analysis:
                                        with st.expander("🔍 Router 意图分析 (点击展开)", expanded=False):
                                            st.json(router_analysis)
                                    
                                    # Display Agent Thought Expander if available
                                    agent_display_names = {
                                        "wan_qing": "晚晴",
                                        "xin_jing": "心镜",
                                        "xing_zhe": "行者"
                                    }
                                    agent_name = agent_display_names.get(key, key)
                                    agent_name_for_history = agent_name
                                    
                                    with st.expander(f"💭 {agent_name} Agent 思考过程 (点击展开)", expanded=False):
                                        st.markdown(thought_content if thought_content else "（本次无返回或模型未生成）")
                                    
                                    message_placeholder.markdown(full_response)
            except Exception as e:
                st.error(f"发生错误: {e}")
                return

        # If we got a response, save it
        if full_response:
            ai_msg = AIMessage(
                content=full_response,
                additional_kwargs={
                    "router_analysis": router_analysis,
                    "thought_content": thought_content,
                    "agent_name": agent_name_for_history
                }
            )
            st.session_state.messages.append(ai_msg)


# Input Area
# Add Audio Input
from aliyun_asr_short import recognize_short_speech
from audio_recorder_ptt import audio_recorder_ptt

# Callback to handle text input
def handle_text_input():
    if st.session_state.user_input_text:
        # Just update state, don't write to UI
        st.session_state.messages.append(HumanMessage(content=st.session_state.user_input_text))
        st.session_state.processing_input = True
        st.session_state.user_input_text = ""

# Container for input widgets at the bottom
# We use columns to create the Horizontal Block
# 9:1 ratio for compact button layout
col1, col2 = st.columns([0.88, 0.12])

with col1:
    # Anchor for CSS positioning - INSIDE col1 to allow selecting the parent HorizontalBlock
    st.markdown('<div id="input-anchor"></div>', unsafe_allow_html=True)
    st.text_input(
        "请输入文字", 
        key="user_input_text", 
        label_visibility="collapsed", 
        placeholder="请输入文字... (按回车发送)",
        on_change=handle_text_input
    )

with col2:
    # PTT Audio Recorder
    try:
        audio_bytes = audio_recorder_ptt(
            text="",
            recording_color="#e74c3c",
            neutral_color="#07C160",
            icon_name="microphone",
            icon_size="2x",
            key="ptt_recorder_component_v5" 
        )
    except Exception as e:
        st.error(f"加载失败: {e}")
        audio_bytes = None

# Logic Handling
# 1. Handle Audio Input
if audio_bytes and audio_bytes != st.session_state.last_audio_bytes and not st.session_state.processing_input:
    # Mark as processed to prevent loops
    st.session_state.last_audio_bytes = audio_bytes
    
    st.info("接收到语音数据，正在识别...")
    text = recognize_short_speech(audio_bytes)
    
    if text and not text.startswith("ASR Error") and not text.startswith("ASR Exception"):
        # st.success(f"识别结果: {text}") # Optional feedback
        st.session_state.messages.append(HumanMessage(content=text))
        st.session_state.processing_input = True
        st.rerun() # Rerun to update UI with new message and trigger processing
    elif text:
        st.error(text)
    else:
        st.warning("未识别到有效的语音内容，请说话声音大一点或检查麦克风。")

# 2. Handle Processing (Text or Audio Transcribed)
if st.session_state.processing_input:
    # Get the last message (which is the user input)
    if st.session_state.messages and isinstance(st.session_state.messages[-1], HumanMessage):
        last_user_input = st.session_state.messages[-1].content
        # We need to rerun to show the user message FIRST? 
        # No, we already appended it to messages list.
        # And the loop at the top has already displayed it (if we rerun).
        # But if we are in the SAME run as the callback (for text input), 
        # the loop at top ran BEFORE the callback updated messages?
        # YES. For text input:
        # Run 1: Loop runs (old msgs). Callback runs (adds new msg, sets flag). Script finishes.
        # Run 2: Loop runs (shows new msg). Flag is True. Enters here. Generates response.
        
        # So we are good.
        st.session_state.processing_input = False # Reset flag
        generate_response(last_user_input)
        st.rerun() # Rerun to show the final result and update state cleanly
