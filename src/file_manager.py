import os
import subprocess
from github_manager import ensure_local_repo, commit_and_push_changes, LOCAL_REPO_PATH

def create_local_file(file_path, content):
    """Create or update a file in the local repository."""
    ensure_local_repo()
    local_file_path = os.path.join(LOCAL_REPO_PATH, file_path)
    try:
        os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
        with open(local_file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully created/updated {file_path} locally."
    except Exception as e:
        return f"Error creating/updating local file: {str(e)}"

def delete_local_file(file_path):
    """Delete a file in the local repository."""
    ensure_local_repo()
    local_file_path = os.path.join(LOCAL_REPO_PATH, file_path)
    try:
        if os.path.exists(local_file_path):
            os.remove(local_file_path)
            return f"Successfully deleted {file_path} locally."
        return f"File {file_path} does not exist locally."
    except Exception as e:
        return f"Error deleting local file: {str(e)}"

def test_code_in_sandbox(code):
    """Test the code in the Docker sandbox."""
    try:
        # Write the code to a temporary file
        with open("/tmp/temp_code.py", "w") as f:
            f.write(code)
        # Run the code in the Docker container
        result = subprocess.run(
            [
                "docker", "run", "--rm",
                "-v", "/tmp/temp_code.py:/app/temp_code.py",
                "--security-opt", "no-new-privileges",
                "--cap-drop", "ALL",
                "--network", "none",
                "billy-python-sandbox",
                "python", "temp_code.py"
            ],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.stderr:
            return f"Test failed: {result.stderr}"
        return "Test passed: Code executed successfully."
    except subprocess.TimeoutExpired:
        return "Test failed: Code execution timed out after 5 seconds."
    except Exception as e:
        return f"Test failed: {str(e)}"
    finally:
        # Clean up the temporary file
        if os.path.exists("/tmp/temp_code.py"):
            os.remove("/tmp/temp_code.py")

def create_file_with_test(file_path, content, commit_message="Created file via Billy"):
    """Create a file locally, test it if it's Python code, and push to GitHub if tests pass."""
    # Create or update the file locally
    result = create_local_file(file_path, content)
    if "Error" in result:
        return result

    # If the file is a Python file, test it in the sandbox
    if file_path.endswith(".py"):
        test_result = test_code_in_sandbox(content)
        if "Test failed" in test_result:
            return f"Failed to create {file_path}: {test_result}"
    
    # Commit and push changes
    commit_result = commit_and_push_changes(commit_message)
    return f"{result}\n{commit_result}"

def update_file_with_test(file_path, content, commit_message="Updated file via Billy"):
    """Update a file locally, test it if it's Python code, and push to GitHub if tests pass."""
    # Update the file locally
    result = create_local_file(file_path, content)
    if "Error" in result:
        return result

    # If the file is a Python file, test it in the sandbox
    if file_path.endswith(".py"):
        test_result = test_code_in_sandbox(content)
        if "Test failed" in test_result:
            return f"Failed to update {file_path}: {test_result}"
    
    # Commit and push changes
    commit_result = commit_and_push_changes(commit_message)
    return f"{result}\n{commit_result}"

def delete_file_with_commit(file_path, commit_message="Deleted file via Billy"):
    """Delete a file locally and push the deletion to GitHub."""
    # Delete the file locally
    result = delete_local_file(file_path)
    if "Error" in result:
        return result
    
    # Commit and push changes
    commit_result = commit_and_push_changes(commit_message)
    return f"{result}\n{commit_result}"
