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
    "||": "T_Or", "<=": "T_LessEqual", ">=": "T_GreaterEqual", "==": "T_Equal",
    "+": "+", "-": "-", "*": "*", "/": "/",
    "<": "<", ">": ">", "=": "=", ";": ";", ",": ",", "!": "!",
    "{": "{", "}": "}", "(": "(", ")": ")"
}

# **Updated Number & String Patterns**
HEX_PATTERN = re.compile(r"\b0[xX][0-9a-fA-F]+\b")  # Hexadecimal numbers
INT_PATTERN = re.compile(r"\b\d+\b")  # Decimal integers
DOUBLE_PATTERN = re.compile(r"\b\d+\.\d*(E[+-]?\d+)?\b", re.IGNORECASE)  # Floating-point numbers
STRING_PATTERN = re.compile(r'"([^"\n]*)"')  # Matches string constants (no newlines)
SINGLE_LINE_COMMENT = re.compile(r"//.*")  # Matches `//` comments
MULTI_LINE_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)  # Matches `/* ... */` comments

def scan(source_code):
    tokens = []
    identifier_pattern = re.compile(r"[a-zA-Z][a-zA-Z0-9_]{0,30}")
    operator_pattern = re.compile(r"\|\||<=|>=|==|[+\-*/<>=;,!{}()]")

    # Replace comments with whitespace to preserve line numbers
    source_code = re.sub(SINGLE_LINE_COMMENT, lambda m: " " * len(m.group(0)), source_code)  # Replace `//...`
    source_code = re.sub(MULTI_LINE_COMMENT, lambda m: "\n" * m.group(0).count("\n"), source_code)  # Replace `/* ... */`

    lines = source_code.split("\n")  # Process input line by line
    for line_num, line in enumerate(lines, start=1):
        column = 0
        while column < len(line):
            # Match String Constants First
            string_match = STRING_PATTERN.match(line, column)
            if string_match:
                lexeme = string_match.group(0)  # Keep full `"string"`
                value = lexeme  # Preserve quotes
                tokens.append((lexeme, line_num, column + 1, column + len(lexeme), "T_StringConstant", value))
                column += len(lexeme)
                continue

            # Match Hexadecimal Constants
            hex_match = HEX_PATTERN.match(line, column)
            if hex_match:
                lexeme = hex_match.group(0)
                value = int(lexeme, 16)  # Convert hex to integer value
                tokens.append((lexeme, line_num, column + 1, column + len(lexeme), "T_HexConstant", value))
                column += len(lexeme)
                continue

            # Match Numbers (Doubles first, then Integers)
            double_match = DOUBLE_PATTERN.match(line, column)
            if double_match:
                lexeme = double_match.group(0)
                value = float(lexeme)
                if value.is_integer():
                    value = int(value)  # Convert to int if no decimal part

                tokens.append((lexeme, line_num, column + 1, column + len(lexeme), "T_DoubleConstant", value))
                column += len(lexeme)
                continue

            int_match = INT_PATTERN.match(line, column)
            if int_match:
                lexeme = int_match.group(0)
                value = int(lexeme)  # Convert integer to remove leading zeros
                tokens.append((lexeme, line_num, column + 1, column + len(lexeme), "T_IntConstant", value))
                column += len(lexeme)
                continue

            # Match Operators & Punctuation
            op_match = operator_pattern.match(line, column)
            if op_match:
                op = op_match.group(0)
                token_type = OPERATORS.get(op, "Unknown")

                # Add quotes only for single-character symbols
                if len(op) == 1:
                    token_type = f"'{token_type}'"

                tokens.append((op, line_num, column + 1, column + len(op), token_type))
                column += len(op)
                continue
            
            # Match Identifiers, Keywords, and Boolean Constants
            match = identifier_pattern.match(line, column)
            if match:
                lexeme = match.group(0)
                if lexeme in BOOLEAN_CONSTANTS:
                    tokens.append((lexeme, line_num, column + 1, column + len(lexeme), "T_BoolConstant", lexeme))
                elif lexeme in KEYWORDS:
                    tokens.append((lexeme, line_num, column + 1, column + len(lexeme), KEYWORDS[lexeme]))
                else:
                    tokens.append((lexeme, line_num, column + 1, column + len(lexeme), "T_Identifier"))
                
                column += len(lexeme)
                continue
            
            column += 1  # Move to next character if no match

    return tokens

def main():
    filename = r"pp1-post\samples\comment.frag"
    try:
        with open(filename, 'r') as file:
            tokens = scan(file.read())
            for token in tokens:
                if len(token) == 6:
                    print(f"{token[0]:<12} line {token[1]} cols {token[2]}-{token[3]} is {token[4]} (value = {token[5]})")
                else:
                    print(f"{token[0]:<12} line {token[1]} cols {token[2]}-{token[3]} is {token[4]}")
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")

if __name__ == "__main__":
    main()