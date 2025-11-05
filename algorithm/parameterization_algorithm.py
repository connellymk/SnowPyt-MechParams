from typing import List
from data_structures import Node, Graph
from definitions import graph

def breadth_first_search(graph: Graph, start_node: Node) -> List[Node]:
    """
    Perform breadth-first search on the graph starting from the given node.
    """
    visited = set()
    queue = [start_node]
    while queue:
        node = queue.pop(0)
        if node not in visited:
            visited.add(node)
            # Add the destination nodes of all outgoing edges to the queue
            for edge in node.outgoing_edges:
                if edge.end not in visited:
                    queue.append(edge.end)
    return list(visited)

#print(breadth_first_search(graph, graph.nodes[0]))

def find_parameterizations(graph: Graph, target_parameter: Node) -> List[Node]:
    """
    Find all parameterizations of the target parameter in the graph.
    """
    parameterizations = []
    end_node = graph.get_node("snow_pit")

    visited = set()
    queue = [target_parameter]
    while queue:
        node = queue.pop(0)
        if node not in visited:
            visited.add(node)
            if node == end_node:
                parameterizations.append(visited)
                
            elif node.type == "parameter":
                # choose 1 path
                for edge in node.outgoing_edges:
                    if edge.end not in visited:
                        queue.append(edge.end)
            elif node.type == "merge":
                # choose all paths
                for edge in node.incoming_edges:
                    if edge.end not in visited:
                        queue.append(edge.end)


    return parameterizations