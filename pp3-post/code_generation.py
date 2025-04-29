# code_generation.py
from helper_functions import calculate_frame_size, allocate_temp, get_print_function_for_type, get_var_type, format_relop_comment, format_offset, allocate_label, emit_store

def generate_code(ast_root):
    lines = []

    # Step 0: Check for main
    if not any("FnDecl" in node and node["FnDecl"]["identifier"]["Identifier"]["name"] == "main"
               for node in ast_root["Program"]):
        return "*** Error.\n*** Linker: function 'main' not defined"

    # Step 1: Scan and remember global variables
    global_locations = {}
    global_offset = 0
    for node in ast_root["Program"]:
        if "VarDecl" in node:
            var_decl = node["VarDecl"]
            var_name = var_decl["identifier"]["Identifier"]["name"]
            global_locations[var_name] = global_offset
            global_offset += 4


    # Step 2: Emit preamble for text section (NO .data)
    lines.append("\t# standard Decaf preamble ")
    lines.append("\t  .text")
    lines.append("\t  .align 2")
    lines.append("\t  .globl main")

    # Step 3: Emit functions with a shared temp counter
    temp_counter = 0
    label_counter = 0
    for node in ast_root["Program"]:
        if "FnDecl" in node:
            fn_decl = node["FnDecl"]
            fn_lines, temp_counter, label_counter = emit_function(fn_decl, temp_counter, label_counter, global_locations)
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

def emit_push_param(lines, offset, var_name=None, is_global=False):
    """
    Emits MIPS instructions to push a variable or constant onto the stack.
    Handles whether it's a global or local based on is_global flag.
    """
    if var_name:
        lines.append(f"\t# PushParam {var_name}")

    lines.append("\t  subu $sp, $sp, 4\t# decrement sp to make space for param")
    if var_name:
        if is_global:
            comment_offset = f"+{offset}" if offset >= 0 else f"{offset}"
            lines.append(f"\t  lw $t0, {offset}($gp)\t# fill {var_name} to $t0 from $gp{comment_offset}")
        else:
            comment_offset = f"+{offset}" if offset >= 0 else f"{offset}"
            lines.append(f"\t  lw $t0, {offset}($fp)\t# fill {var_name} to $t0 from $fp{comment_offset}")
    else:
        comment_offset = f"+{offset}" if offset >= 0 else f"{offset}"
        lines.append(f"\t  lw $t0, {offset}($fp)\t# fill temp to $t0 from $fp{comment_offset}")
    
    lines.append("\t  sw $t0, 4($sp)\t# copy param value to stack")

def emit_function(fn_decl, temp_counter, label_counter, global_locations):
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
        "label_counter": label_counter,
        "globals": set(global_locations.keys()),  # ✅ all global names
        "global_locations": global_locations,     # ✅ all global offsets
    }

    # --- Handle function parameters ---
    formal_offset = 4
    for formal in fn_decl.get("formals", []):
        if "VarDecl" in formal:
            formal_name = formal["VarDecl"]["identifier"]["Identifier"]["name"]
            formal_type = formal["VarDecl"]["type"]["Type"]

            context["var_locations"][formal_name] = formal_offset
            context["var_types"][formal_name] = formal_type

            # ✅ Remove formal name from globals if present
            context["globals"].discard(formal_name)

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
        emit_break_statement(context)
        
    elif "ContinueStmt" in stmt:
        emit_continue_statement(context)
        
    elif "StmtBlock" in stmt:
        for sub_stmt in stmt["StmtBlock"]:
            emit_statement(sub_stmt, context)
    
    elif "Call" in stmt:
        #print(stmt["Call"])
        emit_function_call(stmt["Call"], context=context)

    else:
        print(f"WARNING: Unhandled statement: {stmt}")

