# code_generation.py


def generate_code(ast_root):

    # Step 1: Check for main function
    has_main = any(
        "FnDecl" in node and node["FnDecl"]["identifier"]["Identifier"]["name"] == "main"
        for node in ast_root["Program"]
    )
    if not has_main:
        return "*** Error.\n*** Linker: function 'main' not defined"

    return ""