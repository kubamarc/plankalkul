from syntax import *
import sys


#If type checking fails, raise an exception and terminate the process.
class TypecheckError(Exception):
    def __init__(self, message):
        super().__init__(message)
        print(f"TypecheckError occurred: {message}")
        sys.exit(1)


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
        # Making deep copy of env
        copied_environment = dict(self.environment_dict)
        return Enviroment(copied_environment)


def typecheckAll(program):
    envOfPlans = {}
    envOfChecked = {}
    for ins in program:
        match ins:
            case PlanDef(id, mi, phi, input, output, body):
                envOfPlans[id] = ins
            case _:
                raise TypecheckError("Top level instruction is not Plan")
                return (False, {})
    for ins in program:
        env = Envir().env
        if ins.input[0] is not None:
            if ins.id == 1:
                raise TypecheckError("Plan with id 1 cannot take arguments")
            for var in ins.input:
                t_var = varDeclaredTyp(var)
                n_var = idOfVar(var)
                env[n_var] = t_var
        if ins.output[0] is not None:
            if ins.id == 1:
                raise TypecheckError("Plan with id 1 cannot return values")
            for var in ins.output:
                t_var = varDeclaredTyp(var)
                n_var = idOfVar(var)
                env[n_var] = t_var
        if ins.phi[0] is not None:
            if ins.id == 1:
                raise TypecheckError("Plan with id 1 cannot take operation arguments")
        if ins.mi[0] is not None:
            if ins.id == 1:
                raise TypecheckError("Plan with id 1 cannot take type arguments")
        if ins.phi[0] is None and ins.mi[0] is None:
            t = typecheckPlan(ins.id, env, envOfPlans, envOfChecked)
            if not t[1]:
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
            dec_type = varDeclaredTyp(var)
            var_name = idOfVar(var)
            comp = varComp(var)
            whole_type = ""
            if var_name in env:
                whole_type = env[var_name]
            else:
                if not comp is None:
                    raise TypecheckError("First appearance of variable with non empty component")
                env[var_name] = dec_type
                res = isExpOfType(expr, env, envOfPlans, dec_type, program)
                if not res:
                    raise TypecheckError("Type mismatch: The type of the variable does not match the declared type")
                return res
            if comp is None:
                if dec_type != whole_type:
                    raise TypecheckError("Type mismatch: The type of the variable does not match the declared type")
                else:
                    res = isExpOfType(expr, env, envOfPlans, dec_type, program)
                    return res
            if not comp is None:
                var_comp_type = variableCompType(whole_type, comp, env, envOfPlans, program)
                if var_comp_type != dec_type:
                    raise TypecheckError("Type mismatch: The type of the variable does not match the declared type")
            res = isExpOfType(expr, env, envOfPlans, dec_type, program)
            return res
        case If(cond, then):
            env['finDepth'] += 1
            if isExpOfType(cond, env, envOfPlans, 'bool', program):
                subEnv = env.copy()
                res =  typecheck(then, subEnv, envOfPlans, program)
                env['finDepth'] -= 1
                if not res:
                    raise TypecheckError("If condition not of Ja-Nein type")
                return res
            else:
                raise TypecheckError("If condition is not of type bool")
        case While(typ, start, end, body):
            env['finDepth'] += 1
            if typ != -1 and typ != 0:
                env['namedWhileDepth'] += 1
            res = typecheck(body, env, envOfPlans, program)
            env['finDepth'] -= 1
            if typ != -1 and typ != 0:
                env['namedWhileDepth'] -= 1
            if not res:
                raise TypecheckError(f'while body type error')
            return res
        case Codeblock(content):
            res = True
            for i in content:
                res = typecheck(i, env, envOfPlans, program)
                if not res:
                    raise TypecheckError(f"Type error")
                    return False
            return True
        case Print(data):
            r = inferExprType(data, env, envOfPlans, program)
            if r[1] not in types_dict.values():
                raise TypecheckError("Unprintable data given to Drucken")
            else:
                return True
        case PlanDef(id, mi, phi, input, output, body):
            raise TypecheckError("Declaration of plan inside another plan")
        case Fin(depth):
            if depth is None:
                depth = 1
            if int(depth) > env['finDepth'] or int(depth) < 0:
                raise TypecheckError("To deep fin")
            else:
                return True
        case Dec(var):
            var_name = idOfVar(var)
            if var_name in env:
                raise TypecheckError("Multiple declaration of variable")
            if not varComp(var) is None:
                raise TypecheckError("Component of declared variable is not empty")
            env[var_name] = varDeclaredTyp(var)
            return True
        case _:
            return False


