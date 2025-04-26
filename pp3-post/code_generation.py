# code_generation.py

def calculate_frame_size(offset):
    """
    Given final stack offset, calculate aligned frame size for MIPS.
    Adjustment of +8 because initial offset was -8 for saved $fp/$ra.
    """
    adjusted_offset = abs(offset + 8)
    frame_size = ((adjusted_offset + 3) // 4) * 4  # Round up to nearest 4
    return frame_size

def allocate_temp(context):
    tmp_num = context["temp_counter"]
    tmp_name = f"_tmp{tmp_num}"
    context["temp_counter"] += 1

    tmp_offset = context["offset"]
    context["temp_locations"][tmp_name] = tmp_offset
    context["offset"] -= 4

    return tmp_name, tmp_offset

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

    # Step 2: Emit functions with a shared temp counter
    temp_counter = 0
    for node in ast_root["Program"]:
        if "FnDecl" in node:
            fn_decl = node["FnDecl"]
            fn_lines, temp_counter = emit_function(fn_decl, temp_counter)
            lines.extend(fn_lines)

    return "\n".join(lines) + "\n"

def emit_prologue(fn_name, frame_size):
    lines = []

    label = f"  {fn_name}:" if fn_name == "main" else f"  _{fn_name}:"
    lines.append(label)

    lines.append(emit_comment(f"  # BeginFunc {frame_size}"))

    lines.append(emit("subu $sp, $sp, 8", "decrement sp to make space to save ra, fp"))
    lines.append(emit("sw $fp, 8($sp)", "save fp"))
    lines.append(emit("sw $ra, 4($sp)", "save ra"))
    lines.append(emit("addiu $fp, $sp, 8", "set up new fp"))
    lines.append(emit(f"subu $sp, $sp, {frame_size}", "decrement sp to make space for locals/temps"))

    return lines

def emit_epilogue_lines(add_end_comment=True):
    """
    Emit the standard MIPS function epilogue.
    If add_end_comment is True, also include "# EndFunc" and explanatory comments.
    """
    lines = []
    
    if add_end_comment:
        lines.append(emit_comment("  # EndFunc"))
        lines.append(emit_comment("  # (below handles reaching end of fn body with no explicit return)"))

    lines.append(emit("move $sp, $fp", "pop callee frame off stack"))
    lines.append(emit("lw $ra, -4($fp)", "restore saved ra"))
    lines.append(emit("lw $fp, 0($fp)", "restore saved fp"))
    lines.append("\t  jr $ra        # return from function")

    return lines

def emit_function(fn_decl, temp_counter):
    fn_name = fn_decl["identifier"]["Identifier"]["name"]

    # Create context for this function
    context = {
        "var_locations": {},
        "temp_locations": {},
        "string_table": {},
        "string_counter": 1,
        "temp_counter": temp_counter,
        "offset": -8,  # Start below saved $ra and $fp
        "lines": []
    }

    # Walk and emit all body statements
    body = fn_decl.get("body", {})
    if "StmtBlock" in body:
        for stmt in body["StmtBlock"]:
            emit_statement(stmt, context)

    # --- Calculate frame size dynamically after all emissions ---
    frame_size = calculate_frame_size(context["offset"])

    # --- Assemble full function ---
    lines = []
    lines.extend(emit_prologue(fn_name, frame_size))
    lines.extend(context["lines"])
    lines.extend(emit_epilogue_lines(add_end_comment=True))

    return lines, context["temp_counter"]

def emit_statement(stmt, context):
    if "VarDecl" in stmt:
        var_name = stmt["VarDecl"]["identifier"]
        context["var_locations"][var_name] = context["offset"]
        context["offset"] -= 4  # reserve space for local variable

    elif "AssignExpr" in stmt:
        target = stmt["AssignExpr"]["target"]
        value = stmt["AssignExpr"]["value"]

        if "StringConstant" in value:
            emit_assign_string_constant(stmt["AssignExpr"], context)
        elif "Call" in value:
            emit_assign_call(stmt["AssignExpr"], context)
        # TODO: future case: arithmetic assignments (e.g., x = a + b)

    elif "PrintStmt" in stmt:
        emit_print_statement(stmt["PrintStmt"], context)

    elif "ReturnStmt" in stmt:
        emit_return_statement(stmt["ReturnStmt"], context)

    elif "IfStmt" in stmt:
        # emit_if_statement(stmt["IfStmt"], context)
        pass

    elif "ForStmt" in stmt:
        # emit_for_statement(stmt["ForStmt"], context)
        pass

    elif "WhileStmt" in stmt:
        # emit_while_statement(stmt["WhileStmt"], context)
        pass

    elif "BreakStmt" in stmt:
        # emit_break_statement(stmt["BreakStmt"], context)
        pass

    elif "ContinueStmt" in stmt:
        # emit_continue_statement(stmt["ContinueStmt"], context)
        pass

    else:
        print(f"WARNING: Unhandled statement: {stmt}")

def emit_assign_string_constant(assign_expr, context):
    lines = context["lines"]
    string_val = assign_expr["value"]["StringConstant"]["value"].strip('"')
    dest_var = assign_expr["target"]["FieldAccess"]["identifier"]

    # --- Step 1: Get or create a label in the string table
    string_table = context["string_table"]
    if string_val not in string_table:
        label = f"_string{context['string_counter']}"
        context["string_counter"] += 1
        string_table[string_val] = label
    else:
        label = string_table[string_val]

    # --- Step 2: Allocate a temp (_tmpN)
    tmp_num = context["temp_counter"]
    tmp_name = f"_tmp{tmp_num}"
    context["temp_counter"] += 1

    tmp_offset = context["offset"]
    context["temp_locations"][tmp_name] = tmp_offset
    context["offset"] -= 4  # reserve stack space

    dest_offset = context["var_locations"][dest_var]

    # --- Step 3: Emit MIPS
    lines.append(f"\t# {tmp_name} = \"{string_val}\"")
    lines.append("\t  .data\t\t    # create string constant marked with label")
    lines.append(emit(f"{label}: .asciiz \"{string_val}\""))
    lines.append(emit(".text"))
    lines.append(f"\t  la $t2, {label}\t# load label")
    lines.append(f"\t  sw $t2, {tmp_offset}($fp)\t# spill {tmp_name} from $t2 to $fp{tmp_offset}")

    lines.append(f"\t# {dest_var} = {tmp_name}")
    lines.append(f"\t  lw $t2, {tmp_offset}($fp)\t# fill {tmp_name} to $t2 from $fp{tmp_offset}")
    lines.append(f"\t  sw $t2, {dest_offset}($fp)\t# spill {dest_var} from $t2 to $fp{dest_offset}")

def emit_assign_call(assign_expr, context):
    lines = context["lines"]
    call = assign_expr["value"]["Call"]
    dest_var = assign_expr["target"]["FieldAccess"]["identifier"]

    actuals = call.get("actuals", [])
    tmp_args = []

    # Step 1: Load each argument into a _tmpN
    for arg in actuals:
        if "IntConstant" in arg:
            value = arg["IntConstant"]["value"]

            # Allocate a temp
            tmp_num = context["temp_counter"]
            tmp_name = f"_tmp{tmp_num}"
            context["temp_counter"] += 1

            tmp_offset = context["offset"]
            context["temp_locations"][tmp_name] = tmp_offset
            context["offset"] -= 4

            # Emit loading constant
            lines.append(f"\t# {tmp_name} = {value}")
            lines.append(f"\t  li $t2, {value}\t    # load constant value {value} into $t2")
            lines.append(f"\t  sw $t2, {tmp_offset}($fp)\t# spill {tmp_name} from $t2 to $fp{tmp_offset}")

            tmp_args.append((tmp_name, tmp_offset))

    # Step 2: Push parameters in reverse order
    for tmp_name, tmp_offset in reversed(tmp_args):
        lines.append(f"\t# PushParam {tmp_name}")
        lines.append(f"\t  subu $sp, $sp, 4\t# decrement sp to make space for param")
        lines.append(f"\t  lw $t0, {tmp_offset}($fp)\t# fill {tmp_name} to $t0 from $fp{tmp_offset}")
        lines.append(f"\t  sw $t0, 4($sp)\t# copy param value to stack")

    # Step 3: Call the function and assign to a new temp
    tmp_num = context["temp_counter"]
    tmp_name = f"_tmp{tmp_num}"
    context["temp_counter"] += 1
    tmp_offset = context["offset"]
    context["temp_locations"][tmp_name] = tmp_offset
    context["offset"] -= 4

    lines.append(f"\t# {tmp_name} = LCall _{call['identifier']}")
    lines.append(f"\t  jal _{call['identifier']}\t\t\t    # jump to function")
    lines.append(f"\t  move $t2, $v0\t    # copy function return value from $v0")
    lines.append(f"\t  sw $t2, {tmp_offset}($fp)\t# spill {tmp_name} from $t2 to $fp{tmp_offset}")

    # Step 4: Pop params
    if actuals:
        lines.append(f"\t# PopParams {len(actuals) * 4}")
        lines.append(f"\t  add $sp, $sp, {len(actuals) * 4}\t# pop params off stack")

    # Step 5: Assign to target variable
    dest_offset = context["var_locations"][dest_var]
    lines.append(f"\t# {dest_var} = {tmp_name}")
    lines.append(f"\t  lw $t2, {tmp_offset}($fp)\t# fill {tmp_name} to $t2 from $fp{tmp_offset}")
    lines.append(f"\t  sw $t2, {dest_offset}($fp)\t# spill {dest_var} from $t2 to $fp{dest_offset}")

def emit_return_statement(return_stmt, context):
    lines = context["lines"]
    expr = return_stmt["expr"]

    if "ArithmeticExpr" in expr:
        arith = expr["ArithmeticExpr"]

        left = arith["left"]
        if "FieldAccess" in left:
            left_var = left["FieldAccess"]["identifier"]
            a_offset = context["var_locations"].get(left_var, 4)
        elif "IntConstant" in left:
            left_var = left_val = int(left["IntConstant"]["value"])
            a_offset = None
        else:
            print(f"WARNING: Unhandled left expression: {left}")
            a_offset = None

        right = arith["right"]
        if "FieldAccess" in right:
            right_var = right["FieldAccess"]["identifier"]
            b_offset = context["var_locations"].get(right_var, 8)
        elif "IntConstant" in right:
            right_var = right_val = int(right["IntConstant"]["value"])
            b_offset = None
        elif "Call" in right:
            call_node = right["Call"]
            tmp_name = f"_tmp{context['temp_counter']}"
            context["temp_counter"] += 1

            tmp_offset = context["offset"]
            context["temp_locations"][tmp_name] = tmp_offset
            context["offset"] -= 4

            emit_function_call(call_node, tmp_name, tmp_offset, context)

            right_var = tmp_name
            b_offset = tmp_offset
        else:
            print(f"WARNING: Unhandled right expression: {right}")
            b_offset = None

        op = arith["operator"]

        # --- Allocate _tmpN for result ---
        result_tmp, result_offset = allocate_temp(context)

        # --- Correct Order: first comment ---
        lines.append(f"\t# {result_tmp} = {left_var} {op} {right_var}")

        # --- Load operands ---
        if a_offset is not None:
            lines.append(f"\t  lw $t0, {a_offset}($fp)\t# fill {left_var} to $t0 from $fp+{a_offset}")
        else:
            lines.append(f"\t  li $t0, {left_var}\t# load const {left_var} into $t0")

        if b_offset is not None:
            lines.append(f"\t  lw $t1, {b_offset}($fp)\t# fill {right_var} to $t1 from $fp+{b_offset}")
        else:
            lines.append(f"\t  li $t1, {right_var}\t# load const {right_var} into $t1")

        # --- Perform the operation ---
        if op == "+":
            lines.append(f"\t  add $t2, $t0, $t1")
        elif op == "-":
            lines.append(f"\t  sub $t2, $t0, $t1")
        elif op == "*":
            lines.append(f"\t  mul $t2, $t0, $t1")
        elif op == "/":
            lines.append(f"\t  div $t2, $t0, $t1")
        else:
            lines.append(f"\t  # unsupported op: {op}")

        lines.append(f"\t  sw $t2, {result_offset}($fp)\t# spill {result_tmp} from $t2 to $fp{result_offset}")

        # --- Return result ---
        lines.append(f"\t# Return {result_tmp}")
        lines.append(f"\t  lw $t2, {result_offset}($fp)\t# fill {result_tmp} to $t2 from $fp{result_offset}")
        lines.append(f"\t  move $v0, $t2\t    # assign return value into $v0")

        # --- Inline epilogue ---
        lines.extend(emit_epilogue_lines(add_end_comment=False))


def emit_function_call(call_node, tmp_name, tmp_offset, context):
    lines = context["lines"]
    func_name = call_node["identifier"]
    args = call_node.get("actuals", [])

    # --- Push parameters (reversed order) ---
    for arg in reversed(args):
        if "FieldAccess" in arg:
            var = arg["FieldAccess"]["identifier"]
            var_offset = context["var_locations"].get(var, -4)
            lines.append(f"\t  subu $sp, $sp, 4")
            lines.append(f"\t  lw $t0, {var_offset}($fp)\t# load {var}")
            lines.append(f"\t  sw $t0, 4($sp)")
        elif "IntConstant" in arg:
            value = int(arg["IntConstant"]["value"])
            lines.append(f"\t  subu $sp, $sp, 4")
            lines.append(f"\t  li $t0, {value}\t# load const {value}")
            lines.append(f"\t  sw $t0, 4($sp)")
        elif "ArithmeticExpr" in arg:
            # Handle n-1 inline
            arith = arg["ArithmeticExpr"]
            left = arith["left"]["FieldAccess"]["identifier"]
            right_val = int(arith["right"]["IntConstant"]["value"])
            op = arith["operator"]

            left_offset = context["var_locations"].get(left, -4)

            lines.append(f"\t  lw $t0, {left_offset}($fp)\t# load {left}")
            lines.append(f"\t  li $t1, {right_val}\t# load {right_val}")

            if op == "+":
                lines.append(f"\t  add $t2, $t0, $t1")
            elif op == "-":
                lines.append(f"\t  sub $t2, $t0, $t1")
            elif op == "*":
                lines.append(f"\t  mul $t2, $t0, $t1")
            elif op == "/":
                lines.append(f"\t  div $t2, $t0, $t1")

            # Spill temp
            temp_num = context["temp_counter"]
            temp_name = f"_tmp{temp_num}"
            context["temp_counter"] += 1

            temp_offset = context["offset"]
            context["temp_locations"][temp_name] = temp_offset
            context["offset"] -= 4

            lines.append(f"\t  sw $t2, {temp_offset}($fp)\t# spill {temp_name}")

            # Push temp
            lines.append(f"\t  subu $sp, $sp, 4")
            lines.append(f"\t  lw $t0, {temp_offset}($fp)\t# load {temp_name}")
            lines.append(f"\t  sw $t0, 4($sp)")

        else:
            print(f"WARNING: Complex function call argument not handled: {arg}")

    # --- Call function ---
    lines.append(f"\t# LCall _{func_name}")
    lines.append(f"\t  jal _{func_name}\t# jump to function")
    lines.append(f"\t  move $t2, $v0\t# copy return value from $v0")

    # --- Pop parameters ---
    if args:
        lines.append(f"\t  add $sp, $sp, {len(args) * 4}\t# pop params off stack")

    # --- Spill result into given temp slot ---
    lines.append(f"\t  sw $t2, {tmp_offset}($fp)\t# store result into {tmp_name}")

def emit_print_statement(print_stmt, context):
    lines = context["lines"]

    for arg in print_stmt["args"]:
        if "FieldAccess" in arg:
            var_name = arg["FieldAccess"]["identifier"]

            # Lookup stack offset
            offset = context["var_locations"].get(var_name)
            if offset is None:
                raise KeyError(f"Variable '{var_name}' not found in var_locations")

            # Decide function to call based on var type
            # Simple heuristic: assume strings are at more negative offsets than ints
            # Or hardcode based on known names
            if var_name == "s":  # You can generalize this later
                print_fn = "_PrintString"
            else:
                print_fn = "_PrintInt"

            # Emit MIPS
            lines.append(f"\t# PushParam {var_name}")
            lines.append(f"\t  subu $sp, $sp, 4\t# decrement sp to make space for param")
            lines.append(f"\t  lw $t0, {offset}($fp)\t# fill {var_name} to $t0 from $fp{offset}")
            lines.append(f"\t  sw $t0, 4($sp)\t# copy param value to stack")

            lines.append(f"\t# LCall {print_fn}")
            lines.append(f"\t  jal {print_fn}\t\t\t# jump to function")

            lines.append(f"\t# PopParams 4")
            lines.append(f"\t  add $sp, $sp, 4\t# pop params off stack")
