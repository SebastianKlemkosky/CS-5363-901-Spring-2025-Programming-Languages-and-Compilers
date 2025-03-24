

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

# Format Print Functions
def format_program(node, indent=0):
    lines = []
    spacing = ' ' * indent
    lines.append(f"{spacing}Program: ")
    for child in node['Program']:
        lines.extend(format_node(child, indent + 2))
    return lines

def format_function_declaration(node, indent=0):
    lines = []
    spacing = ' ' * indent
    fn = node['FnDecl']
    line_num = fn.get('line_num', '')
    lines.append(f"{spacing}{line_num:<3} FnDecl:")
    lines.append(f"{spacing}     (return type) Type: {fn['return_type']}")
    lines.append(f"{spacing}{line_num:<3}   Identifier: {fn['identifier']}")

    if fn["formals"]:
        for formal in fn["formals"]:
            f_line_num = formal["VarDecl"]["line_num"]
            f_type = formal["VarDecl"]["type"]
            f_id = formal["VarDecl"]["identifier"]
            lines.append(f"{spacing}{line_num:<3}   (formals) VarDecl:")
            lines.append(f"{spacing}         Type: {f_type}")
            lines.append(f"{spacing}{f_line_num:<3}      Identifier: {f_id}")

    lines.append(f"{spacing}     (body) StmtBlock:")
    lines.extend(format_node(fn['body'], indent + 8))
    return lines

def format_statement_block(node, indent=0):
    lines = []
    for stmt in node['StmtBlock']:
        lines.extend(format_node(stmt, indent + 3))  # always indent block statements by +3
    return lines


def format_print_statement(node, indent=0):
    lines = []
    spacing = ' ' * indent
    stmt = node['PrintStmt']
    line_num = stmt.get('line_num', '')

    lines.append(f"{spacing}PrintStmt:")
    lines.extend(format_node(stmt['args'], indent + 6))
    return lines



def format_node(node, indent=0):
    if 'Program' in node:
        return format_program(node, indent)
    elif 'FnDecl' in node:
        return format_function_declaration(node, indent)
    elif 'VarDecl' in node:
        return format_variable_declaration(node, indent)
    elif 'StmtBlock' in node:
        return format_statement_block(node, indent)
    elif 'PrintStmt' in node:
        return format_print_statement(node, indent)
    elif 'ReturnStmt' in node:
        return format_return_statement(node, indent)
    elif 'Call' in node:
        return format_call(node, indent)
    elif 'AssignExpr' in node:
        return format_assignment_expression(node, indent)
    elif 'ArithmeticExpr' in node:
        return format_arithmetic_expression(node, indent)
    elif 'FieldAccess' in node:
        return format_field_access(node, indent)
    elif 'IntConstant' in node:
        return format_int_constant(node, indent)
    else:
        return []

def format_call(node, indent=0):
    lines = []
    spacing = ' ' * indent
    call = node['Call']
    line_num = call.get('line_num', '')
    lines.append(f"{spacing}{line_num:<3}   (args) Call:")
    lines.append(f"{spacing}{line_num:<3}      Identifier: {call['identifier']}")
    lines.append(f"{spacing}{line_num:<3}      (actuals):")
    
    # Flatten actuals: just print Identifier directly
    actual = call['actuals']
    if 'FieldAccess' in actual:
        fa = actual['FieldAccess']
        lines.append(f"{spacing}{fa['line_num']:<3}         Identifier: {fa['identifier']}")

    return lines




def format_int_constant(node, indent=0):
    lines = []
    spacing = ' ' * indent
    const = node['IntConstant']
    line_num = const.get('line_num', '')
    lines.append(f"{spacing}{line_num:<3}      IntConstant: {const['value']}")
    return lines

def format_assignment_expression(node, indent=0):
    lines = []
    spacing = ' ' * indent
    expr = node['AssignExpr']
    line_num = expr.get('line_num', '')
    lines.append(f"{spacing}{line_num:<3} AssignExpr:")
    lines.extend(format_node(expr['target'], indent + 6))
    lines.append(f"{spacing}{line_num:<3}   Operator: {expr['operator']}")
    lines.extend(format_node(expr['value'], indent + 6))
    return lines


def format_return_statement(node, indent=0):
    lines = []
    spacing = ' ' * indent
    stmt = node['ReturnStmt']
    line_num = stmt.get('line_num', '')
    lines.append(f"{spacing}{line_num:<3} ReturnStmt:")
    lines.extend(format_node(stmt['expr'], indent + 6))
    return lines

