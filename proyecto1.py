from graphviz import Digraph
import re

class Nodo:
    def __init__(self, value):
        self.value = value
        self.left = None
        self.right = None

class Estado:
    def __init__(self, id):
        self.id = id
        self.transiciones = {}
        self.epsilon_transiciones = set()

class AFN:
    def __init__(self, start, accept):
        self.start = start
        self.accept = accept
        self.estados = {start, accept}

    def agregar_transicion(self, origen, simbolo, destino):
        origen.transiciones.setdefault(simbolo, set()).add(destino)
        self.estados.add(origen)
        self.estados.add(destino)

    def agregar_transicion_epsilon(self, origen, destino):
        origen.epsilon_transiciones.add(destino)
        self.estados.add(origen)
        self.estados.add(destino)

class AFD:
    def __init__(self, start, accept):
        self.start = start
        self.accept = accept
        self.estados = {start}
        self.transiciones = {}

    def agregar_transicion(self, estado, simbolo, destino):
        if estado not in self.transiciones:
            self.transiciones[estado] = {}
        self.transiciones[estado][simbolo] = destino
        self.estados.add(estado)
        self.estados.add(destino)

def infix_a_postfix(infix):
    precedence = {'|': 1, '.': 2, '*': 3}
    output, stack = [], []
    for char in infix:
        if char == ' ':
            continue
        if char.isalnum():
            output.append(char)
        elif char == '(':
            stack.append(char)
        elif char == ')':
            while stack and stack[-1] != '(':
                output.append(stack.pop())
            stack.pop()
        else:
            while stack and stack[-1] != '(' and precedence.get(stack[-1], 0) >= precedence.get(char, 0):
                output.append(stack.pop())
            stack.append(char)
    while stack:
        output.append(stack.pop())
    return ''.join(output)

def formatear(regex):
    regex = regex.replace('+', '.*').replace('?', '|ε')
    regex = re.sub(r'\[([^\]]+)\]', lambda m: '|'.join(m.group(1)), regex)
    return regex.replace('(', '( ').replace(')', ' )').replace('*', ' * ').replace('.', ' . ').replace('|', ' | ')

def postfix_a_ast(postfix):
    stack = []
    for char in postfix:
        node = Nodo(char)
        if char in {'|', '.'}:
            node.right = stack.pop()
            node.left = stack.pop()
        elif char == '*':
            node.left = stack.pop()
        stack.append(node)
    return stack.pop()

def construir_afn_thompson(node):
    if node.value == '|':
        left_afn = construir_afn_thompson(node.left)
        right_afn = construir_afn_thompson(node.right)
        start, accept = Estado(f"s{len(left_afn.estados) + len(right_afn.estados)}"), Estado(f"s{len(left_afn.estados) + len(right_afn.estados) + 1}")
        afn = AFN(start, accept)
        afn.agregar_transicion_epsilon(start, left_afn.start)
        afn.agregar_transicion_epsilon(start, right_afn.start)
        afn.agregar_transicion_epsilon(left_afn.accept, accept)
        afn.agregar_transicion_epsilon(right_afn.accept, accept)
        afn.estados.update(left_afn.estados)
        afn.estados.update(right_afn.estados)
        return afn
    elif node.value == '.':
        left_afn = construir_afn_thompson(node.left)
        right_afn = construir_afn_thompson(node.right)
        afn = AFN(left_afn.start, right_afn.accept)
        afn.agregar_transicion_epsilon(left_afn.accept, right_afn.start)
        afn.estados.update(left_afn.estados)
        afn.estados.update(right_afn.estados)
        return afn
    elif node.value == '*':
        sub_afn = construir_afn_thompson(node.left)
        start, accept = Estado(f"s{len(sub_afn.estados)}"), Estado(f"s{len(sub_afn.estados) + 1}")
        afn = AFN(start, accept)
        afn.agregar_transicion_epsilon(start, sub_afn.start)
        afn.agregar_transicion_epsilon(sub_afn.accept, accept)
        afn.agregar_transicion_epsilon(start, accept)
        afn.agregar_transicion_epsilon(sub_afn.accept, sub_afn.start)
        afn.estados.update(sub_afn.estados)
        return afn
    else:
        start, accept = Estado(f"s{node.value}_start"), Estado(f"s{node.value}_accept")
        afn = AFN(start, accept)
        afn.agregar_transicion(start, node.value, accept)
        return afn

def construir_afd_afn(afn):
    start_closure = epsilon_closure({afn.start})
    afd_start = frozenset(start_closure)
    afd = AFD(afd_start, None)
    estados_d = {afd_start}
    no_marcados = [afd_start]
    
    while no_marcados:
        t = no_marcados.pop()
        for simbolo in set(simbolo for estado in t for simbolo in estado.transiciones):
            u = epsilon_closure({destino for estado in t for destino in estado.transiciones.get(simbolo, [])})
            u = frozenset(u)
            if u not in estados_d:
                estados_d.add(u)
                no_marcados.append(u)
            afd.agregar_transicion(t, simbolo, u)
    
    afd.accept = afd_start
    return afd

