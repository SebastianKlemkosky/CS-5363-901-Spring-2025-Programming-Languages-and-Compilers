

# Helper Functions
"""Advances to the next token, returning the new index and current token."""
def advance(tokens, index):
    index += 1
    current_token = tokens[index] if index < len(tokens) else None
    return index, current_token

"""Checks if the current token matches the expected type."""
def lookahead(current_token, expected_type):
    return current_token is not None and current_token[4] == expected_type
    
"""Prints a syntax error message and exits."""
def syntax_error(tokens, index, msg="syntax error"):
    if index < len(tokens):
        line_num = tokens[index][1]
        error_line = get_line_content(tokens, line_num)
        start_col = tokens[index][2]
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


def format_ast_string(ast_dict):
    lines = []

    def format_node(node, indent=0):
        spacing = ' ' * indent

        if 'Program' in node:
            lines.append(f"{spacing}Program: ")
            for child in node['Program']:
                format_node(child, indent + 2)

        elif 'FnDecl' in node:
            fn = node['FnDecl']
            line_num = fn.get('line_num', '')
            lines.append(f"{spacing}{line_num:<3} FnDecl:")
            lines.append(f"{spacing}     (return type) Type: {fn['return_type']}")
            lines.append(f"{spacing}{line_num:<3}   Identifier: {fn['identifier']}")
            lines.append(f"{spacing}     (body) StmtBlock:")
            format_node(fn['body'], indent + 8)

        elif 'StmtBlock' in node:
            for stmt in node['StmtBlock']:
                format_node(stmt, indent + 3)

        elif 'PrintStmt' in node:
            stmt = node['PrintStmt']
            line_num = stmt.get('line_num', '')
            lines.append(f"{spacing}PrintStmt:")
            lines.append(f"{spacing}{line_num:<6}(args) StringConstant: {stmt['args']}")

    format_node(ast_dict)
    return '\n'.join(lines)


def parse(token_stream):
    tokens = token_stream
    index = 0
    current_token = tokens[index] if tokens else None

    ast_dict, index, current_token = parse_program(tokens, index, current_token)

    # Check explicitly for syntax error
    if isinstance(ast_dict, dict) and "SyntaxError" in ast_dict:
        return ast_dict["SyntaxError"]

    ast = format_ast_string(ast_dict)
    return ast

   
def parse_program(tokens, index, current_token):
    program_node = {"Program": []}

    while current_token:
        decl_node, index, current_token = parse_declaration(tokens, index, current_token)

        # Explicitly check for syntax errors:
        if isinstance(decl_node, dict) and "SyntaxError" in decl_node:
            return decl_node, index, current_token

        program_node["Program"].append(decl_node)

    return program_node, index, current_token

def parse_declaration(tokens, index, current_token):
    line_num = current_token[1]
    type_token = current_token
    index, current_token = advance(tokens, index)

    if not lookahead(current_token, "T_Identifier"):
        return syntax_error(tokens, index, "Expected identifier after type"), index, current_token
    id_token = current_token
    index, current_token = advance(tokens, index)

    if not lookahead(current_token, "'('"):
        return syntax_error(tokens, index, "Expected '(' after identifier"), index, current_token
    index, current_token = advance(tokens, index)

    if not lookahead(current_token, "')'"):
        return syntax_error(tokens, index, "syntax error"), index, current_token
    index, current_token = advance(tokens, index)

    body_node, index, current_token = parse_statement_block(tokens, index, current_token)

    # Check for syntax error from body_node
    if isinstance(body_node, dict) and "SyntaxError" in body_node:
        return body_node, index, current_token

    node = {
        "FnDecl": {
            "line_num": line_num,
            "return_type": type_token[0],
            "identifier": id_token[0],
            "body": body_node
        }
    }

    return node, index, current_token


def parse_statement_block(tokens, index, current_token):
    index, current_token = advance(tokens, index)  # '{'

    statements = []

    while current_token and not lookahead(current_token, "'}'"):
        stmt_node, index, current_token = parse_statement(tokens, index, current_token)
        statements.append(stmt_node)

    index, current_token = advance(tokens, index)  # '}'

    return {"StmtBlock": statements}, index, current_token

def parse_statement_block(tokens, index, current_token):
    index, current_token = advance(tokens, index)  # '{'

    statements = []

    while current_token and not lookahead(current_token, "'}'"):
        stmt_node, index, current_token = parse_statement(tokens, index, current_token)
        statements.append(stmt_node)

    index, current_token = advance(tokens, index)  # '}'

    return {"StmtBlock": statements}, index, current_token

def parse_statement(tokens, index, current_token):
    if lookahead(current_token, "T_Print"):
        return parse_print_statement(tokens, index, current_token)
    else:
        syntax_error(tokens, index, "Unknown statement")


def parse_print_statement(tokens, index, current_token):
    line_num = current_token[1]  # Line number from current_token
    index, current_token = advance(tokens, index)  # Print
    index, current_token = advance(tokens, index)  # '('

    expr_token = current_token
    index, current_token = advance(tokens, index)  # StringConstant

    index, current_token = advance(tokens, index)  # ')'
    index, current_token = advance(tokens, index)  # ';'

    node = {
        "PrintStmt": {
            "line_num": line_num,
            "args": expr_token[0]
        }
    }

    return node, index, current_token
