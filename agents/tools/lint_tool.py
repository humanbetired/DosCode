import subprocess
import json
from langchain_core.tools import tool

@tool
def run_linter(file_path: str) -> str:
    """Run ruff linter on a Python file and return style and lint issues found."""
    try:
        result = subprocess.run(
            ["ruff", "check", file_path, "--output-format", "json"],
            capture_output=True,
            text=True
        )
        if not result.stdout.strip():
            return "Linter: No issues found."

        issues = json.loads(result.stdout)
        if not issues:
            return "Linter: No issues found."

        formatted = []
        for issue in issues[:10]:  
            formatted.append(
                f"Line {issue['location']['row']}: [{issue['code']}] {issue['message']}"
            )
        return f"Linter found {len(issues)} issues:\n" + "\n".join(formatted)

    except FileNotFoundError:
        return f"Error: File '{file_path}' not found."
    except Exception as e:
        return f"Linter error: {str(e)}"