from scanner_re import tokenize
from parser import parse
from helper_functions import read_source_file
from semantic_analyzer import check_semantics
from format_nodes import format_ast_string
from code_generation import generate_code
import sys
from contextlib import redirect_stdout
import pprint

#TODO: 
# Create a new main that doesnt concat decaf.asm and our program.s
# Change output.s to program.s
# Try to use our spim from our pp3 to see if we need
#  Loaded: /usr/share/spim/exceptions.s
# Do this tomorrow at work


def write_combined_asm_file(defs_path, compiled_output, combined_output_path):
    """
    Appends the Decaf runtime (defs.asm) to the compiled MIPS code
    and writes both into one .s file.
    """
    with open(defs_path, "r") as f:
        defs_content = f.read()

    # If compiled_output is a list of lines, join it
    if isinstance(compiled_output, list):
        compiled_text = "\n".join(compiled_output)
    else:
        compiled_text = compiled_output

    # Combine and write
    combined = compiled_text + "\n\n" + defs_content
    with open(combined_output_path, "w") as out_file:
        out_file.write(combined)

def main():
    file_path = r"pp3-post\samples\t4.decaf"
    output_path = r"pp3-post\program.s"
    combined_path = r"pp3-post\final.s"  # for SPIM

    source_code = read_source_file(file_path)
    tokens = tokenize(source_code)
    ast_output = parse(tokens)

    if isinstance(ast_output, str):
        output = ast_output
    else:
        #pprint.pprint(ast_output)
        semantic_errors = check_semantics(ast_output, tokens)

        if semantic_errors:
            output = "\n".join(semantic_errors) + "\n"
        else:
            output = generate_code(ast_output)

    # Save compiler-only output
    with open(output_path, "w") as f:
        f.write(output)

    # Save combined .s file for QtSPIM
    defs_path = r"pp3-post\defs.asm"
    write_combined_asm_file(defs_path, output, combined_path)

    print(f"Saved output to: {output_path}")
    print(f"Saved QtSPIM-ready file to: {combined_path}")

if __name__ == "__main__":
    main()