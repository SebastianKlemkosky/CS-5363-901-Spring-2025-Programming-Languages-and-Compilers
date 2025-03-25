from format_nodes import format_ast_string
from helper_functions import lookahead, advance, syntax_error

precedence = {
    '+': 1,
    '-': 1,
    '*': 2,
    '/': 2
}

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

        if not lookahead(current_token, "')'"):
            while True:
                param_line_num = current_token[1]

                # Parameter type
                if current_token[4] not in ('T_Int', 'T_Double', 'T_Bool', 'T_String'):
                    return syntax_error(tokens, index, "Expected type in parameter list"), index, current_token
                param_type = current_token[0]
                index, current_token = advance(tokens, index)

                # Parameter identifier
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

    # Handle variable declaration
    elif lookahead(current_token, "';'"):
        index, current_token = advance(tokens, index)
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
    statements = []

    if not lookahead(current_token, "'{'"):
        return syntax_error(tokens, index, "Expected '{' to begin block"), index, current_token
    index, current_token = advance(tokens, index)  # consume '{'

    while current_token is not None and not lookahead(current_token, "'}'"):
        start_index = index  # track index before parsing
        stmt_node, index, current_token = parse_statement(tokens, index, current_token)
        statements.append(stmt_node)

        # Prevent infinite loop by checking if token stream advanced
        if index == start_index:
            print("*** Internal error: parser did not advance on statement. Breaking loop to avoid infinite loop.")
            break

    if not lookahead(current_token, "'}'"):
        return syntax_error(tokens, index, "Expected '}' at end of block"), index, current_token
    index, current_token = advance(tokens, index)  # consume '}'

    return {"StmtBlock": statements}, index, current_token

def parse_statement(tokens, index, current_token):
    if lookahead(current_token, "T_Print"):
        return parse_print_statement(tokens, index, current_token)

    elif lookahead(current_token, "T_Return"):
        return parse_return_statement(tokens, index, current_token)

    elif lookahead(current_token, "T_Int") or \
        lookahead(current_token, "T_Double") or \
        lookahead(current_token, "T_Bool") or \
        lookahead(current_token, "T_String"):
        return parse_variable_declaration(tokens, index, current_token)


    elif lookahead(current_token, "T_Identifier"):
        # Peek ahead to distinguish assignment vs. call
        next_token = tokens[index + 1] if index + 1 < len(tokens) else None

        if next_token and next_token[4] == "'='":
            return parse_assignment(tokens, index, current_token)

        elif next_token and next_token[4] == "'('":
            # Parse standalone Call statement (e.g., foo(...);)
            call_node, index, current_token = parse_call(tokens, index, current_token)

            if not lookahead(current_token, "';'"):
                return syntax_error(tokens, index, "Expected ';' after function call"), index, current_token
            index, current_token = advance(tokens, index)  # consume ';'

            return call_node, index, current_token

        else:
            return syntax_error(tokens, index, "Unexpected identifier usage"), index, current_token

    else:
    # Avoid infinite loop by consuming the current token
        line_num = current_token[1] if current_token else -1
        index, current_token = advance(tokens, index)
        return syntax_error(tokens, index, "Unknown statement type", line_num), index, current_token
    
def parse_assignment(tokens, index, current_token):
    line_num = current_token[1]
    target_token = current_token
    index, current_token = advance(tokens, index)

    if not lookahead(current_token, "'='"):
        return syntax_error(tokens, index, "Expected '=' in assignment"), index, current_token
    index, current_token = advance(tokens, index)  # consume '='

    # Use full expression parser for RHS
    expr_node, index, current_token = parse_expression(tokens, index, current_token)
    if isinstance(expr_node, dict) and "SyntaxError" in expr_node:
        return expr_node, index, current_token

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
            "value": expr_node
        }
    }

    return node, index, current_token

