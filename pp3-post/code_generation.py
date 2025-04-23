# code_generation.py

string_labels = {}
string_count = 0
tmp_count = -1

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
    lines = []
    name = fn_decl["identifier"]["Identifier"]["name"]
    label = name
    locals_map = {}
    offset = -4  # Start after space reserved for saved ra


    body_stmts = fn_decl["body"]["StmtBlock"]
    assign_temps = {}  # maps stmt ID to (tmp_label, offset)

    # 1a. First pass: assign declared locals
    for stmt in body_stmts:
        if "VarDecl" in stmt:
            var_name = stmt["VarDecl"]["identifier"]
            offset -= 4
            locals_map[var_name] = offset

    # 1b. Then assign temporaries
    tmp_index = 0
    for stmt in body_stmts:
        if "AssignExpr" in stmt:
            value = stmt["AssignExpr"]["value"]
            if requires_temp(value):
                offset -= 4
                tmp_label = f"_tmp{tmp_index}"
                tmp_index += 1
                assign_temps[id(stmt)] = (tmp_label, offset)
                locals_map[tmp_label] = offset


    frame_size = abs(offset) + 4  # Add space back for saved ra/fp area

    # 2. Emit function prologue
    lines.append(f"  {label}:")
    lines.append(f"\t# BeginFunc {frame_size}")
    lines.append("\t  subu $sp, $sp, 8\t# decrement sp to make space to save ra, fp")
    lines.append("\t  sw $fp, 8($sp)\t# save fp")
    lines.append("\t  sw $ra, 4($sp)\t# save ra")
    lines.append("\t  addiu $fp, $sp, 8\t# set up new fp")
    lines.append(f"\t  subu $sp, $sp, {frame_size}\t# decrement sp to make space for locals/temps")

    # 3. Emit assignment statements
    for stmt in body_stmts:
        if "AssignExpr" in stmt:
            target = stmt["AssignExpr"]["target"]["FieldAccess"]["identifier"]
            value = stmt["AssignExpr"]["value"]

            if "StringConstant" in value:
                raw_string = value["StringConstant"]["value"]
                tmp_label, tmp_offset = assign_temps[id(stmt)]

                # Emit _tmpN = "hello"
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

                # Emit s = _tmpN
                lines.append(f"\t# {target} = {tmp_label}")
                lines.append(f"\t  lw $t2, {tmp_offset}($fp)\t# fill {tmp_label} to $t2 from $fp{tmp_offset}")
                lines.append(f"\t  sw $t2, {locals_map[target]}($fp)\t# spill {target} from $t2 to $fp{locals_map[target]}")

            elif "IntConstant" in value:
                int_val = value["IntConstant"]["value"]
                tmp_label, tmp_offset = assign_temps[id(stmt)]

                # Emit _tmpN = 4 or 5
                lines.append(f"\t# {tmp_label} = {int_val}")
                lines.append(f"\t  li $t2, {int_val}\t\t# load constant value {int_val} into $t2")
                lines.append(f"\t  sw $t2, {tmp_offset}($fp)\t# spill {tmp_label} from $t2 to $fp{tmp_offset}")

    return lines
