from lexer import tokenize

def main():
    filename = "pp1-post\samples\string.frag"  # Path to your Decaf file

    try:
        # Step 1: Tokenize the input file
        with open(filename, 'r') as file:
            code = file.read()
            tokens = tokenize(code)  # Use PLY lexer function
            for token in tokens:
                print(token)  # Print each token with the formatted output

    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")

if __name__ == "__main__":
    main()
