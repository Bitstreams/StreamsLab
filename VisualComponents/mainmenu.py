from UI import *

def get_main_menu(ui: UI) -> Menu:
    return Menu(
        ui,
        "Source Laboratory Graph",
        [
            "This script allows for the creation of a Bitcoin payment channel network (BPCN) laboratory from a graph",
            "with BPCN nodes represented as the graph vertices and channels represented as the graph edges",
            "Node and channel attributes (like node resource limits, channel capacities, etc...) are represented as data keys",
            "",
            "Please, choose how to source the laboratory graph"
        ],
        [
            "Generate a new laboratory graph based on the Erdös-Renyi model...",
            "Load laboratory graph from a file...",
            "Exit"
        ],
        True
    )