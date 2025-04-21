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
    get_declared_type,
    get_token_range_on_line,
    get_token_range_between
)

DEBUG = False  # Set to True for debug prints
errors = []  # Global list to accumulate semantic errors
scope_stack = []         # List of dictionaries, one per scope level
scope_names = []         # Optional: human-readable labels
inside_loop = 0  # Used like a counter
current_return_type = None

def check_semantics(ast_root, tokens):
    global errors
    errors = []
    initialize_scope_system()

    # First pass: declare all functions and global variables
    for decl in ast_root["Program"]:
        if "FnDecl" in decl:
            fn_decl = decl["FnDecl"]
            fn_name = fn_decl["identifier"]["Identifier"]["name"]
            if is_declared_in_scope("global", fn_name):
                token = find_token_on_line(tokens, fn_decl["line_num"], match_text=fn_name)
                msg = f"Declared identifier '{fn_name}' more than once in same scope"
                errors.append(semantic_error(tokens, token, msg, underline=True))
            else:
                declare("global", fn_name, fn_decl)

        elif "VarDecl" in decl:
            var_decl = decl["VarDecl"]
            id_info = var_decl["identifier"]
            if isinstance(id_info, dict) and "Identifier" in id_info:
                var_name = id_info["Identifier"]["name"]
            else:
                var_name = id_info

            if is_declared_in_scope("global", var_name):
                token = find_token_on_line(tokens, var_decl["line_num"], match_text=var_name)
                msg = f"Declared identifier '{var_name}' more than once in same scope"
                errors.append(semantic_error(tokens, token, msg, underline=True))
            else:
                declare("global", var_name, var_decl)

    # Second pass: fully analyze functions
    for decl in ast_root["Program"]:
        if "FnDecl" in decl:
            check_function_declaration(decl["FnDecl"], tokens)

    return errors

def check_program(declarations, tokens):
    """
    Processes top-level declarations (global variables and functions).
    Now supports two-pass processing:
    - Pass 1: Declare all global variables and functions
    - Pass 2: Check contents of functions and variable types
    """
    print("[check_program] 🚀 Starting two-pass declaration processing")

    # Pass 1: Declare global variables and functions
    for decl in declarations:
        if "VarDecl" in decl:
            var_decl = decl["VarDecl"]
            id_info = var_decl["identifier"]
            # Handle both top-level VarDecls and formals
            if isinstance(id_info, dict) and "Identifier" in id_info:
                var_name = id_info["Identifier"]["name"]
            else:
                var_name = id_info

            print(f"[check_program] 🧾 Declaring global variable: {var_name}")

            if is_declared_in_scope("global", var_name):
                token = find_token_on_line(tokens, var_decl["line_num"], match_text=var_name)
                msg = f"*** Declared identifier '{var_name}' more than once in same scope"
                errors.append(semantic_error(tokens, token, msg))
            else:
                declare("global", var_name, var_decl)

        elif "FnDecl" in decl:
            fn_name = decl["FnDecl"]["identifier"]["Identifier"]["name"]
            print(f"[check_program] 🧾 Declaring global function: {fn_name}")
            if is_declared_in_scope("global", fn_name):
                token = find_token_on_line(tokens, decl["FnDecl"]["line_num"], match_text=fn_name)
                msg = f"*** Declared identifier '{fn_name}' more than once in same scope"
                errors.append(semantic_error(tokens, token, msg))
            else:
                declare("global", fn_name, decl["FnDecl"])

    # Pass 2: Perform full semantic checks
    print("[check_program] 🔍 Starting semantic analysis on declarations")
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
    if isinstance(vardecl["identifier"], dict) and "Identifier" in vardecl["identifier"]:
        var_name = vardecl["identifier"]["Identifier"]["name"]
    else:
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

    # Enter parameter scope
    param_scope = push_scope(f"params:{fn_name}")
    for formal in fndecl["formals"]:
        check_variable_declaration(formal["VarDecl"], tokens, param_scope)

    global current_return_type
    current_return_type = get_declared_type(fndecl)


    # Enter function body scope
    body_scope = push_scope(f"body:{fn_name}")
    check_statement_block(fndecl["body"], tokens, body_scope)

    pop_scope()  # Exit body scope
    pop_scope()  # Exit param scope

