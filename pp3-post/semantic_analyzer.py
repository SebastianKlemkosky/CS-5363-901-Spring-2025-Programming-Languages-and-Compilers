# semantic_analyzer.py
from helper_functions import get_line_content, make_pointer_line, semantic_error, find_operator_token, find_token_on_line, find_test_expr_token


def check_semantics(ast, tokens):
    errors = []
    global_scope = {}

    if "Program" in ast:
        process_program(ast["Program"], tokens, global_scope, errors)

    return errors

def process_program(program_node, tokens, global_scope, errors):
    for decl in program_node:
        if "FnDecl" in decl:
            fn = decl["FnDecl"]
            name = fn["identifier"]["Identifier"]["name"]
            line_num = fn["identifier"]["Identifier"]["line_num"]

            if name in global_scope:
                dummy_token = ("", line_num, 1, 1, "", "")
                errors.append(semantic_error(tokens, dummy_token, f"Function '{name}' is already defined"))
            else:
                global_scope[name] = fn

            process_function(fn, tokens, global_scope, errors)

def process_function(fn, tokens, global_scope, errors):
    local_scope = {}

    for param in fn.get("formals", []):
        if "VarDecl" in param:
            name = param["VarDecl"]["identifier"]["Identifier"]["name"]
            type_str = param["VarDecl"]["type"]["Type"]
            local_scope[name] = type_str

    for stmt in fn["body"].get("StmtBlock", []):
        if "VarDecl" in stmt:
            var = stmt["VarDecl"]
            ident = var["identifier"]
            name = ident["Identifier"]["name"] if isinstance(ident, dict) else ident
            type_obj = var["type"]
            type_str = type_obj["Type"] if isinstance(type_obj, dict) else type_obj
            local_scope[name] = type_str

    print("[debug] local scope =", local_scope)

    # Get expected return type
    expected_return = fn["type"]["Type"] if isinstance(fn["type"], dict) else fn["type"]

    for stmt in fn["body"].get("StmtBlock", []):
        check_expr_types(stmt, local_scope, errors, tokens, inside_loop=False, expected_return=expected_return)

def get_expr_type(expr, scope, errors=None, tokens=None):
    if "FieldAccess" in expr:
        ident = expr["FieldAccess"]["identifier"]
        name = ident["Identifier"]["name"] if isinstance(ident, dict) else ident
        return scope.get(name, "error")

    if "IntConstant" in expr:
        return "int"
    if "DoubleConstant" in expr:
        return "double"
    if "BoolConstant" in expr:
        return "bool"
    if "StringConstant" in expr:
        return "string"

    if "RelationalExpr" in expr:
        left = expr["RelationalExpr"]["left"]
        right = expr["RelationalExpr"]["right"]
        operator = expr["RelationalExpr"]["operator"]
        line_num = expr["RelationalExpr"]["line_num"]

        left_type = get_expr_type(left, scope, errors, tokens)
        right_type = get_expr_type(right, scope, errors, tokens)

        if left_type == right_type and left_type in ("int", "double"):
            return "bool"

        if errors is not None:
            token = find_operator_token(tokens, line_num, operator)
            dummy_token = ("", line_num, token[2], token[3], "", "") if token else ("", line_num, 11, 11, "", "")
            errors.append(semantic_error(tokens, dummy_token, f"Incompatible operands: {left_type} {operator} {right_type}"))
        return "error"

    if "LogicalExpr" in expr:
        op = expr["LogicalExpr"]["operator"]
        line_num = expr["LogicalExpr"]["line_num"]

        if op == "!":  # Unary logical expr
            right = expr["LogicalExpr"]["right"]
            right_type = get_expr_type(right, scope, errors, tokens)

            if right_type == "bool":
                return "bool"

            if errors is not None:
                token = find_operator_token(tokens, line_num, "!")
                dummy_token = ("", line_num, token[2], token[3], "", "") if token else ("", line_num, 6, 6, "", "")
                errors.append(semantic_error(tokens, dummy_token, f"Incompatible operand: ! {right_type}"))
            return "error"

        # Binary logical expr
        left = expr["LogicalExpr"]["left"]
        right = expr["LogicalExpr"]["right"]

        left_type = get_expr_type(left, scope, errors, tokens)
        right_type = get_expr_type(right, scope, errors, tokens)

        if left_type == right_type == "bool":
            return "bool"

        if errors is not None:
            token = find_operator_token(tokens, line_num, op)
            dummy_token = ("", line_num, token[2], token[3], "", "") if token else ("", line_num, 14, 14, "", "")
            errors.append(semantic_error(tokens, dummy_token, f"Incompatible operands: {left_type} {op} {right_type}"))
        return "error"

    if "ArithmeticExpr" in expr:
        left = expr["ArithmeticExpr"]["left"]
        right = expr["ArithmeticExpr"]["right"]
        operator = expr["ArithmeticExpr"]["operator"]
        line_num = expr["ArithmeticExpr"]["line_num"]

        left_type = get_expr_type(left, scope, errors, tokens)
        right_type = get_expr_type(right, scope, errors, tokens)

        print(f"[debug] {left_type} {operator} {right_type} on line {line_num}")

        if "error" in (left_type, right_type):
            return "error"

        if left_type == right_type and left_type in ("int", "double"):
            return left_type

        if errors is not None:
            token = find_operator_token(tokens, line_num, operator)
            dummy_token = ("", line_num, token[2], token[3], "", "") if token else ("", line_num, 14, 14, "", "")
            errors.append(semantic_error(tokens, dummy_token, f"Incompatible operands: {left_type} {operator} {right_type}"))
        return "error"

    return "error"

