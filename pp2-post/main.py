from scanner_re import tokenize, KEYWORDS
from parser import parse
import os
import argparse

def read_source_file(path):
    try:
        with open(path, 'r') as file:
            return file.read()
    except FileNotFoundError:
        print(f"Error: File '{path}' not found.")
        exit(1)

def scanner_handler(path):    
    try:
        # Open the file and read the content
        with open(path, 'r') as file:
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
        print(f"Error: File '{path}' not found.")

def main():
    # Hardcoded file path for now
    file_path = r"pp2-post\samples\simple.decaf"

    # Step 1: Read file contents
    source_code = read_source_file(file_path)

    # Step 2: Scanner Phase
    tokens = tokenize(source_code)

    # Step 3: Parser Phase
    parse(tokens)
    

if __name__ == "__main__":
    main()