def check_function_call(call_node, tokens, scope_name):
    """
    Checks if a function being called is declared and validates arguments.
    """
    fn_name = call_node["identifier"]
    actuals = call_node.get("actuals", [])
    line_num = call_node["line_num"]

    fn_info = lookup(fn_name)
    if fn_info is None:
        token = find_token_on_line(tokens, line_num, match_text=fn_name)
        errors.append(semantic_error(tokens, token, f"No declaration for Function '{fn_name}' found"))
        return

    if fn_name == "Print":
        for i, actual_expr in enumerate(actuals, start=1):
            actual_type = get_expression_type(actual_expr, tokens, scope_name)

            if actual_type not in ("int", "bool", "string") and actual_type != "error":
                line = actual_expr.get("line_num", line_num)
                token = None
                match_text = None

                # Try to locate the actual constant or identifier token
                if "DoubleConstant" in actual_expr:
                    match_text = str(actual_expr["DoubleConstant"]["value"])
                    token = find_token_on_line(tokens, line, match_text=match_text)
                elif "IntConstant" in actual_expr:
                    match_text = actual_expr["IntConstant"]["value"]
                    token = find_token_on_line(tokens, line, match_text=match_text)
                elif "BoolConstant" in actual_expr:
                    match_text = actual_expr["BoolConstant"]["value"]
                    token = find_token_on_line(tokens, line, match_text=match_text)
                elif "StringConstant" in actual_expr:
                    match_text = actual_expr["StringConstant"]["value"]
                    token = find_token_on_line(tokens, line, match_text=match_text)
                elif "FieldAccess" in actual_expr:
                    match_text = actual_expr["FieldAccess"]["identifier"]
                    token = find_token_on_line(tokens, line, match_text=match_text)
                else:
                    token = find_token_on_line(tokens, line)

                # Now emit the semantic error under the actual argument
                errors.append(semantic_error(
                    tokens,
                    token,
                    f"Incompatible argument {i}: {actual_type} given, int/bool/string expected",
                    underline=True
                ))



    # Check that the symbol is actually a function
    if not isinstance(fn_info, dict) or "formals" not in fn_info:
        token = find_token_on_line(tokens, line_num, match_text=fn_name)
        errors.append(semantic_error(tokens, token, f"No declaration for Function '{fn_name}' found"))
        return

    formals = fn_info["formals"]
    expected_count = len(formals)
    actual_count = len(actuals)

    # Check for argument count mismatch
    if expected_count != actual_count:
        token = find_token_on_line(tokens, line_num, match_text=fn_name)
        errors.append(semantic_error(tokens, token,
            f"Function '{fn_name}' expects {expected_count} arguments but {actual_count} given", True))
        return  # don't bother type checking if count is wrong

    # Check for argument type mismatches
    for i, (formal, actual_expr) in enumerate(zip(formals, actuals), start=1):
        if "VarDecl" in formal:
            expected_type = get_declared_type(formal["VarDecl"])
        else:
            expected_type = get_declared_type(formal)

        actual_type = get_expression_type(actual_expr, tokens, scope_name)

        if expected_type != actual_type and actual_type != "error":
            # Attempt to find the token that corresponds to the actual expression
            line = actual_expr.get("line_num", line_num)
            token = None

            # Try to find the actual token being passed as the argument
            if "IntConstant" in actual_expr:
                token = find_token_on_line(tokens, line, match_text=actual_expr["IntConstant"]["value"])
            elif "BoolConstant" in actual_expr:
                token = find_token_on_line(tokens, line, match_text=actual_expr["BoolConstant"]["value"])
            elif "DoubleConstant" in actual_expr:
                token = find_token_on_line(tokens, line, match_text=actual_expr["DoubleConstant"]["value"])
            elif "FieldAccess" in actual_expr:
                token = find_token_on_line(tokens, line, match_text=actual_expr["FieldAccess"]["identifier"])
            elif "ArithmeticExpr" in actual_expr or ("operator" in actual_expr and "left" in actual_expr and "right" in actual_expr):
                line = actual_expr.get("line_num", line_num)
                line_tokens = [tok for tok in tokens if tok[1] == line]

                # Use first numeric token as start, last numeric token as end
                start_tok = None
                end_tok = None
                for tok in line_tokens:
                    if tok[4] in ("T_IntConstant", "T_DoubleConstant") and start_tok is None:
                        start_tok = tok
                    if tok[4] in ("T_IntConstant", "T_DoubleConstant"):
                        end_tok = tok

                if start_tok and end_tok:
                    token = ("[ArithmeticExpr]", line, start_tok[2], end_tok[3], None, None)
                else:
                    token = find_token_on_line(tokens, line)

            else:
                token = find_token_on_line(tokens, line)

            # Now use that token for error
            errors.append(semantic_error(tokens, token,
                f"Incompatible argument {i}: {actual_type} given, {expected_type} expected", underline=True))