def format_arithmetic_expression(node, indent=0):
    lines = []
    spacing = ' ' * indent
    expr = node['ArithmeticExpr']
    line_num = expr.get('line_num', '')
    lines.append(f"{spacing}{line_num:<3} ArithmeticExpr:")
    lines.extend(format_node(expr['left'], indent + 6))
    lines.append(f"{spacing}{line_num:<3}      Operator: {expr['operator']}")
    lines.extend(format_node(expr['right'], indent + 6))
    return lines

def format_field_access(node, indent=0):
    lines = []
    spacing = ' ' * indent
    fa = node['FieldAccess']
    line_num = fa.get('line_num', '')
    lines.append(f"{spacing}{line_num:<3}      FieldAccess:")
    lines.append(f"{spacing}{line_num:<3}         Identifier: {fa['identifier']}")
    return lines


def format_variable_declaration(node, indent=0):
    lines = []
    spacing = ' ' * indent
    var = node['VarDecl']
    line_num = var.get('line_num', '')
    lines.append(f"{spacing}{line_num:<3} VarDecl: ")
    lines.append(f"{spacing}     Type: {var['type']}")
    lines.append(f"{spacing}{line_num:<3}   Identifier: {var['identifier']}")
    return lines


def format_ast_string(ast_dict):
    lines = format_node(ast_dict)
    return '\n'.join(lines)

# Parse Functions

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

    if lookahead(current_token, "'('"):  # function declaration
        index, current_token = advance(tokens, index)  # consume '('

        formals = []

        # Handle ( ) empty case
        if not lookahead(current_token, "')'"):
            while True:
                param_line_num = current_token[1]

                # Type
                if current_token[4] not in ('T_Int', 'T_Double', 'T_Bool', 'T_String'):
                    return syntax_error(tokens, index, "Expected type in parameter list"), index, current_token
                param_type = current_token[0]
                index, current_token = advance(tokens, index)

                # Identifier
                if not lookahead(current_token, "T_Identifier"):
                    return syntax_error(tokens, index, "Expected identifier in parameter list"), index, current_token
                param_id = current_token[0]
                index, current_token = advance(tokens, index)

                formals.append({
                    "VarDecl": {
                        "line_num": param_line_num,
                        "type": param_type,
                        "identifier": param_id
                    }
                })

                if lookahead(current_token, "')'"):
                    break
                elif lookahead(current_token, "','"):
                    index, current_token = advance(tokens, index)
                else:
                    return syntax_error(tokens, index, "Expected ',' or ')' in parameter list"), index, current_token

        index, current_token = advance(tokens, index)  # consume ')'

        body_node, index, current_token = parse_statement_block(tokens, index, current_token)

        node = {
            "FnDecl": {
                "line_num": line_num,
                "return_type": type_token[0],
                "identifier": id_token[0],
                "formals": formals,
                "body": body_node
            }
        }

        return node, index, current_token

    elif lookahead(current_token, "';'"):  # variable declaration
        index, current_token = advance(tokens, index)  # consume ';'

        node = {
            "VarDecl": {
                "line_num": line_num,
                "type": type_token[0],
                "identifier": id_token[0]
            }
        }

        return node, index, current_token

    else:
        return syntax_error(tokens, index, "Expected '(' or ';' after identifier"), index, current_token

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

    elif current_token[4] in ("T_Int", "T_Double", "T_Bool", "T_String"):
        return parse_variable_decl(tokens, index, current_token)

    elif lookahead(current_token, "T_Return"):
        return parse_return_statement(tokens, index, current_token)

    elif lookahead(current_token, "T_Identifier"):
        return parse_assignment(tokens, index, current_token)

    else:
        return syntax_error(tokens, index, f"Unknown statement: {current_token[0]}"), index + 1, tokens[index + 1] if (index + 1) < len(tokens) else None

def parse_assignment(tokens, index, current_token):
    line_num = current_token[1]
    target_token = current_token
    index, current_token = advance(tokens, index)

    if not lookahead(current_token, "'='"):
        return syntax_error(tokens, index, "Expected '=' in assignment"), index, current_token
    index, current_token = advance(tokens, index)  # consume '='

    # Handle arithmetic expr: ident + ident
    if lookahead(current_token, "T_Identifier"):
        left_token = current_token
        index, current_token = advance(tokens, index)

        if lookahead(current_token, "'+'"):
            operator_token = current_token
            index, current_token = advance(tokens, index)

            if not lookahead(current_token, "T_Identifier"):
                return syntax_error(tokens, index, "Expected identifier after '+'"), index, current_token
            right_token = current_token
            index, current_token = advance(tokens, index)

            if not lookahead(current_token, "';'"):
                return syntax_error(tokens, index, "Expected ';' after assignment"), index, current_token
            index, current_token = advance(tokens, index)  # consume ';'

            node = {
                "AssignExpr": {
                    "line_num": line_num,
                    "target": {
                        "FieldAccess": {
                            "line_num": line_num,
                            "identifier": target_token[0]
                        }
                    },
                    "operator": "=",
                    "value": {
                        "ArithmeticExpr": {
                            "line_num": line_num,
                            "left": {"FieldAccess": {"line_num": line_num, "identifier": left_token[0]}},
                            "operator": operator_token[0],
                            "right": {"FieldAccess": {"line_num": line_num, "identifier": right_token[0]}}
                        }
                    }
                }
            }

            return node, index, current_token

    # fallback (in case it's still just an int constant)
    return syntax_error(tokens, index, "Expected expression after '='"), index, current_token


