# code_generation.py
from helper_functions import calculate_frame_size, allocate_temp, get_print_function_for_type, get_var_type, format_relop_comment, format_offset, allocate_label

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
    label_counter = 0
    for node in ast_root["Program"]:
        if "FnDecl" in node:
            fn_decl = node["FnDecl"]
            fn_lines, temp_counter, label_counter = emit_function(fn_decl, temp_counter, label_counter)
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

def emit_function(fn_decl, temp_counter, label_counter):
    fn_name = fn_decl["identifier"]["Identifier"]["name"]

    # Create context for this function
    context = {
        "var_locations": {},
        "var_types": {},
        "temp_locations": {},
        "constant_temps": set(),
        "string_table": {},
        "string_counter": 1,
        "temp_counter": temp_counter,
        "offset": -8,  # locals grow downward
        "lines": [],
        "label_counter": label_counter

    }

    # --- Handle function parameters ---
    formal_offset = 4
    for formal in fn_decl.get("formals", []):
        if "VarDecl" in formal:
            formal_name = formal["VarDecl"]["identifier"]["Identifier"]["name"]
            formal_type = formal["VarDecl"]["type"]["Type"]

            context["var_locations"][formal_name] = formal_offset
            context["var_types"][formal_name] = formal_type

            formal_offset += 4  # next parameter at +4 bytes higher

    # --- Walk and emit all body statements ---
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

    return lines, context["temp_counter"], context["label_counter"]

def emit_statement(stmt, context):
  
    if "VarDecl" in stmt:
        emit_vardecl(stmt["VarDecl"], context)

    elif "AssignExpr" in stmt:
        emit_assign_expression(stmt["AssignExpr"], context)

    elif "PrintStmt" in stmt:
        emit_print_statement(stmt["PrintStmt"], context)

    elif "ReturnStmt" in stmt:
        emit_return_statement(stmt["ReturnStmt"], context)

    elif "IfStmt" in stmt:
        emit_if_statement(stmt["IfStmt"], context)

    elif "ForStmt" in stmt:
        emit_for_statement(stmt["ForStmt"], context)

    elif "WhileStmt" in stmt:
        emit_while_statement(stmt["WhileStmt"], context)
       
    elif "BreakStmt" in stmt:
        emit_break_statement(stmt["BreakStmt"], context)
        
    elif "ContinueStmt" in stmt:
        emit_continue_statement(stmt["ContinueStmt"], context)
        
    elif "StmtBlock" in stmt:
        for sub_stmt in stmt["StmtBlock"]:
            emit_statement(sub_stmt, context)
    else:
        print(f"WARNING: Unhandled statement: {stmt}")

def emit_vardecl(vardecl_node, context):
    lines = context["lines"]
    var_name = vardecl_node["identifier"]
    var_type = vardecl_node["type"]

    # Assign space in frame
    offset = context["offset"]
    context["offset"] -= 4
    context["var_locations"][var_name] = offset

    # 🔥 Save type information
    context["var_types"][var_name] = var_type