def check_statement_block(stmtblock, tokens, scope_name):
    """
    Checks all statements and variable declarations inside a block.
    Supports both {"StmtBlock": [...] } and raw [...] list structures.
    """
    if isinstance(stmtblock, dict) and "StmtBlock" in stmtblock:
        block = stmtblock["StmtBlock"]
    else:
        block = stmtblock  # it's already a list

    for stmt in block:
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
        check_return_statement(stmt["ReturnStmt"], tokens, scope_name)
        
    elif "AssignExpr" in stmt:
        check_assign_expression(stmt["AssignExpr"], tokens, scope_name)
       
    elif "BreakStmt" in stmt:
        check_break_statement(stmt["BreakStmt"], tokens)
        
    elif "IfStmt" in stmt:
        check_if_statement(stmt["IfStmt"], tokens, scope_name)
        pass

    elif "ForStmt" in stmt:
        check_for_statement(stmt["ForStmt"], tokens, scope_name)

    elif "WhileStmt" in stmt:
        check_while_statement(stmt["WhileStmt"], tokens, scope_name)
      
    elif "PrintStmt" in stmt:
        #print("📣 Entered PrintStmt block in check_statement()")
        check_print_statement(stmt["PrintStmt"], tokens, scope_name)

    elif "Call" in stmt:
        check_function_call(stmt["Call"], tokens, scope_name)

    elif "StmtBlock" in stmt:
        check_statement_block(stmt["StmtBlock"], tokens, scope_name)
    
    elif "ArithmeticExpr" in stmt:
        get_expression_type(stmt["ArithmeticExpr"], tokens, scope_name)

    elif "LogicalExpr" in stmt:
        get_expression_type(stmt["LogicalExpr"], tokens, scope_name)

    elif "EqualityExpr" in stmt:
        get_expression_type(stmt["EqualityExpr"], tokens, scope_name)

    elif "RelationalExpr" in stmt:
        get_expression_type(stmt["RelationalExpr"], tokens, scope_name)

    elif "Call" in stmt:
        get_expression_type(stmt["Call"], tokens, scope_name)

