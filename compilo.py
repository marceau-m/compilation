import lark

grammaire = lark.Lark("""
variables : IDENTIFIANT ("," IDENTIFIANT)*
expr : IDENTIFIANT -> variable | INTEGER -> int | FLOAT -> float | expr OP expr -> binexpr
| "(" expr ")" -> parenexpr | "(" TYPE ")" expr -> cast | "&" IDENTIFIANT -> adresse 
| "*" "*" IDENTIFIANT -> doublepointeur | "*" IDENTIFIANT -> pointeur
cmd : IDENTIFIANT "=" expr ";"-> assignment | "while" "(" expr ")" "{" bloc "}" -> while
| "if" "(" expr ")" "{" bloc "}" -> if | "printf" "(" expr ")" ";"-> printf 
|"*" "*" IDENTIFIANT "=" expr ";"-> doublepointerassignment | "*" IDENTIFIANT "=" expr ";"-> pointerassignment 
| IDENTIFIANT "=" "malloc" "(" expr ")" ";"-> pmalloc 
| "*" IDENTIFIANT "=" "malloc" "(" expr ")" ";"-> dpmalloc 
bloc : (cmd)*
prog : "main" "(" variables ")" "{" bloc "return" "(" expr ")" ";" "}"
INTEGER : /[-]?[0-9]+/
FLOAT : /[-]?[0-9]+\.[0-9]+/
OP : /[+\*>-]/
TYPE : /int|float/
IDENTIFIANT : /[a-zA-Z][a-zA-Z0-9]*/
%import common.WS
%ignore WS
""", start = "prog")

cpt = iter(range(10000)) #compteur pour boucles
cpt_const = 0
dict_float = dict()
dict_var = dict()
opint2asm = {"+": "add", "-": "sub", "*": "imul", ">": "cmp" }
opfloat2asm = {"+": "addsd", "-": "subsd", "*": "mulsd", ">": "comisd"}

def add_ind():
    global ind
    return ("".join("   " for i in range(ind)))


def pp_variables(vars):
    return ", ".join([t.value for t in vars.children])

def pp_type(type):
    if type.data == "typeint":
        return "int"
    elif type.data == "float":
        return "float"
    else:
        raise Exception("Not Implemented")

def pp_expr(expr):
    if expr.data in {"variable", "int", "float"}:
        return expr.children[0].value
    elif expr.data == "binexpr":
        e1 = pp_expr(expr.children[0])
        e2 = pp_expr(expr.children[2])
        op = expr.children[1].value
        return f"{e1} {op} {e2}"
    elif expr.data == "parenexpr":
        return f"({pp_expr(expr.children[0])})"
    elif expr.data == "pointeur":
        return f"*{expr.children[0].value}"
    elif expr.data == "doublepointeur":
        return f"**{expr.children[0].value}"
    elif expr.data == "adresse":
        return f"&{expr.children[0].value}"
    elif expr.data == "cast":
        t = expr.children[0].value
        e1 = pp_expr(expr.children[1])
        return f"({t}) {e1}"
    else:
        raise Exception("Not Implemented")

def pp_cmd(cmd):
    global ind
    if cmd.data == "assignment":
        lhs = cmd.children[0].value
        rhs = pp_expr(cmd.children[1])
        espace = add_ind()
        return f"{espace}{lhs} = {rhs};"
    elif cmd.data == "printf":
        espace = add_ind()
        return f"{espace}printf({pp_expr(cmd.children[0])});\n"
    elif cmd.data == "pmalloc":
        espace = add_ind()
        lhs = cmd.children[0].value
        rhs = pp_expr(cmd.children[1])
        return f"{espace}{lhs} = malloc({rhs});\n"
    elif cmd.data == "dpmalloc":
        espace = add_ind()
        lhs = cmd.children[0].value
        rhs = pp_expr(cmd.children[1])
        return f"{espace}*{lhs} = malloc({rhs});\n"
    elif cmd.data in {"while", "if"}:
        e = pp_expr(cmd.children[0])
        b = pp_bloc(cmd.children[1])
        espace = add_ind()
        ind += 1
        return f"{espace}{cmd.data} ({e}) {{ \n{b}}}\n"
    elif cmd.data == "pointerassignment":
        lhs = cmd.children[0].value
        rhs = pp_expr(cmd.children[1])
        espace = add_ind()
        return f"{espace}*{lhs} = {rhs};"
    elif cmd.data == "doublepointerassignment":
        lhs = cmd.children[0].value
        rhs = pp_expr(cmd.children[1])
        espace = add_ind()
        return f"{espace}**{lhs} = {rhs};"
    else:
        raise Exception("Not Implemented")
    return ""

