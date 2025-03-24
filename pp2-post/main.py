from scanner_re import tokenize, KEYWORDS
from parser import parse

def read_source_file(path):
    """Reads the source code from a file."""
    try:
        with open(path, 'r') as file:
            return file.read()
    except FileNotFoundError:
        print(f"Error: File '{path}' not found.")
        exit(1)

def main():
    # Hardcoded file path for now
    file_path = r"pp2-post\samples\simple.decaf"

    # Step 1: Read file contents
    source_code = read_source_file(file_path)

    # Step 2: Scanner Phase
    tokens = tokenize(source_code)  # Tokenize the source code
    
    # Step 3: Parser Phase
    
    ast = parse(tokens)
    print(ast)   

if __name__ == "__main__":
    main()
