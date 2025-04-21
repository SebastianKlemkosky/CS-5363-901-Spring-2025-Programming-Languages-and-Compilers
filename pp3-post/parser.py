from format_nodes import format_ast_string
from helper_functions import lookahead, advance, syntax_error, parse_type, make_identifier_node, find_syntax_error

precedence = {
    '+': 1,
    '-': 1,
    '*': 2,
    '/': 2,
    '%': 2

}

# Parse Functions
def parse(token_stream):
    tokens = token_stream
    index = 0
    current_token = tokens[index] if tokens else None

    ast_dict, index, current_token = parse_program(tokens, index, current_token)

    # Check entire AST for syntax errors
    syntax_error = find_syntax_error(ast_dict)
    if syntax_error:
        return '\n' + syntax_error + '\n'

    return ast_dict

def parse_program(tokens, index, current_token):
    program_node = {"Program": []}

    while current_token:
        decl_node, index, current_token = parse_declaration(tokens, index, current_token)

        if isinstance(decl_node, dict) and "SyntaxError" in decl_node:
            return decl_node, index, current_token

        program_node["Program"].append(decl_node)

    return program_node, index, current_token

def parse_declaration(tokens, index, current_token):
    line_num = current_token[1]

    # Parse the type (int, bool, string, void, etc.)
    type_node, index, current_token = parse_type(tokens, index, current_token)

    # Expect an identifier next
    if not lookahead(current_token, "T_Identifier"):
        return syntax_error(tokens, index, "syntax error"), index, current_token

    id_node = make_identifier_node(current_token)
    index, current_token = advance(tokens, index)

    # Lookahead to distinguish between function and variable declaration
    if lookahead(current_token, "'('"):
        index, current_token = advance(tokens, index)  # consume '('

        formals, index, current_token = parse_formals(tokens, index, current_token)
        if isinstance(formals, dict) and "SyntaxError" in formals:
            return formals, index, current_token


        if lookahead(current_token, "')'"):
            index, current_token = advance(tokens, index)  # consume ')'
        else:
            return syntax_error(tokens, index, "syntax error"), index, current_token

        # Expect function body to follow
        if not lookahead(current_token, "'{'"):
            return syntax_error(tokens, index, "syntax error"), index, current_token

        body_node, index, current_token = parse_statement_block(tokens, index, current_token)

        if isinstance(body_node, dict) and "SyntaxError" in body_node:
            return body_node, index, current_token  # 🔴 Stop early on block parse error

        return {
            "FnDecl": {
                "line_num": line_num,
                "type": type_node,
                "identifier": id_node,
                "formals": formals,
                "body": body_node
            }
        }, index, current_token

    elif lookahead(current_token, "';'"):
        # This is a variable declaration
        index, current_token = advance(tokens, index)  # consume ';'
        return {
            "VarDecl": {
                "line_num": line_num,
                "type": type_node,
                "identifier": id_node
            }
        }, index, current_token

    else:
        return syntax_error(tokens, index, "syntax error"), index, current_token

def parse_formals(tokens, index, current_token):
    formals = []

    if lookahead(current_token, "')'"):
        return formals, index, current_token

    while True:
        if current_token[4] not in ("T_Int", "T_Bool", "T_String", "T_Double"):
            return syntax_error(tokens, index, "syntax error"), index, current_token


        type_node, index, current_token = parse_type(tokens, index, current_token)

        # Expect an identifier after type
        if not lookahead(current_token, "T_Identifier"):
            return syntax_error(tokens, index, "syntax error"), index, current_token

        id_node = make_identifier_node(current_token)
        index, current_token = advance(tokens, index)

        formals.append({
            "VarDecl": {
                "line_num": id_node["Identifier"]["line_num"],
                "type": type_node,
                "identifier": id_node
            }
        })

        if lookahead(current_token, "','"):
            index, current_token = advance(tokens, index)
        else:
            break

    return formals, index, current_token

