Author: Sebastian Klemkosky
UTSA ID: lmo120
Course: CS-5363-901-Spring 2025 - Programming Languages and Compilers

Steps:
1. Ensure Python 3.9 or greater is Installed:

2. Dependencies:
This project relies on standard Python libraries, so no additional installations are required. 
The following libraries are imported in the project:

os – for interacting with the operating system
argparse – for parsing command-line arguments
re – for regular expression-based tokenization
string – for string manipulation tasks
sys – for low-level system operations like exiting the program
contextlib – for safely redirecting standard output (redirect_stdout)
pprint – for pretty-printing complex data structures like the AST

These libraries are part of Python's standard library and should already be available in your environment.

Program Files
main.py – Entry point that runs the scanner and parser on a .decaf file and prints the AST or error.
scanner_re.py – Uses regular expressions to tokenize Decaf source code.
parser.py – Recursively parses tokens to build and validate an AST, reporting syntax errors.
format_nodes.py – Formats the AST into a readable string with proper indentation and line numbers.
helper_functions.py – Utility functions for token handling, AST construction, and error tracking.
semantic_analyzer.py - Performs semantic checking on the AST.
code_generation.py - Converts AST into MIPS Assembly (.s file). Handles full Decaf constructs including if-statements, loops, function calls, arithmetic expressions, etc.

3. Building the Project:
Run the following command in the terminal to execute the build.sh script:

./workdir/build.sh 

This should output:

	This project was developed using Python 3.13.3.
	This project uses only standard Python libraries.

4. Running the Program:
Place the source code file (e.g., example.decaf) in the appropriate folder.

Run the following command in the terminal:

./workdir/exec.sh <path_to_source_file>

Example:
To analyze a file named t1.decaf located in the samples directory, run:
./workdir/exec.sh samples/t1.decaf > output.s

Concatenate the standard Decaf preamble (defs.asm) with your output into a final file final.s 
that can be loaded in SPIM or QtSPIM.

cat defs.asm output.s > final.s

5. Expected Output:
	# standard Decaf preamble 
	  .text
	  .align 2
	  .globl main
  main:
    # BeginFunc 24
	  subu $sp, $sp, 8  # decrement sp to make space to save ra, fp
	  sw $fp, 8($sp)    # save fp
	  sw $ra, 4($sp)    # save ra
	  addiu $fp, $sp, 8 # set up new fp
	  subu $sp, $sp, 24 # decrement sp to make space for locals/temps
	# _tmp0 = "hello"
	  .data		    # create string constant marked with label
	  _string1: .asciiz "hello"
	  .text
	  la $t2, _string1	# load label
	  sw $t2, -16($fp)	# spill _tmp0 from $t2 to $fp-16
	# s = _tmp0
	  lw $t2, -16($fp)	# fill _tmp0 to $t2 from $fp-16
	  sw $t2, -12($fp)	# spill s from $t2 to $fp-12
...