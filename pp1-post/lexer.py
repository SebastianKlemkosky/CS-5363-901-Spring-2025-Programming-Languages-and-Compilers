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

# Track line numbers for each token
def t_newline(t):
    r'\n+'
    t.lineno += t.value.count("\n")  # Increment line number based on the number of newline characters

# Error handling rule
def t_error(t):
    print(f"Illegal character '{t.value[0]}'")
    t.lexer.skip(1)

# Build the lexer
lexer = lex.lex()



# Function to tokenize the input code and format output
def scan(source_code):
    """Scans source code and returns tokens."""
    tokens = []
    source_code = remove_comments(source_code)
    lines = source_code.split("\n")

    for line_num, line in enumerate(lines, start=1):
        column = 0

        # Check for # directives (e.g., #define)
        if line.strip().startswith("#"):
            # Report invalid # directive
            tokens.append((line.strip(), line_num, 1, len(line.strip()), "T_Error", "Invalid # directive"))
            continue  # Skip the rest of the line

        while column < len(line):
            # Check for string constants
            result = match_string(line, column)
            if result:
                if len(result) == 3:  # Valid string
                    lexeme, value, length = result
                    tokens.append((lexeme, line_num, column + 1, column + length, "T_StringConstant", value))
                elif len(result) == 4:  # Unterminated string
                    lexeme, token_type, error_message, length = result
                    tokens.append((lexeme, line_num, column + 1, column + length, token_type, error_message))
                column += length
                continue

            # Check for numbers (hex, double, int)
            result = match_number(line, column)
            if result:
                if len(result) == 4:  # Valid double
                    lexeme, token_type, value, length = result
                    tokens.append((lexeme, line_num, column + 1, column + length, token_type, value))
                    column += length
                elif len(result) == 3:  # Invalid double
                    lexeme, token_type, length = result
                    token_type = OPERATORS.get(lexeme, "Unknown")
                    tokens.append((lexeme, line_num, column + 1, column + length, token_type))
                    column += length
                continue

            # Check for operators & punctuation
            result = match_operator(line, column)
            if result:
                lexeme, token_type, length = result
                tokens.append((lexeme, line_num, column + 1, column + length, token_type))
                column += length
                continue

            # Check for identifiers & keywords
            result = match_identifier(line, column)
            if result:
                lexeme, token_type, value, length = result
                tokens.append((lexeme, line_num, column + 1, column + length, token_type, value))
                column += length
                continue

            # Check for invalid characters (unrecognized)
            invalid_char = line[column]
            if invalid_char not in string.whitespace and not invalid_char.isalnum() and invalid_char not in OPERATORS and invalid_char not in KEYWORDS:
                # Add error for unrecognized character
                tokens.append((invalid_char, line_num, column + 1, column + 1, "T_Error", f"Unrecognized char: '{invalid_char}'"))
            
            column += 1  # Move to next character if no match

    return tokens