def parse_statement_block(tokens, index, current_token):
    line_num = current_token[1]
    index, current_token = advance(tokens, index)  # consume '{'
    statements = []
    prev_index = -1

    while current_token and not lookahead(current_token, "'}'"):
        if index == prev_index:
            # Prevent infinite loop
            index, current_token = advance(tokens, index)
            continue

        prev_index = index
        stmt_node, index, current_token = parse_statement(tokens, index, current_token)

        if isinstance(stmt_node, dict) and "SyntaxError" in stmt_node:
            # Stop parsing the block entirely on first syntax error
            return stmt_node, index, current_token

        statements.append(stmt_node)

    if lookahead(current_token, "'}'"):
        index, current_token = advance(tokens, index)
    else:
        return syntax_error(tokens, index, "syntax error"), index, current_token

    return {"StmtBlock": statements}, index, current_token

def parse_statement(tokens, index, current_token):

    if not current_token or not current_token[0].strip():
        index, current_token = advance(tokens, index)
        return parse_statement(tokens, index, current_token)

    if lookahead(current_token, "'{'"):
        return parse_statement_block(tokens, index, current_token)

    if lookahead(current_token, "T_Else"):
        return syntax_error(tokens, index, "syntax error", token_override=current_token, underline=True), index, current_token

    if lookahead(current_token, "T_Print"):
        return parse_print_statement(tokens, index, current_token)

    if lookahead(current_token, "T_Return"):
        return parse_return_statement(tokens, index, current_token)

    if lookahead(current_token, "T_Int") or \
       lookahead(current_token, "T_Double") or \
       lookahead(current_token, "T_Bool") or \
       lookahead(current_token, "T_String"):
        return parse_variable_declaration(tokens, index, current_token)

    if lookahead(current_token, "T_While"):
        return parse_while_statement(tokens, index, current_token)

    if lookahead(current_token, "T_For"):
        return parse_for_statement(tokens, index, current_token)

    if lookahead(current_token, "T_If"):

        return parse_if_statement(tokens, index, current_token)

    if lookahead(current_token, "T_Break"):
        return parse_break_statement(tokens, index, current_token)

    if lookahead(current_token, "T_Identifier"):
        next_token = tokens[index + 1] if index + 1 < len(tokens) else None

        if next_token and next_token[4] == "'='":
            stmt_node, index, current_token = parse_assignment(tokens, index, current_token, require_semicolon=True)
            return stmt_node, index, current_token

        elif next_token and next_token[4] == "'('":
            call_node, index, current_token = parse_call(tokens, index, current_token)
            if not lookahead(current_token, "';'"):
                return syntax_error(tokens, index, "syntax error"), index, current_token
            index, current_token = advance(tokens, index)
            return call_node, index, current_token

    # Fallback: try parsing as expression statement (e.g., `a;`)
    expr_stmt, new_index, new_token = parse_expression_statement(tokens, index, current_token)
    if isinstance(expr_stmt, dict) and "SyntaxError" not in expr_stmt:
        return expr_stmt, new_index, new_token

    return syntax_error(tokens, index, "syntax error"), index, current_token

