# code_generation.py

def get_var_offset(var_name):
    """
    Returns the stack offset for a given local variable name.
    For now, hardcoded offsets. Later will use per-function symbol table.
    """
    # Temporary hardcoded stack layout (Decaf aligns locals at negative offsets from $fp)
    fixed_offsets = {
        "c": -8,
        "s": -12
    }

    return fixed_offsets.get(var_name, -100)  # -100 is a signal something's wrong

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