def pp_bloc(bloc):
    return "\n".join([pp_cmd(t) for t in bloc.children])

def pp_prg(prog):
    global ind #pour l'indentation
    ind = 1
    vars = pp_variables(prog.children[0])
    bloc = pp_bloc(prog.children[1])
    ret = pp_expr(prog.children[2])
    return f"main ({vars}){{ \n{bloc}   return ({ret}); \n}}"
    


#prg2 = grammaire.parse(pp_prg(prg))
#print(prg2 == prg)
#print(pp_prg(prg))

def var_list(ast):
    if isinstance(ast, lark.Token):
        if ast.type == "IDENTIFIANT" or ast.type == "FLOAT":
            return {(ast.value,ast.type)}
        else:
            return set()
    s = set()
    for c in ast.children:
        s.update(var_list(c))
    return s

def compile(prg):
    global cpt_const
    with open("moule.asm") as f:
        code = f.read()
        vars_decl = ""
        for x in var_list(prg):
            if x[1] == "IDENTIFIANT":
                vars_decl += f"{x[0]}: dq 0\n"
                dict_var[x[0]] = "int"
            elif x[1] == "FLOAT":
                vars_decl += f"_float{cpt_const}: dq {x[0]}\n"
                dict_float[x[0]] = f"_float{cpt_const}"
                cpt_const+=1
        code = code.replace("VAR_DECL", vars_decl)
        code = code.replace("BODY", compile_bloc(prg.children[1]))
        code = code.replace("VAR_INIT", compile_vars(prg.children[0]))
        ret,typeret = compile_expr(prg.children[2])
        if typeret == "float":
            code = code.replace("RETURN",f"{ret}\nmov rdi, fmt_float\nmov rsi, rax\nmov rax, 1\ncall printf")
        elif typeret == "int":
            code = code.replace("RETURN",f"{ret}\nmov rdi, fmt_int\nmov rsi, rax\nxor rax, rax\ncall printf")
        return code

def compile_vars(ast):
    s = ""
    for i in range(len(ast.children)):
        s += f"mov rbx, [rbp-0x10]\nmov rdi,[rbx+{8*(i+1)}]\ncall atoi\nmov [{ast.children[i].value}], rax\n"
    return s

def compile_expr(expr):
    if expr.data == "variable":
        if dict_var[expr.children[0].value] == "int":
            return f"mov rax, [{expr.children[0].value}]\n","int"
        elif dict_var[expr.children[0].value] == "float":
            return f"movsd xmm0, [{expr.children[0].value}]\n","float"
    elif expr.data == "int":
        return f"mov rax, {expr.children[0].value}","int"
    elif expr.data == "float":
        return f"movsd xmm0, [{dict_float[expr.children[0].value]}]","float"
    elif expr.data == "binexpr":
        OP = expr.children[1].value
        e1, typee1 = compile_expr(expr.children[0])
        e2, typee2 = compile_expr(expr.children[2])
        if typee1 == "float" or typee2 == "float":
            conv1=""
            conv2=""
            if typee1 != "float":
                conv1 = "cvtsi2sd xmm0, rax\n"
            if typee2 != "float":
                conv2 = "cvtsi2sd xmm0, rax\n"
            if expr.children[1].value == ">" :
                typeres = "boolfloat"
            else :
                typeres = "float"
            return f"{e2}\n{conv2}movq rax, xmm0\npush rax\n{e1}\n{conv1}pop rbx\nmovq xmm1, rbx\n{opfloat2asm[OP]} xmm0, xmm1",typeres
        else:
            if expr.children[1].value == ">" :
                typeres = "boolint"
            else :
                typeres = "int"
            return f"{e2}\npush rax\n{e1}\npop rbx\n{opint2asm[OP]} rax, rbx",typeres
    elif expr.data == "parenexpr":
        return compile_expr(expr.children[0])
    elif expr.data == "pointeur":
        return f"mov rcx, [{expr.children[0].value}]\nmov rax, [rcx]\n","int"

    elif expr.data == "doublepointeur":
        return f"mov rcx, [{expr.children[0].value}]\nmov rdx, [rcx]\nmov rax, [rdx]\n","int"

    elif expr.data == "adresse":
        return f"mov rax, {expr.children[0].value}\n","int"
    elif expr.data == "cast":
        e1, typee1 = compile_expr(expr.children[1])
        nouv_type = expr.children[0]
        convertir = ""
        type_sortie = nouv_type.value
        if typee1 == "int": #si on doit convertir int to float
            if type_sortie == "float":
                convertir = "cvtsi2sd xmm0, rax\n"
        elif typee1 == "float": #si on doit convertir float to int
            if type_sortie == "int":
                convertir = "cvttsd2si rax, xmm0\n"
        return f"{e1}\n{convertir}", type_sortie
    else:
        raise Exception("Not implemented")

