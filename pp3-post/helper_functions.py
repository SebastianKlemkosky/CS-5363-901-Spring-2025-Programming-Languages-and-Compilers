def make_pointer_line(start_col, end_col, underline=False):
    """Generate a line of spaces and carets under the offending column range."""
    if underline:
        return ' ' * (start_col - 1) + '^' * max(1, end_col - start_col + 1)
    return ' ' * (start_col - 1) + '^'

def get_token_range_on_line(tokens, line_num):
    """
    Returns the (start_col, end_col) that spans all tokens on the given line.
    Useful for underlining entire expressions like loop tests.
    """
    start_col = None
    end_col = None

    for token in tokens:
        if token[1] == line_num:
            if start_col is None or token[2] < start_col:
                start_col = token[2]
            if end_col is None or token[3] > end_col:
                end_col = token[3]

    return start_col, end_col

def get_token_range_between(tokens, line_num, start_text, end_text):
    """
    Returns (start_col, end_col) for tokens between two delimiters on the same line.
    E.g., between the first ';' and the second ';' in a for loop header.
    """
    start_index = None
    end_index = None

    # Collect all tokens on the target line
    line_tokens = [t for t in tokens if t[1] == line_num]

    # Find first and second semicolon (or custom markers)
    for i, token in enumerate(line_tokens):
        if token[0] == start_text and start_index is None:
            start_index = i
        elif token[0] == end_text and start_index is not None:
            end_index = i
            break

    if start_index is not None and end_index is not None and end_index > start_index + 1:
        start_col = line_tokens[start_index + 1][2]
        end_col = line_tokens[end_index - 1][3]
        return start_col, end_col

    return None, None

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

def initialize_scope_system():
    """
    Resets the scope system and initializes the global scope.
    """
    global scope_stack, scope_names
    scope_stack = [{}]
    scope_names = ["global"]

def push_scope(scope_label):
    """
    Pushes a new scope onto the stack.
    Returns the current label for convenience.
    """
    scope_stack.append({})
    scope_names.append(scope_label)
    return scope_label

def pop_scope():
    """
    Pops the current scope from the stack.
    """
    if scope_stack:
        scope_stack.pop()
        scope_names.pop()

def declare(scope_label, name, entry):
    """
    Adds a name to the current scope dictionary.
    """
    current_scope = scope_stack[-1]
    current_scope[name] = entry

def is_declared_in_scope(scope_label, name):
    """
    Checks only the top (current) scope for the given name.
    """
    return name in scope_stack[-1]

def lookup(name):
    """
    Searches all scopes from innermost to outermost.
    Returns the first match found, or None.
    """
    for scope in reversed(scope_stack):
        if name in scope:
            return scope[name]
    return None

def semantic_error(tokens, token, message, underline=False):
    """
    Formats a semantic error message with line number and caret pointer.
    """
    line_num = token[1]
    start_col = token[2]
    end_col = token[3]

    error_line = get_line_content(tokens, line_num)
    pointer_line = make_pointer_line(start_col, end_col, underline)

    return (
        f"\n*** Error line {line_num}.\n"
        f"{error_line}\n"
        f"{pointer_line}\n"
        f"*** {message}\n"
    )

def find_token_on_line(tokens, line_num, match_text=None):
    """
    Temporary placeholder for finding a token on a given line.
    Replace with full implementation later.
    """
    for token in tokens:
        if token[1] == line_num:
            if match_text is None or token[0] == match_text:
                return token
    return tokens[0] if tokens else None

def get_declared_type(decl):
    """
    Given a VarDecl or a type dict, return the base type string.
    Handles wrapped types like {'Type': 'int'}.
    """
    if isinstance(decl, dict):
        # Case: a wrapped type from a declaration or a 'Type' field
        if "type" in decl:
            type_field = decl["type"]
        else:
            type_field = decl

        if isinstance(type_field, dict) and "Type" in type_field:
            return type_field["Type"]

        # Direct string case (already unwrapped)
        if isinstance(type_field, str):
            return type_field

    return decl  # fallback, e.g. already a string like 'int'

# Code Generation Helpers
def calculate_frame_size(offset):
    """
    Given final stack offset, calculate aligned frame size for MIPS.
    Adjustment of +8 because initial offset was -8 for saved $fp/$ra.
    """
    adjusted_offset = abs(offset + 8)
    frame_size = ((adjusted_offset + 3) // 4) * 4  # Round up to nearest 4
    return frame_size

def allocate_temp(context):
    tmp_num = context["temp_counter"]
    tmp_name = f"_tmp{tmp_num}"
    context["temp_counter"] += 1

    tmp_offset = context["offset"]
    context["temp_locations"][tmp_name] = tmp_offset
    context["offset"] -= 4

    #print(f"ALLOCATE: {tmp_name}")   # ← 🧠 DEBUG PRINT HERE

    return tmp_name, tmp_offset

def get_print_function_for_type(var_type):
    """
    Maps a Decaf type to the corresponding _Print* function.
    """
    type_map = {
        "string": "_PrintString",
        "int": "_PrintInt",
        "bool": "_PrintBool",
        "double": "_PrintDouble"
    }
    return type_map.get(var_type, "_PrintInt")  # fallback to _PrintInt

def get_var_type(field_access, context):
    """
    Given a FieldAccess node and context, return the variable's declared type.
    """
    var_name = field_access["identifier"]
    var_types = context.get("var_types", {})

    var_type = var_types.get(var_name)
    if var_type is None:
        raise KeyError(f"Type for variable '{var_name}' not found in var_types")

    return var_type

def format_relop_comment(tmp_name, left_var, operator, right_var):
    """
    Given tmp_name, left_var, operator, right_var,
    returns a pretty string for relational operation comment.
    """
    # For display purposes, flip <= to < and >= to >
    display_operator = operator
    if operator == "<=":
        display_operator = "<"
    elif operator == ">=":
        display_operator = ">"
    
    return f"\t# {tmp_name} = {left_var} {display_operator} {right_var}"

def format_offset(offset):
    """
    Formats a stack offset for comments.
    Always adds '+' sign if positive, leaves '-' alone.
    """
    if offset >= 0:
        return f"+{offset}"
    else:
        return str(offset)