def emit_vardecl(vardecl_node, context):
    lines = context["lines"]
    var_name = vardecl_node["identifier"]
    var_type = vardecl_node["type"]
    #print(f"DEBUG: Declaring variable '{var_name}' of type '{var_type}' inside {context.get('current_function', '???')}")

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

        lines.append(f"\t# {target} = {tmp_name}")
        lines.append(f"\t  lw $t2, {tmp_offset}($fp)\t# fill {tmp_name} to $t2 from $fp{format_offset(tmp_offset)}")
        emit_store(target, "$t2", context, lines)

    elif "StringConstant" in value:
        emit_assign_string_constant(assign_node, context)

    elif "Call" in value:
        emit_assign_call(assign_node, context)

    elif "ArithmeticExpr" in value:
        arith = value["ArithmeticExpr"]
        left = arith["left"]
        right = arith["right"]
        op = arith["operator"]

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

            lines.append(f"\t  sw $t2, {tmp_result_offset}($fp)\t# spill {tmp_result_name} from $fp{format_offset(tmp_result_offset)}")

        lines.append(f"\t# {target} = {tmp_result_name}")
        lines.append(f"\t  lw $t2, {tmp_result_offset}($fp)\t# fill {tmp_result_name} to $t2 from $fp{format_offset(tmp_result_offset)}")
        emit_store(target, "$t2", context, lines)

    elif "FieldAccess" in value:
        source_var = value["FieldAccess"]["identifier"]

        lines.append(f"\t# {target} = {source_var}")
        if source_var in context.get("globals", set()):
            gp_offset = context["global_locations"].get(source_var, 0)
            comment_offset = f"+{gp_offset}" if gp_offset >= 0 else f"{gp_offset}"
            lines.append(f"\t  lw $t2, {gp_offset}($gp)\t# fill {source_var} to $t2 from $gp{comment_offset}")
        else:
            source_offset = context["var_locations"].get(source_var, -4)
            comment_offset = f"+{source_offset}" if source_offset >= 0 else f"{source_offset}"
            lines.append(f"\t  lw $t2, {source_offset}($fp)\t# fill {source_var} to $t2 from $fp{comment_offset}")

        emit_store(target, "$t2", context, lines)


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
        emit_push_param(lines, tmp_offset, tmp_name)

    # Step 3: Call the function and assign to a new temp
    tmp_name, tmp_offset = allocate_temp(context)

    lines.append(f"\t# {tmp_name} = LCall _{call['identifier']}")
    lines.append(f"\t  jal _{call['identifier']}\t\t\t    # jump to function")
    lines.append(f"\t  move $t2, $v0\t    # copy function return value from $v0")
    lines.append(f"\t  sw $t2, {tmp_offset}($fp)\t# spill {tmp_name} from $t2 to $fp{tmp_offset}")

    # Step 4: Pop params
    # TODO: Fix this
    if actuals:
        lines.append(f"\t# PopParams {len(actuals) * 4}")
        lines.append(f"\t  add $sp, $sp, {len(actuals) * 4}\t# pop params off stack")

    # Step 5: Assign to target variable
    dest_offset = context["var_locations"][dest_var]
    lines.append(f"\t# {dest_var} = {tmp_name}")
    lines.append(f"\t  lw $t2, {tmp_offset}($fp)\t# fill {tmp_name} to $t2 from $fp{tmp_offset}")
    lines.append(f"\t  sw $t2, {dest_offset}($fp)\t# spill {dest_var} from $t2 to $fp{dest_offset}")

