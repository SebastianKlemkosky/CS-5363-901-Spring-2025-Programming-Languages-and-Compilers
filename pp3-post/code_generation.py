# code_generation.py

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
    lines = []

    fn_name = fn_decl["identifier"]["Identifier"]["name"]

    # Use 24 for main, 0 for test for now
    frame_size = 24 if fn_name == "main" else 0

    lines.extend(emit_prologue(fn_name, frame_size))
    # (body goes here later)
    lines.extend(emit_epilogue())

    return lines

