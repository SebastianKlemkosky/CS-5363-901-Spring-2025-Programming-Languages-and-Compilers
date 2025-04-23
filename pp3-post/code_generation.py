# code_generation.py

string_labels = {}
string_count = 0
tmp_count = -1
tmp_index = 0  # global counter for all _tmpN

def requires_temp(expr):
    return (
        "StringConstant" in expr or
        "IntConstant" in expr or
        "Call" in expr
    )

def new_string_label():
    global string_count
    string_count += 1
    return f"_string{string_count}"

def new_temp():
    global tmp_count
    tmp_count += 1
    return f"_tmp{tmp_count}"

def generate_code(ast_root):
    global string_labels, string_count, label_count
    string_labels = {}
    string_count = 0
    label_count = 0

    # Step 1: Check for main function
    has_main = any(
        "FnDecl" in node and node["FnDecl"]["identifier"]["Identifier"]["name"] == "main"
        for node in ast_root["Program"]
    )
    if not has_main:
        return "*** Error.\n*** Linker: function 'main' not defined"

    data_section = []
    text_section = []

    # Step 2: Process all declarations
    for decl in ast_root["Program"]:
        if "FnDecl" in decl:
            fn = decl["FnDecl"]
            text_section.extend(emit_function(fn))
        elif "VarDecl" in decl:
            # Optional: Global variables
            pass

    # Step 3: Add text header
    text_section.insert(0, "\t# standard Decaf preamble ")
    text_section.insert(1, "\t  .text")
    text_section.insert(2, "\t  .align 2")
    text_section.insert(3, "\t  .globl main")


    return "\n".join(data_section + text_section)

def emit_function(fn_decl):
    global tmp_index, offset

    lines = []
    name = fn_decl["identifier"]["Identifier"]["name"]
    label = name if name == "main" else f"_{name}"
    locals_map = {}
    offset = -4  # reserve space above for saved ra/fp

    body_stmts = fn_decl["body"]["StmtBlock"]
    assign_temps = {}

    frame_size = abs(offset)

    # 3. Emit prologue
    lines.extend(emit_prologue(label, frame_size))

   

    # 5. Emit epilogue
    lines.extend(emit_epilogue())

    return lines



def emit_call_expression(target, value, locals_map):
    global tmp_index, offset

    lines = []
    call = value["Call"]
    fn_name = call["identifier"]
    actuals = call.get("actuals", [])

    # Evaluate args in source order (to get correct _tmpN labels)
    tmp_args = []
    for arg in actuals:
        if "IntConstant" in arg:
            const_val = arg["IntConstant"]["value"]

            # Allocate a temp
            offset -= 4
            tmp_label = f"_tmp{tmp_index}"
            tmp_index += 1
            tmp_offset = offset
            locals_map[tmp_label] = tmp_offset

            lines.append(f"\t# {tmp_label} = {const_val}")
            lines.append(f"\t  li $t2, {const_val}")
            lines.append(f"\t  sw $t2, {tmp_offset}($fp)")
            tmp_args.append((tmp_label, tmp_offset))

    # Push params in reverse order (right-to-left)
    for tmp_label, tmp_offset in reversed(tmp_args):
        lines.append(f"\t# PushParam {tmp_label}")
        lines.append(f"\t  subu $sp, $sp, 4")
        lines.append(f"\t  lw $t0, {tmp_offset}($fp)")
        lines.append(f"\t  sw $t0, 4($sp)")

    # Call the function
    offset -= 4
    tmp_label = f"_tmp{tmp_index}"
    tmp_index += 1
    tmp_offset = offset
    locals_map[tmp_label] = tmp_offset

    lines.append(f"\t# {tmp_label} = LCall _{fn_name}")
    lines.append(f"\t  jal _{fn_name}")
    lines.append(f"\t  move $t2, $v0")
    lines.append(f"\t  sw $t2, {tmp_offset}($fp)")

    # Pop parameters
    if tmp_args:
        total = 4 * len(tmp_args)
        lines.append(f"\t# PopParams {total}")
        lines.append(f"\t  add $sp, $sp, {total}")

    # Assign to target
    lines.append(f"\t# {target} = {tmp_label}")
    lines.append(f"\t  lw $t2, {tmp_offset}($fp)")
    lines.append(f"\t  sw $t2, {locals_map[target]}($fp)")

    return lines

