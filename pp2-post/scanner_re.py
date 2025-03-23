import re
import string

# Reserved keywords
KEYWORDS = {
    "void": "T_Void", "int": "T_Int", "double": "T_Double", "bool": "T_Bool", "string": "T_String",
    "null": "T_Null", "for": "T_For", "while": "T_While", "if": "T_If", "else": "T_Else",
    "return": "T_Return", "break": "T_Break", "Print": "T_Print", "ReadInteger": "T_ReadInteger",
    "ReadLine": "T_ReadLine"
}

# Boolean Constants
BOOLEAN_CONSTANTS = {"true", "false"}

# Operators & Punctuation
OPERATORS = {
    "||": "T_Or", 
    "<=": "T_LessEqual", 
    ">=": "T_GreaterEqual", 
    "==": "T_Equal",
    "+": "'+'",  
    "-": "'-'",  
    "*": "'*'",  
    "/": "'/'",  
    "<": "'<'",  
    ">": "'>'",  
    "=": "'='",  
    ";": "';'",  
    ",": "','",  
    "!": "'!'",  
    "{": "'{'",  
    "}": "'}'",  
    "(": "'('",  
    ")": "')'",
    ".": "'.'"  
}

MAX_IDENTIFIER_LENGTH = 31  #maximum length for identifiers

# Regex Patterns
HEX_PATTERN = re.compile(r'0[xX][0-9a-fA-F]+')  # hexadecimal numbers
DOUBLE_PATTERN = re.compile(r'\d+\.\d*([eE][+-]?\d+)?')  # doubles 
INT_PATTERN = re.compile(r'\d+')        # ints

STRING_PATTERN = re.compile(r'"([^"\\\n]*(\\.[^"\\\n]*)*)"')
SINGLE_LINE_COMMENT = re.compile(r"//.*")
MULTI_LINE_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
IDENTIFIER_PATTERN = re.compile(r'[a-zA-Z][a-zA-Z0-9_]*')
OPERATOR_PATTERN = re.compile(r"\|\||<=|>=|==|[+\-*/<>=;,!{}()]")
UNTERMINATED_STRING_PATTERN = re.compile(r'"[^"\n]*$')


def remove_comments(source_code):
    """Removes comments but also preserving line numbers."""
    source_code = re.sub(SINGLE_LINE_COMMENT, lambda m: " " * len(m.group(0)), source_code)
    source_code = re.sub(MULTI_LINE_COMMENT, lambda m: "\n" * m.group(0).count("\n"), source_code)
    return source_code

def match_string(line, column):
    """Matches valid and unterminated strings."""
    match = STRING_PATTERN.match(line, column)  # Check for valid strings
    if match:
        lexeme = match.group(0)
        return lexeme, "T_StringConstant", lexeme, len(lexeme)

    # Check for unterminated strings (no closing quote)
    unterminated_match = UNTERMINATED_STRING_PATTERN.match(line, column)
    if unterminated_match:
        lexeme = unterminated_match.group(0)
        return lexeme, "T_Error", "T_UNTERMINATED_STRING_CONSTANT", len(lexeme)

    return None

def match_number(line, column):
    """Matches integer, hexadecimal, and doubles using regex"""
    
    # Check for hexadecimal numbers
    match = HEX_PATTERN.match(line[column:])
    if match:
        lexeme = match.group(0)
        value = int(lexeme, 16)  # Convert to integer using base 16
        return lexeme, "T_HexConstant", value, len(lexeme)

    
    # Check for invalid .12 cases (but return . as an operator)
    if line[column] == ".":
        if column + 1 < len(line) and line[column + 1].isdigit():
            return ".","'.'"  , None, 1  #Return `.` as an operator
        
        return ".", "'.'" , None, 1  # If it's a standalone `.`

    # Check for floating-point numbers (valid doubles)
    match = DOUBLE_PATTERN.match(line[column:])
    if match:
        lexeme = match.group(0)
        value = float(lexeme)

        if value.is_integer():
            value = int(value)

        return lexeme, "T_DoubleConstant", value, len(lexeme)

    # Check for integer numbers
    match = INT_PATTERN.match(line[column:])
    if match:
        lexeme = match.group(0)
        value = int(lexeme)
        return lexeme, "T_IntConstant", value, len(lexeme)

    return None  # No match found

def match_operator(line, column):
    """Matches operators and punctuation."""
    match = OPERATOR_PATTERN.match(line, column)
    if match:
        lexeme = match.group(0)

        # Check if the lexeme is in the OPERATORS dictionary
        token_type = OPERATORS.get(lexeme, "Unknown")
        return lexeme, token_type, None, len(lexeme)
    
      # No match found
    if line[column] != " ":
        return line[column], "T_Error", "T_UNRECOGNIZED_CHAR", 1
    return None