def get_expression_type(expr, tokens, scope_name):
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
    if "ReadLine" in expr:
        return "string"

    if "FieldAccess" in expr:
        var_name = expr["FieldAccess"]["identifier"]
        decl = lookup(var_name)

        if decl is None:
            line_num = expr["FieldAccess"]["line_num"]
            token = find_token_on_line(tokens, line_num, match_text=var_name)
            errors.append(semantic_error(tokens, token, f"No declaration for Variable '{var_name}' found", underline=True))
            return "error"

        # If it's a function declaration, accessing it like a variable is invalid
        if isinstance(decl, dict) and "formals" in decl:
            line_num = expr["FieldAccess"]["line_num"]
            token = find_token_on_line(tokens, line_num, match_text=var_name)
            errors.append(semantic_error(tokens, token, f"No declaration found for variable '{var_name}'", underline=True))
            return "error"

        return get_declared_type(decl)

    # ArithmeticExpr (wrapped or bare)
    if "ArithmeticExpr" in expr:
        node = expr["ArithmeticExpr"]
    elif "operator" in expr and "left" in expr and "right" in expr:
        if expr["operator"] in ["+", "-", "*", "/", "%"]:
            node = expr
        else:
            node = None
    else:
        node = None

    if node:
        left_type = get_expression_type(node["left"], tokens, scope_name)
        right_type = get_expression_type(node["right"], tokens, scope_name)
        op = node["operator"]
        line_num = node["line_num"]

        if left_type == "error" or right_type == "error":
            return "error"

        if left_type != right_type or left_type not in ("int", "double"):
            token = find_token_on_line(tokens, line_num, match_text=op)
            msg = semantic_error(tokens, token, f"Incompatible operands: {left_type} {op} {right_type}", underline=True)
            errors.append(msg)
            return "error"

        return left_type

    # LogicalExpr (wrapped or bare)
    if "LogicalExpr" in expr:
        node = expr["LogicalExpr"]
    elif "operator" in expr:
        if expr["operator"] in ["&&", "||", "!"]:
            node = expr
        else:
            node = None
    else:
        node = None

    if node and "operator" in node:
        op = node["operator"]
        line_num = node["line_num"]

        if "left" in node:
            left_type = get_expression_type(node["left"], tokens, scope_name)
            right_type = get_expression_type(node["right"], tokens, scope_name)
            if left_type != "bool" or right_type != "bool":
                token = find_token_on_line(tokens, line_num, match_text=op)
                errors.append(semantic_error(tokens, token, f"Incompatible operands: {left_type} {op} {right_type}", underline=True))
                return "error"
        else:
            right_type = get_expression_type(node["right"], tokens, scope_name)
            if right_type != "bool":
                token = find_token_on_line(tokens, line_num, match_text=op)
                errors.append(semantic_error(tokens, token, f"Incompatible operand: {op} {right_type}", underline=True))
                return "error"
        return "bool"

    # EqualityExpr (wrapped or bare)
    if "EqualityExpr" in expr:
        node = expr["EqualityExpr"]
    elif "operator" in expr and expr["operator"] in ["==", "!="]:
        node = expr
    else:
        node = None

    if node:
        left_type = get_expression_type(node["left"], tokens, scope_name)
        right_type = get_expression_type(node["right"], tokens, scope_name)
        op = node["operator"]
        line_num = node["line_num"]

        if left_type != right_type:
            token = find_token_on_line(tokens, line_num, match_text=op)
            errors.append(semantic_error(tokens, token, f"Incompatible operands: {left_type} {op} {right_type}", underline=True))
            return "error"

        return "bool"

    # RelationalExpr (wrapped or bare)
    if "RelationalExpr" in expr:
        node = expr["RelationalExpr"]
    elif "operator" in expr and expr["operator"] in ["<", "<=", ">", ">="]:
        node = expr
    else:
        node = None

    if node:
        left_type = get_expression_type(node["left"], tokens, scope_name)
        right_type = get_expression_type(node["right"], tokens, scope_name)
        op = node["operator"]
        line_num = node["line_num"]

        if left_type == "error" or right_type == "error":
            return "error"

        if left_type != right_type or left_type not in ("int", "double"):
            token = find_token_on_line(tokens, line_num, match_text=op)
            errors.append(semantic_error(tokens, token, f"Incompatible operands: {left_type} {op} {right_type}", underline=True))
            return "error"

        return "bool"

    # Function Call
    if "Call" in expr:
        node = expr["Call"]
        check_function_call(node, tokens, scope_name)
        fn_info = lookup(node["identifier"])
        if fn_info and "type" in fn_info:
            return get_declared_type(fn_info["type"])
        return "int"

    return "error"

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
        rhs_type = get_expression_type(value, tokens, scope_name)

        if lhs_type != rhs_type and lhs_type != "error" and rhs_type != "error":
            token = find_token_on_line(tokens, line_num, match_text='=')
            errors.append(semantic_error(tokens, token, f"Incompatible operands: {lhs_type} = {rhs_type}"))

