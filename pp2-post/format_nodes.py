from helper_functions import custom_line_prefix, format_type

def format_program(node, level=0):

    lines = []
    prefix = custom_line_prefix('', level)
    # Add a space after the colon
    lines.append(f"{prefix}Program: ")

    # Print each child at level+1
    for child in node['Program']:
        lines.extend(format_node(child, level + 1))

    return lines


def format_function_declaration(node, level=0):

    lines = []
    fn = node['FnDecl']
    line_num = fn.get('line_num', '')

    # "FnDecl:"
    prefix_fn = custom_line_prefix(line_num, level)
    lines.append(f"{prefix_fn}FnDecl: ")

    # Return type
    prefix_type = custom_line_prefix('', level + 1)
    lines.append(f"{prefix_type}(return type) Type: {format_type(fn['type'])}")

    # Identifier
    ident_line = fn["identifier"]["Identifier"].get("line_num", '')
    ident_name = fn["identifier"]["Identifier"]["name"]
    prefix_ident = custom_line_prefix(line_num, level + 1)
    lines.append(f"{prefix_ident}Identifier: {ident_name}")

    # Formals
    if fn.get("formals"):
        for formal in fn["formals"]:
            lines.extend(format_formal_declaration(formal, line_num, level + 1))

    # Body
    prefix_body = custom_line_prefix('', level + 1)
    lines.append(f"{prefix_body}(body) StmtBlock: ")
    lines.extend(format_node(fn['body'], level + 2))

    return lines


def format_formal_declaration(formal_node, func_line_num, level):

    lines = []
    var = formal_node["VarDecl"]

    # (formals) VarDecl:  -> same line number as function
    prefix_formals = custom_line_prefix(func_line_num, level)
    lines.append(f"{prefix_formals}(formals) VarDecl: ")

    # Type:
    type_str = format_type(var['type'])
    prefix_type = custom_line_prefix('', level + 1)
    lines.append(f"{prefix_type}Type: {type_str}")

    # Identifier:
    if isinstance(var['identifier'], dict) and 'Identifier' in var['identifier']:
        ident_line = var['identifier']['Identifier']['line_num']
        ident_name = var['identifier']['Identifier']['name']
    else:
        ident_line = func_line_num
        ident_name = str(var['identifier'])

    prefix_ident = custom_line_prefix(func_line_num, level + 1)
    lines.append(f"{prefix_ident}Identifier: {ident_name}")

    return lines


def format_variable_declaration(node, level=0):

    lines = []
    var = node['VarDecl']
    line_num = var.get('line_num', '')

    prefix = custom_line_prefix(line_num, level)
    lines.append(f"{prefix}VarDecl: ")

    prefix_type = custom_line_prefix('', level + 1)
    type_str = format_type(var['type'])
    lines.append(f"{prefix_type}Type: {type_str}")

    ident_prefix = custom_line_prefix(line_num, level + 1)
    if isinstance(var['identifier'], dict) and 'Identifier' in var['identifier']:
        ident_name = var['identifier']['Identifier']['name']
    else:
        ident_name = str(var['identifier'])
    lines.append(f"{ident_prefix}Identifier: {ident_name}")

    return lines


def format_statement_block(node, level=0):

    lines = []
    stmts = node['StmtBlock']
    for stmt in stmts:
        lines.extend(format_node(stmt, level))
    return lines


def format_print_statement(node, level=0):

    lines = []
    stmt = node['PrintStmt']
    line_num = stmt.get('line_num', '')

    prefix = custom_line_prefix(line_num, level)
    lines.append(f"{prefix}PrintStmt: ")

    for arg in stmt['args']:
        # If it's a string
        if 'StringConstant' in arg:
            arg_prefix = custom_line_prefix(line_num, level + 1)
            val = arg['StringConstant']['value']
            lines.append(f"{arg_prefix}(args) StringConstant: {val}")
        else:
            # e.g. FieldAccess, Call, etc.
            arg_prefix = custom_line_prefix(line_num, level + 1)
            # If it's a Call node, we might do directly "(args) Call: "
            if 'Call' in arg:
                lines.append(f"{arg_prefix}(args) Call: ")
                lines.extend(format_node(arg, level + 2))
            else:
                lines.append(f"{arg_prefix}(args)")
                lines.extend(format_node(arg, level + 2))

    return lines


def format_call(node, level=0):

    lines = []
    call = node['Call']
    line_num = call.get('line_num', '')

    # If the parent calls us with "(args) Call:", we only show children here.
    # But if we come from somewhere else, we can do:
    prefix = custom_line_prefix(line_num, level)
    lines.append(f"{prefix}Identifier: {call['identifier']}")

    if call["actuals"]:
        prefix_act = custom_line_prefix(line_num, level)
        lines.append(f"{prefix_act}(actuals) ")
        for actual in call['actuals']:
            lines.extend(format_node(actual, level + 1))

    return lines