def emit_assign_expression(assign_node, context):
    """
    Emits code for an assignment expression (e.g., x = 5, x = y + 1, x = f(), x = a + b).
    Handles IntConstant, StringConstant, Call, ArithmeticExpr.
    """
    lines = context["lines"]
    target = assign_node["target"]["FieldAccess"]["identifier"]
    value = assign_node["value"]

    if "IntConstant" in value:
        val = int(value["IntConstant"]["value"])
        
        tmp_name, tmp_offset = allocate_temp(context)

        lines.append(f"\t# {tmp_name} = {val}")
        lines.append(f"\t  li $t2, {val}\t    # load constant value {val} into $t2")
        lines.append(f"\t  sw $t2, {tmp_offset}($fp)\t# spill {tmp_name} from $t2 to $fp{format_offset(tmp_offset)}")

        target_offset = context["var_locations"].get(target, -4)
        lines.append(f"\t# {target} = {tmp_name}")
        lines.append(f"\t  lw $t2, {tmp_offset}($fp)\t# fill {tmp_name} to $t2 from $fp{format_offset(tmp_offset)}")
        lines.append(f"\t  sw $t2, {target_offset}($fp)\t# spill {target} from $t2 to $fp{format_offset(target_offset)}")

    elif "StringConstant" in value:
        emit_assign_string_constant(assign_node, context)

    elif "Call" in value:
        emit_assign_call(assign_node, context)

    elif "ArithmeticExpr" in value:
        arith = value["ArithmeticExpr"]
        left = arith["left"]
        right = arith["right"]
        op = arith["operator"]

        # --- FIRST: handle right if constant (special case for step like n = n + 1)
        right_is_const = "IntConstant" in right

        if right_is_const:
            const_val = int(right["IntConstant"]["value"])
            tmp_const_name, tmp_const_offset = allocate_temp(context)

            lines.append(f"\t# {tmp_const_name} = {const_val}")
            lines.append(f"\t  li $t2, {const_val}\t    # load constant value {const_val} into $t2")
            lines.append(f"\t  sw $t2, {tmp_const_offset}($fp)\t# spill {tmp_const_name} from $t2 to $fp{format_offset(tmp_const_offset)}")

            tmp_result_name, tmp_result_offset = allocate_temp(context)
            lines.append(f"\t# {tmp_result_name} = {left['FieldAccess']['identifier']} {op} {tmp_const_name}")

            left_var, left_offset = emit_load_operand(left, "$t0", context, lines)
            lines.append(f"\t  lw $t1, {tmp_const_offset}($fp)\t# fill {tmp_const_name} to $t1 from $fp{format_offset(tmp_const_offset)}")

            if op == "+":
                lines.append(f"\t  add $t2, $t0, $t1")
            elif op == "-":
                lines.append(f"\t  sub $t2, $t0, $t1")
            elif op == "*":
                lines.append(f"\t  mul $t2, $t0, $t1")
            elif op == "/":
                lines.append(f"\t  div $t2, $t0, $t1")
            else:
                lines.append(f"\t  # unsupported operator {op}")

            lines.append(f"\t  sw $t2, {tmp_result_offset}($fp)\t# spill {tmp_result_name} from $t2 to $fp{format_offset(tmp_result_offset)}")

        else:
            # --- NORMAL case (both are vars, no extra temp for constant needed)
            left_var, left_offset = emit_load_operand(left, "$t0", context, lines)
            right_var, right_offset = emit_load_operand(right, "$t1", context, lines)

            tmp_result_name, tmp_result_offset = allocate_temp(context)
            lines.append(f"\t# {tmp_result_name} = {left_var} {op} {right_var}")

            if op == "+":
                lines.append(f"\t  add $t2, $t0, $t1")
            elif op == "-":
                lines.append(f"\t  sub $t2, $t0, $t1")
            elif op == "*":
                lines.append(f"\t  mul $t2, $t0, $t1")
            elif op == "/":
                lines.append(f"\t  div $t2, $t0, $t1")
            else:
                lines.append(f"\t  # unsupported operator {op}")

            lines.append(f"\t  sw $t2, {tmp_result_offset}($fp)\t# spill {tmp_result_name} from $t2 to $fp{format_offset(tmp_result_offset)}")

        # --- assign temp into target
        target_offset = context["var_locations"].get(target, -4)
        lines.append(f"\t# {target} = {tmp_result_name}")
        lines.append(f"\t  lw $t2, {tmp_result_offset}($fp)\t# fill {tmp_result_name} to $t2 from $fp{format_offset(tmp_result_offset)}")
        lines.append(f"\t  sw $t2, {target_offset}($fp)\t# spill {target} from $t2 to $fp{format_offset(target_offset)}")

    elif "FieldAccess" in value:
        source_var = value["FieldAccess"]["identifier"]
        source_offset = context["var_locations"].get(source_var, -4)
        target_offset = context["var_locations"].get(target, -4)

        lines.append(f"\t# {target} = {source_var}")
        lines.append(f"\t  lw $t2, {source_offset}($fp)\t# fill {source_var} to $t2 from $fp{format_offset(source_offset)}")
        lines.append(f"\t  sw $t2, {target_offset}($fp)\t# spill {target} from $t2 to $fp{format_offset(target_offset)}")

    else:
        print(f"WARNING: Unhandled assignment value: {value}")

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

            context["constant_temps"].add(tmp_name)

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

