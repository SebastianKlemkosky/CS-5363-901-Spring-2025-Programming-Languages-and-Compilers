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

### **Helper Functions**

def remove_comments(source_code):
    """Removes comments while preserving line numbers."""
    source_code = re.sub(SINGLE_LINE_COMMENT, lambda m: " " * len(m.group(0)), source_code)
    source_code = re.sub(MULTI_LINE_COMMENT, lambda m: "\n" * m.group(0).count("\n"), source_code)
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
    """Matches integer, hexadecimal, and double constants."""
    
    # Check for hexadecimal numbers (0x or 0X followed by valid hexadecimal digits)
    if line[column:column+2].lower() == "0x":
        # Check if the rest of the string after 0x is valid hexadecimal digits
        if column + 2 < len(line) and (line[column + 2].isdigit() or line[column + 2].lower() in 'abcdef'):
            match = HEX_PATTERN.match(line, column)  # Match the whole hexadecimal value
            if match:
                lexeme = match.group(0)
                value = int(lexeme, 16)  # Convert to integer using base 16
                return lexeme, "T_HexConstant", value, len(lexeme)
    
    # Handle period (.) cases for floating-point numbers
    if line[column] == ".":
        # Check if the period is followed by digits (valid double case like 12.34 or 1.12)
        if column - 1 >= 0 and line[column - 1].isdigit() and column + 1 < len(line) and line[column + 1].isdigit():
            match = DOUBLE_PATTERN.match(line, column)
            if match:
                lexeme = match.group(0)
                value = float(lexeme)
                return lexeme, "T_DoubleConstant", value, len(lexeme)

        # If the period is not followed by digits (invalid period like "." or "12.")
        return ".", "T_Operator", 1  # Treat the period as a standalone operator (.)

    # Regular matching for numbers (hex, double, int)
    for pattern, token_type, converter in [
        (HEX_PATTERN, "T_HexConstant", lambda x: int(x, 16)),  # Hexadecimal handling
        (DOUBLE_PATTERN, "T_DoubleConstant", float),           # Double handling
        (INT_PATTERN, "T_IntConstant", int),                   # Integer handling
    ]:
        match = pattern.match(line, column)
        if match:
            lexeme = match.group(0)
            value = converter(lexeme)
            # Convert float to int if it has no decimal portion
            if token_type == "T_DoubleConstant" and value.is_integer():
                value = int(value)  # Remove unnecessary .0

            return lexeme, token_type, value, len(lexeme)
    
    return None

def match_operator(line, column):
    """Matches operators and punctuation."""
    match = OPERATOR_PATTERN.match(line, column)
    if match:
        lexeme = match.group(0)
        token_type = OPERATORS.get(lexeme, "Unknown")
        return lexeme, token_type, len(lexeme)
    return None

def match_identifier(line, column):
    """Matches identifiers and keywords."""
    match = IDENTIFIER_PATTERN.match(line, column)
    if match:
        lexeme = match.group(0)
        if lexeme in BOOLEAN_CONSTANTS:
            return lexeme, "T_BoolConstant", lexeme, len(lexeme)
        elif lexeme in KEYWORDS:
            return lexeme, KEYWORDS[lexeme], lexeme, len(lexeme)
        else:
            return lexeme, "T_Identifier", lexeme, len(lexeme)
    return None

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

def main():
    filename = r"pp1-post\samples\baddouble.frag"
    try:
        with open(filename, 'r') as file:
            tokens = scan(file.read())
            for token in tokens:
                if token[4] == "T_Error":  # Unterminated string case
                    print(f"\n*** Error line {token[1]}.")
                    print(f"*** {token[5]}\n")
                elif len(token) == 6 and token[4] not in KEYWORDS.values() and token[4] != 'T_Identifier':
                    print(f"{token[0]:<12} line {token[1]} cols {token[2]}-{token[3]} is {token[4]} (value = {token[5]})")
                else:
                    print(f"{token[0]:<12} line {token[1]} cols {token[2]}-{token[3]} is {token[4]}")

    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")

if __name__ == "__main__":
    main()