import lark 

grammaire = lark.Lark("""
variables : IDENTIFIANT ("," IDENTIFIANT)*
expr : IDENTIFIANT -> variable | INTEGER -> int | FLOAT -> float | expr OP expr -> binexpr 
| "(" expr ")" -> parenexpr | "(" TYPE ")" expr -> cast
cmd : IDENTIFIANT "=" expr ";"-> assignment | "tant que" "(" expr ")" "{" bloc "}" -> while
    | "si" "(" expr ")" "{" bloc "}" -> if | "affiche" "(" expr ")" ";"-> printf 
bloc : (cmd)*
prog : "principale" "(" variables ")" "{" bloc "renvoie" "(" expr ")" ";" "}"
INTEGER: /[-]?[0-9]+/
FLOAT : /[-]?[0-9]+\.[0-9]+/
OP : /[+\*>-]/
TYPE : /int|float/
IDENTIFIANT : /[a-zA-Z][a-zA-Z0-9]*/
%import common.WS 
%ignore WS
""", start = "prog")
#WS = White Space
#binexpr et parentexpr permet d'être plus précis dans le type d'expression utilisée

cpt = iter(range(10000)) #compteur pour while
cpt_const = 0
dict_float = dict()
dict_var =dict()
opint2asm = {"+": "add", "-": "sub", "*": "imul", ">": "cmp" }
opfloat2asm = {"+": "addsd", "-": "subsd", "*": "mulsd", ">": "comisd"}

def add_ind():
    global ind
    return ("".join("   " for i in range(ind)))

def pp_var(vars):
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
        e2= pp_expr(expr.children[2])
        op = expr.children[1].value
        return f"{e1} {op} {e2}"
    elif expr.data == "parenexpr" :
        return f"({pp_expr(expr.children[0])})"
    elif expr.data == "cast":
        t = expr.children[0].value
        e1 = pp_expr(expr.children[1])
        return f"({t}) {e1}"
    else : 
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
        return f"{espace}affiche({pp_expr(cmd.children[0])});\n"
    elif cmd.data == "while":
        e = pp_expr(cmd.children[0])
        b = pp_bloc(cmd.children[1])
        espace = add_ind()
        ind += 1
        return f"{espace}tant que ({e}) {{ \n{b}}} \n"
    elif cmd.data == "if":
        e = pp_expr(cmd.children[0])
        b = pp_bloc(cmd.children[1])
        espace = add_ind()
        ind += 1
        return f"{espace}si ({e}) {{ \n{b}}}\n"
    else :
        raise Exception("Not Implemented")
    return ""

def pp_bloc(bloc):
    return "\n".join([pp_cmd(t) for t in bloc.children])

def pp_prg(prog): #pretty printer = jolie afficheur
    global ind #pour l'indentation
    ind = 1
    vars = pp_var(prog.children[0])
    bloc = pp_bloc(prog.children[1])
    ret = pp_expr(prog.children[2])
    return f"principale({vars}) {{ \n{bloc}   renvoie({ret}); \n}}"

prg = grammaire.parse("""principale(X,Y) { 
    si (X) { 
        X = X+1.2;
        Y = Y+X;
        Y = (int) X;
        affiche(X); 
        } 
    renvoie(Y+1);
    }""")


#prg2 = grammaire.parse(pp_prg(prg))
#print(prg2 == prg)
#print(pp_prg(prg))

#print(prg)
#Il faut tester tout quand on modifie la grammaire (X, 1333, X+133, ...)
#X+133 renvoie : Tree(rule:expr,[X,+,133]) (en moche avec des tree, token,expr, number, id, ...)
#exemple : principale(X,Y) { si (X) { affiche(X); } renvoie(Y);}
#amélioration possible : rajouter les sauts de ligne et les indentations 

def assembl_prog(prog):
    vars = pp_var(prog.children[0])
    bloc = assembl_bloc(prog.children[1])
    ret = assembl_expr(prog.children[2])
    return f"principale({vars}) {{ \n{bloc}   renvoie({ret}); \n}}" #mettre les global, section,...

