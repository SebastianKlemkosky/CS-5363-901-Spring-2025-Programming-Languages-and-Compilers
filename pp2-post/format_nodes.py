from helper_functions import add_line, insert_label_into_first_line

def format_ast_string(ast_dict):
    #print(ast_dict)
    lines = []
    lines.append("")  # blank line before

    lines.extend(format_node(ast_dict, level=0))

    return "\n".join(lines) 

def format_node(node, level):
    if "Program" in node:
        return format_program(node["Program"], level)
    if "FnDecl" in node:
        return format_function_declaration(node["FnDecl"], level)
    if "VarDecl" in node:
        return format_var_decl(node["VarDecl"], level)
    if "StmtBlock" in node:
        return format_statement_block(node["StmtBlock"], level)
    if "AssignExpr" in node:
        return format_assign_expr(node["AssignExpr"], level)
    if "ReturnStmt" in node:
        return format_return_statement(node["ReturnStmt"], level)
    if "ArithmeticExpr" in node:
        return format_arithmetic_expr(node["ArithmeticExpr"], level)
    if "FieldAccess" in node:
        return format_field_access(node["FieldAccess"], level)
    if "Call" in node:
        return format_call(node["Call"], level)
    if "PrintStmt" in node:
        return format_print_statement(node["PrintStmt"], level)
    if "StringConstant" in node:
        return format_string_constant(node["StringConstant"], level)
    if "IntConstant" in node:
        return format_int_constant(node["IntConstant"], level)
    if "DoubleConstant" in node:
        return format_double_constant(node["DoubleConstant"], level)
    if "BoolConstant" in node:
        return format_bool_constant(node["BoolConstant"], level)
    if "ReadIntegerExpr" in node:
        return format_read_integer_expr(node["ReadIntegerExpr"], level)
    if "LogicalExpr" in node:
        return format_logical_expr(node["LogicalExpr"], level)
    if "EqualityExpr" in node:
        return format_equality_expr(node["EqualityExpr"], level)
    if "RelationalExpr" in node:
        return format_relational_expr(node["RelationalExpr"], level)
    if "WhileStmt" in node:
        return format_while_statement(node["WhileStmt"], level)
    if "IfStmt" in node:
        return format_if_statement(node["IfStmt"], level)
    if "ForStmt" in node:
        return format_for_statement(node["ForStmt"], level)
    if "BreakStmt" in node:
        return format_break_statement(node["BreakStmt"], level)
    return []

def format_program(program_list, level):
    lines = []
    add_line(lines, "", level, "Program:")
    for decl in program_list:
        lines.extend(format_node(decl, level + 1))
    return lines

def format_function_declaration(fn, level):
    lines = []
    line_num = fn.get("line_num", "")
    add_line(lines, line_num, level, "FnDecl:")
    add_line(lines, "", level + 1, f"(return type) Type: {fn['type']['Type']}")

    ident = fn['identifier']['Identifier']
    ident_line = ident.get("line_num", line_num)
    add_line(lines, ident_line, level + 1, f"Identifier: {ident['name']}")

    if fn['formals']:
        for formal in fn['formals']:
            formal_data = formal['VarDecl']
            formal_line = formal_data.get("line_num", line_num)
            add_line(lines, formal_line, level + 1, "(formals) VarDecl:")

            var_type = formal_data["type"]
            if isinstance(var_type, dict) and "Type" in var_type:
                type_str = var_type["Type"]
            else:
                type_str = var_type
            add_line(lines, "", level + 2, f"Type: {type_str}")

            ident = formal_data['identifier']
            if isinstance(ident, dict) and 'Identifier' in ident:
                ident_data = ident['Identifier']
                ident_line = ident_data.get("line_num", formal_line)
                name = ident_data['name']
            else:
                ident_line = formal_line
                name = ident
            add_line(lines, ident_line, level + 2, f"Identifier: {name}")

    add_line(lines, "", level + 1, "(body) StmtBlock:")
    lines.extend(format_node(fn["body"], level + 2))
    return lines

def format_statement_block(stmt_list, level):
    lines = []
    for stmt in stmt_list:
        lines.extend(format_node(stmt, level))
    return lines

def format_print_statement(stmt, level):
    lines = []
    line_num = stmt.get("line_num", "")
    add_line(lines, "", level, "PrintStmt:")
    for arg in stmt["args"]:
        arg_lines = format_node(arg, level + 1)
        insert_label_into_first_line(arg_lines, "(args)", level + 1)
        lines.extend(arg_lines)
    return lines

