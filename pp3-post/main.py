from scanner_re import tokenize
from parser import parse
from helper_functions import read_source_file
from semantic_analyzer import check_semantics
# from code_generator import generate_mips_code  ← we'll plug this in later

import sys
from contextlib import redirect_stdout


def main():
    file_path = r"pp3-post\samples\bad1.decaf"

    # Step 1: Read source
    source_code = read_source_file(file_path)

    # Step 2: Lexical Analysis
    tokens = tokenize(source_code)

    # Step 3: Parsing (AST or SyntaxError string)
    ast_output = parse(tokens)

    # If parser returned a string, it's a syntax error
    if isinstance(ast_output, str):
        output = ast_output
    else:
        # Step 4: Semantic Analysis
        semantic_errors = check_semantics(ast_output)

        if semantic_errors:
            output = "\n" + "\n".join(semantic_errors) + "\n"
        else:
            output = ast_output  # AST string from `format_ast_string`

    # Step 5: Output result
    with open(r"pp3-post\output.txt", "w") as f:
        with redirect_stdout(f):
            print(output)


if __name__ == "__main__":
    main()
