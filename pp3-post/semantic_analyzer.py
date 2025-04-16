# semantic_analyzer.py

from helper_functions import get_line_content

def check_semantics(ast, tokens):
    errors = []

    # Placeholder: we’ll walk the AST here
    # For now, just return empty
    return errors


def semantic_error(tokens, offending_token, message):
    line_num = offending_token[1]
    start_col = offending_token[2]
    error_line = get_line_content(tokens, line_num)
    pointer_line = ' ' * (start_col - 1) + '^'

    return (
        f"*** Error line {line_num}.\n"
        f"{error_line}\n"
        f"{pointer_line}\n"
        f"*** {message}"
    )
