import json
import os
from typing import Annotated, Literal, Optional
from typing_extensions import TypedDict

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver

from agents.tools.lint_tool import run_linter
from agents.tools.security_tool import run_security_scan
from agents.tools.complexity_tool import run_complexity_check
from agents.tools.rag_tool import query_style_guide
from agents.tools.github_tool import fetch_pr_diff, post_review_comment
from dotenv import load_dotenv
load_dotenv()

os.environ.pop("OLLAMA_HOST", None)

class ReviewState(TypedDict):
    messages: Annotated[list, add_messages]
    file_path: str
    language: str
    lint_results: str
    security_results: str
    complexity_results: str
    rag_results: str
    severity: str
    final_summary: str
    loop_count: int
    # GitHub fields
    repo_name: Optional[str]
    pr_number: Optional[int]
    pr_diff: Optional[str]
    human_approved: Optional[bool]

OLLAMA_HOST = "http://127.0.0.1:11434"

llm = ChatOllama(
    model="qwen2.5:1.5b",
    temperature=0,
    base_url=OLLAMA_HOST
)


def classify_code(state: ReviewState) -> ReviewState:
    print("\n[Node] classify_code")
    file_path = state.get("file_path", "")

    if state.get("pr_diff"):
        print("  → Mode: GitHub PR diff")
        return {**state, "language": "Python", "messages": []}

    ext = file_path.rsplit(".", 1)[-1].lower() if "." in file_path else "unknown"
    language_map = {"py": "Python", "js": "JavaScript", "ts": "TypeScript"}
    language = language_map.get(ext, "Unknown")
    print(f"  → Detected: {language}")
    return {**state, "language": language, "messages": []}


def run_tools(state: ReviewState) -> ReviewState:
    print("\n[Node] run_tools")

    if state.get("pr_diff"):
        print("  → Analyzing PR diff (skip local tools)")
        return {
            **state,
            "lint_results": "PR diff mode — static analysis based on diff content",
            "security_results": "Checking diff for security patterns...",
            "complexity_results": "Complexity check from diff",
        }

    file_path = state["file_path"]
    print("  → Running lint...")
    lint = run_linter.invoke({"file_path": file_path})
    print("  → Running security scan...")
    security = run_security_scan.invoke({"file_path": file_path})
    print("  → Running complexity...")
    complexity = run_complexity_check.invoke({"file_path": file_path})

    return {**state, "lint_results": lint, "security_results": security, "complexity_results": complexity}


def findings_evaluator(state: ReviewState) -> ReviewState:
    print("\n[Node] findings_evaluator")

    rag_context = ""
    if state.get("rag_results"):
        rag_context = f"\nStyle Guide:\n{state['rag_results']}"

    pr_context = ""
    if state.get("pr_diff"):
        pr_context = f"\nPR Diff (excerpt):\n{state['pr_diff'][:1000]}"

    prompt = f"""Analyze these code review findings and determine severity.

File: {state.get('file_path', 'PR diff')}
{pr_context}

Lint: {state.get('lint_results', 'N/A')}
Security: {state.get('security_results', 'N/A')}
Complexity: {state.get('complexity_results', 'N/A')}
{rag_context}

Respond in JSON only, no other text:
{{
  "severity": "low|medium|high|critical",
  "needs_rag_lookup": true|false,
  "reasoning": "brief explanation"
}}"""

    try:
        response = llm.invoke([
            SystemMessage(content="You are a code review assistant. Respond with valid JSON only. No markdown, no explanation, just JSON."),
            HumanMessage(content=prompt)
        ])

        raw = response.content.strip()
        print(f"  → LLM raw response: {raw[:200]}")

        # Strip semua kemungkinan markdown wrapper
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0]
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0]

        # Cari JSON object di dalam response
        import re
        json_match = re.search(r'\{.*\}', raw, re.DOTALL)
        if json_match:
            raw = json_match.group()

        result = json.loads(raw.strip())

    except json.JSONDecodeError as e:
        print(f"  → JSON parse error: {e}")
        print(f"  → Raw was: {raw}")
        result = {"severity": "medium", "needs_rag_lookup": False, "reasoning": "Parse error fallback"}
    except Exception as e:
        print(f"  → Evaluator error: {e}")
        result = {"severity": "medium", "needs_rag_lookup": False, "reasoning": "Error fallback"}

    severity = result.get("severity", "medium")
    print(f"  → Severity: {severity}")

    return {**state, "severity": severity}