def OLD_emit_function_call_Old(call_node, tmp_name=None, tmp_offset=None, context=None, allocate_inner_constants=True):
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
            print(f"[emit_function_call] Allocated constant temp: {tmp_name_const}")   # <-- 🧠 ADD THIS

            context["constant_temps"].add(tmp_name_const)
            
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

            # 🔥 Allocate a temp for the constant
            if allocate_inner_constants or tmp_name is None or tmp_offset is None:
                tmp_right_name, tmp_right_offset = allocate_temp(context)
            else:
                tmp_right_name, tmp_right_offset = tmp_name, tmp_offset

                
            context["constant_temps"].add(tmp_right_name)

            lines.append(f"\t# {tmp_right_name} = {right_val}")
            lines.append(f"\t  li $t2, {right_val}\t    # load constant value {right_val} into $t2")
            lines.append(f"\t  sw $t2, {tmp_right_offset}($fp)\t# spill {tmp_right_name} from $t2 to $fp{format_offset(tmp_right_offset)}")


            # 🔥 Allocate a temp for the result of the operation (e.g., _tmp6 = n - _tmp5)
            temp_name, temp_offset = allocate_temp(context)

            lines.append(f"\t# {temp_name} = {left} {op} {tmp_right_name}")
            lines.append(f"\t  lw $t0, {left_offset}($fp)\t# fill {left} to $t0 from $fp{format_offset(left_offset)}")
            lines.append(f"\t  lw $t1, {tmp_right_offset}($fp)\t# fill {tmp_right_name} to $t1 from $fp{format_offset(tmp_right_offset)}")

            if op == "+":
                lines.append(f"\t  add $t2, $t0, $t1")
            elif op == "-":
                lines.append(f"\t  sub $t2, $t0, $t1")
            elif op == "*":
                lines.append(f"\t  mul $t2, $t0, $t1")
            elif op == "/":
                lines.append(f"\t  div $t2, $t0, $t1")

            lines.append(f"\t  sw $t2, {temp_offset}($fp)\t# spill {temp_name} from $t2 to $fp{format_offset(temp_offset)}")

            # 🔥 Push this temp as param
            lines.append(f"\t# PushParam {temp_name}")
            emit_push_param(lines, temp_offset, temp_name)

        else:
            print(f"WARNING: Complex function call argument not handled: {arg}")

    # --- Call function ---
    tmp_result_name, tmp_result_offset = allocate_temp(context)

    lines.append(f"\t# {tmp_result_name} = LCall _{func_name}")
    lines.append(f"\t  jal _{func_name}\t    # jump to function")
    lines.append(f"\t  move $t2, $v0\t    # copy function return value from $v0")
    lines.append(f"\t  sw $t2, {tmp_result_offset}($fp)\t# spill {tmp_result_name} from $t2 to $fp{format_offset(tmp_result_offset)}")

    # --- Pop parameters ---
    if args:
        lines.append(f"\t# PopParams {len(args) * 4}")
        lines.append(f"\t  add $sp, $sp, {len(args) * 4}\t# pop params off stack")

    return tmp_result_name, tmp_result_offset

def emit_function_call(call_node, tmp_name=None, tmp_offset=None, context=None, allocate_inner_constants=True):
    lines = context["lines"]
    func_name = call_node["identifier"]
    args = call_node.get("actuals", [])

    # --- Push parameters (reversed order) ---
    for arg in reversed(args):
        emit_argument(arg, context, tmp_name, tmp_offset, allocate_inner_constants)

   
    tmp_name, tmp_offset = allocate_temp(context)

    lines.append(f"\t# {tmp_name} = LCall _{func_name}")
    lines.append(f"\t  jal _{func_name}\t    # jump to function")
    lines.append(f"\t  move $t2, $v0\t    # copy function return value from $v0")
    lines.append(f"\t  sw $t2, {tmp_offset}($fp)\t# spill {tmp_name} from $t2 to $fp{format_offset(tmp_offset)}")

    # --- Pop parameters ---
    if args:
        lines.append(f"\t# PopParams {len(args) * 4}")
        lines.append(f"\t  add $sp, $sp, {len(args) * 4}\t# pop params off stack")

    return tmp_name, tmp_offset

