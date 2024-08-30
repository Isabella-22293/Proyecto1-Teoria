from graphviz import Digraph
import networkx as nx
import matplotlib.pyplot as plt

epsilon = 'ε'
operadores = {'|', '.', '*', '+', '?'}
precedencia_operador = {
    '(': 1,
    '|': 2,
    '.': 3,
    '?': 4,
    '*': 4,
    '+': 4,
}

def get_precedence(op):
    return precedencia_operador.get(op, 0)

def format_reg_ex(regex):
    formatted = []
    escaped = False

    i = 0 
    while i < len(regex):
        c1 = regex[i]

        if escaped:
            formatted.append('\\' + c1)
            escaped = False
        elif c1 == '\\':
            escaped = True
        else:
            if c1 == '+' or c1 == '?':
                if len(formatted) > 0:
                    formatted.append(c1)
            elif c1 == '*':
                if len(formatted) > 0 and formatted[-1] != '|':
                    formatted.append(c1)
            else:
                if i + 1 < len(regex):
                    c2 = regex[i + 1]
                    formatted.append(c1)
                    if c1 not in ('(', '|') and c2 not in (')', '|', '?', '*', '+', '('):
                        formatted.append('.')
                else:
                    formatted.append(c1)
        i += 1
    return ''.join(formatted)

def infix_a_postfix(regex):
    postfix = []
    stack = []
    regex_formateado = format_reg_ex(regex)
    for c in regex_formateado:
        if c == '(':
            stack.append(c)
        elif c == ')':
            while stack and stack[-1] != '(':
                postfix.append(stack.pop())
            if stack:
                stack.pop()
        elif c not in ('|', '?', '+', '*', '.'):
            postfix.append(c)
        else:
            while stack and get_precedence(stack[-1]) >= get_precedence(c):
                postfix.append(stack.pop())
            stack.append(c)
    while stack:
        postfix.append(stack.pop())
    return ''.join(postfix)

class Node:
    def __init__(self, value):
        self.value = value
        self.left = None
        self.right = None

def postfix_a_ast(postfix):
    stack = []
    for char in postfix:
        if char in ('|', '.', '*', '+', '?'):
            if char in ('|', '.'):
                if len(stack) < 2:
                    raise ValueError(f"Error en la expresión postfix: falta operandos para el operador '{char}'")
                node = Node(char)
                node.right = stack.pop()
                node.left = stack.pop()
            elif char in ('*', '+', '?'):
                if len(stack) < 1:
                    raise ValueError(f"Error en la expresión postfix: falta operando para el operador '{char}'")
                node = Node(char)
                node.left = stack.pop()
            stack.append(node)
        else:
            stack.append(Node(char))

    if len(stack) != 1:
        raise ValueError(f"Error en la conversión postfix: la expresión no es válida. Stack final: {stack}")

    return stack.pop()

def add_edges(dot, node):
    if node:
        node_id = str(id(node))
        dot.node(node_id, node.value)
        if node.left:
            left_id = str(id(node.left))
            dot.edge(node_id, left_id)
            add_edges(dot, node.left)
        if node.right:
            right_id = str(id(node.right))
            dot.edge(node_id, right_id)
            add_edges(dot, node.right)

def draw_ast(root, index):
    dot = Digraph()
    add_edges(dot, root)
    filename = f'ast{index}.png'
    dot.render(filename, format='png', cleanup=True)
    print(f"Árbol sintáctico guardado en {filename}")

class AFN:
    def __init__(self):
        self.states = []
        self.transitions = {}
        self.initial_state = None
        self.accepting_states = set()

    def add_state(self):
        state = len(self.states)
        self.states.append(state)
        self.transitions[state] = []
        return state

    def add_transition(self, from_state, to_state, symbol):
        self.transitions[from_state].append((symbol, to_state))

    def set_initial_state(self, state):
        self.initial_state = state

    def add_accepting_state(self, state):
        self.accepting_states.add(state)