def parse_assignment(tokens, index, current_token, require_semicolon=True):
    line_num = current_token[1]
    target_token = current_token
    index, current_token = advance(tokens, index)

    if not lookahead(current_token, "'='"):
        return syntax_error(tokens, index, "syntax error"), index, current_token
    index, current_token = advance(tokens, index)  # consume '='

    # Use full expression parser for RHS
    expr_node, index, current_token = parse_expression(tokens, index, current_token)
    if isinstance(expr_node, dict) and "SyntaxError" in expr_node:
        return expr_node, index, current_token

    if require_semicolon:
        if not lookahead(current_token, "';'"):
            return syntax_error(tokens, index, "syntax error"), index, current_token
        index, current_token = advance(tokens, index)


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
        return syntax_error(tokens, index, "syntax error"), index, current_token
    id_token = current_token
    index, current_token = advance(tokens, index)

    # Defensive check: only a semicolon is valid after VarDecl
    if not lookahead(current_token, "';'"):
        return syntax_error(tokens, index, "syntax error"), index, current_token

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

    if lookahead(current_token, "';'"):
        index, current_token = advance(tokens, index)
        return {
            "ReturnStmt": {
                "line_num": line_num,
                "expr": {"Empty": True}
            }
        }, index, current_token

    # ✅ Case: return with expression
    expr_node, index, current_token = parse_expression(tokens, index, current_token)

    if not lookahead(current_token, "';'"):
        return syntax_error(tokens, index, "syntax error"), index, current_token

    index, current_token = advance(tokens, index)
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
        return syntax_error(tokens, index, "syntax error"), index, current_token
    index, current_token = advance(tokens, index)

    args = []
    if not lookahead(current_token, "')'"):
        while True:
            expr, index, current_token = parse_expression(tokens, index, current_token)
            if isinstance(expr, dict) and "SyntaxError" in expr:
                return expr, index, current_token

            args.append(expr)

            if lookahead(current_token, "')'"):
                break
            if not lookahead(current_token, "','"):
                return syntax_error(tokens, index, "syntax error"), index, current_token
            index, current_token = advance(tokens, index)  # consume ','


    if not lookahead(current_token, "')'"):
        return syntax_error(tokens, index, "syntax error"), index, current_token

    index, current_token = advance(tokens, index)  # consume ')'
    if not lookahead(current_token, "';'"):
        return syntax_error(tokens, index, "syntax error"), index, current_token

    index, current_token = advance(tokens, index)  # consume ';'

    return {
        "PrintStmt": {
            "line_num": line_num,
            "args": args
        }
    }, index, current_token

def parse_call(tokens, index, current_token):
    line_num = current_token[1]
    function_token = current_token
    index, current_token = advance(tokens, index)  # consume function identifier

    if not lookahead(current_token, "'('"):
        return syntax_error(tokens, index, "syntax error"), index, current_token
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
                return syntax_error(tokens, index, "syntax error"), index, current_token

    index, current_token = advance(tokens, index)  # consume ')'

    node = {
        "Call": {
            "line_num": line_num,
            "identifier": function_token[0],
            "actuals": actuals
        }
    }

    return node, index, current_token

def parse_while_statement(tokens, index, current_token):
    line_num = current_token[1]
    index, current_token = advance(tokens, index)  # consume 'while'

    # Expect '('
    if not lookahead(current_token, "'('"):
        return syntax_error(tokens, index, "syntax error: expected '(' after 'while'"), index, current_token
    index, current_token = advance(tokens, index)  # consume '('

    # Parse the condition expression
    test_expr, index, current_token = parse_expression(tokens, index, current_token)
    if isinstance(test_expr, dict) and "SyntaxError" in test_expr:
        return test_expr, index, current_token

    # Expect ')'
    if not lookahead(current_token, "')'"):
        return syntax_error(tokens, index, "syntax error: expected ')'"), index, current_token
    index, current_token = advance(tokens, index)  # consume ')'

    # Now check if the next token is '{' (block) or not (single statement)
    if lookahead(current_token, "'{'"):
        body_node, index, current_token = parse_statement_block(tokens, index, current_token)
        if isinstance(body_node, dict) and "SyntaxError" in body_node:
            return body_node, index, current_token
    else:
        single_stmt, index, current_token = parse_statement(tokens, index, current_token)
        if isinstance(single_stmt, dict) and "SyntaxError" in single_stmt:
            return single_stmt, index, current_token
        # Wrap the single statement in a small block node
        body_node = {
            "StmtBlock": [single_stmt]
        }

    node = {
        "WhileStmt": {
            "line_num": line_num,
            "test": test_expr,
            "body": body_node
        }
    }
    return node, index, current_token

