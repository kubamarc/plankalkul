from syntax import *
import copy

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
        self.env = {"finDepth" : 0, "namedWhileDepth" : 0}

    def copy(self):
        # Tworzymy głęboką kopię środowiska
        copied_environment = dict(self.environment_dict)
        return Enviroment(copied_environment)


def typecheckAll(program):
    envOfPlans = {}
    envOfChecked = {}
    for ins in program:
        match ins:
            case PlanDef(id, mi, phi, input, output, body):
                # envOfPlans[id] = {'in' : input, 'out' : output, 'phi' : phi, 'body' : body}
                envOfPlans[id] = ins
            case _:
                print("TypeError: Top level instruction is not Plan")
                return (False, {})
    for ins in program:
        env = Envir().env
        if ins.input[0] is not None:
            if ins.id == 1:
                print('TypeError: Plan of id 1 cannot take arguments')
            for var in ins.input:
                t_var = variableWholeType(var)
                n_var = idOfVar(var)
                env[n_var] = t_var
        if ins.output[0] is not None:
            if ins.id == 1:
                print('TypeError: Plan of id 1 cannot return values')
            for var in ins.output:
                t_var = variableWholeType(var)
                n_var = idOfVar(var)
                env[n_var] = t_var
        if ins.phi[0] is not None:
            if ins.id == 1:
                print('TypeError: Plan of id 1 cannot take operation arguments')
            for p in ins.phi:
                n_var = idOfVar(p)
                env[n_var] = ''
        if ins.phi[0] is None and ins.mi[0] is None:
            t = typecheckPlan(ins.id, env, envOfPlans, envOfChecked)
            if not t[1]:
                print('TypeError: Something went badly')
                return (False, {})
    return (True, envOfChecked)


def typecheckPlan(id, env, envOfPlans, program):
    if id in program:
        return (id, True)
    plan = envOfPlans[id]
    name = createPlanName(envOfPlans, id, env)
    if plan.phi[0] is not None or plan.mi[0] is not None:
        plan = copyPlan(plan, env)
    if not name in program:
        program[name] = PlanDef(id = name, mi = plan.mi, phi = plan.phi, input = plan.input, output = plan.output, body = plan.body)
        envOfPlans[name] = program[name]
    else:
        return (name, True)
    return (name, typecheck(plan.body, env, envOfPlans, program))


def typecheck(ins, env, envOfPlans, program):
    match ins:
        case Assign(expr, var):
            t_var = variableCompType(var, env, envOfPlans, program)
            if not t_var:
                return False
            if isExpOfType(expr, env, envOfPlans, t_var, program):
                name = idOfVar(var)
                t = variableWholeType(var)
                if name in env:
                    if env[name] != t:
                        print(f"TypeError: Multiple types assigned to one variable {idOfVar(var)}")
                        return False
                else:
                    env[name] = variableWholeType(var)
                return True
            print(f"TypeError: Assign types missmatch, left side is not of type {t_var}")
            return False
        case If(cond, then):
            env['finDepth'] += 1
            if isExpOfType(cond, env, envOfPlans, 'bool', program):
                res =  typecheck(then, env, envOfPlans, program)
            else:
                print("TypeError: If condition is not of type bool")
                res = False
            env['finDepth'] -= 1
            return res
        case While(typ, start, end, body):
            env['finDepth'] += 1
            if typ != -1 and typ != 0:
                env['namedWhileDepth'] += 1
            res = typecheck(body, env, envOfPlans, program)
            env['finDepth'] -= 1
            if typ != -1 and typ != 0:
                env['namedWhileDepth'] -= 1
            if not res:
                print(f'while body type error {body}')
            return res
        case Codeblock(content):
            res = True
            for i in content:
                res = res and typecheck(i, env, envOfPlans, program)
                if not res:
                    print(f"Type error in instruction {i}")
                    return res
            return True
        case Print(data):
            for i in types_dict.values():
                if isExpOfType(data, env, envOfPlans, i, program):
                    return True
            return False
        case PlanDef(id, mi, phi, input, output, body):
            print("TypeError: Declaration of plan inside another plan")
            return False
        case Fin(depth):
            if depth is None:
                depth = 1
            if int(depth) > env['finDepth'] or int(depth) < 0:
                print("TypeError: To deep fin")
                return False
            else:
                return True
        case _:
            return False


