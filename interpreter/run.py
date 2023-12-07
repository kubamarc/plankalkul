from syntax import *


types = ['bool', 'bit_string', 'natural', 'integer', 'pos_float', 'float', 'complex']


types_dict = {
    0: types[0],
    8: types[1],
    9: types[2],
    10: types[3],
    11: types[4],
    12: types[5],
    13: types[6]
}

@dataclass
class Envir:
    env : dict

    def __init__(self):
        self.env = {'iDepth' : -1, 'fin' : 0}

    def copy(self):
        # Tworzymy głęboką kopię środowiska
        copied_environment = dict(self.environment_dict)
        return Enviroment(copied_environment)


@dataclass
class ValuesList:
    elements : list


@dataclass
class ValuesTuple:
    elements : list


def runWhole(program):
    env = Envir().env
    if '1' not in program:
        print("Error: There was no Plan of id 1 found")
        return
    runStatement(program['1'], env, program)


def runWhile(typ, start, end, body, env, program):
    match typ:
        case -1:
            codeblock = body
            code = codeblock.content
            any_true = True
            while any_true:
                if env['fin'] > 0:
                    env['fin'] -= 1
                    return # Jeżeli w ciele pętli trafiliśmy na fin, to się ewakuujemy
                any_true = False
                for ins in code:
                    if runExpr(ins.cond, env, program) == "Ja":
                        any_true = True
                        runStatement(ins.then, env, program)
                        if env['fin'] > 0:
                            env['fin'] -= 1
        case 0:
            for i in range(start, end):
                runStatement(body, env, program)
                if env['fin'] > 0:
                    env['fin'] -= 1
                    break
        case 1 | 2 | 3 | 4 | 5:
            env['iDepth'] += 1
            iname = 'i' + str(env['iDepth'])
            if start < end:
                change = 1
            else:
                change = -1
            for i in range(start, end, change):
                env[iname] = i
                runStatement(body, env, program)
                if env['fin'] > 0:
                    env['fin'] -= 1
                    break
            env.pop(iname)
            env['iDepth'] -= 1


def runStatement(ins, env, program):
    match ins:
        case PlanDef(id, mi, phi, input, output, body):
            runStatement(body, env, program)
        case Assign(expr, var):
            val = runExpr(expr, env, program)
            name = idOfVar(var)
            if not name in env:
                env[name] = createValOfVar(var.typ)
            v = env[name]
            env[name] = setValOfVar(var.component, val, v, env, program)
        case If(cond, then):
            if runExpr(cond, env, program) == "Ja":  #TODO: Należałoby się zastanowić, co jeśli cond zawiera jakieś wyrażenie modyfikujące środowisko (A może to wyłapuje typechecker?)
                runStatement(then, env, program)
                if env['fin'] > 0: # Jeżeli niżej w ciele trafiliśmy na fin, to wychodząc zmniejszamy głębokość wyjścia o 1
                    env['fin'] -= 1
        case While(typ, start, end, body):
            runWhile(typ, start, end, body, env, program)
        case Codeblock(content):
            for i in content:
                runStatement(i, env, program)
                if env['fin'] > 0:
                    return
        case Print(data):
            print(runExpr(data, env, program))


