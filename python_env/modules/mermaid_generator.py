try:
    from mermaid.sequence import SequenceDiagram, Actor
    from mermaid.sequence.link import Link, ArrowTypes
    from mermaid.graph import Graph, Node, Direction
    from mermaid.graph.link import Link as GraphLink
except ImportError:
    # Fallback definitions
    class SequenceDiagram:
        def __init__(self, title, elements):
            self.script = f"sequenceDiagram\n    title {title}\n" + ''.join(map(str, elements))

    class Actor:
        def __init__(self, name, alias=None):
            self.name, self.alias = name, alias
        
        def __str__(self):
            return f"\tparticipant {self.name} as {self.alias}\n" if self.alias else f"\tparticipant {self.name}\n"

    class Link:
        def __init__(self, from_actor, to_actor, arrow_type, message):
            self.from_actor, self.to_actor = from_actor, to_actor
            self.arrow_type, self.message = arrow_type, message
        
        def __str__(self):
            return f"\t{self.from_actor}{self.arrow_type}{self.to_actor}: {self.message}\n"

    class ArrowTypes:
        SOLID_RIGHT_ARROW = "->>"
        DOTTED_LEFT_ARROW = "-->>"

    class Graph:
        def __init__(self, title, script):
            self.script = f"---\ntitle: {title}\n---\n{script}"

    class Node:
        def __init__(self, id, text):
            self.id, self.text = id, text
        
        def __str__(self):
            return f"    {self.id}[{self.text}]\n"

    class GraphLink:
        def __init__(self, from_node, to_node, label=None):
            self.from_node, self.to_node = from_node, to_node
            self.label = label
        
        def __str__(self):
            return f"    {self.from_node} -->{f'|{self.label}|' if self.label else ''} {self.to_node}\n"

    class Direction:
        TOP_BOTTOM = "TD"

def generate_sequence_diagram(participants, messages, output_file="mermaid_generated/sequence_diagram.mmd"):
    elements = [Actor(p['name'], p.get('alias')) for p in participants]
    elements += [Link(m['from'], m['to'], ArrowTypes.SOLID_RIGHT_ARROW if not m.get('response') else ArrowTypes.DOTTED_LEFT_ARROW, m['message']) for m in messages]
    
    diagram = SequenceDiagram(title="Diagramme de Séquence", elements=elements)
    with open(output_file, "w") as f:
        f.write(diagram.script)
    print(f"Diagramme de séquence Mermaid généré et sauvegardé dans {output_file}")

def generate_flowchart(nodes, connections, output_file="mermaid_generated/flowchart.mmd"):
    flowchart_script = f"graph {Direction.TOP_BOTTOM}\n" + ''.join(map(str, [Node(nd['id'], nd['text']) for nd in nodes] + [GraphLink(conn['from'], conn['to'], conn.get('label')) for conn in connections]))

    diagram = Graph(title="Diagramme de Flux", script=flowchart_script)
    with open(output_file, "w") as f:
        f.write(diagram.script)
    print(f"Diagramme de flux Mermaid généré et sauvegardé dans {output_file}")

if __name__ == "__main__":
    seq_participants = [{'name': 'Utilisateur'}, {'name': 'Système', 'alias': 'S'}, {'name': 'BaseDeDonnées', 'alias': 'DB'}]
    seq_messages = [
        {'from': 'Utilisateur', 'to': 'Système', 'message': 'Requête de données'},
        {'from': 'Système', 'to': 'BaseDeDonnées', 'message': 'Interroger la DB'},
        {'from': 'BaseDeDonnées', 'to': 'Système', 'message': 'Données renvoyées', 'response': True},
        {'from': 'Système', 'to': 'Utilisateur', 'message': 'Afficher les résultats', 'response': True}
    ]
    generate_sequence_diagram(seq_participants, seq_messages)

    flow_nodes = [{'id': 'A', 'text': 'Début'}, {'id': 'B', 'text': 'Effectuer une tâche'}, {'id': 'C', 'text': 'Décision ?'}, {'id': 'D', 'text': 'Fin'}]
    flow_connections = [{'from': 'A', 'to': 'B'}, {'from': 'B', 'to': 'C'}, {'from': 'C', 'to': 'D', 'label': 'Oui'}, {'from': 'C', 'to': 'B', 'label': 'Non'}]
    generate_flowchart(flow_nodes, flow_connections)