def inferExprType(expr, env, envOfPlans, program):
    match expr:
            case Variable(species, id, component, typ):
                name = idOfVar(expr)
                t = variableWholeType(expr)
                if name in env:
                    in_env = env[name]
                    if in_env == t:
                        return (True, in_env)
                    else:
                        print(f"TypeError: Variable {name} type missmatch with previous usage")
                        return (False, None)
                else:
                    print(f"TypeError: Variable {name} used before declaration")
                    return (False, None)
            case Const():
                print(f"TypeError: You cannot use constant value in here")
                return (False, None)
            case Index(id):
                if id is None:
                    if env['namedWhileDepth'] != 1: # If While depth is higher than one, you need to give i an index
                        print("TypeError: Can't match index i to its while")
                        return (False, None)
                    else:
                        return (True, ['integer'])
                else:
                    if id >= env['namedWhileDepth'] or id < 0:
                        print("TypeError: Wrong i index depth")
                        return (False, None)
                    else:
                        return (True, ['integer'])
            case Plus(left, right, typ) | Times (left, right, typ):
                match typ:
                    case List() | Tuple():
                        return (False, None)
                    case _:
                        t1 = inferExprType(left, env, envOfPlans, program)
                        if not t1[0]:
                            return t1
                        if isExpOfType(right, env, envOfPlans, t1[1], program):
                            expr.typ = t1[1]
                            return (True, t1[1])
                return (False, None)
            case Minus(left, right, typ) | Divide(left, right, typ):
                match typ:
                    case List() | Tuple():
                        return (False, None)
                    case _:
                        t1 = inferExprType(left, env, envOfPlans, program)
                        if not t1[0]:
                            return t1
                        if t1[1] == types_dict[0]:
                            print(f"TypeError: Non boolean operation called on boolean expression")
                            return (False, None)
                        if isExpOfType(right, env, envOfPlans, t1[1], program):
                            expr.typ = t1[1]
                            return (True, t1[1])
                return (False, None)
            case Equal(left, right, typ):
                match typ:
                    case List() | Tuple():
                        return (False, None)
                    case _:
                        t1 = inferExprType(left, env, envOfPlans, program)
                        if not t1[0]:
                            return t1
                        if isExpOfType(right, env, envOfPlans, t1[1], program):
                            return (True, t1[1])
                return (False, None)
            case Greater(left, right, typ) | Lower(left, right, typ):
                match typ:
                    case List() | Tuple():
                        return (False, None)
                    case _:
                        t1 = inferExprType(left, env, envOfPlans, program)
                        if not t1[0]:
                            return t1
                        if t1[1] == types_dict[0]:
                            print(f"TypeError: Comparison operator called on booleans")
                            return (False, None)
                            if isExpOfType(right, env, envOfPlans, t1[1], program):
                                expr.typ = t1[1]
                                return (True, t1[1])
                return (False, None)
            case Neg(body):
                return (isExpOfType(body, env, envOfPlans, 'bool', program), 'bool')
            case PlanCall(id, mi, phi, input, output):
                return typecheckPlanCall(expr, env, envOfPlans, program)
            case PhiUse(id, left, right, typ):
                pass
            case Nfun(arg):
                x = inferExprType(arg, env, envOfPlans, program)
                if type(x[1]) is List:
                    return True


