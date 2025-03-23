# parser.py

tokens = []
index = 0
current_token = None

def parse(token_stream):
    global tokens, index, current_token
    tokens = token_stream
    index = 0
    current_token = tokens[index] if tokens else None
    return parse_program()

def parse_program():
    print("=== Parsing Program ===")
    while current_token is not None:
        parse_decl()
    print("=== Done ===")

def parse_decl():
    if lookahead("T_Void") or lookahead("T_Int") or lookahead("T_Double") or lookahead("T_Bool") or lookahead("T_String"):
        # Lookahead for type or void
        type_token = current_token
        advance()

        if lookahead("T_Identifier"):
            id_token = current_token
            advance()

            if lookahead("'('"):
                # This is a FunctionDecl
                print(f"Detected FunctionDecl: return type = {type_token[0]}, name = {id_token[0]}")
                parse_function_decl()
                return

            elif lookahead("';'"):
                # This is a VariableDecl (optional for later)
                print(f"Detected VariableDecl: type = {type_token[0]}, name = {id_token[0]}")
                advance()
                return

            else:
                syntax_error("Expected '(' or ';' after identifier")
        else:
            syntax_error("Expected identifier after type/void")
    else:
        syntax_error("Expected type or 'void' at top-level declaration")

def parse_function_decl():
    advance()  # consume '('
    # Assume no params for now (we'll do Formals later)
    if lookahead("')'"):
        advance()
    else:
        syntax_error("Expected ')' after '(' in function declaration")

    if lookahead("'{'"):
        print("Entering function body...")
        parse_stmt_block()
    else:
        syntax_error("Expected '{' after function header")

def parse_stmt_block():
    advance()  # consume '{'
    while current_token is not None and not lookahead("'}'"):
        print(f"Inside block: {current_token}")
        advance()
    if lookahead("'}'"):
        print("Exiting block.")
        advance()
    else:
        syntax_error("Expected '}' at end of block")


def advance():
    global index, current_token
    index += 1
    if index < len(tokens):
        current_token = tokens[index]
    else:
        current_token = None

def lookahead(expected_type):
    global current_token
    return current_token and current_token[4] == expected_type


def syntax_error(msg="Syntax Error"):
    print(f"Error at token {current_token}: {msg}")
    exit(1)  # Optional: exit for now to stop parsing on the first error
