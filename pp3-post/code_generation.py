# code_generation.py
from helper_functions import calculate_frame_size, allocate_temp, get_print_function_for_type, get_var_type, format_relop_comment, format_offset

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

    # Label
    label = f"  {fn_name}:" if fn_name == "main" else f"  _{fn_name}:"
    lines.append(label)

    # BeginFunc comment
    lines.append(f"    # BeginFunc {frame_size}")

    # Function prologue body
    lines.append(f"\t  subu $sp, $sp, 8  # decrement sp to make space to save ra, fp")
    lines.append(f"\t  sw $fp, 8($sp)    # save fp")
    lines.append(f"\t  sw $ra, 4($sp)    # save ra")
    lines.append(f"\t  addiu $fp, $sp, 8 # set up new fp")
    lines.append(f"\t  subu $sp, $sp, {frame_size} # decrement sp to make space for locals/temps")

    return lines

def emit_epilogue_lines(add_end_comment=True):
    """
    Emit the standard MIPS function epilogue.
    If add_end_comment is True, also include "# EndFunc" and explanatory comments.
    """
    lines = []

    if add_end_comment:
        lines.append(f"    # EndFunc")
        lines.append(f"    # (below handles reaching end of fn body with no explicit return)")

    lines.append(f"\t  move $sp, $fp     # pop callee frame off stack")
    lines.append(f"\t  lw $ra, -4($fp)   # restore saved ra")
    lines.append(f"\t  lw $fp, 0($fp)    # restore saved fp")
    lines.append(f"\t  jr $ra        # return from function")

    return lines

def emit_push_param(lines, offset, var_name=None):
    """
    Emits MIPS instructions to push a variable or constant onto the stack.
    """
    lines.append("\t  subu $sp, $sp, 4\t# decrement sp to make space for param")
    if var_name:
        lines.append(f"\t  lw $t0, {offset}($fp)\t# fill {var_name} to $t0 from $fp{offset}")
    else:
        lines.append(f"\t  lw $t0, {offset}($fp)\t# fill temp to $t0 from $fp{offset}")
    lines.append("\t  sw $t0, 4($sp)\t# copy param value to stack")

