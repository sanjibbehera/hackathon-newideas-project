# AWS IAM Assistant Chatbot

<div align="center">
  <img src="https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6/svgs/solid/user-lock.svg" width="100">
  <img src="https://cdn.jsdelivr.net/npm/@mdi/svg@7/svg/cloud-lock-outline.svg" width="100">
  
  <h1>AWS IAM Assistant</h1>
</div>

A local AI-powered chatbot that helps with AWS IAM policy generation, troubleshooting, and best practices explanations using Ollama and FastAPI.

## Features

- 🛠️ Generate valid IAM policies based on natural language requests
- 🔍 Explain IAM concepts in simple terms
- 🚨 Troubleshoot common IAM errors
- 💻 100% local operation - no AWS credentials required
- 🚀 FastAPI backend with simple web interface

## Prerequisites

- macOS or Linux (Windows via WSL2)
- Python 3.9+
- Ollama (will be installed automatically)
- [Optional] NVIDIA GPU for better performance

## Installation

```bash
# Clone the repository
git clone https://github.com/sanjibbehera/hackathon-newideas-project.git
cd hackathon-newideas-project

# Install Python dependencies
pip install -r requirements.txt

# Run setup script (installs Ollama if missing)
./scripts/setup_ollama.sh

# Start the application
uvicorn app.main:app --reload
```

## Usage
- Access the web interface at http://localhost:8000
- Ask questions like:
  - "Create a read-only policy for S3 bucket 'my-data'"
  - "Explain IAM roles vs users"
  - "Why am I getting AccessDenied for EC2?"

## API Endpoints
```bash
POST /api/chat
Content-Type: application/json

{
  "message": "How do I restrict S3 access by IP?"
}
```

## Project Structure
```bash
hackathon-newideas-project/
├── app/                        # FastAPI application
│   ├── main.py                 # Main application
│   ├── models/                 # Data models
│   └── routes/                 # API routes
├── iam_knowledge/              # Training data
│   ├── policies/               # Policy examples
│   └── common_questions.json   # Common questions
├── ollama/                     # Ollama configuration
│   └── Modelfile               # Model definition
├── static/                     # Frontend assets
├── templates/                  # HTML templates
└── scripts/                    # Utility scripts
```

## Contributing
1. Fork the repository
2. Create a new branch (git checkout -b feature/your-feature)
3. Commit your changes
4. Push to the branch
5. Open a pull request