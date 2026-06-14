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


class State(TypedDict):
    messages: Annotated[list, add_messages]


tools = [run_linter, run_security_scan, run_complexity_check]

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
    file_path = "sample_bad_code.py"

    print("ReviewAgent — Milestone 2 Test")
    print(f"Target file: {file_path}\n")

    tests = [
        ("Lint check", f"Run the linter on {file_path} and report what you find."),
        ("Security scan", f"Check {file_path} for security vulnerabilities."),
        ("Complexity check", f"Analyze the complexity of functions in {file_path}."),
        ("Full review", f"Run a complete code review on {file_path} — check lint, security, and complexity."),
    ]

    for label, prompt in tests:
        print(f"\n{'='*55}")
        print(f"TEST: {label}")
        print("-" * 55)
        result = graph.invoke({"messages": [HumanMessage(content=prompt)]})
        print(result["messages"][-1].content)

    print("\n Milestone 2 selesai!")