def emit_function_call(call_node, tmp_name=None, tmp_offset=None, context=None, allocate_inner_constants=True):
    lines = context["lines"]
    func_name = call_node["identifier"]

    if "actuals" not in call_node:
        raise Exception(f"Function call node missing 'actuals': {call_node}")

    args = call_node["actuals"]

    # ✅ Step 1: Decide if we should reverse arguments
    simple = True
    for arg in args:
        if any(k in arg for k in ("ArithmeticExpr", "RelationalExpr", "LogicalExpr", "Call")):
            simple = False
            break

    if simple:
        #print(f"DEBUG: Simple args detected for {func_name}, reversing arguments")
        process_args = reversed(args)
    else:
        #print(f"DEBUG: Complex args detected for {func_name}, keeping original order")
        process_args = args

    # ✅ Step 2: Compute arguments first (DO NOT push yet)
    computed_args = []  # list of (tmp_name, tmp_offset)
    for arg in process_args:
        tmp_name, tmp_offset, is_global = emit_argument(arg, context, tmp_name, tmp_offset, allocate_inner_constants)
        computed_args.append((tmp_name, tmp_offset, is_global))

    # ✅ Step 3: Push parameters (after all are computed)
    for tmp_name, tmp_offset, is_global in reversed(computed_args):
        
        emit_push_param(lines, tmp_offset, var_name=tmp_name, is_global=is_global)

    # ✅ Step 4: Allocate temp for return value
    tmp_name, tmp_offset = allocate_temp(context)

    lines.append(f"\t# {tmp_name} = LCall _{func_name}")
    lines.append(f"\t  jal _{func_name}\t\t\t    # jump to function")
    lines.append(f"\t  move $t2, $v0\t    # copy function return value from $v0")
    lines.append(f"\t  sw $t2, {tmp_offset}($fp)\t# spill {tmp_name} from $t2 to $fp{format_offset(tmp_offset)}")

    # ✅ Step 5: Pop parameters
    if args:
        lines.append(f"\t# PopParams {len(args) * 4}")
        lines.append(f"\t  add $sp, $sp, {len(args) * 4}\t# pop params off stack")

    return tmp_name, tmp_offset