def inferExprType(expr, env, envOfPlans, program):
    match expr:
            case Variable(species, id, component, typ):
                var_name = idOfVar(expr)
                dec_type = varDeclaredTyp(expr)
                var_comp = varComp(expr)
                whole_type = None
                if var_name in env:
                    whole_type = env[var_name]
                    if var_comp is None:
                        if whole_type != dec_type:
                            raise TypecheckError("Type mismatch: The type of the variable does not match the declared type")
                        else:
                            return (True, dec_type)
                    else:
                        var_comp_type = variableCompType(whole_type, var_comp, env, envOfPlans, program)
                        if var_comp_type != dec_type:
                            raise TypecheckError("Type mismatch: The type of the variable does not match the declared type")
                        else:
                            return (True, dec_type)
                else:
                    raise TypecheckError("Use before declaration: Used variable havn't been declared")
            case Const():
                raise TypecheckError(f"Const value in inappropriate place")
            case Index(id):
                if id is None:
                    if env['namedWhileDepth'] != 1: # If While depth is higher than one, you need to give i an index
                        raise TypecheckError("Can't match index i to its while")
                    else:
                        return (True, 'integer')
                else:
                    if id >= env['namedWhileDepth'] or id < 0:
                        raise TypecheckError("Wrong i index depth")
                    else:
                        return (True, 'integer')
            case Plus(left, right, typ) | Times (left, right, typ):
                match typ:
                    case List() | Tuple():
                        raise TypecheckError("Cannot make arithmetic operations on Lists or Tuples")
                    case _:
                        t1 = inferExprType(left, env, envOfPlans, program)
                        if not t1[0]:
                            return t1
                        if isExpOfType(right, env, envOfPlans, t1[1], program):
                            expr.typ = t1[1]
                            return (True, t1[1])
                raise TypecheckError("Cannot match Addition/Multiplication operation to given type")
            case Minus(left, right, typ) | Divide(left, right, typ):
                match typ:
                    case List() | Tuple():
                        raise TypecheckError("Cannot use arithmetic operations on Lists or Tuples")
                    case _:
                        t1 = inferExprType(left, env, envOfPlans, program)
                        if not t1[0]:
                            return t1
                        if t1[1] == types_dict[0]:
                            raise TypecheckError(f"Non boolean operation called on boolean expression")
                        if isExpOfType(right, env, envOfPlans, t1[1], program):
                            expr.typ = t1[1]
                            return (True, t1[1])
                raise TypecheckError("Cannot match Substraction/Division operation to given type")
            case Equal(left, right, typ):
                match typ:
                    case List() | Tuple():
                        raise TypecheckError("Cannot make arithmetic operations on Lists or Tuples")
                    case _:
                        t1 = inferExprType(left, env, envOfPlans, program)
                        if not t1[0]:
                            return t1
                        if isExpOfType(right, env, envOfPlans, t1[1], program):
                            return (True, t1[1])
                raise TypecheckError("Cannot match Comparison operation to given type")
            case Greater(left, right, typ) | Lower(left, right, typ):
                match typ:
                    case List() | Tuple():
                        raise TypecheckError("Cannot make arithmetic operations on Lists or Tuples")
                    case _:
                        t1 = inferExprType(left, env, envOfPlans, program)
                        if not t1[0]:
                            return t1
                        if t1[1] == types_dict[0]:
                            raise TypecheckError(f"Comparison operator called on type 0")
                            if isExpOfType(right, env, envOfPlans, t1[1], program):
                                expr.typ = t1[1]
                                return (True, t1[1])
                raise TypecheckError("Cannot match Comparison operation to given type")
            case Neg(body):
                res = (isExpOfType(body, env, envOfPlans, 'bool', program), 'bool')
                if res[0]:
                    return res
                raise TypecheckError(f"Negation used not on type 0")
            case PlanCall(id, mi, phi, input, output):
                res = typecheckPlanCall(expr, env, envOfPlans, program)
                if res[0]:
                    return res
                raise TypecheckError("Plan call typechecking failed")
            case PhiUse(id, left, right, typ):
                raise TypecheckError("Something went terribly wrong, please report this")
            case Nfun(arg):
                res = inferExprType(arg, env, envOfPlans, program)
                res = (type(res[1]) is List, ['integer'])
                if res[0]:
                    return res
                raise TypecheckError("Function N should be used on List")
            case Ger(arg):
                res = isExpOfType(arg, env, envOfPlans, 'integer', program)
                if res:
                    return (res, 'bool')
                raise TypecheckError("function Ger should be used on type 10")
            case Ord(arg):
                res =  inferExprType(arg, env, envOfPlans, program)
                res = (type(res[1]) is List, res[1])
                if res[0]:
                    return res
                raise TypecheckError("Function Ord should be used on List")
            case _:
                raise TypecheckError(f"Something went bad. {expr}")