def isExpOfType(expr, env, envOfPlans, if_type, program):
    match expr:
        case Variable(species, id, component, typ):
            name = idOfVar(expr)
            t = variableWholeType(expr)
            if name in env:
                in_env = env[name]
                if in_env == t:
                    return variableCompType(expr, env, envOfPlans, program) == if_type
                else:
                    print(f"TypeError: Variable {name} type missmatch with previous usage")
                    return False
            else:
                print(f"TypeError: Variable {name} used before declaration")
                return False
        case Const(value, typ):
                return (typ == if_type)
        case Index(id):
            if id is None:
                if env['namedWhileDepth'] != 1: # If While depth is higher than one, you need to give i an index
                    print("TypeError: Can't match index i to its while")
                    return False
                else:
                    return if_type in ['natural', 'integer']
            else:
                if id >= env['namedWhileDepth'] or id < 0:
                    print("TypeError: Wrong i index depth")
                    return False
                else:
                    return if_type in ['integer']

        case Plus(left, right, typ) | Times (left, right, typ):
            match typ:
                case List() | Tuple():
                    return False
                case _:
                    if isExpOfType(left, env, envOfPlans, if_type, program) and isExpOfType(right, env, envOfPlans, if_type, program):
                        expr.typ = if_type
                        return True
            return False
        case Minus(left, right, typ) | Divide(left, right, typ):
            if if_type == types_dict[0]: # Czy umiemy dodawać typ 8?
                return False
            match typ:
                case List() | Tuple():
                    return False
                case _:
                    if isExpOfType(left, env, envOfPlans, if_type, program) and isExpOfType(right, env, envOfPlans, if_type, program):
                        expr.typ = if_type
                        return True
            return False
        case Equal(left, right, typ):
            if not if_type == types_dict[0]:
                return False
            match typ:
                case List() | Tuple():
                    return False #TODO: Dopisać kawałek robiący porównanie typów dla list i tupli
                case _:
                    t1 = inferExprType(left, env, envOfPlans, program)
                    if isExpOfType(right, env, envOfPlans, t1[1], program):
                        expr.typ = if_type
                        return True
            return False
        case Greater(left, right, typ) | Lower(left, right, typ):
            if not if_type == types_dict[0]:
                return False
            match typ:
                case List() | Tuple():
                    return False
                case _:
                    t1 = inferExprType(left, env, envOfPlans, program)
                    expr.typ = if_type
                    return t1[1] != types_dict[0] and isExpOfType(right, env, envOfPlans, t1[1], program)
            return False
        case Neg(body):
            if if_type != types_dict[0]:
                return False
            return isExpOfType(body, env, envOfPlans, types_dict[0], program)
        case PlanCall(id, mi, phi, input, output):
            res = typecheckPlanCall(expr, env, envOfPlans, program)
            return res[0] and res[1] == if_type
        case PhiUse(id, left, right, typ):
            pass
        case Nfun(arg):
            x = inferExprType(arg, env, envOfPlans, program)
            if type(x[1]) is List:
                return True


def phiOperator(phi, env):
    p = idOfVar(phi)
    l = phi.left
    r = phi.right
    t = phi.typ
    match env[p].operator:
        case '+':
            expr = Plus(left = l, right = r, typ = t)
        case '-':
            expr = Minus(left = l, right = r, typ = t)
        case '*':
            expr = Times(left = l, right = r, typ = t)
        case '/':
            expr = Divide(left = l, right = r, typ = t)
        case '=':
            expr = Equal(left = l, right = r, typ = t)
        case '>':
            expr = Greater(left = l, right = r, typ = t)
        case '<':
            expr = Lower(left = l, right = r, typ = t)
    return expr


