import networkx as nx

graph: nx.MultiDiGraph = nx.read_graphml("Graphs/Espresso_1.graphml.xml", force_multigraph=True)

for divider in [2, 4, 8]:

    for u, v, k1 in graph.edges(keys = True):
        if int(k1[-1]) % 2:
            capacity = int(graph[u][v][k1]["capacity"])

            old_balance_1 = int(graph[u][v][k1]["balance"])
            new_balance_1 = int(old_balance_1 / divider)

            k2 = f"{k1[0]}{int(k1[1:])-1}"

            new_balance_2 = capacity - new_balance_1

            graph[u][v][k1]["balance"] = abs(new_balance_1)
            graph[v][u][k2]["balance"] = abs(new_balance_2)

    graph.name = f"Espresso_{divider}"
    nx.write_graphml_xml(graph, f"Graphs/Espresso_{divider}.graphml.xml")