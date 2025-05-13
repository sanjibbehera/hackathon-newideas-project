#!/bin/bash

# Start Ollama in background
ollama serve &

# Create base model
ollama create aws-iam-base -f ./ollama/Modelfile

# Train using the API (this is the actual working method)
curl -X POST http://localhost:11434/api/train \
  -H "Content-Type: application/json" \
  -d '{
    "model": "aws-iam-base",
    "training_data": "./iam_knowledge/common_questions.json",
    "output": "aws-iam-helper"
  }'

# Verify
ollama list