def assembl_expr(expr):
    if expr.data == "variable":
        return f"mov rax,[{expr.children[0].value}]\n"
    elif expr.data in {"int","float"}:
        return f"mov rax,{expr.children[0].value}\n"
    elif expr.data == "binexpr":
        e1 = assembl_expr(expr.children[0])
        e2= assembl_expr(expr.children[2])
        op = expr.children[1].value
        if op == "+":
            return f"{e1}\npush rax\n{e2}\npop rbx\npop rax\nadd rax,rbx\n"
    elif expr.data == "parenexpr" :
        return f"{assembl_expr(expr.children[0])}\n"
    else : 
        #print(expr.data)
        raise Exception("Not Implemented")

def assembl_cmd(cmd):
    if cmd.data == "assignment":
        lhs = cmd.children[0].value
        rhs = cmd.children[1]
        return f"{assembl_expr(rhs)} mov [{lhs}],rax\n"
    elif cmd.data == "printf":
        return f"{assembl_expr(cmd.children[0])} mov rdi,fmt\nmov rsi,rax\nxor rax,rax\ncall printf\n"
    elif cmd.data == "while":
        return f"{assembl_expr(cmd.children[0])} cmp rax,0\njz fin\n{assembl_expr(cmd.children[1])} jmp debut\n"
    elif cmd.data == "if":
        e = cmd.children[0]
        b = cmd.children[1]
        return f"{assembl_expr(e)} cpm rax,0\njz fin\n{assembl_expr(b)} jmp debut\n"
    else :
        raise Exception("Not Implemented")
    return ""

def assembl_bloc(bloc):
        return "\n".join([assembl_cmd(t) for t in bloc.children])

#print(assembl_prog(prg))

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
        code = code.replace("BODY", compile_bloc(prg.children[1].children))
        ret,typeret = compile_expr(prg.children[2])
        if typeret == "float":
            code = code.replace("RETURN",f"{ret}\nmov rdi, fmt_float\nmov rsi, rax\nmov rax, 1\ncall printf")
        elif typeret == "int":
            code = code.replace("RETURN",f"{ret}\nmov rdi, fmt_int\nmov rsi, rax\nxor rax, rax\ncall printf")
        code = code.replace("BODY", compile_bloc(prg.children[1].children))
        code = code.replace("VAR_INIT", compile_vars(prg.children[0]))
        return code

def compile_vars(ast):
    s = ""
    for i in range(len(ast.children)):
        s += f"mov rbx, [rbp-0x10]\nmov rdi,[rbx+{8*(i+1)}]\ncall atoi\nmov [{ast.children[i].value}], rax\n"
    return s

def compile_expr(expr, dict_variables = dict_var):
    if expr.data == "variable":
        if dict_variables[expr.children[0].value] == "int":
            return f"mov rax, [{expr.children[0].value}]\n","int"
        elif dict_variables[expr.children[0].value] == "float":
            return f"movsd xmm0, [{expr.children[0].value}]\n","float"
    elif expr.data == "int":
        return f"mov rax, {expr.children[0].value}","int"
    elif expr.data == "float":
        return f"movsd xmm0, [{dict_float[expr.children[0].value]}]","float"
    elif expr.data == "binexpr": #remettre la comparaison
        OP = expr.children[1].value
        e1, typee1 = compile_expr(expr.children[0],dict_variables)
        e2, typee2 = compile_expr(expr.children[2],dict_variables)
        if typee1 == "float" or typee2 == "float":
            conv1=""
            conv2=""
            if typee1 != "float":
                conv1 = "cvtsi2sd xmm0, rax\n"
            elif typee2 != "float":
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
        return compile_expr(expr.children[0],dict_variables)
    elif expr.data == "cast":
        e1, typee1 = compile_expr(expr.children[1],dict_variables)
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


