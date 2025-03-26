# Helper Functions
"""Advances to the next token, returning the new index and current token."""
def advance(tokens, index):
    index += 1
    current_token = tokens[index] if index < len(tokens) else None
    return index, current_token

"""Checks if the current token matches the expected type."""
def lookahead(current_token, expected_type):
    return current_token is not None and current_token[4] == expected_type
    
"""Prints a syntax error message and returns a dict."""
def syntax_error(tokens, index, msg="syntax error", line_num=None):
    if index < len(tokens):
        token = tokens[index]
        # Prefer passed-in line_num, fall back to token
        line_num = line_num if line_num is not None else token[1]
        start_col = token[2]
        error_line = get_line_content(tokens, line_num)
        pointer_line = ' ' * (start_col - 1) + '^'

        error_msg = (
            f"*** Error line {line_num}.\n"
            f"{error_line}\n"
            f"{pointer_line}\n"
            f"*** {msg}"
        )
    else:
        error_msg = f"*** Error at EOF\n*** {msg}"

    return {"SyntaxError": error_msg}

def get_line_content(tokens, line_num):
    line_tokens = [tok[0] for tok in tokens if tok[1] == line_num]
    return ' '.join(line_tokens)

"""Returns the line prefix with correct alignment for output (line number or 3 spaces)"""
def line_prefix(line_num):
    return f"{line_num:>3}  " if line_num != '' else "   "

"""Reads the source code from a file."""
def read_source_file(path):
    try:
        with open(path, 'r') as file:
            return file.read()
    except FileNotFoundError:
        print(f"Error: File '{path}' not found.")
        exit(1)
