import asyncio
import json
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from agents.graph_with_hitl import hitl_graph
import tempfile
import os

app = FastAPI(title="DosCode API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session store
sessions = {}


async def run_review_stream(file_path: str, session_id: str):
    """Stream agent reasoning steps via SSE."""

    def emit(event_type: str, data: dict):
        return {"event": event_type, "data": json.dumps(data)}

    config = {"configurable": {"thread_id": session_id}}

    initial_state = {
        "messages": [],
        "file_path": file_path,
        "language": "",
        "lint_results": "",
        "security_results": "",
        "complexity_results": "",
        "rag_results": "",
        "severity": "",
        "final_summary": "",
        "loop_count": 0,
        "repo_name": None,
        "pr_number": None,
        "pr_diff": None,
        "human_approved": None,
    }

    yield emit("status", {"message": "Starting review...", "node": "start"})
    await asyncio.sleep(0.1)

    # Stream node-by-node via LangGraph stream
    final_state = None
    async for chunk in hitl_graph.astream(initial_state, config=config):
        for node_name, node_output in chunk.items():
            if node_name == "__interrupt__":
                continue

            # Map node ke human-readable message
            node_messages = {
                "classify_code": ("Detecting language and file type...", "🔍"),
                "run_tools": ("Running static analysis tools...", "⚙️"),
                "findings_evaluator": ("Evaluating findings severity...", "🧠"),
                "style_rag": ("Querying style guide documentation...", "📚"),
                "generate_summary": ("Generating review summary...", "✍️"),
                "request_human_approval": ("Waiting for approval...", "⏸️"),
            }

            msg, icon = node_messages.get(node_name, (f"Running {node_name}...", "▶️"))

            # Emit node start
            yield emit("node_start", {
                "node": node_name,
                "message": msg,
                "icon": icon
            })
            await asyncio.sleep(0.3)

            # Emit node-specific details
            if node_name == "run_tools" and node_output:
                tools_info = []
                if node_output.get("lint_results"):
                    issue_count = node_output["lint_results"].count("Line")
                    tools_info.append(f"Linter: {issue_count} issues found")
                if node_output.get("security_results"):
                    has_issues = "found" in node_output["security_results"].lower()
                    tools_info.append(f"Security: {'vulnerabilities detected' if has_issues else 'clean'}")
                if node_output.get("complexity_results"):
                    tools_info.append("Complexity: analyzed")
                yield emit("tool_results", {"tools": tools_info})
                await asyncio.sleep(0.2)

            if node_name == "findings_evaluator" and node_output.get("severity"):
                yield emit("severity", {"level": node_output["severity"]})
                await asyncio.sleep(0.2)

            if node_name == "style_rag":
                yield emit("rag_query", {"message": "Style guide retrieved"})
                await asyncio.sleep(0.2)

            # Emit node complete
            yield emit("node_complete", {"node": node_name})
            await asyncio.sleep(0.1)

            if node_output:
                final_state = node_output

    # Store session state for approval
    if final_state:
        sessions[session_id] = final_state

    # Get full state from checkpointer
    full_state = hitl_graph.get_state(config)
    if full_state and full_state.values:
        sessions[session_id] = full_state.values
        yield emit("review_complete", {
            "summary": full_state.values.get("final_summary", ""),
            "severity": full_state.values.get("severity", "unknown"),
            "loop_count": full_state.values.get("loop_count", 0),
        })
    else:
        yield emit("error", {"message": "Failed to get final state"})


@app.post("/review/stream")
async def review_stream(
    file: UploadFile = File(...),
    session_id: str = Form(default="default-session")
):
    """Upload file dan stream review progress via SSE."""
    # Save uploaded file temporarily
    content = await file.read()
    suffix = os.path.splitext(file.filename)[1]
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(content)
    tmp.close()
    temp_path = tmp.name

    async def event_generator():
        async for event in run_review_stream(temp_path, session_id):
            yield event

    return EventSourceResponse(event_generator())


@app.post("/review/approve")
async def approve_review(session_id: str, approved: bool):
    """Human approval endpoint."""
    if session_id not in sessions:
        return {"error": "Session not found"}

    config = {"configurable": {"thread_id": session_id}}
    state = sessions[session_id]
    state["human_approved"] = approved

    result = hitl_graph.invoke(state, config=config)
    return {
        "status": "approved" if approved else "rejected",
        "message": result["messages"][-1].content if result.get("messages") else ""
    }


@app.get("/health")
async def health():
    return {"status": "ok", "service": "ReviewAgent API"}