def epsilon_closure(states):
    stack = list(states)
    closure = set(states)
    while stack:
        state = stack.pop()
        for next_state in state.epsilon_transiciones:
            if next_state not in closure:
                closure.add(next_state)
                stack.append(next_state)
    return closure

def simular_afn(afn, cadena):
    current_states = epsilon_closure({afn.start})
    for simbolo in cadena:
        next_states = set()
        for state in current_states:
            next_states.update(estado for destino in state.transiciones.get(simbolo, []) for estado in epsilon_closure({destino}))
        current_states = next_states
    return any(state == afn.accept for state in current_states)

def draw_ast(node, filename='ast'):
    dot = Digraph()
    
    def add_nodes_edges(node):
        if node is not None:
            dot.node(str(id(node)), node.value)
            if node.left:
                dot.edge(str(id(node)), str(id(node.left)))
                add_nodes_edges(node.left)
            if node.right:
                dot.edge(str(id(node)), str(id(node.right)))
                add_nodes_edges(node.right)

    add_nodes_edges(node)
    dot.render(filename, format='png', cleanup=True)
    print(f"AST generado y guardado en {filename}.png")

def draw_afn(afn, filename='afn'):
    dot = Digraph()
    for estado in afn.estados:
        dot.node(estado.id, shape='doublecircle' if estado == afn.accept else 'circle')
        for simbolo, destinos in estado.transiciones.items():
            for destino in destinos:
                dot.edge(estado.id, destino.id, label=simbolo)
        for destino in estado.epsilon_transiciones:
            dot.edge(estado.id, destino.id, label='ε')
    dot.render(filename, format='png', cleanup=True)
    print(f"AFN generado y guardado en {filename}.png")

# Función para minimizar el AFD
def minimizar_afd(afd):
    # Particionar estados en aceptadores y no aceptadores
    P = [{estado for estado in afd.estados if estado != afd.accept}, {afd.accept}]
    W = [{afd.accept}]
    
    while W:
        A = W.pop()
        for simbolo in afd.transiciones[next(iter(afd.transiciones))].keys():  # Considerar todos los símbolos
            X = {estado for estado in afd.estados if simbolo in afd.transiciones.get(estado, {}) and afd.transiciones[estado][simbolo] in A}
            new_P = []
            for Y in P:
                interseccion = X.intersection(Y)
                diferencia = Y.difference(X)
                if interseccion and diferencia:
                    P.remove(Y)
                    P.append(interseccion)
                    P.append(diferencia)
                    if Y in W:
                        W.remove(Y)
                        W.append(interseccion)
                        W.append(diferencia)
                    else:
                        W.append(interseccion if len(interseccion) <= len(diferencia) else diferencia)
            P.extend(new_P)
    
    # Crear nuevo AFD minimizado
    estado_map = {frozenset(part): Estado(f"s{index}") for index, part in enumerate(P)}
    afd_min = AFD(estado_map[frozenset({afd.start})], estado_map[frozenset({afd.accept})])
    
    for part in P:
        representativo = next(iter(part))
        estado_origen = estado_map[frozenset(part)]
        for simbolo, estado_destino in afd.transiciones.get(representativo, {}).items():
            part_destino = next(part for part in P if estado_destino in part)
            afd_min.agregar_transicion(estado_origen, simbolo, estado_map[frozenset(part_destino)])
    
    return afd_min

# Dibuja el AFD utilizando graphviz
def draw_afd(afd, filename='afd'):
    dot = Digraph()

    # Convertir el estado a una cadena para su representación
    for estado in afd.estados:
        estado_str = estado.id  # Utiliza directamente el id del estado
        dot.node(estado_str, shape='doublecircle' if estado == afd.accept else 'circle')

    # Dibujar transiciones
    for estado, transiciones in afd.transiciones.items():
        estado_str = estado.id  # Utiliza directamente el id del estado
        for simbolo, destino in transiciones.items():
            destino_str = destino.id  # Utiliza directamente el id del destino
            dot.edge(estado_str, destino_str, label=simbolo)

    dot.render(filename, format='png', cleanup=True)  # Guarda el AFD en un archivo 'filename.png'
    print(f"AFD generado y guardado en {filename}.png")


def main():
    with open('input.txt', 'r') as file:
        for regex in file:
            regex = regex.strip()
            formatted_regex = formatear(regex)
            postfix = infix_a_postfix(formatted_regex)
            ast_root = postfix_a_ast(postfix)
            draw_ast(ast_root, filename='ast')
            afn = construir_afn_thompson(ast_root)
            draw_afn(afn, filename='afn')
            afd = construir_afd_afn(afn)
            afd_min = minimizar_afd(afd)  # Minimizar el AFD antes de dibujarlo
            draw_afd(afd_min, filename='afd_min')  # Dibuja el AFD minimizado
            cadena = input(f"Ingrese una cadena para verificar con la expresión '{regex}': ")
            print(f"La cadena '{cadena}' es {'aceptada' if simular_afn(afn, cadena) else 'NO aceptada'} por el AFN.")

if __name__ == '__main__':
    main()
