#!/bin/bash
# exec.sh: Executes the Python lexical analyzer on the provided source file.

# Check if a file path is provided as an argument
if [ -z "$1" ]; then
  echo "Error: No source file provided."
  echo "Usage: ./exec.sh <path_to_source_file>"
  exit 1
fi

# Run the Python lexer on the given source file
python3 main.py "$1"
