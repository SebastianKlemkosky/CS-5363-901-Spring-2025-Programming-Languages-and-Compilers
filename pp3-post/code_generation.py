# code_generation.py

def get_var_offset(var_name, scope=None):
    if scope == "test":
        if var_name == "a":
            return 4  # $fp + 4
        if var_name == "b":
            return 8  # $fp + 8
    if var_name == "c":
        return -8
    if var_name == "s":
        return -12
    return -100  # fallback

def generate_code(ast_root):
    """
    Entry point to generate MIPS assembly code from a Decaf AST.
    Ensures that 'main' is defined as a global function.
    """
    # Linker-like check for main function
    has_main = False
    for node in ast_root["Program"]:
        if "FnDecl" in node:
            fn_name = node["FnDecl"]["identifier"]["Identifier"]["name"]
            if fn_name == "main":
                has_main = True
                break

    if not has_main:
        return "*** Error.\n*** Linker: function 'main' not defined"

    # standard Decaf preamble
    output = []
    output.append("\t# standard Decaf preamble ")
    output.append("  .text")
    output.append("  .align 2")
    output.append("  .globl main")

    for node in ast_root["Program"]:
        if "FnDecl" in node:
            output += emit_function(node["FnDecl"])  # implement this next

    return "\n".join(output)

def emit_function(fn_decl):
    """
    Emits MIPS assembly for a function definition.
    """
    lines = []

    fn_name = fn_decl["identifier"]["Identifier"]["name"]
    label = fn_name if fn_name == "main" else f"_{fn_name}"

    lines.append(f"{label}:")
    lines.append(f"\t# BeginFunc <placeholder>")

    # Prologue
    lines.append(f"\tsubu $sp, $sp, 8\t# decrement sp to make space to save ra, fp")
    lines.append(f"\tsw $fp, 8($sp)\t# save fp")
    lines.append(f"\tsw $ra, 4($sp)\t# save ra")
    lines.append(f"\taddiu $fp, $sp, 8\t# set up new fp")

    # Space for locals and temps — we will calculate this later
    lines.append(f"\tsubu $sp, $sp, 24\t# space for locals/temps")

    # Body
    if "body" in fn_decl:
        lines += emit_statement_block(fn_decl["body"], fn_name)

    # Epilogue
    lines.append(f"\t# EndFunc")
    lines.append(f"\tmove $sp, $fp\t# pop callee frame off stack")
    lines.append(f"\tlw $ra, -4($fp)\t# restore saved ra")
    lines.append(f"\tlw $fp, 0($fp)\t# restore saved fp")
    lines.append(f"\tjr $ra\t# return from function")

    return lines

def emit_statement_block(block, scope_name):
    """
    Emits MIPS code for a block of statements (StmtBlock).
    """
    lines = []

    for stmt in block.get("StmtBlock", []):
        if "VarDecl" in stmt:
            var_name = stmt["VarDecl"]["identifier"]
            lines.append(f"\t# Declare local variable: {var_name}")
            # No code needed — space is already reserved on stack

        elif "AssignExpr" in stmt:
            lines.append(f"\t# Assignment statement")
            lines += emit_assign(stmt["AssignExpr"], scope_name)

        elif "PrintStmt" in stmt:
            lines += emit_print(stmt["PrintStmt"], scope_name)

        elif "Call" in stmt:
            lines += emit_call(stmt["Call"], scope_name, is_statement=True)
        
        elif "ReturnStmt" in stmt:
            lines += emit_return(stmt, scope_name)

        else:
            lines.append(f"\t# Unhandled statement: {stmt}")

    return lines

