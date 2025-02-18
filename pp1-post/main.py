from lexer import tokenize, literals, KEYWORDS

def main():
    filename = r"pp1-post\samples\reserve_op.frag"
    try:
        with open(filename, 'r') as file:
            tokens = tokenize(file.read())
            for token in tokens:
                # Wrap single-character literals in quotes
                if token[4] in literals:
                    print(f"{token[0]:<12} line {token[1]} cols {token[2]}-{token[3]} is '{token[4]}'")
                elif len(token) == 6 and token[4] not in KEYWORDS.values() and token[4] != 'T_Identifier':
                    print(f"{token[0]:<12} line {token[1]} cols {token[2]}-{token[3]} is {token[4]} (value = {token[5]})")
                else:
                    print(f"{token[0]:<12} line {token[1]} cols {token[2]}-{token[3]} is {token[4]}")

    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")

if __name__ == "__main__":
    main()