def thompson_construction(ast_node):
    afn = AFN()
    if ast_node.value == '|':
        left_afn = thompson_construction(ast_node.left)
        right_afn = thompson_construction(ast_node.right)

        start_state = afn.add_state()
        end_state = afn.add_state()

        afn.set_initial_state(start_state)
        afn.add_transition(start_state, left_afn.initial_state, 'ε')
        afn.add_transition(start_state, right_afn.initial_state, 'ε')

        afn.transitions.update(left_afn.transitions)
        afn.transitions.update(right_afn.transitions)

        if left_afn.accepting_states:
            for state in left_afn.accepting_states:
                afn.add_transition(state, end_state, 'ε')
        if right_afn.accepting_states:
            for state in right_afn.accepting_states:
                afn.add_transition(state, end_state, 'ε')

        afn.add_accepting_state(end_state)

    elif ast_node.value == '.':
        left_afn = thompson_construction(ast_node.left)
        right_afn = thompson_construction(ast_node.right)

        afn.set_initial_state(left_afn.initial_state)
        afn.transitions.update(left_afn.transitions)
        afn.transitions.update(right_afn.transitions)

        if left_afn.accepting_states:
            for state in left_afn.accepting_states:
                afn.add_transition(state, right_afn.initial_state, 'ε')
        afn.add_accepting_state(right_afn.accepting_states.pop())

    elif ast_node.value == '*':
        inner_afn = thompson_construction(ast_node.left)

        start_state = afn.add_state()
        end_state = afn.add_state()

        afn.set_initial_state(start_state)
        afn.add_transition(start_state, inner_afn.initial_state, 'ε')
        afn.add_transition(start_state, end_state, 'ε')
        afn.transitions.update(inner_afn.transitions)

        if inner_afn.accepting_states:
            for state in inner_afn.accepting_states:
                afn.add_transition(state, inner_afn.initial_state, 'ε')
                afn.add_transition(state, end_state, 'ε')

        afn.add_accepting_state(end_state)

    elif ast_node.value == '+':
        inner_afn = thompson_construction(ast_node.left)

        start_state = afn.add_state()
        end_state = afn.add_state()

        afn.set_initial_state(start_state)
        afn.add_transition(start_state, inner_afn.initial_state, 'ε')
        afn.transitions.update(inner_afn.transitions)

        if inner_afn.accepting_states:
            for state in inner_afn.accepting_states:
                afn.add_transition(state, inner_afn.initial_state, 'ε')
                afn.add_transition(state, end_state, 'ε')

        afn.add_accepting_state(end_state)

    elif ast_node.value == '?':
        inner_afn = thompson_construction(ast_node.left)

        start_state = afn.add_state()
        end_state = afn.add_state()

        afn.set_initial_state(start_state)
        afn.add_transition(start_state, inner_afn.initial_state, 'ε')
        afn.add_transition(start_state, end_state, 'ε')
        afn.transitions.update(inner_afn.transitions)

        if inner_afn.accepting_states:
            for state in inner_afn.accepting_states:
                afn.add_transition(state, end_state, 'ε')

        afn.add_accepting_state(end_state)

    else:
        start_state = afn.add_state()
        end_state = afn.add_state()

        afn.set_initial_state(start_state)
        afn.add_transition(start_state, end_state, ast_node.value)
        afn.add_accepting_state(end_state)

    return afn

def graficar_automata(afn, filename):
    G = nx.MultiDiGraph()
    for state in afn.states:
        if state == afn.initial_state:
            G.add_node(state, shape="circle", color="green", style="filled")
        elif state in afn.accepting_states:
            G.add_node(state, shape="doublecircle", color="red", style="filled")
        else:
            G.add_node(state, shape="circle")

    for from_state, transitions in afn.transitions.items():
        for symbol, to_state in transitions:
            G.add_edge(from_state, to_state, label=symbol)

    pos = nx.spring_layout(G)
    edge_labels = nx.get_edge_attributes(G, 'label')
    nx.draw(G, pos, with_labels=True, node_color='skyblue', node_size=2000, font_size=10)
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color='red')
    plt.savefig(filename)
    plt.close()

