from scanner_re import tokenize, KEYWORDS
from parser import parse
from helper_functions import read_source_file
import sys
from contextlib import redirect_stdout

def main():
    # Hardcoded file path for now
    file_path = r"pp2-post\samples\control.decaf"

    # Step 1: Read file contents
    source_code = read_source_file(file_path)

    # Step 2: Scanner Phase
    tokens = tokenize(source_code)  # Tokenize the source code

    # Step 3: Parser Phase
    ast = parse(tokens)

    print(ast)
    # Export the printed AST output to a text file
    with open(r"pp2-post\output.txt", "w") as f:
        with redirect_stdout(f):
            print(ast)

if __name__ == "__main__":
    main()