def format_assignment_expression(node, level=0):
 
    lines = []
    expr = node['AssignExpr']
    line_num = expr.get('line_num', '')

    prefix = custom_line_prefix(line_num, level)
    lines.append(f"{prefix}AssignExpr: ")

    # target
    lines.extend(format_node(expr['target'], level + 1))

    # Operator
    op_prefix = custom_line_prefix(line_num, level + 1)
    lines.append(f"{op_prefix}Operator: {expr['operator']}")

    # value
    lines.extend(format_node(expr['value'], level + 1))

    return lines


def format_return_statement(node, level=0):

    lines = []
    stmt = node['ReturnStmt']
    line_num = stmt.get('line_num', '')

    prefix = custom_line_prefix(line_num, level)
    lines.append(f"{prefix}ReturnStmt: ")

    if stmt['expr'] == {"Empty": True}:
        empty_prefix = custom_line_prefix(line_num, level + 1)
        lines.append(f"{empty_prefix}Empty: ")
    else:
        lines.extend(format_node(stmt['expr'], level + 1))

    return lines


def format_arithmetic_expression(node, level=0):

    lines = []
    expr = node['ArithmeticExpr']
    line_num = expr.get('line_num', '')

    prefix = custom_line_prefix(line_num, level)
    lines.append(f"{prefix}ArithmeticExpr: ")

    lines.extend(format_node(expr['left'], level + 1))

    op_prefix = custom_line_prefix(line_num, level + 1)
    lines.append(f"{op_prefix}Operator: {expr['operator']}")

    lines.extend(format_node(expr['right'], level + 1))

    return lines


def format_field_access(node, level=0):

    lines = []
    fa = node['FieldAccess']
    line_num = fa.get('line_num', '')

    prefix = custom_line_prefix(line_num, level)
    lines.append(f"{prefix}FieldAccess: ")

    ident_prefix = custom_line_prefix(line_num, level + 1)
    lines.append(f"{ident_prefix}Identifier: {fa['identifier']}")

    return lines


def format_read_integer_expr(node, level=0):

    lines = []
    expr = node['ReadIntegerExpr']
    line_num = expr.get('line_num', '')

    prefix = custom_line_prefix(line_num, level)
    lines.append(f"{prefix}ReadIntegerExpr: ")
    return lines


def format_logical_expression(node, level=0):

    lines = []
    expr = node['LogicalExpr']
    line_num = expr.get('line_num', '')

    prefix = custom_line_prefix(line_num, level)
    lines.append(f"{prefix}LogicalExpr: ")

    if 'left' in expr and 'right' in expr:
        lines.extend(format_node(expr['left'], level + 1))
        op_prefix = custom_line_prefix(line_num, level + 1)
        lines.append(f"{op_prefix}Operator: {expr['operator']}")
        lines.extend(format_node(expr['right'], level + 1))
    elif 'right' in expr:
        op_prefix = custom_line_prefix(line_num, level + 1)
        lines.append(f"{op_prefix}Operator: {expr['operator']}")
        lines.extend(format_node(expr['right'], level + 1))
    else:
        malformed_prefix = custom_line_prefix(line_num, level + 1)
        lines.append(f"{malformed_prefix}(Malformed LogicalExpr)")

    return lines


def format_equality_expression(node, level=0):

    lines = []
    expr = node['EqualityExpr']
    line_num = expr.get('line_num', '')

    prefix = custom_line_prefix(line_num, level)
    lines.append(f"{prefix}EqualityExpr: ")

    lines.extend(format_node(expr['left'], level + 1))
    op_prefix = custom_line_prefix(line_num, level + 1)
    lines.append(f"{op_prefix}Operator: {expr['operator']}")
    lines.extend(format_node(expr['right'], level + 1))

    return lines


def format_relational_expression(node, level=0):

    lines = []
    expr = node['RelationalExpr']
    line_num = expr.get('line_num', '')

    prefix = custom_line_prefix(line_num, level)
    lines.append(f"{prefix}RelationalExpr: ")

    lines.extend(format_node(expr['left'], level + 1))
    op_prefix = custom_line_prefix(line_num, level + 1)
    lines.append(f"{op_prefix}Operator: {expr['operator']}")
    lines.extend(format_node(expr['right'], level + 1))

    return lines


def format_while_statement(node, level=0):
    lines = []
    stmt = node['WhileStmt']
    line_num = stmt.get('line_num', '')

    prefix = custom_line_prefix(line_num, level)
    lines.append(f"{prefix}WhileStmt: ")

    test_prefix = custom_line_prefix('', level + 1)
    lines.append(f"{test_prefix}(test)")
    lines.extend(format_node(stmt['test'], level + 2))

    body_prefix = custom_line_prefix('', level + 1)
    lines.append(f"{body_prefix}(body) StmtBlock: ")
    lines.extend(format_node(stmt['body'], level + 2))

    return lines


