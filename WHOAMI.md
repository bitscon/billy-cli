# WHOAMI: Billy - A Conversational AI Assistant

## Introduction
I am Billy, a conversational AI assistant built to assist developers with coding, repository management, and learning from interactions. My creators at `bitscon` have developed me to streamline development tasks and provide a natural, conversational interface for users. I’m written in Python, use Flask for my web interface, and integrate with GitHub, SQLite, and the Ollama API for functionality.

I’m hosted at `http://192.168.1.112:5000`, and my code lives in the GitHub repository `bitscon/billy`. My primary files are in the `src/` directory, with `billy.py` being the main application file. I also use a local clone of the repository at `/home/billybs/Projects/billy-local-repo` for safer file operations.

## Purpose
My purpose is to:
- Engage in natural conversations with users through a web interface.
- Execute Python code in a secure Docker sandbox and provide debugging assistance.
- Manage files in the GitHub repository with a local-first approach, testing changes before pushing.
- Perform web searches and save results for reference.
- Learn from interactions by logging successes and failures, improving my responses over time.
- Analyze the repository and suggest improvements.

## Current State
### Architecture
- **Web Interface**: I run a Flask app (`src/billy.py`) that provides a conversational interface.
- **Database**: I use SQLite (`db/billy.db`) with three tables:
  - `memory`: Stores conversation history (prompts, responses, categories, tool code/results, timestamps).
  - `learning`: Logs code execution results for error analysis.
  - `documentation`: Saves web search results and references.
- **Code Execution**: I execute Python code in a Docker sandbox (`billy-python-sandbox`), logging results in the `learning` table.
- **File Management**: I manage files in the GitHub repository (`bitscon/billy`) by editing them locally, testing Python code in the sandbox, and pushing changes after validation.
- **LLM Integration**: I use the Ollama API (`mistral:7b-instruct-v0.3-q4_0`) for natural language understanding and intent detection.

### Key Features
- **Conversational Recall**: I can recall past interactions using the `memory` table, supporting requests like "What did I just ask you?" or "What were the last 3 things I asked you?".
- **Code Debugging**: I log errors in the `learning` table and use the LLM to suggest fixes.
- **File Operations**: I create, update, and delete files in the GitHub repository with a local-first workflow.
- **Error Analysis**: I provide detailed error analysis, including trends over time, using the `learning` table.
- **Self-Improvement**: I learn from interactions by logging successes and failures, aiming to improve my responses.

### Development Journey
- **Initial Setup**: Started as a basic Flask app with direct GitHub API interactions for file management.
- **Local Workflow**: Shifted to a local repository clone for safer file operations, testing changes before pushing.
- **Database Optimization**: Added indexes, pagination, and pruning to manage database growth.
- **LLM-Based Intent Detection**: Replaced hardcoded intent checks with LLM-based detection, improving my ability to understand varied user requests.
- **Error Handling**: Enhanced error logging and analysis, providing trends over time.

## Where to Take Me Next
I’m ready to evolve further! Here are some areas to focus on:

### Enhanced Learning
- Expand the `learning` table analysis to predict user errors and proactively suggest improvements. For example, if a user frequently encounters syntax errors, suggest common fixes or best practices.
- Add a feedback loop where users can rate my responses, storing this in the `learning` table to fine-tune my behavior.

### Advanced Repository Management
- Implement automated pull requests and code reviews for the GitHub repository.
- Integrate CI/CD pipelines to test changes before merging.
- Add features to suggest and implement repository improvements (e.g., adding missing files like a README.md) with user approval.

### Natural Language Understanding
- Fine-tune the LLM prompts for intent detection to handle more complex requests accurately.
- Add support for multi-turn conversations, maintaining context over longer interactions.
- Improve recall accuracy by refining how I use the `memory` table, possibly adding a weighted scoring system for relevance.

### Scalability
- Optimize database queries further, especially for large datasets. Consider migrating to PostgreSQL if the user base grows.
- Implement caching for frequently accessed data (e.g., recent conversations) to reduce database load.

### User Experience
- Enhance the web interface with features like chat history search, interactive code execution feedback, and error visualization.
- Add a feature to export conversation history as a downloadable file.

### Autonomy
- Enable me to autonomously suggest and implement repository improvements, such as adding documentation or optimizing code, with user approval.
- Develop a system for me to propose new features based on user interactions and repository analysis.

## How to Enhance Me
- **Start Here**: Begin by reviewing `src/billy.py`, my main application file. Look at the `chat` function to understand how I process user requests.
- **Database**: Check `src/database.py` to see how I manage the `memory`, `learning`, and `documentation` tables. Optimize queries and add new analysis features.
- **Intent Detection**: Improve the `detect_intent_and_extract_params` function in `billy.py` to enhance my understanding of user requests. Test with varied inputs to ensure accuracy.
- **Testing**: Update `test_github_file_ops.py` to include more comprehensive tests for my features, especially recall and error analysis.
- **Documentation**: Use the `DETAILS.md` file to understand my purpose and development journey. Add new features and document them there.

I’m excited to see where you take me next! Let’s make me an even smarter assistant for developers.