def isExpOfType(expr, env, envOfPlans, if_type, program):
    match expr:
        case Variable(species, id, component, typ):
            var_name = idOfVar(expr)
            dec_type = varDeclaredTyp(expr)
            var_comp = varComp(expr)
            whole_type = None
            if var_name in env:
                whole_type = env[var_name]
                if var_comp is None:
                    if whole_type != dec_type:
                        raise TypecheckError("Type mismatch with the previous usage of the variable")
                    else:
                        return dec_type == if_type
                else:
                    var_comp_type = variableCompType(whole_type, var_comp, env, envOfPlans, program)
                    if var_comp_type != dec_type:
                        raise TypecheckError("Type missmatch")
                    else:
                        return dec_type == if_type
        case Const(value, typ):
                return (typ == if_type)
        case Index(id):
            if id is None:
                if env['namedWhileDepth'] != 1: # If While depth is higher than one, you need to give i an index
                    raise TypecheckError("Can't match index i to its while")
                else:
                    return if_type in ['natural', 'integer']
            else:
                if id >= env['namedWhileDepth'] or id < 0:
                    raise TypecheckError("Wrong i index depth")
                else:
                    return if_type in ['integer']

        case Plus(left, right, typ) | Times (left, right, typ):
            match typ:
                case List() | Tuple():
                    raise TypecheckError("Cannot use arithmetic operations on Lists or Tuples")
                case _:
                    if isExpOfType(left, env, envOfPlans, if_type, program) and isExpOfType(right, env, envOfPlans, if_type, program):
                        expr.typ = if_type
                        return True
            raise TypecheckError("Cannot match Addition/Multiplication operation to given type")
        case Minus(left, right, typ) | Divide(left, right, typ):
            if if_type == types_dict[0]: # Czy umiemy dodawać typ 8?
                raise TypecheckError(f"Return type of substraction/division operation cannot be 0 type")
            match typ:
                case List() | Tuple():
                    raise TypecheckError("Cannot use arithmetic operations on Lists or Tuples")
                case _:
                    if isExpOfType(left, env, envOfPlans, if_type, program) and isExpOfType(right, env, envOfPlans, if_type, program):
                        expr.typ = if_type
                        return True
            raise TypecheckError("Cannot match Substraction/Division operation to given type")
        case Equal(left, right, typ):
            if not if_type == types_dict[0]:
                raise TypecheckError(f"Equality comparison return type should be Ja-Nein-Vert, not {if_type}")
            match typ:
                case List() | Tuple():
                    raise TypecheckError("Cannot use arithmetic operations on Lists or Tuples")
                case _:
                    t1 = inferExprType(left, env, envOfPlans, program)
                    if isExpOfType(right, env, envOfPlans, t1[1], program):
                        expr.typ = if_type
                        return True
            return False
        case Greater(left, right, typ) | Lower(left, right, typ):
            if not if_type == types_dict[0]:
                raise TypecheckError(f"Comparison return type should be Ja-Nein-Vert, not {if_type}")
            match typ:
                case List() | Tuple():
                    raise TypecheckError("Cannot use comparison operations on Lists or Tuples")
                case _:
                    t1 = inferExprType(left, env, envOfPlans, program)
                    expr.typ = if_type
                    return t1[1] != types_dict[0] and isExpOfType(right, env, envOfPlans, t1[1], program)
            return False
        case Neg(body):
            if if_type != types_dict[0]:
                raise TypecheckError(f"Negation needs to return type of Ja-Nein-Vert, not {if_type}")
            return isExpOfType(body, env, envOfPlans, types_dict[0], program)
        case PlanCall(id, mi, phi, input, output):
            res = typecheckPlanCall(expr, env, envOfPlans, program)
            return res[0] and res[1] == if_type
        case Nfun(arg):
            res = inferExprType(arg, env, envOfPlans, program)
            if type(res[1]) is List:
                return if_type == 'integer'
            raise TypecheckError('N function may be used only on list')
        case Ger(arg):
            res = isExpOfType(arg, env, envOfPlans, 'integer', program)
            if res:
                return if_type == 'bool'
            raise TypecheckError("Ger function may be used only on integers")
        case Ord(arg):
            res = inferExprType(arg, env, envOfPlans, program)
            if type(res[1]) is List:
                return res[1] == if_type
            raise TypecheckError('Ord functions may be used only on list')
        # case Im(var, list):
        #     is_list = inferExprType(list, env, envOfPlans, program)
        #     if type(is_list[1]) is List:
        #         print()
        #     print(var, list, if_type, is_list)


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
                raise TypecheckError(f"Cannot match type arguments while calling plan {id}")
            if inputFits(id, input, envOfPlans, env, program, subEnv) and phiFits(id, phi, envOfPlans):
                out = typeOfOutput(id, output, envOfPlans, env, expr, subEnv)
                if expr.phi is not None:
                    for p_index in range(len(expr.phi)):
                        phi_op = phi[p_index]
                        phi_name = idOfVar(envOfPlans[id].phi[p_index])
                        subEnv[phi_name] = phi_op
                if expr.input is not None:
                    for in_index in range(len(expr.input)):
                        in_type = varDeclaredTyp(envOfPlans[id].input[in_index])
                        in_name = idOfVar(envOfPlans[id].input[in_index])
                        in_type = copyTyp(in_type, subEnv)
                        subEnv[in_name] = intToType(in_type)
                if not envOfPlans[id].output is []:
                    for out_index in range(len(envOfPlans[id].output)):
                        out_type = varDeclaredTyp(envOfPlans[id].output[out_index])
                        out_name = idOfVar(envOfPlans[id].output[out_index])
                        out_type = copyTyp(out_type, subEnv)
                        subEnv[out_name] = intToType(out_type)
                name, res = typecheckPlan(id, subEnv, envOfPlans, program)
                expr.id = name
                return (res, out)
            else:
                raise TypecheckError(f"Cannot match arguments while calling plan {id}")


