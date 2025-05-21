from Lab import *

def get_lab_progress_label(status: Lab.Status):
    match status:
        case Lab.Status.STOPPED:
            return "Starting..."
        case Lab.Status.CREATE_MINERS:
            return "Creating miners..."
        case Lab.Status.CONNECT_MINERS:
            return "Connecting miners..."
        case Lab.Status.CREATE_NODES_FUND_CHANNELS:
            return "Creating nodes and funding channels..."
        case Lab.Status.CREATE_CHANNELS:
            return "Creating channels..."
        case Lab.Status.SYNC_NODES:
            return "Waiting for nodes to sync..."
        case Lab.Status.READY:
            return "Lab ready!"
        case Lab.Status.STOPPING:
            return "Stopping miners and nodes..."
