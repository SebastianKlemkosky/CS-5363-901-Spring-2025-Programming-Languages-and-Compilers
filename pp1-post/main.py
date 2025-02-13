import sys

BOOLEAN_CONSTANTS = {"true", "false"}
KEYWORDS = {"void", "int", "double", "bool", "string", "null", "for", "while", "if", "else", "return", "break", "Print", "ReadInteger", "ReadLine"}
OPERATORS = set("+-*/%<>=!&|;,.(){}")

def scan(source_code):
    tokens = []
    lines = source_code.splitlines()
    
    for line_num, line in enumerate(lines, start=1):
        index = 0
        while index < len(line):
            char = line[index]
            
            if char.isspace():
                index += 1
            elif char.isalpha() or char == '_':
                start = index
                while index < len(line) and (line[index].isalnum() or line[index] == '_'):
                    index += 1
                identifier = line[start:index]
                token_type = "BOOLEAN_CONSTANT" if identifier in BOOLEAN_CONSTANTS else ("KEYWORD" if identifier in KEYWORDS else "IDENTIFIER")
                tokens.append((identifier, line_num, start + 1, index, token_type))
            else:
                print(f"Error: Unrecognized character '{char}' at line {line_num}, column {index+1}")
                index += 1
    return tokens

def main():
    filename = r"pp1-post\samples\badbool.frag"  # Hardcoded file path
    try:
        with open(filename, 'r') as file:
            source_code = file.read()
            tokens = scan(source_code)
            for token in tokens:
                print(f"{token[0]:<12} line {token[1]} cols {token[2]}-{token[3]} is T_{token[4]}")
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")

if __name__ == "__main__":
    main()