def emit_argument(arg, context, tmp_name=None, tmp_offset=None, allocate_inner_constants=True):
    lines = context["lines"]

    if "FieldAccess" in arg:
        var = arg["FieldAccess"]["identifier"]

        if var in context.get("globals", set()):
            var_offset = context["global_locations"].get(var, 0)
            return var, var_offset, True  # ✅ Global
        else:
            var_offset = context["var_locations"].get(var, -4)
            return var, var_offset, False  # ✅ Local

    elif "IntConstant" in arg:
        value = int(arg["IntConstant"]["value"])
        tmp_name, tmp_offset = allocate_temp(context)
        context["constant_temps"].add(tmp_name)

        lines.append(f"\t# {tmp_name} = {value}")
        lines.append(f"\t  li $t2, {value}\t    # load constant value {value} into $t2")
        lines.append(f"\t  sw $t2, {tmp_offset}($fp)\t# spill {tmp_name} from $t2 to $fp{format_offset(tmp_offset)}")

        return tmp_name, tmp_offset, False  # Always frame pointer

    elif "BoolConstant" in arg:
        value = arg["BoolConstant"]["value"]
        bool_val = 1 if value == "true" else 0
        tmp_name, tmp_offset = allocate_temp(context)
        context["constant_temps"].add(tmp_name)

        lines.append(f"\t# {tmp_name} = {bool_val}")
        lines.append(f"\t  li $t2, {bool_val}\t    # load constant value {bool_val} into $t2")
        lines.append(f"\t  sw $t2, {tmp_offset}($fp)\t# spill {tmp_name} from $t2 to $fp{format_offset(tmp_offset)}")

        return tmp_name, tmp_offset, False  # Always frame pointer

    elif "ArithmeticExpr" in arg:
        arith = arg["ArithmeticExpr"]
        left = arith["left"]["FieldAccess"]["identifier"]
        right_val = int(arith["right"]["IntConstant"]["value"])
        op = arith["operator"]

        left_offset = context["var_locations"].get(left, -4)

        tmp_right_name, tmp_right_offset = allocate_temp(context)
        context["constant_temps"].add(tmp_right_name)

        lines.append(f"\t# {tmp_right_name} = {right_val}")
        lines.append(f"\t  li $t2, {right_val}\t    # load constant value {right_val} into $t2")
        lines.append(f"\t  sw $t2, {tmp_right_offset}($fp)\t# spill {tmp_right_name} from $t2 to $fp{format_offset(tmp_right_offset)}")

        result_tmp_name, result_tmp_offset = allocate_temp(context)

        lines.append(f"\t# {result_tmp_name} = {left} {op} {tmp_right_name}")
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

        lines.append(f"\t  sw $t2, {result_tmp_offset}($fp)\t# spill {result_tmp_name} from $t2 to $fp{format_offset(result_tmp_offset)}")

        return result_tmp_name, result_tmp_offset, False  # Always frame pointer

    elif "Call" in arg:
        tmp_call_name, tmp_call_offset = emit_function_call(arg["Call"], context=context)
        return tmp_call_name, tmp_call_offset, False  # Always frame pointer

    elif "RelationalExpr" in arg:
        tmp_relop = emit_relop_expression(arg, context)
        tmp_offset = context["temp_locations"][tmp_relop]
        return tmp_relop, tmp_offset, False  # Always frame pointer

    elif "LogicalExpr" in arg:
        tmp_logic = emit_logical_expression(arg, context)
        tmp_offset = context["temp_locations"][tmp_logic]
        return tmp_logic, tmp_offset, False  # Always frame pointer

    else:
        print(f"WARNING: Complex function call argument not handled: {arg}")
        return None, None, False

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

            #lines.append(f"\t# PushParam {var_name}")
            emit_push_param(lines, offset, var_name)

            lines.append(f"\t# LCall {print_fn}")
            lines.append(f"\t  jal {print_fn}        # jump to function")

            lines.append(f"\t# PopParams 4")
            lines.append(f"\t  add $sp, $sp, 4\t# pop params off stack")

        elif "IntConstant" in arg:
            value = int(arg["IntConstant"]["value"])
            tmp_name, tmp_offset = allocate_temp(context)
            context["constant_temps"].add(tmp_name)

            lines.append(f"\t# {tmp_name} = {value}")
            lines.append(f"\t  li $t2, {value}\t# load constant value {value}")
            lines.append(f"\t  sw $t2, {tmp_offset}($fp)\t# spill {tmp_name} from $t2 to $fp{format_offset(tmp_offset)}")

            emit_push_param(lines, tmp_offset, tmp_name)

            lines.append(f"\t# LCall _PrintInt")
            lines.append(f"\t  jal _PrintInt        # jump to function")

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

            #lines.append(f"\t# PushParam {tmp_name}")
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

            #lines.append(f"\t# PushParam {tmp_name}")
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
    if "FieldAccess" in left:
        left_var = left["FieldAccess"]["identifier"]
        if left_var in context.get("globals", set()):
            left_offset = context["global_locations"].get(left_var, 0)
            left_is_global = True
        else:
            left_offset = context["var_locations"].get(left_var, 4)
            left_is_global = False

    elif "IntConstant" in left or "BoolConstant" in left:
        val = int(left.get("IntConstant", left.get("BoolConstant"))["value"])
        tmp_left, tmp_left_offset = allocate_temp(context)

        if tmp_left not in context["constant_temps"]:
            lines.append(f"\t# {tmp_left} = {val}")
            lines.append(f"\t  li $t2, {val}\t# load constant value {val}")
            lines.append(f"\t  sw $t2, {tmp_left_offset}($fp)\t# spill {tmp_left} from $t2 to $fp{format_offset(tmp_left_offset)}")
            context["constant_temps"].add(tmp_left)

        left_var = tmp_left
        left_offset = tmp_left_offset
        left_is_global = False

    else:
        print(f"WARNING: Unsupported left operand type: {left}")
        left_var, left_offset, left_is_global = None, None, False

    # --- Load right operand ---
    if "FieldAccess" in right:
        right_var = right["FieldAccess"]["identifier"]
        if right_var in context.get("globals", set()):
            right_offset = context["global_locations"].get(right_var, 0)
            right_is_global = True
        else:
            right_offset = context["var_locations"].get(right_var, 8)
            right_is_global = False

    elif "IntConstant" in right or "BoolConstant" in right:
        val = int(right.get("IntConstant", right.get("BoolConstant"))["value"])
        tmp_right, tmp_right_offset = allocate_temp(context)

        if tmp_right not in context["constant_temps"]:
            lines.append(f"\t# {tmp_right} = {val}")
            lines.append(f"\t  li $t2, {val}\t# load constant value {val}")
            lines.append(f"\t  sw $t2, {tmp_right_offset}($fp)\t# spill {tmp_right} from $t2 to $fp{format_offset(tmp_right_offset)}")
            context["constant_temps"].add(tmp_right)

        right_var = tmp_right
        right_offset = tmp_right_offset
        right_is_global = False

    else:
        print(f"WARNING: Unsupported right operand type: {right}")
        right_var, right_offset, right_is_global = None, None, False

    # --- Allocate temp to store result ---
    tmp_name, tmp_offset = allocate_temp(context)

    # --- Emit the load instructions ---
    lines.append(format_relop_comment(tmp_name, left_var, operator, right_var))

    if left_is_global:
        lines.append(f"\t  lw $t0, {left_offset}($gp)\t# fill {left_var} to $t0 from $gp{format_offset(left_offset)}")
    else:
        lines.append(f"\t  lw $t0, {left_offset}($fp)\t# fill {left_var} to $t0 from $fp{format_offset(left_offset)}")

    if right_is_global:
        lines.append(f"\t  lw $t1, {right_offset}($gp)\t# fill {right_var} to $t1 from $gp{format_offset(right_offset)}")
    else:
        lines.append(f"\t  lw $t1, {right_offset}($fp)\t# fill {right_var} to $t1 from $fp{format_offset(right_offset)}")

    # --- Emit relational operation ---
    emit_relop("$t0", "$t1", operator, "$t2", lines)

    # --- Spill result ---
    lines.append(f"\t  sw $t2, {tmp_offset}($fp)\t# spill {tmp_name} from $t2 to $fp{format_offset(tmp_offset)}")

    # --- Handle <= or >= case by merging with ==
    if operator in ("<=", ">="):
        tmp_eq_name, tmp_eq_offset = allocate_temp(context)

        lines.append(f"\t# {tmp_eq_name} = {left_var} == {right_var}")

        if left_is_global:
            lines.append(f"\t  lw $t0, {left_offset}($gp)\t# fill {left_var} to $t0 from $gp{format_offset(left_offset)}")
        else:
            lines.append(f"\t  lw $t0, {left_offset}($fp)\t# fill {left_var} to $t0 from $fp{format_offset(left_offset)}")

        if right_is_global:
            lines.append(f"\t  lw $t1, {right_offset}($gp)\t# fill {right_var} to $t1 from $gp{format_offset(right_offset)}")
        else:
            lines.append(f"\t  lw $t1, {right_offset}($fp)\t# fill {right_var} to $t1 from $fp{format_offset(right_offset)}")

        emit_relop("$t0", "$t1", "==", "$t2", lines)
        lines.append(f"\t  sw $t2, {tmp_eq_offset}($fp)\t# spill {tmp_eq_name} from $t2 to $fp{format_offset(tmp_eq_offset)}")

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

    # If binary op (&& or ||), handle left first
    if op in ("&&", "||"):
        left_expr = logic["left"]
        right_expr = logic["right"]

        left_tmp, left_offset, left_is_global = emit_logical_operand(left_expr, context)
        right_tmp, right_offset, right_is_global = emit_logical_operand(right_expr, context)

        result_tmp, result_offset = allocate_temp(context)

        lines.append(f"\t# {result_tmp} = {left_tmp} {op} {right_tmp}")

        if left_is_global:
            lines.append(f"\t  lw $t0, {left_offset}($gp)\t# fill {left_tmp} to $t0 from $gp{format_offset(left_offset)}")
        else:
            lines.append(f"\t  lw $t0, {left_offset}($fp)\t# fill {left_tmp} to $t0 from $fp{format_offset(left_offset)}")

        if right_is_global:
            lines.append(f"\t  lw $t1, {right_offset}($gp)\t# fill {right_tmp} to $t1 from $gp{format_offset(right_offset)}")
        else:
            lines.append(f"\t  lw $t1, {right_offset}($fp)\t# fill {right_tmp} to $t1 from $fp{format_offset(right_offset)}")

        if op == "&&":
            lines.append(f"\t  and $t2, $t0, $t1")
        elif op == "||":
            lines.append(f"\t  or $t2, $t0, $t1")

        lines.append(f"\t  sw $t2, {result_offset}($fp)\t# spill {result_tmp} from $t2 to $fp{format_offset(result_offset)}")
        context["temp_locations"][result_tmp] = result_offset
        return result_tmp

    # If unary op (!)
    elif op == "!":
        right_expr = logic["right"]
        right_tmp, right_offset, right_is_global = emit_logical_operand(right_expr, context)

        # ✅ Step 1: Allocate a new temp for constant 0
        zero_tmp, zero_offset = allocate_temp(context)

        lines.append(f"\t# {zero_tmp} = 0")
        lines.append(f"\t  li $t2, 0\t    # load constant value 0")
        lines.append(f"\t  sw $t2, {zero_offset}($fp)\t# spill {zero_tmp} from $t2 to $fp{format_offset(zero_offset)}")

        # ✅ Step 2: Allocate the final result temp
        result_tmp, result_offset = allocate_temp(context)

        lines.append(f"\t# {result_tmp} = {right_tmp} == {zero_tmp}")

        if right_is_global:
            lines.append(f"\t  lw $t0, {right_offset}($gp)\t# fill {right_tmp} to $t0 from $gp{format_offset(right_offset)}")
        else:
            lines.append(f"\t  lw $t0, {right_offset}($fp)\t# fill {right_tmp} to $t0 from $fp{format_offset(right_offset)}")

        # Zero temp is always local (frame pointer)
        lines.append(f"\t  lw $t1, {zero_offset}($fp)\t# fill {zero_tmp} to $t1 from $fp{format_offset(zero_offset)}")

        lines.append(f"\t  seq $t2, $t0, $t1")
        lines.append(f"\t  sw $t2, {result_offset}($fp)\t# spill {result_tmp} from $t2 to $fp{format_offset(result_offset)}")

        context["temp_locations"][result_tmp] = result_offset
        return result_tmp


    else:
        raise ValueError(f"Unsupported LogicalExpr operator: {op}")