def emit_argument(arg, context, tmp_name=None, tmp_offset=None, allocate_inner_constants=True):
    lines = context["lines"]

    if "FieldAccess" in arg:
        var = arg["FieldAccess"]["identifier"]
        var_offset = context["var_locations"].get(var, -4)

        lines.append(f"\t# PushParam {var}")
        emit_push_param(lines, var_offset, var)

    elif "IntConstant" in arg:
        value = int(arg["IntConstant"]["value"])
        tmp_name, tmp_offset = allocate_temp(context)
        context["constant_temps"].add(tmp_name)

        lines.append(f"\t# {tmp_name} = {value}")
        lines.append(f"\t  li $t2, {value}\t# load const {value}")
        lines.append(f"\t  sw $t2, {tmp_offset}($fp)\t# spill {tmp_name}")
        emit_push_param(lines, tmp_offset, tmp_name)

    elif "BoolConstant" in arg:
        value = arg["BoolConstant"]["value"]
        bool_val = 1 if value == "true" else 0
        tmp_name, tmp_offset = allocate_temp(context)
        context["constant_temps"].add(tmp_name)

        lines.append(f"\t# {tmp_name} = {bool_val}")
        lines.append(f"\t  li $t2, {bool_val}\t# load bool const {bool_val}")
        lines.append(f"\t  sw $t2, {tmp_offset}($fp)\t# spill {tmp_name}")
        emit_push_param(lines, tmp_offset, tmp_name)

    elif "ArithmeticExpr" in arg:
        arith = arg["ArithmeticExpr"]
        left = arith["left"]["FieldAccess"]["identifier"]
        right_val = int(arith["right"]["IntConstant"]["value"])
        op = arith["operator"]

        left_offset = context["var_locations"].get(left, -4)

        tmp_right_name, tmp_right_offset = tmp_name, tmp_offset
        if tmp_right_name is None or tmp_right_offset is None:
            tmp_right_name, tmp_right_offset = allocate_temp(context)

        context["constant_temps"].add(tmp_right_name)

        lines.append(f"\t# {tmp_right_name} = {right_val}")
        lines.append(f"\t  li $t2, {right_val}\t    # load constant value {right_val} into $t2")
        lines.append(f"\t  sw $t2, {tmp_right_offset}($fp)\t# spill {tmp_right_name} from $t2 to $fp{format_offset(tmp_right_offset)}")

        temp_name, temp_offset = allocate_temp(context)

        lines.append(f"\t# {temp_name} = {left} {op} {tmp_right_name}")
        lines.append(f"\t  lw $t0, {left_offset}($fp)\t# fill {left} to $t0 from $fp{format_offset(left_offset)}")
        lines.append(f"\t  lw $t1, {tmp_right_offset}($fp)\t# fill {tmp_right_name} to $t1 from $fp{format_offset(tmp_right_offset)}")

        if op == "+":
            lines.append(f"\t  add $t2, $t0, $t1")
        elif op == "-":
            lines.append(f"\t  sub $t2, $t0, $t1")
        elif op == "*":
            lines.append(f"\t  mul $t2, $t0, $t1")
        elif op == "/":
            lines.append(f"\t  div $t2, $t0, $t1")
        
        lines.append(f"\t  sw $t2, {temp_offset}($fp)\t# spill {temp_name} from $t2 to $fp{format_offset(temp_offset)}")
        lines.append(f"\t# PushParam {temp_name}")
        emit_push_param(lines, temp_offset, temp_name)

    elif "Call" in arg:
        tmp_call_name, tmp_call_offset = emit_function_call(arg["Call"], context=context)
        lines.append(f"\t# PushParam {tmp_call_name}")
        emit_push_param(lines, tmp_call_offset, tmp_call_name)

    elif "RelationalExpr" in arg:
        tmp_relop = emit_relop_expression(arg, context)
        tmp_offset = context["temp_locations"][tmp_relop]
        lines.append(f"\t# PushParam {tmp_relop}")
        emit_push_param(lines, tmp_offset, tmp_relop)
    
    elif "LogicalExpr" in arg:
        tmp_logic = emit_logical_expression(arg, context)
        tmp_offset = context["temp_locations"][tmp_logic]

        lines.append(f"\t# PushParam {tmp_logic}")
        emit_push_param(lines, tmp_offset, tmp_logic)

    else:
        print(f"WARNING: Complex function call argument not handled: {arg}")

def emit_print_statement(print_stmt, context):
    lines = context["lines"]

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
            print_fn = type_to_print_fn.get(var_type, "_PrintInt")

            lines.append(f"\t# PushParam {var_name}")
            emit_push_param(lines, offset, var_name)

            lines.append(f"\t# LCall {print_fn}")
            lines.append(f"\t  jal {print_fn}        # jump to function")

            lines.append(f"\t# PopParams 4")
            lines.append(f"\t  add $sp, $sp, 4\t# pop params off stack")

        elif "StringConstant" in arg:
            value = arg["StringConstant"]["value"]

            # Create a string label
            label_name = f"_string{context['string_counter']}"
            context['string_table'][label_name] = value
            context['string_counter'] += 1

            tmp_name, tmp_offset = allocate_temp(context)

            lines.append(f"\t# {tmp_name} = {value}")
            lines.append("\t  .data \t    # create string constant marked with label")
            lines.append(f"\t  {label_name}: .asciiz {value}")
            lines.append("\t  .text")
            lines.append(f"\t  la $t2, {label_name}\t# load label")
            lines.append(f"\t  sw $t2, {tmp_offset}($fp)\t# spill {tmp_name} from $t2 to $fp{format_offset(tmp_offset)}")

            lines.append(f"\t# PushParam {tmp_name}")
            emit_push_param(lines, tmp_offset, tmp_name)

            lines.append(f"\t# LCall _PrintString")
            lines.append(f"\t  jal _PrintString      # jump to function")
            
            lines.append(f"\t# PopParams 4")
            lines.append(f"\t  add $sp, $sp, 4\t# pop params off stack")

        elif "Call" in arg:
            call_node = arg["Call"]

            if tmp_name is None and tmp_offset is None:
                tmp_name, tmp_offset = allocate_temp(context)

            tmp_name, tmp_offset = emit_function_call(call_node, tmp_name, tmp_offset, context)

            lines.append(f"\t# PushParam {tmp_name}")
            emit_push_param(lines, tmp_offset, tmp_name)

            lines.append(f"\t# LCall _PrintInt")
            lines.append(f"\t  jal _PrintInt         # jump to function")

            lines.append(f"\t# PopParams 4")
            lines.append(f"\t  add $sp, $sp, 4\t# pop params off stack")


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
        lines.append(f"\t  lw $t0, {tmp_offset}($fp)\t# fill {tmp_name} to $t0 from $fp{format_offset(tmp_offset)}")
        lines.append(f"\t  lw $t1, {tmp_eq_offset}($fp)\t# fill {tmp_eq_name} to $t1 from $fp{format_offset(tmp_eq_offset)}")
        lines.append(f"\t  or $t2, $t0, $t1")
        lines.append(f"\t  sw $t2, {tmp_final_offset}($fp)\t# spill {tmp_final_name} from $t2 to $fp{format_offset(tmp_final_offset)}")

        return tmp_final_name

    return tmp_name

