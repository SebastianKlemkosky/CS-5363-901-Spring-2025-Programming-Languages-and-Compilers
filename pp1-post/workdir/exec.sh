#!/bin/bash
# exec.sh: Executes the Python lexer on the given source file

# Check if a file argument is provided
if [ -z "$1" ]; then
    echo "Error: No file provided."
    echo "Usage: ./exec.sh <filepath>"
    exit 1
fi

# Check if the provided file exists
if [ ! -f "$1" ]; then
    echo "Error: File '$1' not found."
    exit 1
fi

# Run the Python lexer on the provided source file
python3 main.py "$1"
