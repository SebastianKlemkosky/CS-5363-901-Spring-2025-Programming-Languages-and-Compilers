from scanner_re import tokenize
from parser import parse
from helper_functions import read_source_file
from semantic_analyzer import check_semantics
from format_nodes import format_ast_string
from code_generation import generate_code
import sys
from contextlib import redirect_stdout
import pprint


def main():
    file_path = r"pp3-post\samples\t1.decaf"
    output_path = "output.txt"  

    source_code = read_source_file(file_path)
    tokens = tokenize(source_code)
    
    ast_output = parse(tokens)

    if isinstance(ast_output, str):
        output = ast_output
    else:
        #pprint.pprint(ast_output)
        semantic_errors = check_semantics(ast_output, tokens)

        if semantic_errors:
            output =  "\n".join(semantic_errors) + "\n"
        else:
            output = generate_code(ast_output)
                
    print(output)

    # 🔽 Write to output.txt
    with open(output_path, "w") as f:
        f.write(output)

if __name__ == "__main__":
    main()