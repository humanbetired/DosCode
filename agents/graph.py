import json
from typing import Annotated, Literal
from typing_extensions import TypedDict

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

from agents.tools.lint_tool import run_linter
from agents.tools.security_tool import run_security_scan
from agents.tools.complexity_tool import run_complexity_check
from agents.tools.rag_tool import query_style_guide


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


llm = ChatOllama(
    model="qwen2.5:1.5b",
    temperature=0,
    base_url=("OLLAMA_HOST", "http://127.0.0.1:11434")
)


def classify_code(state: ReviewState) -> ReviewState:
    """Deteksi bahasa dan tipe file."""
    print("\n[Node] classify_code")

    file_path = state["file_path"]
    ext = file_path.rsplit(".", 1)[-1].lower() if "." in file_path else "unknown"

    language_map = {
        "py": "Python",
        "js": "JavaScript",
        "ts": "TypeScript",
        "java": "Java",
        "go": "Go",
    }
    language = language_map.get(ext, "Unknown")
    print(f"  → Detected: {language} ({file_path})")

    return {
        **state,
        "language": language,
        "messages": [HumanMessage(content=f"Starting review for {file_path} ({language})")]
    }


def run_tools(state: ReviewState) -> ReviewState:
    """Jalankan semua static analysis tools."""
    print("\n[Node] run_tools")

    file_path = state["file_path"]

    print("  → Running linter...")
    lint = run_linter.invoke({"file_path": file_path})

    print("  → Running security scan...")
    security = run_security_scan.invoke({"file_path": file_path})

    print("  → Running complexity check...")
    complexity = run_complexity_check.invoke({"file_path": file_path})

    print(f"  → Tools done")

    return {
        **state,
        "lint_results": lint,
        "security_results": security,
        "complexity_results": complexity,
    }


def findings_evaluator(state: ReviewState) -> ReviewState:
    """
    LLM node — evaluasi severity findings.
    Ini kunci dynamic routing: LLM memutuskan sendiri apakah
    perlu investigasi lanjut via RAG atau langsung ke summary.
    """
    print("\n[Node] findings_evaluator")

    rag_context = ""
    if state.get("rag_results"):
        rag_context = f"\n\nStyle Guide Reference:\n{state['rag_results']}"

    prompt = f"""You are a senior code reviewer. Analyze these findings and determine severity.

File: {state['file_path']}
Language: {state['language']}

LINT RESULTS:
{state.get('lint_results', 'Not run')}

SECURITY RESULTS:
{state.get('security_results', 'Not run')}

COMPLEXITY RESULTS:
{state.get('complexity_results', 'Not run')}
{rag_context}

Respond in JSON format only:
{{
  "severity": "low|medium|high|critical",
  "needs_rag_lookup": true|false,
  "rag_query": "query string if needs_rag_lookup is true, else null",
  "reasoning": "brief explanation"
}}

Rules:
- severity=critical if: hardcoded secrets, eval() with input, or complexity grade F
- severity=high if: multiple security issues or complexity grade D/E
- severity=medium if: several lint issues or complexity grade C
- severity=low if: minor style issues only
- needs_rag_lookup=true if severity is high or critical AND loop_count < 2"""

    response = llm.invoke([SystemMessage(content="You are a code review assistant. Always respond with valid JSON only."),
                           HumanMessage(content=prompt)])

    try:
        raw = response.content.strip()
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        result = json.loads(raw.strip())
    except Exception as e:
        print(f"  → JSON parse error: {e}, using defaults")
        result = {
            "severity": "medium",
            "needs_rag_lookup": False,
            "rag_query": None,
            "reasoning": "Parse error, defaulting to medium severity"
        }

    severity = result.get("severity", "medium")
    needs_rag = result.get("needs_rag_lookup", False)
    rag_query = result.get("rag_query", "")
    reasoning = result.get("reasoning", "")

    print(f"  → Severity: {severity}")
    print(f"  → Needs RAG: {needs_rag}")
    print(f"  → Reasoning: {reasoning}")

    return {
        **state,
        "severity": severity,
        "loop_count": state.get("loop_count", 0),
        "messages": [AIMessage(content=f"Severity: {severity}. {reasoning}. RAG needed: {needs_rag}")]
    }

def style_rag_node(state: ReviewState) -> ReviewState:
    """Query style guide untuk context tambahan."""
    print("\n[Node] style_rag_node")

    queries = []
    if "hardcoded" in state.get("security_results", "").lower() or \
       "secret" in state.get("security_results", "").lower():
        queries.append("hardcoded credentials security rules")
    if "eval" in state.get("security_results", "").lower():
        queries.append("dangerous functions eval exec security")
    if state.get("severity") in ["high", "critical"]:
        queries.append(f"severity {state['severity']} code review standards")
    if not queries:
        queries.append("code quality standards best practices")

    query = " AND ".join(queries)
    print(f"  → RAG query: {query}")

    rag_result = query_style_guide.invoke({"query": query})

    return {
        **state,
        "rag_results": rag_result,
        "loop_count": state.get("loop_count", 0) + 1,
    }


def generate_summary(state: ReviewState) -> ReviewState:
    """Generate final review summary."""
    print("\n[Node] generate_summary")

    rag_section = ""
    if state.get("rag_results"):
        rag_section = f"\n\nStyle Guide Reference:\n{state['rag_results']}"

    prompt = f"""Generate a clear, structured code review summary.

File: {state['file_path']} ({state['language']})
Overall Severity: {state.get('severity', 'unknown').upper()}

FINDINGS:
Lint: {state.get('lint_results', 'N/A')}
Security: {state.get('security_results', 'N/A')}
Complexity: {state.get('complexity_results', 'N/A')}
{rag_section}

Write a professional code review with:
1. Overall assessment (1-2 sentences)
2. Critical issues (must fix)
3. Recommendations (should fix)
4. Verdict: APPROVE / REQUEST CHANGES / REJECT"""

    response = llm.invoke([HumanMessage(content=prompt)])
    summary = response.content

    print("  → Summary generated")

    return {
        **state,
        "final_summary": summary,
        "messages": [AIMessage(content=summary)]
    }


def route_after_evaluator(state: ReviewState) -> Literal["style_rag", "generate_summary"]:
    severity = state.get("severity", "low")
    loop_count = state.get("loop_count", 0)
    has_rag = bool(state.get("rag_results"))

    if loop_count >= 2:
        print("  → Max loop reached, going to summary")
        return "generate_summary"

    if severity in ["high", "critical"] and not has_rag:
        print(f"  → Severity {severity} — routing to RAG for deeper investigation")
        return "style_rag"

    print(f"  → Severity {severity} — sufficient info, generating summary")
    return "generate_summary"


def build_graph():
    builder = StateGraph(ReviewState)

    builder.add_node("classify_code", classify_code)
    builder.add_node("run_tools", run_tools)
    builder.add_node("findings_evaluator", findings_evaluator)
    builder.add_node("style_rag", style_rag_node)
    builder.add_node("generate_summary", generate_summary)

    builder.add_edge(START, "classify_code")
    builder.add_edge("classify_code", "run_tools")
    builder.add_edge("run_tools", "findings_evaluator")

    builder.add_conditional_edges(
        "findings_evaluator",
        route_after_evaluator,
        {
            "style_rag": "style_rag",
            "generate_summary": "generate_summary"
        }
    )

    builder.add_edge("style_rag", "findings_evaluator")
    builder.add_edge("generate_summary", END)

    return builder.compile()

review_graph = build_graph()