def inputFits(id, input, envOfPlans, env, program, subEnv):
    if input is None:
        return envOfPlans[id].input[0] is None
    if len(input) != len(envOfPlans[id].input) or envOfPlans[id].input[0] is None:
        return False
    for i in range(len(input)):
        t1 = varDeclaredTyp(envOfPlans[id].input[i])
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
            res = varDeclaredTyp(envOfPlans[id].output[0])
            res = copyTyp(res, subEnv)
            expr.output = copyExpr(envOfPlans[id].output[0], subEnv)
            return res
        res = []
        expr.output = []
        for i in envOfPlans[id].output:
            t = [varDeclaredTyp(i)]
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
def variableCompType(typ, comp, env, envOfPlans, program):
    while not (comp is None):
        if type(comp[0]) is Index or type(comp[0]) is Variable or type(comp[0]) is Const:
            match typ:
                case List(lenght, elements):
                    typ = elements
                    comp = comp[1]
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
                    comp = comp[1]
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


def varDeclaredTyp(var):
    if isinstance(var, int):
        return types_dict[var]
    match var.typ:
        case List() | Tuple():
            return var.typ
        case MiUse(id):
            return var.typ
        case _:
            return types_dict[var.typ]


def intToType(var):
        if isinstance(var, int):
            return types_dict[var]
        else:
            return var

def varComp(var):
    return var.component


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
