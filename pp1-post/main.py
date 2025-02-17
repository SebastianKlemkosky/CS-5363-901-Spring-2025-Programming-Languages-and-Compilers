import re

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
DOUBLE_PATTERN = re.compile(r"\b\d+\.\d*(E[+-]?\d+)?\b", re.IGNORECASE)
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
    for pattern, token_type, converter in [
        (HEX_PATTERN, "T_HexConstant", lambda x: int(x, 16)),
        (DOUBLE_PATTERN, "T_DoubleConstant", float),
        (INT_PATTERN, "T_IntConstant", int),
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
                lexeme, token_type, value, length = result
                tokens.append((lexeme, line_num, column + 1, column + length, token_type, value))
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
            
            column += 1  # Move to next character if no match

    return tokens

def main():
    filename = r"pp1-post\samples\badop.frag"
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