def convertir_afn_a_afd(afn):
    dfa = AFN()
    initial_state_set = frozenset([afn.initial_state])
    state_map = {initial_state_set: dfa.add_state()}
    dfa.set_initial_state(state_map[initial_state_set])

    if any(state in afn.accepting_states for state in initial_state_set):
        dfa.add_accepting_state(state_map[initial_state_set])

    stack = [initial_state_set]
    while stack:
        current_set = stack.pop()
        current_state = state_map[current_set]

        transition_map = {}
        for state in current_set:
            for symbol, to_state in afn.transitions.get(state, []):
                if symbol == 'ε':
                    continue
                if symbol not in transition_map:
                    transition_map[symbol] = set()
                transition_map[symbol].add(to_state)

        for symbol, to_state_set in transition_map.items():
            to_state_set = frozenset(to_state_set)
            if to_state_set not in state_map:
                state_map[to_state_set] = dfa.add_state()
                stack.append(to_state_set)
                if any(state in afn.accepting_states for state in to_state_set):
                    dfa.add_accepting_state(state_map[to_state_set])

            dfa.add_transition(current_state, state_map[to_state_set], symbol)

    return dfa

def minimizar_dfa(dfa):
    states = set(dfa.states)
    accepting_states = dfa.accepting_states
    non_accepting_states = states - accepting_states

    partitions = [accepting_states, non_accepting_states]
    while True:
        new_partitions = []
        for group in partitions:
            equiv_classes = {}
            for state in group:
                transitions = frozenset((symbol, dfa.transitions[state]) for symbol in dfa.transitions[state])
                if transitions not in equiv_classes:
                    equiv_classes[transitions] = set()
                equiv_classes[transitions].add(state)
            new_partitions.extend(equiv_classes.values())
        if len(new_partitions) == len(partitions):
            break
        partitions = new_partitions

    minimized_dfa = AFN()
    state_map = {}

    for group in partitions:
        new_state = minimized_dfa.add_state()
        state_map[frozenset(group)] = new_state
        if any(state == dfa.initial_state for state in group):
            minimized_dfa.set_initial_state(new_state)
        if any(state in dfa.accepting_states for state in group):
            minimized_dfa.add_accepting_state(new_state)

    for group in partitions:
        from_state = state_map[frozenset(group)]
        for state in group:
            for symbol, to_states in dfa.transitions[state]:
                to_state_group = next(gr for gr in partitions if to_states.pop() in gr)
                to_state = state_map[frozenset(to_state_group)]
                minimized_dfa.add_transition(from_state, to_state, symbol)

    return minimized_dfa

def simulate_automaton(automaton, input_string):
    current_states = {automaton.initial_state}
    for symbol in input_string:
        next_states = set()
        for state in current_states:
            for transition_symbol, next_state in automaton.transitions.get(state, []):
                if transition_symbol == symbol:
                    next_states.add(next_state)
        current_states = next_states

    return bool(current_states & automaton.accepting_states)

def main():
    with open("input.txt", "r") as file:
        expressions = file.readlines()

    for i, expression in enumerate(expressions):
        expression = expression.strip()

        print(f"Expresión original: {expression}")

        postfix_expression = infix_a_postfix(expression)
        print(f"Expresión en postfix: {postfix_expression}")

        ast_root = postfix_a_ast(postfix_expression)
        draw_ast(ast_root, i + 1)

        afn = thompson_construction(ast_root)
        graficar_automata(afn, f"afn{i + 1}.png")

        afd = convertir_afn_a_afd(afn)
        graficar_automata(afd, f"afd{i + 1}.png")

        minimized_afd = minimizar_dfa(afd)
        graficar_automata(minimized_afd, f"min_afd{i + 1}.png")

        string_to_test = "abba"  # Cambia esta cadena según sea necesario
        pertenece = simulate_automaton(minimized_afd, string_to_test)
        if pertenece:
            print(f"La cadena '{string_to_test}' pertenece al lenguaje definido por la expresión '{expression}'.")
        else:
            print(f"La cadena '{string_to_test}' NO pertenece al lenguaje definido por la expresión '{expression}'.")

if __name__ == "__main__":
    main()
