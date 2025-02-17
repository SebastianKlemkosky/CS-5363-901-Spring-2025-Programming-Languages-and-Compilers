import ply.lex as lex

# Reserved keywords in Decaf 22
reserved = {
    'void': 'T_Void', 'int': 'T_Int', 'double': 'T_Double', 'bool': 'T_Bool', 'string': 'T_String',
    'null': 'T_Null', 'for': 'T_For', 'while': 'T_While', 'if': 'T_If', 'else': 'T_Else',
    'return': 'T_Return', 'break': 'T_Break', 'Print': 'T_Print', 'ReadInteger': 'T_ReadInteger',
    'ReadLine': 'T_ReadLine'
}

# List of token names (including reserved keywords)
tokens = [
    'T_Identifier', 'T_IntConstant', 'T_DoubleConstant', 'T_StringConstant',
    'T_Operator', 'T_LParen', 'T_RParen', 'T_LBrace', 'T_RBrace', 'T_Semicolon',
    'T_Comma', 'T_BoolConstant'
] + list(reserved.values())  # Add reserved keywords

# Regular expressions for basic tokens
t_T_Identifier = r'[a-zA-Z_][a-zA-Z0-9_]*'  # Match identifiers
t_T_IntConstant = r'\d+'  # Integer constants
t_T_DoubleConstant = r'\d*\.\d+([eE][+-]?\d+)?'  # Double constants (with optional scientific notation)
t_T_StringConstant = r'"([^"\\\n]*(\\.[^"\\\n]*)*)"'  # String constants (escaping allowed)
t_T_Operator = r'[+\-*/%=<>&|!^]'
t_T_LParen = r'\('
t_T_RParen = r'\)'
t_T_LBrace = r'\{'
t_T_RBrace = r'\}'
t_T_Semicolon = r';'
t_T_Comma = r','

# Boolean constants (true/false)
t_T_BoolConstant = r'(true|false)'

# Skip whitespace (space, tab, newline)
t_ignore = ' \t\n\r'

# Handle comments (both single-line and multi-line comments)
t_ignore_COMMENT = r'//.*'  # Single-line comment
t_ignore_COMMENT_MULTI = r'/\*.*?\*/'  # Multi-line comment

# Error handling rule
def t_error(t):
    print(f"Illegal character '{t.value[0]}'")
    t.lexer.skip(1)

# Build the lexer
lexer = lex.lex()

# Function to tokenize the input code and format output
def tokenize(code):
    lexer.input(code)
    tokens = []
    while True:
        tok = lexer.token()
        if not tok:
            break
        # Format output in the requested format
        tokens.append(f'{tok.value}      line {tok.lineno} cols {tok.lexpos + 1}-{tok.lexpos + len(tok.value)} is {tok.type} (value = {tok.value})')
    return tokens
