from scanner_re import tokenize, KEYWORDS
from parser import parse
from helper_functions import read_source_file
import sys
from contextlib import redirect_stdout
import argparse


def main():
    # Set up argument parsing to dynamically get the filename
    parser = argparse.ArgumentParser(description='Process a source code file.')
    parser.add_argument('file', type=str, help='Path to the source code file')  # Expects the file as an argument
    args = parser.parse_args()

    # Get the filename from the command-line arguments
    filename = args.file
    
    try:
        # Open the file and read the content
        with open(filename, 'r') as file:
            source_code = file.read()

        # Hardcoded file path for now

        # Step 1: Read file contents
        source_code = read_source_file(source_code)

        # Step 2: Scanner Phase
        tokens = tokenize(source_code)

        # Step 3: Parser Phase
        ast_output = parse(tokens)  # Can be either a string (error) or formatted AST
        print(ast_output)

    
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")



if __name__ == "__main__":
    main()