def emit_equality_expression(expr, context):
    """
    Emits MIPS instructions to evaluate an equality expression (== or !=).
    Returns the name of the temp (_tmpN) holding the boolean result (0/1).
    """
    lines = context["lines"]

    if "EqualityExpr" not in expr:
        raise ValueError("emit_equality_expression expected EqualityExpr")

    eq_expr = expr["EqualityExpr"]
    left = eq_expr["left"]
    right = eq_expr["right"]
    operator = eq_expr["operator"]

    # --- Load left operand ---
    if "FieldAccess" in left:
        left_var = left["FieldAccess"]["identifier"]
        if left_var in context.get("globals", set()):
            left_offset = context["global_locations"].get(left_var, 0)
            left_is_global = True
        else:
            left_offset = context["var_locations"].get(left_var, -4)
            left_is_global = False
    elif "IntConstant" in left or "BoolConstant" in left:
        val = int(left.get("IntConstant", left.get("BoolConstant"))["value"])
        tmp_left, left_offset = allocate_temp(context)
        if tmp_left not in context["constant_temps"]:
            lines.append(f"\t# {tmp_left} = {val}")
            lines.append(f"\t  li $t2, {val}\t# load constant value {val}")
            lines.append(f"\t  sw $t2, {left_offset}($fp)\t# spill {tmp_left} from $t2 to $fp{format_offset(left_offset)}")
            context["constant_temps"].add(tmp_left)
        left_var = tmp_left
        left_is_global = False
    else:
        raise ValueError(f"Unsupported left operand: {left}")

    # --- Load right operand ---
    if "FieldAccess" in right:
        right_var = right["FieldAccess"]["identifier"]
        if right_var in context.get("globals", set()):
            right_offset = context["global_locations"].get(right_var, 0)
            right_is_global = True
        else:
            right_offset = context["var_locations"].get(right_var, -4)
            right_is_global = False
    elif "IntConstant" in right or "BoolConstant" in right:
        val = int(right.get("IntConstant", right.get("BoolConstant"))["value"])
        tmp_right, right_offset = allocate_temp(context)
        if tmp_right not in context["constant_temps"]:
            lines.append(f"\t# {tmp_right} = {val}")
            lines.append(f"\t  li $t2, {val}\t# load constant value {val}")
            lines.append(f"\t  sw $t2, {right_offset}($fp)\t# spill {tmp_right} from $t2 to $fp{format_offset(right_offset)}")
            context["constant_temps"].add(tmp_right)
        right_var = tmp_right
        right_is_global = False
    else:
        raise ValueError(f"Unsupported right operand: {right}")

    # --- Allocate temp to store result ---
    tmp_name, tmp_offset = allocate_temp(context)
    lines.append(f"\t# {tmp_name} = {left_var} {operator} {right_var}")

    # --- Emit load instructions ---
    if left_is_global:
        lines.append(f"\t  lw $t0, {left_offset}($gp)\t# fill {left_var} to $t0 from $gp{format_offset(left_offset)}")
    else:
        lines.append(f"\t  lw $t0, {left_offset}($fp)\t# fill {left_var} to $t0 from $fp{format_offset(left_offset)}")

    if right_is_global:
        lines.append(f"\t  lw $t1, {right_offset}($gp)\t# fill {right_var} to $t1 from $gp{format_offset(right_offset)}")
    else:
        lines.append(f"\t  lw $t1, {right_offset}($fp)\t# fill {right_var} to $t1 from $fp{format_offset(right_offset)}")

    # --- Emit equality instruction ---
    if operator == "==":
        lines.append(f"\t  seq $t2, $t0, $t1")
    elif operator == "!=":
        lines.append(f"\t  sne $t2, $t0, $t1")
    else:
        raise ValueError(f"Unsupported equality operator: {operator}")

    # --- Spill result ---
    lines.append(f"\t  sw $t2, {tmp_offset}($fp)\t# spill {tmp_name} from $t2 to $fp{format_offset(tmp_offset)}")
    context["temp_locations"][tmp_name] = tmp_offset

    return tmp_name

