import ply.yacc as yacc
from syntax import *

from tokenizer import *

import sys

# start = 'statements'
start = 'program'


def p_program(p):
    '''program : SEPAR program
               | subprogram SEPAR empty
               | subprogram SEPAR program'''

    if len(p) == 3:
        p[0] = p[2]
    elif p[3] is None:
        p[0] = [p[1]]
    else:
        p[0] = [p[1]] + p[3]


def p_subprogram(p):
    '''subprogram : PROGRAM prog_id mi_args phi_args program_args ASSIGN program_res statement_codeblock'''

    p[0] = PlanDef(id = p[2], mi = p[3], phi = p[4], input = p[5], output = p[7], body = p[8])


def p_prog_id(p):
    '''prog_id : INTEGER
               | INTEGER DOT prog_id'''

    if len(p) == 2:
        p[0] = (int(p[1]))
    else:
        p[0] = (int(p[1]), p[3])


def p_mi_args(p):
    '''mi_args : LPAREN mi_args_rec RPAREN'''

    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[2]


def p_mi_args_rec(p):
    '''mi_args_rec : empty
                   | mi_dec empty
                   | mi_dec COMMA mi_args_rec''' # ale tu jest brzydki hak w drugiej linijce

    if len(p) == 2:
        p[0] = [None]
    elif len(p) == 3:
        p[0] = [MiDec(id = p[1])]
    else:
        p[0] = [MiDec(id = p[1])] + p[3]


def p_mi_dec(p):
    '''mi_dec : MI
              | MI LSQUBR INTEGER RSQUBR'''

    if len(p) == 2:
        p[0] = None
    else:
        p[0] = int(p[3])


def p_phi_args(p):
    '''phi_args : LPAREN phi_args_rec RPAREN'''

    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[2]


def p_phi_args_rec(p):
    '''phi_args_rec : empty
                    | phi empty
                    | phi COMMA phi_args_rec''' # ale tu jest brzydki hak w drugiej linijce

    if len(p) == 2:
        p[0] = [None]
    elif len(p) == 3:
        p[0] = [PhiDec(id = p[1])]
    else:
        p[0] = [PhiDec(id = p[1])] + p[3]


def p_program_args(p):
    '''program_args : LPAREN program_args_rec RPAREN
                    | LPAREN empty RPAREN'''
    if p[2] is not None:
        p[0] = p[2]
    else:
        p[0] = [None]


def p_program_args_rec(p):
    '''program_args_rec : VVAR variable_data
                        | VVAR variable_data COMMA program_args_rec'''

    if len(p) == 3:
        p[0] = [Variable(species = p[1], id = p[2][0], component = p[2][1], typ = p[2][2])]
    else:
        p[0] = [Variable(species = p[1], id = p[2][0], component = p[2][1], typ = p[2][2])] + p[4]


def p_program_res(p):
    '''program_res : LPAREN program_res_rec RPAREN
                   | LPAREN empty RPAREN'''

    if p[2] is not None:
        p[0] = p[2]
    else:
        p[0] = [None]


def p_program_res_rec(p):
    '''program_res_rec : RVAR variable_data
                       | RVAR variable_data COMMA program_res_rec'''

    if len(p) == 3:
        p[0] = [Variable(species = p[1], id = p[2][0], component = p[2][1], typ = p[2][2])]
    else:
        p[0] = [Variable(species = p[1], id = p[2][0], component = p[2][1], typ = p[2][2])] + p[4]


def p_statement(p):
    '''statement : statement_assign
                 | statement_if
                 | statement_while
                 | statement_print'''

    p[0] = p[1]


def p_statement_assign(p):
    'statement_assign : over_expression ASSIGN writeable_var'

    p[0] = Assign(expr = p[1], var = p[3])


def p_writeable_var(p):
    '''writeable_var : ZVAR variable_data
                     | RVAR variable_data'''

    p[0] = Variable(species = p[1], id = p[2][0], component = p[2][1], typ = p[2][2])


def p_readable_var(p):
    '''readable_var : ZVAR variable_data
                    | VVAR variable_data'''

    p[0] = Variable(species = p[1], id = p[2][0], component = p[2][1], typ = p[2][2])


def p_variable_data(p):
    'variable_data : LSQUBR INTEGER COMMA vcomponent COMMA vtype RSQUBR'

    p[0] = (p[2], p[4], p[6])


def p_vcomponent(p):
    '''vcomponent : empty
                  | component_seq'''

    if len(p) == 0:
        p[0] = None
    else:
        p[0] = p[1]


