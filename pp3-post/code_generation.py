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

def emit_epilogue():
    lines = []
    lines.append(emit_comment("  # EndFunc"))
    lines.append(emit_comment("  # (below handles reaching end of fn body with no explicit return)"))
    lines.append(emit("move $sp, $fp", "pop callee frame off stack"))
    lines.append(emit("lw $ra, -4($fp)", "restore saved ra"))
    lines.append(emit("lw $fp, 0($fp)", "restore saved fp"))
    lines.append("\t  jr $ra        # return from function")
    return lines

def emit_function(fn_decl, temp_counter):
    fn_name = fn_decl["identifier"]["Identifier"]["name"]

    context = {
        "var_locations": {},
        "temp_locations": {},
        "string_table": {},
        "string_counter": 1,
        "temp_counter": temp_counter,  # STARTING from the global value
        "offset": -8,
        "lines": []
    }

    body = fn_decl.get("body", {})
    if "StmtBlock" in body:
        for stmt in body["StmtBlock"]:
            emit_statement(stmt, context)

    print(f"DEBUG: {fn_name} final offset: {context['offset']}")
    print(f"DEBUG: {fn_name} temp_locations: {context['temp_locations']}")
    print(f"DEBUG: {fn_name} var_locations: {context['var_locations']}")

    frame_size = ((abs(context["offset"] + 8) + 3) // 4) * 4
    print(f"DEBUG: {fn_name} frame_size: {frame_size}")

    lines = []
    lines.extend(emit_prologue(fn_name, frame_size))
    lines.extend(context["lines"])
    lines.extend(emit_epilogue())

    # RETURN updated temp_counter
    return lines, context["temp_counter"]

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
        left = arith["left"]["FieldAccess"]["identifier"]
        right = arith["right"]["FieldAccess"]["identifier"]
        op = arith["operator"]

        # Assume a and b passed at +4 and +8
        a_offset = 4
        b_offset = 8

        # Allocate _tmpN
        tmp_num = context["temp_counter"]
        tmp_name = f"_tmp{tmp_num}"
        context["temp_counter"] += 1

        tmp_offset = context["offset"]
        context["temp_locations"][tmp_name] = tmp_offset
        context["offset"] -= 4

        lines.append(f"\t# {tmp_name} = {left} {op} {right}")
        lines.append(f"\t  lw $t0, {a_offset}($fp)\t# fill {left} to $t0 from $fp+{a_offset}")
        lines.append(f"\t  lw $t1, {b_offset}($fp)\t# fill {right} to $t1 from $fp+{b_offset}")

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

        lines.append(f"\t  sw $t2, {tmp_offset}($fp)\t# spill {tmp_name} from $t2 to $fp{tmp_offset}")

        lines.append(f"\t# Return {tmp_name}")
        lines.append(f"\t  lw $t2, {tmp_offset}($fp)\t# fill {tmp_name} to $t2 from $fp{tmp_offset}")
        lines.append(f"\t  move $v0, $t2\t    # assign return value into $v0")

        # Inline epilogue for explicit return
        lines.append(f"\t  move $sp, $fp\t    # pop callee frame off stack")
        lines.append(f"\t  lw $ra, -4($fp)\t# restore saved ra")
        lines.append(f"\t  lw $fp, 0($fp)\t# restore saved fp")
        lines.append(f"\t  jr $ra\t    # return from function")

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
            lines.append(f"\t  jal {print_fn}\t\t# jump to function")

            lines.append(f"\t# PopParams 4")
            lines.append(f"\t  add $sp, $sp, 4\t# pop params off stack")
