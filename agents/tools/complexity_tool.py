import subprocess
from langchain_core.tools import tool


@tool
def run_complexity_check(file_path: str) -> str:
    try:
        result = subprocess.run(
            ["radon", "cc", file_path, "-s", "-a"],
            capture_output=True,
            text=True
        )

        output = result.stdout.strip()
        if not output:
            return "Complexity check: No functions found or file is empty."

        lines = output.splitlines()
        issues = [l for l in lines if any(
            grade in l for grade in [" C ", " D ", " E ", " F "]
        )]

        summary = lines[-1] if lines else ""

        if issues:
            return (
                f"Complexity issues (grade C or worse):\n"
                + "\n".join(issues)
                + f"\n{summary}"
            )
        return f"Complexity check passed.\n{summary}"

    except FileNotFoundError:
        return f"Error: File '{file_path}' not found."
    except Exception as e:
        return f"Complexity error: {str(e)}"