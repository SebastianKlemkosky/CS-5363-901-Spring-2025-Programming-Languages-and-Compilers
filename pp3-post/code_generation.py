# code_generation.py

offset_map = {}           # variable/temp name → stack offset
current_offset = -4       # start at -4, grow downward
temporary_count = 0       # for generating _tmpN names
string_labels = {}        # string → label (e.g., _string1)
string_count = 0          # for unique string label IDs

def generate_code(ast_root):
    global string_labels, string_count, label_count
    global offset_map, current_offset, temporary_count

    # Reset globals
    string_labels = {}
    string_count = 0
    label_count = 0
    offset_map = {}
    current_offset = -4
    temporary_count = 0

    # Step 1: Check for main function
    has_main = any(
        "FnDecl" in node and node["FnDecl"]["identifier"]["Identifier"]["name"] == "main"
        for node in ast_root["Program"]
    )
    if not has_main:
        return "*** Error.\n*** Linker: function 'main' not defined"

    data_section = []
    text_section = []

    # Step 2: Add text header
    text_section.extend([
        "\t# standard Decaf preamble",
        "\t  .text",
        "\t  .align 2",
        "\t  .globl main"
    ])

    # Step 3: Emit all functions using emit_function()
    for node in ast_root["Program"]:
        if "FnDecl" in node:
            function_node = node["FnDecl"]
            text_section.extend(emit_function(function_node))

    # Step 4: Emit .data section if strings were collected
    if ".data" in string_labels:
        data_section.insert(0, "\t.data")
        data_section.extend(string_labels[".data"])

    if data_section:
        return "\n".join(data_section + [""] + text_section)
    else:
        return "\n".join(text_section)

def emit_function(function_node):
    """
    Emits the full MIPS code for a function: prologue, body, and epilogue.
    """
    global offset_map, current_offset, temporary_count

    function_name = function_node["identifier"]["Identifier"]["name"]

    # Reset function-local tracking
    offset_map = {}
    current_offset = -4
    temporary_count = 0

    # Estimate stack frame size (we'll replace this later with a proper count)
    frame_size = 32

    lines = []

    # Prologue
    lines.extend(emit_function_prologue(function_name, frame_size))

    # Function body (statements)
    for statement in function_node["body"]["StmtBlock"]:
        lines.extend(handle_statement(statement, lines, []))  # data_lines passed separately if needed

    # Epilogue
    lines.extend(emit_function_epilogue())

    return lines

def emit_function_prologue(fn_name, frame_size):
    lines = []
    lines.append(f"{fn_name}:")
    lines.append(f"\t# BeginFunc {frame_size}")
    lines.append(f"\tsubu $sp, $sp, 8\t# decrement sp to make space to save ra, fp")
    lines.append(f"\tsw $fp, 8($sp)\t# save fp")
    lines.append(f"\tsw $ra, 4($sp)\t# save ra")
    lines.append(f"\taddiu $fp, $sp, 8\t# set up new fp")
    lines.append(f"\tsubu $sp, $sp, {frame_size}\t# decrement sp to make space for locals/temps")
    return lines

def emit_function_epilogue():
    lines = []
    lines.append(f"\t# EndFunc")
    lines.append(f"\t# (below handles reaching end of fn body with no explicit return)")
    lines.append(f"\tmove $sp, $fp\t# pop callee frame off stack")
    lines.append(f"\tlw $ra, -4($fp)\t# restore saved ra")
    lines.append(f"\tlw $fp, 0($fp)\t# restore saved fp")
    lines.append(f"\tjr $ra\t# return from function")
    return lines

def emit_label(label_name):
    return [f"{label_name}:"]

def allocate_local_variable(variable_name, size=4):
    """
    Assigns a stack offset for a local variable or temporary.
    Assumes 4-byte alignment (can be changed via `size` param).
    """
    global current_offset
    if variable_name not in offset_map:
        offset_map[variable_name] = current_offset
        current_offset -= size
    return offset_map[variable_name]

def get_stack_offset(variable_name):
    """
    Returns the stack offset for the given variable.
    """
    return offset_map.get(variable_name)

def generate_temporary_name():
    """
    Returns a new unique temporary name like _tmp0, _tmp1, ...
    """
    global temporary_count
    name = f"_tmp{temporary_count}"
    temporary_count += 1
    return name

def emit_string_constant(value):
    """
    Adds a string to the .data section if it's new.
    Returns the label name and the .data line to add.
    """
    global string_labels, string_count
    if value not in string_labels:
        label = f"_string{string_count}"
        string_labels[value] = label

def emit_assign_string(destination_variable, string_value):
    lines = []

    # Allocate the destination variable (if not already)
    allocate_local_variable(destination_variable)

    # Create or fetch the string label
    label, data_line = emit_string_constant(string_value)

    # Get the offset for destination
    offset = get_stack_offset(destination_variable)

    # Emit data section line (if newly created)
    if data_line:
        if ".data" not in string_labels:
            string_labels[".data"] = []  # temporary hack to store section contents
        string_labels[".data"].append(data_line)

    # Emit code: load label address and store to variable
    lines.append(f"\tla $t2, {label}\t# load label")
    lines.append(f"\tsw $t2, {offset}($fp)\t# spill {destination_variable} from $t2 to $fp{offset}")

    return lines

def emit_assign_integer_constant(destination_variable, integer_value):
    return []

def emit_assign_temporary(destination_variable, source_variable):
    return []

def emit_push_parameter(parameter_variable):
    return []

def emit_function_call(function_name):
    return []

def emit_pop_parameters(parameter_count):
    return []

def emit_print_statement(variable_name, variable_type):
    return []

def handle_statement(statement_node, code_lines, data_lines):
    # TEMPORARY skeleton return until implemented
    return []
