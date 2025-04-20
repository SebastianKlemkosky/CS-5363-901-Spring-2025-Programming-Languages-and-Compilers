# semantic_analyzer.py
from helper_functions import (
    semantic_error,
    find_token_on_line,
    get_line_content,
    make_pointer_line,
    push_scope,
    pop_scope,
    initialize_scope_system,
    declare,
    is_declared_in_scope,
    lookup,
    get_declared_type
)

DEBUG = False  # Set to True for debug prints
errors = []  # Global list to accumulate semantic errors
scope_stack = []         # List of dictionaries, one per scope level
scope_names = []         # Optional: human-readable labels

def check_semantics(ast_root, tokens):
    """
    Entry point for semantic analysis.
    Initializes scopes and checks semantic rules.
    """
    global errors
    errors = []

    initialize_scope_system()  

    if "Program" in ast_root:
        check_program(ast_root["Program"], tokens)

    return errors

def check_program(declarations, tokens):
    """
    Processes top-level declarations (global variables and functions).
    """
    for decl in declarations:
        if "VarDecl" in decl:
            check_variable_declaration(decl["VarDecl"], tokens, "global")
        elif "FnDecl" in decl:
            check_function_declaration(decl["FnDecl"], tokens)

def check_variable_declaration(vardecl, tokens, scope_name):
    """
    Validates a variable declaration.
    Adds it to the current scope if not already declared.
    """
    var_name = vardecl["identifier"]
    var_type = vardecl["type"]
    line_num = vardecl["line_num"]

    # Check for duplicate declaration
    if is_declared_in_scope(scope_name, var_name):
        token = find_token_on_line(tokens, line_num, match_text=var_name)
        msg = f"*** Declared identifier '{var_name}' more than once in same scope"
        errors.append(semantic_error(tokens, token, msg))
        return

    # Add to current scope
    declare(scope_name, var_name, var_type)

def check_function_declaration(fndecl, tokens):
    """
    Validates a function declaration and its parameters/body.
    Creates separate scopes for parameters and body.
    """
    fn_name = fndecl["identifier"]["Identifier"]["name"]
    line_num = fndecl["line_num"]

    # Check for duplicate in global scope
    if is_declared_in_scope("global", fn_name):
        token = find_token_on_line(tokens, line_num, match_text=fn_name)
        msg = f"*** Declared identifier '{fn_name}' more than once in same scope"
        errors.append(semantic_error(tokens, token, msg))
        return

    # Declare function in global scope
    declare("global", fn_name, fndecl)

    # Enter parameter scope
    param_scope = push_scope(f"params:{fn_name}")
    for formal in fndecl["formals"]:
        check_variable_declaration(formal["VarDecl"], tokens, param_scope)

    # Enter function body scope
    body_scope = push_scope(f"body:{fn_name}")
    check_statement_block(fndecl["body"], tokens, body_scope)

    pop_scope()  # Exit body scope
    pop_scope()  # Exit param scope

def check_function_call(call_node, tokens, scope_name):
    """
    Checks if a function being called is declared.
    """
    fn_name = call_node["identifier"]
    line_num = call_node["line_num"]

    fn_info = lookup(fn_name)
    if fn_info is None:
        token = find_token_on_line(tokens, line_num, match_text=fn_name)
        errors.append(semantic_error(tokens, token, f"No declaration for Function '{fn_name}' found"))
        return

def check_statement_block(stmtblock, tokens, scope_name):
    """
    Checks all statements and variable declarations inside a block.
    """
    for stmt in stmtblock["StmtBlock"]:
        if "VarDecl" in stmt:
            check_variable_declaration(stmt["VarDecl"], tokens, scope_name)
        else:
            check_statement(stmt, tokens, scope_name)

def check_statement(stmt, tokens, scope_name):
    """
    Dispatches to specific check functions based on statement type.
    Each case is defined, but we are not calling the functions yet.
    """
    if "ReturnStmt" in stmt:
        # check_return_statement(stmt["ReturnStmt"], tokens, scope_name)
        pass

    elif "AssignExpr" in stmt:
        check_assign_expression(stmt["AssignExpr"], tokens, scope_name)
       
    elif "BreakStmt" in stmt:
        # check_break_statement(stmt["BreakStmt"], tokens)
        pass

    elif "IfStmt" in stmt:
        # check_if_statement(stmt["IfStmt"], tokens, scope_name)
        pass

    elif "ForStmt" in stmt:
        # check_for_statement(stmt["ForStmt"], tokens, scope_name)
        pass

    elif "WhileStmt" in stmt:
        # check_while_statement(stmt["WhileStmt"], tokens, scope_name)
        pass

    elif "PrintStmt" in stmt:
        # check_print_statement(stmt["PrintStmt"], tokens, scope_name)
        pass

    elif "Call" in stmt:
        check_function_call(stmt["Call"], tokens, scope_name)


    elif "StmtBlock" in stmt:
        check_statement_block(stmt["StmtBlock"], tokens, scope_name)

def get_expression_type(expr, tokens):
    """
    Determines the type of an expression.
    Starts with constants and variables.
    """
    if "IntConstant" in expr:
        return "int"
    if "DoubleConstant" in expr:
        return "double"
    if "BoolConstant" in expr:
        return "bool"
    if "StringConstant" in expr:
        return "string"
    if "ReadIntegerExpr" in expr:
        return "int"

    if "FieldAccess" in expr:
        var_name = expr["FieldAccess"]["identifier"]
        decl = lookup(var_name)
        if decl is None:
            line_num = expr["FieldAccess"]["line_num"]
            token = find_token_on_line(tokens, line_num, match_text=var_name)
            errors.append(semantic_error(tokens, token, f"No declaration for Variable '{var_name}' found"))
            return "error"
        return get_declared_type(decl)
    
    if "ArithmeticExpr" in expr:
            node = expr["ArithmeticExpr"]
            left_type = get_expression_type(node["left"], tokens)
            right_type = get_expression_type(node["right"], tokens)
            op = node["operator"]
            line_num = node["line_num"]

            # If either side is already an error, propagate the error without further checks
            if left_type == "error" or right_type == "error":
                return "error"

            if left_type != right_type or left_type not in ("int", "double"):
                token = find_token_on_line(tokens, line_num, match_text=op)
                errors.append(semantic_error(tokens, token, f"Incompatible operands: {left_type} {op} {right_type}"))
                return "error"

            return left_type


    return "error"  # fallback if unsupported

def check_assign_expression(assign_node, tokens, scope_name):
    """
    Checks the structure of an assignment and extracts the target variable name.
    """
    line_num = assign_node["line_num"]
    target = assign_node["target"]
    value = assign_node["value"]

    if "FieldAccess" in target:
        var_name = target["FieldAccess"]["identifier"]
        if DEBUG:
            print(f"Assigning to variable: {var_name}")

        var_info = lookup(var_name)
        if var_info is None:
            token = find_token_on_line(tokens, line_num, match_text=var_name)
            errors.append(semantic_error(tokens, token, f"No declaration for Variable '{var_name}' found"))
            return
        
        lhs_type = get_declared_type(var_info)
        rhs_type = get_expression_type(value, tokens)

        if lhs_type != rhs_type and lhs_type != "error" and rhs_type != "error":
            token = find_token_on_line(tokens, line_num, match_text='=')
            errors.append(semantic_error(tokens, token, f"Incompatible operands: {lhs_type} = {rhs_type}"))