# Billy: Detailed Overview

## Purpose
Billy is designed as a conversational AI assistant to streamline development tasks, assist with coding, and manage GitHub repositories interactively. The goal is to create a self-improving AI that can:
- Engage in natural conversations with users.
- Execute and debug Python code in a secure environment.
- Manage files in a GitHub repository with local testing before pushing changes.
- Learn from interactions to enhance its responses over time.
- Provide insights into repository health and suggest improvements.

Billy aims to be a helpful tool for developers, reducing manual effort in repetitive tasks while learning from user interactions to become more effective.

## What We Have Built So Far
### Initial Development
- **Web Interface**: Built a Flask-based web app (`src/billy.py`) for user interaction, accessible at `http://192.168.1.112:5000`.
- **Database Integration**: Utilized SQLite (`db/billy.db`) with three tables:
  - `memory`: Stores conversation history (prompts, responses, categories, tool code/results, timestamps).
  - `learning`: Logs code execution results for error analysis.
  - `documentation`: Saves web search results and other references.
- **Code Execution**: Implemented a Docker sandbox (`billy-python-sandbox`) to run Python code securely, with error logging and debugging capabilities.
- **File Management**: Initially allowed direct GitHub API interactions to create, update, and delete files in the repository (`bitscon/billy`).

### Enhancements
- **Local Repository Workflow**: Shifted to a local clone of the repository (`/home/billybs/Projects/billy-local-repo`) for safer file operations. Billy now edits files locally, tests them (if Python code), and pushes changes to GitHub only after validation.
- **LLM Integration**: Integrated the Ollama API for natural language understanding, replacing hardcoded intent detection with LLM-based intent classification.
- **Database Optimization**: Added indexes for efficient querying, implemented pagination, and introduced data pruning to manage database growth.
- **Error Analysis**: Enhanced error logging in the `learning` table to include trends over time, providing deeper insights when users request error analysis.

### Key Features
- **Conversational Recall**: Billy can recall past interactions using the `memory` table, supporting requests like "What did I just ask you?" or "What were the last 3 things I asked you?".
- **Code Debugging**: Logs errors in the `learning` table and provides suggestions for fixes using the LLM.
- **File Operations**: Manages GitHub repository files with a local-first approach, ensuring changes are tested before pushing.
- **Self-Improvement**: Learns from interactions by logging successes and failures, improving future responses.

## Where Billy Is Going
- **Enhanced Learning**: Expand the `learning` table analysis to include predictive insights, such as identifying patterns in user errors to proactively suggest improvements.
- **Advanced Repository Management**: Add features like automated pull requests, code reviews, and CI/CD integration for the GitHub repository.
- **Natural Language Understanding**: Improve the LLM’s intent detection by fine-tuning prompts and adding more context, ensuring accurate interpretation of complex user requests.
- **Scalability**: Optimize database queries further and explore migrating to a more robust database (e.g., PostgreSQL) if the user base grows.
- **User Experience**: Enhance the web interface with features like chat history search, better error visualization, and interactive code execution feedback.
- **Autonomy**: Enable Billy to autonomously suggest and implement repository improvements, such as adding a README.md or optimizing code, with user approval.

Billy’s journey is about becoming a smarter, more autonomous assistant that can handle a wide range of development tasks while continuously learning and improving.