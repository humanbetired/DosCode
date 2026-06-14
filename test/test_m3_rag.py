from typing import Annotated, Literal
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from typing_extensions import TypedDict

from agents.tools.lint_tool import run_linter
from agents.tools.security_tool import run_security_scan
from agents.tools.complexity_tool import run_complexity_check
from agents.tools.rag_tool import query_style_guide

class State(TypedDict):
    messages: Annotated[list, add_messages]


tools = [run_linter, run_security_scan, run_complexity_check, query_style_guide]

llm = ChatOllama(
    model="qwen2.5:1.5b",
    temperature=0,
    base_url="http://127.0.0.1:11434"
)
llm_with_tools = llm.bind_tools(tools)


def agent_node(state: State) -> State:
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}

tool_node = ToolNode(tools)


def should_use_tool(state: State) -> Literal["tools", "end"]:
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        names = [t["name"] for t in last.tool_calls]
        print(f"  → Tool dipanggil: {names}")
        return "tools"
    return "end"


builder = StateGraph(State)
builder.add_node("agent", agent_node)
builder.add_node("tools", tool_node)
builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", should_use_tool, {"tools": "tools", "end": END})
builder.add_edge("tools", "agent")
graph = builder.compile()


if __name__ == "__main__":
    print("ReviewAgent — Milestone 3 Test\n")

    tests = [
        (
            "RAG saja — query langsung",
            "What does our style guide say about hardcoded passwords and security rules?"
        ),
        (
            "Lint + RAG — agent cross-check",
            "Run linter on sample_bad_code.py, then check our style guide for the naming convention rules that were violated."
        ),
        (
            "Security + RAG — agent investigasi",
            "Scan sample_bad_code.py for security issues, then look up our team standards for how serious these violations are."
        ),
    ]

    for label, prompt in tests:
        print(f"\n{'='*55}")
        print(f"TEST: {label}")
        print("-" * 55)
        result = graph.invoke({"messages": [HumanMessage(content=prompt)]})
        print(result["messages"][-1].content)

    print("\nMilestone 3 selesai!")