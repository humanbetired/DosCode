from typing import Annotated, Literal
from langchain_ollama import ChatOllama
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from typing_extensions import TypedDict



class State(TypedDict):
    messages: Annotated[list, add_messages]


@tool
def check_code_quality(code_snippet: str) -> str:
    """Analyze a code snippet and return quality issues found."""
    issues = []
    if len(code_snippet.strip().splitlines()) > 20:
        issues.append("Function too long (>20 lines)")
    if "TODO" in code_snippet:
        issues.append("Unresolved TODO comment found")
    if not issues:
        return "No issues found. Code looks clean."
    return f"Issues found: {'; '.join(issues)}"


tools = [check_code_quality]


llm = ChatOllama(model="qwen2.5:1.5b",
                temperature=0,
                base_url="http://localhost:11434")
llm_with_tools = llm.bind_tools(tools)


def agent_node(state: State) -> State:
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}


tool_node = ToolNode(tools)


def should_use_tool(state: State) -> Literal["tools", "end"]:
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        print(f"  → Agent memutuskan pakai tool: {[t['name'] for t in last_message.tool_calls]}")
        return "tools"
    print("  → Agent jawab langsung (tidak pakai tool)")
    return "end"


graph_builder = StateGraph(State)
graph_builder.add_node("agent", agent_node)
graph_builder.add_node("tools", tool_node)

graph_builder.add_edge(START, "agent")
graph_builder.add_conditional_edges("agent", should_use_tool, {"tools": "tools", "end": END})
graph_builder.add_edge("tools", "agent")  
graph = graph_builder.compile()


def run_test(label: str, user_input: str):
    print(f"\n{'='*55}")
    print(f"TEST: {label}")
    print(f"Input: {user_input}")
    print("-" * 55)
    result = graph.invoke({"messages": [HumanMessage(content=user_input)]})
    final = result["messages"][-1].content
    print(f"Output: {final}")


if __name__ == "__main__":
    print("ReviewAgent — Milestone 1 Test")
    print("Model: qwen2.5:1.5b | LangGraph conditional routing\n")

    run_test(
        "Tanpa tool (pertanyaan umum)",
        "Apa itu code review?"
    )

    run_test(
        "Dengan tool (ada code snippet)",
        """Please analyze this code:
        def process():
            x = 1
            # TODO: fix this later
            return x
        """
            )

    print("\n" + "="*55)
    print("Milestone 1 selesai !")