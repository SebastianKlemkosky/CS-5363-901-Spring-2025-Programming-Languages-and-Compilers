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


3. Building the Project:
Run the following command in the terminal to execute the build.sh script:

./workdir/build.sh 

This should output:

This project was developed using Python 3.11.9.
This project uses only standard Python libraries.

4. Running the Program:
Place the source code file (e.g., example.decaf) in the appropriate folder.

Run the following command in the terminal:

./workdir/exec.sh <path_to_source_file>

Example:
To analyze a file named program.decaf located in the samples directory, run:
./workdir/exec.sh samples/program.decaf 

5. Expected Output:
You should get an output similar to this:
int          line 1 cols 1-3 is T_Int
a            line 1 cols 5-5 is T_Identifier
;            line 1 cols 6-6 is ';'
void         line 3 cols 1-4 is T_Void
main         line 3 cols 6-9 is T_Identifier
(            line 3 cols 10-10 is '('
)            line 3 cols 11-11 is ')'
...