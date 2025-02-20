from scanner_re import tokenize, KEYWORDS
import os
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

        # Tokenize the source code
        tokens = tokenize(source_code)

        # Process each token
        for token in tokens:
            # If it's an error token, print the error message
            if token[4] == 'T_Error':
                print(f"\n*** Error line {token[1]}.")
                print(f"*** {token[5]}\n")
                continue  # Skip further processing for error tokens

            # For valid tokens, print details
            if token[4] not in KEYWORDS.values() and token[4] != 'T_Identifier' and token[5] != None:
                print(f"{token[0]:<12} line {token[1]} cols {token[2]}-{token[3]} is {token[4]} (value = {token[5]})")
                continue

            print(f"{token[0]:<12} line {token[1]} cols {token[2]}-{token[3]} is {token[4]} ")

    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")

if __name__ == "__main__":
    main()


