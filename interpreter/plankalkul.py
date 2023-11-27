#!/usr/bin/python3

import sys
from ply import lex
import ply.yacc as yacc
import tokenizer
from parser import parser
from typechecker import typecheckAll
from run import runWhole


class TypeError(Exception):
    pass


def main():
    program = open(sys.argv[1], "r")
    code = program.read()
    program.close()
    lines = []
    try:
        p = parser.parse(code)
    except SyntaxError as s:
        return
    for i in p:
        lines.append(i)

    t, program = typecheckAll(lines)
    if not t:
        print("typcheck failed")
        return

    runWhole(program)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Wrong arguments number")
    else:
        main()