def check_if_statement(if_stmt, tokens, scope_name):
    """
    Checks the condition and both branches of an if statement.
    """
    if "test" in if_stmt:
        test_expr = if_stmt["test"]
        test_type = get_expression_type(test_expr, tokens, scope_name)
        if test_type != "bool" and test_type != "error":
            line_num = test_expr.get("line_num", if_stmt["line_num"])
            start_tok = None
            end_tok = None

            # Get all tokens on this line
            line_tokens = [tok for tok in tokens if tok[1] == line_num]

            # Find the first token after '('
            for i, tok in enumerate(line_tokens):
                if tok[0] == "(" and i + 1 < len(line_tokens):
                    start_tok = line_tokens[i + 1]
                    break

            # Find the last token before ')'
            for i in range(len(line_tokens) - 1, -1, -1):
                if line_tokens[i][0] == ")" and i - 1 >= 0:
                    end_tok = line_tokens[i - 1]
                    break

            # Fallback to a narrower range if needed
            if not start_tok:
                start_tok = find_token_on_line(tokens, line_num)
            if not end_tok:
                end_tok = start_tok

            token = (
                "[if-test-expr]",
                line_num,
                start_tok[2],
                end_tok[3],
                None,
                None,
            )

            errors.append(
                semantic_error(
                    tokens, token, "Test expression must have boolean type", underline=True
                )
            )

    if "then" in if_stmt:
        check_statement(if_stmt["then"], tokens, scope_name)

    if "else" in if_stmt:
        check_statement(if_stmt["else"], tokens, scope_name)

def check_for_statement(for_stmt, tokens, scope_name):
    global inside_loop
    inside_loop += 1

    if "init" in for_stmt and for_stmt["init"] is not None:
        check_statement(for_stmt["init"], tokens, scope_name)

    if "test" in for_stmt and for_stmt["test"] is not None:
        test_expr = for_stmt["test"]
        test_type = get_expression_type(test_expr, tokens, scope_name)
        if test_type != "bool" and test_type != "error":
            line_num = test_expr.get("line_num", for_stmt["line_num"])
            line_tokens = [tok for tok in tokens if tok[1] == line_num]
            start_tok = None
            end_tok = None

            for i, tok in enumerate(line_tokens):
                if tok[0] == ";" and i + 1 < len(line_tokens):
                    start_tok = line_tokens[i + 1]
                    break

            for i in range(len(line_tokens) - 1, -1, -1):
                if line_tokens[i][0] == ";" and i - 1 >= 0:
                    end_tok = line_tokens[i - 1]
                    break

            if not start_tok:
                start_tok = find_token_on_line(tokens, line_num)
            if not end_tok:
                end_tok = start_tok

            token = ("[for-test-expr]", line_num, start_tok[2], end_tok[3], None, None)
            errors.append(semantic_error(tokens, token, "Test expression must have boolean type", underline=True))

    if "step" in for_stmt and for_stmt["step"] is not None:
        check_statement(for_stmt["step"], tokens, scope_name)

    check_statement(for_stmt["body"], tokens, scope_name)
    inside_loop -= 1

def check_while_statement(while_stmt, tokens, scope_name):
    global inside_loop
    inside_loop += 1

    if "test" in while_stmt:
        test_expr = while_stmt["test"]
        test_type = get_expression_type(test_expr, tokens, scope_name)
        if test_type != "bool" and test_type != "error":
            line_num = test_expr.get("line_num", while_stmt["line_num"])
            line_tokens = [tok for tok in tokens if tok[1] == line_num]
            start_tok = None
            end_tok = None

            for i, tok in enumerate(line_tokens):
                if tok[0] == "(" and i + 1 < len(line_tokens):
                    start_tok = line_tokens[i + 1]
                    break

            for i in range(len(line_tokens) - 1, -1, -1):
                if line_tokens[i][0] == ")" and i - 1 >= 0:
                    end_tok = line_tokens[i - 1]
                    break

            if not start_tok:
                start_tok = find_token_on_line(tokens, line_num)
            if not end_tok:
                end_tok = start_tok

            token = ("[while-test-expr]", line_num, start_tok[2], end_tok[3], None, None)
            errors.append(semantic_error(tokens, token, "Test expression must have boolean type", underline=True))

    check_statement(while_stmt["body"], tokens, scope_name)
    inside_loop -= 1