def emit_logical_expression(expr, context):
    """
    Emits MIPS instructions for a LogicalExpr.
    Returns temp name holding 0/1 result.
    """
    lines = context["lines"]

    if "LogicalExpr" not in expr:
        raise ValueError("emit_logical_expression expected LogicalExpr")

    logic = expr["LogicalExpr"]
    op = logic["operator"]

    # Handle 'right' always
    right_expr = logic["right"]
    right_tmp = None

    if "LogicalExpr" in right_expr:
        right_tmp = emit_logical_expression(right_expr, context)
    elif "RelationalExpr" in right_expr:
        right_tmp = emit_relop_expression(right_expr, context)
    elif "BoolConstant" in right_expr:
        val = 1 if right_expr["BoolConstant"]["value"] == "true" else 0
        right_tmp, right_offset = allocate_temp(context)
        lines.append(f"\t# {right_tmp} = {val}")
        lines.append(f"\t  li $t2, {val}")
        lines.append(f"\t  sw $t2, {right_offset}($fp)\t# spill {right_tmp}")
        context["constant_temps"].add(right_tmp)
        context["temp_locations"][right_tmp] = right_offset
    else:
        print(f"WARNING: LogicalExpr right operand not handled yet: {right_expr}")

    right_offset = context["temp_locations"][right_tmp]

    # If binary op (&& or ||)
    if op in ("&&", "||"):
        left_expr = logic["left"]
        left_tmp = None

        if "LogicalExpr" in left_expr:
            left_tmp = emit_logical_expression(left_expr, context)
        elif "RelationalExpr" in left_expr:
            left_tmp = emit_relop_expression(left_expr, context)
        elif "BoolConstant" in left_expr:
            val = 1 if left_expr["BoolConstant"]["value"] == "true" else 0
            left_tmp, left_offset = allocate_temp(context)
            lines.append(f"\t# {left_tmp} = {val}")
            lines.append(f"\t  li $t2, {val}")
            lines.append(f"\t  sw $t2, {left_offset}($fp)\t# spill {left_tmp}")
            context["constant_temps"].add(left_tmp)
            context["temp_locations"][left_tmp] = left_offset
        else:
            print(f"WARNING: LogicalExpr left operand not handled yet: {left_expr}")

        left_offset = context["temp_locations"][left_tmp]

        result_tmp, result_offset = allocate_temp(context)
        lines.append(f"\t# {result_tmp} = {left_tmp} {op} {right_tmp}")
        lines.append(f"\t  lw $t0, {left_offset}($fp)")
        lines.append(f"\t  lw $t1, {right_offset}($fp)")

        if op == "&&":
            lines.append(f"\t  and $t2, $t0, $t1")
        elif op == "||":
            lines.append(f"\t  or $t2, $t0, $t1")

        lines.append(f"\t  sw $t2, {result_offset}($fp)\t# spill {result_tmp}")
        context["temp_locations"][result_tmp] = result_offset
        return result_tmp

    # If unary op (!)
    elif op == "!":
        result_tmp, result_offset = allocate_temp(context)
        lines.append(f"\t# {result_tmp} = !{right_tmp}")
        lines.append(f"\t  lw $t0, {right_offset}($fp)")

        # Manual NOT: 
        #  if t0 == 0 -> 1, else 0
        lines.append(f"\t  seqz $t2, $t0\t# NOT operation")
        lines.append(f"\t  sw $t2, {result_offset}($fp)\t# spill {result_tmp}")
        context["temp_locations"][result_tmp] = result_offset
        return result_tmp

    else:
        raise ValueError(f"Unsupported LogicalExpr operator: {op}")

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