def parse_if_statement(tokens, index, current_token):

    line_num = current_token[1]
    index, current_token = advance(tokens, index)  # consume 'if'

    if not lookahead(current_token, "'('"):
        return syntax_error(tokens, index, "syntax error"), index, current_token
    index, current_token = advance(tokens, index)

    test_expr, index, current_token = parse_expression(tokens, index, current_token)

    if not lookahead(current_token, "')'"):
        return syntax_error(tokens, index, "syntax error"), index, current_token
    index, current_token = advance(tokens, index)

    start_index = index
    then_stmt, index, current_token = parse_statement(tokens, index, current_token)

    if index == start_index:
        return syntax_error(tokens, index, "syntax error"), index, current_token

    # Check for optional else
    else_stmt = None
    if lookahead(current_token, "T_Else"):
        else_token = current_token  # Save the 'else' token before consuming
        index, current_token = advance(tokens, index)
        else_start_index = index
        else_stmt, index, current_token = parse_statement(tokens, index, current_token)
        if index == else_start_index:
            return syntax_error(tokens, index, "syntax error", line_num=else_token[1], token_override=else_token), index, current_token

    node = {
        "IfStmt": {
            "line_num": line_num,
            "test": test_expr,
            "then": then_stmt
        }
    }

    if else_stmt:
        node["IfStmt"]["else"] = else_stmt

    return node, index, current_token

def parse_break_statement(tokens, index, current_token):
    line_num = current_token[1]
    index, current_token = advance(tokens, index)  # consume 'break'

    if not lookahead(current_token, "';'"):
        return syntax_error(tokens, index, "syntax error"), index, current_token
    index, current_token = advance(tokens, index)

    return {
        "BreakStmt": {
            "line_num": line_num
        }
    }, index, current_token

def parse_for_step_statement(tokens, index, current_token):
    # This handles expressions like: a = a + 1 (no semicolon)
    if lookahead(current_token, "T_Identifier"):
        next_token = tokens[index + 1] if index + 1 < len(tokens) else None
        if next_token and next_token[4] == "'='":
            return parse_assignment(tokens, index, current_token, require_semicolon=False)

    # fallback to expression
    return parse_expression(tokens, index, current_token)

def parse_for_statement(tokens, index, current_token):
    line_num = current_token[1]
    index, current_token = advance(tokens, index)  # consume 'for'

    # Expect '('
    if not lookahead(current_token, "'('"):
        return syntax_error(tokens, index, "syntax error: expected '(' after 'for'"), index, current_token
    index, current_token = advance(tokens, index)  # consume '('

    # Parse (init)
    if lookahead(current_token, "';'"):
        init = {"Empty": True}
        index, current_token = advance(tokens, index)  # consume ';'
    else:
        init, index, current_token = parse_statement(tokens, index, current_token)
        if isinstance(init, dict) and "SyntaxError" in init:
            return init, index, current_token

    # Parse (test)
    if lookahead(current_token, "';'"):
        test = {"Empty": True}
        index, current_token = advance(tokens, index)  # consume ';'
    else:
        test, index, current_token = parse_expression(tokens, index, current_token)
        if isinstance(test, dict) and "SyntaxError" in test:
            return test, index, current_token
        if not lookahead(current_token, "';'"):
            return syntax_error(tokens, index, "syntax error: expected ';' after test"), index, current_token
        index, current_token = advance(tokens, index)  # consume ';'

    # Parse (step)
    if lookahead(current_token, "')'"):
        step = {"Empty": True}
    else:
        step, index, current_token = parse_for_step_statement(tokens, index, current_token)
        if isinstance(step, dict) and "SyntaxError" in step:
            return step, index, current_token

    # Expect ')'
    if not lookahead(current_token, "')'"):
        return syntax_error(tokens, index, "syntax error: expected ')' after for clauses"), index, current_token
    index, current_token = advance(tokens, index)  # consume ')'

    # Now check if the next token is '{' (block) or not
    if lookahead(current_token, "'{'"):
        body_node, index, current_token = parse_statement_block(tokens, index, current_token)
        if isinstance(body_node, dict) and "SyntaxError" in body_node:
            return body_node, index, current_token
    else:
        single_stmt, index, current_token = parse_statement(tokens, index, current_token)
        if isinstance(single_stmt, dict) and "SyntaxError" in single_stmt:
            return single_stmt, index, current_token
        body_node = {
            "StmtBlock": [single_stmt]
        }

    node = {
        "ForStmt": {
            "line_num": line_num,
            "init": init,
            "test": test,
            "step": step,
            "body": body_node
        }
    }
    return node, index, current_token