def emit_function(fn_decl, temp_counter):
    fn_name = fn_decl["identifier"]["Identifier"]["name"]

    # Create context for this function
    context = {
        "var_locations": {},
        "var_types": {},           # Add this if you didn't already!
        "temp_locations": {},
        "constant_temps": set(),
        "string_table": {},
        "string_counter": 1,
        "temp_counter": temp_counter,
        "offset": -8,
        "lines": [],
        "if_counter": 0,            # <<< 🛠 ADD THIS
        "loop_counter": 0           # <<< (for future while/for/break/continue)
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
        var_type = stmt["VarDecl"]["type"]

        # Save variable location (for stack offset)
        context["var_locations"][var_name] = context["offset"]

        # Save variable type (for future things like print detection)
        context.setdefault("var_types", {})[var_name] = var_type

        context["offset"] -= 4  # Reserve space for local variable


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
        emit_if_statement(stmt["IfStmt"], context)
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
    tmp_name, tmp_offset = allocate_temp(context)
    dest_offset = context["var_locations"][dest_var]

    # --- Step 3: Emit MIPS
    lines.append(f"\t# {tmp_name} = \"{string_val}\"")
    lines.append("\t  .data\t\t    # create string constant marked with label")
    lines.append(f"\t  {label}: .asciiz \"{string_val}\"")
    lines.append("\t  .text")
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

            tmp_name, tmp_offset = allocate_temp(context)

            lines.append(f"\t# {tmp_name} = {value}")
            lines.append(f"\t  li $t2, {value}\t    # load constant value {value} into $t2")
            lines.append(f"\t  sw $t2, {tmp_offset}($fp)\t# spill {tmp_name} from $t2 to $fp{tmp_offset}")

            context["constant_temps"].add(tmp_name)   # 👈 ADD THIS!

            tmp_args.append((tmp_name, tmp_offset))

    # Step 2: Push parameters in reverse order
    for tmp_name, tmp_offset in reversed(tmp_args):
        lines.append(f"\t# PushParam {tmp_name}")
        emit_push_param(lines, tmp_offset, tmp_name)

    # Step 3: Call the function and assign to a new temp
    tmp_name, tmp_offset = allocate_temp(context)

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

            lines.append(f"\t# PushParam {var}")
            emit_push_param(lines, var_offset, var)

        elif "IntConstant" in arg:
            value = int(arg["IntConstant"]["value"])

            # Allocate a temp to hold the constant
            tmp_name_const, tmp_offset_const = allocate_temp(context)

            context["constant_temps"].add(tmp_name_const)  # 🔥 ADD THIS

            lines.append(f"\t# {tmp_name_const} = {value}")
            lines.append(f"\t  li $t2, {value}\t# load const {value}")
            lines.append(f"\t  sw $t2, {tmp_offset_const}($fp)\t# spill {tmp_name_const}")

            lines.append(f"\t# PushParam {tmp_name_const}")
            emit_push_param(lines, tmp_offset_const, tmp_name_const)

        elif "StringConstant" in arg:
            value = arg["StringConstant"]["value"]
            print(f"WARNING: String constants not supported in function calls yet: {value}")

        elif "DoubleConstant" in arg:
            value = arg["DoubleConstant"]["value"]
            print(f"WARNING: Double constants not supported in function calls yet: {value}")

        elif "BoolConstant" in arg:
            value = arg["BoolConstant"]["value"]
            print(f"WARNING: Bool constants not supported in function calls yet: {value}")

        elif "ArithmeticExpr" in arg:
            arith = arg["ArithmeticExpr"]
            left = arith["left"]["FieldAccess"]["identifier"]
            right_val = int(arith["right"]["IntConstant"]["value"])
            op = arith["operator"]

            left_offset = context["var_locations"].get(left, -4)

            # Allocate temp BEFORE emitting op
            temp_name, temp_offset = allocate_temp(context)

            lines.append(f"\t# {temp_name} = {left} {op} {right_val}")
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

            lines.append(f"\t  sw $t2, {temp_offset}($fp)\t# spill {temp_name}")

            lines.append(f"\t# PushParam {temp_name}")
            emit_push_param(lines, temp_offset, temp_name)

        else:
            print(f"WARNING: Complex function call argument not handled: {arg}")

    # --- Call function ---
    lines.append(f"\t# LCall _{func_name}")
    lines.append(f"\t  jal _{func_name}\t     # jump to function")
    lines.append(f"\t  move $t2, $v0\t# copy return value from $v0")

    # --- Pop parameters ---
    if args:
        lines.append(f"\t  add $sp, $sp, {len(args) * 4}\t# pop params off stack")

    # --- Spill result into given temp slot ---
    lines.append(f"\t  sw $t2, {tmp_offset}($fp)\t# store result into {tmp_name}")

def emit_print_statement(print_stmt, context):
    lines = context["lines"]

    # Centralized mapping of type -> print function
    type_to_print_fn = {
        "int": "_PrintInt",
        "string": "_PrintString",
        "bool": "_PrintBool",
        "double": "_PrintDouble",
    }

    for arg in print_stmt["args"]:
        if "FieldAccess" in arg:
            var_name = arg["FieldAccess"]["identifier"]
            offset = context["var_locations"].get(var_name)

            if offset is None:
                raise KeyError(f"Variable '{var_name}' not found in var_locations")

            var_type = get_var_type(arg["FieldAccess"], context)

            # Look up print function by type
            print_fn = type_to_print_fn.get(var_type, "_PrintInt")  # fallback to _PrintInt

            lines.append(f"\t# PushParam {var_name}")
            emit_push_param(lines, offset, var_name)

            lines.append(f"\t# LCall {print_fn}")
            if print_fn == "_PrintString":
                lines.append(f"\t  jal {print_fn}      # jump to function")
            else:
                lines.append(f"\t  jal {print_fn}         # jump to function")


            lines.append(f"\t# PopParams 4")
            lines.append(f"\t  add $sp, $sp, 4\t# pop params off stack")

        elif "StringConstant" in arg:
            value = arg["StringConstant"]["value"]
            print(f"WARNING: Print StringConstant '{value}' not supported yet")

        elif "IntConstant" in arg:
            value = arg["IntConstant"]["value"]
            print(f"WARNING: Print IntConstant {value} not supported yet")

        elif "BoolConstant" in arg:
            value = arg["BoolConstant"]["value"]
            print(f"WARNING: Print BoolConstant {value} not supported yet")

        elif "DoubleConstant" in arg:
            value = arg["DoubleConstant"]["value"]
            print(f"WARNING: Print DoubleConstant {value} not supported yet")

        else:
            print(f"WARNING: Complex PrintStmt argument not handled: {arg}")

def emit_relop_expression(expr, context):
    """
    Emits MIPS instructions to evaluate a relational expression.
    Returns the name of the temp (_tmpN) holding the boolean result (0/1).
    """
    lines = context["lines"]

    if "RelationalExpr" not in expr:
        raise ValueError("emit_relop_expression expected RelationalExpr")

    relop = expr["RelationalExpr"]
    left = relop["left"]
    right = relop["right"]
    operator = relop["operator"]

    # --- Load left operand ---
    left_is_field = False
    if "FieldAccess" in left:
        left_var = left["FieldAccess"]["identifier"]
        left_offset = context["var_locations"].get(left_var, 4)
        left_is_field = True

    elif "IntConstant" in left or "BoolConstant" in left:
        val = int(left.get("IntConstant", left.get("BoolConstant"))["value"])
        tmp_left, tmp_left_offset = allocate_temp(context)

        if tmp_left not in context["constant_temps"]:
            lines.append(f"\t# {tmp_left} = {val}")
            lines.append(f"\t  li $t2, {val}\t    # load constant value {val} into $t2")
            lines.append(f"\t  sw $t2, {tmp_left_offset}($fp)\t# spill {tmp_left} from $t2 to $fp{format_offset(tmp_left_offset)}")
            context["constant_temps"].add(tmp_left)

        left_var = tmp_left
        left_offset = tmp_left_offset

    else:
        print(f"WARNING: Unsupported left operand type: {left}")

    # --- Load right operand ---
    right_is_field = False
    if "FieldAccess" in right:
        right_var = right["FieldAccess"]["identifier"]
        right_offset = context["var_locations"].get(right_var, 8)
        right_is_field = True

    elif "IntConstant" in right or "BoolConstant" in right:
        val = int(right.get("IntConstant", right.get("BoolConstant"))["value"])
        tmp_right, tmp_right_offset = allocate_temp(context)

        if tmp_right not in context["constant_temps"]:
            lines.append(f"\t# {tmp_right} = {val}")
            lines.append(f"\t  li $t2, {val}\t    # load constant value {val} into $t2")
            lines.append(f"\t  sw $t2, {tmp_right_offset}($fp)\t# spill {tmp_right} from $t2 to $fp{format_offset(tmp_right_offset)}")
            context["constant_temps"].add(tmp_right)

        right_var = tmp_right
        right_offset = tmp_right_offset

    else:
        print(f"WARNING: Unsupported right operand type: {right}")

    # --- Allocate temp to store result ---
    tmp_name, tmp_offset = allocate_temp(context)

    # --- Emit the load instructions ---
    lines.append(format_relop_comment(tmp_name, left_var, operator, right_var))
    lines.append(f"\t  lw $t0, {left_offset}($fp)\t# fill {left_var} to $t0 from $fp{format_offset(left_offset)}")
    lines.append(f"\t  lw $t1, {right_offset}($fp)\t# fill {right_var} to $t1 from $fp{format_offset(right_offset)}")

    # --- Emit relational operation ---
    emit_relop("$t0", "$t1", operator, "$t2", lines)

    # --- Spill result ---
    lines.append(f"\t  sw $t2, {tmp_offset}($fp)\t# spill {tmp_name} from $t2 to $fp{format_offset(tmp_offset)}")

    if operator in ("<=", ">="):
        # --- Also emit equality check (==)
        tmp_eq_name, tmp_eq_offset = allocate_temp(context)

        # Emit lw for left and right again
        lines.append(f"\t# {tmp_eq_name} = {left_var} == {right_var}")
        lines.append(f"\t  lw $t0, {left_offset}($fp)\t# fill {left_var} to $t0 from $fp{format_offset(left_offset)}")
        lines.append(f"\t  lw $t1, {right_offset}($fp)\t# fill {right_var} to $t1 from $fp{format_offset(right_offset)}")
        emit_relop("$t0", "$t1", "==", "$t2", lines)

        lines.append(f"\t  sw $t2, {tmp_eq_offset}($fp)\t# spill {tmp_eq_name} from $t2 to $fp{format_offset(tmp_eq_offset)}")

        # --- Merge (or) tmp_name and tmp_eq_name into a final OR
        tmp_final_name, tmp_final_offset = allocate_temp(context)

        lines.append(f"\t# {tmp_final_name} = {tmp_name} || {tmp_eq_name}")
        lines.append(f"\t  lw $t0, {tmp_offset}($fp)\t# fill {tmp_name}")
        lines.append(f"\t  lw $t1, {tmp_eq_offset}($fp)\t# fill {tmp_eq_name}")
        lines.append(f"\t  or $t2, $t0, $t1")
        lines.append(f"\t  sw $t2, {tmp_final_offset}($fp)\t# spill {tmp_final_name} from $t2 to $fp{format_offset(tmp_final_offset)}")

        return tmp_final_name


    return tmp_name

def emit_if_statement(if_node, context):
    lines = context["lines"]
    test_expr = if_node["test"]
    then_stmt = if_node.get("then")
    else_stmt = if_node.get("else")

    # --- 1. Evaluate full relational expression ---
    tmp_cond = emit_relop_expression(test_expr, context)

    # --- 2. Label setup ---
    if_label = f"_L{context['if_counter']}"
    end_label = f"_L{context['if_counter'] + 1}"
    context["if_counter"] += 2

    # --- 3. Conditional branch ---
    lines.append(f"\t# IfZ {tmp_cond} Goto {if_label}")
    lines.append(f"\t  lw $t0, {context['temp_locations'][tmp_cond]}($fp)\t# fill {tmp_cond}")
    lines.append(f"\t  beqz $t0, {if_label}")

    # --- 4. THEN block ---
    if then_stmt:
        emit_statement(then_stmt, context)

    # --- 5. Jump over ELSE block ---
    if else_stmt:
        lines.append(f"\t  j {end_label}")

    # --- 6. ELSE label ---
    lines.append(f"{if_label}:")
    if else_stmt:
        emit_statement(else_stmt, context)
        lines.append(f"{end_label}:")

def emit_relop(left_reg, right_reg, operator, target_reg, lines):
    """
    Emits MIPS code for relational operations.
    left_reg, right_reg: $t0, $t1
    operator: "<", "<=", ">", ">=", "==", "!="
    target_reg: e.g., $t2
    """

    if operator == "<" or operator == "<=":
        lines.append(f"\t  slt {target_reg}, {left_reg}, {right_reg}")
    elif operator == ">" or operator == ">=":
        lines.append(f"\t  slt {target_reg}, {right_reg}, {left_reg}")
    elif operator == "==":
        lines.append(f"\t  seq {target_reg}, {left_reg}, {right_reg}")
    elif operator == "!=":
        lines.append(f"\t  sne {target_reg}, {left_reg}, {right_reg}")
    else:
        print(f"WARNING: Unsupported relational operator: {operator}")

def emit_load_operand(operand, dest_reg, context, lines):
    """
    Emits MIPS instructions to load an operand (FieldAccess, IntConstant, BoolConstant) into dest_reg.
    """
    if "FieldAccess" in operand:
        var_name = operand["FieldAccess"]["identifier"]
        offset = context["var_locations"].get(var_name, -4)
        lines.append(f"\t  lw {dest_reg}, {offset}($fp)\t# load {var_name}")
    elif "IntConstant" in operand:
        val = int(operand["IntConstant"]["value"])
        lines.append(f"\t  li {dest_reg}, {val}\t# load int constant {val}")
    elif "BoolConstant" in operand:
        val = 1 if operand["BoolConstant"]["value"] == "true" else 0
        lines.append(f"\t  li {dest_reg}, {val}\t# load bool constant {val}")
    else:
        print(f"WARNING: Unsupported operand type in emit_load_operand: {operand}")