def p_component_seq(p):
    '''component_seq : component_part
                     | component_part DOT component_seq'''

    if len(p) == 2:
        p[0] = [p[1], None]
    else:
        p[0] = [p[1], p[3]]


def p_component_part(p):
    '''component_part : expression'''

    p[0] = p[1]


def p_vtype(p):
    'vtype : type_seq'

    p[0] = p[1]


def p_type_seq(p):
    '''type_seq : type_part
                | LPAREN type_tuple RPAREN
                | type_part DOT type_seq'''

    if len(p) == 2:
        p[0] = p[1]
    else:
        if p[2] == ".":
            p[0] = List(lenght = p[1], elements = p[3])
        else:
            p[0] = p[2]

def p_type_part(p):
    '''type_part : INTEGER
                 | readable_var
                 | index
                 | mi_call'''

    if isinstance(p[1], str):
       p[0] = int(p[1])
    else:
       p[0] = p[1]

def p_mi_call(p):
    '''mi_call : MI
               | MI LSQUBR INTEGER RSQUBR'''

    if len(p) > 2:
        p[0] = MiUse(id = p[3])
    else:
        p[0] = MiUse(id = None)



def p_type_tuple(p):
    '''type_tuple : type_seq
                  | type_seq COMMA type_tuple'''

    if len(p) == 2:
        p[0] = Tuple(elements = (p[1],))
    else:
        p[0] = Tuple(elements = (p[1],) + p[3].elements)


def p_empty(p):
    'empty :'
    pass


# Error rule for syntax errors
def p_error(p):
    print(f"Syntax error: {p}")
    raise SyntaxError # Gdy będę chciał mieć, żeby error syntaxu wywalał całość, trzeba odkomentować tę linijkę


def p_statement_if(p):
    '''statement_if : over_expression IF statement_codeblock
                    | over_expression IF fin'''

    p[0] = If(cond = p[1], then = p[3])


def p_statement_while(p):
    '''statement_while : while_naked
                       | while_numbered'''

    p[0] = p[1]


def p_while_naked(p):
    '''while_naked : WHILE LCURBR if_seq RCURBR'''

    p[0] = While(typ = -1, start = 0, end = 0, body = Codeblock(p[3]))


def p_while_numbered(p):
    '''while_numbered : WHILE while_option statement_codeblock'''

    p[0] = While(typ = p[2][0], start = p[2][1], end = p[2][2], body = p[3])


def p_while_option(p):
    '''while_option : INTEGER LPAREN INTEGER COMMA INTEGER RPAREN
                    | INTEGER LPAREN INTEGER RPAREN'''

    if len(p) == 5:
        if p[1] == '0' or p[1] == '1':
            p[0] = (int(p[1]), 0, int(p[3]))
        elif p[1] == '2':
            p[0] = (int(p[1]), int(p[3]) - 1, 0)
    else:
        if p[1] == '3' or p[1] == '4' or p[1] == '5':
            p[0] = (int(p[1]), int(p[3]), int(p[5]))


def p_expression_equal(p):
    'over_expression : over_expression EQUAL expression'

    p[0] = Equal(left = p[1], right = p[3], typ = None)


def p_expression_greater(p):
    'over_expression : over_expression GREATER expression'

    p[0] = Greater(left = p[1], right = p[3], typ = None)


def p_expression_lower(p):
    'over_expression : over_expression LOWER expression'

    p[0] = Lower(left = p[1], right = p[3], typ = None)


def p_over_expression_expression(p):
    'over_expression : expression'

    p[0] = p[1]


def p_expression_plus(p):
    'expression : expression PLUS term'

    p[0] = Plus(left = p[1], right = p[3], typ = None)


def p_expression_minus(p):
    'expression : expression MINUS term'

    p[0] = Minus(left = p[1],  right = p[3], typ = None)


def p_expression_phi(p):
    'expression : expression phi term'

    p[0] = PhiUse(id = p[2], left = p[1], right = p[3], typ = None)


def p_phi(p):
    '''phi : PHI
           | PHI LSQUBR INTEGER RSQUBR'''

    if len(p) == 2:
        p[0] = None
    else:
        p[0] = int(p[3])


def p_expression_term(p):
    'expression : term'

    p[0] = p[1]


def p_term_times(p):
    'term : term TIMES factor'

    p[0] = Times(left = p[1], right = p[3], typ = None)


def p_term_divide(p):
    'term : term DIVIDE factor'

    p[0] = Divide(left = p[1], right = p[3], typ = None)


