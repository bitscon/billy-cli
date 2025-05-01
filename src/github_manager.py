import os
import subprocess
from config import Config

config = Config()

def ensure_local_repo():
    """Ensure the local repository is cloned and up-to-date."""
    if not os.path.exists(config.LOCAL_REPO_PATH):
        os.makedirs(config.LOCAL_REPO_PATH, exist_ok=True)
        try:
            subprocess.run(
                ["git", "clone", config.REPO_URL, config.LOCAL_REPO_PATH],
                check=True,
                capture_output=True,
                text=True
            )
            return "Cloned repository to local path."
        except subprocess.CalledProcessError as e:
            return f"Error cloning repository: {e.stderr}"
    else:
        # Pull the latest changes
        try:
            subprocess.run(
                ["git", "-C", config.LOCAL_REPO_PATH, "pull"],
                check=True,
                capture_output=True,
                text=True
            )
            return "Pulled latest changes from repository."
        except subprocess.CalledProcessError as e:
            return f"Error pulling repository: {e.stderr}"

def get_local_repo_contents(path=config.LOCAL_REPO_PATH):
    """Recursively fetch all files and their contents from the local repository."""
    try:
        result = []
        for root, dirs, files in os.walk(path):
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, config.LOCAL_REPO_PATH)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    result.append({
                        "path": relative_path,
                        "content": content
                    })
                except Exception as e:
                    result.append({
                        "path": relative_path,
                        "content": f"Error reading file content: {str(e)}"
                    })
        return result
    except Exception as e:
        return f"Error reading local repository contents: {str(e)}"

def commit_and_push_changes(commit_message="Changes by Billy"):
    """Commit and push changes to the remote repository."""
    try:
        # Stage all changes
        subprocess.run(
            ["git", "-C", config.LOCAL_REPO_PATH, "add", "."],
            check=True,
            capture_output=True,
            text=True
        )
        # Commit changes
        subprocess.run(
            ["git", "-C", config.LOCAL_REPO_PATH, "commit", "-m", commit_message],
            check=True,
            capture_output=True,
            text=True
        )
        # Push to GitHub
        subprocess.run(
            ["git", "-C", config.LOCAL_REPO_PATH, "push", "origin", "main"],
            check=True,
            capture_output=True,
            text=True
        )
        return "Successfully committed and pushed changes to GitHub."
    except subprocess.CalledProcessError as e:
        return f"Error committing/pushing changes: {e.stderr}"

def analyze_repo_for_improvements():
    """Analyze the repository and suggest improvements (placeholder for future autonomy)."""
    ensure_local_repo()
    try:
        files = get_local_repo_contents()
        if isinstance(files, str):
            return files  # Error message
        # Basic analysis: Check for missing README.md as an example
        has_readme = any(file["path"].lower() == "readme.md" for file in files)
        suggestions = []
        if not has_readme:
            suggestions.append("I noticed there's no README.md in the repository. Adding one could help document the project. Would you like me to create a README.md with a basic description?")
        return "\n".join(suggestions) if suggestions else "No immediate improvements suggested for the repository."
    except Exception as e:
        return f"Error analyzing repository: {str(e)}"
