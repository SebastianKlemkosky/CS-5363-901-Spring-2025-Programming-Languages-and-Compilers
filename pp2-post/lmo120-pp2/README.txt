Author: Sebastian Klemkosky
UTSA ID: lmo120
Course: CS-5363-901-Spring 2025 - Programming Languages and Compilers

Steps:
1. Ensure Python 3.x is Installed:

2. Dependencies:
This project relies on standard Python libraries, so no additional installations are required. 
The following libraries are imported in the project:

os – for interacting with the operating system
argparse – for parsing command-line arguments
re – for regular expression-based tokenization
string – for string manipulation tasks
These libraries are part of Python's standard library and should already be available in your environment.

Program Files
main.py – Entry point that runs the scanner and parser on a .decaf file and prints the AST or error.
scanner_re.py – Uses regular expressions to tokenize Decaf source code.
parser.py – Recursively parses tokens to build and validate an AST, reporting syntax errors.
format_nodes.py – Formats the AST into a readable string with proper indentation and line numbers.
helper_functions.py – Utility functions for token handling, AST construction, and error tracking.

3. Building the Project:
Run the following command in the terminal to execute the build.sh script:

./workdir/build.sh 

This should output:

	This project was developed using Python 3.13.2.
	This project uses only standard Python libraries.

4. Running the Program:
Place the source code file (e.g., example.decaf) in the appropriate folder.

Run the following command in the terminal:

./workdir/exec.sh <path_to_source_file>

Example:
To analyze a file named control.decaf located in the samples directory, run:
./workdir/exec.sh samples/control.decaf 

5. Expected Output:
Program:
  1   FnDecl:
         (return type) Type: void
  1      Identifier: main
         (body) StmtBlock:
  2         VarDecl:
               Type: int
  2            Identifier: a
  3         VarDecl:
               Type: bool
  3            Identifier: done
...