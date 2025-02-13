import sys

BOOLEAN_CONSTANTS = {"true", "false"}
KEYWORDS = {"void", "int", "double", "bool", "string", "null", "for", "while", "if", "else", "return", "break", "Print", "ReadInteger", "ReadLine"}

def scan(source_code):
    tokens = []
    for line_num, line in enumerate(source_code.splitlines(), start=1):
        words = line.split()
        for word in words:
            token_type = "BOOLEAN_CONSTANT" if word in BOOLEAN_CONSTANTS else ("KEYWORD" if word in KEYWORDS else "IDENTIFIER")
            tokens.append((word, line_num, 1, len(word), token_type))
    return tokens

def main():
    filename = r"pp1-post\samples\badbool.frag"
    try:
        with open(filename, 'r') as file:
            tokens = scan(file.read())
            for token in tokens:
                print(f"{token[0]:<12} line {token[1]} cols {token[2]}-{token[3]} is T_{token[4]}")
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")

if __name__ == "__main__":
    main()