def format_var_decl(var, level):
    lines = []
    line_num = var.get("line_num", "")
    add_line(lines, line_num, level, "VarDecl:")

    var_type = var.get("type")
    if isinstance(var_type, dict) and "Type" in var_type:
        type_str = var_type["Type"]
    else:
        type_str = var_type

    add_line(lines, "", level + 1, f"Type: {type_str}")

    ident = var['identifier']
    if isinstance(ident, dict) and 'Identifier' in ident:
        ident_data = ident['Identifier']
        ident_line = ident_data.get("line_num", line_num)
        name = ident_data['name']
    else:
        ident_line = line_num
        name = ident

    add_line(lines, ident_line, level + 1, f"Identifier: {name}")
    return lines

def format_return_statement(node, level):
    lines = []
    line_num = node.get("line_num", "")
    add_line(lines, line_num, level, "ReturnStmt:")
    expr = node.get("expr", {})
    if isinstance(expr, dict) and expr.get("Empty", False):
        add_line(lines, "", level + 1, "Empty:")
    else:
        lines.extend(format_node(expr, level + 1))
    return lines

def format_assign_expr(node, level):
    lines = []
    line_num = node.get("line_num", "")
    add_line(lines, line_num, level, "AssignExpr:")
    lines.extend(format_node(node["target"], level + 1))
    add_line(lines, line_num, level + 1, f"Operator: {node['operator']}")
    lines.extend(format_node(node["value"], level + 1))
    return lines

def format_field_access(node, level, label_as_actuals=False, indent_identifier_extra=False, suppress_header=False):
    lines = []
    line_num = node.get("line_num", "")
    if not suppress_header:
        if label_as_actuals:
            add_line(lines, line_num, level, "(actuals) FieldAccess:")
        else:
            add_line(lines, line_num, level, "FieldAccess:")
    ident = node['identifier']
    if isinstance(ident, dict) and 'Identifier' in ident:
        ident_data = ident['Identifier']
        ident_line = ident_data.get("line_num", line_num)
        name = ident_data['name']
    else:
        ident_line = line_num
        name = ident
    if suppress_header:
        add_line(lines, ident_line, level, f"Identifier: {name}", extra_indent=0)
    else:
        add_line(lines, ident_line, level + 1, f"Identifier: {name}", extra_indent=0)
    return lines

def format_call(call, level, line_num=None, suppress_header=False):
    lines = []
    line_num = line_num or call.get("line_num", "")
    if not suppress_header:
        add_line(lines, line_num, level, "Call:")
    add_line(lines, line_num, level + 1, f"Identifier: {call['identifier']}")
    for arg in call["actuals"]:
        for key in arg:
            node_type = key
            if node_type == "FieldAccess":
                add_line(lines, line_num, level + 1, f"(actuals) {node_type}:")
                lines.extend(format_field_access(arg[node_type], level + 2, label_as_actuals=True, suppress_header=True))
            elif node_type == "LogicalExpr":
                add_line(lines, line_num, level + 1, f"(actuals) {node_type}:")
                lines.extend(format_logical_expr(arg[node_type], level + 2, label=False))
            elif node_type == "ArithmeticExpr":
                add_line(lines, line_num, level + 1, f"(actuals) {node_type}:")
                lines.extend(format_arithmetic_expr(arg[node_type], level + 2, label=False))
            elif node_type == "Call":
                add_line(lines, line_num, level + 1, f"(actuals) {node_type}:")
                lines.extend(format_call(arg[node_type], level + 2, suppress_header=True))
            else:
                add_line(lines, line_num, level + 1, f"(actuals) {node_type}:")
                lines.extend(format_node(arg[node_type], level + 2))
    return lines

def format_int_constant(node, level):
    lines = []
    line_num = node.get("line_num", "")
    value = node["value"]
    add_line(lines, line_num, level, f"IntConstant: {value}")
    return lines

def format_double_constant(node, level):
    lines = []
    line_num = node.get("line_num", "")
    value = node["value"]
    add_line(lines, line_num, level, f"DoubleConstant: {value}")
    return lines

def format_string_constant(string_node, level):
    line_num = string_node.get("line_num", "")
    value = string_node.get("value", "")
    if not value.startswith('"'):
        value = '"' + value
    if not value.endswith('"'):
        value = value + '"'
    return [f'{line_num:>3}{" " * (level * 3)}StringConstant: {value}']