def match_identifier(line, column):
    """Matches identifiers and keywords."""
    match = IDENTIFIER_PATTERN.match(line[column:])
    if match:
        lexeme = match.group(0)

        # Check if the identifier exceeds the max length
        if len(lexeme) > MAX_IDENTIFIER_LENGTH:
            # Return the truncated identifier with an error message #Have some identifier for this issue lexme twice
            return lexeme, "T_Error", "T_MAX_IDENTIFIER_LENGTH", len(lexeme)

        # Check if it's a boolean constant
        if lexeme in BOOLEAN_CONSTANTS:
            return lexeme, "T_BoolConstant", lexeme, len(lexeme)

        # Check if it's a keyword
        elif lexeme in KEYWORDS:
            return lexeme, KEYWORDS[lexeme], lexeme, len(lexeme)

        # Otherwise, it's a regular identifier
        return lexeme, "T_Identifier", None, len(lexeme)

    return None  # No match found

def handle_error(token):
    """Handles tokens with T_Error and formats our error message."""
    lexeme, line_num, start_col, end_col, token_type, error_message = token

    if error_message == "T_UNTERMINATED_STRING_CONSTANT":
        error_message = f"Unterminated string constant: {lexeme}"

    if error_message == "T_UNRECOGNIZED_CHAR":
        error_message = f"Unrecognized char: \'{lexeme}\'"
    
    if error_message == "T_MAX_IDENTIFIER_LENGTH":
        truncated_lexeme = lexeme[:MAX_IDENTIFIER_LENGTH]
        error_message = f"Identifier too long: \"{lexeme}\"\n"
        error_message += f"\n{lexeme:<12} line {line_num} cols {start_col}-{end_col} is T_Identifier (truncated to {truncated_lexeme})\n"
    
    if error_message == "T_INVALID_DIRECTIVE":
        error_message = f"Invalid # directive"
    
    return lexeme, line_num, start_col, end_col, token_type, error_message

def tokenize(source_code):
    """Scans source code and returns tokens."""
    tokens = []
    source_code = remove_comments(source_code)
    lines = source_code.split("\n")

    for line_num, line in enumerate(lines, start=1):
        column = 0

        # Check for # directives (e.g., #define) // MACROS
        if line.strip().startswith("#"):
            lexeme, line_num, start_col, end_col, token_type, value = handle_error((line.strip(), line_num, 1, len(line.strip()), "T_Error", "T_INVALID_DIRECTIVE"))
            tokens.append((lexeme, line_num, start_col, end_col, token_type, value))  # Append the error message
            continue  # Skip the rest of the line

        while column < len(line):
            # Check for string constants
            result = match_string(line, column)
            if result:
                lexeme, token_type, value, length = result
                start_col, end_col = column + 1, column + length
                if token_type == "T_Error":
                    lexeme, line_num, start_col, end_col, token_type, value = handle_error((lexeme, line_num, start_col, end_col, token_type, value))
                
                tokens.append((lexeme, line_num, start_col, end_col, token_type, value))
                column += length
                continue

            # Check for numbers (hex, double, int)
            result = match_number(line, column)
            if result:
                lexeme, token_type, value, length = result
                start_col, end_col = column + 1, column + length
                if token_type == "T_Error":
                    lexeme, line_num, start_col, end_col, token_type, value = handle_error((lexeme, line_num, start_col, end_col, token_type, value))
                
                tokens.append((lexeme, line_num, start_col, end_col, token_type, value))
                column += length
                continue

            # Check for identifiers & keywords
            result = match_identifier(line, column)
            if result:
                lexeme, token_type, value, length = result
                start_col, end_col = column + 1, column + length
                if token_type == "T_Error":
                    lexeme, line_num, start_col, end_col, token_type, value = handle_error((lexeme, line_num, start_col, end_col, token_type, value))
                
                tokens.append((lexeme, line_num, start_col, end_col, token_type, value))
                column += length
                continue


            # Check for operators & punctuation
            result = match_operator(line, column)
            if result:
                lexeme, token_type, value, length = result
                start_col, end_col = column + 1, column + length
                if token_type == "T_Error":
                    lexeme, line_num, start_col, end_col, token_type, value = handle_error((lexeme, line_num, start_col, end_col, token_type, value))
                
                tokens.append((lexeme, line_num, start_col, end_col, token_type, value))
                column += length
                continue

            column += 1  # Move to next character if there is no matches

    return tokens