def format_if_statement(node, level=0):

    lines = []
    stmt = node['IfStmt']
    line_num = stmt.get('line_num', '')

    prefix = custom_line_prefix(line_num, level)
    lines.append(f"{prefix}IfStmt: ")

    test_prefix = custom_line_prefix('', level + 1)
    lines.append(f"{test_prefix}(test)")
    lines.extend(format_node(stmt['test'], level + 2))

    then_prefix = custom_line_prefix('', level + 1)
    lines.append(f"{then_prefix}(then)")
    lines.extend(format_node(stmt['then'], level + 2))

    if 'else' in stmt:
        else_prefix = custom_line_prefix('', level + 1)
        lines.append(f"{else_prefix}(else)")
        lines.extend(format_node(stmt['else'], level + 2))

    return lines


def format_break_statement(node, level=0):

    lines = []
    brk = node['BreakStmt']
    line_num = brk.get('line_num', '')

    prefix = custom_line_prefix(line_num, level)
    lines.append(f"{prefix}BreakStmt: ")

    return lines


def format_for_statement(node, level=0):

    lines = []
    stmt = node['ForStmt']
    line_num = stmt.get('line_num', '')

    prefix = custom_line_prefix(line_num, level)
    lines.append(f"{prefix}ForStmt: ")

    init_prefix = custom_line_prefix('', level + 1)
    if stmt['init'] == {"Empty": True}:
        lines.append(f"{init_prefix}(init) Empty: ")
    else:
        lines.append(f"{init_prefix}(init)")
        lines.extend(format_node(stmt['init'], level + 2))

    test_prefix = custom_line_prefix('', level + 1)
    if stmt['test'] == {"Empty": True}:
        lines.append(f"{test_prefix}(test) Empty: ")
    else:
        lines.append(f"{test_prefix}(test)")
        lines.extend(format_node(stmt['test'], level + 2))

    step_prefix = custom_line_prefix('', level + 1)
    if stmt['step'] == {"Empty": True}:
        lines.append(f"{step_prefix}(step) Empty: ")
    else:
        lines.append(f"{step_prefix}(step)")
        lines.extend(format_node(stmt['step'], level + 2))

    body_prefix = custom_line_prefix('', level + 1)
    lines.append(f"{body_prefix}(body) StmtBlock: ")
    lines.extend(format_node(stmt['body'], level + 2))

    return lines


def format_string_constant(node, level=0):
    const = node['StringConstant']
    line_num = const.get('line_num', '')

    prefix = custom_line_prefix(line_num, level)
    lines = [f"{prefix}StringConstant: {const['value']}"]
    return lines


def format_int_constant(node, level=0):
    val = node['IntConstant']
    line_num = val.get('line_num', '')

    prefix = custom_line_prefix(line_num, level)
    lines = [f"{prefix}IntConstant: {val['value']}"]
    return lines


def format_double_constant(node, level=0):
    val = node['DoubleConstant']
    line_num = val.get('line_num', '')

    prefix = custom_line_prefix(line_num, level)
    lines = [f"{prefix}DoubleConstant: {val['value']}"]
    return lines


def format_node(node, level=0):
    """Dispatcher for each node type."""
    if 'Program' in node:
        return format_program(node, level)
    elif 'FnDecl' in node:
        return format_function_declaration(node, level)
    elif 'VarDecl' in node:
        return format_variable_declaration(node, level)
    elif 'StmtBlock' in node:
        return format_statement_block(node, level)
    elif 'PrintStmt' in node:
        return format_print_statement(node, level)
    elif 'ReturnStmt' in node:
        return format_return_statement(node, level)
    elif 'WhileStmt' in node:
        return format_while_statement(node, level)
    elif 'IfStmt' in node:
        return format_if_statement(node, level)
    elif 'ForStmt' in node:
        return format_for_statement(node, level)
    elif 'BreakStmt' in node:
        return format_break_statement(node, level)
    elif 'Call' in node:
        return format_call(node, level)
    elif 'AssignExpr' in node:
        return format_assignment_expression(node, level)
    elif 'ArithmeticExpr' in node:
        return format_arithmetic_expression(node, level)
    elif 'FieldAccess' in node:
        return format_field_access(node, level)
    elif 'LogicalExpr' in node:
        return format_logical_expression(node, level)
    elif 'EqualityExpr' in node:
        return format_equality_expression(node, level)
    elif 'RelationalExpr' in node:
        return format_relational_expression(node, level)
    elif 'IntConstant' in node:
        return format_int_constant(node, level)
    elif 'DoubleConstant' in node:
        return format_double_constant(node, level)
    elif 'ReadIntegerExpr' in node:
        return format_read_integer_expr(node, level)
    elif 'StringConstant' in node:
        return format_string_constant(node, level)
    else:
        return []


def format_ast_string(ast_dict):
    lines = format_node(ast_dict, 0)
    return "\n".join(lines)
