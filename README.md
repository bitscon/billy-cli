# Billy - A Conversational AI Assistant

## Overview
Billy is a conversational AI assistant designed to interact with users through a web interface, perform tasks like code execution, file management, and web searches, and learn from interactions to improve its responses. Built with Python and Flask, Billy integrates with GitHub for repository management, uses SQLite for data persistence, and leverages the Ollama API for natural language understanding.

## Features
- **Conversational Interface**: Engage in natural conversations via a Flask-based web app.
- **Code Execution**: Run Python code in a secure Docker sandbox and debug errors.
- **File Management**: Create, update, and delete files in a GitHub repository with local testing.
- **Web Search**: Perform web searches and save results for reference.
- **Learning Capabilities**: Log interactions and errors to improve future responses.
- **Repository Analysis**: Analyze and suggest improvements for the GitHub repository.

## Installation
1. **Clone the Repository**:
   ```bash
   git clone https://github.com/bitscon/billy.git
   cd billy
   ```
2. **Set Up a Virtual Environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Configure the Database**:
   - Ensure SQLite is installed.
   - Initialize the database by running the Flask app for the first time.
5. **Run the Application**:
   ```bash
   python3 src/billy.py
   ```
   Access Billy at `http://localhost:5000`.

## Usage
- **Interact with Billy**: Open the web interface and start a conversation.
- **Run Code**: Provide Python code snippets for execution in a secure sandbox.
- **Manage Files**: Request Billy to create, update, or delete files in the GitHub repository.
- **Search the Web**: Ask Billy to search for information online.

## Contributing
Contributions are welcome! Please fork the repository, create a feature branch, and submit a pull request with your changes. Ensure all tests pass before submitting.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact
For issues or inquiries, please open an issue on GitHub or contact the maintainers at [bitscon@example.com](mailto:bitscon@example.com).