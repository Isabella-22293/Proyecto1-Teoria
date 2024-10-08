from graphviz import Digraph

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

def nuevo_estado(id_counter=[0]):
    estado_id = f"s{id_counter[0]}"
    id_counter[0] += 1
    return Estado(estado_id)

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
    precedence = {'|': 1, '.': 2, '*': 3}  # Precedencia de los operadores
    output, stack = [], []
    for char in infix:
        if char == ' ':
            continue
        if char.isalnum() or char == 'ε':  # Agregar ε como literal
            output.append(char)
        elif char == '(':
            stack.append(char)
        elif char == ')':
            while stack and stack[-1] != '(':
                output.append(stack.pop())
            stack.pop()  # Pop the '('
        else:
            while stack and stack[-1] != '(' and precedence.get(stack[-1], 0) >= precedence.get(char, 0):
                output.append(stack.pop())
            stack.append(char)
    while stack:
        output.append(stack.pop())
    return ''.join(output)
 
def formatear(regex):
    # Almacenar la expresión formateada
    resultado = []
    i = 0
    while i < len(regex):
        if regex[i] == '\\':  # Manejar caracteres escapados
            resultado.append(regex[i:i + 2])
            i += 2
        elif regex[i] in {'*', '+', '?', '|', '(', ')'}:  # Operadores especiales y paréntesis
            resultado.append(regex[i])
            i += 1
        else:  # Caracteres normales
            resultado.append(regex[i])
            i += 1
    
    # Preparar para insertar operadores de concatenación
    final_resultado = []
    for i in range(len(resultado)):
        final_resultado.append(resultado[i])
        # No insertar un '.' después de operadores especiales o antes de '|' y ')'
        if i < len(resultado) - 1:
            prev, curr = resultado[i], resultado[i + 1]
            # Agregar un '.' cuando es necesario
            if (prev not in {'(', '|'} and
                curr not in {')', '*', '+', '?', '|'}):
                final_resultado.append('.')
    
    return ''.join(final_resultado)


def postfix_a_ast(postfix):
    stack = []
    for char in postfix:
        node = Nodo(char)
        if char in {'|', '.'}:  # Operadores binarios
            if len(stack) < 2:
                raise ValueError("Not enough operands for binary operator")
            node.right = stack.pop()
            node.left = stack.pop()
        elif char == '*':  # Operador unario
            if len(stack) < 1:
                raise ValueError("Not enough operands for unary operator")
            node.left = stack.pop()
        stack.append(node)
    
    if len(stack) != 1:
        raise ValueError("The postfix expression did not produce a valid AST")
    
    return stack.pop()


def construir_afn_thompson(node):
    if node.value == '|':  # Unión
        left_afn = construir_afn_thompson(node.left)
        right_afn = construir_afn_thompson(node.right)
        start, accept = nuevo_estado(), nuevo_estado()
        afn = AFN(start, accept)
        afn.agregar_transicion_epsilon(start, left_afn.start)
        afn.agregar_transicion_epsilon(start, right_afn.start)
        afn.agregar_transicion_epsilon(left_afn.accept, accept)
        afn.agregar_transicion_epsilon(right_afn.accept, accept)
        afn.estados.update(left_afn.estados)
        afn.estados.update(right_afn.estados)
        return afn
    
    elif node.value == '.':  # Concatenación
        left_afn = construir_afn_thompson(node.left)
        right_afn = construir_afn_thompson(node.right)
        afn = AFN(left_afn.start, right_afn.accept)
        afn.agregar_transicion_epsilon(left_afn.accept, right_afn.start)
        afn.estados.update(left_afn.estados)
        afn.estados.update(right_afn.estados)
        return afn

    elif node.value == '*':  # Kleene Star
        sub_afn = construir_afn_thompson(node.left)
        start, accept = nuevo_estado(), nuevo_estado()
        afn = AFN(start, accept)

        afn.agregar_transicion_epsilon(start, sub_afn.start)
        afn.agregar_transicion_epsilon(sub_afn.accept, accept)
        afn.agregar_transicion_epsilon(start, accept)
        afn.agregar_transicion_epsilon(sub_afn.accept, sub_afn.start)
        afn.estados.update(sub_afn.estados)
        return afn

    else:  # Símbolo literal
        start, accept = nuevo_estado(), nuevo_estado()
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

def minimizar_afd(afd):
    P = [{estado for estado in afd.estados if estado != afd.accept}, {afd.accept}]
    W = [{afd.accept}]
    
    while W:
        A = W.pop()
        for simbolo in set(simbolo for estado in afd.estados for simbolo in afd.transiciones.get(estado, {})):
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
    
    estado_map = {frozenset(part): Estado(f"s{index}") for index, part in enumerate(P)}
    afd_min = AFD(estado_map[frozenset({afd.start})], estado_map[frozenset({afd.accept})])
    
    for part in P:
        representativo = next(iter(part))
        estado_origen = estado_map[frozenset(part)]
        for simbolo, estado_destino in afd.transiciones.get(representativo, {}).items():
            part_destino = next(part for part in P if estado_destino in part)
            afd_min.agregar_transicion(estado_origen, simbolo, estado_map[frozenset(part_destino)])
    
    return afd_min

def draw_afd(afd, filename='afd'):
    dot = Digraph()

    # Dibujar los nodos del AFD
    for estado in afd.estados:
        # Aquí, estado es un frozenset, así que necesitamos extraer el id del primer estado en el frozenset
        estado_id = next(iter(estado)).id
        dot.node(estado_id, shape='doublecircle' if estado == afd.accept else 'circle')

    # Dibujar las transiciones del AFD
    for estado, transiciones in afd.transiciones.items():
        estado_id = next(iter(estado)).id  # Obtener el id del primer estado en el frozenset
        for simbolo, destino in transiciones.items():
            destino_id = next(iter(destino)).id  # Obtener el id del primer estado en el frozenset
            dot.edge(estado_id, destino_id, label=simbolo)

    dot.render(filename, format='png', cleanup=True)  # Guarda el AFD en un archivo 'filename.png'
    print(f"AFD generado y guardado en {filename}.png")

def draw_afd_normal(afd, filename='afd_normal'):
    draw_afd(afd, filename)  # Usa la misma función para dibujar el AFD normal

def main():
    global estado_counter
    with open('input.txt', 'r') as file:
        for regex in file:
            regex = regex.strip()
            formatted_regex = formatear(regex)
            postfix = infix_a_postfix(formatted_regex)
            ast_root = postfix_a_ast(postfix)
            draw_ast(ast_root, filename='ast')
            estado_counter = 0
            afn = construir_afn_thompson(ast_root)
            draw_afn(afn, filename='afn')
            afd = construir_afd_afn(afn)
            draw_afd_normal(afd, filename='afd_normal')  # Generar y guardar el AFD normal
            afd_min = minimizar_afd(afd)
            draw_afd(afd_min, filename='afd_min')
            
            cadena = input(f"Ingrese una cadena para verificar con la expresión '{regex}': ")
            print(f"La cadena '{cadena}' es {'aceptada' if simular_afn(afn, cadena) else 'NO aceptada'} por el AFN.")

if __name__ == '__main__':
    main()