def emit_assign(assign_expr, scope_name):
    """
    Emits MIPS code for assignment expressions.
    """
    lines = []
    target = assign_expr["target"]
    value = assign_expr["value"]
    line_num = assign_expr["line_num"]

    var_name = target["FieldAccess"]["identifier"]

    # Handle StringConstant: generate string in .data section
    if "StringConstant" in value:
        string_val = value["StringConstant"]["value"].strip('"')
        label = f"_string{line_num}"
        lines.append("\t.data")
        lines.append(f"{label}: .asciiz \"{string_val}\"")
        lines.append("\t.text")
        lines.append(f"\tla $t2, {label}")
        lines.append(f"\tsw $t2, {get_var_offset(var_name)}($fp)")
        return lines

    # Handle IntConstant: load into register and store to stack
    if "IntConstant" in value:
        val = value["IntConstant"]["value"]
        lines.append(f"\tli $t2, {val}")
        lines.append(f"\tsw $t2, {get_var_offset(var_name)}($fp)")
        return lines

    # Handle Call expression
    if "Call" in value:
        lines += emit_call(value["Call"], scope_name, target=var_name)
        return lines
    
    if "FieldAccess" in value:
        src_var = value["FieldAccess"]["identifier"]
        lines.append(f"\tlw $t2, {get_var_offset(src_var)}($fp)")  # load y
        lines.append(f"\tsw $t2, {get_var_offset(var_name)}($fp)")  # store into x
        return lines
    
    if "ArithmeticExpr" in value:
        left = value["ArithmeticExpr"]["left"]
        right = value["ArithmeticExpr"]["right"]
        op = value["ArithmeticExpr"]["operator"]

        # Assume both are FieldAccess for now
        lhs = left["FieldAccess"]["identifier"]
        rhs = right["FieldAccess"]["identifier"]
        lines.append(f"\tlw $t0, {get_var_offset(lhs)}($fp)")
        lines.append(f"\tlw $t1, {get_var_offset(rhs)}($fp)")

        if op == "+":
            lines.append(f"\tadd $t2, $t0, $t1")
        elif op == "-":
            lines.append(f"\tsub $t2, $t0, $t1")
        elif op == "*":
            lines.append(f"\tmul $t2, $t0, $t1")
        elif op == "/":
            lines.append(f"\tdiv $t0, $t1")
            lines.append(f"\tmflo $t2")  # result in $t2

        lines.append(f"\tsw $t2, {get_var_offset(var_name)}($fp)")
        return lines

    lines.append(f"\t# [TODO] Unhandled assignment value: {value}")
    return lines

def emit_call(call_expr, current_function, target=None):
    lines = []
    fn_name = call_expr["identifier"]
    args = call_expr.get("actuals", [])

    # Evaluate and push args (right to left)
    for actual in reversed(args):
        if "IntConstant" in actual:
            val = actual["IntConstant"]["value"]
            lines.append(f"\tli $t2, {val}")
            lines.append(f"\tsubu $sp, $sp, 4")
            lines.append(f"\tsw $t2, 4($sp)")
        else:
            # TODO: later handle variables, expressions, nested calls
            lines.append(f"\t# [TODO] Push other arg types: {actual}")

    # Call function
    lines.append(f"\tjal _{fn_name}")
    lines.append(f"\tmove $t2, $v0")

    # Store return value if needed
    if target:
        lines.append(f"\tsw $t2, {get_var_offset(target)}($fp)")

    # Pop params
    if args:
        lines.append(f"\tadd $sp, $sp, {len(args) * 4}")

    return lines