def emit_load_operand(operand, dest_reg, context, lines=None):
    """
    Emits MIPS instructions to load an operand (FieldAccess, IntConstant, BoolConstant) into dest_reg,
    only if `lines` is provided. Otherwise just returns the (var_name, var_offset) without emitting.
    """

    if "FieldAccess" in operand:
        var_name = operand["FieldAccess"]["identifier"]
        offset = context["var_locations"].get(var_name, 4)   # ✅ default positive 4

        if lines is not None and dest_reg is not None:
            lines.append(f"\t  lw {dest_reg}, {offset}($fp)\t# fill {var_name} to {dest_reg} from $fp{format_offset(offset)}")

        return var_name, offset

    elif "IntConstant" in operand:
        val = int(operand["IntConstant"]["value"])

        if lines is not None and dest_reg is not None:
            lines.append(f"\t  li {dest_reg}, {val}\t# load int constant {val} into {dest_reg}")

        return val, None

    elif "BoolConstant" in operand:
        val = 1 if operand["BoolConstant"]["value"] == "true" else 0

        if lines is not None and dest_reg is not None:
            lines.append(f"\t  li {dest_reg}, {val}\t# load bool constant {val} into {dest_reg}")

        return val, None
    
    elif "Call" in operand:
        # Recursive function call inside an expression
        tmp_call_name, tmp_call_offset = emit_function_call(operand["Call"], context=context)
        if lines is not None and dest_reg is not None:
            lines.append(f"\t  lw {dest_reg}, {tmp_call_offset}($fp)\t# fill {tmp_call_name} to {dest_reg} from $fp{format_offset(tmp_call_offset)}")
        return tmp_call_name, tmp_call_offset

    else:
        print(f"WARNING: Unsupported operand type in emit_load_operand: {operand}")
        return None, None

def emit_if_statement(if_node, context):
    lines = context["lines"]
    test_expr = if_node["test"]
    then_stmt = if_node.get("then")
    else_stmt = if_node.get("else")

    # --- 1. Evaluate the condition ---
    if "RelationalExpr" in test_expr:
        tmp_cond = emit_relop_expression(test_expr, context)
        tmp_offset = context["temp_locations"][tmp_cond]
    elif "LogicalExpr" in test_expr:
        tmp_cond = emit_logical_expression(test_expr, context)
        tmp_offset = context["temp_locations"][tmp_cond]
    elif "FieldAccess" in test_expr:
        var = test_expr["FieldAccess"]["identifier"]
        tmp_cond = var
        tmp_offset = context["var_locations"].get(var, -4)
    else:
        raise ValueError(f"Unsupported if test expression: {test_expr}")

    # --- 2. Label setup ---
    label_true, label_false = allocate_label(context)

    # --- 3. Conditional branch ---
    lines.append(f"\t# IfZ {tmp_cond} Goto {label_true}")
    lines.append(f"\t  lw $t0, {tmp_offset}($fp)\t# fill {tmp_cond} to $t0 from $fp{format_offset(tmp_offset)}")
    lines.append(f"\t  beqz $t0, {label_true}\t# branch if {tmp_cond} is zero")

    # --- 4. THEN block ---
    if then_stmt:
        emit_statement(then_stmt, context)

    # --- 5. Jump over ELSE block ---
    if else_stmt:
        lines.append(f"    # Goto {label_false}")
        lines.append(f"\t  b {label_false}\t    # unconditional branch")

    # --- 6. ELSE label ---
    lines.append(f"  {label_true}:")
    if else_stmt:
        emit_statement(else_stmt, context)
        lines.append(f"{label_false}:")

