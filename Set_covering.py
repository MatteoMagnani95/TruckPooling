from gurobipy import Model, GRB, quicksum
from utils import *
from typing import List, Dict
LOGDIR = "Output/Logs"


def solve_set_covering(i_name: str, trips: List[Dict], deliveries: List[Delivery]) -> List[Dict]:
    """
    Solve the set covering problem:
    Select a subset of trips so that each delivery is covered exactly once,
    minimizing the total traveled kilometers.

    Args:
        trips: list of dicts, each with keys including 'shipment_ids' (list of delivery ids) and 'total_km' (cost)
        deliveries: list of Delivery namedtuples to cover (used to get all delivery ids)

    Returns:
        List of selected trips (subset of trips input).
    """
    model = Model("TripSelection")
    model.setParam("OutputFlag", 1)
    model.setParam("LogFile", os.path.join(LOGDIR, f"{i_name}.log"))
    model.setParam("TimeLimit", 3600)  # Set time limit
    model.setParam("Seed", 12345)  # Set seed for reproducibility

    # Map variable for each trip
    x = {i: model.addVar(vtype=GRB.BINARY, name=f"x_{i}") for i in range(len(trips))}

    # Extract all delivery ids to cover
    delivery_ids = [d.id for d in deliveries]

    # Add constraints: each delivery covered exactly once
    for d_id in delivery_ids:
        model.addConstr(
            quicksum(x[i] for i, t in enumerate(trips) if d_id in t["shipment_ids"]) == 1,
            name=f"cover_{d_id}"
        )

    # Objective: minimize total score of selected trips
    model.setObjective(
        quicksum(x[i] * trips[i]["score"] for i in x),
        GRB.MINIMIZE
    )
    model.optimize()

    selected_trips = [trips[i] for i in x if x[i].X > 0.5]

    return selected_trips