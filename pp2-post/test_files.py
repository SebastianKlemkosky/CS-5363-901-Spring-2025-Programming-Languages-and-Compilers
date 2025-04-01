import os
from scanner_re import tokenize
from parser import parse
from helper_functions import read_source_file

SAMPLES_DIR = r"pp2-post\samples"

def main():
    decaf_files = [f for f in os.listdir(SAMPLES_DIR) if f.endswith(".decaf")]

    for decaf_file in decaf_files:
        decaf_path = os.path.join(SAMPLES_DIR, decaf_file)
        expected_out_path = decaf_path[:-6] + ".out"  # Replace .decaf with .out

        if not os.path.exists(expected_out_path):
            print(f"[SKIP] {decaf_file} has no matching .out file")
            continue

        # Step 1: Read file contents
        source_code = read_source_file(decaf_path)

        # Step 2: Scanner Phase
        tokens = tokenize(source_code)

        # Step 3: Parser Phase
        actual_output = parse(tokens)

        # Step 4: Read expected output
        with open(expected_out_path, "r", encoding="utf-8") as f:
            expected_output = f.read()

        # Step 5: Compare ignoring whitespace
        if normalize_output(actual_output) == normalize_output(expected_output):
            print(f"[MATCH] {decaf_file}")
        else:
            print(f"[MISMATCH] {decaf_file} does not match {os.path.basename(expected_out_path)}")
            print_first_difference(actual_output, expected_output)

def normalize_output(text):
    return [line.strip() for line in text.strip().splitlines()]

def print_first_difference(actual, expected):
    actual_lines = normalize_output(actual)
    expected_lines = normalize_output(expected)
    min_len = min(len(actual_lines), len(expected_lines))

    for i in range(min_len):
        if actual_lines[i] != expected_lines[i]:
            print(f"  Line {i + 1} differs:")
            print(f"    Expected: {repr(expected_lines[i])}")
            print(f"    Actual:   {repr(actual_lines[i])}")
            return

    # If all matched but lengths differ
    if len(actual_lines) != len(expected_lines):
        print("  Outputs differ in number of lines.")

if __name__ == "__main__":
    main()
