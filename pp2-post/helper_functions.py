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


"""Returns the line prefix with correct alignment for output (line number or 3 spaces)"""
def get_line_content(tokens, line_num):
    line_tokens = [tok for tok in tokens if tok[1] == line_num]
    if not line_tokens:
        return ""

    # Reconstruct the line using spacing from original columns
    line = ""
    current_col = 1
    for tok in line_tokens:
        token_text, _, start_col, end_col, *_ = tok
        if start_col > current_col:
            line += " " * (start_col - current_col)
        line += token_text
        current_col = end_col + 1

    return line

def line_prefix(s, indent=0):
    return " " * indent + str(s)



"""Reads the source code from a file."""
def read_source_file(path):
    try:
        with open(path, 'r') as file:
            return file.read()
    except FileNotFoundError:
        print(f"Error: File '{path}' not found.")
        exit(1)

def parse_type(tokens, index, current_token):
    if current_token[4] in ("T_Int", "T_Double", "T_Bool", "T_String", "T_Void"):
        node = {"Type": current_token[0]}  # current_token[0] is the literal value like "int"
        index, current_token = advance(tokens, index)
        return node, index, current_token
    else:
        return syntax_error(tokens, index, "Expected type"), index, current_token

def format_type(type_node):
    if isinstance(type_node, dict) and "Type" in type_node:
        return type_node["Type"]
    return str(type_node)  # Fallback in case of malformed input

def make_identifier_node(token):
    return {
        "Identifier": {
            "line_num": token[1],
            "name": token[0]
        }
    }
