from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3
from state import AgentState
from nodes import wan_qing_node, xin_jing_node, xing_zhe_node, router_node

conn = sqlite3.connect("memories.db", check_same_thread=False)
memory = SqliteSaver(conn)

workflow_wq = StateGraph(AgentState)
workflow_wq.add_node("wan_qing", wan_qing_node)
workflow_wq.set_entry_point("wan_qing")
workflow_wq.add_edge("wan_qing", END)
app_wanqing = workflow_wq.compile(checkpointer=memory)

workflow_xj = StateGraph(AgentState)
workflow_xj.add_node("xin_jing", xin_jing_node)
workflow_xj.set_entry_point("xin_jing")
workflow_xj.add_edge("xin_jing", END)
app_xinjing = workflow_xj.compile(checkpointer=memory)

workflow_xz = StateGraph(AgentState)
workflow_xz.add_node("xing_zhe", xing_zhe_node)
workflow_xz.set_entry_point("xing_zhe")
workflow_xz.add_edge("xing_zhe", END)
app_xingzhe = workflow_xz.compile(checkpointer=memory)

# Router Workflow
workflow_router = StateGraph(AgentState)
workflow_router.add_node("router", router_node)
workflow_router.add_node("wan_qing", wan_qing_node)
workflow_router.add_node("xin_jing", xin_jing_node)
workflow_router.add_node("xing_zhe", xing_zhe_node)

workflow_router.set_entry_point("router")

def route_next(state: AgentState):
    return state["next"]

workflow_router.add_conditional_edges(
    "router",
    route_next,
    {
        "wan_qing": "wan_qing",
        "xin_jing": "xin_jing",
        "xing_zhe": "xing_zhe"
    }
)

workflow_router.add_edge("wan_qing", END)
workflow_router.add_edge("xin_jing", END)
workflow_router.add_edge("xing_zhe", END)

app_router = workflow_router.compile(checkpointer=memory)
