import subprocess
import json
from langchain_core.tools import tool


@tool
def run_security_scan(file_path: str) -> str:
    try:
        result = subprocess.run(
            ["bandit", "-f", "json", "-q", file_path],
            capture_output=True,
            text=True
        )

        output = result.stdout.strip()
        if not output:
            return "Security scan: No vulnerabilities found."

        data = json.loads(output)
        issues = data.get("results", [])

        if not issues:
            return "Security scan: No vulnerabilities found."

        formatted = []
        for issue in issues[:10]:
            formatted.append(
                f"Line {issue['line_number']} [{issue['issue_severity']}]: "
                f"{issue['issue_text']} (confidence: {issue['issue_confidence']})"
            )
        return f"Security scan found {len(issues)} issues:\n" + "\n".join(formatted)

    except FileNotFoundError:
        return f"Error: File '{file_path}' not found."
    except Exception as e:
        return f"Security scan error: {str(e)}"