def main():
    # Hardcoded file path for now
    file_path = r"pp2-post\samples\control.decaf"

    # Step 1: Read file contents
    source_code = read_source_file(file_path)

    # Step 2: Scanner Phase
    tokens = tokenize(source_code)

    # Step 3: Parser Phase
    ast_output = parse(tokens)  # Can be either a string (error) or formatted AST
    print(ast_output)

    # Save output to file (whether error or AST)
    with open(r"pp2-post\output.txt", "w") as f:
        with redirect_stdout(f):
            print(ast_output)