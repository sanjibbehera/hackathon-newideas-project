#!/bin/bash

# Function to install Ollama based on OS
install_ollama() {
    case "$OSTYPE" in
        linux-gnu*)
            echo "Detected Linux, installing via curl..."
            curl -fsSL https://ollama.com/install.sh | sh
            ;;
        darwin*)
            echo "Detected macOS, installing via Homebrew..."
            # Check if Homebrew is installed
            if ! command -v brew &> /dev/null; then
                echo "Homebrew not found. Installing Homebrew first..."
                /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            fi
            brew install ollama
            ;;
        *)
            echo "Unsupported OS: $OSTYPE. Trying Linux method as fallback..."
            curl -fsSL https://ollama.com/install.sh | sh
            ;;
    esac
}

# Check if Ollama is already installed
if command -v ollama &> /dev/null; then
    echo "Ollama is already installed."
else
    echo "Ollama not found. Installing..."
    install_ollama
fi

# Verify installation was successful
if ! command -v ollama &> /dev/null; then
    echo "Failed to install Ollama. Please install manually:"
    echo "Linux: curl -fsSL https://ollama.com/install.sh | sh"
    echo "macOS: brew install ollama"
    exit 1
fi

# Start Ollama service (if not running)
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    if ! systemctl is-active --quiet ollama; then
        echo "Starting Ollama service..."
        sudo systemctl start ollama
    fi
elif [[ "$OSTYPE" == "darwin"* ]]; then
    if ! brew services list | grep ollama | grep -q started; then
        echo "Starting Ollama service..."
        brew services start ollama
    fi
fi

# Create the custom model
echo "Creating AWS IAM helper model..."
ollama create aws-iam-helper -f ./ollama/Modelfile

# Verify model creation
if ollama list | grep -q aws-iam-helper; then
    echo "Setup complete! You can test with:"
    echo "  ollama run aws-iam-helper 'Explain IAM roles'"
else
    echo "Model creation failed. Check Ollama logs and try:"
    echo "  ollama create aws-iam-helper -f ./ollama/Modelfile"
    exit 1
fi