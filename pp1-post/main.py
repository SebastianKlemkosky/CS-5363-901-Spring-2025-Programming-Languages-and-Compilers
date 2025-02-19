from scanner_re import tokenize, KEYWORDS
import os

def main2():
    """Runs lexer tests on all .frag files in /samples and compares with expected .out files."""
    directory = r"pp1-post\samples"
    
    for filename in os.listdir(directory):
        if filename.endswith(".frag"):  # Process only .frag files
            frag_file = os.path.join(directory, filename)
            out_file = os.path.join(directory, filename.replace(".frag", ".out"))
            
            try:
                # Read input .frag file
                with open(frag_file, 'r') as file:
                    tokens = tokenize(file.read())

                # Generate actual output
                actual_output = []
                for token in tokens:
                    if token[4] == 'T_Error':
                        actual_output.append(f"\n*** Error line {token[1]}.")
                        actual_output.append(f"*** {token[5]}\n")
                        continue   

                    if token[4] not in KEYWORDS.values() and token[4] != 'T_Identifier ' and token[5] != None: 
                        actual_output.append(f"{token[0]:<12} line {token[1]} cols {token[2]}-{token[3]} is {token[4]} (value = {token[5]})")
                        continue
                    actual_output.append(f"{token[0]:<12} line {token[1]} cols {token[2]}-{token[3]} is {token[4]} ")

                # Read expected .out file
                with open(out_file, 'r') as expected_file:
                    expected_output = expected_file.read().strip().split("\n")

                # Convert actual output to a list of lines
                actual_output_lines = "\n".join(actual_output).strip().split("\n")

                # Compare line by line
                if actual_output_lines != expected_output:
                    print(f"\n❌ Mismatch in file: {filename}")

                    # Print out the first line where they differ
                    for i, (expected_line, actual_line) in enumerate(zip(expected_output, actual_output_lines)):
                        if expected_line != actual_line:
                            print(f"   Expected [{i+1}]: {repr(expected_line)}")
                            print(f"   Got      [{i+1}]: {repr(actual_line)}\n")
                            break  # Stop at first mismatch

                else:
                    print(f"✅ {filename} matches expected output.")

            except FileNotFoundError:
                print(f"⚠️ Missing .out file for: {filename}")

def main():
    filename = r"pp1-post\samples\badpre.frag"
    try:
        with open(filename, 'r') as file:
            tokens = tokenize(file.read())
            for token in tokens:
                # First, check for T_Error and handle it
                if token[4] == 'T_Error':
                    print(f"\n*** Error line {token[1]}.")
                    print(f"*** {token[5]}\n")
                    continue  

                # If it's not an error token, process normal tokens
                if token[4] not in KEYWORDS.values() and token[4] != 'T_Identifier' and token[5] != None:
                    print(f"{token[0]:<12} line {token[1]} cols {token[2]}-{token[3]} is {token[4]} (value = {token[5]})")
                    continue

                print(f"{token[0]:<12} line {token[1]} cols {token[2]}-{token[3]} is {token[4]} ")

    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")

if __name__ == "__main__":
    main2()


