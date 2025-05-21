import asyncio
import os
from networkx import gnm_random_graph
import networkx as nx
from Lab import *
from UI import *
from VisualComponents import *

async def main():
    with UI("STREAMSLAB") as ui:
        main = get_main_menu(ui)

        main_selected = main.options[0]

        graph: PayGraph | None = None

        while not graph:

            main_selected = main.display(main_selected)

            match main.options.index(main_selected):
                case 0:
                    while not graph:
                        erdos_renyi = get_erdos_renyi_menu(ui).display()

                        if not erdos_renyi:
                            continue

                        topology = nx.gnm_random_graph(
                            n = erdos_renyi["NUMBER_OF_NODES"].value,
                            m = erdos_renyi["NUMBER_OF_EDGES"].value,
                            directed = True
                        )

                        graph = PayGraph(
                            erdos_renyi["EXPERIMENT_NAME"].value,
                            topology,
                            mean_capacity = erdos_renyi["MEAN_CHANNEL_CAPACITY"].value,
                            capacity_deviation = erdos_renyi["CHANNEL_CAPACITY_DEVIATION"].value,
                            mean_ppm_fee = erdos_renyi["MEAN_PROPORTIONAL_FEE"].value * 10_000,
                            ppm_fee_deviation = erdos_renyi["PROPORTIONAL_FEE_DEVIATION"].value * 10_000
                        )

                case 1:
                    load = Menu(
                        ui,
                        "Load Existing Laboratory Graph",
                        [
                            "Please choose one of the existing laboratory graph files"
                        ],
                        [
                            *os.listdir("Graphs"),
                            "Back to Source Graph menu"
                        ],
                        True
                    )

                    load_selected = load.options[0]

                    while not graph:
                         load_selected = load.display(load_selected)
                         if load_selected  ==  load.options[-1]:
                            break
                         else:
                            if YesNoWindow(
                                ui,
                                "Confirm File Load",
                                [
                                    f"You're about to load graph from {load_selected}",
                                    "",
                                    "Are you sure?"
                                ]
                            ).display():
                                graph = PayGraph.load(f"Graphs/{load_selected}")
                
                case 2:
                    return
        
        nx.write_graphml_xml(graph, f"Graphs/{graph.name}.graphml.xml")

        async def track_lab_start(lab: Lab):
            total_progress = lab.total_miner_count + lab.total_node_count * 2 + lab.total_channel_count * 2
            progress = ProgressWindow(ui, f"Start Lab {lab.name}", total = total_progress)
            progress.display()
            while lab.status != Lab.Status.READY:
                progress.update(lab.created_miner_count + lab.created_node_count + lab.funded_channel_count + lab.synced_node_count, get_lab_progress_label(lab.status))
                await asyncio.sleep(1)
            progress.close()
        
        async def track_lab_stop(lab: Lab):
            total_progress = lab.total_node_count
            progress = ProgressWindow(ui, f"Stop Lab {lab.name}", total = total_progress)
            progress.display()
            while lab.status != Lab.Status.STOPPED:
                progress.update(lab.total_miner_count + lab.total_node_count - lab.created_miner_count - lab.created_node_count, get_lab_progress_label(lab.status))
                await asyncio.sleep(1)
            progress.close()

        duration = 600

        lab: Lab = Lab(graph)
        await asyncio.gather(track_lab_start(lab), lab.start())
        wait = ProgressWindow(ui, "Waiting", total = duration)
        wait.display()

        asyncio.create_task(generate_traffic(lab, 10000000))

        c = 0
        while c < duration:
            wait.update(c, f"{duration - c} seconds remaining...")
            await asyncio.sleep(1)
            c += 1

        await asyncio.gather(track_lab_stop(lab), lab.stop())

        wait.close()

        OkWindow(
            ui,
            "Experiment completed",
            [
                "Lab stopped and experiment was completed successfully",
                "",
                "Press any key to continue..."
            ]
        ).display()
try:
    asyncio.run(main=main())
except Exception as e:
    print("ERROR:", e)