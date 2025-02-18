import ply.lex as lex
import string
import re

# Reserved Keywords
KEYWORDS = {
    "void": "T_Void", "int": "T_Int", "double": "T_Double", "bool": "T_Bool", "string": "T_String",
    "null": "T_Null", "for": "T_For", "while": "T_While", "if": "T_If", "else": "T_Else",
    "return": "T_Return", "break": "T_Break", "Print": "T_Print", "ReadInteger": "T_ReadInteger",
    "ReadLine": "T_ReadLine"
}

# Boolean Constants
BOOLEAN_CONSTANTS = {"true", "false"}

# Operators & Punctuation (PLY Requires Valid Token Names)
OPERATORS = {
    "||": "T_Or", "<=": "T_LessEqual", ">=": "T_GreaterEqual", "==": "T_Equal"
}

tokens = [
    "T_Identifier", "T_IntConstant", "T_HexConstant", "T_DoubleConstant",
    "T_StringConstant", "T_BoolConstant", "T_Error"
] + list(KEYWORDS.values()) + ["T_Or", "T_LessEqual", "T_GreaterEqual", "T_Equal"]

# Regex Patterns
HEX_PATTERN = re.compile(r"\b0[xX][0-9a-fA-F]+\b")
INT_PATTERN = re.compile(r"\b\d+\b")
DOUBLE_PATTERN = re.compile(r"'\d*\.\d+([eE][+-]?\d+)?'")
STRING_PATTERN = re.compile(r'"([^"\\\n]*(\\.[^"\\\n]*)*)"')
SINGLE_LINE_COMMENT = re.compile(r"//.*")
MULTI_LINE_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
IDENTIFIER_PATTERN = re.compile(r"[a-zA-Z][a-zA-Z0-9_]{0,30}")
OPERATOR_PATTERN = re.compile(r"\|\||<=|>=|==|[+\-*/<>=;,!{}()]")
UNTERMINATED_STRING_PATTERN = re.compile(r'"[^"\n]*$')



# Define literals for single-character operators
literals = "+-*/<>=;,!{}()."

# Identifier Pattern
t_T_Identifier = r'[a-zA-Z_][a-zA-Z0-9_]*'

# Operator Token Definitions (Only Multi-Character)
t_T_Or = r'\|\|'
t_T_LessEqual = r'<='
t_T_GreaterEqual = r'>='
t_T_Equal = r'=='

def t_error(t):
    """Handles unrecognized tokens but ignores valid whitespace."""
    if t.value[0] in " \t\r":  # Ignore whitespace
        t.lexer.skip(1)
        return
    
    print(f"Illegal character '{t.value[0]}' at line {t.lineno}")
    t.lexer.skip(1)

def t_T_Error(t):
    r'"[^"\n]*$'  # Ensures unterminated strings are only matched when valid strings fail
    t.value = "Unterminated string constant"
    return t


def t_T_StringConstant(t):
    r'"([^"\n]*)"'  # Matches valid strings while ensuring they don't span lines
    return t


# Build the Lexer
lexer = lex.lex()

### **Helper Functions**

def remove_comments(source_code):

    return source_code



def match_string(line, column):
    """Matches valid and unterminated string constants."""
    match = STRING_PATTERN.match(line, column)  # Check for valid strings
    if match:
        lexeme = match.group(0)
        return lexeme, "T_StringConstant", lexeme, len(lexeme)

    # Check for unterminated strings (no closing quote)
    unterminated_match = UNTERMINATED_STRING_PATTERN.match(line, column)
    if unterminated_match:
        lexeme = unterminated_match.group(0)
        return lexeme, "T_Error", f"Unterminated string constant: {lexeme}", len(lexeme)

    return None

def match_number(line, column):

    
    return None

def match_operator(line, column):
    """Matches both multi-character and single-character operators using PLY."""
    
    # First, check multi-character operators (PLY rules)
    lexer.input(line[column:])  
    token = lexer.token()
    if token and token.value in OPERATORS:
        return token.value, OPERATORS[token.value], len(token.value)

    # If not a multi-character operator, check single-character literals
    if line[column] in literals:
        return line[column], line[column], 1  # Return the character as its own token

    return None

def match_identifier(line, column):
    """Matches identifiers and keywords using PLY."""
    lexer.input(line[column:])  # Set PLY lexer input from the current column
    token = lexer.token()  # Get the next token
    if token:
        if token.value in KEYWORDS:
            return token.value, KEYWORDS[token.value], token.value, len(token.value)
        elif token.value in BOOLEAN_CONSTANTS:
            return token.value, "T_BoolConstant", token.value, len(token.value)
        else:
            return token.value, "T_Identifier", token.value, len(token.value)
    return None

def tokenize(source_code):
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

