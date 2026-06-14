from agents.graph import review_graph

def run_review(file_path: str):
    print(f"\n{'='*60}")
    print(f"REVIEWING: {file_path}")
    print("="*60)

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
    }

    result = review_graph.invoke(initial_state)

    print(f"\n{'─'*60}")
    print("FINAL REVIEW SUMMARY:")
    print("─"*60)
    print(result["final_summary"])
    print(f"\nSeverity: {result['severity'].upper()}")
    print(f"RAG loop count: {result['loop_count']}")

    return result


if __name__ == "__main__":
    print("ReviewAgent — Milestone 4: Full Agent Graph")

    run_review("sample_bad_code.py")

    print("\nMilestone 4 selesai!")