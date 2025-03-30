from helper_functions import line_prefix, format_type, aligned_prefix

# Format Print Functions
def format_program(node, indent=0):
    lines = []
    lines.append(f"{aligned_prefix('', 1)}Program:")
    for child in node['Program']:
        lines.extend(format_node(child, indent + 2))
    return lines

def format_function_declaration(node, indent=0):
    lines = []
    spacing = ' ' * indent
    fn = node['FnDecl']
    line_num = fn.get('line_num', '')
    
    lines.append(f"{line_prefix(line_num, indent)}FnDecl:")
    lines.append(f"{line_prefix('', indent + 2)}(return type) Type: {format_type(fn['type'])}")

    # Unwrap identifier
    ident_line = fn["identifier"]["Identifier"]["line_num"]
    ident_name = fn["identifier"]["Identifier"]["name"]
    lines.append(f"{line_prefix(ident_line, indent + 2)}Identifier: {ident_name}")

    # Format formals if present
    if fn["formals"]:
        for formal in fn["formals"]:
            f_line_num = formal["VarDecl"]["line_num"]
            f_type = formal["VarDecl"]["type"]
            f_id = formal["VarDecl"]["identifier"]
            lines.append(f"{line_prefix(line_num, indent + 2)}(formals) VarDecl:")
            lines.append(f"{' ' * (indent + 9)}Type: {f_type}")
            lines.append(f"{line_prefix(f_line_num, indent + 9)}Identifier: {f_id}")

    lines.append(f"{line_prefix('', indent + 2)}(body) StmtBlock:")
    lines.extend(format_node(fn['body'], indent + 6))
    return lines

def format_statement_block(node, indent=0):
    lines = []
    for stmt in node['StmtBlock']:
        lines.extend(format_node(stmt, indent + 3))  # always indent block statements by +3
    return lines

def format_print_statement(node, indent=0):
    lines = []
    stmt = node['PrintStmt']
    line_num = stmt.get('line_num', '')

    lines.append(f"{line_prefix(line_num, indent)}PrintStmt:")

    for arg in stmt['args']:
        if 'StringConstant' in arg:
            string_val = arg['StringConstant']['value']
            lines.append(f"{line_prefix(line_num, indent + 2)}(args) StringConstant: {string_val}")
        else:
            lines.append(f"{line_prefix(line_num, indent + 2)}(args)")
            lines.extend(format_node(arg, indent + 4))

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
    elif 'WhileStmt' in node:
        return format_while_statement(node, indent)
    elif 'IfStmt' in node:
        return format_if_statement(node, indent)
    elif 'ForStmt' in node:
        return format_for_statement(node, indent)
    elif 'BreakStmt' in node:
        return format_break_statement(node, indent)
    elif 'Call' in node:
        return format_call(node, indent)
    elif 'AssignExpr' in node:
        return format_assignment_expression(node, indent)
    elif 'ArithmeticExpr' in node:
        return format_arithmetic_expression(node, indent)
    elif 'FieldAccess' in node:
        return format_field_access(node, indent)
    elif 'LogicalExpr' in node:
        return format_logical_expression(node, indent)
    elif 'EqualityExpr' in node:
        return format_equality_expression(node, indent)
    elif 'RelationalExpr' in node:
        return format_relational_expression(node, indent)
    elif 'IntConstant' in node:
        return format_int_constant(node, indent)
    elif 'DoubleConstant' in node:
        return format_double_constant(node, indent)
    elif 'ReadIntegerExpr' in node:
        return format_read_integer_expr(node, indent)
    elif 'StringConstant' in node:
        return format_string_constant(node, indent)
    else:
        return []

def format_call(node, indent=0):
    lines = []
    call = node['Call']
    line_num = call.get('line_num', '')

    # (args) Call:
    lines.append(f"{line_prefix(line_num, indent)}(args) Call:")
    # Identifier line
    lines.append(f"{line_prefix(line_num, indent + 2)}Identifier: {call['identifier']}")
    
    # (actuals) line
    if call["actuals"]:
        lines.append(f"{line_prefix(line_num, indent + 2)}(actuals)")
        for actual in call['actuals']:
            lines.extend(format_node(actual, indent + 4))

    return lines