def runExpr(expr, env : dict, program):
    match expr:
        case Plus(left, right, typ):
            l = runExpr(left, env, program)
            r = runExpr(right, env, program)
            if typ == types_dict[13]:
                res = (l[0] + r[0], l[1] + r[1])
            elif typ == types_dict[0]:
                if l == "Ja" or r == "Ja":
                    return "Ja"
                return "Nein"
            else:
                res = l + r
            return res
        case Minus(left, right, typ):
            l = runExpr(left, env, program)
            r = runExpr(right, env, program)
            if typ == types_dict[13]:
                res = (l[0] - r[0], l[1] - r[1])
            else:
                res = l - r
            return res
        case Times(left, right, typ):
            l = runExpr(left, env, program)
            r = runExpr(right, env, program)
            if typ == types_dict[13]:
                a, b, c, d = l[0], l[1], r[0], r[1]
                res = (a * c - b * d, b * c + a * d)
            elif typ == types_dict[0]:
                if l == "Ja" and r == "Ja":
                    return "Ja"
                return "Nein"
            else:
                res = l *  r
            return res
        case Divide(left, right, typ):
            l = runExpr(left, env, program)
            r = runExpr(right, env, program)
            if typ == types_dict[13]:
                a, b, c, d = l[0], l[1], r[0], r[1]
                den = c ** 2 + d ** 2
                nom1 = a * c + b * d
                nom2 = b * c - a * d
                res = (nom1 / den, nom2 / den)
            else:
                if typ == types_dict[9] or typ == types_dict[10]:
                    res = l // r
                else:
                    res = l / r
            return res
        case Const(value, typ):
            return value
        case Variable():
            var = idOfVar(expr)
            res = getValOfVar(expr.component, env[var], env, program)
            return res
        case Index(id):
            if id is None: # Jeżeli nie ma powiedziane, który i jest chciany, bierzemy najpłytszy
                id = env['iDepth']
            name = 'i' + str(id)
            return env[name]
        case Equal(left, right):
            if runExpr(left, env, program) == runExpr(right, env, program):
                return "Ja"
            else:
                return "Nein"
        case Greater(left, right, typ):
            if runExpr(left, env, program) > runExpr(right, env, program):
                return "Ja"
            else:
                return "Nein"
        case Lower(left, right, typ):
            if runExpr(left, env, program) < runExpr(right, env, program):
                return "Ja"
            else:
                return "Nein"
        case Neg(body):
            if runExpr(body, env, program) == "Ja":
                return "Nein"
            else:
                return "Ja"
        case Fin(depth): # Jeżeli trafimy na fina, to wstawiamy w środowisko, jak głęboko wychodzimy
            if depth is None:
                depth = 1
            env['fin'] = depth
        case PlanCall(id, mi, phi, input, output):
            subEnv = Envir().env
            called = program[id]
            if input is not None:
                for i in range(len(input)):
                    inp = input[i]
                    dec = called.input[i]
                    name_dec = idOfVar(dec)
                    inp_val = runExpr(inp, env, program)
                    subEnv[name_dec] = inp_val
            if phi is not None:
                for i in range(len(phi)):
                    p = phi[i]
                    dec = called.phi[i]
                    name_dec = idOfVar(dec)
                    p_val = p.operator
                    subEnv[name_dec] = p_val
            runStatement(called, subEnv, program)
            if output is not None:
                if output is not list:
                    res = idOfVar(output)
                    return subEnv[res]
        case PhiUse(id, left, right, typ):
            pass
        case Nfun(arg):
            return len(env[idOfVar(arg)].elements)
        case Ger(arg):
            r = runExpr(arg, env, program)
            if r % 2 == 0:
                return 'Ja'
            else:
                return 'Nein'


# This function creates data structure kept in variable. It's strict, all nodes are initialized to 0
def createValOfVar(var_type):
    match var_type:
        case List(lenght, elements):
            return ValuesList(elements = [createValOfVar(elements) for i in range(lenght)])
        case Tuple(elements):
            res = []
            for e in elements:
                res += [createValOfVar(e)]
            return ValuesTuple(elements = res)
        case _:
            match types_dict[var_type]:
                case 'bool':
                    return "Nein"
                case 'bit_string':
                    return 0
                case 'natural':
                    return 0
                case 'integer':
                    return 0
                case 'pos_float':
                    return 0.0
                case 'float':
                    return 0.0
                case 'complex':
                    return (0.0, 0.0)


def setValOfVar(var_comp, val, structure, env, program):
    if var_comp is None or var_comp == [None]:
        structure = val
        return structure
    if type(var_comp[0]) in [Index, Variable, Const, Minus, Plus, Times, Divide]:
        comp = runExpr(var_comp[0], env, program)
        res = setValOfVar([None], val, structure.elements[comp], env, program)
        structure.elements[comp] = res
        return structure
    res = setValOfVar(var_comp[1], val, structure.elements[var_comp[0]], env, program)
    structure.elements[var_comp[0]] = res
    return structure


def getValOfVar(var_comp, val, env, program):
    if var_comp == [None] or var_comp is None:
        return val
    if type(var_comp[0]) in [Index, Variable, Const, Minus, Plus, Times, Divide]:
        comp = runExpr(var_comp[0], env, program)
        res = getValOfVar([None], val.elements[comp], env, program)
        return res
    return getValOfVar(var_comp[1], val.elements[var_comp[0]], env, program)


def idOfVar(var):
    match var:
        case Variable():
            return var.species + str(var.id)
        case PhiUse(id, left, right, typ):
            if id is not None:
                return "Phi" + str(id)
            else:
                return "Phi"
        case PhiDec(id):
            if id is not None:
                return "Phi" + str(id)
            else:
                return "Phi"