def emit_prologue(label, frame_size):
    return [
        f"  {label}:",
        f"\t# BeginFunc {frame_size}",
        "\t  subu $sp, $sp, 8\t# decrement sp to make space to save ra, fp",
        "\t  sw $fp, 8($sp)\t# save fp",
        "\t  sw $ra, 4($sp)\t# save ra",
        "\t  addiu $fp, $sp, 8\t# set up new fp",
        f"\t  subu $sp, $sp, {frame_size}\t# decrement sp to make space for locals/temps"
    ]

def emit_epilogue():
    return [
        "\t# EndFunc",
        "\t# (below handles reaching end of fn body with no explicit return)",
        "\t  move $sp, $fp\t# pop callee frame off stack",
        "\t  lw $ra, -4($fp)\t# restore saved ra",
        "\t  lw $fp, 0($fp)\t# restore saved fp",
        "\t  jr $ra\t\t# return from function"
    ]

def emit_string_assign(target, value, tmp_label, tmp_offset, locals_map):
    lines = []
    raw_string = value["StringConstant"]["value"]
    lines.append(f"\t# {tmp_label} = {raw_string}")
    lines.append(f"  \t  .data\t\t\t# create string constant marked with label")
    if raw_string not in string_labels:
        str_label = new_string_label()
        string_labels[raw_string] = str_label
        lines.append(f"  \t  {str_label}: .asciiz {raw_string}")
    else:
        str_label = string_labels[raw_string]
    lines.append(f"\t  .text")
    lines.append(f"\t  la $t2, {str_label}\t# load label")
    lines.append(f"\t  sw $t2, {tmp_offset}($fp)\t# spill {tmp_label} from $t2 to $fp{tmp_offset}")
    lines.append(f"\t# {target} = {tmp_label}")
    lines.append(f"\t  lw $t2, {tmp_offset}($fp)\t# fill {tmp_label} to $t2 from $fp{tmp_offset}")
    lines.append(f"\t  sw $t2, {locals_map[target]}($fp)\t# spill {target} from $t2 to $fp{locals_map[target]}")
    return lines

def emit_int_constant(int_val, tmp_label, tmp_offset):
    return [
        f"\t# {tmp_label} = {int_val}",
        f"\t  li $t2, {int_val}\t\t# load constant value {int_val} into $t2",
        f"\t  sw $t2, {tmp_offset}($fp)\t# spill {tmp_label} from $t2 to $fp{tmp_offset}"
    ]

def emit_return_arithmetic(expr, locals_map):
    global tmp_index, offset
    lines = []
    left = expr["ArithmeticExpr"]["left"]
    right = expr["ArithmeticExpr"]["right"]
    op = expr["ArithmeticExpr"]["operator"]

    offset -= 4
    tmp_label = f"_tmp{tmp_index}"
    tmp_index += 1
    tmp_offset = offset
    locals_map[tmp_label] = tmp_offset

    left_id = left["FieldAccess"]["identifier"] if "FieldAccess" in left else "?"
    right_id = right["FieldAccess"]["identifier"] if "FieldAccess" in right else "?"
    lines.append(f"\t# {tmp_label} = {left_id} {op} {right_id}")

    if "FieldAccess" in left:
        param_offset = {"a": 4, "b": 8}.get(left_id)
        if param_offset is not None:
            lines.append(f"\t  lw $t0, {param_offset}($fp)\t# fill {left_id} to $t0")

    if "FieldAccess" in right:
        param_offset = {"a": 4, "b": 8}.get(right_id)
        if param_offset is not None:
            lines.append(f"\t  lw $t1, {param_offset}($fp)\t# fill {right_id} to $t1")

    mips_op = {"+": "add", "-": "sub", "*": "mul", "/": "div"}.get(op, "add")
    lines.append(f"\t  {mips_op} $t2, $t0, $t1")
    lines.append(f"\t  sw $t2, {tmp_offset}($fp)\t# spill {tmp_label}")
    lines.append(f"\t# Return {tmp_label}")
    lines.append(f"\t  lw $t2, {tmp_offset}($fp)")
    lines.append(f"\t  move $v0, $t2")
    return lines