def emit_logical_operand(operand, context):
    """
    Helper to emit left or right operand inside logical expressions.
    Returns (tmp_name, tmp_offset, is_global)
    """
    lines = context["lines"]

    if "LogicalExpr" in operand:
        tmp = emit_logical_expression(operand, context)
        offset = context["temp_locations"][tmp]
        return tmp, offset, False

    elif "RelationalExpr" in operand:
        tmp = emit_relop_expression(operand, context)
        offset = context["temp_locations"][tmp]
        return tmp, offset, False

    elif "FieldAccess" in operand:
        var = operand["FieldAccess"]["identifier"]
        if var in context.get("globals", set()):
            offset = context["global_locations"].get(var, 0)
            return var, offset, True
        else:
            offset = context["var_locations"].get(var, -4)
            return var, offset, False

    elif "BoolConstant" in operand:
        val = 1 if operand["BoolConstant"]["value"] == "true" else 0
        tmp, tmp_offset = allocate_temp(context)
        lines.append(f"\t# {tmp} = {val}")
        lines.append(f"\t  li $t2, {val}\t    # load constant value {val} into $t2")
        lines.append(f"\t  sw $t2, {tmp_offset}($fp)\t# spill {tmp} from $t2 to $fp{format_offset(tmp_offset)}")
        context["constant_temps"].add(tmp)
        context["temp_locations"][tmp] = tmp_offset
        return tmp, tmp_offset, False

    else:
        print(f"WARNING: emit_logical_operand: unhandled operand: {operand}")
        return None, None, False

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
    only if `lines` is provided. Otherwise just returns the (var_name, var_offset).
    """

    if "FieldAccess" in operand:
        var_name = operand["FieldAccess"]["identifier"]

        if var_name in context.get("globals", set()):
            # Global variable: load from $gp + offset
            gp_offset = context["global_locations"].get(var_name, 0)
            if lines is not None and dest_reg is not None:
                comment_offset = f"+{gp_offset}" if gp_offset >= 0 else f"{gp_offset}"
                lines.append(f"\t  lw {dest_reg}, {gp_offset}($gp)\t# fill {var_name} to {dest_reg} from $gp{comment_offset}")
            return var_name, gp_offset
        else:
            # Local variable: load from $fp + offset
            offset = context["var_locations"].get(var_name, -4)
            if lines is not None and dest_reg is not None:
                comment_offset = f"+{offset}" if offset >= 0 else f"{offset}"
                lines.append(f"\t  lw {dest_reg}, {offset}($fp)\t# fill {var_name} to {dest_reg} from $fp{comment_offset}")
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
    elif "EqualityExpr" in test_expr:
        tmp_cond = emit_equality_expression(test_expr, context)
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
        lines.append(f"  {label_false}:")

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
        elif "EqualityExpr" in test:
            tmp_cond = emit_equality_expression(test, context)
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
        elif "EqualityExpr" in test:
            tmp_cond = emit_equality_expression(test, context)
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

        # === Step 4: Load left operand ===
        if left_var in context.get("globals", set()):
            left_gp_offset = context["global_locations"].get(left_var, 0)
            comment_offset = f"+{left_gp_offset}" if left_gp_offset >= 0 else f"{left_gp_offset}"
            lines.append(f"\t  lw $t0, {left_gp_offset}($gp)\t# fill {left_var} to $t0 from $gp{comment_offset}")
        else:
            comment_offset = f"+{left_offset}" if left_offset >= 0 else f"{left_offset}"
            lines.append(f"\t  lw $t0, {left_offset}($fp)\t# fill {left_var} to $t0 from $fp{comment_offset}")

        # === Step 5: Load right operand ===
        if right_var in context.get("globals", set()):
            right_gp_offset = context["global_locations"].get(right_var, 0)
            comment_offset = f"+{right_gp_offset}" if right_gp_offset >= 0 else f"{right_gp_offset}"
            lines.append(f"\t  lw $t1, {right_gp_offset}($gp)\t# fill {right_var} to $t1 from $gp{comment_offset}")
        else:
            comment_offset = f"+{right_offset}" if right_offset >= 0 else f"{right_offset}"
            lines.append(f"\t  lw $t1, {right_offset}($fp)\t# fill {right_var} to $t1 from $fp{comment_offset}")

        # === Step 6: Perform operation ===
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

        # === Step 7: Spill result to frame ===
        lines.append(f"\t  sw $t2, {result_offset}($fp)\t# spill {result_tmp} from $t2 to $fp{format_offset(result_offset)}")

        # === Step 8: Return result ===
        lines.append(f"\t# Return {result_tmp}")
        lines.append(f"\t  lw $t2, {result_offset}($fp)\t# fill {result_tmp} to $t2 from $fp{format_offset(result_offset)}")
        lines.append(f"\t  move $v0, $t2\t    # assign return value into $v0")

        lines.extend(emit_epilogue_lines(add_end_comment=False))
        return

