def make_pointer_line(start_col, end_col, underline=False):
    """Generate a line of spaces and carets under the offending column range."""
    if underline:
        return ' ' * (start_col - 1) + '^' * max(1, end_col - start_col + 1)
    return ' ' * (start_col - 1) + '^'




# Parser Helper Functions
"""Advances to the next token, returning the new index and current token."""
def advance(tokens, index):
    index += 1
    current_token = tokens[index] if index < len(tokens) else None
    return index, current_token

"""Checks if the current token matches the expected type."""
def lookahead(current_token, expected_type):
    return current_token is not None and current_token[4] == expected_type
    
"""Prints a syntax error message and returns a dict."""
def syntax_error(tokens, index, msg="syntax error", line_num=None, token_override=None, underline=False):
    if index < len(tokens):
        token = token_override if token_override else tokens[index]
        line_num = line_num if line_num is not None else token[1]
        start_col = token[2]
        end_col = token[3]
        error_line = get_line_content(tokens, line_num)

        pointer_line = make_pointer_line(start_col, end_col, underline)


        error_msg = (
            f"*** Error line {line_num}.\n"
            f"{error_line}\n"
            f"{pointer_line}\n"
            f"*** {msg}"
        )
    else:
        error_msg = f"*** Error at EOF\n*** {msg}"
    return {"SyntaxError": error_msg}

def find_syntax_error(node):
    if isinstance(node, dict):
        if "SyntaxError" in node:
            return node["SyntaxError"]
        for value in node.values():
            result = find_syntax_error(value)
            if result:
                return result
    elif isinstance(node, list):
        for item in node:
            result = find_syntax_error(item)
            if result:
                return result
    return None

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

def make_identifier_node(token):
    return {
        "Identifier": {
            "line_num": token[1],
            "name": token[0]
        }
    }

# Format Nodes Helper Functions
def add_line(lines, line_num, level, text, extra_indent=0):
    prefix = f"{line_num:>3}" if line_num != "" else "   "
    indent = " " * (level * 3 + extra_indent)

    if text.endswith(":") and not text.endswith(": "):
        text += " "

    lines.append(f"{prefix}{indent}{text}")

def insert_label_into_first_line(lines, label, base_level):
    if not lines:
        return lines
    # The prefix consists of a 3-character line number (or blanks) plus base_level*3 spaces.
    prefix_length = 3 + base_level * 3
    first_line = lines[0]
    prefix = first_line[:prefix_length]
    text = first_line[prefix_length:].lstrip()
    lines[0] = prefix + f"{label} {text}"
    return lines

# Semantic Analysis Helper Functions
def semantic_error(tokens, offending_token, message):
    try:
        line_num = offending_token[1]
        start_col = offending_token[2]
        end_col = offending_token[3]
    except (IndexError, TypeError):
        # Fallback values if the token is malformed
        line_num = 1
        start_col = 1
        end_col = 1

    error_line = get_line_content(tokens, line_num) or ""
    pointer_line = make_pointer_line(start_col, end_col)

    return (
        f"*** Error line {line_num}.\n"
        f"{error_line}\n"
        f"{pointer_line}\n"
        f"*** {message}"
    )


def find_operator_token(tokens, line_num, operator_text):
    for tok in tokens:
        if tok[1] == line_num and tok[0] == operator_text:
            return tok  # (text, line_num, start_col, end_col, ...)
    return None

def find_token_on_line(tokens, line_num, match_text=None, match_type=None):
    """
    Returns the first token on a given line that matches either the token text or type.
    Useful for caret positioning in semantic errors.
    """
    for tok in tokens:
        if tok[1] == line_num:
            if (match_text and tok[0] == match_text) or (match_type and tok[4] == match_type):
                return tok
    return None

def find_test_expr_token(tokens, line_num):
    """
    Finds the token that represents the beginning of a test expression on the given line.
    This is usually the first token inside the parentheses of an `if` or `for` statement.
    """
    paren_depth = 0
    found_if_or_for = False

    for i, tok in enumerate(tokens):
        if tok[1] == line_num and tok[4] in ('T_If', 'T_For'):
            found_if_or_for = True
        elif found_if_or_for and tok[0] == '(':
            paren_depth += 1
        elif found_if_or_for and paren_depth > 0:
            return tok  # return first token after '('
    
    return None