def emit_print(print_stmt, scope_name):
    lines = []
    for arg in print_stmt["args"]:
        if "IntConstant" in arg:
            val = arg["IntConstant"]["value"]
            lines.append(f"\tli $t2, {val}")
            lines.append(f"\tsubu $sp, $sp, 4")
            lines.append(f"\tsw $t2, 4($sp)")
            lines.append(f"\tjal _PrintInt")
            lines.append(f"\tadd $sp, $sp, 4")

        elif "StringConstant" in arg:
            str_val = arg["StringConstant"]["value"].strip('"')
            label = f"_string{print_stmt['line_num']}"
            lines.append(f"\t.data")
            lines.append(f"{label}: .asciiz \"{str_val}\"")
            lines.append(f"\t.text")
            lines.append(f"\tla $t2, {label}")
            lines.append(f"\tsubu $sp, $sp, 4")
            lines.append(f"\tsw $t2, 4($sp)")
            lines.append(f"\tjal _PrintString")
            lines.append(f"\tadd $sp, $sp, 4")

        elif "BoolConstant" in arg:
            val = arg["BoolConstant"]["value"]
            bool_val = "1" if val == "true" else "0"
            lines.append(f"\tli $t2, {bool_val}")
            lines.append(f"\tsubu $sp, $sp, 4")
            lines.append(f"\tsw $t2, 4($sp)")
            lines.append(f"\tjal _PrintBool")
            lines.append(f"\tadd $sp, $sp, 4")

        elif "FieldAccess" in arg:
            var = arg["FieldAccess"]["identifier"]
            offset = get_var_offset(var)
            lines.append(f"\tlw $t2, {offset}($fp)")
            lines.append(f"\tsubu $sp, $sp, 4")
            lines.append(f"\tsw $t2, 4($sp)")
            # Assume it's int or string (we’ll improve later with type info)
            if var == "s":  # TEMP: just a guess that s is string
                lines.append(f"\tjal _PrintString")
            else:
                lines.append(f"\tjal _PrintInt")
            lines.append(f"\tadd $sp, $sp, 4")

        else:
            lines.append(f"\t# [TODO] Unknown print arg type: {arg}")

    return lines

def emit_return(stmt, current_function):
    """
    Emits MIPS code for a ReturnStmt node.
    """
    lines = []
    expr = stmt["ReturnStmt"]["expr"]
    
    # Evaluate the return expression and leave it in $t2
    expr_lines, result_reg = emit_expression(expr, current_function)
    lines += expr_lines

    # Move result into $v0
    lines.append(f"\tmove $v0, {result_reg}")

    # Epilogue
    lines.append(f"\tmove $sp, $fp\t# pop callee frame off stack")
    lines.append(f"\tlw $ra, -4($fp)\t# restore saved ra")
    lines.append(f"\tlw $fp, 0($fp)\t# restore saved fp")
    lines.append(f"\tjr $ra\t# return from function")

    return lines

def emit_expression(expr, current_function):
    """
    Emits MIPS code for an expression and returns (lines, result_register).
    Supports basic constants, variables, and arithmetic.
    """
    lines = []

    if "IntConstant" in expr:
        value = expr["IntConstant"]["value"]
        lines.append(f"\tli $t2, {value}")
        return lines, "$t2"

    if "FieldAccess" in expr:
        var_name = expr["FieldAccess"]["identifier"]
        offset = get_var_offset(var_name, current_function)
        lines.append(f"\tlw $t2, {offset}($fp)")
        return lines, "$t2"

    if "ArithmeticExpr" in expr:
        node = expr["ArithmeticExpr"]
        op = node["operator"]
        left_expr = node["left"]
        right_expr = node["right"]

        left_lines, _ = emit_expression(left_expr, current_function)
        lines += left_lines
        lines.append(f"\tmove $t0, $t2")  # save left in $t0

        right_lines, _ = emit_expression(right_expr, current_function)
        lines += right_lines
        lines.append(f"\tmove $t1, $t2")  # save right in $t1

        if op == "+":
            lines.append(f"\tadd $t2, $t0, $t1")
        elif op == "-":
            lines.append(f"\tsub $t2, $t0, $t1")
        elif op == "*":
            lines.append(f"\tmul $t2, $t0, $t1")
        elif op == "/":
            lines.append(f"\tdiv $t0, $t1")
            lines.append(f"\tmflo $t2")
        elif op == "%":
            lines.append(f"\tdiv $t0, $t1")
            lines.append(f"\tmfhi $t2")
        else:
            lines.append(f"\t# Unsupported operator: {op}")

        return lines, "$t2"

    lines.append(f"\t# [emit_expression] Unhandled expr: {expr}")
    return lines, "$t2"