def p_term_factor(p):
    'term : factor'

    p[0] = p[1]


def p_factor_constant_int(p):
    'factor : INTEGER'

    p[0] = Const(value = int(p[1]), typ = "integer")


def p_factor_constant_float(p):
    'factor : INTEGER DOT INTEGER'

    res = float(f'{p[1]}.{p[3]}')
    p[0] = Const(value = res, typ = "float")


def p_factor_constant_bool(p):
    'factor : BOOL'

    p[0] = Const(value = p[1], typ = "bool")


def p_factor_constant_complex(p):
    'factor : LPAREN number COMMA number RPAREN'

    p[0] = Const(value = (float(p[2]), float(p[4])), typ = "complex")


def p_factor_neg(p):
    'factor : NEG factor'

    p[0] = Neg(body = p[2])


def p_factor_plan_call(p):
    'factor : PROGRAM prog_id mi_call_args phi_call_args program_call_args'

    p[0] = PlanCall(id = p[2], mi = p[3], phi = p[4], input = p[5], output = [])


def p_mi_call_args(p):
    '''mi_call_args : LPAREN mi_call_args_rec RPAREN
                     | LPAREN empty RPAREN'''

    p[0] = p[2]


def p_mi_call_args_rec(p):
    '''mi_call_args_rec : type_part
                        | type_part COMMA mi_call_args_rec'''

    if len(p) == 2:
        p[0] = [MiCall(p[1])]
    else:
        p[0] = [MiCall(p[1])] + p[3]


def p_phi_call_args(p):
    '''phi_call_args : LPAREN phi_call_args_rec RPAREN
                     | LPAREN empty RPAREN'''

    p[0] = p[2]


def p_phi_call_args_rec(p):
    '''phi_call_args_rec : operator
                         | operator COMMA phi_call_args_rec'''

    if len(p) == 2:
        p[0] = [PhiCall(p[1])]
    else:
        p[0] = [PhiCall(p[1])] + p[3]


def p_program_call_args(p):
    '''program_call_args : LPAREN program_call_args_rec RPAREN
                    | LPAREN empty RPAREN'''

    p[0] = p[2]


def p_program_call_args_rec(p):
    '''program_call_args_rec : over_expression
                             | over_expression COMMA program_call_args_rec'''

    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = [p[1]] + p[3]


def p_operator(p):
    '''operator : PLUS
                | MINUS
                | TIMES
                | DIVIDE
                | EQUAL
                | GREATER
                | LOWER'''

    p[0] = p[1]


def p_number(p):
    '''number : INTEGER
              | FLOAT'''

    p[0] = p[1]


def p_factor_variable(p):
    '''factor : readable_var'''

    p[0] = p[1]


def p_factor_expr(p):
    'factor : LPAREN over_expression RPAREN'

    p[0] = p[2]


def p_factor_index(p):
    'factor : index'

    p[0] = p[1]


def p_index(p):
    '''index : INDEX
             | INDEX LSQUBR INTEGER RSQUBR'''

    if len(p) == 2:
        p[0] = Index(id = None)
    else:
        p[0] = Index(id = p[3])


def p_statements(p):
    '''statements : statement SEPAR statements
                  | statement SEPAR empty
                  | statement empty empty'''

    if p[3] is None:
        p[0] = [p[1]]  # Jedna instrukcja
    else:
        p[0] = [p[1]] + p[3]  # Dodajemy instrukcję do listy


def p_statement_codeblock(p):
    '''statement_codeblock : LCURBR maybe_separ statements RCURBR
                           | LCURBR statements maybe_separ RCURBR
                           | statement'''

    if len(p) == 2:
        p[0] = Codeblock(content = [p[1]])
    else:
        if p[2] is None:
            p[0] = Codeblock(content = p[3])
        else:
            p[0] = Codeblock(content = p[2])


def p_if_seq(p):
    '''if_seq : maybe_separ statement_if maybe_separ empty
              | maybe_separ statement_if SEPAR if_seq'''

    if p[4] is None:
        p[0] = [p[2]]
    else:
        p[0] = [p[2]] + p[4]


def p_statement_print(p):
    '''statement_print : PRINT over_expression'''

    p[0] = Print(data = p[2])


def p_maybe_separ(p):
    '''maybe_separ : SEPAR
                   | empty'''

    p[0] = None


def p_fin(p):
    '''fin : FIN INTEGER
           | FIN empty'''

    p[0] = Fin(p[2])


# Build the parser
parser = yacc.yacc(debug=True)
