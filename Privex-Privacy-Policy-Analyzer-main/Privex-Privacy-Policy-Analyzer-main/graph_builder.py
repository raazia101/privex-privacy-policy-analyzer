import networkx as nx
import matplotlib.pyplot as plt

def build_graph(data):
    G = nx.DiGraph()

    # Base nodes
    G.add_node("User")
    G.add_node("Website")

    # Data collected
    for d in data.get("data_collected", []):
        G.add_node(d)
        G.add_edge("User", "Website", label="provides")
        G.add_edge("Website", d, label="collects")

    # Third parties
    for t in data.get("shared_with", []):
        G.add_node(t)
        G.add_edge("Website", t, label="shares")

    # Purpose
    for p in data.get("purpose", []):
        G.add_node(p)
        G.add_edge("Website", p, label="used_for")

    return G


def show_graph(G):
    pos = nx.spring_layout(G)
    nx.draw(G, pos, with_labels=True, node_size=2000)
    edge_labels = nx.get_edge_attributes(G, 'label')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)
    plt.show()