def check_expr_types(stmt, scope, errors, tokens, inside_loop=False, expected_return=None):
    for key, value in stmt.items():
        if key == "AssignExpr":
            lhs_type = get_expr_type(value["target"], scope, errors, tokens)
            rhs_type = get_expr_type(value["value"], scope, errors, tokens)
            if lhs_type != rhs_type:
                token = find_operator_token(tokens, value["line_num"], "=")
                dummy = token if token else ("", value["line_num"], 5, 5, "", "")
                errors.append(semantic_error(tokens, dummy, f"Incompatible operands: {lhs_type} = {rhs_type}"))

        elif key == "BreakStmt":
            if not inside_loop:
                token = find_token_on_line(tokens, value["line_num"], "T_Break")
                if token:
                    dummy = (token[0], token[1], token[2], token[3], "", "")
                else:
                    dummy = ("", value["line_num"], 3, 8, "", "")
                errors.append(semantic_error(tokens, dummy, "break is only allowed inside a loop"))

        elif "ReturnStmt" in value:
            line_num = value["ReturnStmt"]["line_num"]
            if "value" in value["ReturnStmt"]:
                actual_type = get_expr_type(value["ReturnStmt"]["value"], scope, errors, tokens)
            else:
                actual_type = "void"

            if expected_return and actual_type != expected_return:
                token = find_token_on_line(tokens, line_num, match="T_Return")
                dummy = token if token else ("", line_num, 10, 10, "", "")
                errors.append(semantic_error(tokens, dummy, f"Incompatible return: {actual_type} given, {expected_return} expected"))

        elif key == "IfStmt":
            test_type = get_expr_type(value["test"], scope, errors, tokens)
            if test_type != "bool":
                token = find_test_expr_token(tokens, value["line_num"])
                dummy = token if token else ("", value["line_num"], 6, 6, "", "")
                errors.append(semantic_error(tokens, dummy, "Test expression must have boolean type"))

            check_expr_types(value["then"], scope, errors, tokens, inside_loop, expected_return)
            if "else" in value:
                check_expr_types(value["else"], scope, errors, tokens, inside_loop, expected_return)

        elif key == "ForStmt":
            check_expr_types(value["init"], scope, errors, tokens, inside_loop, expected_return)

            test_type = get_expr_type(value["test"], scope, errors, tokens)
            if test_type != "bool":
                token = find_test_expr_token(tokens, value["line_num"])
                dummy = token if token else ("", value["line_num"], 15, 25, "", "")
                errors.append(semantic_error(tokens, dummy, "Test expression must have boolean type"))

            check_expr_types(value["step"], scope, errors, tokens, inside_loop, expected_return)
            check_expr_types(value["body"], scope, errors, tokens, inside_loop=True, expected_return=expected_return)

        elif key == "StmtBlock":
            for s in value:
                check_expr_types(s, scope, errors, tokens, inside_loop, expected_return)
