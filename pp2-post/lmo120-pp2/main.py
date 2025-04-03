from scanner_re import tokenize, KEYWORDS
from parser import parse
from helper_functions import read_source_file
import sys
from contextlib import redirect_stdout
import argparse


def main():
    parser = argparse.ArgumentParser(description='Process a source code file.')
    parser.add_argument('file', type=str, help='Path to the source code file')
    args = parser.parse_args()

    source_code = read_source_file(args.file)
    tokens = tokenize(source_code)
    ast_output = parse(tokens)
    print(ast_output)


if __name__ == "__main__":
    main()
