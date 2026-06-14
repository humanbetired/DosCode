from agents.graph_with_hitl import hitl_graph

def run_with_hitl(file_path: str, repo_name: str = None, pr_number: int = None):
    print("ReviewAgent — Milestone 5: Human-in-the-Loop")
    print("="*60)

    config = {"configurable": {"thread_id": "review-session-1"}}

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
        "repo_name": repo_name,
        "pr_number": pr_number,
        "pr_diff": None,
        "human_approved": None,
    }

    print("\n[Phase 1] Running agent...")
    result = hitl_graph.invoke(initial_state, config=config)

    print("\n" + "="*60)
    print("REVIEW COMPLETE — Waiting for human approval")
    print("="*60)
    print(result["final_summary"])
    print(f"\nSeverity: {result['severity'].upper()}")

    if repo_name and pr_number:
        print(f"\nPost this review to {repo_name} PR #{pr_number}?")
        user_input = input("Approve? (yes/no): ").strip().lower()
        approved = user_input == "yes"
    else:
        print("\n(No GitHub target — simulating approval prompt)")
        user_input = input("Approve posting? (yes/no): ").strip().lower()
        approved = user_input == "yes"

    print(f"\n[Phase 3] Human decision: {'APPROVED' if approved else 'REJECTED'}")

    resume_state = {**result, "human_approved": approved}
    final = hitl_graph.invoke(resume_state, config=config)

    print("\n" + "="*60)
    print("DONE")
    print("="*60)
    if final.get("messages"):
        print(final["messages"][-1].content)


if __name__ == "__main__":
    run_with_hitl(
        file_path="sample_bad_code.py",
        repo_name=None,
        pr_number=None
    )

    print("\nMilestone 5 selesai!")