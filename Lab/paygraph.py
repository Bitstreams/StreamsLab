from __future__ import annotations
from typing import cast, overload
from networkx import MultiDiGraph, Graph
import networkx as nx
import random

class PayGraph(MultiDiGraph):
    @classmethod
    def load(cls, filepath: str) -> PayGraph:
        graph: Graph = nx.read_graphml(path = filepath, force_multigraph = True)
        return cast(PayGraph, graph)

    def __init__(
        self,
        name: str,
        topology: Graph,
        *,
        mean_capacity: int = 50000000,
        capacity_deviation: int = 100,
        mean_balance_ratio: float = 0.5,
        balance_ratio_deviation: float = 100,
        mean_base_fee: int = 0,
        base_fee_deviation: float = 100,
        mean_ppm_fee: float = 1000,
        ppm_fee_deviation: float = 100
    ) -> None:
        super().__init__()
        self.name = name

        for index, (source, target) in enumerate(topology.edges):
            source_key: str = f"n{source}"
            target_key: str = f"n{target}"
            outbound_key: str = f"e{index * 2}"
            inbound_key: str = f"e{index * 2 + 1}"
            
            self.add_edge(source_key, target_key, outbound_key)
            self.add_edge(target_key, source_key, inbound_key)
            capacity = max(int(abs(random.gauss(mean_capacity, capacity_deviation))), 546 / 0.01 * 1000)
            self.edges[source_key, target_key, outbound_key]["capacity"] = capacity
            self.edges[target_key, source_key, inbound_key]["capacity"] = capacity

            self.edges[source_key, target_key, outbound_key]["balance"] = int(random.gauss(mean_balance_ratio * capacity, balance_ratio_deviation))
            self.edges[target_key, source_key, inbound_key]["balance"] =  self.edges[source_key, target_key, outbound_key]["capacity"] - self.edges[source_key, target_key, outbound_key]["balance"]

            self.edges[source_key, target_key, outbound_key]["base_fee"] = int(abs(random.gauss(mean_base_fee, base_fee_deviation))) if mean_base_fee else 0
            self.edges[source_key, target_key, outbound_key]["ppm_fee"] = int(abs(random.gauss(mean_ppm_fee, ppm_fee_deviation))) if mean_ppm_fee else 0
            
            self.edges[target_key, source_key, inbound_key]["base_fee"] = int(abs(random.gauss(mean_base_fee, base_fee_deviation))) if mean_base_fee else 0
            self.edges[target_key, source_key, inbound_key]["ppm_fee"] = int(abs(random.gauss(mean_ppm_fee, ppm_fee_deviation))) if mean_ppm_fee else 0
    
    @classmethod
    def is_outbound_edge(cls, key: str) -> bool:
        return int(key[1:]) % 2 == 0
    
    @classmethod
    def get_inbound_edge_key(cls, edge_key: str) -> str:
        outbound_edge_index: int = int(int(edge_key[1:]) // 2) * 2 + 1
        return f"e{outbound_edge_index}"