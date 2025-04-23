# code_generation.py


def generate_code(ast_root):
    global string_labels, string_count, label_count
    string_labels = {}
    string_count = 0
    label_count = 0

    # Step 1: Check for main function
    has_main = any(
        "FnDecl" in node and node["FnDecl"]["identifier"]["Identifier"]["name"] == "main"
        for node in ast_root["Program"]
    )
    if not has_main:
        return "*** Error.\n*** Linker: function 'main' not defined"

    data_section = []
    text_section = []

    # Step 3: Add text header
    text_section.insert(0, "\t# standard Decaf preamble ")
    text_section.insert(1, "\t  .text")
    text_section.insert(2, "\t  .align 2")
    text_section.insert(3, "\t  .globl main")


    return "\n".join(data_section + text_section)