def emit_for_statement(for_node, context):
    lines = context["lines"]

    init = for_node.get("init")
    test = for_node.get("test")
    step = for_node.get("step")
    body = for_node.get("body")

    # --- 1. Labels
    label_true, label_false = allocate_label(context)

    # --- 2. Emit initialization (only once)
    if init:
        emit_assign_expression(init["AssignExpr"], context)  # <--- unwrap AssignExpr

    # --- 3. Label: Start of loop
    lines.append(f"  {label_true}:")

    # --- 4. Emit test (conditional jump out)
    if test:
        if "RelationalExpr" in test:
            tmp_cond = emit_relop_expression(test, context)
            tmp_offset = context["temp_locations"][tmp_cond]
        elif "LogicalExpr" in test:
            tmp_cond = emit_logical_expression(test, context)
            tmp_offset = context["temp_locations"][tmp_cond]
        elif "FieldAccess" in test:
            var = test["FieldAccess"]["identifier"]
            tmp_cond = var
            tmp_offset = context["var_locations"].get(var, -4)
        else:
            raise ValueError(f"Unsupported for loop test expression: {test}")

        lines.append(f"\t# IfZ {tmp_cond} Goto {label_false}")
        lines.append(f"\t  lw $t0, {tmp_offset}($fp)\t# fill {tmp_cond} to $t0 from $fp{format_offset(tmp_offset)}")
        lines.append(f"\t  beqz $t0, {label_false}\t# branch if {tmp_cond} is zero")

    old_break_label = context.get("break_label")
    old_continue_label = context.get("continue_label")
    context["break_label"] = label_false
    context["continue_label"] = label_true

    # --- 5. Emit body (loop body)
    if body:
        emit_statement(body, context)

    context["break_label"] = old_break_label
    context["continue_label"] = old_continue_label

    # --- 6. Emit step (correct handling for n = n + 1)
    if step:
        #lines.append(f"START")
        emit_assign_expression(step["AssignExpr"], context)


    # --- 7. Jump back to start
    lines.append(f"\t# Goto {label_true}")
    lines.append(f"\t  b {label_true}\t    # unconditional branch")

    # --- 8. Label: End of loop
    lines.append(f"  {label_false}:")

def emit_while_statement(while_node, context):
    """
    Emits MIPS instructions for a WhileStmt node.
    """
    lines = context["lines"]

    test = while_node.get("test")
    body = while_node.get("body")

    # --- 1. Labels
    label_true, label_false = allocate_label(context)

    # --- 2. Label: Start of loop
    lines.append(f"  {label_true}:")

    # --- 3. Emit test (conditional branch)
    if test:
        if "RelationalExpr" in test:
            tmp_cond = emit_relop_expression(test, context)
            tmp_offset = context["temp_locations"][tmp_cond]
        elif "LogicalExpr" in test:
            tmp_cond = emit_logical_expression(test, context)
            tmp_offset = context["temp_locations"][tmp_cond]
        elif "FieldAccess" in test:
            var = test["FieldAccess"]["identifier"]
            tmp_cond = var
            tmp_offset = context["var_locations"].get(var, -4)
        else:
            raise ValueError(f"Unsupported while test expression: {test}")

        lines.append(f"\t# IfZ {tmp_cond} Goto {label_false}")
        lines.append(f"\t  lw $t0, {tmp_offset}($fp)\t# fill {tmp_cond} to $t0 from $fp{format_offset(tmp_offset)}")
        lines.append(f"\t  beqz $t0, {label_false}\t# branch if {tmp_cond} is zero")


    old_break_label = context.get("break_label")
    old_continue_label = context.get("continue_label")
    context["break_label"] = label_false
    context["continue_label"] = label_true

    # --- Emit body (loop body)
    if body:
        emit_statement(body, context)

    # --- Restore previous break/continue labels
    context["break_label"] = old_break_label
    context["continue_label"] = old_continue_label

    # --- 5. Jump back to start
    lines.append(f"\t# Goto {label_true}")
    lines.append(f"\t  b {label_true}\t   # unconditional branch")

    # --- 6. Label: End of loop
    lines.append(f"{label_false}:")

def emit_break_statement(context):
    """
    Emits MIPS code for a break statement inside a loop.
    """
    lines = context["lines"]

    if context.get("break_label") is None:
        print("WARNING: 'break' used outside a loop!")
        return

    lines.append(f"\t# Break: jump to {context['break_label']}")
    lines.append(f"\t  b {context['break_label']}\t    # break jumps to end of loop")

def emit_continue_statement(context):
    """
    Emits MIPS code for a continue statement inside a loop.
    """
    lines = context["lines"]

    if context.get("continue_label") is None:
        print("WARNING: 'continue' used outside a loop!")
        return

    lines.append(f"\t# Continue: jump to {context['continue_label']}")
    lines.append(f"\t  b {context['continue_label']}\t    # continue jumps to start of loop")

