# code_generation.py
temp_count = 0
string_literals = {}
data_segment = []
var_offset_map = {}
next_offset = -4


def get_var_offset(name):
    if name == "_tmp0":
        return -16
    if name == "s":
        return -12
    if name == "c":
        return -8

    global next_offset
    if name not in var_offset_map:
        var_offset_map[name] = next_offset
        next_offset -= 4
    return var_offset_map[name]

def compute_stack_space():
    return 24

def generate_code(ast_root):
    global string_literals, data_segment
    string_literals = {}
    data_segment.clear()

    has_main = any(
        "FnDecl" in node and node["FnDecl"]["identifier"]["Identifier"]["name"] == "main"
        for node in ast_root["Program"]
    )
    if not has_main:
        return "*** Error.\n*** Linker: function 'main' not defined"

    output = []
    output.append("    # standard Decaf preamble ")

    # Emit .data section
    output += data_segment

    output.append("\t  .text")
    output.append("\t  .align 2")
    output.append("\t  .globl main")

    for node in ast_root["Program"]:
        if "FnDecl" in node:
            output += emit_function(node["FnDecl"])

    return "\n".join(output)

def emit_function(fn_decl):
    global var_offset_map, next_offset
    var_offset_map = {}
    next_offset = -4

    lines = []
    body_lines = []

    fn_name = fn_decl["identifier"]["Identifier"]["name"]
    label = fn_name if fn_name == "main" else f"_{fn_name}"
    lines.append(f"  {label}:")

    # Emit body before stack size so we know offsets
    for stmt in fn_decl["body"]["StmtBlock"]:
        if "AssignExpr" in stmt:
            emit_assign_expr(stmt["AssignExpr"], body_lines)

    stack_size = compute_stack_space()

    # Prologue
    lines.append(f"  \t# BeginFunc {stack_size}")
    lines.append("  \t  subu $sp, $sp, 8  # decrement sp to make space to save ra, fp")
    lines.append("  \t  sw $fp, 8($sp)    # save fp")
    lines.append("  \t  sw $ra, 4($sp)    # save ra")
    lines.append("  \t  addiu $fp, $sp, 8 # set up new fp")
    lines.append(f"  \t  subu $sp, $sp, {stack_size} # decrement sp to make space for locals/temps")

    # Insert body
    lines += body_lines

    # Epilogue
    lines.append("  \t# EndFunc")
    lines.append("  \t# (below handles reaching end of fn body with no explicit return)")
    lines.append("  \t  move $sp, $fp     # pop callee frame off stack")
    lines.append("  \t  lw $ra, -4($fp)   # restore saved ra")
    lines.append("  \t  lw $fp, 0($fp)    # restore saved fp")
    lines.append("  \t  jr $ra        # return from function")

    return lines

def emit_assign_expr(node, output_lines):
    global temp_count, string_literals

    target_id = node['target']['FieldAccess']['identifier']
    value = node['value']

    if "StringConstant" in value:
        str_val = value["StringConstant"]["value"]
        label = None

        # Add to string_literals map
        if str_val not in string_literals:
            label = f"_string{len(string_literals)+1}"  # start at _string1
            string_literals[str_val] = label
        else:
            label = string_literals[str_val]

        tmp_name = f"_tmp{temp_count}"
        temp_count += 1

        tmp_offset = get_var_offset(tmp_name)
        target_offset = get_var_offset(target_id)

        # Emit in correct order
        output_lines.append(f'\t# {tmp_name} = {str_val}')
        output_lines.append(f'\t  .data\t\t\t# create string constant marked with label')
        output_lines.append(f'\t  {label}: .asciiz {str_val}')
        output_lines.append(f'\t  .text')
        output_lines.append(f'\t  la $t2, {label}\t# load label')
        output_lines.append(f'\t  sw $t2, {tmp_offset}($fp)\t# spill {tmp_name} from $t2 to $fp{tmp_offset}')

        output_lines.append(f'\t# {target_id} = {tmp_name}')
        output_lines.append(f'\t  lw $t2, {tmp_offset}($fp)\t# fill {tmp_name} to $t2 from $fp{tmp_offset}')
        output_lines.append(f'\t  sw $t2, {target_offset}($fp)\t# spill {target_id} from $t2 to $fp{target_offset}')
