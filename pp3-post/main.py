from scanner_re import tokenize
from parser import parse
from helper_functions import read_source_file
from semantic_analyzer import check_semantics
from format_nodes import format_ast_string
import sys
from contextlib import redirect_stdout


def main():
    file_path = r"pp3-post\samples\bad3.decaf"
    source_code = read_source_file(file_path)

    tokens = tokenize(source_code)
    print("Tokens:", tokens)

    ast_output = parse(tokens)
    print("Parsed type:", type(ast_output))
    
    if isinstance(ast_output, str):
        output = ast_output
    else:
        print("Semantic check starting...")
        semantic_errors = check_semantics(ast_output, tokens)

        if semantic_errors:
            output = "\n" + "\n".join(semantic_errors) + "\n"
        else:
            output = format_ast_string(ast_output)  

    print(output)


if __name__ == "__main__":
    main()
