from dataclasses import dataclass


number = int | float | tuple | str


@dataclass
class Const:
    value : number
    typ : str


@dataclass
class Variable:
    species : str
    id : int
    component : int | None | list | str
    typ : int

    def __str__(self):
        return f'{self.species}[{self.id},{self.component},{self.typ}]'


@dataclass
class Index:
    id : None | int


@dataclass
class Minus:
    left : 'Expression'
    right : 'Expression'
    typ : str


@dataclass
class Plus:
    left : 'Expression'
    right : 'Expression'
    typ : str


@dataclass
class Times:
    left : 'Expression'
    right : 'Expression'
    typ : str


@dataclass
class Divide:
    left : 'Expression'
    right : 'Expression'
    typ : str


@dataclass
class Equal:
    left : 'Expression'
    right : 'Expression'
    typ : str


@dataclass
class Greater:
    left : 'Expression'
    right : 'Expression'
    typ : str


@dataclass
class Lower:
    left : 'Expression'
    right : 'Expression'
    typ : str


@dataclass
class Neg:
    body : 'Expression'


@dataclass
class PhiDec:
    id : int


@dataclass
class PhiUse:
    id : int
    left : 'Expression'
    right : 'Expression'
    typ : str | None


@dataclass
class PhiCall:
    operator : str


@dataclass
class MiDec:
    id : int

@dataclass
class MiCall:
    typ : str


@dataclass
class MiUse:
    id : int


@dataclass
class PlanCall:
    id : tuple
    mi : list[MiCall]
    phi : list[PhiDec]
    input : list[Variable]
    output : list[Variable]


@dataclass
class Nfun:
    arg : Variable


@dataclass
class Ger:
    arg : 'Expression'


@dataclass
class Ord:
    arg : Variable


@dataclass
class Assign:
    expr : 'Expression'
    var : 'Variable'


@dataclass
class If:
    cond : 'Expression'
    then : 'Statement'


@dataclass
class While:
    typ : int
    start : int | None
    end : int | None
    body : 'Statement'


@dataclass
class Codeblock:
    content : list['Statement']


@dataclass
class Print:
    data : 'Expression'


@dataclass
class Fin:
    depth : None | int


@dataclass
class PlanDef:
    id : tuple
    mi : list
    phi : list
    input : list
    output : list
    body : 'Statement'


Expression = Const | Variable | Index | Minus | Plus | Times | Divide | Equal | Greater | Lower | Neg | PhiUse | PlanCall | Nfun | Ger | Ord
Statement = Assign | If | While | Codeblock | Print | Fin
Program = PlanDef


@dataclass
class List:
    lenght : int
    elements : str


@dataclass
class Tuple:
    elements : tuple