def parse_variable_declaration(tokens, index, current_token):
    line_num = current_token[1]
    type_token = current_token
    index, current_token = advance(tokens, index)

    if not lookahead(current_token, "T_Identifier"):
        return syntax_error(tokens, index, "Expected identifier after type"), index, current_token
    id_token = current_token
    index, current_token = advance(tokens, index)

    # Defensive check: only a semicolon is valid after VarDecl
    if not lookahead(current_token, "';'"):
        return syntax_error(tokens, index, "Expected ';' after identifier in variable declaration"), index, current_token

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

    # Parse expression directly (no parentheses)
    expr_node, index, current_token = parse_expression(tokens, index, current_token)
    if isinstance(expr_node, dict) and "SyntaxError" in expr_node:
        return expr_node, index, current_token

    if not lookahead(current_token, "';'"):
        return syntax_error(tokens, index, "Expected ';' after return expression"), index, current_token
    index, current_token = advance(tokens, index)  # consume ';'

    return {
        "ReturnStmt": {
            "line_num": line_num,
            "expr": expr_node
        }
    }, index, current_token

def parse_print_statement(tokens, index, current_token):
    line_num = current_token[1]
    index, current_token = advance(tokens, index)  # consume 'Print'

    if not lookahead(current_token, "'('"):
        return syntax_error(tokens, index, "Expected '(' after Print"), index, current_token
    index, current_token = advance(tokens, index)  # consume '('

    args = []

    if not lookahead(current_token, "')'"):
        while True:
            expr_node, index, current_token = parse_expression(tokens, index, current_token)
            if isinstance(expr_node, dict) and "SyntaxError" in expr_node:
                return expr_node, index, current_token
            args.append(expr_node)

            if lookahead(current_token, "')'"):
                break
            elif lookahead(current_token, "','"):
                index, current_token = advance(tokens, index)
            else:
                return syntax_error(tokens, index, "Expected ',' or ')' in Print arguments"), index, current_token

    index, current_token = advance(tokens, index)  # consume ')'

    if not lookahead(current_token, "';'"):
        return syntax_error(tokens, index, "Expected ';' after Print"), index, current_token
    index, current_token = advance(tokens, index)  # consume ';'

    node = {
        "PrintStmt": {
            "line_num": line_num,
            "args": args
        }
    }

    return node, index, current_token

def parse_call(tokens, index, current_token):
    line_num = current_token[1]
    function_token = current_token
    index, current_token = advance(tokens, index)  # consume function identifier

    if not lookahead(current_token, "'('"):
        return syntax_error(tokens, index, "Expected '(' after function name"), index, current_token
    index, current_token = advance(tokens, index)  # consume '('

    actuals = []

    # Check for empty argument list
    if not lookahead(current_token, "')'"):
        while True:
            expr_node, index, current_token = parse_expression(tokens, index, current_token)
            if isinstance(expr_node, dict) and "SyntaxError" in expr_node:
                return expr_node, index, current_token
            actuals.append(expr_node)

            if lookahead(current_token, "')'"):
                break
            elif lookahead(current_token, "','"):
                index, current_token = advance(tokens, index)
            else:
                return syntax_error(tokens, index, "Expected ',' or ')' in argument list"), index, current_token

    index, current_token = advance(tokens, index)  # consume ')'

    node = {
        "Call": {
            "line_num": line_num,
            "identifier": function_token[0],
            "actuals": actuals
        }
    }

    return node, index, current_token

def parse_expression(tokens, index, current_token):
    return parse_logical_expr(tokens, index, current_token)

def parse_logical_expr(tokens, index, current_token):
    left, index, current_token = parse_equality_expr(tokens, index, current_token)

    while current_token and current_token[0] in ('&&', '||'):
        op_token = current_token
        index, current_token = advance(tokens, index)
        right, index, current_token = parse_equality_expr(tokens, index, current_token)
        left = {
            "LogicalExpr": {
                "line_num": op_token[1],
                "left": left,
                "operator": op_token[0],
                "right": right
            }
        }

    return left, index, current_token

def parse_equality_expr(tokens, index, current_token):
    left, index, current_token = parse_relational_expr(tokens, index, current_token)

    while current_token and current_token[0] in ('==', '!='):
        op_token = current_token
        index, current_token = advance(tokens, index)
        right, index, current_token = parse_relational_expr(tokens, index, current_token)
        left = {
            "EqualityExpr": {
                "line_num": op_token[1],
                "left": left,
                "operator": op_token[0],
                "right": right
            }
        }

    return left, index, current_token