def format_bool_constant(node, level):
    lines = []
    line_num = node.get("line_num", "")
    value = str(node["value"]).lower()
    add_line(lines, line_num, level, f"BoolConstant: {value}")
    return lines

def format_read_integer_expr(node, level):
    lines = []
    line_num = node.get("line_num", "")
    add_line(lines, line_num, level, "ReadIntegerExpr:")
    return lines

def format_logical_expr(node, level, label=True):
    lines = []
    line_num = node.get("line_num", "")
    if label:
        add_line(lines, line_num, level, "LogicalExpr:")
        next_level = level + 1
    else:
        next_level = level
    # If there's a "left" child, it's a binary logical expression (e.g., a && b).
    if node.get("left") is not None:
        lines.extend(format_node(node["left"], next_level))
        add_line(lines, line_num, next_level, f"Operator: {node['operator']}")
        lines.extend(format_node(node["right"], next_level))
    else:
        # Unary operator (e.g., ! true)
        add_line(lines, line_num, next_level, f"Operator: {node['operator']}")
        lines.extend(format_node(node["right"], next_level))
    return lines

def format_equality_expr(node, level):
    lines = []
    line_num = node.get("line_num", "")
    add_line(lines, line_num, level, "EqualityExpr:")
    lines.extend(format_node(node["left"], level + 1))
    add_line(lines, line_num, level + 1, f"Operator: {node['operator']}")
    lines.extend(format_node(node["right"], level + 1))
    return lines

def format_relational_expr(node, level):
    lines = []
    line_num = node.get("line_num", "")
    add_line(lines, line_num, level, "RelationalExpr:")
    lines.extend(format_node(node["left"], level + 1))
    add_line(lines, line_num, level + 1, f"Operator: {node['operator']}")
    lines.extend(format_node(node["right"], level + 1))
    return lines

def format_arithmetic_expr(node, level, label=True):
    lines = []
    line_num = node.get("line_num", "")
    if label:
        add_line(lines, line_num, level, "ArithmeticExpr:")
        next_level = level + 1
    else:
        next_level = level
    if "left" in node:
        lines.extend(format_node(node["left"], next_level))
    if "operator" in node:
        add_line(lines, line_num, next_level, f"Operator: {node['operator']}")
    if "right" in node:
        lines.extend(format_node(node["right"], next_level))
    return lines

def format_while_statement(node, level):
    lines = []
    # Print header without a line number.
    add_line(lines, "", level, "WhileStmt:")
    if "test" in node:
        test_lines = format_node(node["test"], level + 1)
        insert_label_into_first_line(test_lines, "(test)", level + 1)
        lines.extend(test_lines)
    if "body" in node:
        add_line(lines, "", level + 1, "(body) StmtBlock:")
        lines.extend(format_node(node["body"], level + 2))
    return lines

def format_for_statement(node, level):
    lines = []
    # Print header without a line number.
    add_line(lines, "", level, "ForStmt:")
    if "init" in node:
        init = node["init"]
        if isinstance(init, dict) and "Empty" in init:
            add_line(lines, "", level + 1, "(init) Empty:")
        else:
            init_lines = format_node(init, level + 1)
            insert_label_into_first_line(init_lines, "(init)", level + 1)
            lines.extend(init_lines)
    if "test" in node:
        test_lines = format_node(node["test"], level + 1)
        insert_label_into_first_line(test_lines, "(test)", level + 1)
        lines.extend(test_lines)
    if "step" in node:
        step_lines = format_node(node["step"], level + 1)
        insert_label_into_first_line(step_lines, "(step)", level + 1)
        lines.extend(step_lines)
    if "body" in node:
        add_line(lines, "", level + 1, "(body) StmtBlock:")
        lines.extend(format_node(node["body"], level + 2))
    return lines

def format_if_statement(node, level):
    lines = []
    # Print header without a line number.
    add_line(lines, "", level, "IfStmt:")

    if "test" in node:
        test_lines = format_node(node["test"], level + 1)
        insert_label_into_first_line(test_lines, "(test)", level + 1)
        lines.extend(test_lines)

    if "then" in node:
        then_lines = format_node(node["then"], level + 1)
        insert_label_into_first_line(then_lines, "(then)", level + 1)
        lines.extend(then_lines)

    if "else" in node:
        else_lines = format_node(node["else"], level + 1)
        insert_label_into_first_line(else_lines, "(else)", level + 1)
        lines.extend(else_lines)

    return lines

def format_break_statement(node, level):
    lines = []
    line_num = node.get("line_num", "")
    add_line(lines, line_num, level, "BreakStmt:")
    return lines
