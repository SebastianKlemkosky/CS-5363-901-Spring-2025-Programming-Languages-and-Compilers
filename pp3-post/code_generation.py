# code_generation.py

temp_counter = 0
def new_temp():
    global temp_counter
    name = f"_tmp{temp_counter}"
    temp_counter += 1
    return name

string_counter = 1
def next_string_label():
    global string_counter
    label = f"_string{string_counter}"
    string_counter += 1
    return label

def get_var_offset(var_name):
    """
    Placeholder for retrieving the stack offset of a variable.
    Replace this with actual symbol table logic later.
    """
    return "<offset>"  # e.g., will be replaced with -8, -12, etc.

def compute_stack_space():
    """
    Placeholder stack size computation — returns '<placeholder>' string for now.
    """
    return "<placeholder>"

def generate_code(ast_root):

    """
    Entry point to generate MIPS assembly code from a Decaf AST.
    Ensures that 'main' is defined as a global function.
    """
    # Linker check for 'main'
    has_main = any(
        "FnDecl" in node and node["FnDecl"]["identifier"]["Identifier"]["name"] == "main"
        for node in ast_root["Program"]
    )
    if not has_main:
        return "*** Error.\n*** Linker: function 'main' not defined"

    output = []
    output.append("    # standard Decaf preamble ")
    output.append("\t  .text")
    output.append("\t  .align 2")
    output.append("\t  .globl main")

    for node in ast_root["Program"]:
        if "FnDecl" in node:
            output += emit_function(node["FnDecl"])

    return "\n".join(output)

def emit_function(fn_decl):


    lines = []

    fn_name = fn_decl["identifier"]["Identifier"]["name"]
    label = fn_name if fn_name == "main" else f"_{fn_name}"
    lines.append(f"  {label}:")

    # Compute actual stack space
    stack_size = compute_stack_space()
    lines.append(f"  \t# BeginFunc {stack_size}")
    lines.append("  \t  subu $sp, $sp, 8  # decrement sp to make space to save ra, fp")
    lines.append("  \t  sw $fp, 8($sp)    # save fp")
    lines.append("  \t  sw $ra, 4($sp)    # save ra")
    lines.append("  \t  addiu $fp, $sp, 8 # set up new fp")
    lines.append(f"  \t  subu $sp, $sp, {stack_size} # decrement sp to make space for locals/temps")

    lines.append("  \t# EndFunc")
    lines.append("  \t# (below handles reaching end of fn body with no explicit return)")
    lines.append("  \t  move $sp, $fp     # pop callee frame off stack")
    lines.append("  \t  lw $ra, -4($fp)   # restore saved ra")
    lines.append("  \t  lw $fp, 0($fp)    # restore saved fp")
    lines.append("  \t  jr $ra        # return from function")

    return lines

