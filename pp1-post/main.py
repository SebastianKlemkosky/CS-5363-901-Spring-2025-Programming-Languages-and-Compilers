import re

# Reserved keywords (Renamed to match expected output)
KEYWORDS = {
    "void": "T_Void", "int": "T_Int", "double": "T_Double", "bool": "T_Bool", "string": "T_String",
    "null": "T_Null", "for": "T_For", "while": "T_While", "if": "T_If", "else": "T_Else",
    "return": "T_Return", "break": "T_Break", "Print": "T_Print", "ReadInteger": "T_ReadInteger",
    "ReadLine": "T_ReadLine"
}

# Boolean Constants
BOOLEAN_CONSTANTS = {"true", "false"}

# Operators & Punctuation (Renamed to match expected output)
OPERATORS = {
    "||": "T_Or", "<=": "T_LessEqual", ">=": "T_GreaterEqual", "==": "T_Equal",
    "+": "+", "-": "-", "*": "*", "/": "/",
    "<": "<", ">": ">", "=": "=", ";": ";", ",": ",", "!": "!",
    "{": "{", "}": "}", "(": "(", ")": ")"
}

def scan(source_code):
    tokens = []
    identifier_pattern = re.compile(r"[a-zA-Z][a-zA-Z0-9_]{0,30}")
    operator_pattern = re.compile(r"\|\||<=|>=|==|[+\-*/<>=;,!{}()]")

    lines = source_code.split("\n")  # Process input line by line
    for line_num, line in enumerate(lines, start=1):
        column = 0
        while column < len(line):
            # Match Operators & Punctuation First
            op_match = operator_pattern.match(line, column)
            if op_match:
                op = op_match.group(0)
                token_type = OPERATORS.get(op, "Unknown")  # Use symbol directly if not in OPERATORS

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
    filename = r"pp1-post\samples\reserve_op.frag"
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