def style_rag_node(state: ReviewState) -> ReviewState:
    print("\n[Node] style_rag_node")
    query = f"security rules {state.get('severity', '')} severity code standards"
    rag_result = query_style_guide.invoke({"query": query})
    return {**state, "rag_results": rag_result, "loop_count": state.get("loop_count", 0) + 1}


def generate_summary(state: ReviewState) -> ReviewState:
    print("\n[Node] generate_summary")

    rag_section = f"\nStyle Guide:\n{state['rag_results']}" if state.get("rag_results") else ""

    prompt = f"""Write a professional code review summary.

File: {state.get('file_path', 'GitHub PR')}
Severity: {state.get('severity', 'unknown').upper()}

Lint: {state.get('lint_results', 'N/A')}
Security: {state.get('security_results', 'N/A')}
Complexity: {state.get('complexity_results', 'N/A')}
{rag_section}

Format:
## Code Review Summary
**Overall Severity:** ...
**Verdict:** APPROVE / REQUEST CHANGES / REJECT

### Critical Issues
...

### Recommendations
...

### Style Guide Violations
..."""

    response = llm.invoke([HumanMessage(content=prompt)])
    summary = response.content
    print("  → Summary generated")
    return {**state, "final_summary": summary, "messages": [AIMessage(content=summary)]}


def request_human_approval(state: ReviewState) -> ReviewState:
    print("\n[Node] request_human_approval")
    print("  → WAITING FOR HUMAN APPROVAL...")
    print("\n" + "="*60)
    print("REVIEW SUMMARY:")
    print(state["final_summary"])
    print("="*60)
    print(f"\nTarget: {state.get('repo_name')} PR #{state.get('pr_number')}")
    print("Ketik 'yes' untuk post ke GitHub, 'no' untuk cancel")

    return {**state, "messages": [AIMessage(content="Waiting for human approval to post review...")]}


def post_to_github(state: ReviewState) -> ReviewState:
    print("\n[Node] post_to_github")

    if not state.get("human_approved"):
        print("  → Not approved, skipping post")
        return {**state, "messages": [AIMessage(content="Review cancelled by human.")]}

    repo_name = state.get("repo_name")
    pr_number = state.get("pr_number")

    if not repo_name or not pr_number:
        print("  → No GitHub target, skipping post")
        return {**state, "messages": [AIMessage(content="No GitHub PR target specified.")]}

    result = post_review_comment.invoke({
        "repo_name": repo_name,
        "pr_number": pr_number,
        "comment": state["final_summary"]
    })
    print(f"  → {result}")
    return {**state, "messages": [AIMessage(content=result)]}


def route_after_evaluator(state: ReviewState) -> Literal["style_rag", "generate_summary"]:
    severity = state.get("severity", "low")
    loop_count = state.get("loop_count", 0)
    has_rag = bool(state.get("rag_results"))

    if loop_count >= 2:
        return "generate_summary"
    if severity in ["high", "critical"] and not has_rag:
        print(f"  → Routing to RAG (severity: {severity})")
        return "style_rag"
    return "generate_summary"


def route_after_approval(state: ReviewState) -> Literal["post_to_github", "end"]:
    """Routing setelah human approval node."""
    if state.get("human_approved") is True:
        return "post_to_github"
    if state.get("human_approved") is False:
        return "end"
    return "end"


def build_hitl_graph():
    builder = StateGraph(ReviewState)

    builder.add_node("classify_code", classify_code)
    builder.add_node("run_tools", run_tools)
    builder.add_node("findings_evaluator", findings_evaluator)
    builder.add_node("style_rag", style_rag_node)
    builder.add_node("generate_summary", generate_summary)
    builder.add_node("request_human_approval", request_human_approval)
    builder.add_node("post_to_github", post_to_github)

    builder.add_edge(START, "classify_code")
    builder.add_edge("classify_code", "run_tools")
    builder.add_edge("run_tools", "findings_evaluator")
    builder.add_conditional_edges(
        "findings_evaluator",
        route_after_evaluator,
        {"style_rag": "style_rag", "generate_summary": "generate_summary"}
    )
    builder.add_edge("style_rag", "findings_evaluator")
    builder.add_edge("generate_summary", "request_human_approval")
    builder.add_conditional_edges(
        "request_human_approval",
        route_after_approval,
        {"post_to_github": "post_to_github", "end": END}
    )
    builder.add_edge("post_to_github", END)

    checkpointer = MemorySaver()
    return builder.compile(
        checkpointer=checkpointer,
        interrupt_before=["request_human_approval"] 
    )


hitl_graph = build_hitl_graph()