def typecheckPlanCall(expr, env, envOfPlans, program):
    match expr:
        case PlanCall(id, mi, phi, input, output):
            subEnv = Envir().env
            if miFits(id, mi, envOfPlans):
                if expr.mi is not None:
                    for m_index in range(len(expr.mi)):
                        mi_typ = mi[m_index]
                        mi_name = idOfVar(envOfPlans[id].mi[m_index])
                        subEnv[mi_name] = mi_typ.typ
            else:
                return (False, None)
            if inputFits(id, input, envOfPlans, env, program, subEnv) and phiFits(id, phi, envOfPlans):
                out = typeOfOutput(id, output, envOfPlans, env, expr, subEnv)
                if expr.phi is not None:
                    for p_index in range(len(expr.phi)):
                        phi_op = phi[p_index]
                        phi_name = idOfVar(envOfPlans[id].phi[p_index])
                        subEnv[phi_name] = phi_op
                if expr.input is not None:
                    for in_index in range(len(expr.input)):
                        in_type = variableWholeType(envOfPlans[id].input[in_index])  #TODO: Co jeśli ktoś w nagłówku funkcji poda zmienną z komponentem?
                        in_name = idOfVar(envOfPlans[id].input[in_index])
                        match in_type:
                            case MiUse():
                                in_type = expr.input[in_index]
                                in_type = in_type.typ
                        subEnv[in_name] = in_type
                name, res = typecheckPlan(id, subEnv, envOfPlans, program)
                expr.id = name
                return (res, out)
            else:
                return (False, None)


def inputFits(id, input, envOfPlans, env, program, subEnv):
    if input is None:
        return envOfPlans[id].input[0] is None
    if len(input) != len(envOfPlans[id].input) or envOfPlans[id].input[0] is None:
        return False
    for i in range(len(input)):
        t1 = variableWholeType(envOfPlans[id].input[i])
        match t1:
            case MiUse():
                name = idOfVar(t1)
                t1 = types_dict[subEnv[name]]
        if not isExpOfType(input[i], env, envOfPlans, t1, program):
            return False
    return True


def phiFits(id, phi, envOfPlans):
    if phi is None:
        return envOfPlans[id].phi[0] is None
    if len(phi) != len(envOfPlans[id].phi) or envOfPlans[id].phi[0] is None:
        return False
    return True


def miFits(id, mi, envOfPlans):
    if mi is None:
        return envOfPlans[id].mi[0] is None
    if len(mi) != len(envOfPlans[id].mi) or envOfPlans[id].mi[0] is None:
        return False
    return True


def typeOfOutput(id, output, envOfPlans, env, expr, subEnv):
    if envOfPlans[id].output[0] is None:
        return []
    else:
        if len(envOfPlans[id].output) == 1:
            res = variableWholeType(envOfPlans[id].output[0])
            res = copyTyp(res, subEnv)
            expr.output = copyExpr(envOfPlans[id].output[0], subEnv)
            return res
        res = []
        expr.output = []
        for i in envOfPlans[id].output:
            t = [variableWholeType(i)]
            res += copyTyp(t, subEnv)
            expr.output += [copyExpr(i, subEnv)]
    return res


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
        case MiDec(id):
            if id is not None:
                return "Mi" + str(id)
            else:
                return "Mi"
        case MiUse(id):
            if id is not None:
                return "Mi" + str(id)
            else:
                return "Mi"


# This function from whole type and component gets type of exact part of variable. Problem:
# What if we iterate in while throught list (or tuple) (i mean we use index i).
# What should that function do in such situation?
# I have literaly no idea
def variableCompType(var, env, envOfPlans, program):
    comp = var.component
    typ = var.typ
    while not (comp is None):
        if type(comp[0]) is Index or type(comp[0]) is Variable or type(comp[0]) is Const:
            match typ:
                case List(lenght, elements):
                    typ = elements
                    comp = None
                case _:
                    print(f"TypeError: type {type(typ)} is not indexable by variable")
                    return False
        elif type(comp[0]) in [Minus, Plus, Times, Divide]:
            if not isExpOfType(comp[0], env, envOfPlans, 'integer', program):
                print(f"TypeError: you cannot iterate with type other than integer")
                return False
            match typ:
                case List(lenght, elements):
                    typ = elements
                    comp = None
                case _:
                    print(f"TypeError: type {type(typ)} is not indexable by variable")
                    return False
        else:
            c = comp[0]
            if c < 0:
                print("TypeError: negative component")
                return False
            comp = comp[1]
            match typ:
                case List(length, elements):
                    if c >= length:
                        print("TypeError: too big component")
                        return False
                    else:
                        typ = elements
                case Tuple(elements):
                    if c >= len(elements):
                        print("TypeError: too big component")
                        return False
                    else:
                        typ = elements[c]
    match typ:
        case List() | Tuple():
            return typ
        case _:
            return types_dict[typ]