def check_break_statement(break_stmt, tokens):
    """
    Verifies that 'break' is only used inside loops.
    """
    line_num = break_stmt["line_num"]

    if inside_loop == 0:
        token = find_token_on_line(tokens, line_num, match_text="break")
        errors.append(semantic_error(tokens, token, "break is only allowed inside a loop", underline=True))

def check_return_statement(return_stmt, tokens, scope_name):
    global current_return_type
    line_num = return_stmt["line_num"]

    # Get the actual return expression type
    if "expr" in return_stmt and return_stmt["expr"] is not None:
        actual_type = get_expression_type(return_stmt["expr"], tokens, scope_name)
    else:
        actual_type = "void"

    if actual_type != current_return_type and actual_type != "error":
        # Try to find the token for the returned identifier
        expr = return_stmt.get("expr")
        token = None

        if expr and "FieldAccess" in expr:
            var_name = expr["FieldAccess"]["identifier"]
            token = find_token_on_line(tokens, line_num, match_text=var_name)

        # Fallback to 'return' token if we couldn't find the identifier
        if token is None:
            token = find_token_on_line(tokens, line_num, match_text="return")

        errors.append(semantic_error(
            tokens,
            token,
            f"Incompatible return: {actual_type} given, {current_return_type} expected",
            underline=True
        ))

def check_print_statement(print_stmt, tokens, scope_name):
    """
    Checks that all arguments to Print are int, bool, or string.
    """
    line_num = print_stmt["line_num"]
    actuals = print_stmt.get("args", [])

    for i, expr in enumerate(actuals, start=1):
        actual_type = get_expression_type(expr, tokens, scope_name)

        if actual_type not in ("int", "bool", "string") and actual_type != "error":
            line = expr.get("line_num", line_num)
            token = None

            if "DoubleConstant" in expr:
                match_text = expr["DoubleConstant"]["value"]
                token = find_token_on_line(tokens, line, match_text=match_text)
            elif "IntConstant" in expr:
                match_text = expr["IntConstant"]["value"]
                token = find_token_on_line(tokens, line, match_text=match_text)
            elif "BoolConstant" in expr:
                match_text = expr["BoolConstant"]["value"]
                token = find_token_on_line(tokens, line, match_text=match_text)
            elif "StringConstant" in expr:
                match_text = expr["StringConstant"]["value"]
                token = find_token_on_line(tokens, line, match_text=match_text)
            elif "FieldAccess" in expr:
                match_text = expr["FieldAccess"]["identifier"]
                token = find_token_on_line(tokens, line, match_text=match_text)
            elif "Call" in expr:
                match_text = expr["Call"]["identifier"]
                line = expr["Call"]["line_num"]

                # Find start token
                start_tok = find_token_on_line(tokens, line, match_text=match_text)

                # Find all tokens on that line
                line_tokens = [tok for tok in tokens if tok[1] == line]

                # Try to find RPAREN
                end_tok = None
                for tok in line_tokens:
                    if tok[0] == ")":
                        end_tok = tok
                        break

                if start_tok and end_tok:
                    token = (
                        "[CallExpr]",
                        line,
                        start_tok[2],
                        end_tok[3],
                        None,
                        None
                    )
                else:
                    token = start_tok or find_token_on_line(tokens, line, match_text=match_text)



            errors.append(semantic_error(
                tokens,
                token,
                f"Incompatible argument {i}: {actual_type} given, int/bool/string expected",
                underline=True
            ))
