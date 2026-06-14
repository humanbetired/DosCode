import os
import sys
import json
import tempfile
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.graph import review_graph
from evaluation.eval_dataset import EVAL_DATASET


def severity_to_rank(severity: str) -> int:
    return {"low": 0, "medium": 1, "high": 2, "critical": 3}.get(severity.lower(), -1)


def evaluate_single(sample: dict) -> dict:
    """Run agent on one sample dan compare dengan expected."""

    # Tulis code ke temp file
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    )
    tmp.write(sample["code"])
    tmp.close()

    start_time = time.time()

    try:
        initial_state = {
            "messages": [],
            "file_path": tmp.name,
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
        elapsed = time.time() - start_time

        detected_severity = result.get("severity", "unknown").lower()
        expected_severity  = sample["expected_severity"].lower()
        expected_verdict   = sample["expected_verdict"].upper()
        final_summary      = result.get("final_summary", "")

        # Severity match — exact atau within 1 level
        severity_exact  = detected_severity == expected_severity
        severity_within = abs(
            severity_to_rank(detected_severity) - severity_to_rank(expected_severity)
        ) <= 1

        # Verdict detection dari summary
        verdict_detected = "UNKNOWN"
        for v in ["REJECT", "REQUEST CHANGES", "APPROVE"]:
            if v in final_summary.upper():
                verdict_detected = v
                break

        verdict_match = verdict_detected == expected_verdict

        # Security detection
        security_expected = sample["expected_issues"]["security"]
        security_keywords = {
            "hardcoded_secret":   ["hardcoded", "api key", "secret", "credential"],
            "hardcoded_password": ["password", "hardcoded"],
            "eval_usage":         ["eval"],
            "shell_injection":    ["shell=true", "shell injection", "subprocess"],
        }
        security_hits = 0
        for issue in security_expected:
            keywords = security_keywords.get(issue, [issue.replace("_", " ")])
            if any(kw in final_summary.lower() for kw in keywords):
                security_hits += 1

        security_recall = (
            security_hits / len(security_expected)
            if security_expected else 1.0
        )

        return {
            "id":               sample["id"],
            "name":             sample["name"],
            "expected_severity": expected_severity,
            "detected_severity": detected_severity,
            "severity_exact":    severity_exact,
            "severity_within":   severity_within,
            "expected_verdict":  expected_verdict,
            "verdict_detected":  verdict_detected,
            "verdict_match":     verdict_match,
            "security_recall":   security_recall,
            "loop_count":        result.get("loop_count", 0),
            "elapsed_sec":       round(elapsed, 1),
            "status":            "ok",
        }

    except Exception as e:
        return {
            "id":     sample["id"],
            "name":   sample["name"],
            "status": "error",
            "error":  str(e),
        }
    finally:
        os.unlink(tmp.name)


def run_evaluation():
    print("=" * 60)
    print("ReviewAgent — Evaluation Suite")
    print(f"Dataset: {len(EVAL_DATASET)} samples")
    print("=" * 60)

    results = []
    for i, sample in enumerate(EVAL_DATASET, 1):
        print(f"\n[{i}/{len(EVAL_DATASET)}] {sample['id']}: {sample['name']}")
        print(f"  Expected: severity={sample['expected_severity']} | verdict={sample['expected_verdict']}")

        result = evaluate_single(sample)

        if result["status"] == "error":
            print(f"  ❌ ERROR: {result['error']}")
        else:
            sev_icon = "✅" if result["severity_exact"] else ("⚠️" if result["severity_within"] else "❌")
            ver_icon = "✅" if result["verdict_match"] else "❌"
            print(f"  Severity : {sev_icon} detected={result['detected_severity']}")
            print(f"  Verdict  : {ver_icon} detected={result['verdict_detected']}")
            print(f"  Security recall: {result['security_recall']:.0%}")
            print(f"  RAG loops: {result['loop_count']} | Time: {result['elapsed_sec']}s")

        results.append(result)

    # ── Metrics ────────────────────────────────────────────────────────
    ok = [r for r in results if r["status"] == "ok"]

    if not ok:
        print("\nAll samples failed.")
        return

    severity_exact  = sum(1 for r in ok if r["severity_exact"])  / len(ok)
    severity_within = sum(1 for r in ok if r["severity_within"]) / len(ok)
    verdict_acc     = sum(1 for r in ok if r["verdict_match"])   / len(ok)
    avg_recall      = sum(r["security_recall"] for r in ok)      / len(ok)
    avg_time        = sum(r["elapsed_sec"] for r in ok)          / len(ok)
    avg_loops       = sum(r["loop_count"] for r in ok)           / len(ok)

    print("\n" + "=" * 60)
    print("EVALUATION RESULTS")
    print("=" * 60)
    print(f"Samples evaluated  : {len(ok)}/{len(EVAL_DATASET)}")
    print(f"Severity (exact)   : {severity_exact:.0%}")
    print(f"Severity (±1 level): {severity_within:.0%}")
    print(f"Verdict accuracy   : {verdict_acc:.0%}")
    print(f"Security recall    : {avg_recall:.0%}")
    print(f"Avg response time  : {avg_time:.1f}s")
    print(f"Avg RAG loops      : {avg_loops:.1f}")
    print("=" * 60)

    # Save hasil ke JSON
    os.makedirs("data", exist_ok=True)
    output = {
        "metrics": {
            "severity_exact":   round(severity_exact, 3),
            "severity_within":  round(severity_within, 3),
            "verdict_accuracy": round(verdict_acc, 3),
            "security_recall":  round(avg_recall, 3),
            "avg_time_sec":     round(avg_time, 1),
            "avg_rag_loops":    round(avg_loops, 2),
        },
        "samples": ok,
    }

    with open("data/eval_results.json", "w") as f:
        json.dump(output, f, indent=2)

    try:
        from evaluation.langfuse_setup import get_lf_client
        print("\nSending results to Langfuse...")

        lf = get_lf_client()

        for r in ok:
            # Buat trace context dulu
            trace_id = lf.create_trace_id()
            trace_context = {"trace_id": trace_id}

            # Buat observation
            obs = lf.start_observation(
                name=f"eval_{r['id']}",
                as_type="evaluator",
                input={"sample_name": r["name"]},
                output={
                    "severity_detected": r["detected_severity"],
                    "verdict_detected":  r["verdict_detected"],
                },
                metadata={
                    "expected_severity": r["expected_severity"],
                    "expected_verdict":  r["expected_verdict"],
                    "severity_exact":    r["severity_exact"],
                    "verdict_match":     r["verdict_match"],
                    "security_recall":   r["security_recall"],
                    "loop_count":        r["loop_count"],
                    "elapsed_sec":       r["elapsed_sec"],
                },
            )
            obs.end()

            # Score pakai create_score dengan trace_id
            lf.create_score(
                trace_id=obs.trace_id,
                name="severity_exact",
                value=1.0 if r["severity_exact"] else 0.0,
                comment=f"Expected {r['expected_severity']}, got {r['detected_severity']}",
            )
            lf.create_score(
                trace_id=obs.trace_id,
                name="verdict_match",
                value=1.0 if r["verdict_match"] else 0.0,
                comment=f"Expected {r['expected_verdict']}, got {r['verdict_detected']}",
            )
            lf.create_score(
                trace_id=obs.trace_id,
                name="security_recall",
                value=r["security_recall"],
            )

            print(f"  ✓ {r['id']} traced (trace_id: {obs.trace_id})")

        lf.flush()
        print("✅ Results sent to Langfuse!")
        print("   → Buka cloud.langfuse.com → Traces")

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Langfuse skip: {e}")

    print(f"\nResults saved → data/eval_results.json")
    print("\n Milestone 7 Evaluation selesai!")


if __name__ == "__main__":
    run_evaluation()