def compile_cmd(cmd, dict_variables=dict_var):
    if cmd.data == "assignment":
        lhs = cmd.children[0].value
        rhs, typerhs = compile_expr(cmd.children[1],dict_variables)
        if typerhs == "float":
            dict_variables[lhs]="float"
            return f"{rhs}\nmovsd [{lhs}], xmm0\n",0,dict_variables
        elif typerhs == "int":
            dict_variables[lhs]="int"
            return f"{rhs}\nmov [{lhs}],rax",0,dict_variables
        elif typerhs == "boolfloat":
            dict_variables[lhs] = "float"
            return f"{rhs}\nseta al\nmovzx rax, al\nmov [{lhs}],rax\n",0,dict_variables
        elif typerhs == "boolint":
            dict_variables[lhs] = "int"
            return f"{rhs}\nsetg al\nmovzx rax, al\nmov [{lhs}],rax\n",0,dict_variables
    elif cmd.data == "while":
        types_avant = dict_variables.copy() #on memorise au cas où on ne rentre pas dans la boucle
        e1, typee1 = compile_expr(cmd.children[0],dict_variables) #au premier tour dans a boucle
        b1 = compile_bloc(cmd.children[1].children,dict_variables)
        e2, typee2 = compile_expr(cmd.children[0],dict_variables) #pour les tours suivants
        b2 = compile_bloc(cmd.children[1].children,dict_variables)
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
        index_suiv = next(cpt)
        return f"\n{e1}\n{comp1}\n{jump} fin{index}\n{b1}\ndebut{index}:\n{e2}\n{comp2}\n{jump} fin{index_suiv}\n{b2}\njmp debut{index}\nfin{index}:",index_suiv,types_avant
    elif cmd.data == "if":
        e,typee = compile_expr(cmd.children[0],dict_variables)
        b = compile_bloc(cmd.children[1].children,dict_variables)
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
        return f"{e}\n{comp}\n{jump} fin{index}\n{b}\nfin{index}:\n",0,dict_variables #a modifier
    elif cmd.data == "printf":
        e, typee = compile_expr(cmd.children[0],dict_variables)
        if typee == "float":
            return f"{e}\nmov rdi, fmt_float\nmov rsi, rax\nmov rax, 1\ncall printf\n",0,dict_variables
        elif typee == "int":
            return f"{e}\nmov rdi, fmt_int\nmov rsi, rax\nxor rax, rax\ncall printf\n",0,dict_variables
    else:
        raise Exception("Not implemented")

def compile_bloc(children, dict_variables = dict_var):
    sortie =""
    disjonct = False
    types_avant = None
    for i in range(len(children)):
        t = children[i]
        if disjonct:
            #sortie += "disjonction"
            #si on est pas rentré dans la boucle
            disjonct = False
            b, index_suiv,types = compile_cmd(t,types_avant) #on ne met pas à jour dict_var
            sortie += f"\n{b}" + compile_bloc(children[(i+1):],types)+ f"\njmp fin{indice_prec+1}\n" 
            #si on est rentré dedans
            b, index_suiv,types = compile_cmd(t,dict_variables) 
            sortie += f"\nfin{indice_prec}:\n{b}" + compile_bloc(children[(i+1):],types) + f"\nfin{indice_prec+1}:\n"
            return sortie
        else :
            b, index_suiv,types = compile_cmd(t) #on maj dict_var
            if index_suiv:
                disjonct = True
                sortie += f"\n{b}"
                indice_prec = index_suiv
                a = next(cpt)
                types_avant = types.copy()
            else:
              sortie += f"\n{b}"
    return sortie



prg7 = grammaire.parse("""principale(X) {
    Z = 1;
    Y = 2;
    affiche(Y);
    si(Z>Y) {
        Y = Y + 1.2;
        Z = Z - 1;
        affiche(Y);
    }
    affiche(Y);
    affiche(Z);
    renvoie(X);}""")

prg8 = grammaire.parse("""principale(X) {
    Z = 1;
    Y = 2;
    tant que(Z>Y) {
        Y = 1;
    }
    tant que(Y) {
        Y = 0;
    }
    Y = 3;
    renvoie(Y);}""")

print(compile(prg7))
