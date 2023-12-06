#!/usr/bin/env python3

import ply.lex as lex
import sys

# List of token names. This is always required
tokens = [
   'INTEGER',
   'FLOAT',
   # 'COMPLEX',
   'PLUS',
   'MINUS',
   'TIMES',
   'DIVIDE',
   'LPAREN',
   'RPAREN',
   'LSQUBR',
   'RSQUBR',
   'LCURBR',
   'RCURBR',
   'ASSIGN',
   'IF',
   'ZVAR',
   'RVAR',
   'VVAR',
   'COMMA',
   'PRINT',
   'WHILE',
   'SEPAR',
   'FIN',
   'INDEX',
   'BOOL',
   'EQUAL',
   'GREATER',
   'LOWER',
   'PROGRAM',
   'DOT',
   'NEG',
   'PHI',
   'MI',
   'LIST_LEN'
]

# Regular expression rules for simple tokens
t_PLUS    = r'\+'
t_MINUS   = r'-'
t_TIMES   = r'\*'
t_DIVIDE  = r'/'
t_LPAREN  = r'\('
t_RPAREN  = r'\)'
t_LSQUBR  = r'\['
t_RSQUBR  = r'\]'
t_LCURBR  = r'\{'
t_RCURBR  = r'\}'
t_ASSIGN  = r'=>'
t_IF      = r'->'
t_ZVAR    = r'Z'
t_VVAR    = r'V'
t_RVAR    = r'R'
t_COMMA   = r','
t_PRINT   = r'Drucken'
t_WHILE   = r'W'
# t_SEPAR   = r'[\|\n]'
t_FIN     = r'Fin'
t_INDEX   = r'i'
t_BOOL    = r'(Ja|Nein)'
t_EQUAL   = r'='
t_GREATER = r'>'
t_LOWER   = r'<'
t_PROGRAM = r'P'
t_DOT     = r'\.'
t_NEG     = r'~'
t_PHI     = r'Phi'
t_MI      = r'mi'
t_LIST_LEN= r'N'


# def t_FLOAT(t):
#     r'[-+]?\d+\.\d+'
#     t.value = float(t.value)
#     return t


def t_INTEGER(t):
    r'-?\d+'
    return t


# Define a rule so we can track line numbers
def t_SEPAR(t):
    r'\n*([\n|]|\#.*)\n*'
    t.lexer.lineno += t.value.count('\n')
    return t


# A string containing ignored characters (spaces and tabs)
t_ignore  = ' \t'

# Error handling rule
def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)

# Build the lexer
lexer = lex.lex()

# Give the lexer some input

def tokenize(code):
    tokens = []
    lexer.input(code)

    # Tokenize
    while True:
        tok = lexer.token()
        if not tok:
            break      # No more input
        tokens.append(tok)
    return tokens
