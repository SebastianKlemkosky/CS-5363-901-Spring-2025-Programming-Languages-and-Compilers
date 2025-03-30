import os
from scanner_re import tokenize
from parser import parse
from helper_functions import read_source_file

SAMPLES_DIR = r"pp2-post\samples"

def main():
    """
    Batch mode only: for each .decaf in pp2-post\samples, compile and compare with .out.
    If there's a difference, also print the first line that differs ignoring trailing space.
    """
    decaf_files = [f for f in os.listdir(SAMPLES_DIR) if f.endswith(".decaf")]
    
    if not decaf_files:
        print(f"No .decaf files found in {SAMPLES_DIR}.")
        return
    
    for decaf_name in decaf_files:
        decaf_path = os.path.join(SAMPLES_DIR, decaf_name)
        base_name = decaf_name[:-6]  # e.g. "functions" for "functions.decaf"
        out_name = base_name + ".out"
        out_path = os.path.join(SAMPLES_DIR, out_name)

        # If there's no .out file, just warn
        if not os.path.exists(out_path):
            print(f"[WARNING] No corresponding .out for {decaf_name}. Skipping compare.")
            continue
        
        # 1) Compile the .decaf in memory
        actual_output = compile_in_memory(decaf_path)

        # 2) Read the expected .out
        with open(out_path, "r", encoding="utf-8") as f:
            expected_output = f.read()

        # 3) Compare
        if actual_output == expected_output:
            print(f"[PASS] {decaf_name} => EXACT match with {out_name}")
        else:
            # check if differs only by whitespace
            if differs_only_in_whitespace(actual_output, expected_output):
                print(f"[ALMOST] {decaf_name} differs only by whitespace from {out_name}")
            else:
                print(f"[FAIL] {decaf_name} => text differs from {out_name}")
                print_first_mismatch_line(expected_output, actual_output)

def compile_in_memory(file_path):
    """
    Compile a single .decaf file in memory using scanner -> parser -> AST string or error.
    Returns the compiler's output (a string).
    """
    source_code = read_source_file(file_path)
    tokens = tokenize(source_code)
    ast_output = parse(tokens)
    return ast_output

def differs_only_in_whitespace(s1, s2):
    """
    Returns True if s1, s2 differ only by whitespace,
    e.g. indentation or trailing spaces. Otherwise False.
    """
    s1_norm = [" ".join(line.strip().split()) for line in s1.splitlines()]
    s2_norm = [" ".join(line.strip().split()) for line in s2.splitlines()]
    return s1_norm == s2_norm

def print_first_mismatch_line(expected, actual):
    """
    Prints the first line where 'expected' and 'actual' differ beyond trailing whitespace.
    We'll compare line by line, ignoring trailing spaces. The first mismatch is displayed.
    """
    expected_lines = expected.splitlines()
    actual_lines   = actual.splitlines()

    # Compare line by line up to min(len, len)
    min_len = min(len(expected_lines), len(actual_lines))
    for i in range(min_len):
        # Remove trailing whitespace (rstrip), but keep indentation in front
        e_stripped = expected_lines[i].rstrip()
        a_stripped = actual_lines[i].rstrip()

        if e_stripped != a_stripped:
            print(f"First difference at line {i+1}:")
            print(f"Expected: {repr(expected_lines[i])}")
            print(f"Actual:   {repr(actual_lines[i])}")
            return

    # If all corresponding lines match ignoring trailing space,
    # but lengths differ, mention that
    if len(expected_lines) != len(actual_lines):
        print("Mismatch in line count. One file has more lines than the other.")
    else:
        print("No textual mismatch found (this is unexpected if we're in FAIL mode).")

if __name__ == "__main__":
    main()