def format_string_constant(node, indent=0):
    lines = []
    const = node['StringConstant']
    line_num = const.get('line_num', '')
    lines.append(f"{line_prefix(line_num)}   StringConstant: {const['value']}")
    return lines

def format_int_constant(node, indent=0):
    lines = []
    const = node['IntConstant']
    line_num = const.get('line_num', '')
    lines.append(f"{line_prefix(line_num)}   IntConstant: {const['value']}")
    return lines

def format_double_constant(node, indent=0):
    lines = []
    spacing = ' ' * indent
    const = node['DoubleConstant']
    line_num = const.get('line_num', '')
    lines.append(f"{line_prefix(line_num)}   DoubleConstant: {const['value']}")
    return lines

def format_assignment_expression(node, indent=0):
    lines = []
    spacing = ' ' * indent
    expr = node['AssignExpr']
    line_num = expr.get('line_num', '')
    lines.append(f"{line_prefix(line_num)} AssignExpr:")
    lines.extend(format_node(expr['target'], indent + 6))
    lines.append(f"{line_prefix(line_num)}   Operator: {expr['operator']}")
    lines.extend(format_node(expr['value'], indent + 6))
    return lines

def format_return_statement(node, indent=0):
    lines = []
    stmt = node['ReturnStmt']
    line_num = stmt.get('line_num', '')
    lines.append(f"{line_prefix(line_num)}   ReturnStmt:")

    if stmt['expr'] == {"Empty": True}:
        lines.append(f"{line_prefix(line_num)}      Empty:")
    else:
        lines.extend(format_node(stmt['expr'], indent + 6))

    return lines

def format_arithmetic_expression(node, indent=0):
    lines = []
    spacing = ' ' * indent
    expr = node['ArithmeticExpr']
    line_num = expr.get('line_num', '')
    lines.append(f"{line_prefix(line_num)} ArithmeticExpr:")
    lines.extend(format_node(expr['left'], indent + 6))
    lines.append(f"{line_prefix(line_num)}      Operator: {expr['operator']}")
    lines.extend(format_node(expr['right'], indent + 6))
    return lines

def format_field_access(node, indent=0):
    lines = []
    spacing = ' ' * indent
    fa = node['FieldAccess']
    line_num = fa.get('line_num', '')
    lines.append(f"{line_prefix(line_num)}      FieldAccess:")
    lines.append(f"{line_prefix(line_num)}         Identifier: {fa['identifier']}")
    return lines

def format_variable_declaration(node, indent=0):
    lines = []
    spacing = ' ' * indent
    var = node['VarDecl']
    line_num = var.get('line_num', '')
    lines.append(f"{line_prefix(line_num)} VarDecl: ")
    lines.append(f"{spacing}        Type: {var['type']}")
    lines.append(f"{line_prefix(line_num)}    Identifier: {var['identifier']}")
    return lines

def format_read_integer_expr(node, indent=0):
    lines = []
    expr = node['ReadIntegerExpr']
    line_num = expr.get('line_num', '')
    lines.append(f"{line_prefix(line_num)}   ReadIntegerExpr:")
    return lines

def format_logical_expression(node, indent=0):
    lines = []
    expr = node['LogicalExpr']
    line_num = expr.get('line_num', '')
    lines.append(f"{line_prefix(line_num)}   LogicalExpr:")

    if 'left' in expr and 'right' in expr:
        # Binary expression (e.g., a && b)
        lines.extend(format_node(expr['left'], indent + 6))
        lines.append(f"{line_prefix(line_num)}      Operator: {expr['operator']}")
        lines.extend(format_node(expr['right'], indent + 6))
    elif 'right' in expr:
        # Unary expression (e.g., !true)
        lines.append(f"{line_prefix(line_num)}      Operator: {expr['operator']}")
        lines.extend(format_node(expr['right'], indent + 6))
    else:
        lines.append(f"{line_prefix(line_num)}      (Malformed LogicalExpr)")

    return lines

