from gurobipy import Model, GRB, quicksum
from utils import *
from typing import List, Dict

def solve_set_covering(LOGDIR: str,
                                     i_name: str,
                                     trips: List[Dict],
                                     deliveries: List[Delivery],
                                     pool_solutions: int = 100,
                                     pool_gap: float = None,
                                     time_limit: int = 3600):
    """
    Solve the set-covering MIP and return ALL solutions stored in Gurobi's solution pool.

    Returns:
        solutions: list of dicts, one per solution found/stored. Each dict contains:
            - 'obj': objective value (PoolObjVal for that solution)
            - 'selected_trip_indices': list of trip indices selected in this solution
            - 'selected_trips': list of trip dicts (from input trips)
            - 'total_km', 'total_weight', 'total_volume', 'score' aggregated for the solution
            - 'solution_number': solution index in the pool (0..SolCount-1)
    Notes:
        - We set PoolSearchMode and PoolSolutions to ask Gurobi to keep multiple solutions.
        - Optionally set PoolGap (e.g. 0.05 for within 5% of best) to restrict stored suboptimal solutions.
        - See Gurobi docs (Solution Pool and Xn attribute) for details. :contentReference[oaicite:2]{index=2}
    """
    # --- Model setup ---------------------------------------------------------
    model = Model("TripSelection")
    model.setParam("OutputFlag", 1)
    model.setParam("LogFile", os.path.join(LOGDIR, f"{i_name}.log"))
    model.setParam("TimeLimit", time_limit)
    model.setParam("Seed", 12345)

    # Solution pool parameters
    model.setParam("PoolSearchMode", 2)      # search for many solutions (2 = aggressive search)
    model.setParam("PoolSolutions", pool_solutions)  # max number of solutions to store
    if pool_gap is not None:
        # Store solutions within `pool_gap` relative gap of best objective (e.g. 0.05 for 5%)
        model.setParam("PoolGap", float(pool_gap))

    # --- Variables -----------------------------------------------------------
    x = {i: model.addVar(vtype=GRB.BINARY, name=f"x_{i}") for i in range(len(trips))}
    all_vars = list(x.values())

    # --- Covering constraints ------------------------------------------------
    delivery_ids = [d.id for d in deliveries]
    for d_id in delivery_ids:
        model.addConstr(
            quicksum(x[i] for i, t in enumerate(trips) if d_id in t["shipment_ids"]) == 1,
            name=f"cover_{d_id}"
        )

    # --- Objective -----------------------------------------------------------
    # Keep same objective (minimize total score)
    model.setObjective(quicksum(x[i] * trips[i]["score"] for i in x), GRB.MINIMIZE)

    # --- Optimize ------------------------------------------------------------
    model.optimize()

    # If no solution found at all
    if model.SolCount == 0:
        print(f"No feasible solution found for instance {i_name}. Status={model.Status}")
        return []

    # --- Extract solutions from pool ----------------------------------------
    solutions = []
    # iterate over pool solutions (0 .. SolCount-1)
    sol_count = model.SolCount
    for s in range(sol_count):
        # Tell Gurobi which solution from the pool we want to inspect
        # (SolutionNumber is a parameter that controls which Xn values are returned)
        model.setParam("SolutionNumber", s)

        # Get the variable values for the chosen pool solution:
        # model.getAttr("Xn", all_vars) returns the list of Xn values for current SolutionNumber.
        xn_list = model.getAttr("Xn", all_vars)  # list of 0.0/1.0 (or fractional) per var for solution s

        obj_val = model.getAttr("PoolObjVal")

        # Collect selected trips
        selected_indices = [i for i, val in enumerate(xn_list) if val > 0.5]
        selected_trip_dicts = [trips[i] for i in selected_indices]

        # Aggregate some metrics
        total_km = sum(t["total_km"] for t in selected_trip_dicts)
        total_weight = sum(t["total_weight"] for t in selected_trip_dicts)
        total_volume = sum(t["total_volume"] for t in selected_trip_dicts)
        total_score = sum(t["score"] for t in selected_trip_dicts)

        solutions.append({
            "solution_number": s,
            "obj": float(obj_val),
            "selected_trip_indices": selected_indices,
            "selected_trips": selected_trip_dicts,
            "total_km": float(total_km),
            "total_weight": float(total_weight),
            "total_volume": float(total_volume),
            "total_score": float(total_score),
        })

    print(f"Found {len(solutions)} solution(s) in pool for instance {i_name}.")
    # Sort solutions by objective (lowest first)
    solutions_sorted = sorted(solutions, key=lambda z: z["obj"])
    with open(os.path.join(LOGDIR, f"{i_name}.log"), "a") as f:
        f.write(f"Found {len(solutions_sorted)} pool solutions for {i_name} (Time {model.Runtime:.2f}s)\n")
        for sol in solutions_sorted:
            f.write(f"Solution #{sol['solution_number']}: obj={sol['obj']:.6f}, "
                    f"selected_trips={sol['selected_trip_indices']}, total_km={sol['total_km']:.2f}\n")

    # Print brief summary
    for idx, sol in enumerate(solutions_sorted):
        print(f"[{idx}] Sol#{sol['solution_number']}: obj={sol['obj']:.6f}, "
              f"trips={len(sol['selected_trip_indices'])}, total_km={sol['total_km']:.2f}")

    # Return ALL solutions (sorted by objective)
    return solutions_sorted