def parse_variable_decl(tokens, index, current_token):
    line_num = current_token[1]
    type_token = current_token
    index, current_token = advance(tokens, index)

    if not lookahead(current_token, "T_Identifier"):
        return syntax_error(tokens, index, "Expected identifier after type"), index, current_token

    id_token = current_token
    index, current_token = advance(tokens, index)

    if not lookahead(current_token, "';'"):
        return syntax_error(tokens, index, "Expected ';' after variable declaration"), index, current_token
    index, current_token = advance(tokens, index)  # consume ';'

    node = {
        "VarDecl": {
            "line_num": line_num,
            "type": type_token[0],
            "identifier": id_token[0]
        }
    }

    return node, index, current_token

def parse_return_statement(tokens, index, current_token):
    line_num = current_token[1]
    index, current_token = advance(tokens, index)  # consume 'return'

    if lookahead(current_token, "'('"):
        index, current_token = advance(tokens, index)  # consume '('

        # Stub parse_expr() for now, just get identifiers and operator
        left_token = current_token  # 'a'
        index, current_token = advance(tokens, index)

        operator_token = current_token  # '+'
        index, current_token = advance(tokens, index)

        right_token = current_token  # 'd'
        index, current_token = advance(tokens, index)

        if lookahead(current_token, "')'"):
            index, current_token = advance(tokens, index)
        else:
            return syntax_error(tokens, index, "Expected ')' after return expression"), index, current_token

        if lookahead(current_token, "';'"):
            index, current_token = advance(tokens, index)
        else:
            return syntax_error(tokens, index, "Expected ';' after return"), index, current_token

        node = {
            "ReturnStmt": {
                "line_num": line_num,
                "expr": {
                    "ArithmeticExpr": {
                        "line_num": line_num,
                        "left": {"FieldAccess": {"line_num": line_num, "identifier": left_token[0]}},
                        "operator": operator_token[0],
                        "right": {"FieldAccess": {"line_num": line_num, "identifier": right_token[0]}}
                    }
                }
            }
        }

        return node, index, current_token

    else:
        return syntax_error(tokens, index, "Expected '(' after return"), index, current_token

def parse_print_statement(tokens, index, current_token):
    line_num = current_token[1]
    index, current_token = advance(tokens, index)  # consume 'Print'
    index, current_token = advance(tokens, index)  # consume '('

    if lookahead(current_token, "T_Identifier"):
        call_node, index, current_token = parse_call(tokens, index, current_token)

        if not lookahead(current_token, "')'"):
            return syntax_error(tokens, index, "Expected ')' after Print argument"), index, current_token
        index, current_token = advance(tokens, index)  # consume ')'

        if not lookahead(current_token, "';'"):
            return syntax_error(tokens, index, "Expected ';' after Print"), index, current_token
        index, current_token = advance(tokens, index)  # consume ';'

        node = {
            "PrintStmt": {
                "line_num": line_num,
                "args": call_node
            }
        }

        return node, index, current_token

    return syntax_error(tokens, index, "Expected function call inside Print"), index, current_token

def parse_call(tokens, index, current_token):
    line_num = current_token[1]
    function_token = current_token
    index, current_token = advance(tokens, index)  # consume identifier

    if not lookahead(current_token, "'('"):
        return syntax_error(tokens, index, "Expected '(' after function name"), index, current_token
    index, current_token = advance(tokens, index)  # consume '('

    # parse single argument for now (e.g., tester(c))
    if not lookahead(current_token, "T_Identifier"):
        return syntax_error(tokens, index, "Expected argument inside function call"), index, current_token
    arg_token = current_token
    index, current_token = advance(tokens, index)

    if not lookahead(current_token, "')'"):
        return syntax_error(tokens, index, "Expected ')' after call actuals"), index, current_token
    index, current_token = advance(tokens, index)  # consume ')'

    node = {
        "Call": {
            "line_num": line_num,
            "identifier": function_token[0],
            "actuals": {
                "FieldAccess": {
                    "line_num": arg_token[1],
                    "identifier": arg_token[0]
                }
            }
        }
    }

    return node, index, current_token
