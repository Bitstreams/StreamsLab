from UI import *

def get_erdos_renyi_menu(ui: UI):
    return InputWindow(
        ui,
        "Erdös-Renyi",
        [
            "Generates a {{i:G_{n,m}}} random graph",
            "",
            "In the {{i:G_{n,m}}} model, a graph is chosen uniformly at random",
            "from the set of all graphs with {{i:n}} nodes and {{i:m}} edges.",
            "",
            "{{iu:Note: }}{{i:Numeric attributes are generated randomly with μ and σ using the Box-Muller Transform}}"
        ],
        {
            "EXPERIMENT_NAME": Input(
                "Experiment name",
                str,
                lambda s: 3 <= len(s) <= 12 and (s.isalnum() or '_' in s),
                "Name must be between 3 and 12 alphanumeric characters or underscore"
            ),
            "NUMBER_OF_NODES": Input(
                "Number of nodes ({{i:n}})",
                int,
                lambda n: 2 <= n <= 1_000,
                "{{i:n}} must be a number between two and one thousand"
            ),
            "NUMBER_OF_EDGES": Input(
                "Number of edges ({{i:m}})",
                int,
                lambda n: 10 <= n <= 2_000,
                "{{i:m}} must be a number between ten and two thousands"
            ),
            "MEAN_CHANNEL_CAPACITY": Input(
                "Mean channel capacity ({{i:μ_capacity}})",
                int,
                lambda n: 100_000_000 <= n <= 100_000_000_000,
                "{{i:μ_capacity}} must be a number between a hundred million and a hundred billion"
            ),
            "CHANNEL_CAPACITY_DEVIATION": Input(
                "Channel capacity deviation ({{i:σ_capacity}})",
                float,
                lambda n: 0.0 <= n,
                "{{i:σ_capacity}} must be a floating-point number greater than zero"
            ),
            "MEAN_PROPORTIONAL_FEE": Input(
                "Mean proportional fee percent ({{i:μ_proportional_fee}})",
                float,
                lambda n: 0.0 <= n <= 50.0,
                "{{i:μ_base_fee}} must be a floating-point number between zero and fifty"
            ),
            "PROPORTIONAL_FEE_DEVIATION": Input(
                "Proportional fee deviation ({{i:σ_base_fee}})",
                float,
                lambda n: 0.0 <= n,
                "{{i:σ_base_fee}} must be a floating-point number greater than zero"
            )
        },
        "Confirm selected inputs",
        "Cancel"
    )