def format_equality_expression(node, indent=0):
    lines = []
    expr = node['EqualityExpr']
    line_num = expr.get('line_num', '')
    lines.append(f"{line_prefix(line_num)}   EqualityExpr:")
    lines.extend(format_node(expr['left'], indent + 6))
    lines.append(f"{line_prefix(line_num)}      Operator: {expr['operator']}")
    lines.extend(format_node(expr['right'], indent + 6))
    return lines

def format_relational_expression(node, indent=0):
    lines = []
    expr = node['RelationalExpr']
    line_num = expr.get('line_num', '')
    lines.append(f"{line_prefix(line_num)}   RelationalExpr:")
    lines.extend(format_node(expr['left'], indent + 6))
    lines.append(f"{line_prefix(line_num)}      Operator: {expr['operator']}")
    lines.extend(format_node(expr['right'], indent + 6))
    return lines

def format_while_statement(node, indent=0):
    lines = []
    stmt = node['WhileStmt']
    line_num = stmt.get('line_num', '')
    lines.append(f"{line_prefix('')}WhileStmt:")
    lines.append(f"{line_prefix(line_num)}   (test)")
    lines.extend(format_node(stmt['test'], indent + 6))
    lines.append(f"{line_prefix('')}   (body) StmtBlock:")
    lines.extend(format_node(stmt['body'], indent + 6))
    return lines

def format_if_statement(node, indent=0):
    lines = []
    stmt = node['IfStmt']
    line_num = stmt.get('line_num', '')
    lines.append(f"{line_prefix('')}IfStmt:")
    lines.append(f"{line_prefix(line_num)}   (test)")
    lines.extend(format_node(stmt['test'], indent + 6))
    lines.append(f"{line_prefix('')}   (then)")
    lines.extend(format_node(stmt['then'], indent + 6))
    if 'else' in stmt:
        lines.append(f"{line_prefix('')}   (else)")
        lines.extend(format_node(stmt['else'], indent + 6))
    return lines

def format_break_statement(node, indent=0):
    stmt = node['BreakStmt']
    line_num = stmt.get('line_num', '')
    return [f"{line_prefix(line_num)}   BreakStmt:"]

def format_for_statement(node, indent=0):
    lines = []
    stmt = node['ForStmt']
    line_num = stmt.get('line_num', '')
    lines.append(f"{line_prefix('')}ForStmt:")

    if stmt['init'] == {"Empty": True}:
        lines.append(f"{line_prefix(line_num)}   (init) Empty:")
    else:
        lines.append(f"{line_prefix(line_num)}   (init)")
        lines.extend(format_node(stmt['init'], indent + 6))

    if stmt['test'] == {"Empty": True}:
        lines.append(f"{line_prefix(line_num)}   (test) Empty:")
    else:
        lines.append(f"{line_prefix(line_num)}   (test)")
        lines.extend(format_node(stmt['test'], indent + 6))

    if stmt['step'] == {"Empty": True}:
        lines.append(f"{line_prefix(line_num)}   (step) Empty:")
    else:
        lines.append(f"{line_prefix(line_num)}   (step)")
        lines.extend(format_node(stmt['step'], indent + 6))

    lines.append(f"{line_prefix('')}   (body) StmtBlock:")
    lines.extend(format_node(stmt['body'], indent + 6))
    return lines

def format_identifier(node, indent=0):
    id_info = node["Identifier"]
    line = f"{line_prefix(id_info['line_num'], indent)}Identifier: {id_info['name']}"
    return [line]

def format_ast_string(ast_dict):
    lines = format_node(ast_dict)
    return '\n'.join(lines)