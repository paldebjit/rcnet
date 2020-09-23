from pyverilog.vparser.ast import *

# TODO Comments

######## Mutation Types
MUTATION_TYPES = [
        "OPERATOR",
        "SIGNAL"
        ]

######## Valid Parent types
OP_PARENT_TYPES = [
        Assign,
        Substitution,
        NonblockingSubstitution,
        BlockingSubstitution,
        IfStatement,
        ForStatement,
        WhileStatement,
        CaseStatement,
        CasexStatement,
        CasezStatement,
        UniqueCaseStatement,
        Function,
        FunctionCall,
        Task,
        TaskCall,
        GenerateStatement
        ]

SIG_PARENT_TYPES = [
        Rvalue,
        PortArg,
        SensList
        ]

######## Operator types and their maps
OP_TYPES = {
        Uplus: 1,
        Uminus: 1,
        Ulnot: 1,
        Unot: 1,
        Uand: 1,
        Unand: 1,
        Uor: 1,
        Unor: 1,
        Uxor: 1,
        Uxnor: 1,
        Power: 2,
        Times: 2,
        Divide: 2,
        Mod: 2,
        Plus: 2,
        Minus: 2,
        Sll: 3,
        Srl: 3,
        Sla: 4,
        Sra: 4,
        LessThan: 5,
        GreaterThan: 5,
        LessEq: 5,
        GreaterEq: 5,
        Eq: 5,
        NotEq: 5,
        Eql: 5,
        NotEql: 5,
        And: 6,
        Xor: 6,
        Xnor: 6,
        Or: 6,
        Land: 6,
        Lor: 6
        }

OP_MAP = {}
for key,val in OP_TYPES.items():
    if val not in OP_MAP:
        OP_MAP[val] = []
    OP_MAP[val].append(key)