def old_emit_return_statement(return_stmt, context):
    lines = context["lines"]
    expr = return_stmt["expr"]

    if "IntConstant" in expr:
        value = int(expr["IntConstant"]["value"])
        tmp_name, tmp_offset = allocate_temp(context)
        #print(f"RETURN statement allocating: {tmp_name}")

        lines.append(f"\t# {tmp_name} = {value}")
        lines.append(f"\t  li $t2, {value}\t    # load constant value {value} into $t2")
        lines.append(f"\t  sw $t2, {tmp_offset}($fp)\t# spill {tmp_name} from $t2 to $fp{format_offset(tmp_offset)}")

        lines.append(f"\t# Return {tmp_name}")
        lines.append(f"\t  lw $t2, {tmp_offset}($fp)\t# fill {tmp_name} to $t2 from $fp{format_offset(tmp_offset)}")
        lines.append(f"\t  move $v0, $t2\t    # assign return value into $v0")

        # Inline epilogue
        lines.extend(emit_epilogue_lines(add_end_comment=False))
        return

    # --- Existing CASE: Return an ArithmeticExpr ---
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
            tmp_name_call, tmp_offset_call = allocate_temp(context)
            tmp_name_call, tmp_offset_call = emit_function_call(call_node, tmp_name_call, tmp_offset_call, context, False)

            right_var = tmp_name_call
            b_offset = tmp_offset_call
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
            lines.append(f"\t  lw $t0, {a_offset}($fp)\t# fill {left_var} to $t0 from $fp{format_offset(a_offset)}")
        else:
            lines.append(f"\t  li $t0, {left_var}\t# load const {left_var} into $t0")

        if b_offset is not None:
            lines.append(f"\t  lw $t1, {b_offset}($fp)\t# fill {right_var} to $t1 from $fp{format_offset(b_offset)}")
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

def emit_return_statement(return_stmt, context):
    lines = context["lines"]
    expr = return_stmt["expr"]

    # --- CASE 1: Return an IntConstant directly ---
    if "IntConstant" in expr:
        value = int(expr["IntConstant"]["value"])
        tmp_name, tmp_offset = allocate_temp(context)

        lines.append(f"\t# {tmp_name} = {value}")
        lines.append(f"\t  li $t2, {value}\t    # load constant value {value} into $t2")
        lines.append(f"\t  sw $t2, {tmp_offset}($fp)\t# spill {tmp_name} from $t2 to $fp{format_offset(tmp_offset)}")

        lines.append(f"\t# Return {tmp_name}")
        lines.append(f"\t  lw $t2, {tmp_offset}($fp)\t# fill {tmp_name} to $t2 from $fp{format_offset(tmp_offset)}")
        lines.append(f"\t  move $v0, $t2\t    # assign return value into $v0")

        lines.extend(emit_epilogue_lines(add_end_comment=False))
        return

    # --- CASE 2: Return an ArithmeticExpr (like a + 2) ---
    if "ArithmeticExpr" in expr:
        arith = expr["ArithmeticExpr"]
        left = arith["left"]
        right = arith["right"]
        op = arith["operator"]

        # === Step 1: Handle right operand ===
        right_var, right_offset = emit_load_operand(right, None, context)  # no emission

        if right_offset is None:
            # It's a constant, we need to allocate and spill
            right_tmp, right_tmp_offset = allocate_temp(context)
            lines.append(f"\t# {right_tmp} = {right_var}")
            lines.append(f"\t  li $t2, {right_var}\t    # load constant value {right_var} into $t2")
            lines.append(f"\t  sw $t2, {right_tmp_offset}($fp)\t# spill {right_tmp} from $t2 to $fp{format_offset(right_tmp_offset)}")
            right_var = right_tmp
            right_offset = right_tmp_offset

        # === Step 2: Handle left operand ===
        left_var, left_offset = emit_load_operand(left, None, context)  # no emission

        # === Step 3: Allocate result temp ===
        result_tmp, result_offset = allocate_temp(context)

        lines.append(f"\t# {result_tmp} = {left_var} {op} {right_var}")
        lines.append(f"\t  lw $t0, {left_offset}($fp)\t# fill {left_var} to $t0 from $fp{format_offset(left_offset)}")
        lines.append(f"\t  lw $t1, {right_offset}($fp)\t# fill {right_var} to $t1 from $fp{format_offset(right_offset)}")

        if op == "+":
            lines.append(f"\t  add $t2, $t0, $t1")
        elif op == "-":
            lines.append(f"\t  sub $t2, $t0, $t1")
        elif op == "*":
            lines.append(f"\t  mul $t2, $t0, $t1")
        elif op == "/":
            lines.append(f"\t  div $t2, $t0, $t1")
        else:
            lines.append(f"\t  # unsupported operator: {op}")

        lines.append(f"\t  sw $t2, {result_offset}($fp)\t# spill {result_tmp} from $t2 to $fp{format_offset(result_offset)}")

        # === Step 4: Return result ===
        lines.append(f"\t# Return {result_tmp}")
        lines.append(f"\t  lw $t2, {result_offset}($fp)\t# fill {result_tmp} to $t2 from $fp{format_offset(result_offset)}")
        lines.append(f"\t  move $v0, $t2\t# assign return value into $v0")

        lines.extend(emit_epilogue_lines(add_end_comment=False))
        return
