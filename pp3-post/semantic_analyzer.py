# semantic_analyzer.py
from helper_functions import get_line_content, make_pointer_line, semantic_error

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

    # Add parameters (if any)
    for param in fn.get("formals", []):
        if "VarDecl" in param:
            name = param["VarDecl"]["identifier"]["Identifier"]["name"]
            type_str = param["VarDecl"]["type"]["Type"]
            local_scope[name] = type_str

    # Add local variable declarations
    for stmt in fn["body"].get("StmtBlock", []):
        if "VarDecl" in stmt:
            var = stmt["VarDecl"]
            ident = var["identifier"]
            name = ident["Identifier"]["name"] if isinstance(ident, dict) else ident
            type_obj = var["type"]
            type_str = type_obj["Type"] if isinstance(type_obj, dict) else type_obj
            local_scope[name] = type_str

    print("[debug] local scope =", local_scope)

    # Check each statement in the function body
    for stmt in fn["body"].get("StmtBlock", []):
        check_expr_types(stmt, local_scope, errors, tokens)

def check_expr_types(node, scope, errors, tokens):
    if isinstance(node, list):
        for child in node:
            check_expr_types(child, scope, errors, tokens)
        return

    if not isinstance(node, dict):
        return

    for key, value in node.items():
        if key == "AssignExpr":
            target = value["target"]
            value_expr = value["value"]
            operator = value["operator"]
            line_num = value["line_num"]

            left_type = get_expr_type(target, scope, errors, tokens)
            right_type = get_expr_type(value_expr, scope, errors, tokens)

            print(f"[debug] {left_type} {operator} {right_type} on line {line_num}")

            # Only report if both sides are valid (not already error from inner expression)
            if operator == "=" and left_type != "error" and right_type != "error" and left_type != right_type:
                dummy_token = ("", line_num, 6, 6, "", "")
                errors.append(semantic_error(tokens, dummy_token, f"Incompatible operands: {left_type} = {right_type}"))

            # Always walk RHS for nested expression analysis
            check_expr_types(value_expr, scope, errors, tokens)

        elif key == "ArithmeticExpr":
            left = value["left"]
            right = value["right"]
            operator = value["operator"]
            line_num = value["line_num"]

            left_type = get_expr_type(left, scope)
            right_type = get_expr_type(right, scope)

            print(f"[debug] {left_type} {operator} {right_type} on line {line_num}")

            if "error" in (left_type, right_type):
                return  # stop here — error already handled in subexpr

            if left_type != right_type or left_type not in ("int", "double"):
                dummy_token = ("", line_num, 12, 12, "", "")
                errors.append(semantic_error(tokens, dummy_token, f"Incompatible operands: {left_type} {operator} {right_type}"))
                return  # don't descend further into invalid tree

            # Recurse into children only if valid
            check_expr_types(left, scope, errors, tokens)
            check_expr_types(right, scope, errors, tokens)


        elif isinstance(value, (dict, list)):
            check_expr_types(value, scope, errors, tokens)

def get_expr_type(expr, scope, errors=None, tokens=None):
    # Handle variables (field access)
    if "FieldAccess" in expr:
        ident = expr["FieldAccess"]["identifier"]
        name = ident["Identifier"]["name"] if isinstance(ident, dict) else ident
        return scope.get(name, "error")

    # Handle constants
    if "IntConstant" in expr:
        return "int"
    if "DoubleConstant" in expr:
        return "double"
    if "BoolConstant" in expr:
        return "bool"
    if "StringConstant" in expr:
        return "string"

    # Handle relational expressions: <, >, <=, >=, ==, !=
    if "RelationalExpr" in expr:
        left = expr["RelationalExpr"]["left"]
        right = expr["RelationalExpr"]["right"]
        operator = expr["RelationalExpr"]["operator"]
        line_num = expr["RelationalExpr"]["line_num"]

        left_type = get_expr_type(left, scope, errors, tokens)
        right_type = get_expr_type(right, scope, errors, tokens)

        if "error" in (left_type, right_type):
            return "error"

        if left_type == right_type and left_type in ("int", "double"):
            return "bool"

        if errors is not None:
            dummy_token = ("", line_num, 11, 11, "", "")
            errors.append(semantic_error(tokens, dummy_token, f"Incompatible operands: {left_type} {operator} {right_type}"))
        return "error"

    # Handle logical expressions: &&, ||
    if "LogicalExpr" in expr:
        left = expr["LogicalExpr"]["left"]
        right = expr["LogicalExpr"]["right"]
        operator = expr["LogicalExpr"]["operator"]
        line_num = expr["LogicalExpr"]["line_num"]

        left_type = get_expr_type(left, scope, errors, tokens)
        right_type = get_expr_type(right, scope, errors, tokens)

        if "error" in (left_type, right_type):
            return "error"

        if left_type == right_type == "bool":
            return "bool"

        if errors is not None:
            dummy_token = ("", line_num, 11, 11, "", "")
            errors.append(semantic_error(tokens, dummy_token, f"Incompatible operands: {left_type} {operator} {right_type}"))
        return "error"

    # Handle arithmetic expressions: +, -, *, /, %
    if "ArithmeticExpr" in expr:
        left = expr["ArithmeticExpr"]["left"]
        right = expr["ArithmeticExpr"]["right"]
        operator = expr["ArithmeticExpr"]["operator"]
        line_num = expr["ArithmeticExpr"]["line_num"]

        left_type = get_expr_type(left, scope, errors, tokens)
        right_type = get_expr_type(right, scope, errors, tokens)

        print(f"[debug] {left_type} {operator} {right_type} on line {line_num}")

        if "error" in (left_type, right_type):
            return "error"  # avoid bubbling the same error again

        if left_type == right_type and left_type in ("int", "double"):
            return left_type

        if errors is not None:
            dummy_token = ("", line_num, 14, 14, "", "")
            errors.append(semantic_error(tokens, dummy_token, f"Incompatible operands: {left_type} {operator} {right_type}"))
        return "error"

    # Default fallback
    return "error"