def parse_expression(tokens, index, current_token):
    return parse_logical_expr(tokens, index, current_token)

def parse_expression_statement(tokens, index, current_token):

    expr_node, index, current_token = parse_expression(tokens, index, current_token)

    if isinstance(expr_node, dict) and "SyntaxError" in expr_node:
        return expr_node, index, current_token

    if not lookahead(current_token, "';'"):
        return syntax_error(tokens, index, "missing semicolon after expression"), index, current_token

    index, current_token = advance(tokens, index)  # ✅ consume ';'

    return expr_node, index, current_token

def parse_logical_expr(tokens, index, current_token):
    left, index, current_token = parse_equality_expr(tokens, index, current_token)

    while current_token and current_token[0] in ('&&', '||'):
        op_token = current_token
        index, current_token = advance(tokens, index)
        right, index, current_token = parse_logical_expr(tokens, index, current_token)
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
    left, index, current_token = parse_primary(tokens, index, current_token)

    while current_token and current_token[0] in precedence and precedence[current_token[0]] >= min_prec:
        op_token = current_token
        op_prec = precedence[op_token[0]]
        index, current_token = advance(tokens, index)
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
    if lookahead(current_token, "'('"):
        index, current_token = advance(tokens, index)
        expr_node, index, current_token = parse_expression(tokens, index, current_token)
        if not lookahead(current_token, "')'"):
            return syntax_error(tokens, index, "syntax error"), index, current_token
        index, current_token = advance(tokens, index)
        return expr_node, index, current_token

    return parse_expression_leaf(tokens, index, current_token)

def parse_expression_leaf(tokens, index, current_token):
    line_num = current_token[1]

    if lookahead(current_token, "'-'"):
        operator_token = current_token
        index, current_token = advance(tokens, index)
        right_expr, index, current_token = parse_expression(tokens, index, current_token)
        result = {
            "ArithmeticExpr": {
                "line_num": line_num,
                "operator": "-",
                "left": {
                    "IntConstant": {
                        "line_num": line_num,
                        "value": "0"
                    }
                },
                "right": right_expr
            }
        }
        return result, index, current_token

    if lookahead(current_token, "'!'"):
        operator_token = current_token
        index, current_token = advance(tokens, index)
        right_expr, index, current_token = parse_expression(tokens, index, current_token)
        result = {
            "LogicalExpr": {
                "line_num": line_num,
                "operator": operator_token[0],
                "right": right_expr
            }
        }
        return result, index, current_token

    if lookahead(current_token, "T_ReadInteger"):
        index, current_token = advance(tokens, index)
        if not lookahead(current_token, "'('"):
            return syntax_error(tokens, index, "syntax error"), index, current_token
        index, current_token = advance(tokens, index)
        if not lookahead(current_token, "')'"):
            return syntax_error(tokens, index, "syntax error"), index, current_token
        index, current_token = advance(tokens, index)
        node = {
            "ReadIntegerExpr": {
                "line_num": line_num
            }
        }
        return node, index, current_token
    
    if lookahead(current_token, "T_ReadLine"):
        index, current_token = advance(tokens, index)
        if not lookahead(current_token, "'('"):
            return syntax_error(tokens, index, "syntax error"), index, current_token
        index, current_token = advance(tokens, index)
        if not lookahead(current_token, "')'"):
            return syntax_error(tokens, index, "syntax error"), index, current_token
        index, current_token = advance(tokens, index)
        node = {
            "ReadLine": {
                "line_num": line_num
            }
        }
        return node, index, current_token

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

    return syntax_error(tokens, index, "syntax error"), index, current_token