def variableWholeType(var):
    if isinstance(var, int):
        return types_dict[var]
    match var.typ:
        case List() | Tuple():
            return var.typ
        case MiUse(id):
            return var.typ
        case _:
            return types_dict[var.typ]


def createPlanName(envOfPlans, id, env):
    name = str(id)
    for i in envOfPlans[id].phi:
        if i is not None:
            j = idOfVar(i)
            name += env[j].operator
    for i in envOfPlans[id].mi:
        if i is not None:
            j = idOfVar(i)
            name += 'm' + str(env[j])
    return name


def copyPlan(plan, env):
    match plan:
        case PlanDef(id, mi, phi, input, output, body):
            return PlanDef(id = id, mi = mi, phi = phi, input = copyInOut(input, env), output = copyInOut(output, env), body = copyStatement(body, env))


def copyStatement(stat, env):
    match stat:
        case Assign(expr, var):
            return Assign(expr = copyExpr(expr, env), var = copyExpr(var, env))
        case If(cond, then):
            return If(cond = copyExpr(cond, env), then = copyStatement(then, env))
        case While(typ, start, end, body):
            return While(typ = typ, start = start, end = end, body = copyStatement(body, env))
        case Codeblock(content):
            res = []
            for i in content:
                res.append(copyStatement(i, env))
            return Codeblock(content = res)
        case Print(data):
            return Print(data = copyExpr(data, env))
        case Fin(depth):
            return Fin(depth)


def copyExpr(expr, env):
    match expr:
        case Const(value, typ):
            return Const(value, typ)
        case Variable(species, id, component, typ):
            return Variable(species = species, id = id, component = component, typ = copyTyp(typ, env)) #TODO: czy powinienem schodzić głębiej, do komponentów i typów?
        case Index(id):
            return Index(id = id)
        case Minus(left, right, typ):
            return Minus(left = copyExpr(left, env), right = copyExpr(right, env), typ = typ)
        case Plus(left, right, typ):
            return Plus(left = copyExpr(left, env), right = copyExpr(right, env), typ = typ)
        case Times(left, right, typ):
            return Times(left = copyExpr(left, env), right = copyExpr(right, env), typ = typ)
        case Divide(left, right, typ):
            return Divide(left = copyExpr(left, env), right = copyExpr(right, env), typ = typ)
        case Equal(left, right, typ):
            return Equal(left = copyExpr(left, env), right = copyExpr(right, env), typ = typ)
        case Greater(left, right, typ):
            return Greater(left = copyExpr(left, env), right = copyExpr(right, env), typ = typ)
        case Lower(left, right, typ):
            return Lower(left = copyExpr(left, env), right = copyExpr(right, env), typ = typ)
        case Neg(body):
            return Neg(body = copyExpr(body, env))
        case PhiUse(id, left, right, typ):
            p = phiOperator(expr, env)
            p.left = copyExpr(left, env)
            p.right = copyExpr(right, env)
            return p
        case PlanCall(id, mi, phi, input, output):
            return PlanCall(id = id, mi = mi, phi = phi, input = input, output = output)


def copyTyp(typ, env):
    match typ:
        case List(lenght, elements):
            return List(lenght = lenght, elements = copyTyp(elements, env))
        case Tuple(elements):
            res = ()
            for i in elements:
                res += (copyTyp(i, env),)
            return Tuple(elements = res)
        case MiUse(id):
            mi_name = idOfVar(typ)
            t = env[mi_name]
            return copyTyp(t, env)
        case _:
            return typ


def copyInOut(l, env):
    res = []
    if l is None:
        return None
    for i in l:
        new = copyExpr(i, env)
        res += [new]
    return res
