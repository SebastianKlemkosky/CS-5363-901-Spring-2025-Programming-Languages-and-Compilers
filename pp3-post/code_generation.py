# code_generation.py

def assign_stack_offsets(fn_decl):
    """
    STUB: Returns hardcoded frame sizes for now.
    Will later compute variable stack offsets and temp space dynamically.

    For now:
    - main gets 24 bytes (2 locals + 4 temps)
    - test gets 4 bytes (no locals, 1 temp for return)
    """
    fn_name = fn_decl["identifier"]["Identifier"]["name"]

    if fn_name == "main":
        frame_size = 24
        var_locations = { "c": -8, "s": -12 }  # hardcoded stack slots
    elif fn_name == "test":
        frame_size = 4
        var_locations = {}  # 'a' and 'b' are params (not stored here yet)
    else:
        frame_size = 0
        var_locations = {}

    return var_locations, frame_size

def emit(line, comment=None):
    """
    Formats a MIPS instruction line with optional comment.
    Comment is shifted 2 spaces to the left compared to instruction.
    """
    if comment:
        return f"\t  {line:<18}# {comment}"
    return f"\t  {line}"

def emit_comment(comment):
    """
    Emits a full-line comment with two spaces indent, for things like # BeginFunc.
    """
    return f"  {comment}"

def generate_code(ast_root):
    lines = []

    # Step 0: Check for main
    if not any("FnDecl" in node and node["FnDecl"]["identifier"]["Identifier"]["name"] == "main"
               for node in ast_root["Program"]):
        return "*** Error.\n*** Linker: function 'main' not defined"

    # Step 1: Emit preamble
    lines.append("\t# standard Decaf preamble ")
    lines.append("\t  .text")
    lines.append("\t  .align 2")
    lines.append("\t  .globl main")

    # Step 2: Emit functions
    for node in ast_root["Program"]:
        if "FnDecl" in node:
            fn_decl = node["FnDecl"]
            lines.extend(emit_function(fn_decl))  # you'll implement this next

    return "\n".join(lines) + "\n"

def emit_prologue(fn_name, frame_size):
    lines = []
    lines.append(f"  {fn_name}:")
    lines.append(emit_comment(f"  # BeginFunc {frame_size}"))
    lines.append(emit("subu $sp, $sp, 8", "decrement sp to make space to save ra, fp"))
    lines.append(emit("sw $fp, 8($sp)", "save fp"))
    lines.append(emit("sw $ra, 4($sp)", "save ra"))
    lines.append(emit("addiu $fp, $sp, 8", "set up new fp"))
    lines.append(emit(f"subu $sp, $sp, {frame_size}", "decrement sp to make space for locals/temps"))
    return lines

def emit_epilogue():
    lines = []
    lines.append(emit_comment("  # EndFunc"))
    lines.append(emit_comment("  # (below handles reaching end of fn body with no explicit return)"))
    lines.append(emit("move $sp, $fp", "pop callee frame off stack"))
    lines.append(emit("lw $ra, -4($fp)", "restore saved ra"))
    lines.append(emit("lw $fp, 0($fp)", "restore saved fp"))
    lines.append("\t  jr $ra          # return from function")
    return lines

def emit_function(fn_decl):
    fn_name = fn_decl["identifier"]["Identifier"]["name"]

    # Context tracks everything during statement walking
    context = {
        "var_locations": {},      # { 'c': -8, 's': -12 }
        "temp_locations": {},     # { '_tmp0': -16, '_tmp1': -20, ... }
        "string_table": {},       # { 'hello': '_string1' }
        "string_counter": 1,
        "temp_counter": 0,
        "offset": -8,             # start just below saved ra/fp
        "lines": []               # final emitted lines
    }

    # Walk statements and emit lines into context["lines"]
    body = fn_decl.get("body", {})
    if "StmtBlock" in body:
        for stmt in body["StmtBlock"]:
            emit_statement(stmt, context)

    # After all var/temp allocation, calculate final frame size
    frame_size = ((abs(context["offset"]) + 3) // 4) * 4

    # Emit final full function: prologue + body + epilogue
    lines = []
    lines.extend(emit_prologue(fn_name, frame_size))
    lines.extend(context["lines"])
    lines.extend(emit_epilogue())
    return lines


def emit_statement(stmt, context):
    """
    Given a statement node and context (which includes variable offsets, etc),
    emit corresponding MIPS code.

    context should be a dict like:
    {
        "var_locations": { "c": -8, "s": -12 },
        "temp_locations": { "_tmp0": -16 },
        "string_table": { "hello": "_string1" },
        "string_counter": 1,
        "lines": []  # accumulated MIPS output
    }
    """
    if "VarDecl" in stmt:
        # Handled elsewhere — offset assignment, no MIPS to emit here
        pass

    elif "AssignExpr" in stmt:
        target = stmt["AssignExpr"]["target"]
        value = stmt["AssignExpr"]["value"]

        if "StringConstant" in value:
            # TODO: implement string assignment handler
            # emit_assign_string_constant(stmt["AssignExpr"], context)
            pass

        elif "Call" in value:
            # TODO: implement function call assignment handler
            # emit_assign_call(stmt["AssignExpr"], context)
            pass

        # TODO: future case: arithmetic assignments (e.g., x = a + b)

    elif "PrintStmt" in stmt:
        # TODO: implement printing of variables (e.g., Print(c), Print(s))
        # emit_print_statement(stmt["PrintStmt"], context)
        pass

    elif "ReturnStmt" in stmt:
        # TODO: implement returning from a function (e.g., return a + b)
        # emit_return_statement(stmt["ReturnStmt"], context)
        pass

    else:
        print(f"WARNING: Unhandled statement: {stmt}")