def parse_relational_expr(tokens, index, current_token):
    left, index, current_token = parse_arithmetic_expr(tokens, index, current_token, 0)

    while current_token and current_token[0] in ('<', '<=', '>', '>='):
        op_token = current_token
        index, current_token = advance(tokens, index)
        right, index, current_token = parse_arithmetic_expr(tokens, index, current_token, 0)
        left = {
            "RelationalExpr": {
                "line_num": op_token[1],
                "left": left,
                "operator": op_token[0],
                "right": right
            }
        }

    return left, index, current_token

def parse_arithmetic_expr(tokens, index, current_token, min_prec):
    # Parse the left-hand side (base or nested expression)
    left, index, current_token = parse_primary(tokens, index, current_token)

    while current_token and current_token[0] in precedence and precedence[current_token[0]] >= min_prec:
        op_token = current_token
        op_prec = precedence[op_token[0]]
        index, current_token = advance(tokens, index)  # consume operator

        # Parse the right-hand side with tighter or equal precedence
        right, index, current_token = parse_arithmetic_expr(tokens, index, current_token, op_prec + 1)

        left = {
            "ArithmeticExpr": {
                "line_num": op_token[1],
                "left": left,
                "operator": op_token[0],
                "right": right
            }
        }

    return left, index, current_token

def parse_primary(tokens, index, current_token):
    # Handle parenthesized expressions
    if lookahead(current_token, "'('"):
        index, current_token = advance(tokens, index)  # consume '('
        expr_node, index, current_token = parse_arithmetic_expr(tokens, index, current_token, 0)
        if not lookahead(current_token, "')'"):
            return syntax_error(tokens, index, "Expected ')'"), index, current_token
        index, current_token = advance(tokens, index)
        return expr_node, index, current_token

    # Otherwise, fall back to your existing expression parser for literals and variables
    return parse_expression_leaf(tokens, index, current_token)

def parse_expression_leaf(tokens, index, current_token):
    line_num = current_token[1]

    if lookahead(current_token, "'!'"):
        operator_token = current_token
        index, current_token = advance(tokens, index)
        right_expr, index, current_token = parse_expression(tokens, index, current_token)
        return {
            "LogicalExpr": {
                "line_num": line_num,
                "operator": operator_token[0],
                "right": right_expr
            }
        }, index, current_token

    if lookahead(current_token, "T_ReadInteger"):
        index, current_token = advance(tokens, index)
        if not lookahead(current_token, "'('"):
            return syntax_error(tokens, index, "Expected '(' after ReadInteger"), index, current_token
        index, current_token = advance(tokens, index)
        if not lookahead(current_token, "')'"):
            return syntax_error(tokens, index, "Expected ')' after ReadInteger"), index, current_token
        index, current_token = advance(tokens, index)
        return {
            "ReadIntegerExpr": {
                "line_num": line_num
            }
        }, index, current_token

    if lookahead(current_token, "T_Identifier"):
        next_token = tokens[index + 1] if index + 1 < len(tokens) else None
        if next_token and next_token[4] == "'('":
            return parse_call(tokens, index, current_token)
        node = {
            "FieldAccess": {
                "line_num": current_token[1],
                "identifier": current_token[0]
            }
        }
        index, current_token = advance(tokens, index)
        return node, index, current_token

    if lookahead(current_token, "T_BoolConstant"):
        node = {
            "BoolConstant": {
                "line_num": line_num,
                "value": current_token[0]
            }
        }
        index, current_token = advance(tokens, index)
        return node, index, current_token

    if lookahead(current_token, "T_IntConstant"):
        node = {
            "IntConstant": {
                "line_num": line_num,
                "value": current_token[0]
            }
        }
        index, current_token = advance(tokens, index)
        return node, index, current_token

    if lookahead(current_token, "T_DoubleConstant"):
        node = {
            "DoubleConstant": {
                "line_num": line_num,
                "value": current_token[0]
            }
        }
        index, current_token = advance(tokens, index)
        return node, index, current_token


    if lookahead(current_token, "T_StringConstant"):
        node = {
            "StringConstant": {
                "line_num": line_num,
                "value": current_token[0]
            }
        }
        index, current_token = advance(tokens, index)
        return node, index, current_token


    return syntax_error(tokens, index, "Unrecognized expression"), index, current_token