def compile_cmd(cmd):
    if cmd.data == "assignment":
        lhs = cmd.children[0].value
        rhs, typerhs = compile_expr(cmd.children[1])
        if typerhs == "float":
            dict_var[lhs]="float"
            return f"{rhs}\nmovsd [{lhs}], xmm0\n"
        elif typerhs == "int":
            dict_var[lhs]="int"
            return f"{rhs}\nmov [{lhs}],rax"
        elif typerhs == "boolfloat":
            dict_var[lhs] = "float"
            return f"{rhs}\nseta al\nmovzx rax, al\nmov [{lhs}],rax\n"
        elif typerhs == "boolint":
            dict_var[lhs] = "int"
            return f"{rhs}\nsetg al\nmovzx rax, al\nmov [{lhs}],rax\n"
    elif cmd.data == "while":
        e1, typee1 = compile_expr(cmd.children[0]) #au premier tour dans a boucle
        b1 = compile_bloc(cmd.children[1])
        e2, typee2 = compile_expr(cmd.children[0]) #pour les tours suivants
        b2 = compile_bloc(cmd.children[1])
        if cmd.children[0].data == "binexpr":
            jump = "jna"
            comp1 = ""
            comp2 = ""
        else:
            jump = "jle"
            if typee1 == "int":
                comp1 = "cmp rax,0\n"
            elif typee1 == "float":
                comp1 = "pxor xmm1,xmm1\ncomisd xmm0,xmm1\n" #equivaut a cmp rax,0 avec un float
            if typee2 == "int":
                comp2 = "cmp rax,0\n"
            elif typee2 == "float":
                comp2 = "pxor xmm1,xmm1\ncomisd xmm0,xmm1\n" #equivaut a cmp rax,0 avec un float
        index = next(cpt)
        return f"{e1}\n{comp1}\n{jump} fin{index}\n{b1}\ndebut{index}:\n{e2}\n{comp2}\n{jump} fin{index}\n{b2}\njmp debut{index}\nfin{index}:\n"
    elif cmd.data == "if":
        e,typee = compile_expr(cmd.children[0])
        b = compile_bloc(cmd.children[1])
        if cmd.children[0].data == "binexpr":
            jump = "jna"
            comp = ""
        else:
            jump = "jle"
            if typee == "int":
                comp = "cmp rax,0\n"
            elif typee == "float":
                comp = "pxor xmm1,xmm1\ncomisd xmm0,xmm1\n" #equivaut a cmp rax,0 avec un float
        index = next(cpt)
        return f"{e}\n{comp}\n{jump} fin{index}\n{b}\nfin{index}:\n"
    elif cmd.data == "printf":
        e, typee = compile_expr(cmd.children[0])
        if typee == "float":
            return f"{e}\nmov rdi, fmt_float\nmov rsi, rax\nmov rax, 1\ncall printf\n"
        elif typee == "int":
            return f"{e}\nmov rdi, fmt_int\nmov rsi, rax\nxor rax, rax\ncall printf\n"
    elif cmd.data == "pointerassignment":
        lhs = cmd.children[0].value
        rhs, typerhs = compile_expr(cmd.children[1])
        dict_var[lhs]="int"
        return f"{rhs}\nmov rbx,[{lhs}]\n mov [rbx],rax"
    elif cmd.data == "doublepointerassignment":
        lhs = cmd.children[0].value
        rhs, typerhs = compile_expr(cmd.children[1])
        dict_var[lhs]="int"
        return f"{rhs}\nmov rbx,[{lhs}]\nmov rcx, [rbx]\nmov [rcx],rax"
    elif cmd.data == "pmalloc":
        lhs = cmd.children[0].value
        rhs, typerhs = compile_expr(cmd.children[1])
        return f"{rhs}\nmov rdi,rax\ncall malloc\nmov [{lhs}],rax\n"
    elif cmd.data == "dpmalloc" :
        lhs = cmd.children[0].value
        rhs, typerhs = compile_expr(cmd.children[1])
        return f"{rhs}\nmov rdi,rax\ncall malloc\nmov rbx, [{lhs}]\nmov [rbx],rax\n"

    else:
        raise Exception("Not implemented")

def compile_bloc(bloc):
    return "\n".join([compile_cmd(t) for t in bloc.children])

data = open("exemples/example1.cmm","r")
prg = grammaire.parse(data.read())

print(compile(prg))