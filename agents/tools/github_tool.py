import os
from github import Github
from dotenv import load_dotenv
from langchain_core.tools import tool

load_dotenv()


def get_github_client():
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise ValueError("GITHUB_TOKEN not found in .env")
    return Github(token)


@tool
def fetch_pr_diff(repo_name: str, pr_number: int) -> str:
    """Fetch the code diff from a GitHub Pull Request and return changed files with their diffs."""
    try:
        g = get_github_client()
        repo = g.get_repo(repo_name)
        pr = repo.get_pull(pr_number)

        files = pr.get_files()
        result = []
        result.append(f"PR #{pr_number}: {pr.title}")
        result.append(f"Author: {pr.user.login}")
        result.append(f"Files changed: {pr.changed_files}")
        result.append("─" * 40)

        for f in files:
            result.append(f"\nFile: {f.filename} ({f.status})")
            result.append(f"Changes: +{f.additions} -{f.deletions}")
            if f.patch: 
                patch = f.patch[:2000]
                result.append(f"Diff:\n{patch}")
                if len(f.patch) > 2000:
                    result.append("... (diff truncated)")

        return "\n".join(result)

    except Exception as e:
        return f"GitHub fetch error: {str(e)}"


@tool
def post_review_comment(repo_name: str, pr_number: int, comment: str) -> str:
    """Post a review comment to a GitHub Pull Request after human approval."""
    try:
        g = get_github_client()
        repo = g.get_repo(repo_name)
        pr = repo.get_pull(pr_number)

        pr.create_issue_comment(comment)
        return f"✅ Comment posted successfully to PR #{pr_number} in {repo_name}"

    except Exception as e:
        return f"GitHub post error: {str(e)}"