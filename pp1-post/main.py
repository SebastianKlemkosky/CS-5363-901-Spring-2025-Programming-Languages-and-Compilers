import sys
import re

BOOLEAN_CONSTANTS = {"true": "T_BoolConstant", "false": "T_BoolConstant"}
KEYWORDS = {"void": "T_Void", "int": "T_Int", "double": "T_Double", "bool": "T_Bool", "string": "T_String", "null": "T_Null", "for": "T_For", "while": "T_While", "if": "T_If", "else": "T_Else", "return": "T_Return", "break": "T_Break", "Print": "T_Print", "ReadInteger": "T_ReadInteger", "ReadLine": "T_ReadLine"}

TOKEN_PATTERN = re.compile(r"\b(true|false)\b|\b(void|int|double|bool|string|null|for|while|if|else|return|break|Print|ReadInteger|ReadLine)\b|\b\w+\b")

def scan(source_code):
    tokens = []
    for line_num, line in enumerate(source_code.splitlines(), start=1):
        for match in TOKEN_PATTERN.finditer(line):
            word = match.group()
            if word in BOOLEAN_CONSTANTS:
                token_type = BOOLEAN_CONSTANTS[word]
                tokens.append((word, line_num, match.start() + 1, match.end(), token_type, word))
                continue
            elif word in KEYWORDS:
                token_type = KEYWORDS[word]
            else:
                token_type = "T_Identifier"
            tokens.append((word, line_num, match.start() + 1, match.end(), token_type))
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
